"""Automatic refreshes must not wipe admin forms or move the page (UAT batch 1, iPhone reports 15 Oct).
Runs on a read-only preview built by tools/build_preview.py (demo data; every 10 s a demo courier goes on/offline,
so every screen is really rebuilt, as on a busy day).
  python3 tools/form_keep_check.py <preview_dir> [--quick]      (--quick skips the two slow real-time parts, ~90 s)
Real data refreshes are made by changing the demo tables and firing the app's own "page visible again" refresh,
or by waiting for the 10 s polling. Chromium with a phone viewport and touch; NOT Safari/WebKit."""
import os,sys,time
from playwright.sync_api import sync_playwright
d=os.path.abspath(sys.argv[1]);quick='--quick' in sys.argv;fails=[];npass=0
def ok(c,m):
    global npass
    print(('PASS ' if c else 'FAIL ')+m)
    if c: npass+=1
    else: fails.append(m)
FORMS=[ # name, open, [(selector, value)]
 ('promo (new)',"tab='c';showAddP=true;render()",[('#pcode','SALE10'),('#pkind','fixed'),('#pval','15'),('#pmin','100'),('#pmax','50'),('#pfr','2026-10-20'),('#pto','2026-10-30')]),
 ('banner (new)',"tab='b';BE=null;BD=null;showAddB=true;render()",[('#bt','Скидка выходного дня'),('#bpl','bottom'),('#bfr','2026-10-21'),('#bto','2026-11-05'),('#bo','3')]),
 ('banner (edit)',"tab='b';showAddB=false;render();openBE('bn1')",[('#app input[type=text]','Новый заголовок'),('#app input[type=date] >> nth=0','2026-10-22'),('#app input[type=date] >> nth=1','2026-11-06')]),
 ('happy hour (new)',"tab='y';HE=null;render();heOpen()",[('#he_t','Обеденный час'),('#app input[type=time] >> nth=0','12:30'),('#app input[type=time] >> nth=1','15:45'),('#app input[min="1"][max="90"]','35')]),
 ('happy hour (edit)',"tab='y';HE=null;render();heOpen(TLB.happyHours()[0]&&TLB.happyHours()[0].id)",[('#he_t','Вечер'),('#app input[type=time] >> nth=0','18:10'),('#app input[min="1"][max="90"]','25')]),
 ('loyalty settings',"tab='y';HE=null;render()",[('#ly_cashback_pct','4.5'),('#ly_loyalty_min_order','17')]),
 ('new store',"tab='s';E=null;showAddS=true;render()",[('#sn','Тест кафе'),('#sp','+992900001122')]),
]
def fill(pg,fields):
    for s,v in fields:
        el=pg.locator(s).first
        if el.evaluate("e=>e.tagName")=='SELECT': el.select_option(v)
        else: el.fill(v)
def vals(pg,fields): return [pg.locator(s).first.input_value() for s,_ in fields]
def blur(E): E("()=>document.activeElement&&document.activeElement.blur()")
def settle(E):  # the redraw waits for 1.2 s of calm after touch/scroll/rotation: make it immediate for forced checks
    E("()=>{lastTouch=0;userAt=0}")
def watch(E): E("()=>{window.__rb=0;window.__mo&&__mo.disconnect();window.__mo=new MutationObserver(m=>{if(m.some(x=>x.target.id=='app'))__rb++});__mo.observe($('app'),{childList:true})}")
def rb(E): return E("()=>window.__rb")
def scroll_to(E,y): E("y=>{const m=document.documentElement.scrollHeight-innerHeight;scrollTo(0,Math.min(y,m))}",y);return E("()=>scrollY")
def real_refresh(pg,E,js):  # change the demo data, then the app's own refresh path (visibilitychange -> refresh -> TLB.on -> autoR)
    E("()=>{const T=window.__pvTables;"+js+"}");E("()=>document.dispatchEvent(new Event('visibilitychange'))");pg.wait_for_timeout(2900)
def new_page(b,vw,lang):
    pg=b.new_page(viewport={'width':vw[0],'height':vw[1]},is_mobile=True,has_touch=True,device_scale_factor=2);errs=[]
    pg.on('pageerror',lambda e:errs.append(str(e)));pg.on('dialog',lambda x:x.accept())
    pg.route('**/*',lambda rt,rq:(rt.abort() if rq.url.startswith('http') else rt.continue_()))
    pg.goto('file://'+d+'/admin.html');pg.wait_for_timeout(2500)
    if lang=='en': pg.evaluate("()=>TLB.setLang('en')");pg.wait_for_timeout(300)
    return pg,errs
def forms_pass(pg,E,tag):
    for name,open_js,fields in FORMS:
        E("()=>{"+open_js+"}");pg.wait_for_timeout(120);fill(pg,fields);blur(E)
        y0=scroll_to(E,260);watch(E)
        for i in range(5): E("()=>{lastTouch=0;userAt=0;LASTH='';autoR()}");pg.wait_for_timeout(60)   # LASTH='' = the data changed: a real rebuild
        pg.wait_for_timeout(150)
        ok(rb(E)>=5,'%s %s: 5 automatic rebuilds happened (%d)'%(tag,name,rb(E)))
        ok(vals(pg,fields)==[v for _,v in fields],'%s %s: values kept %s'%(tag,name,vals(pg,fields)))
        ok(abs(E("()=>scrollY")-y0)<=1,'%s %s: scroll kept (%s -> %s)'%(tag,name,y0,E("()=>scrollY")))
    ok(E("()=>document.documentElement.scrollWidth<=innerWidth+1"),'%s: no horizontal page scroll'%tag)
