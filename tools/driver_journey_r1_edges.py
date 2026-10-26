"""R1-only edge cases on actual driver UI with isolated services. No backend writes."""
import driver_journey_r1_check as S
from playwright.sync_api import sync_playwright
import json,os
results=[]
def check(v,msg):
 assert v,msg
 results.append(msg);print('PASS',msg,flush=True)
with sync_playwright() as pw:
 for eng in os.environ.get('JOURNEY_EDGE_ENGINES','chromium,webkit').split(','):
  b=getattr(pw,eng).launch();c,p,errors=S.boot(b,360,652,'pickup');p.on('dialog',lambda d:d.dismiss())
  # Keep one Leaflet map + user view during the new mode / grip layout.
  S.settle(p);p.wait_for_timeout(300);p.evaluate("window.__r1Map=DM;DM.setView([38.57,68.79],15,{animate:false})")
  r=p.locator('.a-map-space').bounding_box();p.mouse.move(140,r['y']+30);p.mouse.down();p.mouse.move(175,r['y']+45,steps=5);p.mouse.up();p.wait_for_timeout(650)
  view=p.evaluate('({lat:DM.getCenter().lat,lng:DM.getCenter().lng,z:DM.getZoom()})')
  p.locator('#a-mode-toggle').click();p.locator('#a-mode-toggle').click();p.evaluate('render()');S.settle(p)
  check(p.evaluate('DM===__r1Map') and p.evaluate('DM.getZoom()')==view['z'] and abs(p.evaluate('DM.getCenter().lat')-view['lat'])<.00001,eng+' one map + user view retained across work/map/render')
  # Partial and cancelled panel drags restore their stable mode.
  r=p.locator('#a-grip').bounding_box();p.mouse.move(r['x']+22,r['y']+22);p.mouse.down();p.mouse.move(r['x']+22,r['y']+42,steps=4);p.mouse.up();S.settle(p);check(p.evaluate('ASnap')=='default',eng+' partial panel drag does not switch mode')
  p.locator('#a-grip').evaluate("e=>e.addEventListener('pointerdown',ev=>window.__r1Pointer=ev.pointerId,{once:true})");r=p.locator('#a-grip').bounding_box();p.mouse.move(r['x']+22,r['y']+22);p.mouse.down();p.mouse.move(r['x']+22,r['y']+82,steps=8);p.locator('#a-grip').dispatch_event('pointercancel',{'pointerId':p.evaluate('__r1Pointer'),'clientX':20,'clientY':370});p.mouse.up();S.settle(p);check(p.evaluate('ASnap')=='default' and p.evaluate('window.__drag')==0,eng+' pointercancel restores panel without advancing')
  # New layout still enforces original anti-accidental confirmation gestures.
  S.swipe(p,1,70);check(not p.evaluate("__UI_RPCS.some(x=>x[0]==='set_order_status')"),eng+' vertical drift cannot confirm pickup')
  # Simulated 32px top / 24px bottom safe insets: measurements, no production fake browser bars.
  p.evaluate("()=>{document.documentElement.style.setProperty('--a-headh','84px');document.querySelector('#a-dock').style.paddingBottom='28px';aJourneyQueueLayout()}");S.settle(p)
  m=S.visible_layout(p);check(not m['bodyScroll'] and all(v['visible'] for v in m['boxes'].values()) and m['dockBottom']<=652,eng+' simulated safe insets keep essentials above dock');p.screenshot(path=str(S.OUT/f'safe-{eng}-360.png'))
  p.evaluate("()=>{document.documentElement.style.removeProperty('--a-headh');document.querySelector('#a-dock').style.paddingBottom='4px';aJourneyQueueLayout()}");S.settle(p)
  # Missing source address is explicit; no prototype restaurant address or payout.
  p.evaluate("async()=>{__UI_TABLES.stores[0].address=null;await TLB.reload();render()}");S.settle(p)
  check('Адрес ресторана не указан' in p.locator('.a-target').inner_text() and 'Рудаки' not in p.locator('.a-target').inner_text(),eng+' missing restaurant address remains missing')
  # Large exceptional titles use explicit scrolling rather than a line clamp or font shrinking.
  p.evaluate("async()=>{const x=__UI_TABLES.orders.find(x=>x.id==='ord1');__UI_TABLES.stores[0].name=('Очень длинное название ресторана ').repeat(8);__UI_TABLES.stores[0].address=('Длинный адрес · вход со двора ').repeat(10);await TLB.reload();render()}");S.settle(p)
  p.evaluate("()=>{const x=aTask();window.__r1LongName=x.store;}")
  # stores name is a model field; exercise the actual presentation with a long current title as provided by core.
  S.settle(p)
  check(p.locator('#a-sheet-body').evaluate('(e)=>e.scrollHeight>e.clientHeight') and p.locator('.a-target h1').evaluate('(e)=>getComputedStyle(e).display')=='block',eng+' exceptional long text is scrollable, not clamped')
  p.locator('#a-sheet-body').evaluate('(e)=>e.scrollTop=e.scrollHeight');S.settle(p);check(p.locator('.a-chat').bounding_box()['y']+44<=p.locator('#a-dock').bounding_box()['y']+1,eng+' long-text tools scroll clear of confirmation')
  p.screenshot(path=str(S.OUT/f'long-{eng}-360.png'))
  p.evaluate("async()=>{__UI_TABLES.stores[0].address=null;const x=__UI_TABLES.orders.find(x=>x.id==='ord1');x.status='pickedup';x.address='';x.payment='card';await TLB.reload();render()}");S.settle(p)
  check('Адрес не указан' in p.locator('.a-target').inner_text() and 'Оплачено онлайн' in p.locator('.a-journey-money').inner_text(),eng+' missing customer address + online payment explicit')
  # New chat plate preserves badge, draft and real chat handler; only fixture data is used.
  p.evaluate("()=>{window.__r1Unread=TLB.unread;TLB.unread=()=>7;render()}");S.settle(p);check(p.locator('.a-chat .dotb').inner_text()=='7' and p.locator('.a-chat').bounding_box()['height']>=44,eng+' unread chat badge on full target')
  p.locator('.a-chat').click();p.locator('#ci').fill('R1 isolated draft');p.set_viewport_size({'width':360,'height':360});S.settle(p);p.evaluate('render()');S.settle(p)
  check(p.locator('#ci').input_value()=='R1 isolated draft' and p.locator('.a-chat-modal').bounding_box()['height']<=336+1,eng+' keyboard-height simulation keeps draft and bounded dialog')
  p.locator('#ci').scroll_into_view_if_needed();p.locator('.a-chat-modal .row .b').last.click();S.wait(p,"()=>!AChatBusy['ord1']");check(p.evaluate("__UI_RPCS.some(x=>x[0]==='chat'&&x[1].body==='R1 isolated draft')"),eng+' chat uses original service payload')
  p.set_viewport_size({'width':360,'height':652});p.evaluate('chatOpen=false;TLB.unread=__r1Unread;render()');S.settle(p)
  # Existing photo gate remains real; no demo acceptance before upload/server.
  p.evaluate("async()=>{const x=__UI_TABLES.orders.find(x=>x.id==='ord1');x.arrived_cust_at=new Date().toISOString();x.leave_at_door=true;await TLB.reload();render();aRun()}");S.settle(p)
  check(p.locator('.phb input[type=file]').count()==1 and p.locator('#dvok').is_disabled() and not p.evaluate("__UI_RPCS.some(x=>x[0]==='deliver_order')"),eng+' leave-at-door photo still required')
  check(not errors,eng+' no edge-case page errors '+repr(errors));c.close();b.close()
(S.OUT/'journey-edges.json').write_text(json.dumps({'checks':len(results),'results':results},ensure_ascii=False,indent=2));print('TOTAL',len(results))
