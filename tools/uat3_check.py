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
# points stand-ins: LOY = summary; the snapshot (history + balance read together) is a promise the test answers (__q), counted (__calls)
STUB="""()=>{window.__realSnap=TLB.pointsSnapshot;window.__realAb=TLB.pointsAbandon;window.LOY={balance:900,voucher_points:1000,points_per_tjs:100,earn_per_tjs:10,min_redeem:1000,min_order:30,expiry_days:90,cashback_pct:0,rate_reward:10};
  window.PTS=[];window.__ab=0;TLB.loyalty=()=>LOY;TLB.points=()=>PTS;window.__q=[];window.__calls=0;
  TLB.pointsSnapshot=()=>{window.__calls++;return new Promise((res,rej)=>__q.push({res,rej}))};TLB.pointsAbandon=()=>{window.__ab++};
  Object.keys(localStorage).filter(k=>/^tlb-l[bm]-/.test(k)).forEach(k=>localStorage.removeItem(k));
  Object.assign(PL,{busy:0,again:0,bal:null,sig:null,failAt:0,retry:0});go('wallet')}"""
CF="()=>document.querySelectorAll('.cfw').length"
def snap(E,bal,cons='true',idx=0):
    # answer the oldest pending read with the current PTS rows and the given balance
    E("()=>{LOY.balance=%s;const x=__q.shift();x&&x.res({rows:PTS.slice(),balance:%s,consistent:%s})}"%(bal,bal,cons))
