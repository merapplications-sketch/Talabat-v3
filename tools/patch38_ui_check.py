"""Patch 38 package — screens of the four apps on the read-only previews. The new server calls are replaced in the page by
controllable stand-ins (delayed / failed / unknown answers). Chromium only; server behaviour is in sql/test_patch38.sql and
tools/patch38_race.py. Electronic payments are not captured anywhere (no provider): only the agreement rules are shown.
  python3 tools/patch38_ui_check.py <customer_dir> <admin_dir> <driver_dir> <merchant_dir>"""
import sys
from playwright.sync_api import sync_playwright
CU,AD,DR,ME=sys.argv[1:5];fails=[];n=0
def ok(c,m):
    global n;n+=1;print(('PASS ' if c else 'FAIL ')+m)
    if not c: fails.append(m)
def page(b,d,app,w=390):
    pg=b.new_page(viewport={'width':w,'height':844},is_mobile=True,has_touch=True);errs=[];pg.on('pageerror',lambda e:errs.append(str(e)))
    pg.route('**/*',lambda rt,rq:(rt.abort() if rq.url.startswith('http') else rt.continue_()))
    dl=[];pg.on('dialog',lambda dg:(dl.append(dg.message),dg.accept('REF-9') if dg.type=='prompt' else dg.accept()))
    pg.goto('file://'+d+'/'+app+'.html');pg.wait_for_timeout(2500);pg.evaluate("()=>TLB.setLang('ru')");pg.wait_for_timeout(300);return pg,errs,dl
# controllable server call: window.__q[name] = pending calls, window.__a[name] = their arguments
CTL="""(names)=>{window.__q=window.__q||{};window.__a=window.__a||{};names.forEach(n=>{window.__q[n]=[];window.__a[n]=[];
  TLB[n]=function(){window.__a[n].push([...arguments]);return new Promise(r=>window.__q[n].push(r))}})}"""
