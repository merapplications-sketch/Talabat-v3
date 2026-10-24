"""Map stability (iPhone report 24 Oct: the map jumped and re-zoomed by itself) — LOCAL mock only.
Chromium + repo fixture, local Leaflet 1.9.4 copy, local 1-px tiles, mocked browser geolocation. Every programmatic view change
(setView / fitBounds / flyTo / panTo / setZoom) of every Leaflet map is counted. Waiting map and mission map (offer opened):
renders, GPS readings, offer countdown, panel snaps and viewport height changes (Safari toolbar) must cause 0 view changes;
first display / task change frame once; user pan / wheel zoom is kept until «my location» / aMapRecenter().
  python3 tools/driver_map_stability_check.py <leaflet_dist_dir>"""
import os, sys, base64, subprocess
from playwright.sync_api import sync_playwright
here = os.path.dirname(os.path.abspath(__file__)); root = os.path.abspath(os.path.join(here, '..'))
LEAF = sys.argv[1]; out = os.path.join(root, 'map-stability-qa'); os.makedirs(out, exist_ok=True)
subprocess.run([sys.executable, os.path.join(here, 'driver_a_fixture.py'), out], check=True, capture_output=True)
FIX = open(os.path.join(out, 'review-fixture.js')).read()
PNG = base64.b64decode('iVBORw0KGgoAAAANSUhEUgAAAAEAAAABCAQAAAC1HAwCAAAAC0lEQVR42mP8/x8AAwMCAO+ip1sAAAAASUVORK5CYII=')
TAS = {'latitude': 41.2995, 'longitude': 69.2401, 'accuracy': 35}     # the iPhone test place; demo restaurants are in Dushanbe
fails = []; n = 0
def ok(c, m):
    global n; n += 1; print(('PASS ' if c else 'FAIL ') + m, flush=True)
    if not c: fails.append(m)
# count programmatic view changes on every L.Map (installed as soon as Leaflet is evaluated)
SPY = """(function(){window.__views=[];var depth=0,val;function spy(L){if(!L||!L.Map||L.Map.__spy)return;L.Map.__spy=1;
 ['setView','fitBounds','flyTo','panTo','setZoom','flyToBounds'].forEach(function(k){var f=L.Map.prototype[k];L.Map.prototype[k]=function(){
   if(!depth){var c=this.getContainer();window.__views.push([k,(c.parentNode&&c.parentNode.id==='w-map')?'w-map':c.id,Date.now()])}   /* top-level calls only (fitBounds calls setView inside) */
   depth++;try{return f.apply(this,arguments)}finally{depth--}}})}
 Object.defineProperty(window,'L',{configurable:true,get:function(){return val},set:function(v){val=v;try{spy(v)}catch(e){}}})})();"""

def page(b, case='empty', width=390, height=844):
    ctx = b.new_context(viewport={'width': width, 'height': height}, permissions=['geolocation'], geolocation=TAS)
    def rt(r, q):
        u = q.url
        if 'supabase-js' in u: return r.fulfill(status=200, content_type='application/javascript', body=FIX)
        if 'leaflet.js' in u: return r.fulfill(status=200, content_type='application/javascript', body=open(os.path.join(LEAF, 'leaflet.js')).read())
        if 'leaflet.css' in u: return r.fulfill(status=200, content_type='text/css', body=open(os.path.join(LEAF, 'leaflet.css')).read())
        if 'tile.openstreetmap' in u: return r.fulfill(status=200, content_type='image/png', body=PNG)
        if u.startswith('http'): return r.abort()
        return r.continue_()
    ctx.route('**/*', rt)
    ctx.add_init_script("window.__UI_CASE=%r;localStorage.setItem('tlb_lang','ru');window.fetch=()=>Promise.resolve(new Response('',{status:200}));" % case + SPY)
    pg = ctx.new_page(); errs = []; pg.on('pageerror', lambda e: errs.append(str(e)))
    pg.goto('file://' + root + '/driver.html'); pg.wait_for_function("()=>typeof DRV!=='undefined'&&!!DRV")
    pg.evaluate("()=>{online=true;startGeo();render()}"); pg.wait_for_timeout(2500)
    return ctx, pg, errs
