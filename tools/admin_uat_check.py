"""UAT batch 1 (admin panel): order search over all orders, filters/tabs keep their place, timeline names and durations,
payment & settlement block, free-delivery invoice, chat layout, banner button, rating counters, summary caption,
no horizontal overflow in date/time forms. Runs the real admin.html against the mocked Supabase of qa_all.py."""
import os,sys,re,json
from playwright.sync_api import sync_playwright
here=os.path.dirname(os.path.abspath(__file__));root=os.path.abspath(os.path.join(here,'..'))
FIX=open(os.path.join(here,'qa_all.py')).read().split('FIX="""')[1].split('"""')[0].replace('window.__ROLE','"admin"')
# admin_search_orders is answered by window.__srch (ids, or an error object) and every call is recorded
SPY="""(function(){var cc=window.supabase.createClient;window.__sq=[];window.__srch=null;
 window.supabase.createClient=function(){var c=cc.apply(this,arguments),r=c.rpc;c.rpc=function(n,a){if(n==='admin_search_orders'){window.__sq.push(a);var x=window.__srch;
   if(x&&x.error)return Promise.resolve({data:null,error:x.error});return Promise.resolve({data:(x||[]).map(function(i){return {id:i}}),error:null})}return r.call(c,n,a)};return c}})();"""
fails=[]
def ok(c,m):
    print(('PASS ' if c else 'FAIL ')+m)
    if not c: fails.append(m)
