"""Batch B (prepared, not deployed): street route on the driver mission map — LOCAL mock only.
Chromium + fixture, local Leaflet copy, local tiles, mocked geolocation; the Edge Function is replaced by a stub
(`functions.invoke('route')`) whose answers / failures are chosen by the test. Not proof of the real provider, iPhone or live.
  python3 tools/driver_route_check.py <leaflet_dist_dir>"""
import os, sys, base64, subprocess
from playwright.sync_api import sync_playwright
here = os.path.dirname(os.path.abspath(__file__)); root = os.path.abspath(os.path.join(here, '..'))
LEAF = sys.argv[1]; out = os.path.join(root, 'route-qa'); os.makedirs(out, exist_ok=True)
subprocess.run([sys.executable, os.path.join(here, 'driver_a_fixture.py'), out], check=True, capture_output=True)
FIX = open(os.path.join(out, 'review-fixture.js')).read()
PNG = base64.b64decode('iVBORw0KGgoAAAANSUhEUgAAAAEAAAABCAQAAAC1HAwCAAAAC0lEQVR42mP8/x8AAwMCAO+ip1sAAAAASUVORK5CYII=')
ME = {'latitude': 38.5600, 'longitude': 68.7700, 'accuracy': 20}      # near the demo restaurant (Dushanbe)
fails = []; n = 0
def ok(c, m):
    global n; n += 1; print(('PASS ' if c else 'FAIL ') + m, flush=True)
    if not c: fails.append(m)
STUB = """(function(){var val;Object.defineProperty(window,'supabase',{configurable:true,get:function(){return val},set:function(v){val=v;var cc=v.createClient;
 v.createClient=function(){var c=cc.apply(this,arguments);window.__rq=[];c.functions={invoke:function(name,o){window.__rq.push([name,o&&o.body]);var m=window.__routeMode||'none';
  if(m==='none')return Promise.reject(new Error('FunctionsFetchError'));if(m==='fail')return Promise.resolve({data:null,error:{message:'quota'}});
  var f=o.body.from,t=o.body.to,pts=[];for(var i=0;i<=30;i++){var k=i/30;pts.push([f[0]+(t[0]-f[0])*k+Math.sin(k*6)*0.002,f[1]+(t[1]-f[1])*k])}
  return Promise.resolve({data:{coords:pts,distance_m:4210,duration_s:611,source:'openrouteservice'},error:null})}};return c}}})})();"""
SPY = """(function(){window.__views=0;var val,depth=0;Object.defineProperty(window,'L',{configurable:true,get:function(){return val},set:function(v){val=v;if(!v||!v.Map||v.Map.__spy)return;v.Map.__spy=1;
 ['setView','fitBounds','flyTo','panTo','setZoom'].forEach(function(k){var f=v.Map.prototype[k];v.Map.prototype[k]=function(){if(!depth)window.__views++;depth++;try{return f.apply(this,arguments)}finally{depth--}}})}})})();"""
def page(b, mode):
    ctx = b.new_context(viewport={'width': 390, 'height': 844}, permissions=['geolocation'], geolocation=ME)
    def rt(r, q):
        u = q.url
        if 'supabase-js' in u: return r.fulfill(status=200, content_type='application/javascript', body=FIX)
        if 'leaflet.js' in u: return r.fulfill(status=200, content_type='application/javascript', body=open(os.path.join(LEAF, 'leaflet.js')).read())
        if 'leaflet.css' in u: return r.fulfill(status=200, content_type='text/css', body=open(os.path.join(LEAF, 'leaflet.css')).read())
        if 'tile.openstreetmap' in u: return r.fulfill(status=200, content_type='image/png', body=PNG)
        if u.startswith('http'): return r.abort()
        return r.continue_()
    ctx.route('**/*', rt)
    ctx.add_init_script("window.__UI_CASE='orders';window.__routeMode=%r;localStorage.setItem('tlb_lang','ru');window.fetch=()=>Promise.resolve(new Response('',{status:200}));" % mode + STUB + SPY)
    pg = ctx.new_page(); errs = []; pg.on('pageerror', lambda e: errs.append(str(e)))
    pg.goto('file://' + root + '/driver.html'); pg.wait_for_function("()=>typeof DRV!=='undefined'&&!!DRV")
    pg.evaluate("()=>{const o=window.__UI_TABLES.orders.find(x=>x.id==='ord1');o.lat=38.5701;o.lng=68.7905;TLB.reload()}"); pg.wait_for_timeout(800)   # the order pin (fixture had none)
    pg.evaluate("()=>{online=true;startGeo();render()}"); pg.wait_for_timeout(1500)
    pg.evaluate("()=>aSelect(TLB.offers()[0].id)"); pg.wait_for_timeout(2500)
    return ctx, pg, errs