PANEL = """(sel)=>new Promise(res=>{const out=[];const t0=performance.now();(function f(){const e=document.querySelector(sel);out.push(e?Math.round(e.getBoundingClientRect().top):null);
 if(performance.now()-t0<5000)requestAnimationFrame(f);else res([...new Set(out)])})()})"""
def views(pg, since=0): return pg.evaluate("(s)=>(window.__views||[]).slice(s)", since)
def nviews(pg): return pg.evaluate("()=>(window.__views||[]).length")
def churn(pg, ctx, sel_snap):
    """everything that ran on each render before the fix: renders, GPS readings, countdown, panel snaps, Safari toolbar"""
    for i in range(6): pg.evaluate("()=>render()"); pg.wait_for_timeout(120)
    for d in (0.02, 0.04, 0.06):   # ~2-7 km: visible as a marker move even at the wide Tashkent-Dushanbe zoom
        ctx.set_geolocation({'latitude': TAS['latitude'] + d, 'longitude': TAS['longitude'] + d, 'accuracy': 30}); pg.wait_for_timeout(700)
    pg.wait_for_timeout(2500)                                   # offer countdown / periodic sections
    for snap in ('collapsed', 'expanded', 'default'): pg.evaluate(sel_snap % snap); pg.wait_for_timeout(450)
    for h in (760, 700, 844): pg.set_viewport_size({'width': 390, 'height': h}); pg.wait_for_timeout(450)   # Safari toolbar shows / hides

