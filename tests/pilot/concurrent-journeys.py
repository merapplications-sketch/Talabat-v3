"""NEW 42-authenticated-user stages, first-cash consent + real order/GPS REST.
No settlement/closed financial suites. Temporary Docker VM loopback only.
"""
import concurrent.futures,json,os,threading,time,uuid
import lab
lock=threading.Lock();metrics=[];errors=[];stop=threading.Event()
def measured(token,path,data=None):
 start=time.perf_counter()
 try:code,value=lab.request(3000,path,data,token)
 except Exception as e:code,value=0,{'message':type(e).__name__}
 with lock:metrics.append({'endpoint':path.split('?')[0],'ms':(time.perf_counter()-start)*1000,'status':code})
 if code not in(200,204):raise AssertionError(path.split('?')[0]+' '+str(code)+' '+str(value)[:160])
 return value
def rpc(token,fn,args):return measured(token,'/rpc/'+fn,args)
def poll(name):
 token=lab.bearer(name)
 while not stop.is_set():
  try:
   lim=300 if name=='admin'else 200 if name=='merchant'else 60
   path='/orders?select=*&order=created_at.desc&limit='+str(lim)
   if name.startswith('loadc'):path+='&customer_id=eq.'+lab.uid(name)
   elif name.startswith('loadd'):path+='&driver_id=eq.'+lab.uid(name)
   elif name=='merchant':path+='&store_id=in.('+lab.STORE+')'
   rows=measured(token,path);ids=[o['id']for o in rows]
   rpc(token,'order_approval_states',{'p_order_ids':ids[:300]})
   if ids:measured(token,'/order_items?select=*&order_id=in.('+','.join(map(str,ids))+')')
  except Exception as e:
   with lock:errors.append({'poll':name,'error':str(e)[:180]})
  stop.wait(25 if name.startswith('loadc')else 10)
def trip(slot,stage,roundn):
 c,d=lab.bearer('loadc'+str(slot)),lab.bearer('loadd'+str(slot));m,a=lab.bearer('merchant'),lab.bearer('admin')
 rpc(c,'delivery_quote',{'p_store':lab.STORE,'p_lat':lab.LAT,'p_lng':lab.LNG})
 oid=rpc(c,'place_order',{'p_store':lab.STORE,'p_items':[{'item_id':lab.ITEM,'qty':2}],'p_address':'SYNTHETIC concurrent journey','p_lat':lab.LAT,'p_lng':lab.LNG,'p_payment':'cash','p_key':f'concurrent_{stage}_{roundn}_{slot}','p_fee':15})
 view=rpc(c,'order_approval_states',{'p_order_ids':[oid]})[0]
 if view['state']=='awaiting_merchant':
  offer=rpc(m,'merchant_review_order',{'p_order':oid,'p_minutes':15,'p_request':str(uuid.uuid4())})
  rpc(c,'customer_confirm_order',{'p_order':oid,'p_revision':offer['revision'],'p_request':str(uuid.uuid4())})
 else:
  rpc(m,'merchant_review_order',{'p_order':oid,'p_minutes':15,'p_request':str(uuid.uuid4())})
  rpc(m,'set_order_status',{'p_id':oid,'p_to':'preparing'})
 rpc(a,'admin_assign_driver',{'p_order':oid,'p_driver':lab.uid('loadd'+str(slot))})
 rpc(m,'set_order_status',{'p_id':oid,'p_to':'ready'});rpc(d,'set_order_status',{'p_id':oid,'p_to':'pickedup'});rpc(d,'driver_ping',{'p_online':True})
 for n in range(3):
  if n:time.sleep(8)
  rpc(d,'driver_location',{'p_lat':lab.LAT+n*.0001,'p_lng':lab.LNG,'p_acc':12})
  assert rpc(c,'order_courier_position',{'p_order':oid}),'position_missing'
 rpc(d,'deliver_order',{'p_id':oid,'p_cash':65,'p_note':None});return oid

