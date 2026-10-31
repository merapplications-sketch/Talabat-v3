"""Geoapify attribution on the driver mission map (internal route) — LOCAL mock only, Chromium 360/390/430.
Reuses the navigation UI fixture (run node tools/navigation_contract_check.mjs first, then
MAP_LEAFLET=<leaflet dist dir> python3 tools/navigation_attribution_check.py). Checks: the «Powered by Geoapify» text is a
link to https://www.geoapify.com/, placed top-right of the visible map strip, not covered by the header or the sheet."""
import os, runpy, sys
from pathlib import Path
from playwright.sync_api import sync_playwright
ROOT = Path(__file__).resolve().parents[1]
src = (ROOT / 'tools/navigation_ui_check.py').read_text()
pre = src.split('results=[]')[0]                  # imports, fixture, WRAP stub — the consultant's harness, unchanged
g = {'__file__': str(ROOT / 'tools/navigation_ui_check.py')}; exec(compile(pre, 'navigation_ui_check.py', 'exec'), g)
FIX, WRAP, DATA, LEAF, PNG = g['FIX'], g['WRAP'], g['DATA'], g['LEAF'], g['PNG']
fails = []
def ok(c, m):
    print(('PASS ' if c else 'FAIL ') + m, flush=True)
    if not c: fails.append(m)
with sync_playwright() as pw:
    b = pw.chromium.launch()
    for width in (360, 390, 430):
        ctx = b.new_context(viewport={'width': width, 'height': 844}, has_touch=True, is_mobile=True, permissions=['geolocation'], geolocation={'latitude': 38.56, 'longitude': 68.78, 'accuracy': 10})
        ctx.add_init_script("window.__UI_CASE='pickup';window.__NAV_DATA=" + __import__('json').dumps(DATA) + ";localStorage.setItem('tlb_lang','ru')")
        def intercept(r):
            u = r.request.url
            if 'supabase-js' in u: r.fulfill(content_type='application/javascript', body=FIX + '\n' + WRAP)
            elif 'leaflet.js' in u: r.fulfill(content_type='application/javascript', body=(LEAF / 'leaflet.js').read_text())
            elif 'leaflet.css' in u: r.fulfill(content_type='text/css', body=(LEAF / 'leaflet.css').read_text())
            elif 'tile.openstreetmap.org' in u: r.fulfill(content_type='image/png', body=PNG)
            elif u.startswith('http'): r.abort()
            else: r.continue_()
        ctx.route('**/*', intercept); pg = ctx.new_page(); errs = []; pg.on('pageerror', lambda e: errs.append(str(e)))
        pg.goto((ROOT / 'driver.html').as_uri()); pg.wait_for_selector('#a-sheet')
        pg.wait_for_function("()=>typeof DM!=='undefined'&&DM&&DM!==1&&typeof DM.getCenter==='function'")
        pg.evaluate("()=>{const x=window.__UI_TABLES.orders.find(x=>x.id==='ord1');x.lat=40.27934;x.lng=69.6332017;Object.assign(GEO,{state:'ok',lat:38.56,lng:68.78,acc:10,at:Date.now()});TLB.reload()}")
        pg.locator('.a-navigation,.k-act-nav').click(); pg.wait_for_selector('.n-provider')
        pg.get_by_role('button', name='Внутри TALABOT', exact=True).click()
        pg.wait_for_function("()=>__routeLayer.state().mode==='internal'", timeout=10000)
        a = pg.evaluate("""()=>{const l=[...document.querySelectorAll('#dmap .leaflet-control-attribution a')].find(a=>/Geoapify/.test(a.textContent));if(!l)return null;
          const r=l.getBoundingClientRect(),hit=document.elementFromPoint(r.left+r.width/2,r.top+r.height/2),head=document.querySelector('.a-header,.hd'),sheet=document.getElementById('a-sheet');
          return {href:l.href,text:l.closest('.leaflet-control-attribution').textContent,top:Math.round(r.top),right:Math.round(r.right),hit:hit===l||l.contains(hit),
            belowHeader:!head||r.top>=head.getBoundingClientRect().bottom-1,aboveSheet:!sheet||r.bottom<=sheet.getBoundingClientRect().top+1,corner:l.closest('.leaflet-top.leaflet-right')!==null}}""")
        ok(a and a['href'] == 'https://www.geoapify.com/' and 'Powered by Geoapify' in a['text'], f'[{width}] «Powered by Geoapify» is a link to https://www.geoapify.com/ ({a and a["href"]})')
        ok(a and a['hit'] and a['belowHeader'] and a['aboveSheet'] and a['corner'], f'[{width}] link visible near the map: top-right of the visible strip, not covered (hit={a and a["hit"]})')
        ok(not errs, f'[{width}] no JS errors {errs[:1]}'); ctx.close()
    b.close()
print('\nNAVIGATION ATTRIBUTION CHECK %s' % ('FAILS %d' % len(fails) if fails else 'OK')); sys.exit(1 if fails else 0)
