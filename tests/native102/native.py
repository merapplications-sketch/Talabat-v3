"""Native PostgreSQL; isolated synthetic data and independent connections only."""
import os,json,time,threading,hashlib
from pathlib import Path
import psycopg
from tcp_proxy import CutProxy
assert os.environ.get('PGHOST')=='127.0.0.1'
B='10000000-0000-4000-8000-000000000092';O='20000000-0000-4000-8000-000000000092';S='30000000-0000-4000-8000-000000000092';I='40000000-0000-4000-8000-000000000092';G='60000000-0000-4000-8000-000000000092'
a=psycopg.connect(autocommit=True);results=[]
a.execute(''.join(Path(p).read_text() for p in ['tests/native98/setup.sql','tests/native102/constraints.sql','tests/native102/candidate.sql']))
def reset():
 a.execute('truncate orders,order_items,wallet_entries,order_customer_phone,order_recipient,group_orders,fulfillment_private.order_approvals,security_private.order_request_bindings restart identity cascade')
 a.execute("insert into wallet_entries(user_id,amount,kind) values(%s,100,'adjust'),(%s,100,'adjust')",(B,O))
def session(uid=B,port=5432):
 c=psycopg.connect(port=port,sslmode='disable');c.execute("set statement_timeout='10s'");c.execute("select set_config('request.jwt.claims',%s,false)",(json.dumps({'sub':uid,'aal':'aal1','session_id':'50000000-0000-4000-8000-000000000092'}),));c.execute('set role authenticated');return c
def order(c,key,extra=None,qty=1):
 return c.execute("select place_order(p_store=>%s,p_items=>%s::jsonb,p_address=>'synthetic',p_lat=>38.5,p_lng=>68.7,p_key=>%s,p_wallet=>5,p_extra=>%s::jsonb)",(S,json.dumps([{'item_id':I,'qty':qty,'options':[]}]),key,json.dumps(extra or {}))).fetchone()[0]
def counts():
 return a.execute("select (select count(*) from orders),(select count(*) from order_items),(select count(*) from wallet_entries where kind='spend'),(select coalesce(sum(amount),0) from wallet_entries where kind='spend'),(select count(*) from security_private.order_request_bindings),(select count(*) from fulfillment_private.order_approvals)").fetchone()
def record(name,**kw):results.append({'case':name,'passed':True,**kw})
try:
 for mode in ['group','scheduled','plain']:
  reset();extra={}
  if mode=='group':a.execute("insert into group_orders(id,host_id,status,store_id,expires_at)values(%s,%s,'open',%s,now()+interval '1 hour')",(G,B,S));extra={'group':G}
  if mode=='scheduled':extra={'at':a.execute("select now()+interval '40 minutes 2 seconds'").fetchone()[0].isoformat()}
  c1=session();c2=session();first=order(c1,'request102_same',extra);out={}
  def replay():
   try:out['id']=order(c2,'request102_same',extra);c2.commit()
   except Exception as e:out['error']=str(e);c2.rollback()
  t=threading.Thread(target=replay);t.start();blocked=False
  for _ in range(150):
   blocked=c1.info.backend_pid in a.execute('select pg_blocking_pids(%s)',(c2.info.backend_pid,)).fetchone()[0]
   if blocked:break
   time.sleep(.01)
  assert blocked
  c1.commit();t.join(12);assert not t.is_alive() and out.get('id')==first,out
  c1.close();c2.close()
  if mode=='scheduled':time.sleep(2.2)
  before=counts()
  with session() as c:assert order(c,'request102_same',extra)==first
  assert counts()==before==(1,1,1,-5,1,1)
  record(mode+' concurrent replay and discarded ACK',blocking_observed=blocked,orders=1,wallet_spends=1,wallet_amount='-5',bindings=1)
  with session() as c:
   try:order(c,'request102_same',extra,3);raise AssertionError('mismatch accepted')
   except psycopg.Error as e:assert 'idempotency_mismatch' in str(e);c.rollback()
  assert counts()==before;record(mode+' changed payload denied atomically')
  if mode!='plain':
   with session() as c:
    try:order(c,'request102_new',extra);raise AssertionError('new key bypassed admission')
    except psycopg.Error as e:assert ('bad_group' if mode=='group' else 'bad_time') in str(e);c.rollback()
   assert counts()==before;record(mode+' new key admission preserved')
 reset()
 with session() as c:first=order(c,'request102_accounts')
 with session(O) as c:second=order(c,'request102_accounts')
 assert first!=second and counts()==(2,2,2,-10,2,2);record('same key distinct identities return own order')
 for mode in ['before','after']:
  reset();proxy=CutProxy(mode);c=session(port=proxy.port);first=order(c,'request102_tcp');proxy.arm=True
  try:c.commit();raise AssertionError('expected TCP loss')
  except (psycopg.OperationalError,psycopg.InterfaceError):pass
  finally:c.close()
  proxy.join();assert proxy.cut
  for _ in range(100):
   if counts()[0]==(1 if mode=='after' else 0):break
   time.sleep(.02)
  assert counts()[0]==(1 if mode=='after' else 0)
  with session() as c:second=order(c,'request102_tcp')
  assert (first==second)==(mode=='after') and counts()==(1,1,1,-5,1,1)
  record('real TCP cut '+mode+' COMMIT',orders=1,wallet_spends=1,bindings=1)
 reset();hold=psycopg.connect();hold.execute('select * from profiles where id=%s for update',(B,));c=session();c.execute("set lock_timeout='150ms'")
 try:order(c,'request102_timeout');raise AssertionError('no timeout')
 except psycopg.Error as e:assert e.sqlstate=='55P03';c.rollback()
 finally:hold.rollback();hold.close();c.close()
 assert counts()==(0,0,0,0,0,0)
 with session() as c:order(c,'request102_timeout')
 assert counts()==(1,1,1,-5,1,1);record('candidate lock timeout and retry')
 reset();a.execute("insert into group_orders(id,host_id,status,store_id,expires_at)values(%s,%s,'open',%s,now()+interval '1 hour')",(G,B,S))
 hold=psycopg.connect();hold.execute("set deadlock_timeout='100ms'");hold.execute('select * from profiles where id=%s for update',(B,));c=session();out={}
 def waiting():
  try:out['id']=order(c,'request102_deadlock',{'group':G});c.commit()
  except psycopg.Error as e:out['error']=e.sqlstate;c.rollback()
 t=threading.Thread(target=waiting);t.start();blocked=False
 for _ in range(200):
  blocked=hold.info.backend_pid in a.execute('select pg_blocking_pids(%s)',(c.info.backend_pid,)).fetchone()[0]
  if blocked:break
  time.sleep(.01)
 assert blocked
 code=None
 try:hold.execute('select * from group_orders where id=%s for update',(G,))
 except psycopg.Error as e:code=e.sqlstate
 finally:hold.rollback();hold.close()
 t.join(12);assert not t.is_alive();c.close();assert code=='40P01' or out.get('error')=='40P01',(code,out)
 with session() as c:order(c,'request102_deadlock',{'group':G})
 assert counts()==(1,1,1,-5,1,1);record('candidate versus opposite-order caller: deadlock and recovery',sqlstate='40P01',global_deadlock_freedom=False)
finally:
 a.close()
 Path('native102-result.json').write_text(json.dumps({'results':results,'candidate_sha256':hashlib.sha256(Path('tests/native102/candidate.sql').read_bytes()).hexdigest(),'scope':'native PostgreSQL17.6; partial captured schema; synthetic delivery/happy-hour; not hosted RBAC'},indent=2))
print(json.dumps({'passed':len(results),'results':results}))
