"""Export one offline review HTML from current driver/core; never loaded by the app."""
from pathlib import Path
import base64, html, json, re, subprocess, sys
ROOT=Path(__file__).resolve().parents[1]
out=Path(sys.argv[1]);out.mkdir(parents=True,exist_ok=True)
subprocess.run([sys.executable,str(ROOT/'tools/driver_a_fixture.py'),str(out)],check=True)
fixture=(out/'review-fixture.js').read_text()
# Override only the local fixture's amounts, before its simulated client initializes.
fixture=fixture.replace("window.__UI_OFFER=", "Object.assign(main,{total:90,points_value:10,wallet_used:15});\n window.__UI_OFFER=",1)
guard="""window.__reviewOffline=false;window.fetch=()=>window.__reviewOffline?Promise.reject(new TypeError('review offline')):Promise.resolve(new Response('',{status:200}));
window.addEventListener('message',e=>{if(e.data==='review-offline'||e.data==='review-online'){window.__reviewOffline=e.data==='review-offline';window.dispatchEvent(new Event(window.__reviewOffline?'offline':'online'))}});
"""
def script(s):return '<script>'+s.replace('</script','<\\/script')+'</script>'
def data(p):
    mime={'.woff2':'font/woff2','.png':'image/png','.svg':'image/svg+xml'}[p.suffix]
    return 'data:'+mime+';base64,'+base64.b64encode(p.read_bytes()).decode()
css=(ROOT/'assets/driver-a/driver-a.css').read_text()
css=re.sub(r"url\('([^']+)'\)",lambda m:"url('"+data(ROOT/'assets/driver-a'/m[1])+"')",css)
s=(ROOT/'driver.html').read_text()
s=re.sub(r'<meta http-equiv="Content-Security-Policy"[^>]*>', '<meta http-equiv="Content-Security-Policy" content="default-src \'none\'; script-src \'unsafe-inline\'; style-src \'unsafe-inline\'; img-src data: blob:; font-src data:; connect-src \'none\'; base-uri \'none\'; form-action \'none\'">',s)
s=s.replace("<script>if(window.top!==window.self){document.documentElement.style.display='none';try{window.top.location=window.self.location}catch(e){}}</script>",'')
s=s.replace('<link rel="stylesheet" href="assets/driver-a/driver-a.css">','<style>'+css+'</style>')
s=re.sub(r'<script src="https://cdn.jsdelivr.net/npm/@supabase/supabase-js@[^\"]+"></script>',lambda m:script(fixture+guard),s)
s=re.sub(r'<script src="talabat-core.js[^\"]*"></script>',lambda m:script((ROOT/'talabat-core.js').read_text()),s)
adapter=(ROOT/'assets/driver-a/driver-a.js').read_text().replace('assets/driver-a/brand/TALABOT-Original-RU.png',data(ROOT/'assets/driver-a/brand/TALABOT-Original-RU.png'))
s=s.replace('<script src="assets/driver-a/driver-a.js"></script>',script(adapter))
shell='''<!doctype html><html lang="ar" dir="rtl"><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1"><title>TALABOT v82 · H review</title><style>body{font:14px system-ui;margin:0;background:#e8ebef;color:#17243c}header{padding:12px;text-align:center;background:white}button,select{font:inherit;padding:7px;margin:3px}iframe{display:block;margin:12px auto;border:1px solid #ccd1d8;background:white;width:390px;max-width:100%;height:844px}p{margin:4px}</style><header><b>السائق A · تصحيحات H1/H2/H3/H6 · معاينة معزولة</b><p>بيانات تجريبية فقط · دون ربط حي أو خريطة/GPS · الشاشات الأخرى ما زالت للمراجعة</p><select id="scenario"><option value="delivery">H1/H6 · عند الزبون</option><option value="pickup">H1/H6 · عند المطعم</option><option value="orders">H1/H6 · قبل القبول</option><option value="pending">H3 · انتظار التسليم</option></select><select id="width"><option>360</option><option selected>390</option><option>430</option></select><select id="lang"><option value="ru">RU</option><option value="en">EN</option></select><button id="off">H2 · انقطاع</button><button id="on">عودة الاتصال</button></header><iframe id="view" sandbox="allow-scripts allow-same-origin allow-modals" title="Driver review"></iframe><script>const source=SOURCE;const view=document.getElementById('view');function load(){const c=document.getElementById('scenario').value,l=document.getElementById('lang').value;let init="window.__UI_CASE="+JSON.stringify(c==='pending'?'delivery':c)+";localStorage.setItem('tlb_lang',"+JSON.stringify(l)+");";let end="if(typeof DRV!=='undefined'&&DRV){online=true;render();}";if(c==='pending')end+="window.__UI_DELAY=120000;aRun();confirmDeliver();";view.srcdoc=source.replace('<head>','<head><script>'+init+'<\\/script>').replace('</body>','<script>setTimeout(()=>{'+end+'},700)<\\/script></body>')}document.getElementById('scenario').onchange=load;document.getElementById('lang').onchange=load;document.getElementById('width').onchange=e=>view.style.width=e.target.value+'px';document.getElementById('off').onclick=()=>view.contentWindow.postMessage('review-offline','*');document.getElementById('on').onclick=()=>view.contentWindow.postMessage('review-online','*');load();</script></html>'''
(out/'TALABOT-v82-Driver-H-Preview.html').write_text(shell.replace('SOURCE',json.dumps(s,ensure_ascii=False).replace('</script','<\\/script')))
print('Offline review exported; source CSP and services unchanged')
