"""New 180s mixed order/GPS/poll workload; loopback-only, no finance calls."""
import concurrent.futures, json, os, statistics, threading, time
import lab

DURATION=180
assert os.environ.get('PILOT_SOAK_SECONDS','180')=='180'
metrics=[];failures=[];lock=threading.Lock();stop=threading.Event()

def measured(token,path,data=None):
    t=time.perf_counter()
    try:
        code,value=lab.request(3000,path,data,token)
    except Exception as e:
        code,value=0,None
        with lock:failures.append({'endpoint':path.split('?')[0],'failure':type(e).__name__})
    with lock:metrics.append({'path':path.split('?')[0],'ms':(time.perf_counter()-t)*1000,'status':code})
    if code not in (200,204):raise AssertionError('http_'+str(code)+' '+path.split('?')[0])
    return value

def rpc(token,fn,args):return measured(token,'/rpc/'+fn,args)

def poll(name):
    while not stop.is_set():
        try:
            limit=300 if name=='admin' else 200 if name=='merchant' else 60
            path='/orders?select=*&order=created_at.desc&limit='+str(limit)
            if name.startswith('soakc'):path+='&customer_id=eq.'+lab.uid(name)
            elif name.startswith('soakd'):path+='&driver_id=eq.'+lab.uid(name)
            elif name=='merchant':path+='&store_id=in.('+lab.STORE+')'
            measured(lab.bearer(name),path)
        except Exception as e:
            with lock:failures.append({'poll':name,'error':str(e)[:100]})
        stop.wait(25 if name.startswith('soakc') else 10)

def trip(slot,round_n):
    customer,driver=lab.bearer('soakc'+str(slot)),lab.bearer('soakd'+str(slot))
    rpc(customer,'delivery_quote',{'p_store':lab.STORE,'p_lat':lab.LAT,'p_lng':lab.LNG})
    key=f'soak_{slot}_{round_n}'
    oid=rpc(customer,'place_order',{'p_store':lab.STORE,'p_items':[{'item_id':lab.ITEM,'qty':2}],'p_address':'SYNTHETIC soak','p_lat':lab.LAT,'p_lng':lab.LNG,'p_payment':'cash','p_key':key,'p_fee':15})
    rpc(lab.bearer('merchant'),'set_prep_time',{'p_id':oid,'p_min':10})
    rpc(lab.bearer('merchant'),'set_order_status',{'p_id':oid,'p_to':'preparing'})
    rpc(lab.bearer('admin'),'admin_assign_driver',{'p_order':oid,'p_driver':lab.uid('soakd'+str(slot))})
    rpc(lab.bearer('merchant'),'set_order_status',{'p_id':oid,'p_to':'ready'})
    rpc(driver,'set_order_status',{'p_id':oid,'p_to':'pickedup'})
    rpc(driver,'driver_ping',{'p_online':True})
    for n in range(3):
        if n:time.sleep(8)
        rpc(driver,'driver_location',{'p_lat':lab.LAT+n*.0001,'p_lng':lab.LNG,'p_acc':12})
        position=rpc(customer,'order_courier_position',{'p_order':oid})
        assert position,'location_missing'
    rpc(driver,'deliver_order',{'p_id':oid,'p_cash':65,'p_note':None})
    return oid


