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
    # ---------- admin: refund cap breakdown; the order card does not call an order «not handed over» from an empty old mark ----------
    pg,errs,dl=page(b,AD,'admin');E=pg.evaluate
    h=E("()=>{TK.sel='x';TK.room={id:'x',total:275,refunded:0,room:0,paidWallet:0,paidCash:0,unproven:150.62};return refundBox({id:'x',order_id:'ord5'})}")
    ok('Максимум к возврату: 0 TJS' in h and 'без подтверждённой оплаты 150.62' in h,'admin: refund box shows the maximum 0 with its breakdown (confirmed wallet + cash, unconfirmed 150.62)')
    h=E("()=>finBox(Object.assign({},TLB.order('ord4'),{status:'delivered',payment:'cash',walletUsed:0,cashCollected:150,cashNote:'',cashSettled:false}))")
    ok('Не отмечено старой кнопкой' in h and 'Ещё не сдано' not in h,'admin: a delivered cash order without the old mark is not called «not handed over»')
    h=E("()=>finBox(Object.assign({},TLB.order('ord4'),{status:'delivered',payment:'cash',walletUsed:0,cashCollected:200,cashNote:'',cashSettled:true}))")
    ok('Сдано в кассу' in h,'admin: an order marked by the old «receive cash» keeps its mark')
    ok(not errs,'admin: no JS errors %s'%errs[:1]);pg.close()
    # ---------- courier: photo not found on the server ----------
    pg,errs,dl=page(b,DR,'driver');E=pg.evaluate
    E("()=>{DV={id:'ord3',photo:true,ph:{path:'x/ord3/abcdefgh12.jpg'},cash:false,amt:'',note:''};TLB.deliver=()=>Promise.resolve({error:'photo_missing'})}")
    r=E("async()=>await finish('ord3',null,null,'x/ord3/abcdefgh12.jpg')")
    ok(r is False and E("()=>DV&&DV.ph")==None and any('не найдено' in m for m in dl),'courier: photo_missing → message, the photo must be taken / uploaded again')
    ok(not errs,'courier: no JS errors %s'%errs[:1]);pg.close()
    b.close()
print('\nP37 UI %d/%d'%(n-len(fails),n));sys.exit(1 if fails else 0)
