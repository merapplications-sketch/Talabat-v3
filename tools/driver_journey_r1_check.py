"""Affected R1 integration checks: actual driver/core with isolated service doubles.
Browser viewport is available APP space after explicit simulated browser bars (44+84px).
No real iPhone/Safari/GPS/provider/account/order writes. MAP_LEAFLET points to local Leaflet JS/CSS.
"""
from pathlib import Path
import os,sys,subprocess,json,time,base64,ast
from playwright.sync_api import sync_playwright
ROOT=Path(__file__).resolve().parents[1];OUT=Path(os.environ.get('JOURNEY_OUT','/tmp/talabot-driver-r1'));OUT.mkdir(exist_ok=True)
subprocess.run([sys.executable,str(ROOT/'tools/driver_a_fixture.py'),str(OUT)],check=True,capture_output=True)
FIX=(OUT/'review-fixture.js').read_text()
# Reuse the pre-existing external-only UI double. No live function or CORS tests repeated.
tree=ast.parse((ROOT/'tools/driver_polish_preview.py').read_text());WRAP=next(ast.literal_eval(n.value) for n in tree.body if isinstance(n,ast.Assign) and any(isinstance(t,ast.Name) and t.id=='WRAP' for t in n.targets))
LEAF=Path(os.environ.get('MAP_LEAFLET','/workspace/scratch/72a93aea6c2a/hc-evidence/leaflet'))
PNG=base64.b64decode('iVBORw0KGgoAAAANSUhEUgAAAAEAAAABCAQAAAC1HAwCAAAAC0lEQVR42mP8/x8AAwMCAO+ip1sAAAAASUVORK5CYII=')
results=[];metrics=[]
def check(v,msg):
 if not v:raise AssertionError(msg)
 results.append(msg);print('PASS',msg,flush=True)
def wait(p,fn):
 end=time.monotonic()+12
 while time.monotonic()<end:
  if p.evaluate(fn):return
  p.wait_for_timeout(60)
 raise AssertionError(fn)
def settle(p):p.wait_for_timeout(100)
def boot(browser,width,height,case='offer'):
 ctx=browser.new_context(viewport={'width':width,'height':height},is_mobile=True,has_touch=True,user_agent='Mozilla/5.0 (iPhone; CPU iPhone OS 18_7 like Mac OS X) AppleWebKit/605.1.15 Version/18.0 Mobile/15E148 Safari/604.1')
 ctx.add_init_script("window.__UI_CASE="+json.dumps(case)+";localStorage.setItem('tlb_lang','ru');window.fetch=()=>Promise.reject(Error('isolated UI'));")
 def route(r):
  u=r.request.url
  if 'supabase-js' in u:r.fulfill(content_type='application/javascript',body=FIX+'\n'+WRAP)
  elif 'leaflet.js' in u:r.fulfill(content_type='application/javascript',body=(LEAF/'leaflet.js').read_text())
  elif 'leaflet.css' in u:r.fulfill(content_type='text/css',body=(LEAF/'leaflet.css').read_text())
  elif 'tile.openstreetmap.org' in u:r.fulfill(content_type='image/png',body=PNG)
  elif u.startswith('http'):r.abort()
  else:r.continue_()
 ctx.route('**/*',route);p=ctx.new_page();errors=[];p.on('pageerror',lambda e:errors.append(str(e)));p.goto((ROOT/'driver.html').as_uri());wait(p,'()=>!!DRV');p.evaluate('online=true;render()');p.wait_for_selector('#a-sheet');wait(p,"()=>typeof DM!=='undefined'&&DM&&DM!==1&&typeof DM.getCenter==='function'")
 p.evaluate("async()=>{const x=__UI_TABLES.orders.find(x=>x.id==='ord1');x.lat=38.58;x.lng=68.80;Object.assign(GEO,{state:'ok',lat:38.56,lng:68.78,acc:10,at:Date.now()});await TLB.reload()}");settle(p)
 return ctx,p,errors
def visible_layout(p):
 return p.evaluate("""()=>{const sels=['.a-stages','.a-target','.a-journey-offer-route','.a-journey-money','.a-tools','#swp','.a-accessible'];let boxes={};for(const s of sels){const e=document.querySelector(s);if(e){const r=e.getBoundingClientRect();boxes[s]={top:r.top,bottom:r.bottom,height:r.height,visible:r.top>=0&&r.bottom<=visualViewport.height+1}}}const body=document.querySelector('#a-sheet-body'),d=document.querySelector('#a-dock').getBoundingClientRect(),sh=document.querySelector('#a-sheet').getBoundingClientRect();return {boxes,bodyScroll:body.scrollHeight>body.clientHeight+1,bodyY:body.scrollTop,header:document.querySelector('.a-header').getBoundingClientRect().height,map:document.querySelector('.a-map-space').getBoundingClientRect().height,sheetBottom:sh.bottom,dockTop:d.top,dockBottom:d.bottom,viewport:visualViewport.height,overflow:document.documentElement.scrollWidth>innerWidth,stage:aTaskStage(aTask()),mode:ASnap}}""")
