"""Affected Driver A polish only. Isolated real core + mock services, Chromium/WebKit; not a real iPhone."""
import runpy,json,time,os,subprocess,sys
from pathlib import Path
from playwright.sync_api import sync_playwright
ROOT=Path(__file__).resolve().parents[1];OUT=Path('/tmp/talabot-driver-polish');OUT.mkdir(exist_ok=True)
mod=runpy.run_path(str(ROOT/'tools/driver_polish_preview.py'));FIX=mod['FIX'];WRAP=mod['WRAP'];LEAF=Path(os.environ.get('MAP_LEAFLET','/tmp/talabot-leaflet'))
results=[]
def check(ok,msg):
 assert ok,msg
 results.append(msg);print('PASS',msg,flush=True)
def wait(p,predicate):
 end=time.monotonic()+12
 while time.monotonic()<end:
  if p.evaluate(predicate):return
  p.wait_for_timeout(80)
 raise AssertionError(predicate)
def settle(p):p.wait_for_timeout(280)
def rect(p,sel):return p.locator(sel).bounding_box()
if __name__=='__main__':
 with sync_playwright() as pw:
  for eng in os.environ.get('POLISH_ENGINES','chromium,webkit').split(','):
   browser=getattr(pw,eng).launch()
   for w in map(int,os.environ.get('POLISH_WIDTHS','360,390,430').split(',')):
    ctx=browser.new_context(viewport={'width':w,'height':780},is_mobile=True,has_touch=True,permissions=['geolocation'],geolocation={'latitude':38.56,'longitude':68.78},user_agent='Mozilla/5.0 (iPhone; CPU iPhone OS 18_7 like Mac OS X) AppleWebKit/605.1.15 Version/18.0 Mobile/15E148 Safari/604.1')
    ctx.add_init_script("window.__UI_CASE='pickup';localStorage.setItem('tlb_lang','ru');window.fetch=()=>Promise.reject(Error('offline fixture'));")
    def intercept(r):
     u=r.request.url
     if 'supabase-js' in u:r.fulfill(content_type='application/javascript',body=FIX+'\n'+WRAP)
     elif 'leaflet.js' in u:r.fulfill(content_type='application/javascript',body=(LEAF/'leaflet.js').read_text())
     elif 'leaflet.css' in u:r.fulfill(content_type='text/css',body=(LEAF/'leaflet.css').read_text())
     elif 'tile.openstreetmap.org' in u:r.fulfill(content_type='image/png',body=__import__('base64').b64decode('iVBORw0KGgoAAAANSUhEUgAAAAEAAAABCAQAAAC1HAwCAAAAC0lEQVR42mP8/x8AAwMCAO+ip1sAAAAASUVORK5CYII='))
     elif u.startswith('http'):r.abort()
     else:r.continue_()
    ctx.route('**/*',intercept);p=ctx.new_page();errs=[];p.on('pageerror',lambda e:errs.append(str(e)))
    p.goto((ROOT/'driver.html').as_uri());p.wait_for_selector('#a-sheet');wait(p,"()=>typeof DM!=='undefined'&&DM&&DM!==1&&typeof DM.getCenter==='function'")
    p.evaluate("async()=>{const x=__UI_TABLES.orders.find(x=>x.id==='ord1');x.lat=38.58;x.lng=68.80;Object.assign(GEO,{state:'ok',lat:38.56,lng:68.78,acc:10,at:Date.now()});await TLB.reload()}");settle(p)
    tag=f'{eng} {w}'
    check(rect(p,'.a-header')['height']<=58,tag+' compact header')
    check(p.locator('.a-stages details').get_attribute('open') is None and p.locator('.a-stage-current b').inner_text().strip()=='Заберите заказ',tag+' current stage, other stages collapsed '+repr([p.locator('.a-stages details').get_attribute('open'),p.locator('.a-stage-current').inner_text()]))
    p.locator('.a-stages summary').click();settle(p);check(p.locator('.a-stages li').count()==4 and p.locator('.a-stages li.current').inner_text().startswith('2'),tag+' four steps accessible')
    p.evaluate('render()');settle(p);check(p.locator('.a-stages details').get_attribute('open') is not None,tag+' expansion survives render')
    p.locator('.a-stages summary').click();settle(p)
    check(p.locator('#a-sheet').inner_text().count('Ваш заработок')==1 and p.locator('#a-sheet').inner_text().count('Получаете от клиента')==1,tag+' earnings once, collection separate')
    boxes=[rect(p,x) for x in ['.a-navigation','.a-call','.a-chat']];check(max(b['height'] for b in boxes)-min(b['height'] for b in boxes)<1 and all(b['height']>=44 for b in boxes),tag+' aligned tools / 44px targets')
    p.screenshot(path=str(OUT/f'mission-{eng}-{w}.png'))
    # Keyboard collapse/expand is same public handle binding, not direct DOM styling.
    p.locator('#a-grip').focus();p.locator('#a-grip').press('End');settle(p)
    sh=rect(p,'#a-sheet');hd=rect(p,'.a-header');dk=rect(p,'#a-dock')
    check(sh['y']-hd['height']>=260 and abs(sh['y']+sh['height']-dk['y'])<2,tag+' collapsed map space / dock separation')
    before=p.evaluate('({lat:DM.getCenter().lat,lng:DM.getCenter().lng,z:DM.getZoom()})');p.mouse.move(w/2,150);p.mouse.down();p.mouse.move(w/2+40,180,steps=5);p.mouse.up();settle(p)
    after=p.evaluate('({lat:DM.getCenter().lat,lng:DM.getCenter().lng,z:DM.getZoom()})');check(before!=after,tag+' map pan while panel collapsed')
    p.evaluate('render()');settle(p);check(p.evaluate('ASnap')=='collapsed' and p.evaluate('DM.getZoom()')==after['z'],tag+' collapse / map zoom kept after render')
    p.screenshot(path=str(OUT/f'collapsed-{eng}-{w}.png'))
    p.locator('#a-grip').press('Home');settle(p)
    p.locator('.a-navigation').click();p.wait_for_selector('.n-provider');settle(p)
    check(p.locator('.n-provider').count()==3 and p.locator('.n-provider a').count()==6,tag+' external choices kept')
    check(p.locator('.n-provider .n-open').count()==3 and p.locator('.n-provider .n-web').count()==3 and not p.locator('#a-map-state').is_visible(),tag+' primary / secondary links and one mode note')
    check('зависит от телефона' in p.locator('.n-hint').inner_text() and 'браузере' not in p.locator('.n-hint').inner_text(),tag+' no browser-only promise')
    check(p.locator('.n-provider').evaluate_all('(els)=>els.every(e=>{let b=e.getBoundingClientRect();return b.width<=innerWidth})'),tag+' provider rows fit')
    p.screenshot(path=str(OUT/f'chooser-{eng}-{w}.png'))
    p.set_viewport_size({'width':w,'height':520});settle(p)
    check(p.locator('.n-heading button').is_visible() and rect(p,'.n-heading button')['y']>=0 and rect(p,'.n-heading button')['y']+44<=520,tag+' close stays visible on short viewport')
    p.locator('.n-body').evaluate('(e)=>e.scrollTop=e.scrollHeight');check(p.locator('.n-provider').last.locator('.n-web').is_visible(),tag+' chooser scroll on short viewport')
    p.screenshot(path=str(OUT/f'short-{eng}-{w}.png'))
    p.keyboard.press('Escape');settle(p);check(p.locator('.n-chooser').count()==0,tag+' Escape closes chooser')
    p.set_viewport_size({'width':w,'height':780});settle(p)
    # affected receipt confirmation only: slow/error/normal server reply + duplicate press.
    p.evaluate("()=>{window.__UI_DELAY=650;window.__UI_FAIL='set_order_status';window.__run1=aRun();aRun()}");p.wait_for_timeout(120)
    check(p.locator('.a-confirmed').count()==0 and p.evaluate("__UI_RPCS.filter(x=>x[0]==='set_order_status').length")==1,tag+' pending has no success / duplicate request blocked')
    wait(p,'()=>!AFlight');check(p.locator('.a-error').count()==1 and p.evaluate('aTaskStage(aTask())')==2,tag+' server error keeps pickup stage')
    p.evaluate("()=>{__UI_FAIL='';__UI_DELAY=500;window.__run2=aRun();aRun()}");p.wait_for_timeout(100);check(p.locator('.a-confirmed').count()==0,tag+' success waits for server')
    wait(p,'()=>!AFlight');settle(p)
    check(p.evaluate('aTaskStage(aTask())')==3 and p.locator('.a-confirmed').count()==1,tag+' pickup success advances to customer stage')
    check(rect(p,'.a-confirmed')['y']+rect(p,'.a-confirmed')['height']<rect(p,'#swp')['y'] and p.evaluate("__UI_RPCS.filter(x=>x[0]==='set_order_status').length")==2,tag+' success away from swipe / single retry')
    check(p.locator('#a-sheet').inner_text().count('Ваш заработок')==1 and p.locator('#a-sheet').inner_text().count('Получаете от клиента')==1,tag+' after pickup money not duplicated')
    check(p.evaluate("__navCalls.every(x=>x.op==='config'||x.op==='links')"),tag+' no internal route requests')
    check(not errs,tag+' no page errors '+repr(errs))
    p.screenshot(path=str(OUT/f'success-{eng}-{w}.png'));ctx.close()
   browser.close()
 (OUT/'polish-results.json').write_text(json.dumps({'checks':len(results),'results':results,'limits':'Isolated Chromium/WebKit simulation; no live server mutation, GPS or native apps / actual iPhone.'},ensure_ascii=False,indent=2))
 print('TOTAL',len(results))