with sync_playwright() as p:
    b=p.chromium.launch()
    def page(w):
        pg=b.new_page(viewport={'width':w,'height':800});pg.errs=[]
        pg.on('pageerror',lambda e:pg.errs.append(str(e)))
        pg.route('**/*',lambda rt,rq:(rt.fulfill(status=200,content_type='application/javascript',body=FIX+SPY) if 'supabase-js' in rq.url else (rt.abort() if rq.url.startswith('http') else rt.continue_())))
        pg.goto('file://'+root+'/admin.html',wait_until='domcontentloaded');pg.wait_for_timeout(2300);pg.evaluate("()=>TLB.setLang('ru')");pg.wait_for_timeout(200);return pg
    pg=page(390);E=pg.evaluate
    ids=lambda:E("()=>[...document.querySelectorAll('[onclick^=\"openOrd(\"]')].map(e=>e.querySelector('b').textContent)")
    # ---- 0. the sample orders themselves follow the production formula (test data check, not a change of the formula)
    bad=E("()=>TLB.orders().filter(o=>{const it=o.items.reduce((s,i)=>s+i.qty*i.price,0),tot=Math.max(5,o.subtotal-o.discount-o.promoDiscount-o.pointsValue+o.delivery+o.tip);return Math.abs(it-o.subtotal)>0.004||Math.abs(tot-o.total)>0.004||(o.payment=='wallet'&&Math.abs(o.walletUsed-o.total)>0.004)}).map(o=>o.id)")
    ok(bad==[],'sample orders are consistent: lines = items, total = items − discount − promo − points + delivery + tip, wallet payment = wallet used %s'%bad)
    # ---- 1. search
    ok(E("()=>!!document.getElementById('oq')&&document.getElementById('oq').getBoundingClientRect().top<document.querySelector('.chips').getBoundingClientRect().top"),'search box above the status filters')
    E("()=>{window.__srch=['ord5']}");pg.fill('#oq','Мадина');pg.wait_for_timeout(700)
    ok(E("()=>window.__sq.length")==1 and E("()=>window.__sq[0].p_q")=='Мадина','typing asks the server (all orders), once after a pause')
    ok(ids()==['#ord5'] and 'во всех заказах: 1' in E("()=>document.body.innerText"),'server results are listed: %s'%ids())
    ok(E("()=>document.activeElement&&document.activeElement.id")=='oq','the search box keeps the focus while results arrive')
    E("()=>{f='delivered';render()}");ok(ids()==[],'combined with the status filter (cancelled result hidden under "Доставлен")')
    E("()=>{f='cancelled';render()}");ok(ids()==['#ord5'],'… and shown under "Отменён"')
    ok(E("()=>TLB.order('ord5')&&TLB.orders().length")>0,'found order opens like any other')
    E("()=>document.querySelector('.osx').click()");pg.wait_for_timeout(200)
    ok(E("()=>OQ")=='' and len(ids())==1 and E("()=>f")=='cancelled','clear button empties the search, the status filter stays')
    E("()=>{f='all';render()}")
    E("()=>{window.__srch={error:{message:'Could not find the function public.admin_search_orders in the schema cache',code:'PGRST202'}}}");pg.fill('#oq','ord');pg.wait_for_timeout(700)
    t=E("()=>document.querySelector('.osn').innerText")
    ok('schema_patch35' in t,'server search not installed → says so and searches the loaded orders: '+t[:60])
    pg.fill('#oq','Муаммад');pg.wait_for_timeout(700);ok(len(ids())==7,'fallback finds by customer name among loaded orders (%d)'%len(ids()))
    E("()=>{window.__srch={error:{message:'not_allowed',code:'P0001'}}}");pg.fill('#oq','777');pg.wait_for_timeout(700)
    ok('Нет прав' in E("()=>document.querySelector('.osn').innerText"),'no permission → clear message (the server decides)')
    E("()=>{window.__srch=[]}");pg.fill('#oq','x');pg.wait_for_timeout(600);ok(E("()=>window.__sq.slice(-1)[0].p_q")=='x' and ids()==[],'no results → empty list')
    E("()=>oqSet('')")
    # ---- 2. tabs / chips keep their place; back from an order keeps filter, search and position
    E("()=>{document.querySelector('.chips').scrollLeft=260}");sl0=E("()=>document.querySelector('.chips').scrollLeft")
    E("()=>{const c=document.querySelector('.chips'),a=c.getBoundingClientRect();const v=[...c.querySelectorAll('button')].filter(x=>{const r=x.getBoundingClientRect();return r.left>=a.left&&r.right<=a.right});v[v.length-1].click()}");pg.wait_for_timeout(150)
    sl1=E("()=>document.querySelector('.chips').scrollLeft")
    ok(sl0>0 and abs(sl1-sl0)<=40,'status chips keep their scroll after a choice (%s → %s)'%(sl0,sl1))
    vis=E("()=>{const c=document.querySelector('.chips'),o=c.querySelector('.on'),a=c.getBoundingClientRect(),r=o.getBoundingClientRect();return r.left>=a.left-1&&r.right<=a.right+1}")
    ok(vis,'the chosen status stays visible')
    E("()=>{document.querySelectorAll('.tabs button')[7].click()}");pg.wait_for_timeout(150)
    vis=E("()=>{const c=document.querySelector('.tabs'),o=c.querySelector('.on'),a=c.getBoundingClientRect(),r=o.getBoundingClientRect();return c.scrollLeft>0&&r.left>=a.left-1&&r.right<=a.right+1}")
    ok(vis,'a far section tab stays visible after it is opened')
    E("()=>{document.querySelectorAll('.tabs button')[0].click()}");E("()=>{f='all';render()}")
    E("()=>{window.__srch=TLB.orders().map(o=>o.id);oqSet('Муаммад')}");pg.wait_for_timeout(600)
    E("()=>scrollTo(0,500)");y0=E("()=>scrollY")
    E("()=>document.querySelectorAll('[onclick^=\"openOrd(\"]')[3].click()");pg.wait_for_timeout(200)
    ok(E("()=>D")!=None,'order opened')
    E("()=>[...document.querySelectorAll('button')].find(b=>b.textContent.includes('Назад')).click()");pg.wait_for_timeout(200)
    ok(abs(E("()=>scrollY")-y0)<=2 and E("()=>OQ")=='Муаммад' and E("()=>f")=='all','back: same list position (%s), search and filter kept'%E("()=>scrollY"))
    E("()=>oqSet('')")
    # ---- 3. timeline
    E("()=>{D='ord4';render();TLB.loadOrderExtra('ord4')}");pg.wait_for_timeout(600);E("()=>render()")
    tl=E("()=>[...document.querySelectorAll('.tl')].map(e=>[e.querySelector('b').textContent,e.querySelector('small').textContent])")
    names=[x[0] for x in tl]
    ok(names.count('Заказ оформлен')==1,'"Заказ оформлен" only once: %s'%names)
    ok('Курьер в ресторане' in names and 'Курьер у клиента' in names,'courier arrival events have their own names')
    ok(any(n.startswith('Событие: mystery_kind') for n in names),'an unknown event is shown with its own code, not renamed')
    def secs(x):
        h,m,s_=map(int,re.search(r'(\d\d):(\d\d):(\d\d)',x).groups());return h*3600+m*60+s_
    good=True
    for k in range(1,len(tl)):
        m=re.search(r'\(\+(?:(\d+) мин )?(\d+) с\)',tl[k][1]);d=(int(m.group(1) or 0)*60+int(m.group(2))) if m else -1
        if d!=secs(tl[k][1])-secs(tl[k-1][1]): good=False;print('   diff',tl[k-1][1],tl[k][1])
    ok(good,'each "+duration" equals the difference of the shown times')
    tot=E("()=>[...document.querySelectorAll('.l')].find(e=>e.textContent.includes('Общее время')).textContent")
    m=re.search(r'(\d+) мин (\d+) с',tot);ok(m and int(m.group(1))*60+int(m.group(2))==secs(tl[-1][1])-secs(tl[0][1]),'total time = last − first shown time ('+tot+')')
    # ---- 5. free delivery invoice
    body=E("()=>document.body.innerText")
    ok('Доставка (оплачивает клиент)\n0.00' in body and 'Доставку оплачивает ресторан\n22.00' in body,'free delivery: customer pays 0.00, restaurant pays 22.00')
    ok(E("()=>!!document.querySelector('.subl')&&document.querySelector('.subl').innerText.includes('10.00')&&document.querySelector('.subl').innerText.includes('12.00')"),'the 10 + 12 breakdown sits inside the restaurant line')
    ok('Итого\n415.00 TJS' in body,'total unchanged: 415.00')
    # ---- 4. settlement
    E("()=>{D='ord6';render()}");fb=E("()=>[...document.querySelectorAll('.fr')].map(e=>e.innerText.replace(/\\n/g,' | '))")
    j=' / '.join(fb)
    ok('Сбор и возврат не подтверждены — платёжный шлюз не подключён' in j and 'Apple Pay' in j,'Apple Pay: collection and refund not verified, gateway not connected')
    ok(j.count('платёжный шлюз не подключён')==2,'refund row says the same, nothing invented')
    ok('10.00 TJS — не входят в выплаты приложения' in j and '22.00 TJS — расчётная, не учитывается' in j,'tip and commission of a rejected order are marked as not counted')
    E("()=>{D='ord5';render()}");j=' / '.join(E("()=>[...document.querySelectorAll('.fr')].map(e=>e.innerText.replace(/\\n/g,' | '))"))
    ok('Возвращено в кошелёк клиента | 20.00 TJS' in j and 'Баллы возвращены клиенту' in j,'cancelled order: wallet and points returns shown from their records')
    E("()=>{const o=TLB.order('ord5');o.walletReturnedAt=null;render()}");j=' / '.join(E("()=>[...document.querySelectorAll('.fr')].map(e=>e.innerText.replace(/\\n/g,' | '))"))
    ok('Возвращено в кошелёк клиента | Статус возврата не подтверждён' in j,'no return record → "Статус возврата не подтверждён", not a success and not a failure')
    E("()=>{D='ord4';render()}");j=' / '.join(E("()=>[...document.querySelectorAll('.fr')].map(e=>e.innerText.replace(/\\n/g,' | '))"))
    ok('учитывается: заказ доставлен' in j,'delivered order: commission counted')
    # ---- 7. chat
    E("()=>{D='ord1';render();TLB.loadOrderExtra('ord1')}");pg.wait_for_timeout(500);E("()=>render()")
    r=E("()=>{const m=document.querySelector('.msg');if(!m)return null;const a=m.querySelector('.mwho').getBoundingClientRect(),b=m.querySelector('.mtx').getBoundingClientRect();return [b.top>=a.bottom-1,m.scrollWidth<=m.clientWidth+1]}")
    ok(r and r[0],'chat: sender and time on their own line above the text')
    ok(r and r[1],'chat: long text wraps inside the bubble')
    # ---- 8. banner button
    E("()=>{D=null;tab='b';render();openBE('bn1')}");btn=E("()=>[...document.querySelectorAll('button')].find(b=>(b.getAttribute('onclick')||'')=='bannerSave()').textContent")
    ok('Сохранить изменения баннера' in btn and 'магазин' not in btn,'banner save button says what it does: '+btn.strip())
    # ---- 9. ratings
    E("()=>{BE=null;BD=null;tab='r';rfl='need';render()}")
    tile=E("()=>+[...document.querySelectorAll('.grid .k')].find(k=>k.innerText.includes('Требуют внимания')).querySelector('b').textContent")
    chip=E("()=>+(document.querySelector('.chips .chip').textContent.match(/(\\d+)$/)||[0,0])[1]")
    badge=E("()=>+([...document.querySelectorAll('.tabs button')].find(b=>b.classList.contains('on')).querySelector('em')||{textContent:0}).textContent")
    E("()=>{rfl='all';render()}");cards=E("()=>[...document.querySelectorAll('.rst')].filter(e=>e.textContent.includes('Требует внимания')).length")
    hi=E("()=>[...document.querySelectorAll('.rst')].filter(e=>e.textContent.includes('Не обработано')).length")
    ok(tile==chip==badge==cards==1,'"needs attention": tile %s = filter %s = tab badge %s = cards %s'%(tile,chip,badge,cards))
    ok(hi==4,'unhandled 4–5 star ratings are "Не обработано", not "needs attention" (%d)'%hi)
    # ---- 10. summary caption
    E("()=>{tab='o';D=null;render()}");cap=E("()=>document.querySelector('.kcap').innerText")
    ok('не более 300' in cap and '(сейчас 7)' in cap and 'не итог за всё время' in cap and re.search(r'период \d\d\.\d\d\.\d{4}.* — \d\d\.\d\d\.\d{4}',cap),'summary: "не более 300", real period, not all-time: '+cap[:90])
    ok(re.search(r'\d+\.\d\d TJS',E("()=>document.querySelector('.grid').innerText")) is not None,'money shown with 2 decimals')
    ok(not pg.errs,'no JS errors '+str(pg.errs[:2]))
    # ---- 6. forms fit the screen (no horizontal scroll), RU and EN
    for w in (360,390,430):
        for lg in ('ru','en'):
            q=page(w);q.evaluate("(l)=>TLB.setLang(l)",lg);bad=[]
            for js in ("tab='y';HE=null;heOpen()","HE=null;tab='c';showAddP=true;render()","tab='b';BE=null;openBE('bn1')"):
                q.evaluate("()=>{"+js+"}");q.wait_for_timeout(250)
                r=q.evaluate("()=>{const W=innerWidth;const o=[...document.querySelectorAll('input,select')].filter(e=>e.offsetParent).filter(e=>{const r=e.getBoundingClientRect();return r.right>W+0.5||r.left<-0.5});return [document.scrollingElement.scrollWidth,o.length]}")
                if r[0]>w or r[1]: bad.append((js[:12],r))
            ok(not bad,'%dpx %s: date/time fields and pages fit %s'%(w,lg,bad));q.close()
    b.close()
print('ADMIN UAT FAILS',len(fails));sys.exit(1 if fails else 0)
