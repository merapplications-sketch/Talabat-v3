"""Patch 37 package — screens (read-only previews; the new server calls are replaced by controllable stand-ins).
Chromium only. Server behaviour is tested in sql/test_patch37.sql and tools/patch37_race.py.
  python3 tools/patch37_ui_check.py <customer_dir> <admin_dir> <driver_dir>"""
import sys
from playwright.sync_api import sync_playwright
CU,AD,DR=sys.argv[1:4];fails=[];n=0
def ok(c,m):
    global n;n+=1;print(('PASS ' if c else 'FAIL ')+m)
    if not c: fails.append(m)
def page(b,d,app,w=390):
    pg=b.new_page(viewport={'width':w,'height':844},is_mobile=True,has_touch=True);errs=[];pg.on('pageerror',lambda e:errs.append(str(e)))
    pg.route('**/*',lambda rt,rq:(rt.abort() if rq.url.startswith('http') else rt.continue_()))
    dl=[];pg.on('dialog',lambda dg:(dl.append(dg.message),dg.accept()))
    pg.goto('file://'+d+'/'+app+'.html');pg.wait_for_timeout(2500);pg.evaluate("()=>TLB.setLang('ru')");pg.wait_for_timeout(300);return pg,errs,dl
with sync_playwright() as p:
    b=p.chromium.launch()
    # ---------- customer: support refunds read per order ----------
    pg,errs,dl=page(b,CU,'customer');E=pg.evaluate
    E("()=>{const o=window.__pvTables.orders.find(o=>o.id=='ord5');Object.assign(o,{status:'cancelled',payment:'cash',total:275,wallet_used:124.38,wallet_returned_at:new Date().toISOString(),points_used:0,cash_collected:null})}")
    E("()=>TLB.reload()");pg.wait_for_timeout(900)
    E("()=>{window.__ow=[];TLB.orderWallet=id=>{window.__ow.push(id);return Promise.resolve([{id:1,amount:-124.38,kind:'spend',orderId:id,ticketId:null,at:1},{id:2,amount:124.38,kind:'return',orderId:id,ticketId:null,at:2},{id:900,amount:15,kind:'refund',orderId:id,ticketId:'t42',at:3}])};go('track',{tid:'ord5'})}");pg.wait_for_timeout(500)
    st=pg.inner_text('#stl') if pg.locator('#stl').count() else ''
    ok(E("()=>__ow")==['ord5'] and 'Возврат по обращению #t42' in st and '+15 TJS' in st,'customer: the refund of THIS order is read from the server (one read) and shown')
    ok(pg.locator('#stlcov').count()==0 and 'последних 60' not in st,'customer: no «latest 60 operations» limit any more')
    E("()=>render()");pg.wait_for_timeout(200);ok(E("()=>__ow.length")==1,'customer: a redraw does not read again')
    E("()=>{TLB.orderWallet=()=>Promise.resolve(null);S.owl=null;go('orders');go('track',{tid:'ord5'})}");pg.wait_for_timeout(500)
    ok('не проверены' in (pg.inner_text('#stlcov') if pg.locator('#stlcov').count() else ''),'customer: a failed read → «support refunds not checked here»')
    ok(not errs,'customer: no JS errors %s'%errs[:1]);pg.close()
    # ---------- admin: receive any positive amount, history, refund cap breakdown ----------
    pg,errs,dl=page(b,AD,'admin');E=pg.evaluate
    did=E("()=>{const d=TLB.drivers()[0];return d&&d.id}")
    E("""()=>{TLB.cash=()=>410;window.__rc=[];window.__q=[];TLB.receiveCash=function(){__rc.push([...arguments]);return new Promise(r=>__q.push(r))};
      TLB.cashReceipts=()=>Promise.resolve([{id:1,amount:25.5,dueBefore:410,remaining:384.5,by:null,at:Date.now(),reference:'REC-1',note:''}])}""")
    E("(id)=>{tab='d';openDrvEdit(id)}",did);pg.wait_for_timeout(500)
    ok(pg.locator('#cscard').count()==1 and pg.input_value('#csa')=='410.00','admin: courier card has an amount field (default = all owed 410)')
    ok('REC-1' in pg.inner_text('#cscard') and '384.50' in pg.inner_text('#cscard'),'admin: received amounts listed with reference and what is left')
    pg.fill('#csa','25.5');pg.fill('#csr','REC-2');pg.click('#csgo');pg.wait_for_timeout(150);pg.locator('#csgo').click(force=True);pg.wait_for_timeout(150)
    ok(E("()=>__rc.length")==1 and E("()=>__rc[0][1]")==25.5 and E("()=>__rc[0][2]")=='REC-2' and len(E("()=>__rc[0][4]"))>=8,'admin: 25.5 TJS (below any limit) sent ONCE with reference and a form key, double tap ignored')
    k1=E("()=>__rc[0][4]");E("()=>__q.shift()({error:'amount_too_high'})");pg.wait_for_timeout(300)
    ok(any('больше долга' in m for m in dl),'admin: «more than owed» explained')
    pg.click('#csgo');pg.wait_for_timeout(150);ok(E("()=>__rc[1][4]")==k1,'admin: a retry of the same form keeps its key (no double receipt)')
    E("()=>__q.shift()({ok:true,amount:25.5,remaining:384.5})");pg.wait_for_timeout(300);pg.click('#csgo') if not pg.locator('#csgo').is_disabled() else None;pg.wait_for_timeout(150)
    ok(E("()=>__rc.length")==3 and E("()=>__rc[2][4]")!=k1,'admin: after a success a NEW form gets a new key')
    h=E("()=>{TK.sel='x';TK.room={id:'x',total:275,refunded:0,room:0,paidWallet:0,paidCash:0,unproven:150.62};return refundBox({id:'x',order_id:'ord5'})}")
    ok('Максимум к возврату: 0 TJS' in h and 'без подтверждённой оплаты 150.62' in h,'admin: refund box shows the maximum 0 with its breakdown (confirmed wallet + cash, unconfirmed 150.62)')
    h=E("()=>finBox(Object.assign({},TLB.order('ord4'),{status:'delivered',payment:'cash',walletUsed:0,cashCollected:150,cashNote:'',cashSettled:false}))")
    ok('В долге курьера' in h and 'Ещё не сдано' not in h,'admin (model A): a delivered cash order is shown «in the courier balance», never «not handed over» just because the old mark is empty')
    h=E("()=>finBox(Object.assign({},TLB.order('ord4'),{status:'delivered',payment:'cash',walletUsed:0,cashCollected:200,cashNote:'',cashSettled:true}))")
    ok('до учёта по балансу' in h,'admin (model A): an order marked by the OLD full settlement keeps its mark, labelled as such')
    ok(not errs,'admin: no JS errors %s'%errs[:1]);pg.close()
    # ---------- courier: photo not found on the server ----------
    pg,errs,dl=page(b,DR,'driver');E=pg.evaluate
    E("()=>{DV={id:'ord3',photo:true,ph:{path:'x/ord3/abcdefgh12.jpg'},cash:false,amt:'',note:''};TLB.deliver=()=>Promise.resolve({error:'photo_missing'})}")
    r=E("async()=>await finish('ord3',null,null,'x/ord3/abcdefgh12.jpg')")
    ok(r is False and E("()=>DV&&DV.ph")==None and any('не найдено' in m for m in dl),'courier: photo_missing → message, the photo must be taken / uploaded again')
    ok(not errs,'courier: no JS errors %s'%errs[:1]);pg.close()
    b.close()
print('\nP37 UI %d/%d'%(n-len(fails),n));sys.exit(1 if fails else 0)