def main():
 lab.wait(lambda:lab.request(3000,'/')[0]==200,'rest');s=lab.state()
 for slot in range(20):
  for prefix,base in [('loadc',700),('loadd',800)]:
   name=prefix+str(slot);s['accounts'][name]=lab.register(name,base+slot,admin=True);lab.save(lab.STATE,s)
 with lab.db()as db:
  db.execute("update profiles set role='driver',driver_status='approved',online=false where id=any(%s::uuid[])",([lab.uid('loadd'+str(i))for i in range(20)],))
  db.execute("insert into orders(store_id,customer_id,status,payment,subtotal,total,created_at,done_at,cash_collected,cash_settled_at)select %s,%s,'delivered','cash',25,40,now()-interval'3 days',now()-interval'3 days',0,now()-interval'3 days'from generate_series(1,10000)",(lab.STORE,lab.uid('outsider')))
  db.execute('analyze;select pg_stat_statements_reset()')
 result={'source':os.environ.get('GITHUB_SHA'),'live':False,'environment':'free GitHub ubuntu-24.04 VM; native PostgreSQL17.6 GoTrue2.197 PostgREST14.18; loopback','stages':[],'limits':['HTTP virtual users; no browser rendering','not production WAN/plan, Realtime/push, upload, GPS accuracy, battery or multi-hour endurance','one synthetic restaurant; admin assignment, claim races already closed separately','no settlement load or financial tests repeated'],'production_capacity_claim':False}
 for stage,n in enumerate([5,10,20]):
  stop.clear();start=time.monotonic();mi=len(metrics);ei=len(errors);done=[]
  users=['admin','merchant']+['loadc'+str(i)for i in range(n)]+['loadd'+str(i)for i in range(n)]
  threads=[threading.Thread(target=poll,args=(name,),daemon=True)for name in users];[t.start()for t in threads]
  with concurrent.futures.ThreadPoolExecutor(max_workers=n)as pool:
   for roundn in range(3):
    wait=start+roundn*20-time.monotonic()
    if wait>0:stop.wait(wait)
    for f in concurrent.futures.as_completed([pool.submit(trip,i,stage,roundn)for i in range(n)]):
     try:done.append(f.result())
     except Exception as e:
      with lock:errors.append({'stage':stage,'error':str(e)[:200]})
  remaining=60-(time.monotonic()-start)
  if remaining>0:stop.wait(remaining)
  stop.set();[t.join(timeout=25)for t in threads];duration=time.monotonic()-start;part=metrics[mi:];v=sorted(x['ms']for x in part);pct=lambda p:round(v[int((len(v)-1)*p)],2)
  item={'concurrent_authenticated_sessions':len(users),'concurrent_journeys':n,'duration_s':round(duration,2),'planned_orders':n*3,'completed_orders':len(done),'http_requests':len(part),'http_error_rate':sum(x['status']not in(200,204)for x in part)/len(part),'rps':round(len(part)/duration,2),'p50_ms':pct(.5),'p95_ms':pct(.95),'p99_ms':pct(.99),'max_ms':round(max(v),2),'errors':errors[ei:]}
  result['stages'].append(item);lab.save(lab.HERE/'result-concurrent-journeys.json',result);print(json.dumps(item),flush=True)
 with lab.db()as db:
  result['delivered']=lab.q(db,"select count(*)from orders where client_key like 'concurrent_%%'and status='delivered'")
  result['duplicates']=lab.q(db,"select count(*)from(select customer_id,client_key from orders where client_key like'concurrent_%%'group by customer_id,client_key having count(*)>1)x")
  result['remaining_active']=lab.q(db,"select count(*)from orders where client_key like'concurrent_%%'and status not in('delivered','cancelled','rejected')")
  result['approval_events']=lab.q(db,"select count(*)from fulfillment_private.approval_events e join orders o on o.id=e.order_id where o.client_key like'concurrent_%%'and e.kind='customer_confirm'")
  result['db_top_queries']=db.execute("select calls,round(total_exec_time::numeric,2),round(mean_exec_time::numeric,3),left(query,180)from pg_stat_statements where query not like'%pg_stat_statements%'order by total_exec_time desc limit 10").fetchall()
  result['db_counters']=db.execute('select deadlocks,temp_bytes,numbackends from pg_stat_database where datname=current_database()').fetchone()
 result.update({'historical_orders':10000,'poll_intervals_s':{'customer':25,'merchant_driver_admin':10},'gps_interval_s':8,'lab_p95_budget_ms':2000,'unique_authenticated_identities':42})
 result['pass']=result['delivered']==105 and result['duplicates']==0 and result['remaining_active']==0 and not errors and all(x['p95_ms']<=2000 and x['http_error_rate']==0 for x in result['stages'])
 lab.save(lab.HERE/'result-concurrent-journeys.json',result)
 if not result['pass']:raise SystemExit(1)
if __name__=='__main__':main()
