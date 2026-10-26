"""Only repeated mission gestures and customer location picker/send feedback; isolated services."""
import json,subprocess,os
from pathlib import Path
from playwright.sync_api import sync_playwright
import driver_journey_r1_check as S
ROOT=S.ROOT;OUT=ROOT/'docs/driver-handoff/repeat-location-20261027';OUT.mkdir(exist_ok=True)
results=[];measurements=[]
def check(ok,msg):
 assert ok,msg
 results.append(msg);print('PASS',msg,flush=True)
def touch(p,cdp,dy,cancel=False):
 r=p.locator('#a-grip i').bounding_box();x=r['x']+r['width']/2;y=r['y']+2
 cdp.send('Input.dispatchTouchEvent',{'type':'touchStart','touchPoints':[{'x':x,'y':y}]})
 for i in range(1,9):cdp.send('Input.dispatchTouchEvent',{'type':'touchMove','touchPoints':[{'x':x,'y':y+dy*i/8}]})
 cdp.send('Input.dispatchTouchEvent',{'type':'touchCancel' if cancel else 'touchEnd','touchPoints':[]});S.settle(p)
def rect(p):return p.locator('#a-sheet').bounding_box()['y']
with sync_playwright() as pw:
 b=pw.chromium.launch()
 # Prove the unpatched detail=0 compatibility-click defect, without server actions.
 c,p,e=S.boot(b,390,716,'pickup')
 old=subprocess.check_output(['git','show','226f05e0b3dd4be27f032ed10af6fc49a46b5330:assets/driver-a/driver-a.js'],cwd=ROOT,text=True);a=old.index('function aBindSheet()');z=old.index('\n/*',a)
 p.evaluate('code=>(0,eval)(code)',old[a:z]+';render()');r=p.locator('#a-grip').bounding_box();p.mouse.move(r['x']+22,r['y']+22);p.mouse.down();p.mouse.move(r['x']+22,r['y']+85,steps=8);p.mouse.up();S.settle(p)
 before=p.evaluate('ASnap');p.locator('#a-grip').dispatch_event('click',{'detail':0});S.settle(p)
 check(before=='collapsed' and p.evaluate('ASnap')=='default','baseline reproduces zero-detail compatibility click reversing completed drag');c.close()
 for w,h in [(360,780),(390,844),(430,932)]:
  c,p,errors=S.boot(b,w,h-128,'pickup');cdp=c.new_cdp_session(p)
  for bars in [128,68,128]:
   p.set_viewport_size({'width':w,'height':h-bars});S.settle(p)
   for cycle in range(3):
    touch(p,cdp,65);assert p.evaluate('ASnap')=='collapsed'
    p.locator('#a-grip').dispatch_event('click',{'detail':0});assert p.evaluate('ASnap')=='collapsed'
    touch(p,cdp,-65);assert p.evaluate('ASnap')=='default'
   check(p.evaluate('!window.__drag && scrollY===0') and abs(p.locator('.a-header').bounding_box()['y'])<1,f'{w} repeated native touch + compatibility click, root/header stable bars={bars}')
  work=rect(p);touch(p,cdp,65);collapsed=rect(p);p.locator('#a-mode-toggle').click();S.settle(p);buttonwork=rect(p);p.locator('#a-mode-toggle').click();S.settle(p)
  check(abs(rect(p)-collapsed)<1 and abs(work-buttonwork)<1 and collapsed>work+20,f'{w} drag/button reach identical two layouts')
  measurements.append({'width':w,'workTop':work,'mapTop':collapsed,'delta':collapsed-work})
  touch(p,cdp,-65,cancel=True);check(p.evaluate("ASnap==='collapsed' && !window.__drag"),f'{w} touchcancel restores stable map mode')
  touch(p,cdp,-65);check(p.evaluate("ASnap==='default' && !window.__drag"),f'{w} fresh touch after cancellation works')
  touch(p,cdp,15);check(p.evaluate("ASnap==='default' && !window.__drag"),f'{w} partial release restores work')
  # Browser focus/background cancellation must release render deferral, not leave __drag latched.
  r=p.locator('#a-grip').bounding_box();cdp.send('Input.dispatchTouchEvent',{'type':'touchStart','touchPoints':[{'x':r['x']+22,'y':r['y']+22}]});p.evaluate("window.dispatchEvent(new Event('pagehide'))");cdp.send('Input.dispatchTouchEvent',{'type':'touchEnd','touchPoints':[]});S.settle(p)
  check(p.evaluate('!window.__drag'),f'{w} pagehide terminates touch gesture');touch(p,cdp,65)
  # Actual pointer path includes failed capture and cancel/lost capture, not just touchscreen.
  p.locator('#a-grip').evaluate("e=>{e.__capture=e.setPointerCapture;e.setPointerCapture=()=>{throw Error('capture unavailable')}}")
  p.locator('#a-grip').dispatch_event('pointerdown',{'pointerId':53,'pointerType':'mouse','button':0,'clientX':22,'clientY':400,'isPrimary':True})
  check(p.evaluate('!window.__drag'),f'{w} capture failure releases gesture lock');p.locator('#a-grip').evaluate('e=>e.setPointerCapture=e.__capture')
  p.locator('#a-grip').press('Home');S.settle(p);p.locator('#a-grip').press(' ');S.settle(p)
  check(p.evaluate("ASnap==='collapsed'"),f'{w} keyboard non-drag alternative')
  # Keep map pan, detail scroll and existing confirmation independent of the grip lifecycle.
  r=p.locator('.a-map-space').bounding_box();before=p.evaluate('DM.getCenter().lng');p.mouse.move(90,r['y']+25);p.mouse.down();p.mouse.move(160,r['y']+25,steps=8);p.mouse.up();p.wait_for_timeout(650)
  check(abs(p.evaluate('DM.getCenter().lng')-before)>.00001,f'{w} map still receives pan')
  p.locator('.a-quick-details').click();p.locator('.a-dialog-body').evaluate("e=>{e.insertAdjacentHTML('beforeend','<div style=\"height:1500px\"></div>');e.scrollTop=250}");S.settle(p)
  check(p.locator('.a-dialog-body').evaluate('e=>e.scrollTop>0') and p.evaluate('scrollY===0'),f'{w} details scroll separately');p.get_by_role('button',name='Закрыть',exact=True).click()
  S.swipe(p,.35);check(not p.evaluate("__UI_RPCS.some(x=>x[0]==='set_order_status')"),f'{w} partial confirmation cannot advance stage')
  # Suppression survives the deferred render which replaces the old grip after release.
  p.locator('#a-mode-toggle').click();S.settle(p);r=p.locator('#a-grip').bounding_box();x=r['x']+22;y=r['y']+22
  cdp.send('Input.dispatchTouchEvent',{'type':'touchStart','touchPoints':[{'x':x,'y':y}]});cdp.send('Input.dispatchTouchEvent',{'type':'touchMove','touchPoints':[{'x':x,'y':y+65}]});p.evaluate('render()');cdp.send('Input.dispatchTouchEvent',{'type':'touchEnd','touchPoints':[]});S.settle(p)
  p.locator('#a-grip').dispatch_event('click',{'detail':0});check(p.evaluate("ASnap==='collapsed' && !window.__drag && !window.__rp"),f'{w} compatibility click stays suppressed after deferred render replaces grip')
  check(not errors,f'{w} no driver page errors {errors}')
  if w==390:p.screenshot(path=str(OUT/'driver-map.png'));p.locator('#a-mode-toggle').click();S.settle(p);p.screenshot(path=str(OUT/'driver-work.png'))
  c.close()
 # Customer: real core picker, isolated geolocation and chat reply. Preparing is already eligible in the source.
 subprocess.run(['python',str(ROOT/'tools/ui_hc_fixture.py'),'/tmp/repeat-location-fixture'],check=True,capture_output=True)
 fixture=Path('/tmp/repeat-location-fixture/customer-fixture.js').read_text()
 def customer(mapfail=False):
  ctx=b.new_context(viewport={'width':390,'height':716},has_touch=True,is_mobile=True);page=ctx.new_page();errors=[];page.on('pageerror',lambda e:errors.append(str(e)))
  page.add_init_script("window.__C_SCENE='preparing';localStorage.setItem('tlb_lang','ru');window.fetch=()=>Promise.reject(Error('isolated'));Object.defineProperty(navigator,'geolocation',{value:{getCurrentPosition:(ok,fail)=>{window.__geoOK=ok;window.__geoFail=fail}}});")
  def route(r):
   u=r.request.url
   if 'supabase-js' in u:r.fulfill(content_type='application/javascript',body=fixture)
   elif 'leaflet.js' in u:
    if mapfail is True:r.abort()
    elif mapfail=='empty':r.fulfill(content_type='application/javascript',body='/* invalid empty CDN response */')
    else:r.fulfill(content_type='application/javascript',body=(S.LEAF/'leaflet.js').read_text())
   elif 'leaflet.css' in u:r.fulfill(content_type='text/css',body=(S.LEAF/'leaflet.css').read_text())
   elif 'tile.openstreetmap.org' in u:r.fulfill(content_type='image/png',body=S.PNG)
   elif u.startswith('http'):r.abort()
   else:r.continue_()
  ctx.route('**/*',route);page.goto((ROOT/'customer.html').as_uri());S.wait(page,'()=>!!ME?.phone');page.evaluate("()=>{S.v='track';S.tid='ord1';render();window.__sent=[];TLB.chat=(id,sender,text)=>{__sent.push({id,sender,text});return new Promise(r=>window.__chatReply=r)}}")
  return ctx,page,errors
 c,p,errors=customer(True);p.locator('button[onclick="sendLoc()"]').click();S.wait(p,"()=>CLoc.ord1?.phase==='error'");check('не загрузилась' in p.locator('#cloc-status').inner_text(),'customer picker-load failure is visible and retryable');c.close()
 c,p,errors=customer();p.locator('button[onclick="sendLoc()"]').click();p.wait_for_selector('#tlb-me')
 check('Определяем' in p.locator('#tlb-lm').inner_text() and p.locator('#tlb-me').is_disabled(),'customer geolocation waiting feedback + duplicate guard')
 for code,label in [(1,'запрещён'),(2,'Не удалось'),(3,'истекло')]:
  p.evaluate(f'__geoFail({{code:{code}}})');check(label in p.locator('#tlb-lm').inner_text() and not p.locator('#tlb-me').is_disabled(),f'customer geolocation failure code {code} is explained');p.locator('#tlb-me').click()
 p.evaluate('__geoOK({coords:{latitude:41.3,longitude:69.2}})');check('определено' in p.locator('#tlb-lm').inner_text(),'customer successful GPS waits for explicit send')
 p.screenshot(path=str(OUT/'customer-picker.png'));p.locator('#tlb-ls').click();check(p.evaluate("CLoc.ord1.phase==='sending' && __sent.length===1") and 'Отправляем' in p.locator('#cloc-status').inner_text(),'customer sending feedback before server reply')
 p.evaluate('sendLoc()');check(p.evaluate('__sent.length')==1,'customer duplicate location send blocked while pending')
 p.evaluate("__chatReply({error:'generic'})");S.wait(p,"()=>CLoc.ord1.phase==='error'");check('Не удалось отправить' in p.locator('#cloc-status').inner_text(),'customer chat rejection never reports success')
 p.locator('button[onclick="sendLoc()"]').click();p.wait_for_selector('#tlb-ls');p.evaluate('__geoOK({coords:{latitude:41.3,longitude:69.2}})');p.locator('#tlb-ls').click();p.evaluate('__chatReply({ok:true})');S.wait(p,"()=>CLoc.ord1.phase==='sent'")
 check(p.evaluate("__sent[1].id==='ord1' && __sent[1].text==='LOC:41.300000,69.200000'") and 'отправлено курьеру' in p.locator('#cloc-status').inner_text(),'customer sends captured order id and source LOC payload only after confirmation')
 p.screenshot(path=str(OUT/'customer-sent.png'))
 # Late selection may not send to a different order or newly ended state.
 p.locator('button[onclick="sendLoc()"]').click();p.wait_for_selector('#tlb-ls');p.evaluate("S.tid='another';S.v='orders';render()");p.locator('#tlb-ls').click();check(p.evaluate('__sent.length')==2,'customer navigation during selection cannot send to another order')
 p.evaluate("S.tid='ord1';S.v='track';TLB.order('ord1').status='pending';render();sendLoc()");check(p.locator('#tlb-map').count()==0,'customer pending status remains ineligible')
 check(not errors,'customer no page errors '+str(errors));c.close()
 c,p,errors=customer('empty');p.locator('button[onclick="sendLoc()"]').click();S.wait(p,"()=>CLoc.ord1?.phase==='error'");check('не загрузилась' in p.locator('#cloc-status').inner_text() and not errors,'empty CDN script yields picker failure rather than an exception');c.close()
 c,p,errors=customer();p.clock.install();p.locator('button[onclick="sendLoc()"]').click();p.wait_for_selector('#tlb-me');p.clock.fast_forward(13100);check('истекло' in p.locator('#tlb-lm').inner_text(),'location deadline covers a browser that never calls back')
 p.locator('#tlb-me').click();p.evaluate('window.__lateGeo=__geoOK');p.locator('#tlb-lx').click();p.evaluate('__lateGeo({coords:{latitude:41.3,longitude:69.2}})');check(p.locator('#tlb-map').count()==0 and p.evaluate('__sent.length')==0,'closing picker drops late GPS without sending')
 p.locator('button[onclick="sendLoc()"]').click();p.wait_for_selector('#tlb-ls');p.evaluate('__geoOK({coords:{latitude:41.3,longitude:69.2}})');p.locator('#tlb-ls').click();p.clock.fast_forward(15100);check('ещё не подтвердил' in p.locator('#cloc-status').inner_text() and p.locator('button[onclick="sendLoc()"]').is_disabled(),'slow chat reply shows unconfirmed status without allowing duplicate send');p.evaluate('__chatReply({ok:true})');S.wait(p,"()=>CLoc.ord1.phase==='sent'");check(p.evaluate('__sent.length')==1,'late successful chat reply resolves exactly one send');check(not errors,'deadline and closed-picker cases have no JS errors');c.close();b.close()
(OUT/'results.json').write_text(json.dumps({'checks':len(results),'results':results,'layouts':measurements,'real_iphone':False,'webkit':'Unavailable: prior host library limitation; not claimed'},indent=2))
print('TOTAL',len(results))
