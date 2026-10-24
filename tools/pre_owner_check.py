"""Cross-engine, isolated regressions for the pre-owner audit; never connects to Supabase.
Uses current application/core and the existing C1/C2 fixtures. No live acceptance claims.
"""
from pathlib import Path
import os, subprocess, json
from playwright.sync_api import sync_playwright
ROOT=Path(__file__).resolve().parents[1]
OUT=Path(os.environ.get('AUDIT_OUT','/tmp/talabot-pre-owner'));OUT.mkdir(exist_ok=True,parents=True)
subprocess.run(['python3',str(ROOT/'tools/ui_hc_fixture.py'),str(OUT)],check=True)
FIX=(OUT/'customer-fixture.js').read_text()
subprocess.run(['python3',str(ROOT/'tools/driver_a_fixture.py'),str(OUT)],check=True)
DRIVER_FIX=(OUT/'review-fixture.js').read_text().replace("if(window.__EMPTY)","T.orders.find(o=>o.id==='ord1').is_gift=true;T.order_recipient=[{order_id:'ord1',name:'Test Recipient',phone:'+992900000099'}];if(window.__EMPTY)",1)
results=[]
with sync_playwright() as pw:
 for engine in ['chromium','webkit']:
  browser=getattr(pw,engine).launch()
  for width in ([] if os.environ.get('AUDIT_PART')=='driver' else [360,390,430]):
   errors=[]
   page=browser.new_page(viewport={'width':width,'height':844})
   page.on('pageerror',lambda e:errors.append(str(e)))
   page.clock.install()
   page.add_init_script("""window.__C_SCENE='loading';
   window.AudioContext=function(){this.state='suspended';this.resume=()=>Promise.reject(new Error('audio device unavailable'))};
   window.fetch=()=>Promise.resolve(new Response('',{status:200}));localStorage.setItem('tlb_lang','ru');""")
   def route(r):
    u=r.request.url
    if 'supabase-js' in u:r.fulfill(content_type='application/javascript',body=FIX)
    elif u.startswith('http'):r.abort()
    else:r.continue_()
   page.route('**/*',route)
   page.goto((ROOT/'customer.html').as_uri())
   page.wait_for_function("typeof ME!=='undefined'&&!!ME.phone&&TLB.orders().length>0")
   # Rejected audio resume must never become an unhandled rejection / blocking reload banner.
   page.evaluate("document.dispatchEvent(new Event('click'))")
   page.wait_for_timeout(80)
   assert not page.evaluate('!!window.__errShown'),errors
   logo=page.locator('img[src="assets/brand/talabot-ru.png"]')
   assert logo.count()>0
   assert logo.first.evaluate('(e)=>e.complete&&e.naturalWidth>0')
   page.evaluate("S.v='track';S.tid='ord1';render()")
   page.wait_for_timeout(60)
   assert page.evaluate('__C_CALLS.length')==1
   page.clock.fast_forward(10100);page.wait_for_timeout(60)
   assert page.evaluate('__C_ABORTS')==1
   assert 'недоступно' in page.locator('.c-track-age').inner_text()
   page.evaluate('__C_DELAY=0;__C_MODE="none"')
   page.clock.fast_forward(5000);page.wait_for_timeout(60)
   assert page.evaluate('__C_CALLS.length')==2
   assert page.locator('.c-track-map').evaluate('(e)=>e.hidden')
   # A pending request is canceled on background; a late reply cannot repaint the old page.
   page.evaluate("__C_DELAY=120000;Object.defineProperty(document,'hidden',{configurable:true,get:()=>true});document.dispatchEvent(new Event('visibilitychange'))")
   page.evaluate("Object.defineProperty(document,'hidden',{configurable:true,get:()=>false});document.dispatchEvent(new Event('visibilitychange'))")
   page.wait_for_timeout(60)
   page.evaluate("Object.defineProperty(document,'hidden',{configurable:true,get:()=>true});document.dispatchEvent(new Event('visibilitychange'))")
   page.wait_for_timeout(60)
   assert page.evaluate('__C_ABORTS')==2
   count=page.evaluate('__C_CALLS.length')
   page.clock.fast_forward(125000);page.wait_for_timeout(60)
   assert page.evaluate('__C_CALLS.length')==count
   assert page.locator('.c-track').count()==0
   page.evaluate("__C_DELAY=0;Object.defineProperty(document,'hidden',{configurable:true,get:()=>false});document.dispatchEvent(new Event('visibilitychange'))")
   page.wait_for_timeout(60)
   assert page.evaluate('__C_CALLS.length')==count+1
   page.evaluate("TLB.order('ord1').status='delivered';render()")
   count=page.evaluate('__C_CALLS.length')
   page.clock.fast_forward(30000);page.wait_for_timeout(60)
   assert page.evaluate('__C_CALLS.length')==count
   assert not page.evaluate('document.documentElement.scrollWidth>innerWidth')
   assert not errors,errors
   page.screenshot(path=str(OUT/f'{engine}-{width}.png'),full_page=True)
   results.append({'engine':engine,'width':width,'pass':True})
   print('PASS',engine,width,'audio rejection, original logo, C1 timeout/retry/null/background/return/end; no overflow/errors',flush=True)
   page.close()
  for width in [360,390,430]:
   page=browser.new_page(viewport={'width':width,'height':844});errors=[]
   page.on('pageerror',lambda e:errors.append(str(e)))
   page.add_init_script("window.__UI_CASE='delivery';localStorage.setItem('tlb_lang','ru');window.fetch=()=>Promise.resolve(new Response('',{status:200}))")
   def driver_route(r):
    if 'supabase-js' in r.request.url:r.fulfill(content_type='application/javascript',body=DRIVER_FIX)
    elif r.request.url.startswith('http'):r.abort()
    else:r.continue_()
   page.route('**/*',driver_route)
   page.goto((ROOT/'driver.html').as_uri())
   page.wait_for_selector('#a-sheet')
   page.wait_for_selector('.a-note a[href="tel:+992900000099"]')
   assert 'Test Recipient' in page.locator('.a-note').first.inner_text()
   # Inspect the link only: never dial even a fixture number.
   page.locator('#a-sheet-body').evaluate('(e)=>e.scrollTop=e.scrollHeight')
   assert not page.evaluate('document.documentElement.scrollWidth>innerWidth')
   # A smaller visual viewport exercises chat layout but is not a real iPhone keyboard.
   page.evaluate('chatOpen=true;render()')
   page.set_viewport_size({'width':width,'height':520})
   assert page.locator('.a-chat-modal').is_visible()
   page.locator('#ci').fill('Draft only — not sent')
   send=page.locator('.a-chat-modal > .row .b').last
   send.scroll_into_view_if_needed()
   box=send.bounding_box();assert box['y']>=0 and box['y']+box['height']<=520
   assert page.locator('#ci').input_value()=='Draft only — not sent'
   assert not page.evaluate('document.documentElement.scrollWidth>innerWidth')
   assert not errors,errors
   page.screenshot(path=str(OUT/f'{engine}-driver-{width}.png'),full_page=True)
   print('PASS',engine,width,'gift recipient link, driver sheet scroll, chat at reduced height; no calls sent',flush=True)
   page.close()
  browser.close()
(OUT/'results.json').write_text(json.dumps(results,indent=2))