def main():
    lab.wait(lambda:lab.request(3000,'/')[0]==200,'rest')
    s=lab.state()
    for slot in range(3):
        for prefix,base in [('soakc',300),('soakd',400)]:
            name=prefix+str(slot);s['accounts'][name]=lab.register(name,base+slot,admin=True);lab.save(lab.STATE,s)
    with lab.db() as c:
        c.execute("update profiles set role='driver',driver_status='approved',online=false where id=any(%s::uuid[])",([lab.uid('soakd'+str(i))for i in range(3)],))
        c.execute("insert into orders(store_id,customer_id,status,payment,subtotal,total,created_at,done_at,cash_collected,cash_settled_at) select %s,%s,'delivered','cash',25,40,now()-interval '3 days',now()-interval '3 days',0,now()-interval '3 days' from generate_series(1,10000)",(lab.STORE,lab.uid('outsider')))
        c.execute('analyze;select pg_stat_statements_reset()')
    threads=[threading.Thread(target=poll,args=(name,),daemon=True)for name in ['admin','merchant']+['soakc'+str(i)for i in range(3)]+['soakd'+str(i)for i in range(3)]]
    started=time.monotonic();[t.start()for t in threads];completed=[]
    try:
        with concurrent.futures.ThreadPoolExecutor(max_workers=3) as pool:
            for r in range(6):
                deadline=started+r*30
                if deadline>time.monotonic():stop.wait(deadline-time.monotonic())
                futs=[pool.submit(trip,i,r)for i in range(3)]
                for f in concurrent.futures.as_completed(futs):
                    try:completed.append(f.result())
                    except Exception as e:failures.append({'round':r,'error':str(e)[:120]})
                print('SOAK round='+str(r+1)+' completed='+str(len(completed)),flush=True)
        if time.monotonic()-started<DURATION:stop.wait(DURATION-(time.monotonic()-started))
    finally:
        stop.set();[t.join(timeout=25)for t in threads]
    duration=time.monotonic()-started
    values=sorted(x['ms']for x in metrics)
    pct=lambda p:round(values[int((len(values)-1)*p)],2)
    with lab.db()as c:
        confirmed=lab.q(c,"select count(*) from orders where client_key like 'soak_%%' and status='delivered'")
        duplicate=lab.q(c,"select count(*)from(select customer_id,client_key from orders where client_key like 'soak_%%' group by customer_id,client_key having count(*)>1)x")
        active=lab.q(c,"select count(*)from orders where client_key like 'soak_%%' and status not in('delivered','cancelled','rejected')")
        top=c.execute("select calls,round(total_exec_time::numeric,2),round(mean_exec_time::numeric,3),left(query,160)from pg_stat_statements where query not like '%pg_stat_statements%' order by total_exec_time desc limit 8").fetchall()
        counters=c.execute("select deadlocks,temp_bytes,numbackends from pg_stat_database where datname=current_database()").fetchone()
    result={'source':os.environ.get('GITHUB_SHA'),'live':False,'environment':'native PostgreSQL17.6 + GoTrue2.197 + PostgREST14.18; GitHub Linux VM loopback','duration_s':round(duration,2),'order_concurrency':3,'polling_sessions':8,'poll_intervals_s':{'customer':25,'merchant_driver_admin':10},'polling_matches_ordersQuery_filters_and_limits':True,'gps_interval_s':8,'planned_journeys':18,'completed_journeys':len(completed),'confirmed_delivered':confirmed,'duplicate_keys':duplicate,'remaining_active':active,'requests':len(metrics),'read_polls':sum(x['path']=='/orders'for x in metrics),'rps':round(len(metrics)/duration,2),'http_error_rate':sum(x['status']not in(200,204)for x in metrics)/len(metrics),'p50_ms':pct(.5),'p95_ms':pct(.95),'p99_ms':pct(.99),'max_ms':round(max(values),2),'failures':failures,'db_top_queries':top,'db_counters':dict(zip(['deadlocks','temp_bytes','active_connections_at_end'],counters)),'limits':['3 minute sustained mixed lab only, not hours/day endurance','no WAN, real devices, Realtime, photos, production plan','admin assignment, offer claim covered separately','no new settlement or old closed tests'],'production_capacity_claim':False}
    result['lab_p95_budget_ms']=2000
    result['pass']=confirmed==18 and duplicate==0 and active==0 and not failures and result['http_error_rate']==0 and result['p95_ms']<=2000
    lab.save(lab.HERE/'result-soak.json',result);print(json.dumps({k:v for k,v in result.items()if k!='db_top_queries'},default=str),flush=True)
    if not result['pass']:raise SystemExit(1)

if __name__=='__main__':main()
