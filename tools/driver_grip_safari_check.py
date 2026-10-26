"""Grip/root-scroll regression only; isolated services, not real iPhone Safari chrome."""
import json,os
from pathlib import Path
from playwright.sync_api import sync_playwright
import driver_journey_r1_check as S

OUT=S.ROOT/'docs/driver-handoff/grip-safari-20261026'
OUT.mkdir(exist_ok=True)
results=[]
def check(ok,msg):
 assert ok,msg
 results.append(msg)
 (OUT/'results.json').write_text(json.dumps({'checks':len(results),'results':results,'real_iphone':False},indent=2))
 print('PASS',msg,flush=True)
def drag(p,dy,cdp=None):
 r=p.locator('#a-grip').bounding_box();x=r['x']+22;y=r['y']+22
 if cdp:
  cdp.send('Input.dispatchTouchEvent',{'type':'touchStart','touchPoints':[{'x':x,'y':y}]})
  for i in range(1,13):
   cdp.send('Input.dispatchTouchEvent',{'type':'touchMove','touchPoints':[{'x':x,'y':y+dy*i/12}]})
  cdp.send('Input.dispatchTouchEvent',{'type':'touchEnd','touchPoints':[]})
 else:
  p.mouse.move(x,y);p.mouse.down();p.mouse.move(x,y+dy,steps=12);p.mouse.up()
 S.settle(p)
with sync_playwright() as pw:
 for engine in os.environ.get('GRIP_ENGINES','chromium,webkit').split(','):
  browser=getattr(pw,engine).launch()
  for width,outer in [(360,780),(390,844),(430,932)]:
   ctx,p,errors=S.boot(browser,width,outer-128,'pickup')
   cdp=ctx.new_cdp_session(p) if engine=='chromium' else None
   tag=f'{engine} {width}'
   check(p.evaluate("document.documentElement.classList.contains('a-mission-lock') && getComputedStyle(document.body).position==='fixed' && getComputedStyle(document.documentElement).overscrollBehaviorY==='none'"),tag+' mission-only root lock')
   # Includes a start on the visible child handle, not just button whitespace.
   check(p.locator('#a-grip i').evaluate("e=>getComputedStyle(e).touchAction==='none'"),tag+' handle child rejects native pan from gesture start')
   check(p.locator('#a-grip').evaluate("e=>{const t=new Event('touchmove',{bubbles:true,cancelable:true});e.dispatchEvent(t);return t.defaultPrevented}"),tag+' non-passive grip touchmove cancellation')
   for bars in [128,68,128]:
    p.set_viewport_size({'width':width,'height':outer-bars});S.settle(p)
    for repeat in range(3):
     drag(p,65,cdp);assert p.evaluate('ASnap')=='collapsed'
     drag(p,-65,cdp);assert p.evaluate('ASnap')=='default'
    check(p.evaluate("scrollY===0 && Math.abs(document.querySelector('.a-header').getBoundingClientRect().top-visualViewport.offsetTop)<1 && document.querySelector('#a-dock').getBoundingClientRect().bottom<=visualViewport.height+1"),tag+f' repeated up/down, header/root/dock stable bars={bars}')
   p.locator('#a-mode-toggle').click();S.settle(p)
   check(p.evaluate("ASnap==='collapsed'"),tag+' button alternative retained')
   p.evaluate('window.__gripMap=DM');r=p.locator('.a-map-space').bounding_box()
   before=p.evaluate('DM.getCenter().lng');p.mouse.move(100,r['y']+25);p.mouse.down();p.mouse.move(155,r['y']+25,steps=10);p.mouse.up();p.wait_for_timeout(700)
   check(p.evaluate('DM===__gripMap') and abs(p.evaluate('DM.getCenter().lng')-before)>0.00001,tag+' Leaflet receives map pan')
   if width==390:p.screenshot(path=str(OUT/f'{engine}-map.png'))
   p.locator('.a-quick-details').click();p.locator('.a-dialog-body').evaluate("e=>{const d=document.createElement('div');d.style.height='1500px';e.append(d);e.scrollTop=300}");S.settle(p)
   check(p.locator('.a-dialog-body').evaluate('e=>e.scrollTop>0') and p.evaluate('scrollY===0'),tag+' details scroll independently')
   p.get_by_role('button',name='Закрыть',exact=True).click();p.locator('#a-mode-toggle').click();S.settle(p)
   S.swipe(p,.35)
   check(not p.evaluate("__UI_RPCS.some(x=>x[0]==='set_order_status')") and p.evaluate('scrollY===0'),tag+' partial confirmation remains independent')
   if width==390:p.screenshot(path=str(OUT/f'{engine}-work.png'))
   p.evaluate("aTab('h')")
   # Actual utility exit uses aShow; exercise its original hook.
   S.settle(p)
   check(not p.evaluate("document.body.classList.contains('a-mission') || document.documentElement.classList.contains('a-mission-lock')"),tag+' leaving mission releases root lock')
   check(not errors,tag+' no page errors')
   ctx.close()
  browser.close()
(OUT/'results.json').write_text(json.dumps({'checks':len(results),'results':results,'real_iphone':False,'limits':'Chromium native CDP touch; WebKit pointer + cancelable TouchEvent. Toolbar sizes simulated; Safari pull-to-refresh not available in automation.'},indent=2))
print('TOTAL',len(results))
