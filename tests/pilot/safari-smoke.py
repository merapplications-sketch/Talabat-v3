"""Native macOS Safari UI smoke with explicitly synthetic SDK, not hosted Auth.
No external resources: the fixture replaces the CDN SDK and all app network URLs.
New coverage is recovery UI on the actual Safari engine; not iPhone acceptance.
"""
import base64, http.server, json, os, pathlib, re, subprocess, threading, time, urllib.request, urllib.error, zlib
ROOT=pathlib.Path(__file__).resolve().parents[2]
HERE=pathlib.Path(__file__).parent
SDK='''window.__authCalls=[];window.supabase={createClient:function(url,key,options){window.__storageKey=options.auth.storageKey;return {auth:{getSession:function(){return Promise.resolve({data:{session:location.search.indexOf('fixture_existing=1')>=0?{user:{id:'synthetic-existing'}}:null}})},onAuthStateChange:function(){return {data:{subscription:{unsubscribe:function(){}}}}},resetPasswordForEmail:function(email,options){window.__authCalls.push({operation:'recover',email:email,redirect:options.redirectTo});return Promise.resolve({data:{},error:null})}}}}};'''
class Handler(http.server.BaseHTTPRequestHandler):
 def log_message(self,*args):pass
 def do_GET(self):
  path=self.path.split('?')[0]
  if path=='/fixture-sdk.js':data=SDK.encode();mime='application/javascript'
  elif path in ['/customer.html','/merchant.html','/driver.html','/admin.html','/talabat-core.js']:
   text=(ROOT/path[1:]).read_text()
   if path.endswith('.html'):text=re.sub(r'https://cdn\.jsdelivr\.net/npm/@supabase/supabase-js@[^"\']+/dist/umd/supabase\.js','/fixture-sdk.js',text)
   # No installed client can send traffic to the real backend.
   text=text.replace('https://dzydscryrnahnneydnry.supabase.co','http://127.0.0.1:8087').replace('wss://dzydscryrnahnneydnry.supabase.co','ws://127.0.0.1:8087')
   data=text.encode();mime='text/html'if path.endswith('.html')else'application/javascript'
  else:self.send_error(404);return
  self.send_response(200);self.send_header('Content-Type',mime+';charset=utf-8');self.send_header('Content-Security-Policy',"default-src 'self'; script-src 'self' 'unsafe-inline'; style-src 'self' 'unsafe-inline'; img-src 'self' data: blob:; connect-src 'self'; font-src 'self'");self.send_header('Content-Length',str(len(data)));self.end_headers();self.wfile.write(data)

def wd(path,body=None,method=None):
 req=urllib.request.Request('http://127.0.0.1:4444'+path,data=json.dumps(body).encode()if body is not None else None,headers={'Content-Type':'application/json'},method=method)
 try:
  with urllib.request.urlopen(req,timeout=90 if path=='/session' else 30)as response:value=json.loads(response.read())['value']
 except urllib.error.HTTPError as e:raise RuntimeError('webdriver_http_'+str(e.code))from None
 if isinstance(value,dict)and value.get('error'):raise RuntimeError('webdriver_'+value['error'])
 return value

def wait(fn):
 end=time.monotonic()+25
 while time.monotonic()<end:
  if fn():return
  time.sleep(.2)
 raise TimeoutError('condition')

