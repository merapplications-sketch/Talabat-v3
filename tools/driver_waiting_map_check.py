"""Waiting map binding (assets/driver-tech/waiting-map.js) on driver A WAIT-HOME-01 — LOCAL mock only.
Chromium + the repo fixture (no Supabase), Leaflet 1.9.4 served from a local copy in place of the CDN, OSM tiles answered
locally (1-px image) or failed on purpose, browser geolocation mocked by Playwright. NOT proof of: iPhone Safari, real GPS,
real OSM tiles, the live database or dispatch.
  python3 tools/driver_waiting_map_check.py <leaflet_dist_dir>     (dir with leaflet.js + leaflet.css of leaflet@1.9.4)"""
import os, sys, base64, subprocess, json
from playwright.sync_api import sync_playwright
here = os.path.dirname(os.path.abspath(__file__)); root = os.path.abspath(os.path.join(here, '..'))
LEAF = sys.argv[1]
out = os.path.join(root, 'waiting-map-qa'); os.makedirs(out, exist_ok=True)
subprocess.run([sys.executable, os.path.join(here, 'driver_a_fixture.py'), out], check=True, capture_output=True)
FIX = open(os.path.join(out, 'review-fixture.js')).read()
PNG = base64.b64decode('iVBORw0KGgoAAAANSUhEUgAAAAEAAAABCAQAAAC1HAwCAAAAC0lEQVR42mP8/x8AAwMCAO+ip1sAAAAASUVORK5CYII=')
ME = {'latitude': 38.5735, 'longitude': 68.7862, 'accuracy': 25}
fails = []; n = 0
def ok(c, m):
    global n; n += 1; print(('PASS ' if c else 'FAIL ') + m, flush=True)
    if not c: fails.append(m)

def page(b, geo='grant', tiles='ok', leaflet='ok', width=390, stores=None):
    ctx = b.new_context(viewport={'width': width, 'height': 844}, permissions=(['geolocation'] if geo == 'grant' else []),
                        geolocation=ME if geo == 'grant' else None)
    errs = []; net = {'tiles': 0, 'leaflet': 0, 'other': [], 'mode': {'tiles': tiles, 'leaflet': leaflet}}   # mode can change during a case (retry)
    def route(rt, rq):
        u = rq.url
        if 'supabase-js' in u: return rt.fulfill(status=200, content_type='application/javascript', body=FIX)
        if 'leaflet@1.9.4/dist/leaflet.js' in u:
            net['leaflet'] += 1
            return rt.abort() if net['mode']['leaflet'] == 'fail' else rt.fulfill(status=200, content_type='application/javascript', body=open(os.path.join(LEAF, 'leaflet.js')).read())
        if 'leaflet@1.9.4/dist/leaflet.css' in u: return rt.fulfill(status=200, content_type='text/css', body=open(os.path.join(LEAF, 'leaflet.css')).read())
        if 'tile.openstreetmap.org' in u:
            net['tiles'] += 1
            return rt.abort() if net['mode']['tiles'] == 'fail' else rt.fulfill(status=200, content_type='image/png', body=PNG)
        if u.startswith('http'): net['other'].append(u); return rt.abort()
        return rt.continue_()
    ctx.route('**/*', route)
    init = "window.__UI_CASE='empty';localStorage.setItem('tlb_lang','ru');window.__netFail=false;" \
           "window.fetch=()=>window.__netFail?Promise.reject(new Error('isolated offline')):Promise.resolve(new Response('',{status:200}));" \
           "window.__watch=0;const _w=navigator.geolocation.watchPosition.bind(navigator.geolocation);navigator.geolocation.watchPosition=function(){window.__watch++;return _w.apply(null,arguments)};"
    if geo == 'deny':
        init += "navigator.geolocation.watchPosition=function(s,e){window.__watch++;setTimeout(()=>e({code:1,message:'denied'}),50);return 1};"
    if geo == 'hang':
        init += "navigator.geolocation.watchPosition=function(){window.__watch++;return 1};"
    ctx.add_init_script(init)
    pg = ctx.new_page(); pg.on('pageerror', lambda e: errs.append(str(e)))
    pg.goto('file://' + root + '/driver.html', wait_until='domcontentloaded')
    pg.wait_for_function("()=>typeof DRV!=='undefined'&&!!DRV")
    # wrap the real provider to count its lifecycle (the provider itself is unchanged)
    pg.evaluate("""()=>{const P=window.TALABOT_WAITING_MAP_UI,m=P.mount;window.__lc={mount:0,destroy:0};P.mount=function(node,o){window.__lc.mount++;const h=m.call(P,node,o),d=h.destroy;h.destroy=function(){window.__lc.destroy++;return d.apply(h,arguments)};return h}}""")
    if stores: pg.evaluate(stores)
    pg.evaluate("()=>{online=true;startGeo();render()}")
    pg.wait_for_timeout(1500)
    return ctx, pg, errs, net