def essentials(p,tag):
 m=visible_layout(p);metrics.append({'tag':tag,**m});check(all(x['visible'] for x in m['boxes'].values()) and not m['bodyScroll'] and abs(m['sheetBottom']-m['dockTop'])<1.1 and m['dockBottom']<=m['viewport']+1 and not m['overflow'],tag+' essentials simultaneously visible / no overlap '+json.dumps(m,ensure_ascii=False))
def swipe(p,fraction=1,vertical=0,cancel=False):
 wait(p,"()=>!!document.querySelector('#swk')?.offsetWidth");r,w=p.evaluate("()=>['#swk','#swp'].map(s=>{const r=document.querySelector(s).getBoundingClientRect();return {x:r.x,y:r.y,width:r.width,height:r.height}})");sx=r['x']+r['width']/2;sy=r['y']+r['height']/2;dx=(w['width']-r['width']-8)*fraction
 p.mouse.move(sx,sy);p.mouse.down();p.mouse.move(sx+dx,sy+vertical,steps=12)
 if cancel:p.locator('#swk').dispatch_event('pointercancel',{'pointerId':1})
 p.mouse.up();settle(p)
if __name__=='__main__':
 with sync_playwright() as pw:
  for eng in os.environ.get('JOURNEY_ENGINES','chromium,webkit').split(','):
   b=getattr(pw,eng).launch()
   for width,outer in [(360,780),(390,844),(430,932)]:
    if str(width) not in os.environ.get('JOURNEY_WIDTHS','360,390,430').split(','):continue
    tag=f'{eng} {width}';ctx,p,errors=boot(b,width,outer-128)
    try:
     print('BRAND',p.locator('.a-brand img').evaluate('(e)=>({natural:e.naturalWidth,width:e.getBoundingClientRect().width,height:e.getBoundingClientRect().height,css:getComputedStyle(e).cssText})'),flush=True);essentials(p,tag+' offer/work');check(p.evaluate('aTaskStage(aTask())')==0 and 'Открыть заказ' not in p.locator('#a-sheet').inner_text(),tag+' direct offer, no intermediate open/accept')
     p.screenshot(path=str(OUT/f'offer-{eng}-{width}.png'))
     p.locator('.a-quick-details').click();check(p.locator('.a-dialog-body .inv').count()==1 and p.evaluate('aTaskStage(aTask())')==0 and not p.evaluate("__UI_RPCS.some(x=>x[0]==='driver_accept')"),tag+' details only, no implicit accept')
     p.get_by_role('button',name='Закрыть',exact=True).click();settle(p)
     swipe(p,.4);check(not p.evaluate("__UI_RPCS.some(x=>x[0]==='driver_accept')"),tag+' partial swipe never accepts')
     p.evaluate('window.__UI_DELAY=450');swipe(p);check(p.locator('.a-confirmed').count()==0,tag+' accept waits for server');wait(p,'()=>!AFlight');settle(p)
     check(p.evaluate('aTaskStage(aTask())')==1 and p.evaluate("__UI_RPCS.filter(x=>x[0]==='driver_accept').length")==1,tag+' accepted through original handler')
     essentials(p,tag+' to-store/work');p.screenshot(path=str(OUT/f'to-store-{eng}-{width}.png'))
     check(p.locator('.a-stages li').count()==4 and p.locator('.a-stages li[aria-current=step]').count()==1 and p.locator('.a-stages details').count()==0,tag+' four stages always visible')
     p.locator('#a-mode-toggle').click();settle(p);essentials(p,tag+' to-store/map');check(p.evaluate('ASnap')=='collapsed',tag+' mode button switches without drag');p.screenshot(path=str(OUT/f'map-{eng}-{width}.png'))
     p.locator('#a-mode-toggle').click();settle(p);check(p.evaluate('ASnap')=='default',tag+' Work returns')
     if os.environ.get('JOURNEY_SMOKE'):continue
     # Drag lives only on the 44px grip; source confirmation swipe remains unchanged.
     r=p.locator('#a-grip').bounding_box();p.mouse.move(r['x']+22,r['y']+22);p.mouse.down();p.mouse.move(r['x']+22,r['y']+82,steps=12);mid=p.locator('#a-sheet').bounding_box()['y'];p.mouse.up();settle(p);check(p.evaluate('ASnap')=='collapsed' and mid>r['y'],tag+' live grip drag into map mode')
     p.locator('#a-grip').press('Home');settle(p)
     p.locator('.a-navigation').click();p.wait_for_selector('.n-provider');check(p.locator('.n-provider').count()==3,tag+' existing chooser retained')
     p.evaluate("()=>{document.dispatchEvent(new Event('visibilitychange'));window.dispatchEvent(new Event('pagehide'));document.dispatchEvent(new Event('visibilitychange'))}");settle(p);check(p.evaluate('aTaskStage(aTask())')==1,tag+' external return preserves stage')
     p.evaluate('aNavigationClose()');settle(p)
     p.evaluate("()=>{window.__UI_DELAY=400;window.__UI_FAIL='driver_arrived';aRun();aRun()}");wait(p,'()=>!AFlight');check(p.evaluate('aTaskStage(aTask())')==1 and p.locator('.a-error').count()==1,tag+' error keeps stage / duplicate blocked');essentials(p,tag+' failure')
     p.evaluate("()=>{__UI_FAIL='';aRun()}");wait(p,'()=>!AFlight');check(p.evaluate('aTaskStage(aTask())')==2,tag+' arrived store via existing service')
     p.evaluate("async()=>{__UI_TABLES.orders.find(x=>x.id==='ord1').status='preparing';__UI_TABLES.orders.find(x=>x.id==='ord1').prep_time=45;await TLB.reload()}");settle(p);check(p.locator('#swp.off').count()==1,tag+' preparing cannot confirm pickup');essentials(p,tag+' pickup/waiting');p.screenshot(path=str(OUT/f'waiting-{eng}-{width}.png'))
     p.evaluate("async()=>{__UI_TABLES.orders.find(x=>x.id==='ord1').status='ready';await TLB.reload()}");settle(p);essentials(p,tag+' pickup/ready');p.screenshot(path=str(OUT/f'pickup-{eng}-{width}.png'))
     p.locator('.a-accessible').click();check(p.evaluate('aTaskStage(aTask())')==2,tag+' Without gesture asks explicitly');p.locator('.a-dialog-body .b').click();wait(p,'()=>!AFlight');check(p.evaluate('aTaskStage(aTask())')==3 and p.locator('.a-confirmed').count()==1,tag+' pickup acknowledgement advances to customer')
     essentials(p,tag+' to-customer/work');p.screenshot(path=str(OUT/f'customer-{eng}-{width}.png'))
     p.evaluate("()=>{aRun();aRun()}");wait(p,'()=>!AFlight');check(p.evaluate('aTaskStage(aTask())')==4 and p.evaluate("__UI_RPCS.filter(x=>x[0]==='chat').length")==1,tag+' customer arrival preserves atCustMsg once')
     essentials(p,tag+' handover');p.screenshot(path=str(OUT/f'handover-{eng}-{width}.png'))
     p.evaluate('aRun()');settle(p);check(p.locator('#cashAmt').count()==1 and not p.evaluate("__UI_RPCS.some(x=>x[0]==='deliver_order')"),tag+' existing cash delivery gate')
     p.locator('#cashAmt').fill('100');p.locator('#dvok').click();settle(p);check(not p.evaluate("__UI_RPCS.some(x=>x[0]==='deliver_order')"),tag+' discrepancy still needs note')
     p.locator('#cashNote').fill('Test-only discrepancy');p.locator('#dvok').click();p.wait_for_timeout(100);check(p.locator('.a-delivered-summary').count()==0,tag+' no delivered before response');wait(p,'()=>!AFlight');settle(p)
     check(p.evaluate("TLB.order('ord1').status")== 'delivered' and p.locator('.a-delivered-summary').count()==1,tag+' confirmed delivered / waiting resumes');p.screenshot(path=str(OUT/f'done-{eng}-{width}.png'))
     check(not errors,tag+' no page errors '+repr(errors))
    except Exception:
     p.screenshot(path=str(OUT/f'failure-{eng}-{width}.png'));print('DEBUG',json.dumps(visible_layout(p) if p.locator('#a-sheet').count() else {'text':p.locator('body').inner_text(),'errors':errors},ensure_ascii=False),flush=True);raise
    finally:ctx.close()
   b.close()
 (OUT/'journey-results.json').write_text(json.dumps({'checks':len(results),'results':results,'metrics':metrics,'real_device':False},ensure_ascii=False,indent=2));print('TOTAL',len(results))