def main():
 result={'source':os.environ.get('GITHUB_SHA'),'environment':'native Safari WebDriver on standard GitHub macOS15 runner; synthetic SDK only','actual_iPhone':False,'actual_Auth_PostgREST':False,'live':False,'checks':[]};session=None
 server=http.server.ThreadingHTTPServer(('127.0.0.1',8087),Handler);threading.Thread(target=server.serve_forever,daemon=True).start()
 try:
  result['stage']='driver_status';wait(lambda:wd('/status').get('ready'));result['stage']='create_browser_session'
  created=wd('/session',{'capabilities':{'alwaysMatch':{'browserName':'safari'}}});session=created['sessionId'];result['stage']='application_navigation';result['capabilities']=created['capabilities'];base='/session/'+session
  script=lambda code:wd(base+'/execute/sync',{'script':code,'args':[]})
  def ok(value,name):
   assert value,name
   result['checks'].append({'name':name,'pass':True});print('PASS Safari '+name,flush=True)
  def element(css):return wd(base+'/element',{'using':'css selector','value':css})['element-6066-11e4-a52e-4f735466cecf']
  def click(css):wd(base+'/element/'+element(css)+'/click',{})
  wd(base+'/window/rect',{'width':430,'height':900})
  for app,role in [('customer','customer'),('merchant','merchant'),('driver','driver'),('admin','admin')]:
   wd(base+'/url',{'url':'http://127.0.0.1:8087/'+app+'.html?lang=en'});wait(lambda:script("return !!document.querySelector('#tlb-forgot')"))
   ok(script("return window.__storageKey")=='tlb-auth-'+role,app+' retains separate role session key and recovery entry')
   click('#tlb-forgot');wait(lambda:script("return !!document.querySelector('#tlb-rem')"))
   ok(script("return getComputedStyle(document.querySelector('#tlb-ov')).display==='flex' && getComputedStyle(document.querySelector('#tlb-ov > div:last-child')).backgroundColor==='rgb(255, 255, 255)'"),app+' original inline styles remain active under unmodified app CSP')
   wd(base+'/element/'+element('#tlb-rem')+'/value',{'text':'demo@synthetic.invalid'})
   click('#tlb-rgo');wait(lambda:script("return document.querySelector('#tlb-rsent').hidden===false"))
   ok(script("return window.__authCalls.length===1 && window.__authCalls[0].redirect===location.origin+location.pathname"),app+' reset targets the same app; one SDK request')
   ok(script("return document.documentElement.scrollWidth<=innerWidth+1"),app+' recovery screen fits narrow desktop window')
  raw=wd(base+'/screenshot');png=HERE/'.runtime-safari.png';png.write_bytes(base64.b64decode(raw));jpg=HERE/'.runtime-safari.jpg'
  subprocess.run(['sips','-s','format','jpeg','--setProperty','formatOptions','55','-Z','900',str(png),'--out',str(jpg)],check=True,stdout=subprocess.DEVNULL)
  result['screenshot_jpeg_base64']=base64.b64encode(jpg.read_bytes()).decode()
  wd(base+'/url',{'url':'http://127.0.0.1:8087/customer.html?lang=en#type=recovery'});wait(lambda:script("return !!document.querySelector('#tlb-forgot')"))
  ok(script("return !document.querySelector('#tlb-newpw') && document.querySelector('#tlb-er').textContent.length>0"),'recovery marker without session cannot open password update form')
  wd(base+'/url',{'url':'http://127.0.0.1:8087/customer.html?lang=en&fixture_existing=1#type=recovery'});wait(lambda:script("return !!document.querySelector('#tlb-forgot')"))
  ok(script("return !document.querySelector('#tlb-newpw') && document.querySelector('#tlb-er').textContent.length>0"),'untrusted recovery marker cannot target an existing signed-in fixture identity')
  result['pass']=True
 except Exception as e:
  result['pass']=False;result['error']=str(e)[:160];log=HERE/'.runtime-safaridriver.log';result['driver_diagnostics']=log.read_text()[-3500:]if log.exists()else'unavailable';print('FAIL Safari '+result['stage']+' '+result['error'],flush=True)
 finally:
  if session:
   try:wd('/session/'+session,method='DELETE')
   except Exception:pass
  server.shutdown();(HERE/'result-safari-desktop.json').write_text(json.dumps(result,indent=2)+'\n')
  print('SAFARI_RESULT_ZLIB_BASE64='+base64.b64encode(zlib.compress(json.dumps(result).encode())).decode(),flush=True)
 if not result['pass']:raise SystemExit(1)
if __name__=='__main__':main()