with sync_playwright() as p:
    b=p.chromium.launch()
    # ======== 1. every form, RU+EN, portrait+landscape, 360/390/430 ========
    for vw,lang in [((390,844),'ru'),((844,390),'ru'),((390,844),'en'),((844,390),'en'),((360,780),'ru'),((430,932),'en')]:
        pg,errs=new_page(b,vw,lang);E=pg.evaluate;tag='[%dx%d %s]'%(vw[0],vw[1],lang)
        forms_pass(pg,E,tag)
        ok(not errs,tag+' no JS errors '+str(errs[:2]));pg.close()
    # ======== 2. behaviour details (390 portrait, RU) ========
    pg,errs=new_page(b,(390,844),'ru');E=pg.evaluate
    # 2a. an automatic redraw that changes nothing on screen does not touch the page
    E("()=>{tab='c';showAddP=true;render()}");pg.fill('#pcode','SAME1');blur(E);watch(E);E("()=>{lastTouch=0;userAt=0;autoR()}")
    ok(rb(E)==0 and pg.input_value('#pcode')=='SAME1','2a: refresh with nothing new on this screen = page not rebuilt at all')
    # 2b. postponed while a field is in use / finger on screen / rotation / keyboard
    pg.focus('#pfr');watch(E);E("()=>{lastTouch=0;LASTH='';autoR()}")
    ok(rb(E)==0,'2b: no rebuild while the date field is open (picker)');blur(E);pg.wait_for_timeout(1800)
    ok(rb(E)>=1 and pg.input_value('#pcode')=='SAME1','2b: rebuilt after the field closed, input kept')
    for ev,label in [("document.dispatchEvent(new Event('touchstart'))",'finger on screen'),("window.dispatchEvent(new Event('resize'))",'rotation/resize'),("window.dispatchEvent(new Event('orientationchange'))",'orientationchange'),("visualViewport.dispatchEvent(new Event('resize'))",'keyboard (visual viewport)')]:
        watch(E);E("()=>{LASTH='';"+ev+";autoR()}");n0=rb(E);pg.wait_for_timeout(1900)
        ok(n0==0 and rb(E)>=1,'2b: rebuild waits while %s, then happens (%d -> %d)'%(label,n0,rb(E)))
    # 2c. user actions on the same screen keep what was typed elsewhere on it
    E("()=>{tab='y';HE=null;render()}");pg.fill('#ly_loyalty_min_order','17');blur(E)
    pg.locator('#app button[onclick="heOpen()"]').click();pg.wait_for_timeout(200)
    ok(pg.input_value('#ly_loyalty_min_order')=='17' and E("()=>!!HE"),'2c: opening the happy-hour form keeps the typed points setting 17')
    E("()=>{HE=null;render()}")
    # 2d. nothing is carried to another record / a closed form
    E("()=>{tab='c';showAddP=true;render()}");pg.fill('#pcode','GONE1');E("()=>{showAddP=false;render();showAddP=true;render()}")
    ok(pg.input_value('#pcode')=='','2d: closing and reopening the promo form starts empty')
    E("()=>{tab='y';HE=null;render();heOpen(TLB.happyHours()[0].id)}");pg.fill('#he_t','Чужое');E("()=>{HE=null;render();heOpen()}")
    ok(pg.input_value('#he_t')=='','2d: a new happy hour does not inherit the title typed in another one')
    E("()=>{HE=null;render()}")
    # 2e. language switch (a redraw from the app) keeps typed values
    E("()=>{tab='c';showAddP=true;render()}");pg.fill('#pcode','LANG1');pg.fill('#pfr','2026-10-25');blur(E);E("()=>TLB.setLang('en')");pg.wait_for_timeout(1800)
    ok(pg.input_value('#pcode')=='LANG1' and pg.input_value('#pfr')=='2026-10-25','2e: switching RU/EN keeps typed values');E("()=>TLB.setLang('ru')");pg.wait_for_timeout(1800)
    E("()=>{showAddP=false;render()}")
    # 2f. "open order" buttons now really go to the top (inline scrollTo used to scroll the button)
    E("()=>{tab='r';rfl='all';render()}");scroll_to(E,600)
    btn=E("()=>{const b=[...document.querySelectorAll('#app button')].find(x=>(x.getAttribute('onclick')||'').startsWith('D=')&&(x.getAttribute('onclick')||'').includes('window.scrollTo(0,0)'));if(!b)return null;b.click();return true}")
    pg.wait_for_timeout(200);ok(btn and E("()=>scrollY")==0 and E("()=>!!D"),'2f: opening an order from the ratings list shows it from the top')
    E("()=>{D=null;tab='y';render()}")
    # ======== 3. someone else saves on the server meanwhile: nothing typed is lost silently ========
    pg.fill('#ly_cashback_pct','9');blur(E)
    real_refresh(pg,E,"T.app_settings.find(x=>x.key=='cashback_pct').value='2'")
    ok(pg.input_value('#ly_cashback_pct')=='9','3a: points setting: the typed 9 stays after the server changed it to 2')
    ok(E("()=>{const n=document.querySelector('.confn[data-for=\"ly_cashback_pct\"]');return !!n&&n.textContent.includes('«2»')}"),'3a: a notice under the field shows the server value «2»')
    real_refresh(pg,E,"T.app_settings.find(x=>x.key=='loyalty_rate_reward').value='7'")
    ok(pg.input_value('#ly_cashback_pct')=='9' and E("()=>document.querySelectorAll('.confn[data-for=\"ly_cashback_pct\"]').length")==1,'3a: value and one notice survive further refreshes')
    E("()=>document.querySelector('.confn[data-for=\"ly_cashback_pct\"] button').click()")
    ok(pg.input_value('#ly_cashback_pct')=='2' and not E("()=>!!document.querySelector('.confn')"),'3a: «use the server value» puts 2 and removes the notice')
    # banner edited by someone else
    E("()=>{tab='b';render();openBE('bn1')}");pg.fill('#app input[type=text]','Моё название');blur(E)
    real_refresh(pg,E,"const x=T.banners.find(x=>x.id=='bn1');x.title='Чужое название';x.sort=9")
    ok(pg.locator('#app input[type=text]').first.input_value()=='Моё название','3b: banner editor: my unsaved title stays')
    txt=E("()=>{const n=document.querySelector('#app .confn');return n?n.innerText:''}")
    ok('Чужое название' in txt and '9' in txt,'3b: banner editor: a notice lists what changed on the server')
    real_refresh(pg,E,"T.banners=T.banners.filter(x=>x.id!='bn1')")
    ok(E("()=>BE=='bn1'") and pg.locator('#app input[type=text]').first.input_value()=='Моё название' and 'удалена' in E("()=>document.querySelector('#app .confn').innerText") and not E("()=>[...document.querySelectorAll('#app button')].some(b=>(b.getAttribute('onclick')||'')=='bannerSave()')"),'3c: banner deleted on the server: editor stays with my values, notice, no save button')
    E("()=>{BE=null;BD=null;tab='y';render()}")
    # happy hour edited by someone else
    E("()=>heOpen(TLB.happyHours()[0].id)");pg.fill('#app input[min=\"1\"][max=\"90\"]','33');blur(E)
    real_refresh(pg,E,"T.happy_hours[0].discount_pct=44")
    ok(pg.input_value('#app input[min=\"1\"][max=\"90\"]')=='33' and '44' in E("()=>{const n=document.querySelector('#app .confn');return n?n.innerText:''}"),'3d: happy hour: my 33 % stays, notice shows the server 44')
    E("()=>{HE=null;render()}")
    ok(not errs,'2-3 no JS errors '+str(errs[:2]));pg.close()
    if not quick:
        # ======== 4. real polling (every 10 s, demo courier on/offline) — no help from the test ========
        pg,errs=new_page(b,(390,844),'ru');E=pg.evaluate
        E("()=>{tab='c';showAddP=true;render()}");fill(pg,FORMS[0][2]);blur(E);y0=scroll_to(E,300);watch(E);t0=E("()=>__pvTick")
        pg.wait_for_timeout(44000)
        ok(E("()=>__pvTick")-t0>=3 and rb(E)>=3,'4a: real polling: %d data cycles, page rebuilt %d times'%(E("()=>__pvTick")-t0,rb(E)))
        ok(vals(pg,FORMS[0][2])==[v for _,v in FORMS[0][2]],'4a: promo values kept through real polling')
        ok(abs(E("()=>scrollY")-y0)<=1,'4a: page did not move (%s -> %s)'%(y0,E("()=>scrollY")))
        # 4b. rotation during real polling on the points settings (the owner's case: counters 49-51)
        E("()=>{showAddP=false;tab='y';HE=null;render()}");pg.fill('#ly_loyalty_min_order','17');blur(E);y0=scroll_to(E,420)
        pg.set_viewport_size({'width':844,'height':390});pg.wait_for_timeout(12000)
        pg.set_viewport_size({'width':390,'height':844});pg.wait_for_timeout(1600);y1=E("()=>scrollY");watch(E);pg.wait_for_timeout(22000)
        ok(pg.input_value('#ly_loyalty_min_order')=='17','4b: value 17 kept through rotation and real refreshes')
        ok(rb(E)>=1 and abs(E("()=>scrollY")-y1)<=2 and y1>0,'4b: after coming back to portrait, %d rebuilds did not move the page (%s -> %s)'%(rb(E),y1,E("()=>scrollY")))
        ok(not errs,'4 no JS errors '+str(errs[:2]));pg.close()
    b.close()
print('FORM PASS',npass,'FAILS',len(fails));sys.exit(1 if fails else 0)
