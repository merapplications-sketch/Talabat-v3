"""One isolated Driver A review, external navigation only; never contacts Supabase/GPS/maps services."""
from pathlib import Path
import sys, subprocess, json, re, base64, os
ROOT=Path(__file__).resolve().parents[1]
OUT=Path('/tmp/talabot-driver-polish');OUT.mkdir(exist_ok=True)
subprocess.run([sys.executable,str(ROOT/'tools/driver_a_fixture.py'),str(OUT)],check=True,capture_output=True)
FIX=(OUT/'review-fixture.js').read_text()
# UI doubles only. Production links still come solely from route.
WRAP="""
(function(){const old=supabase.createClient;supabase.createClient=function(){const c=old.apply(this,arguments);window.__navCalls=[];
 const config={internal:false,external:true,providers:['yandex','2gis','google'],mode:'tracking',reason:'disabled',configTtlMs:30000};
 c.functions={invoke:async function(name,opt){const b=opt.body;window.__navCalls.push(b);if(b.op==='config')return {data:config,error:null};
 if(b.op==='links'){const p=b.to,xy=encodeURIComponent(p.join(',')),yx=p[1]+','+p[0];const y='https://yandex.ru/maps/?rtext=~'+xy+'&rtt=auto',d='https://2gis.ru/directions/tab/car/points/|'+yx,g='https://www.google.com/maps/dir/?api=1&destination='+xy+'&travelmode=driving&dir_action=navigate';return {data:{config,links:[{id:'yandex',name:'Yandex Maps',app:y.replace('https://yandex.ru/maps/','yandexmaps://maps.yandex.ru/'),web:y},{id:'2gis',name:'2GIS',app:d,web:d},{id:'google',name:'Google Maps',app:g,web:g}]},error:null};}throw Error('Internal routes forbidden in review');}};return c;}})();
"""
def script(x):return '<script>'+x.replace('</script','<\\/script')+'</script>'
s=(ROOT/'driver.html').read_text()
s=re.sub(r'<script>if\(window.top!==window.self\).*?</script>','',s,count=1)
s=s.replace('<script src="https://cdn.jsdelivr.net/npm/@supabase/supabase-js@2.117.2/dist/umd/supabase.js"></script>',script("window.__UI_CASE='pickup';localStorage.setItem('tlb_lang','ru');window.fetch=()=>Promise.reject(Error('Review offline'));"+FIX+WRAP))
s=re.sub(r'<script src="talabat-core\.js[^"]*"></script>',lambda m:script((ROOT/'talabat-core.js').read_text()),s,count=1)
css=(ROOT/'assets/driver-a/driver-a.css').read_text()
css=re.sub(r"url\('([^']+)'\)",lambda m:"url('data:font/woff2;base64,"+base64.b64encode((ROOT/'assets/driver-a'/m[1]).read_bytes()).decode()+"')",css)
s=s.replace('<link rel="stylesheet" href="assets/driver-a/driver-a.css">','<style>'+css+'</style>')
for path in ['assets/driver-tech/waiting-map.js','assets/driver-a/driver-a.js','assets/driver-tech/map-view.js','assets/driver-tech/navigation-model.js','assets/driver-tech/route-layer.js']:
 s=s.replace('<script src="'+path+'"></script>',script((ROOT/path).read_text()))
logo='data:image/png;base64,'+base64.b64encode((ROOT/'assets/driver-a/brand/TALABOT-Original-RU.png').read_bytes()).decode()
s=s.replace('assets/driver-a/brand/TALABOT-Original-RU.png',logo)
# Actual Leaflet interactions, blank offline tiles clearly identified by the review shell.
leaf=Path(os.environ.get('MAP_LEAFLET','/tmp/talabot-leaflet'))
s=s.replace('</head>','<style>'+(leaf/'leaflet.css').read_text()+'</style>'+script((leaf/'leaflet.js').read_text())+'</head>')
s=s.replace('https://tile.openstreetmap.org/{z}/{x}/{y}.png','data:image/png;base64,iVBORw0KGgoAAAANSUhEUgAAAAEAAAABCAQAAAC1HAwCAAAAC0lEQVR42mP8/x8AAwMCAO+ip1sAAAAASUVORK5CYII=')
post="""
(function(){Object.defineProperty(navigator,'geolocation',{configurable:true,value:{watchPosition:()=>1,getCurrentPosition:()=>{},clearWatch:()=>{}}});
 let timer=setInterval(async()=>{if(!window.TLB?.me())return;clearInterval(timer);const x=__UI_TABLES.orders.find(x=>x.id==='ord1');x.lat=38.58;x.lng=68.80;Object.assign(GEO,{state:'ok',lat:38.56,lng:68.78,acc:10,at:Date.now()});await TLB.reload();},50);
 window.addEventListener('message',async e=>{if(e.source!==parent)return;
 if(e.data==='pickup'||e.data==='customer'){const x=__UI_TABLES.orders.find(x=>x.id==='ord1');x.status=e.data==='pickup'?'ready':'pickedup';x.arrived_cust_at=null;await TLB.reload();}
 if(e.data==='collapsed'||e.data==='expanded'||e.data==='default')aSnap(e.data);
 if(e.data==='nav')aNavigationOpen();});})();
"""
s=s.replace('</body>',script(post)+'</body>')
encoded=json.dumps(s,ensure_ascii=False).replace('</','<\\/')
h='''<!doctype html><html lang="ar" dir="rtl"><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1"><title>TALABOT — تشطيب السائق A</title><style>*{box-sizing:border-box}body{margin:0;background:#e8ebef;font:12px system-ui;color:#17243c}header{padding:8px;min-height:80px;display:flex;align-items:center;justify-content:center;gap:6px;flex-wrap:wrap}button{font:inherit;padding:8px;border:1px solid #d9dee7;border-radius:8px;background:white}iframe{display:block;width:100%;max-width:430px;height:calc(100dvh - 100px);min-height:480px;margin:auto;border:0;background:white}</style><header><span>معاينة معزولة · بيانات تجريبية وخريطة بلاط فارغ · لا GPS أو خادم أو دفع</span><button data-action="pickup">قبل الاستلام</button><button data-action="customer">بعد الاستلام</button><button data-action="collapsed">طيّ</button><button data-action="expanded">توسعة</button><button data-action="nav">الملاحة</button></header><iframe id="review" title="تشطيب السائق A المعزول"></iframe><script>const f=document.getElementById('review');f.srcdoc='''+encoded+''';document.querySelectorAll('[data-action]').forEach(b=>b.onclick=()=>f.contentWindow.postMessage(b.dataset.action,'*'));</script></html>'''
p=ROOT/'docs/driver-handoff/navigation-review.html';p.write_text(h);print(p)