E = None
def st(pg): return pg.evaluate("()=>({view:window.TALABOT_WAITING_MAP_UI.read(),geo:GEO.state,title:(document.querySelector('.w-title h1')||{}).textContent,"
                                 "rec:!!$('w-recentre')&&$('w-recentre').disabled,me:document.querySelectorAll('#w-map .dmk.me').length,"
                                 "storeMk:document.querySelectorAll('#w-map .leaflet-marker-icon .dmk:not(.me)').length,maps:document.querySelectorAll('#w-map .leaflet-container').length,"
                                 "scripts:document.querySelectorAll('script[src*=\"leaflet@1.9.4\"]').length,watch:window.__watch,lc:window.__lc})")

with sync_playwright() as p:
    b = p.chromium.launch()
    src = open(os.path.join(root, 'assets/driver-tech/waiting-map.js')).read()
    ok('watchPosition' not in src.replace('No second watcher', '') and 'sendLocation' not in src and 'my_offers' not in src and 'rpc(' not in src,
       'provider: no own GPS watcher, no location write, no dispatch / server call')
    # 1) granted location, tiles OK
    for w in (360, 390, 430):
        ctx, pg, errs, net = page(b, width=w); s = st(pg)
        valid = pg.evaluate("()=>TLB.stores().filter(x=>x.lat!=null&&x.lng!=null&&isFinite(+x.lat)&&isFinite(+x.lng)&&!(+x.lat===0&&+x.lng===0)).length")
        ok(s['view'] == {'map': 'ready', 'nearby': 'ready'} and s['geo'] == 'ok' and s['me'] == 1 and s['maps'] == 1,
           '[%d] location granted: one Leaflet map, driver marker from GEO, map ready, nearby ready (%s)' % (w, s))
        ok(s['storeMk'] == valid and valid > 0, '[%d] restaurant markers = active restaurants with valid coordinates (%d/%d)' % (w, s['storeMk'], valid))
        ok(pg.evaluate("()=>[...document.querySelectorAll('#w-map .leaflet-marker-icon .dmk:not(.me)')].every(e=>!!e.querySelector('svg'))"), '[%d] restaurant markers carry the app store icon' % w)
        ok(not s['rec'] and s['title'] == 'Ожидаем заказ', '[%d] «my location» enabled; title «Ожидаем заказ»' % w)
        ok(s['watch'] == 1 and s['scripts'] == 1 and net['leaflet'] == 1, '[%d] one GEO watcher (the existing one), Leaflet loaded once' % w)
        ok(pg.evaluate("()=>document.documentElement.scrollWidth<=innerWidth"), '[%d] no horizontal overflow' % w)
        if w == 390:
            # driver marker centred in the uncovered strip (header bottom .. panel top), not behind the panel
            def centred():
                return pg.evaluate("()=>{const h=document.querySelector('.a-header').getBoundingClientRect().bottom,t=$('w-sheet').getBoundingClientRect().top,m=document.querySelector('#w-map .dmk.me').getBoundingClientRect();return [Math.round((m.top+m.bottom)/2),Math.round((h+t)/2)]}")
            inside = "()=>{const h=document.querySelector('.a-header').getBoundingClientRect().bottom,t=$('w-sheet').getBoundingClientRect().top;return [...document.querySelectorAll('#w-map .leaflet-marker-icon')].map(e=>{const r=e.getBoundingClientRect();return r.top>=h-2&&r.bottom<=t+2&&r.left>=0&&r.right<=innerWidth}).every(Boolean)}"
            ok(pg.evaluate(inside), 'first view: driver + every drawn restaurant inside the uncovered strip (header..panel), no radius applied')
            pg.evaluate("()=>wSnap('collapsed')"); pg.wait_for_timeout(700)
            ok(pg.evaluate(inside), 'panel collapsed: view re-fitted to the larger strip')
            pg.evaluate("()=>wSnap('default')"); pg.wait_for_timeout(700)
            ok(pg.evaluate(inside), 'panel back to default: all markers still in the strip')
            m = pg.locator('#w-map'); bx = m.bounding_box(); pg.mouse.move(bx['x'] + 150, bx['y'] + 120); pg.mouse.down(); pg.mouse.move(bx['x'] + 40, bx['y'] + 20, steps=8); pg.mouse.up(); pg.wait_for_timeout(300)
            c2 = centred(); ok(abs(c2[0] - c2[1]) > 30, 'user pan moves the map away (%s)' % c2)
            pg.evaluate("()=>wSnap('collapsed')"); pg.wait_for_timeout(700); pg.evaluate("()=>wSnap('default')"); pg.wait_for_timeout(700)
            c2b = centred(); ok(abs(c2b[0] - c2[0]) <= 2, 'after a pan, panel moves do not pull the map back (%s)' % c2b)
            pg.evaluate("()=>render()"); pg.wait_for_timeout(300); c3 = centred()
            ok(abs(c3[0] - c2[0]) <= 2, 're-render / GEO update does not pull the map back after a pan (%s)' % c3)
            pg.click('#w-recentre'); pg.wait_for_timeout(400); c4 = centred()
            ok(abs(c4[0] - c4[1]) <= 12, '«my location» re-centres on the real position in the visible strip (%s)' % c4)
            pg.evaluate("()=>wSnap('expanded')"); pg.wait_for_timeout(400); pg.click('#w-recentre', force=True) if not pg.locator('#w-recentre').is_disabled() else None
            pg.evaluate("()=>wSnap('default')"); pg.wait_for_timeout(300)
            # GEO update moves the marker (same marker, no new one)
            ctx.set_geolocation({'latitude': 38.58, 'longitude': 68.79, 'accuracy': 15}); pg.wait_for_timeout(1500)
            ll = pg.evaluate("()=>[GEO.lat,GEO.lng,document.querySelectorAll('#w-map .dmk.me').length]")
            ok(abs(ll[0] - 38.58) < 1e-6 and ll[2] == 1, 'new GPS reading from the existing watcher moves the one driver marker (%s)' % ll)
            # 2) lifecycle: history / profile / task / end of shift
            pg.evaluate("()=>aTab('h')"); pg.wait_for_timeout(300); s = st(pg)
            ok(not pg.locator('#w-map').count() and s['lc']['destroy'] == 1, 'history tab: waiting map destroyed and removed (%s)' % s['lc'])
            pg.evaluate("()=>aTab('o')"); pg.wait_for_timeout(800); s = st(pg)
            ok(s['lc']['mount'] == 2 and s['maps'] == 1 and s['scripts'] == 1 and net['leaflet'] == 1, 'back to orders: mounted once again, Leaflet not reloaded (%s)' % s['lc'])
            for i in range(5): pg.evaluate("()=>render()")
            pg.wait_for_timeout(200); s = st(pg)
            ok(s['lc']['mount'] == 2 and s['maps'] == 1, '5 re-renders: no new mount, no second map (%s)' % s['lc'])
            pg.evaluate("()=>aTab('m')"); pg.wait_for_timeout(300); ok(not pg.locator('#w-map').count(), 'profile tab: map removed')
            pg.evaluate("()=>aTab('o')"); pg.wait_for_timeout(600)
            pg.evaluate("()=>{online=false;stopGeo();render()}"); pg.wait_for_timeout(300); s = st(pg)
            ok(not pg.locator('#w-map').count() and s['lc']['destroy'] == s['lc']['mount'], 'end of shift: map destroyed (%s)' % s['lc'])
        ok(not errs, '[%d] no JS errors %s' % (w, errs[:2])); ctx.close()
    # 3) offline and back: last view kept, no «no restaurants», back to normal
    ctx, pg, errs, net = page(b)
    before = st(pg)
    pg.evaluate("()=>{window.__netFail=true;dispatchEvent(new Event('offline'))}"); pg.wait_for_selector('#tlb-off'); pg.wait_for_timeout(500); s = st(pg)
    ok(s['title'] == 'Нет соединения' and s['rec'] and s['maps'] == 1 and s['storeMk'] == before['storeMk'] and s['lc']['mount'] == 1,
       'offline: «Нет соединения», last map kept (same mount, markers kept), «my location» disabled (%s)' % s)
    pg.evaluate("()=>{window.__netFail=false;dispatchEvent(new Event('online'))}"); pg.wait_for_timeout(2500); s = st(pg)
    ok(s['title'] == 'Ожидаем заказ' and not s['rec'] and s['lc']['mount'] == 1, 'connection back: waiting state again, same map (%s)' % s)
    ok(not errs, 'offline: no JS errors %s' % errs[:2]); ctx.close()
    # 4) location denied
    ctx, pg, errs, net = page(b, geo='deny'); s = st(pg)
    ok(s['geo'] == 'denied' and s['title'] == 'Нет доступа к геопозиции' and s['me'] == 0 and s['rec'],
       'location denied: denied state, no driver marker, «my location» disabled (%s)' % s)
    ok(s['view']['nearby'] != 'empty', 'location denied is not shown as «no restaurants nearby»')
    ok(not errs, 'denied: no JS errors %s' % errs[:2]); ctx.close()
    # 5) location still loading
    ctx, pg, errs, net = page(b, geo='hang'); s = st(pg)
    ok(s['geo'] == 'wait' and s['title'] == 'Определяем местоположение…' and s['me'] == 0 and s['rec'] and s['view']['nearby'] == 'loading',
       'location loading: loading state, no marker, nothing invented (%s)' % s)
    ctx.close()
    # 6) no restaurant with coordinates: until D-W1 nothing says «none nearby» (no radius exists)
    ctx, pg, errs, net = page(b, stores="()=>TLB.stores(true).forEach(s=>{s.lat=null;s.lng=null})"); s = st(pg)
    txt = pg.evaluate("()=>document.body.innerText")
    ok(s['view']['nearby'] == 'ready' and s['title'] == 'Ожидаем заказ' and s['storeMk'] == 0 and s['me'] == 1 and 'Поблизости' not in txt and 'рядом' not in txt,
       'no restaurant with coordinates: no «Поблизости нет ресторанов», normal waiting state, no substitute point (%s)' % s)
    ok(pg.evaluate("()=>$('w-map').getAttribute('aria-label')") == 'Рестораны', 'map area is named «Рестораны» (not «nearby»)')
    ctx.close()
    # 7) invalid coordinates and inactive records are not drawn
    ctx, pg, errs, net = page(b, stores="()=>{const a=TLB.stores(true);a[0].lat=0;a[0].lng=0;a[1].lat='x';a[2].is_active=false}"); s = st(pg)
    exp = pg.evaluate("()=>TLB.stores().filter(x=>x.lat!=null&&x.lng!=null&&isFinite(+x.lat)&&isFinite(+x.lng)&&!(+x.lat===0&&+x.lng===0)).length")
    ok(s['storeMk'] == exp, '(0,0), non-numeric and inactive restaurants are not drawn (%d/%d)' % (s['storeMk'], exp))
    ctx.close()
    # 8) H8: tiles fail -> message + retry in the map area; offers / panel untouched; retry recovers
    FAILV = "()=>{const f=document.querySelector('#w-map .w-map-fail');if(!f||f.hidden)return null;const r=f.getBoundingClientRect(),h=document.querySelector('.a-header').getBoundingClientRect().bottom,t=$('w-sheet').getBoundingClientRect().top,btn=f.querySelector('button').getBoundingClientRect();return {text:f.innerText,inStrip:r.top>=h-2&&r.bottom<=t+2,btn:[btn.width,btn.height],btnVisible:btn.top>=h&&btn.bottom<=t}}"
    for w in (360, 390, 430):
        ctx, pg, errs, net = page(b, tiles='fail', width=w); pg.wait_for_timeout(1000); s = st(pg); f = pg.evaluate(FAILV)
        ok(s['view']['map'] == 'error' and s['rec'] and s['me'] == 1, '[%d] tiles fail: map «error», «my location» disabled, real marker kept (%s)' % (w, s['view']))
        ok(f and 'Карта не загрузилась' in f['text'] and 'Повторить' in f['text'] and f['inStrip'] and f['btnVisible'] and f['btn'][1] >= 44,
           '[%d] H8: «Карта не загрузилась» + «Повторить» (44px) inside the uncovered map strip (%s)' % (w, f))
        ok(s['title'] == 'Ожидаем заказ' and pg.locator('.nav').is_visible() and pg.locator('#w-sheet').is_visible(), '[%d] panel, shift and navigation unchanged' % w)
        if w == 390:
            pg.evaluate("()=>{window.__UI_OFFER=[{order_id:'ord1',mode:'broadcast',rank:1,dist_km:null,secs_left:3600}];TLB.reload()}"); pg.wait_for_timeout(1500)
            ok(pg.evaluate("()=>TLB.offers().length") == 1 and (pg.evaluate("()=>(document.querySelector('.w-title h1')||{}).textContent") == 'Новое предложение'),
               'with the map failed, a new offer still arrives in the panel')
            pg.evaluate("()=>{window.__UI_OFFER=[];TLB.reload()}"); pg.wait_for_timeout(1200)
            net['mode']['tiles'] = 'ok'; pg.click('#w-map .w-map-retry'); pg.wait_for_timeout(1500); s = st(pg)
            ok(s['view']['map'] == 'ready' and pg.evaluate(FAILV) is None and not s['rec'] and s['maps'] == 1 and s['lc']['mount'] == 1,
               'retry: tiles load, message gone, «my location» enabled, same map (no remount) (%s)' % s)
            net['mode']['tiles'] = 'fail'; pg.evaluate("()=>{const m=document.querySelector('#w-map .leaflet-container');}")
        ok(not errs, '[%d] tiles fail: no JS errors %s' % (w, errs[:2])); ctx.close()
    # Leaflet fails -> same message; retry after it becomes reachable builds the map once
    ctx, pg, errs, net = page(b, leaflet='fail'); s = st(pg); f = pg.evaluate(FAILV)
    ok(s['view']['map'] == 'error' and s['maps'] == 0 and s['rec'] and f and 'Повторить' in f['text'], 'Leaflet fails: message + retry, no map, button disabled (%s)' % s['view'])
    net['mode']['leaflet'] = 'ok'; pg.click('#w-map .w-map-retry'); pg.wait_for_timeout(2000); s = st(pg)
    ok(s['view']['map'] == 'ready' and s['maps'] == 1 and s['me'] == 1 and pg.evaluate(FAILV) is None and s['scripts'] == 1,
       'retry after Leaflet becomes reachable: one map built, message gone, one script tag (%s)' % s)
    ok(not errs, 'Leaflet fail: no JS errors %s' % errs[:2]); ctx.close()
    # connection returns while the map is in error: one automatic retry
    ctx, pg, errs, net = page(b, tiles='fail'); pg.wait_for_timeout(800); net['mode']['tiles'] = 'ok'
    pg.evaluate("()=>dispatchEvent(new Event('online'))"); pg.wait_for_timeout(1500); s = st(pg)
    ok(s['view']['map'] == 'ready' and pg.evaluate(FAILV) is None, 'connection back while in error: map retried by itself (%s)' % s['view'])
    ctx.close()
    b.close()
