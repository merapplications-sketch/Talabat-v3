"""Loopback-only synthetic payment journey. Never use with hosted databases."""
import sys, pathlib, json, uuid, secrets, threading, hashlib, hmac, importlib.util
from http.server import ThreadingHTTPServer, BaseHTTPRequestHandler
sys.path.insert(0, str(pathlib.Path(__file__).resolve().parents[1]))
import lab
ROOT=pathlib.Path(__file__).parent
LOCK=threading.RLock()
KEY=secrets.token_bytes(32)
ROLES={'customer':'customer','merchant':'merchant','driver':'driver1','admin':'admin'}
SESSIONS={secrets.token_urlsafe(24):r for r in ROLES}

def setup():
    spec=importlib.util.spec_from_file_location('returns',lab.HERE/'driver-returns.py');m=importlib.util.module_from_spec(spec);spec.loader.exec_module(m);m.setup()
    with lab.db() as c:
        c.execute('create schema electronic_test; revoke all on schema electronic_test from public; create table electronic_test.intents(id uuid primary key, customer uuid not null, request_key uuid unique not null, amount numeric not null, currency text not null, state text not null, event text unique, order_id bigint unique references public.orders(id));')
        definition=lab.q(c,"select pg_get_functiondef('public.place_order(uuid,jsonb,numeric,text,text,double precision,double precision,text,text,numeric,numeric,integer,jsonb)'::regprocedure)")
        old="if p_payment is distinct from 'cash' then raise exception 'payment_not_configured'; end if;"
        assert definition.count(old)==1
        new="""if p_payment is distinct from 'cash' and not (p_payment='card' and session_user='postgres' and exists(select 1 from electronic_test.intents where id::text=current_setting('electronic_test.intent',true) and customer=auth.uid() and state='succeeded' and order_id is null)) then raise exception 'payment_not_configured'; end if;"""
        c.execute(definition.replace(old,new),prepare=False)

def intent(key):
    key=str(uuid.UUID(key))
    with lab.db() as c:
        old=c.execute('select id,amount,currency,state,order_id from electronic_test.intents where request_key=%s',(key,)).fetchone()
        if old:return dict(zip(['id','amount','currency','state','order_id'],old))
        quote=lab.rpc(lab.bearer('customer'),'delivery_quote',dict(p_store=lab.STORE,p_lat=lab.LAT,p_lng=lab.LNG))
        price=lab.q(c,'select price from menu_items where id=%s',(lab.ITEM,))
        amount=price+type(price)(str(quote['fee']))
        iid=str(uuid.uuid4());c.execute("insert into electronic_test.intents values(%s,%s,%s,%s,'TJS','pending',null,null)",(iid,lab.uid('customer'),key,amount))
        return {'id':iid,'amount':amount,'currency':'TJS','state':'pending','order_id':None}

def event(iid,outcome):
    # Synthetic provider constructs and signs its own authoritative response server-side.
    with lab.db() as c:
        amount,currency=c.execute('select amount,currency from electronic_test.intents where id=%s',(iid,)).fetchone()
    payload=json.dumps({'id':iid,'event':'test_'+iid,'outcome':outcome,'amount':str(amount),'currency':currency},sort_keys=True)
    return payload,hmac.new(KEY,payload.encode(),hashlib.sha256).hexdigest()

