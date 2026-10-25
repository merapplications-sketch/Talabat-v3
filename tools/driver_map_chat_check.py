"""Affected driver A map and cross-session chat checks. LOCAL doubles; never live account proof.
Usage: MAP_LEAFLET=/path/to/leaflet/dist TEST_ENGINE=chromium|webkit python tools/driver_map_chat_check.py
Actual Leaflet and current app/core; offline 1px tiles. Chat uses distinct customer/driver browser contexts
and the shared in-memory DB; receipt is by the app scheduler (no receiver reload/render calls).
"""
from pathlib import Path
import os,sys,subprocess,json,base64,time
from playwright.sync_api import sync_playwright
ROOT=Path(__file__).resolve().parents[1]
OUT=Path(os.environ.get('MAP_CHAT_OUT','/tmp/talabot-map-chat'));OUT.mkdir(parents=True,exist_ok=True)
LEAF=Path(os.environ['MAP_LEAFLET']);ENGINE=os.environ.get('TEST_ENGINE','chromium')
subprocess.run([sys.executable,str(ROOT/'tools/driver_a_fixture.py'),str(OUT)],check=True)
FIX=(OUT/'review-fixture.js').read_text()
PNG=base64.b64decode('iVBORw0KGgoAAAANSUhEUgAAAAEAAAABCAQAAAC1HAwCAAAAC0lEQVR42mP8/x8AAwMCAO+ip1sAAAAASUVORK5CYII=')
# Existing shared DB fixture, with no test execution imported.
ns={'__file__':str(ROOT/'tools/flow_check.py')}
exec(compile((ROOT/'tools/flow_check.py').read_text().split('shots=[]')[0],ns['__file__'],'exec'),ns)
errors=[];checks=[]
def pause(pg,n=250):pg.wait_for_timeout(n)
def wait_read(pg,fn,arg=None,timeout=35):
 end=time.monotonic()+timeout
 while not pg.evaluate(fn,arg):
  if time.monotonic()>end:raise AssertionError('Timed out waiting for '+fn)
  pause(pg,200)
def drag(pg,x,y,dx,dy):
 pg.mouse.move(x,y);pg.mouse.down();pg.mouse.move(x+dx,y+dy,steps=14);pg.mouse.up();pause(pg)
def map_page(browser,width,height,scene='pickup'):
 ctx=browser.new_context(viewport={'width':width,'height':height},permissions=['geolocation'],geolocation={'latitude':38.56,'longitude':68.78,'accuracy':20},has_touch=True)
 ctx.add_init_script("window.__UI_CASE=%s;localStorage.setItem('tlb_lang','ru');window.fetch=()=>Promise.resolve(new Response('',{status:200}))"%json.dumps(scene))
 def route(r):
  u=r.request.url
  if 'supabase-js' in u:r.fulfill(content_type='application/javascript',body=FIX)
  elif 'leaflet.js' in u:r.fulfill(content_type='application/javascript',body=(LEAF/'leaflet.js').read_text())
  elif 'leaflet.css' in u:r.fulfill(content_type='text/css',body=(LEAF/'leaflet.css').read_text())
  elif 'tile.openstreetmap.org' in u:r.fulfill(content_type='image/png',body=PNG)
  elif u.startswith('http'):r.abort()
  else:r.continue_()
 ctx.route('**/*',route);pg=ctx.new_page();pg.on('pageerror',lambda e:errors.append(str(e)))
 pg.goto((ROOT/'driver.html').as_uri());pg.wait_for_selector('#a-sheet');pg.wait_for_function("typeof DM!=='undefined'&&DM&&DM!==1&&typeof DM.getCenter==='function'")
 pause(pg,900);return ctx,pg
