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
    ok(not errs,'customer: no JS errors %s'%errs[:1]);pg.close()
    # ================= admin =================
    pg,errs,dl=page(b,AD,'admin');E=pg.evaluate
    E(CTL,['setStorePayRules','recordDriverSettlement','recordStoreSettlement','decideStorePayment'])
    E("""()=>{TLB.storePosition=()=>Promise.resolve({gross:300,commission:30,store_funded:0,net_due:270,paid_by_drivers:400,paid_by_platform:0,balance:-130,paid_on_undelivered:100,claimed_unconfirmed:200});
      TLB.driverPosition=id=>Promise.resolve(id==window.__dA?{collected:300,paid_to_stores_confirmed:200,paid_to_stores_claimed:0,handed_to_platform:0,cash_held:100,earned:40,earnings_paid:15,earnings_due:25}
                                                            :{collected:50,paid_to_stores_confirmed:0,paid_to_stores_claimed:0,handed_to_platform:0,cash_held:50,earned:10,earnings_paid:0,earnings_due:10});
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
    ok('-130.00' in sm and 'Отрицательный остаток' in sm and 'неполученным заказам: 100.00' in sm,'admin store: position with its negative balance and the «paid on undelivered orders» item explained')
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
    ok('100.00' in dm and 'К выплате курьеру' in dm and 'не вычитается' in dm and 'Старый учёт' in dm,'admin courier: cash held, pay owed (not netted), old accounting shown apart')
    pg.fill('#ds-in-a','60');pg.fill('#ds-in-r','KASSA-1');pg.click('#ds-in-go');pg.wait_for_timeout(150)
    ok(E("()=>__a.recordDriverSettlement.length")==1 and E("()=>__a.recordDriverSettlement[0][1]")=='driver_to_platform','admin courier A: cash receipt sent (answer pending)')
    E("(id)=>{DE=id;render()}",dB);pg.wait_for_timeout(400)
    pg.fill('#ds-in-a','7');E("()=>__q.recordDriverSettlement[0]({error:'amount_too_high'})");pg.wait_for_timeout(300)
    ok(pg.input_value('#ds-in-a')=='7' and 'больше остатка' not in pg.inner_text('#dmcard') and not pg.locator('#ds-in-go').is_disabled(),'admin: courier A’s answer does NOT touch courier B’s open form')
    ok(E("(d)=>FM['ds:driver_to_platform:'+d].msg",dA).startswith('Сумма больше'),'… it lands on courier A’s own form')
    pg.click('#ds-out-go') if False else None
    # order card: courier → store payment
    E("""()=>{TLB.moneyRecords=(k,by)=>Promise.resolve({rows:k=='dsp'?[{id:7,order_id:by.order_id,amount:100,reference:'CHK-1',status:'claimed',recorded_at:new Date().toISOString(),decided_by_name:null}]:[],more:false})}""")
    h=E("()=>{const o=Object.assign({},TLB.order('ord4'),{payRules:{settle_method:'driver_pays'}});return dspBox(o)}");pg.wait_for_timeout(300)
    h=E("()=>{const o=Object.assign({},TLB.order('ord4'),{payRules:{settle_method:'driver_pays'}});return dspBox(o)}")
    ok('CHK-1' in h and 'Подтвердить' in h and 'Ждёт подтверждения' in h,'admin order: the courier’s payment to the place, with confirm / dispute for finance')
    ok(E("()=>dspBox(Object.assign({},TLB.order('ord4'),{payRules:{settle_method:'platform_settles'}}))")=='','admin order: nothing for «platform settles» orders')
    ok(not errs,'admin: no JS errors %s'%errs[:1]);pg.close()
    # ================= courier =================
    pg,errs,dl=page(b,DR,'driver');E=pg.evaluate
    E(CTL,['recordStorePayment'])
    E("()=>{TLB.moneyRecords=()=>Promise.resolve({rows:[],more:false});TLB.driverPosition=()=>Promise.resolve({collected:300,paid_to_stores_confirmed:200,paid_to_stores_claimed:100,handed_to_platform:0,cash_held:0,earned:40,earnings_paid:15,earnings_due:25})}")
    E("()=>{const o=window.__pvTables.orders.find(o=>o.id=='ord2');Object.assign(o,{status:'ready',driver_id:TLB.me().id||o.driver_id,pay_rules:{settle_method:'driver_pays'}});TLB.reload()}");pg.wait_for_timeout(900)
    h=E("()=>storePayBox(TLB.order('ord2'))");pg.wait_for_timeout(300);E("()=>render()")
    h=E("()=>storePayBox(TLB.order('ord2'))")
    ok('Оплата заведению' in h and 'sp-go' in h,'courier: a «courier pays the place» order shows the payment form')
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
    ok('Мои деньги' in h and '25.00' in h and 'не вычитается' in h and 'ждут подтверждения заведения: 100.00' in h,'courier: own money — held, paid to places, pay owed (not netted), awaiting confirmation')
    ok('комисс' not in h.lower(),'courier: the platform commission is not shown to the courier')
    ok(not errs,'courier: no JS errors %s'%errs[:1]);pg.close()
    # ================= restaurant =================
    pg,errs,dl=page(b,ME,'merchant');E=pg.evaluate
    E(CTL,['decideStorePayment'])
    E("""()=>{TLB.moneyRecords=(k,by)=>Promise.resolve({rows:k=='dsp'?[{id:9,order_id:by.order_id,amount:100,reference:'CHK-9',status:'claimed',recorded_at:new Date().toISOString()}]:[],more:false});
      TLB.storePosition=()=>Promise.resolve({gross:300,commission:30,store_funded:0,net_due:270,paid_by_drivers:200,paid_by_platform:50,balance:20,paid_on_undelivered:0,claimed_unconfirmed:100})}""")
    h=E("()=>odPayBox(Object.assign({},TLB.order('ord1'),{payRules:{settle_method:'driver_pays'}}))");pg.wait_for_timeout(300)
    h=E("()=>odPayBox(Object.assign({},TLB.order('ord1'),{payRules:{settle_method:'driver_pays'}}))")
    ok('CHK-9' in h and 'Подтвердить' in h and 'Не получено' in h,'restaurant: the courier’s payment for the order, to confirm or mark «not received»')
    E("()=>{mhDecide(9,true,'o:ord1')}");pg.wait_for_timeout(150)
    ok(E("()=>__a.decideStorePayment[0]")==[9,True,''],'restaurant: confirmation sent through the server function')
    E("()=>{tab='s';per='dY';render()}");pg.wait_for_timeout(500)
    st=pg.inner_text('#setlcard') if pg.locator('#setlcard').count() else ''
    ok('Остаток к получению' in st and '20' in st and 'Ждут вашего подтверждения: 100' in st,'restaurant: settlement with the platform (owed, received from couriers / platform, left)')
    ok(not errs,'restaurant: no JS errors %s'%errs[:1]);pg.close()
    b.close()
print('\nP38 UI %d/%d'%(n-len(fails),n));sys.exit(1 if fails else 0)
