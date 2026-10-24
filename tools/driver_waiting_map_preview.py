"""Export ONE self-contained review page of the driver waiting map — never loaded by the app.
   python3 tools/driver_waiting_map_preview.py <out_dir>
What is real in the page: driver.html + talabat-core.js + driver A + assets/driver-tech/waiting-map.js of this branch,
the phone's own location (browser permission, the app's existing GEO watcher), Leaflet 1.9.4 and OSM tiles.
What is demo: the database. The Supabase client is replaced by the repo's test fixture (tools/driver_a_fixture.py):
no account, no request to the database (the connection probe is answered from navigator.onLine), every action stays
in memory. Demo restaurants keep the fixture's coordinates (Dushanbe). One demo offer arrives 25 s after «start shift»
(fixture my_offers), to see the panel with an offer. Nothing else is changed: no map drawing, no fake location."""
import base64, json, re, subprocess, sys
from pathlib import Path
ROOT = Path(__file__).resolve().parents[1]
out = Path(sys.argv[1]); out.mkdir(parents=True, exist_ok=True)
subprocess.run([sys.executable, str(ROOT / 'tools/driver_a_fixture.py'), str(out)], check=True, capture_output=True)
fixture = (out / 'review-fixture.js').read_text()
def script(s): return '<script>' + s.replace('</script', '<\\/script') + '</script>'
def data(p):
    mime = {'.woff2': 'font/woff2', '.png': 'image/png', '.svg': 'image/svg+xml'}[p.suffix]
    return 'data:' + mime + ';base64,' + base64.b64encode(p.read_bytes()).decode()
A = ROOT / 'assets/driver-a'
css = (A / 'driver-a.css').read_text()
css = re.sub(r"url\('([^']+)'\)", lambda m: "url('" + data(A / m[1]) + "')", css)
js = (A / 'driver-a.js').read_text().replace('assets/driver-a/brand/TALABOT-Original-RU.png', data(A / 'brand/TALABOT-Original-RU.png'))
s = (ROOT / 'driver.html').read_text()
pre = """window.__UI_CASE='empty';try{localStorage.setItem('tlb_lang',localStorage.getItem('tlb_lang')||'ru')}catch(e){}
/* demo only: the connection probe never reaches the database; it follows the phone's real connection state */
(function(){var f=window.fetch;window.fetch=function(u,o){if(String(u).indexOf('supabase.co')>=0)return navigator.onLine?Promise.resolve(new Response('',{status:200})):Promise.reject(new TypeError('offline'));return f.apply(this,arguments)}})();"""
post = """(function(){var go=startShift;startShift=async function(){var r=await go.apply(this,arguments);clearTimeout(window.__demoOffer);
 window.__demoOffer=setTimeout(function(){window.__UI_OFFER=[{order_id:'ord1',mode:'broadcast',rank:1,dist_km:null,secs_left:3600}];try{TLB.reload&&TLB.reload()}catch(e){}},25000);return r}})();
(function(){var b=document.createElement('div');b.textContent='\\u0414\\u0435\\u043c\\u043e-\\u0434\\u0430\\u043d\\u043d\\u044b\\u0435 \\u00b7 GPS \\u0438 \\u043a\\u0430\\u0440\\u0442\\u0430 \\u0440\\u0435\\u0430\\u043b\\u044c\\u043d\\u044b\\u0435';
 b.style.cssText='position:fixed;left:8px;bottom:calc(84px + env(safe-area-inset-bottom,0px));z-index:5;font:600 10px/14px system-ui;background:#17243cd0;color:#fff;padding:3px 8px;border-radius:8px;pointer-events:none';document.body.appendChild(b)})();"""
s = s.replace('<script src="https://cdn.jsdelivr.net/npm/@supabase/supabase-js@2.117.2/dist/umd/supabase.js"></script>', script(pre) + script(fixture), 1)
s = re.sub(r'<script src="talabat-core\.js[^"]*"></script>', lambda m: script((ROOT / 'talabat-core.js').read_text()), s, count=1)
s = s.replace('<script src="assets/driver-tech/waiting-map.js"></script>', script((ROOT / 'assets/driver-tech/waiting-map.js').read_text()), 1)
s = s.replace('<script src="assets/driver-a/driver-a.js"></script>', script(js) + script(post), 1)
s = s.replace('<link rel="stylesheet" href="assets/driver-a/driver-a.css">', '<style>' + css + '</style>', 1)
# CSP of the export only: fonts / logo are embedded as data:, so allow data: fonts. Nothing else opened.
s = s.replace("img-src 'self' data: blob: https:;", "img-src 'self' data: blob: https:; font-src 'self' data:;", 1)
s = re.sub(r'<title>[^<]*</title>', '<title>TALABOT Waiting Map</title>', s, count=1)
assert 'supabase-js' not in s and 'src="talabat-core' not in s and 'src="assets/' not in s
(out / 'TALABOT-Driver-Waiting-Map-Preview.html').write_text(s)
print('preview:', out / 'TALABOT-Driver-Waiting-Map-Preview.html', len(s) // 1024, 'KB')