ST = "()=>({route:document.querySelectorAll('#dmap path.a-route').length,straight:[...document.querySelectorAll('#dmap path')].filter(p=>!p.classList.contains('a-route')&&!p.classList.contains('w-acc')&&p.getAttribute('stroke-dasharray')).length,label:(document.getElementById('a-map-state')||{}).textContent,rq:(window.__rq||[]).filter(x=>x[0]==='route').length,views:window.__views,nav:(document.querySelector('.a-navigation')||{}).href||''})"
with sync_playwright() as p:
    b = p.chromium.launch()
    # 1) function not deployed (today): nothing changes, straight line + its honest label
    ctx, pg, errs = page(b, 'none'); s = pg.evaluate(ST)
    ok(s['route'] == 0 and s['straight'] >= 1 and 'не дорожный' in (s['label'] or ''), 'not deployed: straight line and «не дорожный маршрут» kept (%s)' % s)
    ok(not errs, 'not deployed: no JS errors %s' % errs[:2]); ctx.close()
    # 2) route available
    ctx, pg, errs = page(b, 'ok'); s = pg.evaluate(ST)
    ok(s['route'] == 1 and s['straight'] == 0, 'route: street line drawn, straight line removed (%s)' % s)
    ok(s['label'] == 'По дорогам: 4,2 км · ~10 мин', 'route: distance and estimated minutes from the route source (%r)' % s['label'])
    sent = pg.evaluate("()=>window.__rq[0][1]")
    ok(abs(sent['from'][0] - ME['latitude']) < 1e-9 and sent['to'] == pg.evaluate("()=>storePt(aTask().store)"), 'route asked from the real driver position to the restaurant point (%s)' % sent)
    v0, r0 = s['views'], s['rq']
    for d in (0.0003, 0.0006, 0.0009):     # small moves inside 120 s: no new request, no re-framing
        ctx.set_geolocation({'latitude': ME['latitude'] + d, 'longitude': ME['longitude'], 'accuracy': 20}); pg.wait_for_timeout(700)
    for i in range(5): pg.evaluate("()=>render()"); pg.wait_for_timeout(100)
    s = pg.evaluate(ST)
    ok(s['rq'] == r0 and s['route'] == 1, 'GPS updates / renders within 120 s: no new route request, line kept (%d requests)' % s['rq'])
    ok(s['views'] == v0, 'route drawing never re-frames the map (%d -> %d)' % (v0, s['views']))
    pg.evaluate("()=>aRun()"); pg.wait_for_timeout(2500); s = pg.evaluate(ST)
    ok(s['rq'] == r0 + 1 and s['route'] == 1, 'stage change (accepted): one new request for the new leg (%d)' % s['rq'])
    sp = pg.evaluate("()=>storeLL(aTask().store)")
    ok('maps/dir/' in s['nav'] and ('destination=' + sp) in s['nav'], '«Навигатор»: directions link to the same restaurant point (%s)' % s['nav'][:110])
    pg.evaluate("()=>{const o=aTask();window.__pinNav=pt(o)}"); pv = pg.evaluate("()=>window.__pinNav")
    ok(pv and 'maps/dir/' in pv and 'destination=38.5701,68.7905' in pv, 'customer leg: directions link to the exact order pin (%s)' % pv)
    ok(not errs, 'route: no JS errors %s' % errs[:2]); ctx.close()
    # 3) provider fails (quota / down): straight line + honest label, no error shown as a route
    ctx, pg, errs = page(b, 'fail'); s = pg.evaluate(ST)
    ok(s['route'] == 0 and s['straight'] >= 1 and 'не дорожный' in (s['label'] or ''), 'provider fails: straight line + «не дорожный маршрут» (%s)' % s)
    ok(not errs, 'fail: no JS errors %s' % errs[:2]); ctx.close()
    b.close()
print('\nDRIVER ROUTE CHECK %s' % ('FAILS %d of %d' % (len(fails), n) if fails else 'OK (%d)' % n)); sys.exit(1 if fails else 0)
