"""Batch 2 (v59): UAT008 / 009 / 012 / 013 / 014 / 015 on the read-only previews (customer + restaurant).
The points history loader and the points summary are replaced in the page by controllable stand-ins (delayed, failed, superseded answers);
order rows are edited in the preview's in-memory tables. Chromium only — not proof for iPhone Safari, and not a test of the live database.
  python3 tools/uat3_check.py <customer_preview_dir> <merchant_preview_dir>"""
import sys, re
from playwright.sync_api import sync_playwright
CU,ME=sys.argv[1],sys.argv[2];fails=[];n=0
def ok(c,m):
    global n;n+=1;print(('PASS ' if c else 'FAIL ')+m)
    if not c: fails.append(m)
def page(b,d,app,w=390):
    pg=b.new_page(viewport={'width':w,'height':844},is_mobile=True,has_touch=True);errs=[];pg.on('pageerror',lambda e:errs.append(str(e)))
    pg.route('**/*',lambda rt,rq:(rt.abort() if rq.url.startswith('http') else rt.continue_()))
    pg.on('dialog',lambda dg:dg.accept())
    pg.goto('file://'+d+'/'+app+'.html');pg.wait_for_timeout(2500);pg.evaluate("()=>TLB.setLang('ru')");pg.wait_for_timeout(300);return pg,errs
# points stand-ins: LOY = summary, PTS = ledger rows (newest first), loadPoints = a promise the test answers (__q), counted (__calls)
STUB="""()=>{window.__realLoad=TLB.loadPoints;window.LOY={balance:900,voucher_points:1000,points_per_tjs:100,earn_per_tjs:10,min_redeem:1000,min_order:30,expiry_days:90,cashback_pct:0,rate_reward:10};
  window.PTS=[];TLB.loyalty=()=>LOY;TLB.points=()=>PTS;window.__q=[];window.__calls=0;
  TLB.loadPoints=()=>{window.__calls++;return new Promise((res,rej)=>__q.push({res,rej}))};
  Object.keys(localStorage).filter(k=>/^tlb-l[bm]-/.test(k)).forEach(k=>localStorage.removeItem(k));
  Object.assign(PL,{busy:0,again:0,bal:null,sig:null,gain:0,gainAt:0,failAt:0});go('wallet')}"""
