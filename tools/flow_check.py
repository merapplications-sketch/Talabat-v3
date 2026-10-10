"""End-to-end order flow, the way real people use the 4 apps (v44).

One shared in-memory "database" (Python) serves the customer, merchant, driver and admin pages at the same
time, so an action in one app is seen by the others after a refresh. Each step is done by CLICKING the real
button (found by its text), then every app's screen is checked with the qa_all visual rules and screenshotted.

  customer orders -> restaurant sets 15 min + accepts -> courier starts shift, gets the offer, accepts
  -> restaurant marks ready -> courier picks up -> courier delivers (cash) -> customer rates -> admin sees it
  + side paths: customer cancels a pending order, restaurant rejects one, a 2nd courier offer is not shown
    to a busy courier.

The RPC rules mirror the SQL (set_order_status in patch 26, driver_accept in patch 18, place_order in 22).
Limits: this is not the real Supabase (no RLS / triggers / realtime); it checks the apps' flow and screens."""
import os,json,sys,re,copy,datetime
from playwright.sync_api import sync_playwright
here=os.path.dirname(os.path.abspath(__file__));root=os.path.abspath(os.path.join(here,'..'))
SRC=open(os.path.join(here,'qa_all.py')).read()
FIX=SRC.split('FIX="""')[1].split('"""')[0]
CHECK=SRC.split('CHECK="""')[1].split('"""')[0]
OUT=os.environ.get('FLOW_OUT','/tmp/flow');os.makedirs(OUT,exist_ok=True)
W=int(os.environ.get('FLOW_W','390'))
U={'customer':'c0000000-0000-4000-8000-000000000001','merchant':'c0000000-0000-4000-8000-000000000002',
   'driver':'c0000000-0000-4000-8000-000000000003','admin':'c0000000-0000-4000-8000-000000000004',
   'driver2':'c0000000-0000-4000-8000-000000000005'}
uu=lambda n:'00000000-0000-4000-8000-%012d'%n
def now(): return datetime.datetime.now(datetime.timezone.utc).isoformat()
fails=[];log=[]
def swipe(pg):
    k=pg.locator('#swk');k.wait_for(timeout=3000);b=k.bounding_box();w=pg.locator('#swp').bounding_box()
    pg.mouse.move(b['x']+b['width']/2,b['y']+b['height']/2);pg.mouse.down()
    for i in range(1,11): pg.mouse.move(b['x']+b['width']/2+(w['width']-b['width'])*i/10,b['y']+b['height']/2)
    pg.mouse.up();pg.wait_for_timeout(700)
def ok(c,m):
    print(('PASS ' if c else 'FAIL ')+m,flush=True)
    if not c: fails.append(m)

# ---------- shared database ----------
def base_tables(page):
    page.goto('about:blank')
    page.evaluate("window.__ROLE='customer'")
    page.evaluate(FIX.replace('var T={','var T=window.__T={',1))
    T=page.evaluate("JSON.parse(JSON.stringify(window.__T))")
    ids={};n=[0]
    def m(x):
        if x not in ids: n[0]+=1;ids[x]=uu(n[0])
        return ids[x]
    for it in T['menu_items']: it['id']=m(it['id'])
    for g in T['item_option_groups']: g['id']=m(g['id']);g['item_id']=m(g['item_id'])
    for o in T['item_options']: o['id']=m(o['id']);o['group_id']=m(o['group_id'])
    for s in T['stores']: s['owner_id']=U['merchant']
    T['stores']=[s for s in T['stores'] if s['id'] in ('s1','s3')]
    T['menu_items']=[i for i in T['menu_items'] if i['store_id'] in ('s1','s3')]
    for k in ('orders','order_items','ratings','order_chat','support_tickets','ticket_messages','order_offers','wallet_entries','favorites','store_requests','audit_log','banners','brands'):
        T[k]=[]
    for s in T['stores']: s['brand_id']=None
    T['addresses']=[dict(a,user_id=U['customer']) for a in T['addresses']]
    T['profiles']=[
     {'id':U['customer'],'email':'customer@test.com','role':'customer','name':'Зарина','phone':'+992900000001','created_at':now()},
     {'id':U['merchant'],'email':'merchant@test.com','role':'merchant','name':'Ресторан','phone':'+992900000002','created_at':now()},
     {'id':U['driver'],'email':'driver@test.com','role':'driver','name':'Фаррух','phone':'+992900000003','driver_status':'approved','cash_limit':1000,'created_at':now()},
     {'id':U['admin'],'email':'admin@test.com','role':'admin','name':'Admin','phone':'+992900000004','created_at':now()},
     {'id':U['driver2'],'email':'driver2@test.com','role':'driver','name':'Бахтиёр','phone':'+992900000005','driver_status':'approved','cash_limit':1000,'created_at':now()}]
    return T
