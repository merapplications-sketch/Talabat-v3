"""Integration check for f2f2999 (shared core pickLocation): the OTHER, two-argument caller — the customer's
«here» delivery point (sheetHere) — still opens, waits for GPS, confirms into S.tmp and cancels cleanly.
LOCAL only: repo fixture, local Leaflet, mocked geolocation. python3 tools/address_picker_caller_check.py"""
import subprocess, sys
from pathlib import Path
from playwright.sync_api import sync_playwright
sys.path.insert(0, str(Path(__file__).parent)); import driver_journey_r1_check as S
ROOT = S.ROOT; fails = []
def ok(c, m): print(('PASS ' if c else 'FAIL ') + m, flush=True); (None if c else fails.append(m))
subprocess.run([sys.executable, str(ROOT/'tools/ui_hc_fixture.py'), '/tmp/addr-picker-fixture'], check=True, capture_output=True)
fixture = Path('/tmp/addr-picker-fixture/customer-fixture.js').read_text()
with sync_playwright() as pw:
    b = pw.chromium.launch(); ctx = b.new_context(viewport={'width': 390, 'height': 716}, has_touch=True, is_mobile=True)
    pg = ctx.new_page(); errs = []; pg.on('pageerror', lambda e: errs.append(str(e)))
    pg.add_init_script("localStorage.setItem('tlb_lang','ru');Object.defineProperty(navigator,'geolocation',{value:{getCurrentPosition:(ok,fail)=>{window.__geoOK=ok;window.__geoFail=fail}}});")
    def route(r):
        u = r.request.url
        if 'supabase-js' in u: r.fulfill(content_type='application/javascript', body=fixture)
        elif 'leaflet.js' in u: r.fulfill(content_type='application/javascript', body=(S.LEAF/'leaflet.js').read_text())
        elif 'leaflet.css' in u: r.fulfill(content_type='text/css', body=(S.LEAF/'leaflet.css').read_text())
        elif 'tile.openstreetmap.org' in u: r.fulfill(content_type='image/png', body=S.PNG)
        elif u.startswith('http'): r.abort()
        else: r.continue_()
    ctx.route('**/*', route); pg.goto((ROOT/'customer.html').as_uri()); S.wait(pg, '()=>!!ME?.phone')
    pg.evaluate('sheetHere()'); pg.wait_for_selector('#tlb-me')
    ok('Определяем' in pg.locator('#tlb-lm').inner_text(), 'address picker (2-arg caller) opens and asks for GPS without hooks')
    pg.evaluate('__geoOK({coords:{latitude:38.5601,longitude:68.7871}})'); pg.wait_for_timeout(300)
    pg.locator('#tlb-ls').click(); pg.wait_for_timeout(300)
    t = pg.evaluate('S.tmp')
    ok(t and abs(t['lat'] - 38.5601) < 1e-4 and abs(t['lng'] - 68.7871) < 1e-4 and pg.evaluate('S.useTmp') and pg.locator('#tlb-map').count() == 0,
       'confirm stores the delivery point in S.tmp and closes the picker (%s)' % (t and [t['lat'], t['lng']]))
    pg.evaluate("S.tmp=null;S.useTmp=false;sheetHere()"); pg.wait_for_selector('#tlb-lx'); pg.locator('#tlb-lx').click(); pg.wait_for_timeout(300)
    ok(pg.locator('#tlb-map').count() == 0 and pg.evaluate('S.tmp') is None, 'cancel closes without a point')
    ok(not errs, 'no page errors %s' % errs[:2]); b.close()
print('\nADDRESS PICKER CALLER CHECK %s' % ('FAILS %d' % len(fails) if fails else 'OK')); sys.exit(1 if fails else 0)
