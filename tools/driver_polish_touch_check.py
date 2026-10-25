"""Delta gesture/short mission/cash display checks only, no rerun of the completed matrix."""
import driver_polish_check as S
from pathlib import Path
from playwright.sync_api import sync_playwright
import json,base64
out=S.OUT;results=[]
def check(ok,msg):
 assert ok,msg
 results.append(msg);print('PASS',msg,flush=True)
with sync_playwright() as pw:
 for engine in ['chromium','webkit']:
  b=getattr(pw,engine).launch();ctx=b.new_context(viewport={'width':390,'height':780},is_mobile=True,has_touch=True)
  ctx.add_init_script("window.__UI_CASE='pickup';localStorage.setItem('tlb_lang','ru');window.fetch=()=>Promise.reject(Error('isolated'));")
  def route(r):
   u=r.request.url
   if 'supabase-js' in u:r.fulfill(content_type='application/javascript',body=S.FIX+'\n'+S.WRAP)
   elif 'leaflet.js' in u:r.fulfill(content_type='application/javascript',body=(S.LEAF/'leaflet.js').read_text())
   elif 'leaflet.css' in u:r.fulfill(content_type='text/css',body=(S.LEAF/'leaflet.css').read_text())
   elif u.startswith('http'):r.abort()
   else:r.continue_()
  ctx.route('**/*',route);p=ctx.new_page();p.goto((S.ROOT/'driver.html').as_uri());p.wait_for_selector('#a-sheet');S.settle(p)
  # Real pointer events on the grip, distinct from touch-scrolling the content and map.
  x=S.rect(p,'#a-grip');p.mouse.move(190,x['y']+20);p.mouse.down();p.mouse.move(190,x['y']+280,steps=12);p.mouse.up();S.settle(p)
  check(p.evaluate("ASnap==='collapsed'") and p.evaluate("__UI_RPCS.filter(x=>x[0]==='set_order_status').length===0"),engine+' grip drag collapses without confirmation')
  p.locator('#a-grip').press('Home');S.settle(p);p.locator('#a-sheet-body').evaluate('(e)=>e.scrollTop=e.scrollHeight');S.settle(p)
  d=S.rect(p,'.a-details-link');dk=S.rect(p,'#a-dock');check(d['y']+d['height']<=dk['y'] and p.evaluate('scrollY')==0,engine+' sheet scroll reaches details above dock without page scroll')
  p.set_viewport_size({'width':390,'height':520});p.locator('#a-grip').press('End');S.settle(p);h=S.rect(p,'.a-header');sh=S.rect(p,'#a-sheet');dk=S.rect(p,'#a-dock')
  check(sh['y']>=h['height']+110 and abs(sh['y']+sh['height']-dk['y'])<2,engine+' short mission keeps map strip and separate dock')
  p.set_viewport_size({'width':390,'height':780});p.locator('#a-grip').press('Home');S.settle(p)
  p.evaluate("async()=>{const x=__UI_TABLES.orders.find(x=>x.id==='ord1');Object.assign(x,{total:100,points_value:20,wallet_used:10,driver_payout:20});await TLB.reload()}");S.settle(p)
  check(p.evaluate('due(aTask())')==90 and '90,00' in p.locator('.a-money-secondary').inner_text(),engine+' points-inclusive total not discounted twice in displayed collection')
  check(p.locator('.a-cash-detail').count()==1 and '120.00' in p.locator('.a-cash-detail').inner_text(),engine+' existing cash breakdown kept separately')
  # Content scroll and handle dragging never dispatch a stage mutation.
  check(p.evaluate("__UI_RPCS.filter(x=>x[0]==='set_order_status').length===0"),engine+' scroll/drag never confirms pickup')
  ctx.close();b.close()
(out/'polish-extra-results.json').write_text(json.dumps({'checks':len(results),'results':results},indent=2))
