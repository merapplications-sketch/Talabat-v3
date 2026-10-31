"""31 Oct limited fixes — LOCAL only (isolated fixtures, Chromium): (1) map chooser shows «loading» / «failed + retry»
instead of «road navigation disabled» while links are pending or failed; (2) a point shared in the chat opens the chooser
for exactly that point (driver) or a small choice sheet (customer) — Google is not forced; (3) no straight connector line
between the restaurant and customer pins. MAP_LEAFLET=<leaflet dist> python3 tools/map_points_check.py"""
import json, subprocess, sys
from pathlib import Path
from playwright.sync_api import sync_playwright
ROOT = Path(__file__).resolve().parents[1]
src = (ROOT / 'tools/navigation_ui_check.py').read_text(); g = {'__file__': str(ROOT / 'tools/navigation_ui_check.py')}
exec(compile(src.split('results=[]')[0], 'navigation_ui_check.py', 'exec'), g)
FIX, WRAP, DATA, LEAF, PNG = g['FIX'], g['WRAP'], g['DATA'], g['LEAF'], g['PNG']
EXTRA = """(function(){const old=supabase.createClient;supabase.createClient=function(){const c=old.apply(this,arguments),inv=c.functions.invoke;
 c.functions.invoke=async function(n,o){if(o.body.op==='links'){if(window.__linksHold)await new Promise(r=>window.__linksGo=r);if(window.__linksFail)return {data:null,error:{message:'offline'}}}return inv(n,o)};return c}})();"""
fails = []
def ok(c, m): print(('PASS ' if c else 'FAIL ') + m, flush=True); (None if c else fails.append(m))
def route(r):
    u = r.request.url
    if 'supabase-js' in u: r.fulfill(content_type='application/javascript', body=FIX + '\n' + WRAP + '\n' + EXTRA)
    elif 'leaflet.js' in u: r.fulfill(content_type='application/javascript', body=(LEAF / 'leaflet.js').read_text())
    elif 'leaflet.css' in u: r.fulfill(content_type='text/css', body=(LEAF / 'leaflet.css').read_text())
    elif 'tile.openstreetmap.org' in u: r.fulfill(content_type='image/png', body=PNG)
    elif u.startswith('http'): r.abort()
    else: r.continue_()
