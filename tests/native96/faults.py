import runpy, socket, select, threading, struct, time, json, os
from pathlib import Path
import psycopg
selected=os.environ.get('TALABOT_TEST_SETUP','tests/native96/setup.sql')
assert selected in ['tests/native96/setup.sql','tests/native98/setup.sql']
source=Path('tests/native95/contention.py').read_text().replace("Path('tests/native95/setup.sql')",'Path('+repr(selected)+')')
x={'__name__':'native96_fixture'};exec(compile(source,'tests/native95/contention.py','exec'),x)
B=x['B']; O=x['O']; order=x['order']; session=x['session']
a=psycopg.connect(autocommit=True); results=[]
def release_consent():a.execute("update fulfillment_private.order_approvals set state='accepted',customer_at=now()")
class CutProxy:
 def __init__(self,mode):
  self.mode=mode;self.arm=False;self.cut=False;self.error=None
  self.listener=socket.socket();self.listener.bind(('127.0.0.1',0));self.listener.listen(1);self.port=self.listener.getsockname()[1]
  self.thread=threading.Thread(target=self.run,daemon=True);self.thread.start()
 def run(self):
  front=back=None
  try:
   front,_=self.listener.accept();back=socket.create_connection(('127.0.0.1',5432),timeout=10);front.settimeout(10)
   buffers={front:b'',back:b''}
   while True:
    ready,_,_=select.select([front,back],[],[],10)
    if not ready:raise TimeoutError('bounded proxy wait')
    for s in ready:
     data=s.recv(65536)
     if not data:return
     other=back if s is front else front
     if not self.arm:other.sendall(data);continue
     buffers[s]+=data
     while len(buffers[s])>=5:
      n=1+struct.unpack('!I',buffers[s][1:5])[0]
      if len(buffers[s])<n:break
      frame=buffers[s][:n];buffers[s]=buffers[s][n:]
      before=s is front and frame[:1]==b'Q' and frame[5:].rstrip(b'\0').strip().upper()==b'COMMIT'
      after=s is back and frame[:1]==b'C' and frame[5:]==b'COMMIT\0'
      if (self.mode=='before' and before) or (self.mode=='after' and after):
       self.cut=True
       for c in [front,back]:
        try:c.shutdown(socket.SHUT_RDWR)
        except OSError:pass
       return
      other.sendall(frame)
  except Exception as e:self.error=type(e).__name__
  finally:
   for c in [front,back,self.listener]:
    if c:c.close()
 def join(self):self.thread.join(12);assert not self.thread.is_alive();assert self.error is None,self.error
try:
 for mode in ['before','after']:
  release_consent();key='request96_tcp_'+mode;p=CutProxy(mode)
  c=psycopg.connect(host='127.0.0.1',port=p.port,sslmode='disable',connect_timeout=5)
  c.execute("set statement_timeout='10s'");c.execute("select set_config('request.jwt.claims',%s,false)",(json.dumps({'sub':B,'aal':'aal1','session_id':'50000000-0000-4000-8000-000000000092'}),));c.execute('set role authenticated')
  original=order(c,key);p.arm=True;error=None
  try:c.commit()
  except (psycopg.OperationalError,psycopg.InterfaceError) as e:error=type(e).__name__
  finally:c.close()
  p.join();assert p.cut and error
  for _ in range(100):
   count=a.execute('select count(*) from orders where client_key=%s',(key,)).fetchone()[0]
   if count==(1 if mode=='after' else 0):break
   time.sleep(.02)
  assert count==(1 if mode=='after' else 0)
  with session() as retry:newid=order(retry,key)
  assert (newid==original)==(mode=='after')
  assert a.execute('select count(*) from orders where client_key=%s',(key,)).fetchone()[0]==1
  assert a.execute("select count(*) from wallet_entries where order_id=%s and kind='spend'",(newid,)).fetchone()[0]==1
  results.append({'case':'real TCP cut '+mode+' COMMIT','passed':True,'client_error':error,'before_retry_orders':count,'final_orders':1,'final_wallet_spends':1})
 # Bounded lock timeout; ordinary transaction conflict, not a claim about business deadlocks.
 c1=psycopg.connect();c2=psycopg.connect();c1.execute('update profiles set name=name where id=%s',(B,));c2.execute("set lock_timeout='150ms'")
 code=None
 try:c2.execute('update profiles set name=name where id=%s',(B,))
 except psycopg.Error as e:code=e.sqlstate;c2.rollback()
 assert code=='55P03';c1.rollback();c2.execute('update profiles set name=name where id=%s',(B,));c2.commit();c1.close();c2.close();results.append({'case':'lock timeout and retry','passed':True,'sqlstate':code})
 # Four independent connections, bounded burst; no hosted load.
 release_consent()
 import concurrent.futures
 def contender(_):
  with session() as c:return order(c,'request96_four')
 with concurrent.futures.ThreadPoolExecutor(max_workers=4) as pool:ids=list(pool.map(contender,range(4)))
 assert len(set(ids))==1
 assert a.execute("select count(*) from wallet_entries where order_id=%s and kind='spend'",(ids[0],)).fetchone()[0]==1
 results.append({'case':'four concurrent same-key requests','passed':True,'connections':4,'distinct_orders':1,'wallet_spends':1})
 c=session();code=None
 try:order(c,'request96_fresh_over_limit')
 except psycopg.Error as e:code=str(e).split('\n')[0];c.rollback()
 finally:c.close()
 assert code=='too_many_orders',code
 results.append({'case':'new key still denied at existing unfinished-order limit','passed':True,'error':code})
 # Deliberate two-row deadlock in fixture transactions; no claim of business-path deadlock.
 d1=psycopg.connect();d2=psycopg.connect()
 for c in [d1,d2]:c.execute("set deadlock_timeout='100ms';set statement_timeout='5s'")
 d1.execute('update profiles set name=name where id=%s',(B,));d2.execute('update profiles set name=name where id=%s',(O,));out=[]
 def cross(c,uid):
  try:c.execute('update profiles set name=name where id=%s',(uid,));out.append('ok')
  except psycopg.Error as e:out.append(e.sqlstate)
  finally:c.rollback();c.close()
 ts=[threading.Thread(target=cross,args=(d1,O)),threading.Thread(target=cross,args=(d2,B))]
 for t in ts:t.start()
 for t in ts:t.join(7);assert not t.is_alive()
 assert sorted(out)==['40P01','ok'],out
 results.append({'case':'synthetic two-row deadlock releases victim transaction','passed':True,'outcomes':sorted(out)})
finally:a.close()
Path('native96-result.json').write_text(json.dumps({'results':results,'limits':['native95 captured minimal schema and declared doubles remain','synthetic consent release, not customer approval UI','timeout is fixture-row contention; no claim that place_order deadlocks']},indent=2))
print(json.dumps({'native96_passed':len(results)}))