def rows(E,js):E("()=>{PTS=[%s].concat(PTS)}"%js)
def ev(E,name):E("()=>{PL.sig='%s';ptsWatch()}"%name)
def clr(E):E("()=>document.querySelectorAll('.cfw').forEach(x=>x.remove())")
with sync_playwright() as p:
    b=p.chromium.launch()
    # ================= UAT009 / UAT008: customer points =================
    pg,errs=page(b,CU,'customer');E=pg.evaluate
    E(STUB);E("()=>ptsWatch()");pg.wait_for_timeout(100)
    ok(E("()=>__calls")==1,'009: first look → one read (history + balance)')
    E("()=>{PL.sig='e1';ptsWatch();PL.sig='e2';ptsWatch();LOY.balance=901;ptsWatch()}")
    ok(E("()=>__calls")==1,'009: three events during the read → still ONE read in flight')
    rows(E,"{id:5,kind:'earn',points:300,orderId:'ord4'},{id:4,kind:'spend',points:-1000,orderId:'ord3'}");snap(E,900);pg.wait_for_timeout(150)
    ok(E("()=>__calls")==2,'009: events during the read → exactly ONE more read after it (%d)'%E("()=>__calls"))
    snap(E,900);pg.wait_for_timeout(150);E("()=>render()");pg.wait_for_timeout(150)
    ok(E("()=>__calls")==2,'009: no further read when nothing changed (%d)'%E("()=>__calls"))
    ok(E(CF)==0 and E("()=>localStorage.getItem(uidK('tlb-lm-'))")=='5','008: first read sets the mark (last row 5), no celebration for old rows')
    ok(E("()=>document.querySelectorAll('.card .dr').length")>=2,'009: history shown in the wallet')
    pg.wait_for_timeout(3000);ok(E("()=>__calls")==2,'009: no timer — idle 3 s, no read')
    # reviewer case: earn +200 and spend −200 together (balance stays 900), then a return +200 alone (1100)
    rows(E,"{id:7,kind:'spend',points:-200,orderId:'ord1'},{id:6,kind:'earn',points:200,orderId:'ord4'}");ev(E,'r1');snap(E,900);pg.wait_for_timeout(250)
    ok(E(CF)==0,'008 (review case): earn +200 and spend −200 in one batch, balance 900 → no celebration')
    rows(E,"{id:8,kind:'return',points:200,orderId:'ord1'}");ev(E,'r2');snap(E,1100);pg.wait_for_timeout(250)
    ok(E(CF)==0,'008 (review case): a later return +200 → 1100 → NO celebration (the earlier gain does not carry over)')
    # same balance, spend + return in one batch: the order event still re-reads
    c0=E("()=>__calls");rows(E,"{id:10,kind:'return',points:1000,orderId:'ord5'},{id:9,kind:'spend',points:-1000,orderId:'ord5'}")
    E("()=>{window.__pvTables.orders.find(o=>o.id=='ord0').status='cancelled'}");E("()=>TLB.reload()");pg.wait_for_timeout(900)
    ok(E("()=>__calls")==c0+1,'009: an order status event re-reads the history even with the SAME balance');snap(E,1100);pg.wait_for_timeout(200)
    ok(E("()=>document.body.innerText.includes(t('pk_return'))") and E(CF)==0,'009: the return row appears without a page reload, no celebration')
    # return lifting over a step while a small earn is in the same batch: the earn does not take the credit
    rows(E,"{id:12,kind:'earn',points:10,orderId:'ord4'},{id:11,kind:'return',points:900,orderId:'ord2'}");ev(E,'r3');snap(E,2010);pg.wait_for_timeout(250)
    ok(E(CF)==0,'008: return lifts 1100 → 2000, a small earn (+10) in the same batch → no celebration')
    # a new earn that itself crosses a step → one celebration
    rows(E,"{id:13,kind:'earn',points:1000,orderId:'ord4'}");ev(E,'r4');snap(E,3010);pg.wait_for_timeout(250)
    ok(E(CF)==1,'008: a NEW earn crossing 3000 → one celebration');clr(E)
    E("()=>{Object.assign(PL,{busy:0,again:0,bal:null,sig:null,retry:0});ptsWatch()}");pg.wait_for_timeout(100);snap(E,3010);pg.wait_for_timeout(250);E("()=>render()");pg.wait_for_timeout(150)
    ok(E(CF)==0,'008: reopening / re-reading does not repeat the celebration')
    # rating reward crossing a step → celebrates (not dropped by an earn-only rule)
    rows(E,"{id:14,kind:'spend',points:-15,orderId:'ord3'}");ev(E,'r5');snap(E,2995);pg.wait_for_timeout(200)
    rows(E,"{id:15,kind:'reward',points:10,orderId:'ord4'}");ev(E,'r6');snap(E,3005);pg.wait_for_timeout(250)
    ok(E(CF)==1,'008: a NEW rating reward crossing 3000 → celebration');clr(E)
    # history and balance out of step (a write between the reads): nothing decided, mark kept; the next consistent read decides once
    rows(E,"{id:16,kind:'earn',points:1000,orderId:'ord4'}");ev(E,'r7');snap(E,3005,'false');pg.wait_for_timeout(250)
    ok(E(CF)==0 and E("()=>localStorage.getItem(uidK('tlb-lm-'))")=='15','008: history newer than its balance (not consistent) → no decision, mark stays 15')
    E("()=>{LOY.balance=4005;ptsWatch()}");pg.wait_for_timeout(100)
    ok(E("()=>__calls")>c0+5,'009: the new balance (arriving first through the summary) triggers a read');snap(E,4005);pg.wait_for_timeout(250)
    ok(E(CF)==1 and E("()=>localStorage.getItem(uidK('tlb-lm-'))")=='16','008: the consistent read celebrates the earn crossing 4000 once');clr(E)
    E("()=>render()");pg.wait_for_timeout(150);ok(E(CF)==0,'008: a redraw does not repeat it')
    # failure: the loader is freed; the next event reads again
    c0=E("()=>__calls");ev(E,'f1');snap_fail="()=>{const x=__q.shift();x&&x.res(null)}";E(snap_fail);pg.wait_for_timeout(200)
    ok(E("()=>PL.busy")==0 and E("()=>PL.failAt")>0,'009: a failed read frees the loader')
    ev(E,'f2');pg.wait_for_timeout(100);ok(E("()=>__calls")==c0+2,'009: the next event reads again after a failure');snap(E,4005)
    ok(E("()=>uidK('tlb-lm-')").endswith(E("()=>(TLB.me()||{}).id")),'008: the mark is stored per user id')
    E("()=>{TLB.rateOrder=()=>Promise.resolve({});rt0('ord4').s=5}");c0=E("()=>__calls")
    E("()=>sendRate('ord4')");pg.wait_for_timeout(300);ok(E("()=>__calls")>c0,'009: a saved rating re-reads the history');snap(E,4005)
    ok(not errs,'customer points: no JS errors %s'%errs[:1]);pg.close()
    # ================= UAT009: 15 s limit with a simulated clock =================
    pg,errs=page(b,CU,'customer');E=pg.evaluate;pg.clock.install();E(STUB)
    E("()=>{localStorage.setItem(uidK('tlb-lm-'),'20');ptsWatch()}");pg.clock.run_for(100)
    ok(E("()=>__calls")==1 and E("()=>PL.busy")==1,'009 timeout: a read is in flight')
    pg.clock.run_for(15100)
    ok(E("()=>__ab")==1 and E("()=>__calls")==2,'009 timeout: after 15 s the read is abandoned and retried ONCE (abandon %d, reads %d)'%(E("()=>__ab"),E("()=>__calls")))
    E("()=>{PTS=[{id:21,kind:'earn',points:1000,orderId:'ord4'}];const x=__q.shift();x.res({rows:PTS.slice(),balance:1900,consistent:true})}");pg.clock.run_for(100)
    ok(E(CF)==0 and E("()=>localStorage.getItem(uidK('tlb-lm-'))")=='20','009 timeout: the LATE reply of the abandoned read is ignored (no celebration, mark unchanged)')
    pg.clock.run_for(15100)
    ok(E("()=>__ab")==2 and E("()=>__calls")==2 and E("()=>PL.busy")==0,'009 timeout: the retry also times out → no further automatic read (no polling)')
    pg.clock.run_for(60000);ok(E("()=>__calls")==2,'009 timeout: 60 s later still no automatic read')
    ev(E,'t1');pg.clock.run_for(100);ok(E("()=>__calls")==3,'009 timeout: the next event reads again')
    E("()=>{const x=__q.pop();x.res({rows:PTS.slice(),balance:1900,consistent:true})}");pg.clock.run_for(100)   # the newest read (the retry's reply never came)
    ok(E(CF)==1 and E("()=>localStorage.getItem(uidK('tlb-lm-'))")=='21','009 timeout: the fresh read is applied (the earn crossing 1000 celebrates once)')
    ok(not errs,'customer timeout: no JS errors %s'%errs[:1]);pg.close()
    # ================= core: consistent snapshot =================
    pg,errs=page(b,CU,'customer');E=pg.evaluate
    r=E("async()=>{const x=await TLB.pointsSnapshot();return x&&{c:x.consistent,b:x.balance,n:x.rows.length}}")
    ok(r and r['c'] is True and r['b']==2850,'009 core: history + balance read as a consistent pair %s'%r)
    r=E("""async()=>{const T=window.__pvTables,base=T.loyalty_ledger,u=base[0].user_id;let n=0;
      Object.defineProperty(T,'loyalty_ledger',{configurable:true,get(){n++;if(n==2)base.unshift({id:999,user_id:u,points:50,kind:'earn',order_id:'ord4',created_at:new Date().toISOString()});return base.slice()}});
      const x=await TLB.pointsSnapshot();return {c:x&&x.consistent,reads:n,top:x&&x.rows[0].id}}""")
    ok(r['c'] is True and r['reads']>=4 and r['top']==999,'009 core: a write between the reads → read again until both reads agree %s'%r)
    r=E("async()=>{const a=TLB.pointsSnapshot(),b=TLB.pointsSnapshot();return [await a===null,(await b)!==null]}")
    ok(r==[True,True],'009 core: of two overlapping reads the older reply is ignored')
    r=E("async()=>{const a=TLB.pointsSnapshot();TLB.pointsAbandon();return await a}")
    ok(r is None,'009 core: an abandoned read is ignored when its reply comes')
    ok(not errs,'core snapshot: no JS errors %s'%errs[:1]);pg.close()
    # ================= UAT012: customer receipt of a cancelled order =================
    pg,errs=page(b,CU,'customer');E=pg.evaluate
    E("()=>{window.__owReal=id=>Promise.resolve(window.__pvTables.wallet_entries.filter(e=>e.order_id==id).map(e=>({id:e.id,amount:+e.amount,kind:e.kind,orderId:e.order_id,ticketId:e.ticket_id,at:Date.parse(e.created_at)})));TLB.orderWallet=window.__owReal}")
    def setord(js):E("()=>{const o=window.__pvTables.orders.find(o=>o.id=='ord5');Object.assign(o,%s)}"%js);E("()=>TLB.reload()");pg.wait_for_timeout(900);E("()=>{go('track',{tid:'ord5'})}");pg.wait_for_timeout(400)
    # v61: the live trigger writes the return entry together with wallet_returned_at; the receipt reads the entry (it can be capped)
    E("()=>{const W=window.__pvTables.wallet_entries;if(!W.some(e=>e.order_id=='ord5'&&e.kind=='return'))W.push({id:99005,user_id:'u',amount:124.38,kind:'return',order_id:'ord5',ticket_id:null,created_at:new Date().toISOString()})}")
    setord("{status:'cancelled',subtotal:265,discount:0,delivery_fee:10,tip:0,total:275,payment:'cash',wallet_used:124.38,points_used:1000,points_value:10,wallet_returned_at:new Date().toISOString(),points_returned_at:new Date().toISOString(),cash_collected:null}")
    E("()=>{S.owl=null;render()}");pg.wait_for_timeout(400)
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
    E("()=>{S.owl=null;render()}");pg.wait_for_timeout(500)
    st=pg.inner_text('#stl') if pg.locator('#stl').count() else ''
    ok('Возврат по обращению #t7' in st and '+20 TJS' in st and 'автоматически' not in st.split('Возврат по обращению')[1],'012: a support refund is its own line, apart from the automatic return')
    E("()=>{const T=window.__pvTables.wallet_entries,u=T[0].user_id,n=Date.now();for(let i=0;i<70;i++)T.push({id:'wx'+i,user_id:u,amount:1,kind:'adjust',order_id:null,note:'x',created_at:new Date(n+1000+i).toISOString()})}")
    E("()=>{S.owl=null}");setord("{}");pg.wait_for_timeout(600)
    st=pg.inner_text('#stl') if pg.locator('#stl').count() else ''
    ok('#t7' in st and pg.locator('#stlcov').count()==0,'012 (patch 37 package): 70 newer wallet operations → the refund of THIS order is still shown, no limit note')
    ok('По записям системы' in pg.inner_text('#stl') and 'Итог по заказу' not in pg.inner_text('#stl'),'012: the block is titled «По записям системы» (not a full settlement)')
    E("()=>{TLB.orderWallet=()=>Promise.resolve(null);S.owl=null;render()}");pg.wait_for_timeout(400)
    ok('не проверены' in (pg.inner_text('#stlcov') if pg.locator('#stlcov').count() else ''),'012: the per-order read failed → «support refunds not checked here»')
    E("()=>{TLB.orderWallet=window.__owReal;S.owl=null}")
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
    ok('при доставке' in E("()=>document.body.textContent"),'015: store page: the same estimate note (v80: inside the folded points line)')
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
