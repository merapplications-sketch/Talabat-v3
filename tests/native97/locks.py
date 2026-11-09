import runpy,json,time,threading
from pathlib import Path
import psycopg
x=runpy.run_path('tests/native96/faults.py');session=x['session'];order=x['order'];B=x['B'];O=x['O']
a=psycopg.connect(autocommit=True);hold=psycopg.connect();wait=session();result={}
try:
 hold.execute("select pg_advisory_xact_lock(hashtextextended(%s,0))",(B+':request95_same',))
 def replay():
  try:result['id']=order(wait,'request95_same');wait.commit()
  except psycopg.Error as e:result['error']=e.sqlstate;wait.rollback()
 t=threading.Thread(target=replay);t.start();blocked=False
 for _ in range(100):
  blocked=hold.info.backend_pid in a.execute('select pg_blocking_pids(%s)',(wait.info.backend_pid,)).fetchone()[0]
  if blocked:break
  time.sleep(.02)
 assert blocked
 # Known existing keys return without admission changes or new financial effects.
 before=a.execute('select count(*) from orders').fetchone()[0]
 with session(B) as c:
  c.execute("set lock_timeout='300ms'");other_key=order(c,'request95_failure')
 with session(O) as c:
  c.execute("set lock_timeout='300ms'");other_account=order(c,'request95_same')
 assert a.execute('select count(*) from orders').fetchone()[0]==before
 hold.rollback();t.join(12);assert not t.is_alive() and 'id' in result,result
 assert other_account!=result['id'] and other_key!=result['id']
 Path('native97-result.json').write_text(json.dumps({'passed':True,'same_key_blocking_observed':blocked,'different_key_replay':'allowed while lock held','different_account_same_key_replay':'allowed while lock held','new_orders':0,'limits':['existing-order replay independence only','new keys still share profile row; global deadlock freedom not proven','captured minimal native96 fixture, not live SQL or HTTP']},indent=2))
finally:
 hold.rollback();hold.close();wait.close();a.close()