class DB:
    def __init__(s,T): s.T=T;s.seq=1000;s.calls=[];s.online=set()
    def rows(s,name,f):
        r=s.T.get(name,[])
        for op,col,v in f:
            if op=='eq': r=[x for x in r if str(x.get(col))==str(v)]
            elif op=='neq': r=[x for x in r if str(x.get(col))!=str(v)]
            elif op=='in': r=[x for x in r if x.get(col) in v or str(x.get(col)) in [str(y) for y in v]]
            elif op=='is': r=[x for x in r if x.get(col) is None]
        return r
    def handle(s,q):
        role,uid,kind,name=q['role'],q['uid'],q['kind'],q['name']
        if kind=='rpc':
            s.calls.append((role,name,q.get('args')))
            fn=getattr(s,'rpc_'+name,None)
            try: return fn(uid,q.get('args') or {}) if fn else s.default(name,uid)
            except Exception as e: return {'__err':str(e)}
        r=s.rows(name,q['f'])
        if q['op']=='select': return (copy.deepcopy(r[0]) if r else None) if q['single'] else copy.deepcopy(r)
        if q['op']=='update':
            for x in r: x.update(q['payload'] or {})
            return copy.deepcopy(r)
        if q['op'] in ('insert','upsert'):
            p=q['payload'];p=p if isinstance(p,list) else [p]
            for x in p: s.seq+=1;x=dict(x);x.setdefault('id',s.seq);x.setdefault('created_at',now());s.T.setdefault(name,[]).append(x)
            return p
        if q['op']=='delete':
            s.T[name]=[x for x in s.T.get(name,[]) if x not in r];return []
        return None
    def default(s,name,uid):
        D={'my_perms':None,'wallet_balance':0,'cash_balances':[],'my_rating':None,'brand_stats':[],'brand_route':[],'staff_list':[],'admin_customers':[],
           'store_private':[{'id':x['id'],'owner_id':U['merchant'],'commission_pct':10,'max_discount_pct':30} for x in s.T['stores']],
           'delivery_quote':{'fee':10,'fee_full':10,'base':10,'extra':0,'km':2.1,'steps':0,'free_km':3,'first_free':False},'check_promo':None,
           'driver_ping':None,'dispatch_tick':None,'report_client_error':None}
        return D.get(name)
    def order(s,i): return next((o for o in s.T['orders'] if str(o['id'])==str(i)),None)
    def prof(s,uid): return next(p for p in s.T['profiles'] if p['id']==uid)
    def rpc_place_order(s,uid,a):
        st=next((x for x in s.T['stores'] if x['id']==a['p_store'] and x['is_active']),None)
        if not st: raise Exception('store_unavailable')
        if not st['is_open']: raise Exception('closed')
        if a.get('p_key'):
            o=next((o for o in s.T['orders'] if o['customer_id']==uid and o.get('client_key')==a['p_key']),None)
            if o: return o['id']
        if a.get('p_lat') is None or len((a.get('p_address') or '').strip())<3: raise Exception('address_required')
        sub=0;items=[]
        for l in a['p_items']:
            it=next((i for i in s.T['menu_items'] if i['id']==l['item_id'] and i['store_id']==st['id'] and i['available'] and i['approved']),None)
            if not it: raise Exception('unavailable')
            sub+=it['price']*l['qty'];items.append((it,l))
        s.seq+=1;oid=s.seq;disc=round(sub*(st.get('discount_pct') or 0)/100,2);fee=10;tip=a.get('p_tip') or 0
        total=max(5,sub-disc+fee+tip)
        s.T['orders'].append({'id':oid,'store_id':st['id'],'customer_id':uid,'driver_id':None,'driver_name':None,'status':'pending','subtotal':sub,'discount':disc,'promo_discount':0,
          'delivery_fee':fee,'driver_payout':15,'tip':tip,'total':total,'commission':round(sub*0.1,2),'commission_pct':10,'payment':a.get('p_payment') or 'cash','address':a['p_address'],
          'lat':a['p_lat'],'lng':a['p_lng'],'customer_name':s.prof(uid)['name'],'created_at':now(),'done_at':None,'wallet_used':0,'client_key':a.get('p_key'),'prep_time':None})
        for it,l in items:
            s.seq+=1;s.T['order_items'].append({'id':s.seq,'order_id':oid,'item_id':it['id'],'name':it['name'],'price':it['price'],'qty':l['qty'],'note':l.get('note') or '','options':[]})
        return oid
    def rpc_set_order_status(s,uid,a):
        o=s.order(a['p_id']);to=a['p_to']
        if not o: raise Exception('not_found')
        role=s.prof(uid)['role'];st=o['status'];okk=False
        if role=='admin': okk=True
        elif o['customer_id']==uid: okk=(st=='pending' and to=='cancelled')
        elif role=='merchant': okk=(st=='pending' and to in ('preparing','rejected')) or (st=='preparing' and to=='ready')
        elif o['driver_id']==uid: okk=(st=='ready' and to=='pickedup')
        if not okk: raise Exception('bad_transition')
        o['status']=to;o['done_at']=now() if to in ('delivered','rejected','cancelled') else None
        return None
    def rpc_set_prep_time(s,uid,a):
        o=s.order(a['p_id']);o['prep_time']=min(90,max(5,a['p_min']));return None
    def rpc_driver_ping(s,uid,a):
        (s.online.add if a.get('p_online') else s.online.discard)(uid);return None
    def rpc_my_offers(s,uid,a):
        if uid not in s.online: return []
        if any(o['driver_id']==uid and o['status'] in ('preparing','ready','pickedup') for o in s.T['orders']): return []
        return [{'order_id':o['id'],'mode':'broadcast','rank':1,'dist_km':1.8,'secs_left':30} for o in s.T['orders'] if o['status'] in ('preparing','ready') and not o['driver_id']]
    def rpc_driver_accept(s,uid,a):
        if any(o['driver_id']==uid and o['status'] in ('preparing','ready','pickedup') for o in s.T['orders']): raise Exception('busy')
        o=s.order(a['p_id'])
        if not o or o['driver_id'] or o['status'] not in ('preparing','ready'): return False
        o['driver_id']=uid;o['driver_name']=s.prof(uid)['name'];return True
    def rpc_driver_decline(s,uid,a): return None
    def rpc_deliver_order(s,uid,a):
        o=s.order(a['p_id'])
        if not o or o['driver_id']!=uid or o['status']!='pickedup': raise Exception('bad_transition')
        if o.get('leave_at_door') and not a.get('p_photo'): raise Exception('photo_required')
        o['status']='delivered';o['done_at']=now();o['cash_collected']=a.get('p_cash');o['delivery_photo']=a.get('p_photo');return None
    def rpc_driver_arrived(s,uid,a):        # patch 34
        o=s.order(a['p_id'])
        if not o or o['driver_id']!=uid: raise Exception('not_allowed')
        if a['p_where']=='store' and o['status'] in ('preparing','ready'): o['arrived_store_at']=o.get('arrived_store_at') or now()
        elif a['p_where']=='customer' and o['status']=='pickedup': o['arrived_cust_at']=o.get('arrived_cust_at') or now()
        else: raise Exception('bad_transition')
        return None
    def rpc_reject_order(s,uid,a):          # patch 34
        o=s.order(a['p_id'])
        if not o or o['status'] not in ('pending','preparing'): raise Exception('bad_transition')
        if a['p_reason'] not in ('out_of_stock','too_busy','closing','other'): raise Exception('bad_value')
        o['status']='rejected';o['done_at']=now();o['cancel_reason']=a['p_reason'];o['cancel_note']=a.get('p_note');o['cancelled_by']='store';return None
    def rpc_active_contacts(s,uid,a):
        out=[]
        for o in s.T['orders']:
            if o['status'] not in ('pending','preparing','ready','pickedup'): continue
            if uid in (o['customer_id'],o['driver_id']) or s.prof(uid)['role']=='merchant':
                out.append({'order_id':o['id'],'customer_phone':s.prof(o['customer_id'])['phone'] if uid!=o['customer_id'] else '',
                            'driver_phone':s.prof(o['driver_id'])['phone'] if o['driver_id'] and uid!=o['driver_id'] else ''})
        return out
    def rpc_contacts_for(s,uid,a):
        return [{'order_id':o['id'],'customer_phone':s.prof(o['customer_id'])['phone'],'driver_phone':s.prof(o['driver_id'])['phone'] if o['driver_id'] else ''} for o in s.T['orders'] if o['id'] in a['p_ids']]
    def rpc_rate_order(s,uid,a):
        s.seq+=1;s.T['ratings'].append({'id':s.seq,'order_id':a['p_order'],'customer_id':uid,'store_stars':a.get('p_store'),'driver_stars':a.get('p_driver'),'comment':a.get('p_comment'),'created_at':now()});return None

