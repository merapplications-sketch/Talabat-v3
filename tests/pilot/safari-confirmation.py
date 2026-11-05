"""NEW consent components only on native desktop Safari. No old 18 tests.
Uses actual app component functions and explicit UI boundary fixtures; NOT Auth/REST or iPhone.
"""
import importlib.util,json,os,threading,base64,zlib
from pathlib import Path
spec=importlib.util.spec_from_file_location('safari_base',Path(__file__).with_name('safari-smoke.py'));base=importlib.util.module_from_spec(spec);spec.loader.exec_module(base)
result={'source':os.environ.get('GITHUB_SHA'),'environment':'native Safari desktop/macOS15; actual new component source; explicit order/RPC UI fixtures','actual_iPhone':False,'actual_Auth_PostgREST':False,'live':False,'checks':[]};session=None
server=base.http.server.ThreadingHTTPServer(('127.0.0.1',8087),base.Handler);threading.Thread(target=server.serve_forever,daemon=True).start()
try:
 base.wait(lambda:base.wd('/status').get('ready'));created=base.wd('/session',{'capabilities':{'alwaysMatch':{'browserName':'safari'}}});session=created['sessionId'];root='/session/'+session;result['capabilities']=created['capabilities']
 def js(code):return base.wd(root+'/execute/sync',{'script':code,'args':[]})
 def ok(v,n):
  assert v,n
  result['checks'].append({'name':n,'pass':True});print('PASS Safari consent '+n,flush=True)
 base.wd(root+'/window/rect',{'width':430,'height':900});base.wd(root+'/url',{'url':'http://127.0.0.1:8087/customer.html?lang=en'});base.wait(lambda:js("return typeof approvalCard==='function'"))
 fixture={'id':70001,'status':'pending','total':65,'address':'SYNTHETIC Rudaki 1','approvalReady':True,'approval':{'state':'awaiting_customer','revision':3,'deadline':'2026-11-05T15:30:00Z','expired':False,'snapshot':{'total':75,'address':'SYNTHETIC Rudaki 1','prep_minutes':20,'lines':[{'name':'DEMO Meal','qty':2,'price':30}]}}}
 js("window.fixture="+json.dumps(fixture)+";document.querySelector('#tlb-ov')?.remove();TLB.lang=()=> 'en';window.render=()=>{document.querySelector('#app').innerHTML=approvalCard(fixture)};render();return true")
 if os.environ.get('SAFARI_SUMMARY_ONLY'):
  fixture['createdAt']=1793880000000;fixture['items']=[]
  js('window.fixture='+json.dumps(fixture)+';document.querySelector("#app").innerHTML=approvalCard(fixture)+orderSummary(fixture);return true')
  ok(js("return document.querySelector('.d6-order-summary h2').textContent==='Waiting for your approval' && document.querySelector('.d6-order-summary p').textContent.includes('restaurant confirmed')"),'order summary agrees with consent card after merchant review; no stale restaurant-wait message')
  ok(js('return document.documentElement.scrollWidth<=innerWidth+1'),'updated summary fits the native Safari window')
 else:
  ok(js("return document.querySelector('[data-revision=\"3\"]')?.textContent.includes('75 TJS') && document.querySelector('[data-confirm-order]').textContent==='Confirm and start preparation'"),'native Safari renders exact proposal revision, total and explicit consent action')
  js("fixture.approval.expired=true;render();return true");ok(js("return document.querySelector('[data-confirm-order]').disabled"),'expired consent is disabled on Safari without silent approval')
  js("fixture.approvalReady=false;render();return true");ok(js("return !!document.querySelector('[data-approval=\"unavailable\"] button') && !document.querySelector('[data-confirm-order]')"),'read failure exposes in-screen recovery and removes consent action')
  js("fixture.approvalReady=true;fixture.approval.expired=false;window.confirmCalls=[];TLB.confirmOrder=async(id,revision)=>{confirmCalls.push({id,revision});return {data:{}}};TLB.reload=async()=>{};render();document.querySelector('[data-confirm-order]').click();return true")
  base.wait(lambda:js('return !approvalBusy'));ok(js('return confirmCalls.length===1 && confirmCalls[0].revision===3'),'Safari forwards the displayed revision to the approval boundary')
  ok(js('return document.documentElement.scrollWidth<=innerWidth+1'),'consent card fits narrow native Safari window')
 raw=base.wd(root+'/screenshot');result['screenshot_png_base64']=raw;result['pass']=True
except Exception as e:result['pass']=False;result['error']=type(e).__name__+': '+str(e)[:200];print('FAIL Safari consent '+result['error'],flush=True)
finally:
 if session:
  try:base.wd('/session/'+session,method='DELETE')
  except Exception:pass
 server.shutdown();Path(__file__).with_name('result-safari-confirmation.json').write_text(json.dumps(result,indent=2)+'\n');print('SAFARI_CONFIRMATION_ZLIB_BASE64='+base64.b64encode(zlib.compress(json.dumps(result).encode())).decode(),flush=True)
if not result['pass']:raise SystemExit(1)