def confirm(payload,signature):
    assert hmac.compare_digest(hmac.new(KEY,payload.encode(),hashlib.sha256).hexdigest(),signature),'invalid_signature'
    e=json.loads(payload);assert e['outcome'] in ('succeeded','failed','pending')
    with lab.db() as c:
        # lab.db autocommit is overridden: receipt, order and link commit atomically.
        with c.transaction():
            row=c.execute('select customer,amount,currency,state,order_id from electronic_test.intents where id=%s for update',(e['id'],)).fetchone()
            assert row and str(row[1])==e['amount'] and row[2]==e['currency'],'amount_mismatch'
            if row[4]:return row[4]
            if row[3]=='failed':return None
            if e['outcome']!='succeeded':
                c.execute('update electronic_test.intents set state=%s where id=%s',(e['outcome'],e['id']));return None
            c.execute("update electronic_test.intents set state='succeeded',event=%s where id=%s",(e['event'],e['id']))
            c.execute("select set_config('request.jwt.claim.sub',%s,true)",(str(row[0]),))
            c.execute("select set_config('request.jwt.claims',%s,true)",(json.dumps({'sub':str(row[0]),'role':'authenticated'}),))
            c.execute("select set_config('electronic_test.intent',%s,true)",(e['id'],))
            oid=lab.q(c,"select public.place_order(p_store=>%s,p_items=>%s::jsonb,p_payment=>'card',p_address=>'DEMO Rudaki 1',p_lat=>%s,p_lng=>%s,p_key=>%s)",(lab.STORE,json.dumps([{'item_id':lab.ITEM,'qty':1}]),lab.LAT,lab.LNG,'electronic_'+e['id'].replace('-','')))
            assert lab.q(c,'select total from orders where id=%s',(oid,))==row[1],'order_amount_changed'
            c.execute('update electronic_test.intents set order_id=%s where id=%s',(oid,e['id']))
            return oid

def state(role):
    code,orders=lab.request(3000,'/orders?select=id,status,payment,total,cash_collected&order=id.desc',token=lab.bearer(ROLES[role]))
    assert code==200
    with lab.db() as c:
        rows=c.execute('select id,amount,currency,state,order_id from electronic_test.intents order by id').fetchall() if role in ('customer','admin') else []
    return {'orders':orders,'intents':[dict(zip(['id','amount','currency','state','order_id'],r)) for r in rows]}

def action(role,data):
    op=data['op']
    if op=='create':assert role=='customer';return intent(data['key'])
    if op=='provider':
        assert role=='customer';return {'order_id':confirm(*event(str(uuid.UUID(data['id'])),data['outcome']))}
    oid=int(data['id']);token=lab.bearer(ROLES[role])
    if op=='assign':assert role=='admin';return lab.rpc(token,'admin_assign_driver',{'p_order':oid,'p_driver':lab.uid('driver1')})
    if op=='deliver':assert role=='driver';return lab.rpc(token,'deliver_order',{'p_id':oid,'p_cash':0,'p_note':'DEMO prepaid; no cash','p_photo':None})
    assert (role,op) in [('merchant','preparing'),('merchant','ready'),('driver','pickedup')]
    return lab.rpc(token,'set_order_status',{'p_id':oid,'p_to':op})

class Handler(BaseHTTPRequestHandler):
    def log_message(self,*args):pass
    def send(self,code,value,ctype='application/json'):
        raw=value if isinstance(value,bytes) else json.dumps(value,default=str).encode()
        self.send_response(code);self.send_header('Content-Type',ctype);self.send_header('Cache-Control','no-store');self.send_header('X-Content-Type-Options','nosniff');self.end_headers();self.wfile.write(raw)
    def role(self):return SESSIONS.get(self.headers.get('Authorization','').removeprefix('Bearer '))
    def do_GET(self):
        if self.path=='/':return self.send(200,(ROOT/'index.html').read_bytes(),'text/html; charset=utf-8')
        if self.path=='/sessions':return self.send(200,{r:k for k,r in SESSIONS.items()}) # explicit sandbox role switcher
        if self.path=='/state' and self.role():return self.send(200,state(self.role()))
        self.send(404,{'error':'not_found'})
    def do_POST(self):
        if self.headers.get('Origin') not in (None,'http://127.0.0.1:8088'):return self.send(403,{'error':'origin'})
        if self.path!='/action' or not self.role():return self.send(403,{'error':'role'})
        try:
            assert int(self.headers.get('Content-Length','0'))<4096
            data=json.loads(self.rfile.read(int(self.headers['Content-Length'])))
            with LOCK:result=action(self.role(),data)
            self.send(200,{'result':result})
        except Exception as e:self.send(400,{'error':str(e)[:160]})

if __name__=='__main__':
    if '--setup' in sys.argv:setup()
    ThreadingHTTPServer(('127.0.0.1',8088),Handler).serve_forever()