with sync_playwright() as pw:
    b = pw.chromium.launch()
    ctx = b.new_context(viewport={'width': 390, 'height': 844}, has_touch=True, is_mobile=True, permissions=['geolocation'], geolocation={'latitude': 38.56, 'longitude': 68.78, 'accuracy': 10})
    ctx.add_init_script("window.__UI_CASE='pickup';window.__NAV_DATA=" + json.dumps(DATA) + ";localStorage.setItem('tlb_lang','ru')")
    ctx.route('**/*', route); pg = ctx.new_page(); errs = []; pg.on('pageerror', lambda e: errs.append(str(e)))
    pg.goto((ROOT / 'driver.html').as_uri()); pg.wait_for_selector('#a-sheet')
    pg.wait_for_function("()=>typeof DM!=='undefined'&&DM&&DM!==1&&typeof DM.getCenter==='function'")
    pg.evaluate("window.__navMode='disabled';window.__linksHold=true"); pg.locator('.a-navigation').click(); pg.wait_for_timeout(400)
    t1 = pg.locator('.n-chooser').inner_text()
    ok('Загружаем' in t1 or 'Проверяем' in t1 or 'Загрузка' in t1 or pg.evaluate("t('nLoading')") in t1, 'links pending: «%s» shown, not «disabled»' % pg.evaluate("t('nLoading')"))
    ok(pg.evaluate("t('nDisabled')") not in t1, 'links pending: no «road navigation disabled» text')
    pg.evaluate("window.__linksFail=true;window.__linksGo()"); pg.wait_for_timeout(400)
    t2 = pg.locator('.n-chooser').inner_text()
    ok(pg.evaluate("t('nLinksFail')") in t2 and pg.get_by_role('button', name='Повторить').count() == 1, 'links failed: explicit failure + «Повторить»')
    pg.evaluate("window.__linksFail=false;window.__linksHold=false"); pg.get_by_role('button', name='Повторить').click(); pg.wait_for_timeout(500)
    ok(pg.locator('.n-provider').count() == 3, 'retry: the three providers appear (%d)' % pg.locator('.n-provider').count())
    pg.locator('.n-heading .round').click(); pg.wait_for_timeout(200)
    # chat point
    html = pg.evaluate("TLB.fmtMsg('LOC:38.566619,68.780465')")
    ok('google.com' not in html and 'openPoint' in html, 'chat point link no longer forces Google: %s' % html[:80])
    pg.evaluate("chatOpen=true;render()"); n0 = pg.evaluate("__navCalls.length")
    pg.evaluate("TLB.openPoint(38.566619,68.780465)"); pg.wait_for_timeout(500)
    t3 = pg.locator('.n-chooser').inner_text(); last = pg.evaluate("__navCalls.filter(c=>c.op==='links').pop()")
    ok('Точка из чата' in t3 and '38.566619, 68.780465' in t3 and last['to'] == [38.566619, 68.780465] and pg.locator('.n-provider').count() == 3,
       'chat point: same chooser, links for exactly that point %s' % last['to'])
    ok('Внутри TALABOT' not in t3, 'chat point: no internal route offer')
    pg.locator('.n-heading .round').click(); pg.wait_for_timeout(200)
    ok(pg.evaluate('chatOpen') is True, 'closing returns to the chat')
    # no straight connector
    pg.evaluate("chatOpen=false;render()"); pg.wait_for_timeout(300)
    lines = pg.evaluate("(()=>{let n=0;DM.eachLayer(l=>{if(l instanceof L.Polyline&&!(l instanceof L.Polygon))n++});return n})()")
    ok(lines == 0, 'no straight line between the pins (polylines on the map: %d)' % lines)
    ok(not errs, 'driver: no page errors %s' % errs[:2]); ctx.close()
    # customer: point sheet without the driver chooser, service unavailable -> coordinates to copy, no forced provider
    subprocess.run([sys.executable, str(ROOT / 'tools/ui_hc_fixture.py'), '/tmp/map-points-fixture'], check=True, capture_output=True)
    cf = Path('/tmp/map-points-fixture/customer-fixture.js').read_text()
    ctx = b.new_context(viewport={'width': 390, 'height': 760}); pg = ctx.new_page(); errs = []; pg.on('pageerror', lambda e: errs.append(str(e)))
    ctx.add_init_script("window.__C_SCENE='pickedup';localStorage.setItem('tlb_lang','ru')")
    ctx.route('**/*', lambda r: r.fulfill(content_type='application/javascript', body=cf) if 'supabase-js' in r.request.url else (r.abort() if r.request.url.startswith('http') else r.continue_()))
    pg.goto((ROOT / 'customer.html').as_uri()); pg.wait_for_function('()=>window.TLB&&TLB.order&&TLB.order("ord1")', timeout=20000)
    pg.evaluate("TLB.openPoint(38.566619,68.780465)"); pg.wait_for_timeout(600)
    sheet = pg.locator('#tlb-pt').inner_text()
    ok('38.566619, 68.780465' in sheet and 'Скопировать координаты' in sheet and pg.locator('#tlb-pt a[href*="google"]').count() == 0,
       'customer: point sheet with the coordinates and copy; no Google link when the map links are unavailable')
    pg.locator('#tlb-pt-x').click(); ok(pg.locator('#tlb-pt').count() == 0, 'customer: sheet closes')
    ok(pg.evaluate("TLB.openPoint(999,1)") is False and pg.locator('#tlb-pt').count() == 0, 'invalid point ignored')
    ok(not errs, 'customer: no page errors %s' % errs[:2]); b.close()
print('\nMAP POINTS CHECK %s' % ('FAILS %d' % len(fails) if fails else 'OK')); sys.exit(1 if fails else 0)
