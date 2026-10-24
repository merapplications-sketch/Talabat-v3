"""Build one isolated H+C review from current source and supplied designer preview shells.
Usage: python3 tools/ui_hc_review.py H_PREVIEW C_PREVIEW OUT_DIR
Demo fixtures/map rendering remain in this export only. No deployment or database access.
"""
from pathlib import Path
import re,json,base64,sys
root=Path(__file__).resolve().parents[1];out=Path(sys.argv[3]);out.mkdir(parents=True,exist_ok=True)
def extract(p,key):
 s=Path(p).read_text();m=re.search('const '+key+'=',s);assert m;return json.JSONDecoder().raw_decode(s[m.end():])[0]
H=extract(sys.argv[1],'TEMPLATES');C=extract(sys.argv[2],'TEMPLATE')
def data(p):
 mime={'.png':'image/png','.woff2':'font/woff2','.svg':'image/svg+xml'}[p.suffix]
 return 'data:'+mime+';base64,'+base64.b64encode(p.read_bytes()).decode()
def controller(role):return next(s for s in re.findall(r'<script[^>]*>(.*?)</script>',(root/(role+'.html')).read_text(),re.S) if ('let DLV=' if role=='driver' else 'let S=') in s)
def css_driver():return re.sub(r"url\('([^']+)'\)",lambda m:"url('"+data(root/'assets/driver-a'/m[1])+"')",(root/'assets/driver-a/driver-a.css').read_text())
def update(template,role):
 def scripts(m):
  s=m[1]
  if s.startswith('/* talabat-core.js'):s=(root/'talabat-core.js').read_text()
  elif ('let DLV=' if role=='driver' else 'let S=') in s:s=controller(role)
  elif role=='driver' and 'function aSheet(' in s:s=(root/'assets/driver-a/driver-a.js').read_text().replace('assets/driver-a/brand/TALABOT-Original-RU.png',data(root/'assets/driver-a/brand/TALABOT-Original-RU.png'))
  elif s.startswith('/* TALABOT driver — mission map view policy'):s=(root/'assets/driver-tech/map-view.js').read_text()
  if '/* Local proposed delta.' in s:
   a=s.index('/* Local proposed delta.');b=s.index("document.addEventListener('click',e=>",a)
   s=s[:a]+(root/'assets/customer-c/customer-c.js').read_text()+'\n'+s[b:]
  return '<script>'+s.replace('</script','<\\/script')+'</script>'
 template=re.sub(r'<script>(.*?)</script>',scripts,template,flags=re.S)
 if role=='driver':template=re.sub(r'<style>(@font-face.*?)</style>',lambda m:'<style>'+css_driver()+'</style>',template,flags=re.S)
 else:
  src=(root/'customer.html').read_text();base=re.search(r'<style>(.*?)</style>',src,re.S)[1]
  template=re.sub(r'<style>.*?</style>',lambda m:'<style>'+base+'</style>',template,count=1,flags=re.S)
  # C stylesheet in supplied preview is a separate style; replace it if present.
  template=re.sub(r'<style>/\* C1/C2 only.*?</style>',lambda m:'<style>'+(root/'assets/customer-c/customer-c.css').read_text()+'</style>',template,flags=re.S)
 return template
templates={};views={}
for k,desc in {'driverPreparing':'H7/H9/H12 · تجهيز السائق','driverReady':'H7/H9 · جاهز للاستلام','driverUnset':'H12 · مدة غير محددة','store':'H4 · ملاحظة المطعم','customerPreparing':'H13 · تجهيز طلب الزبون','customerUnset':'H13 · مدة غير محددة','customerReady':'H13 · الطلب جاهز','copy':'H11 · صياغة رسائل الخريطة'}.items():
 role='driver' if k.startswith('driver') else 'copy' if k=='copy' else 'customer'
 templates[k]=update(H['proposed:'+role],role).replace('__VIEW__',k) if role!='copy' else H['proposed:copy'];views[k]=desc
for k,desc in {'point':'C1 · موقع متاح','older':'C1 · وقت سابق ظاهر','none':'C1 · موقع غير متاح','loading':'C1 · انتظار الموقع','mapFail':'C1 · تعذر الخريطة','browse':'C2 · طلب واحد','browseCart':'C2 · مع السلة','browseMulti':'C2 · عدة طلبات'}.items():templates[k]=update(C,'customer').replace('__CASE__',k);views[k]=desc
options=''.join('<option value="'+k+'">'+v+'</option>' for k,v in views.items())
shell='''<!doctype html><html lang="ar" dir="rtl"><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1"><title>TALABOT · H+C applied</title><style>body{margin:0;background:#e8ebef;color:#17243c;font:14px/1.6 system-ui}header{padding:12px;text-align:center}select{font:16px system-ui;min-height:44px;margin:4px;padding:8px;border:1px solid #ccd1d8;border-radius:10px}p{margin:4px}#phone{margin:8px auto 24px;width:390px;height:844px}iframe{width:100%;height:100%;border:0;background:white}.zone{direction:ltr;overflow:auto}</style><header><b>TALABOT · حزمة H وإضافتا C1/C2 المطبّقة</b><p>معاينة محلية معزولة · الخريطة وبيانات الموقع Demo · لا اتصال بقاعدة حقيقية</p><p>القراءة بحساب الزبون والآيفون لم تُتحقق · B1 وB2 معلّقان</p><select id="view">OPTIONS</select><select id="width"><option>360</option><option selected>390</option><option>430</option></select></header><div class="zone"><div id="phone"><iframe id="frame" title="TALABOT H+C"></iframe></div></div><script>const TEMPLATES=JSON;function load(){document.getElementById('phone').style.width=document.getElementById('width').value+'px';document.getElementById('frame').srcdoc=TEMPLATES[document.getElementById('view').value]}document.getElementById('view').onchange=load;document.getElementById('width').onchange=load;load();</script></html>'''
(out/'TALABOT-H-C-Applied-Preview.html').write_text(shell.replace('OPTIONS',options).replace('JSON',json.dumps(templates,ensure_ascii=False).replace('<','\\u003c')))
print('One H+C review exported from current source; Demo map/fixtures export-only')
