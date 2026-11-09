import json, os, time, threading, hashlib
from pathlib import Path
import psycopg
assert os.environ.get('PGHOST') == '127.0.0.1', 'isolated loopback only'
B='10000000-0000-4000-8000-000000000092'; O='20000000-0000-4000-8000-000000000092'
S='30000000-0000-4000-8000-000000000092'; I='40000000-0000-4000-8000-000000000092'
setup=Path('tests/native95/setup.sql').read_text()
a=psycopg.connect(autocommit=True); a.execute(setup)
results=[]
def session(uid=B):
 c=psycopg.connect(); c.execute("set statement_timeout='10s'");c.execute("select set_config('request.jwt.claims',%s,false)",(json.dumps({'sub':uid,'aal':'aal1','session_id':'50000000-0000-4000-8000-000000000092'}),));c.execute('set role authenticated');return c
def order(c,key,qty=1):
 return c.execute("select place_order(p_store=>%s::uuid,p_items=>%s::jsonb,p_address=>'synthetic',p_lat=>38.5,p_lng=>68.7,p_key=>%s,p_wallet=>5)",(S,json.dumps([{'item_id':I,'qty':qty,'options':[]}]),key)).fetchone()[0]
def snap():
 return {t:a.execute('select coalesce(jsonb_agg(to_jsonb(t) order by to_jsonb(t)::text),\'[]\'::jsonb) from '+t+' t').fetchone()[0] for t in ['orders','order_items','wallet_entries','fulfillment_private.order_approvals']}
try:
 c1=session();c2=session();p1=c1.info.backend_pid;p2=c2.info.backend_pid;assert p1!=p2
 first=order(c1,'same95'); box={}
 def second():
  try:box['id']=order(c2,'same95');c2.commit()
  except Exception as e:box['error']=type(e).__name__;c2.rollback()
 t=threading.Thread(target=second);t.start(); blocked=False
 for _ in range(100):
  blocked=p1 in a.execute('select pg_blocking_pids(%s)',(p2,)).fetchone()[0]
  if blocked:break
  time.sleep(.02)
 assert blocked,'second independent connection never observed blocked by first'
 c1.commit();t.join(12);assert not t.is_alive() and box.get('id')==first,box
 assert a.execute('select count(*) from orders').fetchone()[0]==1
 assert a.execute("select count(*) from wallet_entries where kind='spend'").fetchone()[0]==1
 results.append({'case':'same key two independent connections','passed':True,'pids':[p1,p2],'blocking_observed':blocked,'orders':1,'wallet_spends':1})
 c1.close();c2.close()
 before=snap()
 with session() as c:assert order(c,'same95')==first
 assert snap()==before;results.append({'case':'committed result discarded then retry','passed':True,'note':'ACK loss modeled by discarding result; not a TCP fault'})
 with session() as c:assert order(c,'same95',3)==first
 assert snap()==before;results.append({'case':'same key changed quantity preserves original','passed':True})
 with session(O) as c:other=order(c,'same95')
 assert other!=first and str(a.execute('select customer_id from orders where id=%s',(other,)).fetchone()[0])==O
 results.append({'case':'same key different account returns own order','passed':True})
 a.execute("update fulfillment_private.order_approvals set state='accepted',customer_at=now() where order_id=%s",(first,))
 before=snap();c=session();c.execute("select set_config('test92.fail_end','yes',false)")
 try:order(c,'fail95');raise AssertionError('expected failure')
 except psycopg.Error as e:assert 'synthetic_final_failure' in str(e);c.rollback()
 finally:c.close()
 assert snap()==before
 with session() as c:order(c,'fail95')
 assert len(snap()['orders'])==len(before['orders'])+1
 assert len(snap()['wallet_entries'])==len(before['wallet_entries'])+1
 results.append({'case':'late failure rolls back then retry has one effect','passed':True})
finally:
 a.close()
Path('native95-result.json').write_text(json.dumps({'engine':'native PostgreSQL','setup_sha256':hashlib.sha256(setup.encode()).hexdigest(),'results':results,'limits':['minimal synthetic schema; delivery and happy hour doubles','captured SQL, not current hosted catalog','no inventory decrement in captured path','no hosted HTTP or provider Auth','synthetic prior cash consent for retry case']},indent=2))
print(json.dumps({'passed':len(results),'failed':0}))
