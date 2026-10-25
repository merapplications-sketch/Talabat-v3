"""Build ONE review-only navigation preview from this branch. No real GPS, DB, provider, credentials or payments.
Run navigation_contract_check.mjs first; output is docs/driver-handoff/navigation-review.html.
"""
from pathlib import Path
import json,re,subprocess,sys,runpy
ROOT=Path(__file__).resolve().parents[1];TMP=Path('/tmp/talabot-navigation-preview');TMP.mkdir(exist_ok=True)
subprocess.run([sys.executable,str(ROOT/'tools/driver_a_fixture.py'),str(TMP)],check=True,capture_output=True)
fixture=(TMP/'review-fixture.js').read_text();data=json.loads(Path('/tmp/talabot-navigation-fixture.json').read_text())
# Reuse the same function-contract fixture as the navigation UI checks, without executing those tests.
source=(ROOT/'tools/navigation_ui_check.py').read_text();wrapper=source.split("WRAP='''",1)[1].split("'''",1)[0]
def script(s):return '<script>'+s.replace('</script','<\\/script')+'</script>'
s=(ROOT/'driver.html').read_text()
s=re.sub(r'<script>if\(window.top!==window.self\).*?</script>','',s,count=1)
# The export only may run in its review iframe. Production CSP and frame guard are untouched.
s=s.replace('<meta charset="UTF-8">','<meta charset="UTF-8"><base href="../../">')
setup="window.__UI_CASE='pickup';window.__NAV_DATA="+json.dumps(data,ensure_ascii=False)+";localStorage.setItem('tlb_lang','ru');window.fetch=()=>Promise.resolve(new Response('',{status:200}));"
s=s.replace('<script src="https://cdn.jsdelivr.net/npm/@supabase/supabase-js@2.117.2/dist/umd/supabase.js"></script>',script(setup)+script(fixture)+script(wrapper),1)
s=re.sub(r'<script src="talabat-core\.js[^"]*"></script>',lambda m:script((ROOT/'talabat-core.js').read_text()),s,count=1)
css=(ROOT/'assets/driver-a/driver-a.css').read_text();css=re.sub(r"url\('([^']+)'\)",lambda m:"url('assets/driver-a/"+m[1]+"')",css)
s=s.replace('<link rel="stylesheet" href="assets/driver-a/driver-a.css">','<style>'+css+'</style>')
for path in ['assets/driver-tech/waiting-map.js','assets/driver-a/driver-a.js','assets/driver-tech/map-view.js','assets/driver-tech/navigation-model.js','assets/driver-tech/route-layer.js']:
 s=s.replace('<script src="'+path+'"></script>',script((ROOT/path).read_text()))
# Keep preview offline from tiles as well. Leaflet library/fonts/logo still load from ordinary public/static assets.
s=s.replace('https://tile.openstreetmap.org/{z}/{x}/{y}.png','data:image/png;base64,iVBORw0KGgoAAAANSUhEUgAAAAEAAAABCAQAAAC1HAwCAAAAC0lEQVR42mP8/x8AAwMCAO+ip1sAAAAASUVORK5CYII=')
post='''
(function(){
 const demoFix=()=>({coords:{latitude:38.56,longitude:68.78,accuracy:10},timestamp:Date.now()});
 Object.defineProperty(navigator,'geolocation',{configurable:true,value:{watchPosition:f=>{f(demoFix());return 1},getCurrentPosition:f=>f(demoFix()),clearWatch:()=>{}}});
 async function refresh(){if(!window.TLB?.me())return;const o=window.__UI_TABLES.orders.find(x=>x.id==='ord1');o.lat=40.27934;o.lng=69.6332017;Object.assign(GEO,{state:'ok',lat:38.56,lng:68.78,acc:10,at:Date.now()});await TLB.reload();}
 const timer=setInterval(()=>{if(window.TLB?.me()){clearInterval(timer);refresh();}},100);
 setInterval(()=>{GEO.at=Date.now();},1000);
 window.addEventListener('message',async e=>{if(e.source!==parent||!['internal','disabled','quota','fail','customer'].includes(e.data))return;
  if(e.data==='customer'){const o=window.__UI_TABLES.orders.find(x=>x.id==='ord1');o.status='pickedup';o.arrived_cust_at=null;await TLB.reload();}
  else{window.__navMode=e.data;window.__navVersion++;await __routeLayer.refreshPolicy();if(e.data!=='disabled')aNavigationInside();render();}
 });
})();
'''
s=s.replace('</body>',script(post)+'</body>')
encoded=json.dumps(s,ensure_ascii=False).replace('</','<\\/')
html='''<!doctype html><html lang="ar" dir="rtl"><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1"><title>TALABOT — معاينة الملاحة المعزولة</title><style>*{box-sizing:border-box}body{margin:0;background:#eef1f5;font:13px system-ui;color:#17243c}header{height:70px;padding:8px;display:flex;align-items:center;justify-content:center;gap:12px;flex-wrap:wrap}select{font:inherit;padding:7px;border-radius:8px}iframe{display:block;border:0;width:100%;height:calc(100dvh - 70px);max-width:430px;margin:auto;background:white}</style><header><span>محاكاة فقط · بلا GPS أو قاعدة بيانات أو مزوّد حي</span><select id="state"><option value="internal">ملاحة داخلية</option><option value="disabled">تتبّع فقط / تعطيل الطرق</option><option value="quota">نفاد الحصة</option><option value="fail">فشل الخدمة</option><option value="customer">بعد الاستلام: وجهة الزبون</option></select></header><iframe id="review" title="معاينة TALABOT المعزولة"></iframe><script>const f=document.getElementById('review');f.srcdoc='''+encoded+''';document.getElementById('state').onchange=e=>f.contentWindow.postMessage(e.target.value,'*');</script></html>'''
p=ROOT/'docs/driver-handoff/navigation-review.html';p.write_text(html);print(str(p),p.stat().st_size)
