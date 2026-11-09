import os,json,time,threading,hashlib
from pathlib import Path
import psycopg
assert os.environ.get('PGHOST')=='127.0.0.1'
B='10000000-0000-4000-8000-000000000092';S='30000000-0000-4000-8000-000000000092';I='40000000-0000-4000-8000-000000000092'
admin=psycopg.connect(autocommit=True);results=[]
setup=Path('tests/native96/setup.sql').read_text().replace('create role authenticated;create role anon;','')
for mode,n,status in [('open_limit',4,'pending'),('hour_limit',19,'delivered')]:
 admin.execute('drop database if exists native98');admin.execute('create database native98')
 a=psycopg.connect(dbname='native98',autocommit=True);a.execute(setup)
 if Path('tests/native98/place_order.fixed.sql').exists():a.execute(Path('tests/native98/place_order.fixed.sql').read_text())
 a.execute("insert into orders(store_id,customer_id,payment,status,created_at) values(%s,%s,'cash','delivered',now()-interval '2 hours')",(S,B))
 for _ in range(n):a.execute('insert into orders(store_id,customer_id,payment,status) values(%s,%s,\'cash\',%s)',(S,B,status))
 hold=psycopg.connect(dbname='native98');hold.execute('select id from profiles where id=%s for update',(B,))
 conns=[psycopg.connect(dbname='native98') for _ in range(2)];out=[None,None]
 for c in conns:
  c.execute("set statement_timeout='10s'");c.execute("select set_config('request.jwt.claims',%s,false)",(json.dumps({'sub':B}),));c.execute('set role authenticated')
 def call(i):
  c=conns[i]
  try:
   oid=c.execute("select place_order(p_store=>%s,p_items=>%s::jsonb,p_address=>'synthetic',p_lat=>38.5,p_lng=>68.7,p_key=>%s,p_wallet=>5)",(S,json.dumps([{'item_id':I,'qty':1,'options':[]}]),'request98_'+mode+'_'+str(i))).fetchone()[0];c.commit();out[i]={'order':oid}
  except psycopg.Error as e:c.rollback();out[i]={'error':str(e).split('\n')[0],'sqlstate':e.sqlstate}
 ts=[threading.Thread(target=call,args=(i,)) for i in range(2)]
 for t in ts:t.start()
 blocked=False
 for _ in range(200):
  blocked=all(a.execute('select cardinality(pg_blocking_pids(%s))>0',(c.info.backend_pid,)).fetchone()[0] for c in conns)
  if blocked:break
  time.sleep(.01)
 hold.rollback();hold.close()
 for t in ts:t.join(12);assert not t.is_alive()
 for c in conns:c.close()
 successes=sum('order' in x for x in out);spends=a.execute("select count(*),coalesce(sum(amount),0) from wallet_entries where kind='spend'").fetchone()
 count=a.execute("select count(*) from orders where customer_id=%s and "+("status in ('pending','preparing','ready','pickedup')" if mode=='open_limit' else "created_at>now()-interval '1 hour'"),(B,)).fetchone()[0]
 passed=blocked and successes==1 and count==n+1 and spends==(1,-5) and sum(x.get('error')=='too_many_orders' for x in out)==1
 results.append({'case':mode,'blocking_observed':blocked,'outcomes':out,'count_after':count,'wallet_spends':spends[0],'wallet_amount':str(spends[1]),'passed':passed});a.close()
# Fresh fixture for a bounded burst below limits and independent-account admission.
O='20000000-0000-4000-8000-000000000092'
for mode in ['three_keys','two_accounts']:
 admin.execute('drop database native98');admin.execute('create database native98')
 a=psycopg.connect(dbname='native98',autocommit=True);a.execute(setup)
 if Path('tests/native98/place_order.fixed.sql').exists():a.execute(Path('tests/native98/place_order.fixed.sql').read_text())
 for uid in [B,O]:a.execute("insert into orders(store_id,customer_id,payment,status,created_at) values(%s,%s,'cash','delivered',now()-interval '2 hours')",(S,uid))
 out={};barrier=threading.Barrier(3 if mode=='three_keys' else 2)
 def independent(i,uid):
  c=psycopg.connect(dbname='native98')
  try:
   c.execute("set statement_timeout='10s'");c.execute("select set_config('request.jwt.claims',%s,false)",(json.dumps({'sub':uid}),));c.execute('set role authenticated');barrier.wait(5)
   oid=c.execute("select place_order(p_store=>%s,p_items=>%s::jsonb,p_address=>'synthetic',p_lat=>38.5,p_lng=>68.7,p_key=>%s,p_wallet=>5)",(S,json.dumps([{'item_id':I,'qty':1,'options':[]}]),'request98_burst_'+str(i))).fetchone()[0];c.commit();out[i]={'order':oid}
  except psycopg.Error as e:c.rollback();out[i]={'error':e.sqlstate}
  finally:c.close()
 hold=None
 if mode=='two_accounts':hold=psycopg.connect(dbname='native98');hold.execute('select id from profiles where id=%s for update',(B,))
 ts=[threading.Thread(target=independent,args=(i,uid)) for i,uid in enumerate([B,B,B] if mode=='three_keys' else [B,O])]
 for t in ts:t.start()
 independent_observed=True
 if hold:
  for _ in range(300):
   if 1 in out:break
   time.sleep(.01)
  independent_observed=1 in out and 0 not in out and 'order' in out[1];hold.rollback();hold.close()
 for t in ts:t.join(12);assert not t.is_alive()
 spends=a.execute("select count(*),count(distinct order_id),sum(amount) from wallet_entries where kind='spend'").fetchone()
 expected=len(ts);passed=independent_observed and len(out)==expected and all('order' in v for v in out.values()) and spends==(expected,expected,-5*expected)
 results.append({'case':mode,'passed':passed,'connections':expected,'independent_account_observed':independent_observed,'wallet_spends':spends[0],'distinct_spends':spends[1],'wallet_amount':str(spends[2]),'outcomes':out});a.close()
admin.execute('drop database native98');admin.close()
Path('native98-result.json').write_text(json.dumps({'results':results,'source_setup_sha256':hashlib.sha256(setup.encode()).hexdigest(),'scope':'native PostgreSQL separate connections; synthetic seeded orders; captured minimal schema and declared doubles, not hosted HTTP'},indent=2))
print(json.dumps(results));assert all(x['passed'] for x in results),'admission limit race'