with sync_playwright() as p:
    b = p.chromium.launch()
    # ---------- waiting map ----------
    ctx, pg, errs = page(b, 'empty')
    first = views(pg)
    ok(len(first) >= 1 and all(v[1] == 'w-map' for v in first) and len(first) <= 2, 'waiting: first display frames the map once (%d view calls: %s)' % (len(first), [v[0] for v in first]))
    me0 = pg.evaluate("()=>{const r=document.querySelector('#w-map .dmk.me').getBoundingClientRect();return [r.left,r.top]}")
    k = nviews(pg); churn(pg, ctx, "()=>wSnap('%s')")
    v = views(pg, k)
    ok(not v, 'waiting: renders + 3 GPS readings + countdown + panel snaps + toolbar heights -> 0 view changes (%s)' % v)
    me1 = pg.evaluate("()=>{const r=document.querySelector('#w-map .dmk.me').getBoundingClientRect();return [r.left,r.top,GEO.lat]}")
    ok(abs(me1[2] - (TAS['latitude'] + 0.06)) < 1e-9 and (abs(me1[0] - me0[0]) > 0.5 or abs(me1[1] - me0[1]) > 0.5), 'waiting: GPS readings move only the marker (%s -> %s)' % (me0, me1))
    # panel jump: each render rebuilt the panel at its CSS top (460) and slid it up; sampled every frame for 5 s, no touch
    pg.evaluate("()=>{window.__UI_OFFER=[{order_id:'ord1',mode:'broadcast',rank:1,dist_km:null,secs_left:3600}];TLB.reload()}"); pg.wait_for_timeout(2500)
    tops = pg.evaluate(PANEL, '#w-sheet'); ok(len(tops) == 1, 'waiting panel with an offer: one position for 5 s of renders (frames: %s)' % tops)
    pg.evaluate("()=>{window.__UI_OFFER=[];TLB.reload()}"); pg.wait_for_timeout(2500)
    # offer arrives while waiting: panel grows, view stays
    k = nviews(pg); pg.evaluate("()=>{window.__UI_OFFER=[{order_id:'ord1',mode:'broadcast',rank:1,dist_km:null,secs_left:3600}];TLB.reload()}"); pg.wait_for_timeout(2500)
    ok(pg.evaluate("()=>(document.querySelector('.w-title h1')||{}).textContent") == 'Новое предложение' and not views(pg, k), 'waiting: an offer arrives -> panel changes, 0 view changes (%s)' % views(pg, k))
    # user zoom (wheel) is kept through GPS / renders / resize; «my location» brings the driver back
    k = nviews(pg); box = pg.locator('#w-map .leaflet-container').bounding_box()
    pg.mouse.move(box['x'] + 200, box['y'] + 150); pg.mouse.wheel(0, -400); pg.wait_for_timeout(900)
    z0 = pg.evaluate("()=>{const r=document.querySelector('#w-map .dmk.me').getBoundingClientRect();return [Math.round(r.left),Math.round(r.top)]}")
    k2 = nviews(pg); churn(pg, ctx, "()=>wSnap('%s')")
    ok(not views(pg, k2), 'waiting: after a user zoom, GPS / renders / panel / toolbar do not re-frame (%s)' % views(pg, k2))
    k3 = nviews(pg); pg.click('#w-recentre'); pg.wait_for_timeout(500); rv = views(pg, k3)
    ok(len(rv) == 1 and rv[0][0] == 'setView', '«Моё местоположение»: exactly one view change, on request (%s)' % rv)
    ok(not errs, 'waiting: no JS errors %s' % errs[:2]); ctx.close()
    # ---------- mission map (offer opened) ----------
    ctx, pg, errs = page(b, 'orders')
    pg.evaluate("()=>aSelect(TLB.offers()[0].id)"); pg.wait_for_timeout(2500)
    first = [x for x in views(pg) if x[1] == 'dmap']
    tops = pg.evaluate(PANEL, '#a-sheet'); ok(len(tops) == 1, 'mission panel: one position for 5 s of renders (frames: %s)' % tops)
    pg.click('#a-grip'); tops = pg.evaluate(PANEL, '#a-sheet'); ok(len(tops) > 2, 'mission panel: a tap on the grip still animates (frames: %d)' % len(tops))
    pg.click('#a-grip'); pg.click('#a-grip'); pg.wait_for_timeout(400)
    ok(1 <= len(first) <= 4, 'mission: first display frames the map (%d calls: %s)' % (len(first), [x[0] for x in first]))
    k = nviews(pg); churn(pg, ctx, "()=>aSnap('%s')")
    v = [x for x in views(pg, k) if x[1] == 'dmap']
    ok(not v, 'mission: renders + 3 GPS readings + countdown + sheet snaps + toolbar heights -> 0 view changes (%s)' % [x[0] for x in v])
    mk = pg.evaluate("()=>{const m=document.querySelector('#dmap .dmk.me');return !!m}")
    ok(mk, 'mission: own marker still drawn after GPS readings')
    # user pan kept
    box = pg.locator('#dmap').bounding_box(); pg.mouse.move(box['x'] + 200, box['y'] + 200); pg.mouse.down(); pg.mouse.move(box['x'] + 120, box['y'] + 140, steps=8); pg.mouse.up(); pg.wait_for_timeout(500)
    k = nviews(pg); churn(pg, ctx, "()=>aSnap('%s')")
    ok(not [x for x in views(pg, k) if x[1] == 'dmap'], 'mission: after a user pan, GPS / renders / sheet / toolbar keep the user view')
    k = nviews(pg); pg.evaluate("()=>aMapRecenter()"); pg.wait_for_timeout(400)
    ok(len([x for x in views(pg, k) if x[1] == 'dmap']) == 1, 'mission: aMapRecenter() frames once on request')
    # task change: back to the list, another offer id would be a new key; here stage change of the same order via accept
    k = nviews(pg); pg.evaluate("()=>{const x=aTask();aRun()}"); pg.wait_for_timeout(2500)
    st2 = pg.evaluate("()=>aTask()?aTaskStage(aTask()):null"); v = [x for x in views(pg, k) if x[1] == 'dmap']
    ok(st2 == 1 and 1 <= len(v) <= 4, 'mission: stage change (accepted) frames once for the new stage (stage %s, %d calls)' % (st2, len(v)))
    k = nviews(pg); churn(pg, ctx, "()=>aSnap('%s')")
    ok(not [x for x in views(pg, k) if x[1] == 'dmap'], 'mission (new stage): GPS / renders / sheet / toolbar -> 0 view changes')
    ok(not errs, 'mission: no JS errors %s' % errs[:2]); ctx.close()
    b.close()
print('\nMAP STABILITY CHECK %s' % ('FAILS %d of %d' % (len(fails), n) if fails else 'OK (%d)' % n)); sys.exit(1 if fails else 0)
