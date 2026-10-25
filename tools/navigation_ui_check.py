"""Affected navigation regression only. Real app/core/map, generated server contracts, isolated existing UI fixture.
Chromium Android UA + WebKit iPhone UA at 360/390/430. No native apps, real device, provider, live DB or messages.
Run node tools/navigation_contract_check.mjs first.
"""
import os,json,sys,subprocess,base64,time
from pathlib import Path
from playwright.sync_api import sync_playwright
ROOT=Path(__file__).resolve().parents[1];OUT=Path('/tmp/talabot-nav-ui');OUT.mkdir(exist_ok=True)
LEAF=Path(os.environ.get('MAP_LEAFLET','/workspace/scratch/72a93aea6c2a/hc-evidence/leaflet'))
subprocess.run([sys.executable,str(ROOT/'tools/driver_a_fixture.py'),str(OUT)],check=True,capture_output=True)
FIX=(OUT/'review-fixture.js').read_text();DATA=json.loads(Path('/tmp/talabot-navigation-fixture.json').read_text())
PNG=base64.b64decode('iVBORw0KGgoAAAANSUhEUgAAAAEAAAABCAQAAAC1HAwCAAC0lEQVR42mP8/x8AAwMCAO+ip1sAAAAASUVORK5CYII=') if False else base64.b64decode('iVBORw0KGgoAAAANSUhEUgAAAAEAAAABCAQAAAC1HAwCAAAAC0lEQVR42mP8/x8AAwMCAO+ip1sAAAAASUVORK5CYII=')
WRAP='''
(function(){const old=supabase.createClient;supabase.createClient=function(){const c=old.apply(this,arguments);window.__navCalls=[];window.__navMode='internal';window.__navVersion=1;
c.functions={invoke:async function(name,opt){const b=opt.body;window.__navCalls.push(b);const D=window.__NAV_DATA;let config={...(window.__navMode==='disabled'?D.disabled:D.internal),revision:String(window.__navVersion)};
 if(b.op==='config')return window.__navMode==='service_missing'?{data:null,error:{message:'missing'}}:{data:config,error:null};
 if(b.op==='links')return {data:{config,links:(b.to[0]>40?D.linksCustomer:D.linksRestaurant)},error:null};
 if(window.__navMode==='delay')await new Promise((resolve,reject)=>{window.__navRelease=resolve;opt.signal?.addEventListener('abort',()=>reject(new Error('aborted')),{once:true})});
 if(window.__navMode==='fail')throw Error('offline');
 if(window.__navMode==='quota')return {data:{mode:'tracking',reason:'quota',retry_after_s:120,config:{...config,mode:'tracking',reason:'quota'}},error:null};
 return {data:{...D.route,coords:window.__useRequestPath?[b.from,b.to]:D.route.coords,config,calculated_at:Date.now()},error:null};}};return c;}})();
'''
results=[]
def wait(pg, predicate, timeout=10000):
 end=time.monotonic()+timeout/1000
 while time.monotonic()<end:
  if pg.evaluate(predicate):return
  pg.wait_for_timeout(100)
 raise AssertionError({'predicate':predicate,'state':pg.evaluate('()=>window.__routeLayer?.state()'),'calls':pg.evaluate('()=>window.__navCalls'),'label':pg.locator('#a-map-state').inner_text() if pg.locator('#a-map-state').count() else '', 'errors':pg.evaluate('()=>window.__navErrors||[]')})
def check(c,label):
 assert c,label
 results.append(label);print('PASS',label,flush=True)