MOCK="""(function(){var role=window.__ROLE,uid=window.__UID,user={id:uid,email:role+'@test.com'};
 function chain(kind,name,args){var f=[],single=false,op='select',payload=null;
  var c=new Proxy(function(){},{get:function(t,p){
   if(p==='then')return function(ok,bad){return window.__db({kind:kind,name:name,args:args||null,f:f,single:single,op:op,payload:payload,role:role,uid:uid}).then(function(d){return d&&d.__err?{data:null,error:{message:d.__err}}:{data:d,error:null}}).then(ok,bad)};
   if(p==='single'||p==='maybeSingle')return function(){single=true;return c};
   if(p==='eq'||p==='in'||p==='neq'||p==='is')return function(col,v){f.push([p,col,v]);return c};
   if(p==='insert'||p==='update'||p==='upsert'||p==='delete')return function(x){op=p;payload=x===undefined?null:x;return c};
   return function(){return c}}});return c}
 window.supabase={createClient:function(){return {auth:{getSession:function(){return Promise.resolve({data:{session:{user:user,access_token:'x'}},error:null})},signOut:function(){return Promise.resolve({})},signInWithPassword:function(){return Promise.resolve({error:{message:'x'}})},onAuthStateChange:function(){return {data:{subscription:{unsubscribe:function(){}}}}}},
  from:function(n){return chain('from',n)},rpc:function(n,a){return chain('rpc',n,a)},channel:function(){var ch={on:function(){return ch},subscribe:function(){return ch},unsubscribe:function(){}};return ch},removeChannel:function(){},
  storage:{from:function(){return {upload:function(){return Promise.resolve({})},getPublicUrl:function(){return {data:{publicUrl:''}}}}}}}}};})();"""

