"""Automatic refreshes must not wipe admin forms or move the page (UAT batch 1, iPhone reports 15 Oct).
Runs on a read-only preview built by tools/build_preview.py (demo data; every 10 s a demo courier goes on/offline,
so every screen is really rebuilt, as on a busy day).
  python3 tools/form_keep_check.py <preview_dir> [--quick]      (--quick skips the two slow real-time parts, ~90 s)
Real data refreshes are made by changing the demo tables and firing the app's own "page visible again" refresh,
or by waiting for the 10 s polling. Chromium with a phone viewport and touch; NOT Safari/WebKit."""
import os,sys,time,re
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
def watch(E): E("()=>{window.__n0=RINFO.n;window.__full=0;window.__mo&&__mo.disconnect();window.__mo=new MutationObserver(m=>{if(m.some(x=>x.target.id=='app'&&[...x.removedNodes].some(n=>n.nodeType==1&&n.classList&&n.classList.contains('top'))))__full++});__mo.observe($('app'),{childList:true})}")
def rb(E): return E("()=>RINFO.n-window.__n0")      # redraws that really ran (patched or rebuilt)
def full(E): return E("()=>window.__full")          # whole page thrown away and rebuilt
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
    # 2a'. a real data change on the same screen patches the page: the form fields are the SAME elements (nothing rebuilt)
    E("()=>{document.getElementById('pcode').__mark=1}");watch(E)
    E("()=>{const T=window.__pvTables;const c=T.profiles.find(x=>x.id=='pv-courier');c.online=!c.online;c.last_seen=new Date().toISOString();document.dispatchEvent(new Event('visibilitychange'))}");pg.wait_for_timeout(2900)
    ok(rb(E)>=1 and full(E)==0 and E("()=>document.getElementById('pcode').__mark===1") and pg.input_value('#pcode')=='SAME1','2a: real data change: page patched in place (%d redraw, %d full rebuilds), same input element, value kept'%(rb(E),full(E)))
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
    E("()=>{tab='r';rfl='all';render()}");y2f=scroll_to(E,600)
    btn=E("()=>{const b=[...document.querySelectorAll('#app [onclick^=\"openFrom(\"]')].pop();if(!b)return null;b.click();return true}")
    pg.wait_for_timeout(200);ok(btn and E("()=>scrollY")==0 and E("()=>!!D"),'2f: opening an order from the ratings list shows it from the top')
    pg.locator('#app button[onclick="ordBack()"]').first.click();pg.wait_for_timeout(200)
    ok(E("()=>tab")=='r' and E("()=>rfl")=='all' and E("()=>!D") and abs(E("()=>scrollY")-y2f)<=2,'2f: «Назад» returns to the ratings list, same filter and position (%s)'%E("()=>scrollY"))
    # same from a support ticket
    E("()=>{tab='h';TK.sel=TLB.adminTickets()[0].id;render()}");y0=scroll_to(E,200)
    ok(E("()=>{const b=document.querySelector('#app [onclick^=\"openFrom(\"]');if(!b)return false;b.click();return !!D}"),'2f: order opened from a support ticket')
    pg.locator('#app button[onclick="ordBack()"]').first.click();pg.wait_for_timeout(200)
    ok(E("()=>tab")=='h' and E("()=>TK.sel")==E("()=>TLB.adminTickets()[0].id"),'2f: «Назад» returns to the same support ticket')
    E("()=>{D=null;TK.sel=null;tab='y';render()}")
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
    # ======== 5. Texts tab: never stuck on «…» ========
    E("()=>{tab='g';PGE={};render();TLB.loadPages(true)}");pg.wait_for_timeout(1900)
    ok(E("()=>document.querySelectorAll('#app textarea[id^=pgt_]').length")==4,'5: Texts tab shows the 4 editors (about/privacy × ru/en)')
    E("()=>{window.__pvTables.app_pages=[];TLB.loadPages(true)}");pg.wait_for_timeout(1900)
    t5=E("()=>$('app').innerText")
    ok('нет записей' in t5 and 'Повторить' in t5 and '…' not in E("()=>[...document.querySelectorAll('#app .card')].map(c=>c.innerText).join('|')"),'5: no rows in the table → clear message + retry, not «…»')
    E("()=>{window.__pvTables.app_pages=[{slug:'about',body_ru:'a',body_en:'b'},{slug:'privacy',body_ru:'c',body_en:'d'}];tab='y';render()}")
    ok(not errs,'2-3 no JS errors '+str(errs[:2]))
    # ======== 6. the page is loaded again (iPhone frees memory in the background) ========
    E("()=>{tab='c';showAddP=true;render()}");fill(pg,FORMS[0][2]);blur(E);y6=scroll_to(E,240);pg.wait_for_timeout(600)
    pg.reload();pg.wait_for_timeout(3000)
    ok(E("()=>tab")=='c' and E("()=>showAddP") and vals(pg,FORMS[0][2])==[v for _,v in FORMS[0][2]],'6: after a reload the promo form is back with every typed value %s'%vals(pg,FORMS[0][2]))
    ok(abs(E("()=>scrollY")-y6)<=2,'6: after a reload the page is at the same place (%s -> %s)'%(y6,E("()=>scrollY")))
    E("()=>{showAddP=false;tab='y';HE=null;render()}");pg.fill('#ly_loyalty_min_order','17');blur(E);pg.wait_for_timeout(600);pg.reload();pg.wait_for_timeout(3000)
    ok(E("()=>tab")=='y' and pg.input_value('#ly_loyalty_min_order')=='17','6: after a reload the typed points setting 17 is back (not 30)')
    E("()=>{const s=JSON.parse(sessionStorage.getItem('tlb-ui-admin'));s.act=Date.now()-31*60*1000;sessionStorage.setItem('tlb-ui-admin',JSON.stringify(s));window.TLB_SIGNING_OUT=true}");pg.reload();pg.wait_for_timeout(3000)
    ok(E("()=>tab")=='o' and E("()=>UIR&&UIR.skipped")=='older than 30 min' and E("()=>JSON.stringify(JSON.parse(sessionStorage.getItem('tlb-ui-admin')||'{}').f||{})")=='{}','6: older than the 30-minute inactivity limit → nothing restored, kept data deleted')
    E("()=>{tab='y';render()}");pg.fill('#ly_loyalty_min_order','18');blur(E);pg.wait_for_timeout(600)
    E("()=>{window.alert=()=>{};TLB.logout()}");pg.wait_for_timeout(3000)
    ok(E("()=>tab")=='o' and E("()=>document.getElementById('ly_loyalty_min_order')") is None,'6: after sign-out nothing is restored')
    E("()=>{tab='u';CU.ph='+992900000000';render()}");pg.wait_for_timeout(700)
    ok('992900000000' not in (E("()=>sessionStorage.getItem('tlb-ui-admin')") or ''),'6: customer search/phone fields are never kept')
    E("()=>{CU.ph='';tab='y';render()}")
    # ======== 7. preview diagnostic log ========
    E("()=>{tab='c';showAddP=true;render()}");pg.fill('#pcode','SECRET17');blur(E);pg.wait_for_timeout(600);E("()=>{showAddP=false;tab='o';render()}");pg.wait_for_timeout(1300);E("()=>window.scrollTo(0,0)");scroll_to(E,900);pg.wait_for_timeout(300)
    pg.click('#pv-strip button:has-text(\"سجل التشخيص\")');pg.wait_for_timeout(200);lg=E("()=>document.querySelector('#pv-dp textarea').value")
    ok(re.search(r'PAGE LOAD · build \S+( \+local changes)? · type reload',lg) is not None and 'JUMP' in lg and 'app scrollTo' in lg,'7: diagnostic log records reloads, jumps and who moved the page')
    ok(not any(x in lg for x in ['Муаммад','+99290','SECRET17','SALE10','Рудаки']),'7: diagnostic log holds no names, phones, addresses or typed values')
    E("()=>document.getElementById('pv-dp').remove()")
    # ======== 8. customer card: whole history in pages of 50, and «Назад» from an order returns to the card ========
    E("()=>{const T=window.__pvTables;for(let i=0;i<60;i++)T.orders.push({id:'cx'+i,store_id:'s1',customer_id:'u3',driver_id:null,status:'delivered',subtotal:100,discount:0,promo_discount:0,delivery_fee:10,tip:0,total:110,commission:10,commission_pct:10,payment:'cash',customer_name:'Клиент',created_at:new Date(Date.now()-(400+i)*86400000).toISOString(),done_at:null,wallet_used:0})}")
    E("()=>{tab='u';CU.q='Клиент';render();cuLoad(true)}");pg.wait_for_timeout(800);E("()=>cuOpen('u3')");pg.wait_for_timeout(1000)
    ok(E("()=>CU.orders.length")==50 and 'показано 50 из 60' in E("()=>$('app').innerText"),'8: customer card says «показано 50 из 60» (orders of THIS account id)')
    ok(E("()=>CU.orders.every(o=>String(o.id).startsWith('cx'))"),'8: only orders with this customer id are listed')
    E("()=>{const b=[...document.querySelectorAll('#app button')].find(x=>x.getAttribute('onclick')=='cuMore()');b.scrollIntoView({block:'center'})}");y8=E("()=>scrollY")
    E("()=>[...document.querySelectorAll('#app button')].find(x=>x.getAttribute('onclick')=='cuMore()').click()");pg.wait_for_timeout(800)
    ok(E("()=>CU.orders.length")==60 and 'показано 60 из 60' in E("()=>$('app').innerText") and not E("()=>[...document.querySelectorAll('#app button')].some(x=>x.getAttribute('onclick')=='cuMore()')"),'8: «Показать ещё» loads the other 10, then the button disappears')
    ok(abs(E("()=>scrollY")-y8)<=2,'8: the page stays where it was while loading more (%s -> %s)'%(y8,E("()=>scrollY")))
    E("()=>{const c=[...document.querySelectorAll('#app [onclick^=\"openFrom(\"]')].find(x=>x.getAttribute('onclick').includes('cx55'));c.scrollIntoView({block:'center'})}");y8=E("()=>scrollY")
    E("()=>[...document.querySelectorAll('#app [onclick^=\"openFrom(\"]')].find(x=>x.getAttribute('onclick').includes('cx55')).click()");pg.wait_for_timeout(300)
    pg.wait_for_timeout(400);st8=E("()=>[tab,D,CU.sel,CU.orders&&CU.orders.length,!!TLB.order('cx55'),$('app').innerText.includes('#cx55')]")
    ok(st8[0]=='o' and st8[1]=='cx55' and st8[4] and st8[5],'8: an old order (cx55, not among the loaded ones) is fetched and opens from the customer card %s'%st8)
    pg.locator('#app button[onclick="ordBack()"]').first.click();pg.wait_for_timeout(300)
    ok(E("()=>tab")=='u' and E("()=>CU.sel")=='u3' and E("()=>CU.q")=='Клиент' and E("()=>CU.orders.length")==60 and abs(E("()=>scrollY")-y8)<=2,'8: «Назад» returns to the same customer, same search, all 60 orders, same place (%s)'%E("()=>scrollY"))
    E("()=>openFrom('nope404')");pg.wait_for_timeout(700)
    ok('nope404 не найден' in E("()=>$('app').innerText"),'8: an order that does not exist says so (no silent jump to the orders list)')
    pg.locator('#app button[onclick="ordBack()"]').first.click();pg.wait_for_timeout(300)
    ok(E("()=>tab")=='u' and E("()=>CU.sel")=='u3','8: and «Назад» still returns to the customer')
    # ======== 9. delivery type label in the store form ========
    E("()=>{CU.sel=null;tab='s';E=null;showAddS=true;render()}")
    ok(E("()=>document.querySelector('#sf option[value=free]').textContent")=='Бесплатная' and 'свободны' in E("()=>document.querySelector('.lp').title"),'9: store form: delivery type «free» reads «Бесплатная»; «свободны» stays only for free couriers')
    E("()=>{showAddS=false;render()}")
    # ======== 10. real taps (not script shortcuts) on the paths the Chrome review used ========
    errs.clear();E("()=>{BACKO=null;D=null;tab='h';TK.sel=null;render();window.scrollTo(0,0)}");pg.wait_for_timeout(300)
    pg.locator('#app .card[onclick^="TK.sel="]').first.click();pg.wait_for_timeout(500)
    ok(not errs and E("()=>TK.sel")!=None,'10: tapping a support ticket opens it (no "t1 is not defined") %s'%errs[:1])
    pg.locator('#app [onclick^="openFrom("]').first.click();pg.wait_for_timeout(500)
    ok(E("()=>tab")=='o' and E("()=>!!D"),'10: from the ticket, «Открыть заказ» opens the order')
    pg.locator('#app button[onclick="ordBack()"]').first.click();pg.wait_for_timeout(400)
    ok(E("()=>tab")=='h' and E("()=>TK.sel")!=None and not errs,'10: «Назад» returns to the same ticket')
    E("()=>{TK.sel=null;tab='r';rfl='all';render()}");pg.wait_for_timeout(300)
    for sel,lbl in [('#app button[onclick^="RES={o:"]','rating «resolve»'),('#app button[onclick^="ASG="]','assign courier')]:
        n=pg.locator(sel).count()
        if n: pg.locator(sel).first.click();pg.wait_for_timeout(300)
        ok(not errs,'10: tapping %s works (%d buttons) %s'%(lbl,n,errs[:1]));E("()=>{RES=null;ASG=null;render()}")
    # the courier map: its Close button is not under the preview strip
    E("()=>{tab='d';render()}");pg.wait_for_timeout(200);E("()=>openMap()");pg.wait_for_timeout(600)
    pg.locator('.ovl button[onclick="MAPO=false;render()"]').click(timeout=3000);pg.wait_for_timeout(300)
    ok(not E("()=>MAPO"),'10: the map closes with a normal tap on «Закрыть»')
    # the demo customer with 62 old orders, by taps only
    E("()=>{tab='u';CU.q='';render();cuLoad(true)}");pg.wait_for_timeout(900)
    pg.locator('#app .card',has_text='Демо-клиент').first.click();pg.wait_for_timeout(1200)
    ok('показано 50 из 62' in E("()=>$('app').innerText"),'10: demo customer card: «показано 50 из 62»')
    pg.locator('#app button[onclick="cuMore()"]').click();pg.wait_for_timeout(900)
    ok('показано 62 из 62' in E("()=>$('app').innerText"),'10: «Показать ещё» → 62 of 62')
    old=pg.locator('#app [onclick^="openFrom("]').last;old.scroll_into_view_if_needed();y10=E("()=>scrollY");old.click();pg.wait_for_timeout(1200)
    ok(E("()=>tab")=='o' and E("()=>!!TLB.order(D)") and 'Демо-блюдо' in E("()=>$('app').innerText"),'10: the oldest order (not among the loaded ones) opens with its items')
    pg.locator('#app button[onclick="ordBack()"]').first.click();pg.wait_for_timeout(500)
    ok(E("()=>tab")=='u' and 'показано 62 из 62' in E("()=>$('app').innerText") and abs(E("()=>scrollY")-y10)<=2,'10: «Назад» → same customer, 62 orders, same place')
    ok(E("()=>TLB.orders().every(o=>!String(o.id).startsWith('h9'))"),'10: the old sample orders stay out of the main orders list (like production: newest 300 only)')
    ok(not errs,'5-10 no JS errors '+str(errs[:2]));pg.close()
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