CF="()=>document.querySelectorAll('.cfw').length"
def ans(E,v='true'):E("()=>{const x=__q.shift();x&&x.res(%s)}"%v)
with sync_playwright() as p:
    b=p.chromium.launch()
    # ================= UAT009 / UAT008: customer points =================
    pg,errs=page(b,CU,'customer');E=pg.evaluate
    E(STUB);E("()=>ptsWatch()");pg.wait_for_timeout(100)
    ok(E("()=>__calls")==1,'009: first look → one history load')
    E("()=>{PL.sig='changed-1';ptsWatch();PL.sig='changed-2';ptsWatch();LOY.balance=901;ptsWatch()}")
    ok(E("()=>__calls")==1,'009: three events during the load → still ONE request in flight')
    E("()=>{PTS=[{id:5,kind:'earn',points:300,orderId:'ord4',at:Date.now()},{id:4,kind:'spend',points:-1000,orderId:'ord3',at:Date.now()}]}");ans(E);pg.wait_for_timeout(150)
    ok(E("()=>__calls")==2,'009: events during the load → exactly ONE more load after it (%d)'%E("()=>__calls"))
    ans(E,'false');pg.wait_for_timeout(150);E("()=>render()");pg.wait_for_timeout(150)
    ok(E("()=>__calls")==2,'009: no further load when nothing changed (%d)'%E("()=>__calls"))
    ok(E(CF)==0 and E("()=>localStorage.getItem(uidK('tlb-lm-'))")=='5','008: first read sets the mark (last id 5), no celebration for old rows')
    ok(E("()=>document.querySelectorAll('.card .dr').length")>=2,'009: history shown in the wallet')
    pg.wait_for_timeout(3000);ok(E("()=>__calls")==2,'009: no timer — idle 3 s, no load')
    # same balance, two movements (spend + return): the order event still reloads the history
    E("()=>{PTS=[{id:7,kind:'return',points:1000,orderId:'ord5',at:Date.now()},{id:6,kind:'spend',points:-1000,orderId:'ord5',at:Date.now()}].concat(PTS);window.__pvTables.orders.find(o=>o.id=='ord0').status='cancelled'}")
    E("()=>TLB.reload()");pg.wait_for_timeout(900)
    ok(E("()=>__calls")==3,'009: an order status event reloads the history even with the SAME balance (%d)'%E("()=>__calls"))
    ans(E);pg.wait_for_timeout(200)
    ok(E("()=>document.body.innerText.includes(t('pk_return'))"),'009: the return row appears without a page reload')
    # return that crosses a voucher step: no celebration
    E("()=>{LOY.balance=1901;PTS=[{id:8,kind:'return',points:1000,orderId:'ord6',at:Date.now()}].concat(PTS);PL.sig='ev-ret';ptsWatch()}");pg.wait_for_timeout(100);ans(E);pg.wait_for_timeout(300);E("()=>render()");pg.wait_for_timeout(200)
    ok(E(CF)==0 and E("()=>localStorage.getItem(uidK('tlb-lb-'))")=='1901','008: returned points cross 1000 → NO celebration (mark moved to 1901)')
    # new earn that crosses a step → one celebration
    E("()=>{LOY.balance=2050;PTS=[{id:9,kind:'earn',points:149,orderId:'ord4',at:Date.now()}].concat(PTS);PL.sig='ev-earn';ptsWatch()}");pg.wait_for_timeout(100);ans(E);pg.wait_for_timeout(300)
    ok(E(CF)==1,'008: a NEW earn crossing 2000 → one celebration')
    E("()=>document.querySelectorAll('.cfw').forEach(x=>x.remove())")
    # the page is opened again: memory reset, marks kept on the device → nothing repeats
    E("()=>{Object.assign(PL,{busy:0,again:0,bal:null,sig:null,gain:0});ptsWatch()}");pg.wait_for_timeout(100);ans(E);pg.wait_for_timeout(300);E("()=>render()");pg.wait_for_timeout(200)
    ok(E(CF)==0,'008: reopening / reloading the history does not repeat the celebration')
    # reward (rating bonus) crossing a step → celebrates (not dropped by an earn-only rule)
    E("()=>{LOY.balance=2995;PTS=[{id:10,kind:'return',points:945,orderId:'ord2',at:Date.now()}].concat(PTS);PL.sig='ev-r0';ptsWatch()}");pg.wait_for_timeout(100);ans(E);pg.wait_for_timeout(300)
    E("()=>{LOY.balance=3005;PTS=[{id:11,kind:'reward',points:10,orderId:'ord4',at:Date.now()}].concat(PTS);PL.sig='ev-rw';ptsWatch()}");pg.wait_for_timeout(100);ans(E);pg.wait_for_timeout(300)
    ok(E(CF)==1,'008: a NEW rating reward crossing 3000 → celebration')
    E("()=>document.querySelectorAll('.cfw').forEach(x=>x.remove())")
    # the balance arrives BEFORE the history: the history is read again first, then the celebration
    E("()=>{PTS=[{id:12,kind:'earn',points:1000,orderId:'ord4',at:Date.now()}].concat(PTS);LOY.balance=4005;render()}");pg.wait_for_timeout(200)
    ok(E("()=>__calls")>=1 and E(CF)==0,'008/009: a new balance without its history → history read first, no early decision')
    ans(E);pg.wait_for_timeout(300)
    ok(E(CF)==1,'008: after the history arrives → the earn crossing 4000 celebrates once')
    E("()=>document.querySelectorAll('.cfw').forEach(x=>x.remove())");E("()=>render()");pg.wait_for_timeout(200);ok(E(CF)==0,'008: a redraw does not repeat it')
    # failure: no stuck state, the next event loads again
    c0=E("()=>__calls");E("()=>{PL.sig='ev-f';ptsWatch()}");pg.wait_for_timeout(100);ans(E,'null');pg.wait_for_timeout(200)
    ok(E("()=>PL.busy")==0 and E("()=>PL.failAt")>0,'009: a failed load frees the loader')
    E("()=>{PL.sig='ev-f2';ptsWatch()}");pg.wait_for_timeout(100);ok(E("()=>__calls")==c0+2,'009: the next event loads again after a failure');ans(E,'false')
    # per user: marks are kept per account
    ok(E("()=>uidK('tlb-lm-')").endswith(E("()=>(TLB.me()||{}).id")) ,'008: the marks are stored per user id')
    # the rating triggers a history load
    E("()=>{const o=window.__pvTables.orders.find(o=>o.id=='ord4');TLB.rateOrder=()=>Promise.resolve({});rt0('ord4').s=5}");c0=E("()=>__calls")
    E("()=>sendRate('ord4')");pg.wait_for_timeout(300);ok(E("()=>__calls")>c0,'009: a saved rating reloads the history');ans(E,'false')
    # core: a reply older than the newest call is ignored
    E("()=>{TLB.loadPoints=__realLoad}")
    r=E("async()=>{const a=TLB.loadPoints(),b=TLB.loadPoints();return [await a,await b]}")
    ok(r[0] is None and r[1] in (True,False),'009 core: of two overlapping loads the older reply is ignored %s'%r)
    ok(not errs,'customer points: no JS errors %s'%errs[:1]);pg.close()
    # ================= UAT012: customer receipt of a cancelled order =================
    pg,errs=page(b,CU,'customer');E=pg.evaluate
    def setord(js):E("()=>{const o=window.__pvTables.orders.find(o=>o.id=='ord5');Object.assign(o,%s)}"%js);E("()=>TLB.reload()");pg.wait_for_timeout(900);E("()=>{go('track',{tid:'ord5'})}");pg.wait_for_timeout(400)
    setord("{status:'cancelled',subtotal:265,discount:0,delivery_fee:10,tip:0,total:275,payment:'cash',wallet_used:124.38,points_used:1000,points_value:10,wallet_returned_at:new Date().toISOString(),points_returned_at:new Date().toISOString(),cash_collected:null}")
    st=pg.inner_text('#stl') if pg.locator('#stl').count() else ''
    ok('Возвращено в кошелёк' in st and '+124.38' in st,'012 (9104): wallet return shown from the record: +124.38')
    ok('Баллы возвращены' in st and re.search(r'\+1\s?000',st) is not None,'012: points return shown from the record: +1000')
    ok('150.62' in st and 'получение не записано' in st,'012: cash 150.62 → «no collection recorded»')
    ok(not re.search(r'возвращ[^\n]*150\.62|не получен',st,re.I),'012: cash never shown as refunded / «not received»')
    ok('Сумма заказа' in pg.inner_text('.card.sum'),'012: the total of a cancelled order is «Сумма заказа», not a paid total')
    setord("{wallet_returned_at:null,points_returned_at:null}")
    st=pg.inner_text('#stl') if pg.locator('#stl').count() else ''
    ok('124.38' in st and 'не подтверждён' in st and '1 000 баллов не подтверждён'.replace(' ',' ',1) in st or ('не подтверждён' in st and st.count('не подтверждён')==2),'012: without the return records → «return not confirmed» (wallet and points)')
    setord("{wallet_used:0,points_used:0,points_value:0,payment:'card',total:275}")
    st=pg.inner_text('#stl') if pg.locator('#stl').count() else ''
    ok('не подтверждён' not in st and 'Карта 275 TJS' in st and 'данных о списании нет' in st,'012: nothing from wallet / points → no «not confirmed»; card: «no charge data»')
    E("()=>{window.__pvTables.wallet_entries.push({id:'w9',user_id:window.__pvTables.wallet_entries[0].user_id,amount:20,kind:'refund',order_id:'ord5',ticket_id:'t7',note:null,created_at:new Date().toISOString()})}")
    E("()=>{S.walL=0;TLB.loadWallet(true)}");pg.wait_for_timeout(800);E("()=>render()");pg.wait_for_timeout(200)
    st=pg.inner_text('#stl') if pg.locator('#stl').count() else ''
    ok('Возврат по обращению #t7' in st and '+20 TJS' in st and 'автоматически' not in st.split('Возврат по обращению')[1],'012: a support refund is its own line, apart from the automatic return')
    setord("{status:'rejected',cancel_reason:'too_busy',wallet_used:50,wallet_returned_at:new Date().toISOString(),payment:'cash',total:275}")
    ok(not E("()=>document.body.innerText.includes(t('cxBack'))"),'012: the rejected-order card no longer claims «already returned» without the record')
    E("()=>{const o=window.__pvTables.orders.find(o=>o.id=='ord4');o.cash_collected=135}");E("()=>TLB.reload()");pg.wait_for_timeout(900);E("()=>{go('track',{tid:'ord4'})}");pg.wait_for_timeout(400)
    ok(pg.locator('#stl').count()==0 and pg.locator('.card.sum').count()>=1,'012: a delivered order without refunds keeps its receipt (no extra block)')
    ok(not errs,'customer receipt: no JS errors %s'%errs[:1])
    # ================= UAT015: rates (from the settings, estimate wording) =================
    E("()=>{TLB.loyalty=()=>({balance:0,voucher_points:1000,points_per_tjs:100,earn_per_tjs:7,min_redeem:1000,min_order:30,expiry_days:90,cashback_pct:0});go('wallet')}");pg.wait_for_timeout(300)
    ok('Обычно 7 баллов за 1 TJS' in pg.inner_text('body') and 'своя ставка' in pg.inner_text('body'),'015: wallet rate comes from the setting (7) + «some places have their own rate»')
    E("()=>{S.cart={i2:2};S.cartStore=STORES[0].n;go('pay')}");pg.wait_for_timeout(1200)
    bt=pg.inner_text('body')
    ok('≈' in bt and pg.locator('#ernn').count()==1 and 'при доставке' in pg.inner_text('#ernn'),'015: pay page: points / cashback as an estimate, credited on delivery at that moment\'s rate')
    E("()=>openN(STORES[0].n)");pg.wait_for_timeout(600)
    ok('при доставке' in pg.inner_text('body'),'015: store page: the same estimate note')
    E("()=>TLB.setLang('en')");pg.wait_for_timeout(200);E("()=>go('pay')");pg.wait_for_timeout(500)
    ok('Estimate' in pg.inner_text('#ernn'),'015: English wording present')
    ok(not errs,'customer rates: no JS errors %s'%errs[:1]);pg.close()
    # ================= restaurant: UAT013 / UAT014 / UAT012 =================
    pg,errs=page(b,ME,'merchant');E=pg.evaluate
    E("""()=>{const T=window.__pvTables.orders,now=Date.now(),iso=h=>new Date(now-h*3600e3).toISOString();
      T.forEach((o,i)=>{o.done_at=o.done_at||iso(2+i)});
      Object.assign(T.find(o=>o.id=='ord4'),{status:'delivered',subtotal:200,discount:20,commission:18,commission_pct:10,points_value:5,cashback:3,fee_waived:10});
      Object.assign(T.find(o=>o.id=='ord5'),{status:'cancelled',cancel_reason:null,commission:12});
      Object.assign(T.find(o=>o.id=='ord6'),{status:'rejected',cancel_reason:'out_of_stock',commission:11});
      Object.assign(T.find(o=>o.id=='ord3'),{status:'rejected',cancel_reason:null,cancel_note:'свободный текст',commission:9,done_at:iso(1)});
      TLB.reload()}""");pg.wait_for_timeout(1000)
    E("()=>{tab='s';per='dY';render()}");pg.wait_for_timeout(400)
    bt=pg.inner_text('body')
    ok('Отклонено (2)' in bt and 'Отменено (1)' in bt,'013: «Отклонено (2)» and «Отменено (1)» counted separately by status')
    ok('рестораном' not in bt and 'Отклонён' not in bt,'013: history pills are neutral («Отклонено», not «rejected by the restaurant»)')
    ok(pg.locator('#stnote').count()==1 and 'не оценка ресторана' in pg.inner_text('#stnote'),'013: note — statuses, not a rating of the restaurant')
    ok('После комиссии' not in bt and 'Чистыми к получению' in bt,'014: «После комиссии» replaced by «Чистыми к получению»')
    br=pg.inner_text('#stbr') if pg.locator('#stbr').count() else ''
    nums=[float(x.replace('−','-').replace('−','-')) for x in re.findall(r'([−−]?\d+(?:\.\d+)?) TJS',br)]
    ok(len(nums)>=3 and abs(nums[0]+sum(nums[1:-1])-nums[-1])<0.011,'014: breakdown adds up (revenue − deductions = net) %s'%nums)
    exp=E("()=>{const r=x=>Math.round(x*100)/100;return r(TLB.orders(o=>o.store==STORE&&o.status=='delivered'&&o.commissionSet).reduce((s,o)=>s+o.subtotal-o.discount-(+o.commission||0)-(+o.pointsValue||0)-(+o.cashback||0)-(+o.feeWaived||0),0))}")
    ok(nums and abs(nums[-1]-exp)<0.011,'014: net = the unchanged formula (%s = %s)'%(nums[-1] if nums else None,exp))
    E("()=>{OD='ord5';render()}");pg.wait_for_timeout(300);md=pg.inner_text('.md')
    ok(pg.locator('#odcomno').count()==1 and 'не начисляется' in md and 'Вам' not in md and '−12' not in md,'012 restaurant: cancelled order — commission «not charged», no net payable')
    ok('причина не указана' in md,'013: no recorded code → «причина не указана»')
    E("()=>{OD='ord3';render()}");pg.wait_for_timeout(300);md=pg.inner_text('.md')
    ok('причина не указана' in md and 'свободный текст' not in md,'013: free text is never used as the reason')
    E("()=>{OD='ord6';render()}");pg.wait_for_timeout(300);md=pg.inner_text('.md')
    ok(E("()=>t('cr_out_of_stock')") in md,'013: a recorded code is shown')
    E("()=>{OD='ord4';render()}");pg.wait_for_timeout(300);md=pg.inner_text('.md')
    ok('−18 TJS' in md and 'Вам' in md and '144 TJS' in md,'012/014: a delivered order keeps its commission and «Вам» 144 (180−18−5−3−10, unchanged)')
    E("()=>{OD=null;TLB.setLang('en');render()}");pg.wait_for_timeout(300);bt=pg.inner_text('body')
    ok('Net payable to you' in bt and 'After commission' not in bt and 'Cancelled (1)' in bt,'014/013: English wording')
    for w in (360,):
        pg.set_viewport_size({'width':w,'height':780});E("()=>{TLB.setLang('ru');render()}");pg.wait_for_timeout(300)
        ok(E("()=>document.documentElement.scrollWidth<=innerWidth+1"),'restaurant stats at %d px: no horizontal scroll'%w)
    ok(not errs,'restaurant: no JS errors %s'%errs[:1]);pg.close()
    b.close()
print('\nUAT3 %d/%d'%(n-len(fails),n));sys.exit(1 if fails else 0)