with sync_playwright() as p:
    b=p.chromium.launch()
    # ================= customer: the store agreement at checkout =================
    pg,errs,dl=page(b,CU,'customer');E=pg.evaluate
    def pay(flags,uw=False):
        E("(f)=>{const s=window.__pvTables.stores.find(x=>x.id=='s1');Object.assign(s,f);TLB.reload()}",flags);pg.wait_for_timeout(900)
        E("()=>{syncStores();S.cart={i2:2};S.cartStore=STORES.find(x=>x.id=='s1').n;S.pay='card';S.useWallet=%s;S.usePts=true;go('pay')}"%('true' if uw else 'false'));pg.wait_for_timeout(900)
        return pg.inner_text('body')
    bt=pay({'accept_online':True,'allow_wallet':True,'allow_points':True})
    ok('Apple Pay' in bt or E("()=>document.querySelectorAll('.pay').length")==3,'customer: a store accepting online shows all methods (today’s behaviour)')
    bt=pay({'accept_online':False,'allow_wallet':True,'allow_points':True})
    ok(E("()=>document.querySelectorAll('.pay').length")==1 and E("()=>S.pay")=='cash' and pg.locator('#cashonly').count()==1 and 'Только наличные' in bt,'customer: cash-only store → only «cash», chosen automatically, clear notice (RU)')
    E("()=>{TLB.setLang('en');render()}");pg.wait_for_timeout(300)
    ok('Cash only' in pg.inner_text('#cashonly'),'customer: cash-only notice in English');E("()=>{TLB.setLang('ru');render()}")
    bt=pay({'accept_online':True,'allow_wallet':True,'allow_points':True},True)
    ok(E("()=>calc().w")>0,'customer: wallet allowed → the wallet is used as before')
    bt=pay({'accept_online':True,'allow_wallet':False,'allow_points':True},True)
    ok(E("()=>calc().w")==0 and 'Оплатить из кошелька' not in bt,'customer: wallet not allowed → no wallet switch, nothing taken from the wallet')
    bt=pay({'accept_online':True,'allow_wallet':True,'allow_points':False})
    ok(E("()=>calc().pts")==0 and E("()=>calc().canP")==False,'customer: points not allowed → no points used')
    E("()=>{const s=window.__pvTables.stores.find(x=>x.id=='s1');Object.assign(s,{accept_online:true,allow_wallet:true,allow_points:true});TLB.reload()}");pg.wait_for_timeout(600)
    E("()=>{TLB.orderWallet=()=>{const a=[{id:1,amount:20,kind:'refund',orderId:'ord5',ticketId:'t1',at:1}];a.partial=true;return Promise.resolve(a)};S.owl=null;const o=window.__pvTables.orders.find(o=>o.id=='ord5');o.status='cancelled';TLB.reload()}");pg.wait_for_timeout(900)
    E("()=>go('track',{tid:'ord5'})");pg.wait_for_timeout(500)
    ok('первые 2000' in (pg.inner_text('#stlcov') if pg.locator('#stlcov').count() else ''),'customer: if an order had more wallet operations than read, the receipt says so (no silent cap)')
    # v61: the automatic return shown is the RECORDED entry (0 after a full support refund; partial when capped)
    E("()=>{const o=window.__pvTables.orders.find(o=>o.id=='ord5');Object.assign(o,{status:'cancelled',wallet_used:50,wallet_returned_at:new Date().toISOString()});TLB.orderWallet=()=>Promise.resolve([{id:1,amount:-50,kind:'spend',orderId:'ord5',at:1},{id:2,amount:120,kind:'refund',orderId:'ord5',ticketId:'t1',at:2}]);S.owl=null;TLB.reload()}");pg.wait_for_timeout(900)
    E("()=>go('track',{tid:'ord5'})");pg.wait_for_timeout(500);st=pg.inner_text('#stl') if pg.locator('#stl').count() else ''
    ok('Автоматически при отмене не возвращалось' in st and '0 TJS' in st and '+120 TJS' in st and '+50 TJS' not in st,'customer v61: after a full support refund the cancel returned nothing — the receipt shows 0, not the wallet 50')
    E("()=>{TLB.orderWallet=()=>Promise.resolve([{id:1,amount:-50,kind:'spend',orderId:'ord5',at:1},{id:2,amount:30,kind:'refund',orderId:'ord5',ticketId:'t1',at:2},{id:3,amount:20,kind:'return',orderId:'ord5',at:3}]);S.owl=null;render()}");pg.wait_for_timeout(500)
    st=pg.inner_text('#stl') if pg.locator('#stl').count() else ''
    ok('+20 TJS' in st and '+30 TJS' in st and '+50 TJS' not in st,'customer v61: a capped automatic return shows the recorded 20 (not the wallet 50) next to the support refund 30')
    ok(not errs,'customer: no JS errors %s'%errs[:1]);pg.close()
    # ================= admin =================
    pg,errs,dl=page(b,AD,'admin');E=pg.evaluate
    E(CTL,['setStorePayRules','recordDriverSettlement','recordStoreSettlement','decideStorePayment'])
    # the same numbers as sql/test_patch38.sql (Kebab after A, B, E, D2; courier D) and the owner's example alone (courier B)
    E("""()=>{TLB.storePosition=()=>Promise.resolve({gross:300,commission:30,store_funded:0,net_due:270,cp_bill:300,cp_paid:300,cp_paid_confirmed:200,cp_paid_disputed:100,cp_unpaid:0,cp_paid_open:100,cp_owed_by_store:30,pp_net_due:0,pp_paid_done:0,pp_paid_pending:0,pp_available:0,unassigned_due:90});
      TLB.driverPosition=id=>Promise.resolve(id==window.__dA?{collected:330,store_paid:300,store_paid_confirmed:200,store_paid_disputed:100,store_paid_open:100,pay_kept:60,handed_to_platform:0,repaid_to_courier:0,net:-30,can_hand_over:0,owed_to_courier:30,ps_pay_earned:20,ps_pay_paid:15,ps_pay_due:5}
                                                            :{collected:120,store_paid:100,store_paid_confirmed:0,store_paid_disputed:0,store_paid_open:0,pay_kept:20,handed_to_platform:0,repaid_to_courier:0,net:0,can_hand_over:0,owed_to_courier:0,ps_pay_earned:0,ps_pay_paid:0,ps_pay_due:0});
      window.__mr=[];TLB.moneyRecords=(k,by,before,size)=>{window.__mr.push([k,by,before]);const base=before==null?100:before;
        const rows=Array.from({length:20},(_,i)=>({id:base-1-i,recorded_at:new Date().toISOString(),amount:5,after_amount:1,direction:'driver_to_platform',method:'bank',status:'done',reference:'R'+(base-1-i),
          recorded_by_name:i==0?null:'Finance Farhod',order_id:'ord1'}));return Promise.resolve({rows,more:base>60})}}""")
    # store: agreement + money
    sid=E("()=>{const s=TLB.stores(true)[0];return s.id}")
    E("(id)=>{tab='s';E=id;render()}",sid);pg.wait_for_timeout(600)
    ok(pg.locator('#prcard').count()==1 and pg.locator('#smcard').count()==1,'admin store: «payment and settlement» and «settlement with the place» cards')
    pg.uncheck('#pr-on');pg.select_option('#pr-me','driver_pays');pg.click('#pr-go');pg.wait_for_timeout(150)
    ok(E("()=>__a.setStorePayRules.length")==1 and E("()=>__a.setStorePayRules[0].slice(1)")==[False,True,True,'driver_pays'],'admin store: saves cash-only + «courier pays the place» through the server function')
    E("()=>__q.setStorePayRules[0]({ok:true})");pg.wait_for_timeout(200)
    sm=pg.inner_text('#smcard')
    ok('Чек доставленных заказов' in sm and '-300.00' in sm and 'Курьеры ещё не оплатили' in sm and 'незавершённым или отменённым заказам: 100.00' in sm,'admin store v61: bill 300 paid 300 by couriers (recorded = paid), left 0; payments on unfinished / cancelled orders apart')
    ok('подтвердило 200.00 из 300.00' in sm and 'не обязательно' in sm and 'Оспорено заведением: 100.00' in sm and 'ответственность не определена' in sm,'admin store v61: confirmation optional (200 of 300 confirmed), disputed apart without blame')
    ok('Заведение должно платформе' in sm and '30.00' in sm and 'не вычитается' in sm and 'не задан' in sm,'admin store v61: commission 30 shown as owed BY THE STORE, not deducted from the bill; collection not invented')
    ok('Платформа может оплатить' in sm and 'без способа расчёта: 90.00' in sm,'admin store: platform part apart; orders without a method shown as payable by neither path')
    ok('имя не указано' in sm and 'Finance Farhod' in sm,'admin store: history shows who recorded; a missing name is said, not hidden')
    pg.click('#more-hs'+sid.replace('-','')[:0] if False else '[id^=more-hs]');pg.wait_for_timeout(300)
    ok(E("()=>__mr.filter(x=>x[0]=='pss').length")==2 and E("()=>__mr.filter(x=>x[0]=='pss')[1][2]")==80,'admin store: «show more» loads the next page after the last id (stable order)')
    pg.fill('#ss-a','50');pg.fill('#ss-r','BANK-1');pg.click('#ss-go');pg.wait_for_timeout(150);pg.locator('#ss-go').click(force=True);pg.wait_for_timeout(150)
    k1=E("()=>__a.recordStoreSettlement[0][6]")
    ok(E("()=>__a.recordStoreSettlement.length")==1 and k1,'admin store: a settlement sent ONCE with its form key (double tap ignored)')
    E("()=>__q.recordStoreSettlement[0]({error:'unknown'})");pg.wait_for_timeout(200)
    ok('не создаст вторую запись' in pg.inner_text('#smcard'),'admin store: unknown answer → «check the history; sending again will not record twice»')
    pg.click('#ss-go');pg.wait_for_timeout(150)
    ok(E("()=>__a.recordStoreSettlement[1][6]")==k1,'admin store: the retry uses the SAME key')
    E("()=>__q.recordStoreSettlement[1]({ok:true,row:{}})");pg.wait_for_timeout(200)
    ok('Записано' in pg.inner_text('#smcard') and E("()=>FM['ss:'+E].key")!=k1,'admin store: after success a new form (new key)')
    # courier: isolation of two forms
    dA,dB=E("()=>[TLB.drivers()[0].id,TLB.drivers()[1].id]");E("(d)=>{window.__dA=d}",dA)
    E("(id)=>{tab='d';E=null;DE=id;render()}",dA);pg.wait_for_timeout(500)
    dm=pg.inner_text('#dmcard')
    ok('330.00' in dm and '-300.00' in dm and 'Оставил себе оплату доставки' in dm and '-60.00' in dm and 'Сдать платформе' in dm and 'Старый учёт' in dm,'admin courier v61: collected 330 − paid to places 300 − pay kept 60 → nothing to hand over; old accounting apart')
    ok('Платформа должна курьеру' in dm and '30.00' in dm and 'К выплате курьеру' in dm and '5.00' in dm and 'не повторяется' in dm,'admin courier v61: owed to him 30 and platform-settled pay 5 shown apart (pay counted once)')
    ok('Оспорено заведениями: 100.00' in dm and 'ответственность не определена' in dm and 'незавершённым или отменённым заказам: 100.00' in dm and pg.locator('#ds-adv-go').count()==1 and 'подготовлен к проверке' in dm,'admin courier v61: disputed held apart without blame; payments on unfinished orders apart; payout path labelled as prepared for review')
    pg.fill('#ds-in-a','60');pg.fill('#ds-in-r','KASSA-1');pg.click('#ds-in-go');pg.wait_for_timeout(150)
    ok(E("()=>__a.recordDriverSettlement.length")==1 and E("()=>__a.recordDriverSettlement[0][1]")=='driver_to_platform','admin courier A: cash receipt sent (answer pending)')
    E("(id)=>{DE=id;render()}",dB);pg.wait_for_timeout(400)
    dmb=pg.inner_text('#dmcard')
    ok('120.00' in dmb and '-100.00' in dmb and '-20.00' in dmb and 'Платформа должна курьеру' not in dmb,'admin courier v61 — OWNER EXAMPLE: collected 120, paid the place 100, kept 20 → hand over 0.00, nothing owed')
    pg.fill('#ds-in-a','7');E("()=>__q.recordDriverSettlement[0]({error:'amount_too_high'})");pg.wait_for_timeout(300)
    ok(pg.input_value('#ds-in-a')=='7' and 'больше остатка' not in pg.inner_text('#dmcard') and not pg.locator('#ds-in-go').is_disabled(),'admin: courier A’s answer does NOT touch courier B’s open form')
    ok(E("(d)=>FM['ds:driver_to_platform:'+d].msg",dA).startswith('Сумма больше'),'… it lands on courier A’s own form')
    pg.click('#ds-out-go') if False else None
    # order card: courier → store payment
    E("""()=>{TLB.moneyRecords=(k,by)=>Promise.resolve({rows:k=='dsp'?[{id:7,order_id:by.order_id,amount:100,reference:'CHK-1',status:'claimed',recorded_at:new Date().toISOString(),decided_by_name:null}]:[],more:false})}""")
    h=E("()=>{const o=Object.assign({},TLB.order('ord4'),{payRules:{settle_method:'driver_pays'}});return dspBox(o)}");pg.wait_for_timeout(300)
    h=E("()=>{const o=Object.assign({},TLB.order('ord4'),{payRules:{settle_method:'driver_pays'}});return dspBox(o)}")
    ok('CHK-1' in h and 'Подтвердить' in h and 'подтверждение не обязательно' in h,'admin order: the courier’s payment to the place (recorded = paid), confirm / dispute optional for finance')
    E("()=>{TLB.orderWallet=()=>Promise.resolve([{id:3,amount:20,kind:'return',orderId:'ord4',at:3}])}")
    E("()=>finBox(Object.assign({},TLB.order('ord4'),{status:'cancelled',walletUsed:50,walletReturnedAt:Date.now()}))");pg.wait_for_timeout(300)
    h=E("()=>finBox(Object.assign({},TLB.order('ord4'),{status:'cancelled',walletUsed:50,walletReturnedAt:Date.now()}))")
    ok('20.00 TJS (не больше, чем осталось после возвратов поддержки)' in h,'admin order v61: the automatic return shown is the recorded 20, said to be capped (not the wallet 50)')
    ok(E("()=>dspBox(Object.assign({},TLB.order('ord4'),{payRules:{settle_method:'platform_settles'}}))")=='','admin order: nothing for «platform settles» orders')
    ok(not errs,'admin: no JS errors %s'%errs[:1]);pg.close()
    # ================= courier =================
    pg,errs,dl=page(b,DR,'driver');E=pg.evaluate
    E(CTL,['recordStorePayment'])
    E("()=>{TLB.moneyRecords=()=>Promise.resolve({rows:[],more:false});TLB.driverPosition=()=>Promise.resolve({collected:330,store_paid:300,store_paid_confirmed:200,store_paid_disputed:100,store_paid_open:100,pay_kept:60,handed_to_platform:0,repaid_to_courier:0,net:-30,can_hand_over:0,owed_to_courier:30,ps_pay_earned:20,ps_pay_paid:15,ps_pay_due:5})}")
    E("()=>{const o=window.__pvTables.orders.find(o=>o.id=='ord2');Object.assign(o,{status:'ready',driver_id:TLB.me().id||o.driver_id,payment:'cash',subtotal:100,discount:0,total:120,wallet_used:0,driver_payout:20,pay_rules:{settle_method:'driver_pays',courier_pay:'keeps_fee_from_cash'}});TLB.reload()}");pg.wait_for_timeout(900)
    h=E("()=>storePayBox(TLB.order('ord2'))");pg.wait_for_timeout(300);E("()=>render()")
    h=E("()=>storePayBox(TLB.order('ord2'))")
    ok('Оплата заведению' in h and 'sp-go' in h,'courier: a «courier pays the place» order shows the payment form')
    import re as _re; tx=' '.join(_re.sub('<[^>]+>',' ',h).replace(' TJS','').split())
    ok('Заплатить заведению (чек) 100.00' in tx and 'Получить с клиента 120.00' in tx and 'Оставить себе (оплата доставки) 20.00' in tx and 'Сдать платформе по заказу 0.00' in tx,'courier v61 — OWNER EXAMPLE on the order: pay 100, collect 120, keep 20, hand over 0')
    ok('value="100"' in h and 'не обязательно' in h,'courier v61: the amount is prefilled with the bill (100); the place\'s confirmation is said to be optional')
    tc=' '.join(_re.sub('<[^>]+>',' ',E("()=>storePayBox(Object.assign({},TLB.order('ord2'),{payment:'card'}))")).replace(' TJS','').split())
    ok('Получить с клиента 0.00' in tc and 'Платформа должна вам по заказу 120.00' in tc,'courier v61: a «card» order — nothing to collect, the platform owes him the bill 100 + his pay 20')
    E("()=>{document.body.insertAdjacentHTML('beforeend','<div id=\"spwrap\">'+storePayBox(TLB.order('ord2'))+'</div>')}")
    E("()=>{spOf('ord2').a='100';spOf('ord2').r='CHK-77';spSend('ord2');spSend('ord2')}");pg.wait_for_timeout(200)
    k=E("()=>__a.recordStorePayment[0][4]")
    ok(E("()=>__a.recordStorePayment.length")==1 and E("()=>__a.recordStorePayment[0].slice(0,3)")==['ord2',100,'CHK-77'] and k,'courier: payment sent ONCE (double tap), with amount, receipt number and a form key')
    E("()=>__q.recordStorePayment[0]({error:'unknown'})");pg.wait_for_timeout(200)
    ok('не создаст вторую запись' in E("()=>spOf('ord2').msg"),'courier: unknown answer → message, nothing recorded twice on retry')
    E("()=>{spSend('ord2')}");pg.wait_for_timeout(150)
    ok(E("()=>__a.recordStorePayment[1][4]")==k,'courier: the retry uses the SAME key')
    ok(E("()=>storePayBox(Object.assign({},TLB.order('ord2'),{payRules:{settle_method:'platform_settles'}}))")=='','courier: nothing for «platform settles» orders (commission never shown)')
    E("()=>{tab='m';render()}");pg.wait_for_timeout(500)
    h=E("()=>myMoneyCard()")
    tx=' '.join(_re.sub('<[^>]+>',' ',h).replace(' TJS','').split())
    ok('Мои деньги' in tx and 'Сдать платформе 0.00' in tx and 'Оплата доставки (осталась у вас) -60.00' in tx and 'Платформа должна вам 30.00' in tx and 'К выплате вам 5.00' in tx and 'один раз' in tx,'courier v61: own money — paid to places, pay kept, nothing to hand over, owed 30, platform-settled pay 5 apart (counted once)')
    ok('Оспорено заведениями: 100.00' in tx and 'незавершённым или отменённым заказам: 100.00' in tx,'courier v61: disputed and unfinished-order payments shown apart')
    ok('комисс' not in h.lower(),'courier: the platform commission is not shown to the courier')
    ok(not errs,'courier: no JS errors %s'%errs[:1]);pg.close()
    # ================= restaurant =================
    pg,errs,dl=page(b,ME,'merchant');E=pg.evaluate
    E(CTL,['decideStorePayment'])
    E("""()=>{TLB.moneyRecords=(k,by)=>Promise.resolve({rows:k=='dsp'?[{id:9,order_id:by.order_id,amount:100,reference:'CHK-9',status:'claimed',recorded_at:new Date().toISOString()}]:[],more:false});
      TLB.storePosition=()=>Promise.resolve({gross:300,commission:30,store_funded:0,net_due:270,cp_bill:300,cp_paid:280,cp_paid_confirmed:200,cp_paid_disputed:0,cp_unpaid:20,cp_paid_open:0,cp_owed_by_store:30,pp_net_due:90,pp_paid_done:50,pp_paid_pending:0,pp_available:40,unassigned_due:0})}""")
    h=E("()=>odPayBox(Object.assign({},TLB.order('ord1'),{payRules:{settle_method:'driver_pays'}}))");pg.wait_for_timeout(300)
    h=E("()=>odPayBox(Object.assign({},TLB.order('ord1'),{payRules:{settle_method:'driver_pays'}}))")
    ok('CHK-9' in h and 'Подтвердить' in h and 'Не получено' in h and 'подтверждать не обязательно' in h,'restaurant: the courier’s payment for the order; confirming is optional, «not received» possible')
    E("()=>{mhDecide(9,true,'o:ord1')}");pg.wait_for_timeout(150)
    ok(E("()=>__a.decideStorePayment[0]")==[9,True,''],'restaurant: confirmation sent through the server function')
    E("()=>{tab='s';per='dY';render()}");pg.wait_for_timeout(500)
    st=pg.inner_text('#setlcard') if pg.locator('#setlcard').count() else ''
    ok('Курьеры ещё не оплатили' in st and '20' in st and 'Остаток к получению' in st and '40' in st and 'оплачивает курьер' in st and 'рассчитывается платформа' in st,'restaurant v61: bill 300, received from couriers 280, 20 left; platform part apart (40 left)')
    ok('Вы должны платформе' in st and '30' in st and 'не вычитается' in st and 'пока не задан' in st,'restaurant v61: the commission 30 is shown as owed by the restaurant, not deducted from what the courier pays; no collection invented')
    ok(not errs,'restaurant: no JS errors %s'%errs[:1]);pg.close()
    b.close()
print('\nP38 UI %d/%d'%(n-len(fails),n));sys.exit(1 if fails else 0)