shots=[]
with sync_playwright() as p:
    b=p.chromium.launch();tmp=b.new_page();db=DB(base_tables(tmp));tmp.close()
    P={};ERR={};DLG=[]
    def open_app(role,app=None):
        app=app or role;ctx=b.new_context(viewport={'width':W,'height':844});pg=ctx.new_page();ERR[role]=[]
        ctx.expose_function('__db',db.handle)
        pg.add_init_script("window.__ROLE=%s;window.__UID=%s"%(json.dumps('driver' if role=='driver2' else role),json.dumps(U[role])))
        pg.on('pageerror',lambda e,r=role:ERR[r].append(str(e)))
        pg.on('dialog',lambda d:(DLG.append(d.message),d.accept()))
        pg.route('**/*',lambda rt,rq:(rt.fulfill(status=200,content_type='application/javascript',body=MOCK) if 'supabase-js' in rq.url else (rt.abort() if rq.url.startswith('http') else rt.continue_())))
        pg.goto('file://'+root+'/'+app+'.html',wait_until='domcontentloaded');pg.wait_for_timeout(1800);P[role]=pg;return pg
    for r in ('customer','merchant','driver','admin'): open_app(r)
    def sync(*roles):
        for r in roles or P.keys(): P[r].evaluate("()=>TLB.reload&&TLB.reload()");P[r].wait_for_timeout(350);P[r].evaluate("()=>{try{render()}catch(e){}}")
    def look(role,label):
        pg=P[role];pg.wait_for_timeout(200);iss=pg.evaluate(CHECK,'top');pg.evaluate("window.scrollTo(0,document.body.scrollHeight)");pg.wait_for_timeout(100)
        iss=iss+pg.evaluate(CHECK,'end');pg.evaluate("window.scrollTo(0,0)")
        f='%s/%02d_%s_%s.png'%(OUT,len(shots),role,label);pg.screenshot(path=f,full_page=True);shots.append(f)
        ok(not iss,'%s · %s: screen clean %s'%(role,label,'' if not iss else sorted(set(iss))[:4]))
    def click(role,text,sel='button'):
        pg=P[role];loc=(pg.locator(text) if text.startswith('[') else pg.locator(sel,has_text=re.compile(text))).first
        if not loc.count(): ok(False,'%s: button «%s» not found'%(role,text));return False
        loc.scroll_into_view_if_needed();loc.click();pg.wait_for_timeout(500);return True
    status=lambda i:(db.order(i) or {}).get('status')

    # 1) customer orders
    c=P['customer'];c.evaluate("()=>TLB.setLang('ru')");
    for r in ('merchant','driver','admin'): P[r].evaluate("()=>TLB.setLang('ru')")
    item=c.evaluate("()=>{const s=ALLS.find(x=>x.id=='s1');openN(s.n);const it=menuOf(s.n).find(i=>!i.hasOpts&&i.available);addFrom(it.id);addFrom(it.id);return it.name}")
    look('customer','1-menu-added')
    ok(c.evaluate("()=>!document.querySelector('.mt,.tabs .tb,.hb')&&document.querySelectorAll('.msec').length>1"),'restaurant page: one vertical scroll with section titles, no top/side tabs')
    ok(c.evaluate("()=>{const e=document.getElementById('tlb-lang');return !e||getComputedStyle(e).display=='none'}"),'customer: no floating language pill (language is in Settings)')
    ok(c.evaluate("()=>cartCount()")==2,'customer: 2 dishes in the cart from the restaurant page')
    c.locator('.bar').first.click();c.wait_for_timeout(300);look('customer','2-cart')
    click('customer','Перейти к оплате');c.wait_for_timeout(400)
    c.evaluate("()=>{S.useWallet=false;S.pay='cash';render()}");look('customer','3-pay')
    click('customer','Оформить заказ');c.wait_for_timeout(800)
    oid=max([o['id'] for o in db.T['orders']] or [0])
    ok(oid and status(oid)=='pending','order created (#%s, pending)'%oid)
    ok(c.evaluate("()=>S.v")=='track','customer lands on the tracking page')
    look('customer','4-track-pending')
    # 2) restaurant accepts with a time
    sync('merchant');m=P['merchant']
    ok(m.evaluate("(i)=>TLB.orders().some(o=>o.id==i&&o.status=='pending')",oid),'restaurant sees the new order')
    look('merchant','5-new-order')
    ok(m.evaluate("()=>!!document.querySelector('.nav')&&!document.querySelector('.tabs')"),'restaurant: bottom navigation like the other apps')
    ok(m.evaluate("()=>{const e=document.getElementById('tlb-out');return !e||getComputedStyle(e).display=='none'}"),'restaurant: sign out moved into Profile (no floating pill)')
    ok(not re.search(r'\d min\b',m.evaluate("()=>document.body.innerText")),'restaurant: minutes translated (мин)')
    click('merchant','^\\s*15')
    ok(db.order(oid).get('prep_time')==15,'restaurant set 15 min')
    click('merchant','Принять');ok(status(oid)=='preparing','restaurant accepted → preparing')
    sync('customer');look('customer','6-track-preparing')
    ok(not c.evaluate("()=>!!document.querySelector('.placed')"),'customer: the "order placed" banner disappears once the restaurant accepted')
    # 3) courier: shift, offer, accept
    d=P['driver'];sync('driver');click('driver','Начать смену|Выйти на смену|смену');sync('driver');d.wait_for_timeout(500);sync('driver')
    look('driver','7-offer')
    ok(d.evaluate("(i)=>!!document.body.innerText.match(/#"+str(oid)+"/)",oid) or d.evaluate("()=>document.querySelectorAll('[onclick^=\"take(\"]').length>0"),'courier sees the offer')
    d.locator('[onclick^="take("]').first.click();d.wait_for_timeout(500);sync('driver')
    ok(db.order(oid)['driver_id']==U['driver'],'courier accepted the order')
    look('driver','8-active-pickup')
    ok(d.evaluate("()=>document.body.classList.contains('mapmode')&&!!document.querySelector('.sht')"),'courier: full-screen map + bottom sheet')
    swipe(d);ok(db.order(oid).get('arrived_store_at'),'courier: swipe 1 "На месте в ресторане"')
    sync('driver');ok(d.evaluate("()=>!!document.querySelector('.swp.off')"),'swipe 2 is locked until the restaurant presses ready')
    sync('merchant');ok(m.evaluate("()=>document.body.innerText.includes('Курьер в ресторане')"),'restaurant sees the courier is there')
    # 2nd courier must not get it any more
    d2=open_app('driver2','driver');sync('driver2');d2.locator('button',has_text=re.compile('смену')).first.click() if d2.locator('button',has_text=re.compile('смену')).count() else None;sync('driver2')
    ok(d2.evaluate("()=>document.querySelectorAll('[onclick^=\"take(\"]').length")==0,'a 2nd courier does not see a taken order')
    sync('merchant');look('merchant','9-preparing-courier')
    ok(m.evaluate("(i)=>document.body.innerText.includes('Фаррух')",oid),'restaurant sees the courier name')
    click('merchant','[onclick="st(%s,\'ready\')"]'%oid);ok(status(oid)=='ready','restaurant: ready for pickup')
    sync('driver');look('driver','10-ready')
    swipe(d);ok(status(oid)=='pickedup','courier: swipe 2 "Заказ забран" (allowed only after ready)')
    sync('customer');look('customer','11-track-onway')
    sync('driver');swipe(d);ok(db.order(oid).get('arrived_cust_at'),'courier: swipe 3 "На месте у клиента"')
    ok(any('на месте' in (m.get('body') or '').lower() for m in db.T.get('order_chat',[])),'the customer gets "I am here" in the chat')
    sync('customer');ok(c.evaluate("()=>document.body.innerText.includes('Курьер на месте')"),'customer sees "the courier is here"')
    sync('driver');look('driver','12-deliver')
    swipe(d);d.wait_for_timeout(300);look('driver','13-cash-dialog')
    if d.locator('[onclick="confirmDeliver()"]').count(): d.locator('[onclick="confirmDeliver()"]').first.click();d.wait_for_timeout(600)
    ok(status(oid)=='delivered','courier: delivered (cash %s TJS)'%db.order(oid).get('cash_collected'))
    sync('driver');look('driver','14-after-delivery')
    sync('customer');look('customer','15-track-delivered')
    # 4) customer rates
    for k in ('s','d'):
        loc=c.locator('[onclick^="setStar(%s,\'%s\',5)"]'%(oid,k))
        ok(loc.count()==1,'customer: 5-star button for %s'%('restaurant' if k=='s' else 'courier'))
        if loc.count(): loc.first.click();c.wait_for_timeout(250)
    click('customer','[onclick="sendRate(%s)"]'%oid)
    ok(len(db.T['ratings'])==1,'customer rated the order (%s)'%(db.T['ratings'][:1] and {k:db.T['ratings'][0][k] for k in ('store_stars','driver_stars')}))
    look('customer','16-rated')
    # 5) admin
    sync('admin');a=P['admin'];look('admin','17-orders')
    ok(a.evaluate("(i)=>TLB.orders().some(o=>o.id==i)",oid),'admin sees the order')
    a.evaluate("(i)=>{D=i;render()}",oid);a.wait_for_timeout(400);look('admin','18-order-detail')
    # 6) side paths
    c.evaluate("()=>{const s=ALLS.find(x=>x.id=='s1');S.cart={};openN(s.n);const it=menuOf(s.n).find(i=>!i.hasOpts&&i.available);addFrom(it.id);goCart()}")
    click('customer','Перейти к оплате');c.evaluate("()=>{S.pay='cash';render()}");click('customer','Оформить заказ')
    o2=max(o['id'] for o in db.T['orders']);ok(status(o2)=='pending','2nd order placed')
    c.evaluate("()=>{window.confirm=()=>true}");click('customer','Отменить заказ');ok(status(o2)=='cancelled','customer cancelled a pending order')
    sync('customer');look('customer','19-cancelled')
    c.evaluate("()=>{const s=ALLS.find(x=>x.id=='s1');S.cart={};openN(s.n);const it=menuOf(s.n).find(i=>!i.hasOpts&&i.available);addFrom(it.id);goCart()}")
    click('customer','Перейти к оплате');c.evaluate("()=>{S.pay='cash';render()}");click('customer','Оформить заказ')
    o3=max(o['id'] for o in db.T['orders']);sync('merchant')
    c.evaluate("()=>go('home')")
    click('merchant','[onclick="rjOpen(%s)"]'%o3);look('merchant','20a-reject-reasons')
    click('merchant','Нет блюда в наличии');m.locator('#rjn').fill('закончился плов');click('merchant','[onclick="rjSend()"]')
    ok(status(o3)=='rejected' and db.order(o3).get('cancel_reason')=='out_of_stock','restaurant cancelled with the reason "out of stock"')
    sync('customer');ok(c.evaluate("()=>S.cxn!=null&&document.body.innerText.includes('отменён')"),'customer gets an instant notice on the home page')
    look('customer','20b-cancel-notice')
    c.evaluate("(i)=>{S.cxn=null;go('track',{tid:i})}",o3);look('customer','20-rejected')
    ok(c.evaluate("()=>document.body.innerText.includes('простите')&&document.body.innerText.includes('закончился плов')"),'customer sees the reason with an apology')
    sync('merchant');look('merchant','21-after')
    for r,e in ERR.items(): ok(not e,'%s: no JS errors %s'%(r,e[:2]))
    print('calls:',', '.join(sorted(set('%s:%s'%(r,n) for r,n,_ in db.calls if n not in ('wallet_balance','store_private','my_perms','cash_balances','active_contacts','report_client_error','driver_ping','dispatch_tick','my_rating')))))
    b.close()
print('SCREENS',len(shots),'->',OUT)
print('FLOW FAILS',len(fails));sys.exit(1 if fails else 0)