prot = subprocess.run(['git', 'diff', '--stat', 'ab8fd6c', '--', 'talabat-core.js', 'customer.html', 'admin.html', 'merchant.html', 'assets/driver-a/driver-a.css'], cwd=root, capture_output=True, text=True).stdout.strip()
ok(prot == '', 'core / customer / admin / merchant / driver A css unchanged by the binding (%s)' % (prot or 'no diff'))
dj = subprocess.run(['git', 'diff', '-U0', '--word-diff=porcelain', '--word-diff-regex=[^,{}]+', 'ab8fd6c', '--', 'assets/driver-a/driver-a.js'], cwd=root, capture_output=True, text=True).stdout
ch = sorted(l for l in dj.splitlines() if l[:1] in '+-' and not l.startswith(('+++', '---')))
ok(ch == sorted(["-wArea:'Карта рядом'", "+wArea:'Рестораны'", "-wEmpty:'Поблизости нет ресторанов'", "+wEmpty:'Рестораны не найдены'",
                 "-wArea:'Nearby map'", "+wArea:'Restaurants'", "-wEmpty:'No nearby restaurants'", "+wEmpty:'No restaurants found'"]),
   'driver-a.js: only the 4 «nearby» strings renamed (%s)' % ch)
print('\nWAITING MAP CHECK %s' % ('FAILS %d of %d' % (len(fails), n) if fails else 'OK (%d)' % n)); sys.exit(1 if fails else 0)