with sync_playwright() as pw:
 for engine in ['chromium','webkit']:
  browser=getattr(pw,engine).launch()
  for width in [int(x) for x in os.environ.get('NAV_WIDTHS','360,390,430').split(',')]:
   ua='Mozilla/5.0 (iPhone; CPU iPhone OS 18_7 like Mac OS X) AppleWebKit/605.1.15 Version/18.0 Mobile/15E148 Safari/604.1' if engine=='webkit' else 'Mozilla/5.0 (Linux; Android 14; Pixel 7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/130.0.0.0 Mobile Safari/537.36'
   ctx=browser.new_context(viewport={'width':width,'height':844},user_agent=ua,has_touch=True,is_mobile=True,permissions=['geolocation'],geolocation={'latitude':38.56,'longitude':68.78,'accuracy':10})
   ctx.add_init_script("window.__UI_CASE='pickup';localStorage.setItem('tlb_lang','ru');window.__NAV_DATA="+json.dumps(DATA)+";window.fetch=()=>Promise.resolve(new Response('',{status:200}));")
   def intercept(r):
    u=r.request.url
    if 'supabase-js' in u:r.fulfill(content_type='application/javascript',body=FIX+'\n'+WRAP)
    elif 'leaflet.js' in u:r.fulfill(content_type='application/javascript',body=(LEAF/'leaflet.js').read_text())
    elif 'leaflet.css' in u:r.fulfill(content_type='text/css',body=(LEAF/'leaflet.css').read_text())
    elif 'tile.openstreetmap.org' in u:r.fulfill(content_type='image/png',body=PNG)
    elif u.startswith('http'):r.abort()
    else:r.continue_()
   ctx.route('**/*',intercept);pg=ctx.new_page();errors=[];pg.on('pageerror',lambda e:errors.append(str(e)))
   pg.goto((ROOT/'driver.html').as_uri());pg.wait_for_selector('#a-sheet');wait(pg, "()=>typeof DM!=='undefined'&&DM&&DM!==1&&typeof DM.getCenter==='function'")
   pg.evaluate("()=>{const x=window.__UI_TABLES.orders.find(x=>x.id==='ord1');x.lat=40.27934;x.lng=69.6332017;Object.assign(GEO,{state:'ok',lat:38.56,lng:68.78,acc:10,at:Date.now()});TLB.reload()}")
   pg.evaluate("aSnap('full')");pg.locator('.a-navigation').click();pg.wait_for_selector('.n-provider');check(pg.locator('.n-provider').count()==3,f'{engine} {width}: three coordinate-only external choices')
   pg.screenshot(path=str(OUT/f'chooser-{engine}-{width}.png'),full_page=True)
   rest_links=pg.locator('.n-provider a').evaluate_all('(els)=>els.map(e=>e.href)')
   check(all('38.56' in u and '68.78' in u and 'Душанбе' not in u for u in rest_links),f'{engine} {width}: all links target actual restaurant')
   check(pg.locator('.n-provider a').count()==6 and 'зависит от телефона' in pg.locator('.md').inner_text(),f'{engine} {width}: primary / website links, no browser-only or installation detection claim')
   pg.get_by_role('button',name='Внутри TALABOT',exact=True).click();wait(pg, "()=>__routeLayer.state().mode==='internal'",timeout=10000)
   check(pg.locator('#dmap path.a-route').count()==1 and 'примерно' in pg.locator('#a-map-state').inner_text(),f'{engine} {width}: internal route on existing map with approximate ETA')
   check(not pg.evaluate('document.documentElement.scrollWidth>innerWidth'),f'{engine} {width}: no horizontal overflow')
   if width==390:
    before=len(pg.evaluate('window.__navCalls.filter(x=>x.from)'))
    pg.evaluate("()=>{Object.assign(GEO,{lat:38.5625,lng:68.785,at:Date.now()});render()}")
    wait(pg,"()=>document.querySelector('#a-map-state').textContent.includes('0.5')")
    check(len(pg.evaluate('window.__navCalls.filter(x=>x.from)'))==before,f'{engine}: GPS progress updates remaining estimate locally')
    pg.evaluate("()=>{window.__realNavNow=Date.now;window.__navOffset=121000;Date.now=()=>window.__realNavNow()+window.__navOffset;Object.assign(GEO,{lat:38.58,lng:68.77,at:Date.now()});render()}")
    wait(pg,"()=>__routeLayer.state().reason==='off_route'")
    check('прибытия недоступно' in pg.locator('#a-map-state').inner_text(),f'{engine}: deviation immediately suppresses old ETA')
    check(len(pg.evaluate('window.__navCalls.filter(x=>x.from)'))==before,f'{engine}: off-route requires sustained evidence before spending')
    pg.evaluate("()=>{window.__useRequestPath=true;window.__navOffset+=6000;GEO.at=Date.now();render()}")
    wait(pg,"()=>window.__navCalls.filter(x=>x.from).length>1&&!__routeLayer.state().inflight")
    wait(pg,"()=>__routeLayer.state().mode==='internal'")
    check(len(pg.evaluate('window.__navCalls.filter(x=>x.from)'))==before+1,f'{engine}: sustained deviation requests one new route')
    pg.evaluate("render();render();render()")
    check(len(pg.evaluate('window.__navCalls.filter(x=>x.from)'))==before+1,f'{engine}: no duplicate reroute on repeated render')
    pg.evaluate("GEO.at=Date.now()-31000;render()")
    wait(pg,"()=>__routeLayer.state().reason==='gps_unavailable'")
    check('прибытия недоступно' in pg.locator('#a-map-state').inner_text(),f'{engine}: stale position removes arrival estimate')
    pg.evaluate("Object.assign(GEO,{lat:38.56,lng:68.78,at:Date.now()});render()")
    wait(pg,"()=>__routeLayer.state().mode==='internal'")
   pg.screenshot(path=str(OUT/f'internal-{engine}-{width}.png'),full_page=True)
   # Central disable clears old route/ETA. No change to the order status.
   pg.evaluate("async()=>{window.__navMode='disabled';window.__navVersion++;await __routeLayer.refreshPolicy();render()}")
   wait(pg, "()=>__routeLayer.state().mode==='tracking'&&document.querySelectorAll('#dmap path.a-route').length===0")
   check('прибытия недоступно' in pg.locator('#a-map-state').inner_text() and pg.evaluate("aTask().status")=='ready',f'{engine} {width}: disabled -> tracking without ETA or order mutation')
   if width==390:
    pg.evaluate("async()=>{window.__navMode='service_missing';await __routeLayer.refreshPolicy();render()}")
    missing_before=len(pg.evaluate('window.__navCalls'))
    pg.wait_for_timeout(2100)
    check(len(pg.evaluate('window.__navCalls'))==missing_before,f'{engine}: unavailable function has bounded policy retry, no request loop')
    for failure in ['fail','quota']:
     pg.evaluate("async(m)=>{window.__navMode=m;window.__navVersion++;Object.assign(GEO,{state:'ok',lat:38.56,lng:68.78,acc:10,at:Date.now()});await __routeLayer.refreshPolicy();aNavigationInside()}",failure)
     wait(pg, "()=>__routeLayer.state().mode==='tracking'&&!__routeLayer.state().inflight")
     pg.wait_for_timeout(300)
     check('прибытия недоступно' in pg.locator('#a-map-state').inner_text(),f'{engine}: {failure} no stale ETA')
    # Regression of ordinary services under quota failure, not a repeat of accepted two-session repair.
    pg.evaluate("aChatSend(aTask().id,'Navigation-quota regression')");wait(pg, "()=>window.__UI_RPCS.some(x=>x[0]==='chat')")
    check(pg.evaluate("window.__UI_TABLES.order_chat.some(x=>x.body==='Navigation-quota regression')"),f'{engine}: chat service remains available under quota')
    pg.evaluate("async()=>{chatOpen=false;window.__navMode='delay';window.__navVersion++;Object.assign(GEO,{state:'ok',lat:38.56,lng:68.78,acc:10,at:Date.now()});await __routeLayer.refreshPolicy();aNavigationInside()}")
    wait(pg,"()=>__routeLayer.state().inflight")
    pg.evaluate('aRun()');wait(pg,"()=>mine().status==='pickedup'")
    wait(pg,"()=>!__routeLayer.state().inflight")
    pg.evaluate("()=>{window.__navRelease?.();window.__navMode='quota';render()}")
    check(not pg.evaluate('__routeLayer.state().hasRoute'),f'{engine}: pickup cancels pending restaurant route and suppresses late response')
    pg.evaluate('aNavigationOpen()');pg.wait_for_selector('.n-provider');customer_links=pg.locator('.n-provider a').evaluate_all('(els)=>els.map(e=>e.href)')
    check(all('40.27934' in u and '69.6332017' in u for u in customer_links),f'{engine}: same choices switch to customer pin after pickup')
    pg.evaluate('aNavigationClose();aRun()');wait(pg, '()=>aTaskStage(aTask())===4')
    pg.evaluate('aRun()');pg.wait_for_selector('#dvok');pg.locator('#dvok').click();wait(pg, "()=>window.__UI_TABLES.orders.find(x=>x.id==='ord1').status==='delivered'")
    check(pg.evaluate("window.__UI_RPCS.some(x=>x[0]==='deliver_order')"),f'{engine}: original confirmation and delivery service work under quota')
   check(not errors,f'{engine} {width}: no JavaScript errors {errors}')
   pg.screenshot(path=str(OUT/f'navigation-{engine}-{width}.png'),full_page=True)
   ctx.close()
  browser.close()
Path('/tmp/talabot-navigation-ui-result.json').write_text(json.dumps({'checks':len(results),'results':results},ensure_ascii=False,indent=2))
print('NAVIGATION UI CHECK OK',len(results))