with sync_playwright() as pw:
 browser=getattr(pw,ENGINE).launch()
 for width in ([] if os.environ.get('CHECK_PART')=='chat' else [360,390,430]):
  for height in [700,844]:
   ctx,pg=map_page(browser,width,height)
   g=pg.evaluate("""()=>{const h=document.querySelector('.a-header').getBoundingClientRect(),s=$('a-sheet').getBoundingClientRect(),d=$('a-dock').getBoundingClientRect(),r=$('a-ready-recentre').getBoundingClientRect();return {head:h.bottom,sheet:s.top,dock:d.top,x:innerWidth/2,y:(h.bottom+s.top)/2,recenter:r.bottom,overflow:document.documentElement.scrollWidth>innerWidth}}""")
   assert not g['overflow'] and g['sheet']-g['head']>=160 and g['recenter']<g['sheet'],g
   assert pg.evaluate('([x,y])=>$("dmap").contains(document.elementFromPoint(x,y))',[g['x'],g['y']]),'map intercepted by overlay'
   before=pg.evaluate('({c:DM.getCenter(),z:DM.getZoom(),snap:ASnap})')
   drag(pg,g['x'],g['y'],-60,32)
   after=pg.evaluate('({c:DM.getCenter(),z:DM.getZoom(),snap:ASnap})')
   assert before['c']!=after['c'] and before['snap']==after['snap'],'pan must move map only'
   pg.locator('.leaflet-control-zoom-in').click();pause(pg,400);z=pg.evaluate('DM.getZoom()');assert z>after['z']
   pg.locator('.leaflet-control-zoom-out').click();pause(pg,400);assert pg.evaluate('DM.getZoom()')==after['z']
   if ENGINE=='chromium':
    cdp=ctx.new_cdp_session(pg);x,y=g['x'],g['y'];start=pg.evaluate('DM.getZoom()')
    def touches(span):return [{'x':x-span,'y':y,'id':0},{'x':x+span,'y':y,'id':1}]
    cdp.send('Input.dispatchTouchEvent',{'type':'touchStart','touchPoints':touches(15)})
    for span in range(18,72,6):cdp.send('Input.dispatchTouchEvent',{'type':'touchMove','touchPoints':touches(span)})
    cdp.send('Input.dispatchTouchEvent',{'type':'touchEnd','touchPoints':[]});pause(pg,500)
    assert pg.evaluate('DM.getZoom()')>start,'two-finger pinch should zoom map'
    assert pg.evaluate('ASnap')=='default'
   # Sheet grip, sheet body and confirmation slider have separate gesture targets.
   grip=pg.locator('#a-grip').bounding_box();drag(pg,grip['x']+width/2,grip['y']+20,0,220)
   assert pg.evaluate('ASnap')=='collapsed'
   pg.evaluate("aSnap('expanded')");pause(pg)
   body=pg.locator('#a-sheet-body');box=body.bounding_box();pg.mouse.move(box['x']+width/2,box['y']+70);pg.mouse.wheel(0,600);pause(pg)
   assert body.evaluate('(e)=>e.scrollTop')>0
   # Vertical movement over confirmation does not accept/pick up/deliver.
   knob=pg.locator('#swk').bounding_box();drag(pg,knob['x']+20,knob['y']+20,0,-80)
   assert pg.evaluate("__UI_RPCS.filter(x=>['driver_accept','deliver_order','set_order_status'].includes(x[0])).length")==0
   assert pg.locator('.a-navigation').count()==1
   assert pg.locator('.a-navigation').get_attribute('onclick')=='aNavigationOpen()'  # current explicit internal/external chooser
   assert pg.locator('.a-target a').count()==0
   pg.evaluate("aSnap('default');$('a-sheet-body').scrollTop=0");pause(pg);pg.screenshot(path=str(OUT/f'{ENGINE}-map-{width}-{height}.png'))
   print('PASS',ENGINE,width,height,'hit target, pan, zoom, sheet/scroll/slider separation, explicit external navigation',flush=True)
   checks.append([ENGINE,width,height]);ctx.close()
 # Distinct sessions, distinct users, one shared isolated order, ordinary polling with realtime intentionally absent.
 tmp=browser.new_page();T=ns['base_tables'](tmp);tmp.close();U=ns['U'];now=ns['now']
 order={'id':5001,'store_id':T['stores'][0]['id'],'customer_id':U['customer'],'driver_id':U['driver'],'status':'preparing','subtotal':100,'discount':0,'promo_discount':0,'delivery_fee':10,'tip':0,'total':110,'commission':10,'commission_pct':10,'payment':'cash','address':'Test address','lat':38.56,'lng':68.78,'customer_name':'Test Customer','driver_name':'Test Driver','created_at':now(),'done_at':None,'driver_payout':15,'arrived_store_at':None,'arrived_cust_at':None}
 T['orders']=[order];T['order_chat']=[];db=ns['DB'](T);pages={};contexts=[]
 def handle(q):
  # Postgres order_chat.order_id is bigint; normalize JSON strings just as the real DB does.
  if q['kind']=='from' and q['name']=='order_chat' and q['op']=='insert':
   q['payload']['order_id']=int(q['payload']['order_id'])
  return db.handle(q)
 for role in ['customer','driver']:
  ctx=browser.new_context(viewport={'width':390,'height':844});contexts.append(ctx);ctx.expose_function('__db',handle)
  ctx.add_init_script('window.__ROLE=%s;window.__UID=%s;window.fetch=()=>Promise.resolve(new Response())'%(json.dumps(role),json.dumps(U[role])))
  ctx.route('**/*',lambda r:r.fulfill(content_type='application/javascript',body=ns['MOCK']) if 'supabase-js' in r.request.url else r.abort() if r.request.url.startswith('http') else r.continue_())
  pg=ctx.new_page();pg.on('pageerror',lambda e:errors.append(str(e)));pg.goto((ROOT/(role+'.html')).as_uri());pg.wait_for_timeout(1600);pages[role]=pg
 c,d=pages['customer'],pages['driver'];c.evaluate('S.tid=5001;S.v="track";render()')
 for status in ['preparing','ready','pickedup']:
  order['status']=status
  wait_read(c,'(s)=>TLB.order(5001).status===s',status)
  wait_read(d,'(s)=>TLB.order(5001).status===s',status)
  msg='Customer to driver '+status;c.locator('#ci').fill(msg);c.locator('#cisend').click()
  wait_read(d,'()=>TLB.unread(5001)>0')
  assert d.locator('.a-chat .dotb').inner_text().strip()=='1'
  d.locator('.a-chat').click();wait_read(d,'(s)=>document.querySelector("#ch").textContent.includes(s)',msg)
  assert d.evaluate('TLB.order(5001).chat.filter(x=>x.t===%s)[0].s'%json.dumps(msg))=='client'
  reply='Driver to customer '+status;d.locator('#ci').fill(reply);d.locator('.a-chat-modal .b').last.click()
  wait_read(c,'(s)=>document.querySelector("#ch").textContent.includes(s)',reply)
  assert c.evaluate('TLB.order(5001).chat.filter(x=>x.t===%s).length'%json.dumps(reply))==1
  assert len(T['order_chat'])==2*(['preparing','ready','pickedup'].index(status)+1)
  d.locator('.a-chat-modal button.round').first.click()
  print('PASS',ENGINE,status,'customer send -> unread badge -> driver opens/sees -> replies -> customer sees, no receiver reload',flush=True)
 for ctx in contexts:ctx.close()
 assert not errors,errors
 browser.close()
(OUT/(ENGINE+'-results.json')).write_text(json.dumps({'pass':True,'cases':checks,'errors':errors,'scope':'local isolated two-session shared DB; real Leaflet with local tiles; no live credentials or OS Safari'},indent=2))
