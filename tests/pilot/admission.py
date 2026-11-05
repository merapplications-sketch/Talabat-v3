"""Only new pilot admission gate; synthetic participants and configuration."""
import os,uuid,threading,concurrent.futures,datetime
import lab,confirmation as cf
r={'source':os.environ.get('GITHUB_SHA'),'live':False,'checks':[],'environment':'native PostgreSQL17 GoTrue PostgREST, temporary Linux VM'}
def ok(v,n):
 assert v,n
 r['checks'].append({'name':n,'pass':True});lab.save(lab.HERE/'result-admission.json',r);print('PASS admission '+n,flush=True)
def configure(cfg=None,paused=False):return lab.rpc(lab.bearer('admin'),'configure_pilot_admission',{'p_config':cfg,'p_paused':paused})
def args(n=0,**changes):
 a={'p_store':lab.STORE,'p_items':[{'item_id':lab.ITEM,'qty':2}],'p_payment':'cash','p_address':'SYNTHETIC admission','p_lat':lab.LAT,'p_lng':lab.LNG,'p_key':'admission_'+str(n),'p_fee':15};a.update(changes);return a
def main():
 lab.wait(lambda:lab.request(3000,'/')[0]==200,'rest');c=lab.bearer('customer');cf.denied(c,'place_order',args(),'pilot_paused');ok(True,'unconfigured review candidate blocks new orders by default')
 cf.denied(c,'configure_pilot_admission',{'p_paused':False},'not_allowed');cf.denied(lab.bearer('admin'),'configure_pilot_admission',{'p_config':{},'p_paused':False},'pilot_config_incomplete');ok(True,'configuration is admin-only and incomplete policy cannot open intake')
 now=datetime.datetime.now(datetime.timezone.utc);cfg={'owner_approved':True,'timezone':'UTC','valid_from':(now-datetime.timedelta(hours=1)).isoformat(),'valid_until':(now+datetime.timedelta(hours=2)).isoformat(),'open_minute':0,'close_minute':1440,'max_active':1,'daily_orders':20,'min_lat':38.55,'max_lat':38.57,'min_lng':68.78,'max_lng':68.80,'weekdays':list(range(1,8)),'customers':[lab.uid('customer')],'drivers':[lab.uid('driver1')],'stores':[lab.STORE]}
 configure(cfg);cf.denied(lab.bearer('outsider'),'place_order',args(1),'pilot_not_invited');cf.denied(c,'place_order',args(2,p_lat=38.54),'pilot_region');ok(True,'server enforces invited customer/store and geographical boundary')
 closed={**cfg,'weekdays':[1 if now.isoweekday()!=1 else 2]};configure(closed);cf.denied(c,'place_order',args(3),'pilot_closed');configure(cfg)
 cf.denied(c,'place_order',args(4,p_extra={'at':(now+datetime.timedelta(hours=1)).isoformat()}),'pilot_scheduled_unavailable');ok(True,'server enforces operating days and rejects unreviewed scheduled orders')
 oid=lab.rpc(c,'place_order',args(5));configure(paused=True);cf.denied(c,'place_order',args(6),'pilot_paused');same=lab.rpc(c,'place_order',args(5));ok(same==oid,'pause stops new admissions while same-key recovery returns the existing order')
 configure();a=cf.review(oid,15);cf.confirm(c,oid,a['revision']);cf.denied(lab.bearer('admin'),'admin_assign_driver',{'p_order':oid,'p_driver':lab.uid('driver2')},'pilot_driver_not_invited');configure(paused=True);lab.rpc(lab.bearer('admin'),'admin_assign_driver',{'p_order':oid,'p_driver':lab.uid('driver1')});ok(True,'nonparticipant assignment is rejected; pausing intake still permits authorized handling of existing work')
 # Native cleanup is a fixture transition, never a financial claim/refund.
 with lab.db()as db:db.execute("update orders set status='cancelled'where id=%s",(oid,))
 cfg['daily_orders']=1;configure(cfg);cf.denied(c,'place_order',args(7),'pilot_daily_limit');ok(True,'cancellation does not reset the daily order budget')
 t1=cf.fresh('admitrace1',603);t2=cf.fresh('admitrace2',604);cfg['daily_orders']=20;cfg['customers']+=[lab.uid('admitrace1'),lab.uid('admitrace2')];configure(cfg);barrier=threading.Barrier(2)
 def go(t):barrier.wait();return lab.request(3000,'/rpc/place_order',args(uuid.uuid4().hex),t)
 with concurrent.futures.ThreadPoolExecutor(max_workers=2)as pool:ans=list(pool.map(go,[t1,t2]))
 with lab.db()as db:
  active=lab.q(db,"select count(*)from pilot_private.admissions a join orders o on o.id=a.order_id where o.status in('pending','preparing','ready','pickedup')")
  audit=db.execute('select actor,at from pilot_private.config_events order by id desc limit 1').fetchone()
 ok(sorted(x[0]for x in ans)==[200,400]and active==1 and any(isinstance(v,dict)and v.get('message')=='pilot_capacity'for _,v in ans),'concurrent users cannot overbook the configured active-order ceiling')
 ok(str(audit[0])==lab.uid('admin')and audit[1]is not None,'pilot configuration preserves the independent actor and server time')
 configure(paused=True);r['pass']=True;r['configured_values_are_synthetic_only']=True;lab.save(lab.HERE/'result-admission.json',r)
if __name__=='__main__':main()
