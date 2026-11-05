"""Only new confirmation contract, real GoTrue JWTs/PostgREST/native PG. No live."""
import concurrent.futures,json,os,threading,uuid,traceback
import lab
RESULT={'source':os.environ.get('GITHUB_SHA'),'live':False,'engine':'native PostgreSQL17.6 + GoTrue2.197 + PostgREST14.18','checks':[]}

def save():lab.save(lab.HERE/'result-confirmation.json',RESULT)
def ok(value,name,evidence=None):
 assert value,name
 RESULT['checks'].append({'name':name,'pass':True,'evidence':evidence});save();print('PASS confirmation '+name,flush=True)
def fresh(name,n):
 s=lab.state();s['accounts'][name]=lab.register(name,n,admin=True);lab.save(lab.STATE,s);return lab.bearer(name)
def state(token,oid):return lab.rpc(token,'order_approval_states',{'p_order_ids':[oid]})[0]
def review(oid,minutes,items=None,key=None):return lab.rpc(lab.bearer('merchant'),'merchant_review_order',{'p_order':oid,'p_minutes':minutes,'p_request':key or str(uuid.uuid4()),'p_items':items,'p_note':'SYNTHETIC review'})
def confirm(token,oid,rev,key=None):return lab.rpc(token,'customer_confirm_order',{'p_order':oid,'p_revision':rev,'p_request':key or str(uuid.uuid4())})
def denied(token,fn,args,message=None):
 code,value=lab.request(3000,'/rpc/'+fn,args,token)
 assert code>=400,(fn,code)
 if message:assert value.get('message')==message,(fn,value)
 return {'status':code,'message':value.get('message')}
def config(timeout=None,delay=None,ta=False,da=False):return lab.rpc(lab.bearer('admin'),'configure_order_confirmation',{'p_timeout_seconds':timeout,'p_material_delay_minutes':delay,'p_timeout_approved':ta,'p_delay_approved':da,'p_enabled':True})

def main():
 lab.wait(lambda:lab.request(3000,'/')[0]==200,'rest')
 try:
  if os.environ.get('CONFIRM_REMAINING'):
   RESULT['prior_passes_preserved']='dcf7aa16de1430c3a8d1400dcfaefceb37dc6f30: first 12 checks; not rerun'
   c=fresh('confirmcustomer',600);oid=lab.order(c);r=review(oid,15);confirm(c,oid,r['revision']) # setup accepted first order
  else:
   settings=lab.rpc(lab.bearer('customer'),'order_confirmation_settings')
   ok(settings['timeout_seconds']is None and settings['material_delay_minutes']is None and not settings['timeout_approved']and not settings['delay_approved'],'numeric policies default to NULL/unapproved; proposals are not activated',settings)
   c=fresh('confirmcustomer',600);oid=lab.order(c)
   a=state(c,oid);ok(a['state']=='awaiting_merchant'and a['first_cash'],'first cash starts blocked before merchant availability')
   denied(lab.bearer('merchant'),'set_order_status',{'p_id':oid,'p_to':'preparing'},'customer_confirmation_required')
   denied(lab.bearer('admin'),'set_order_status',{'p_id':oid,'p_to':'delivered'},'customer_confirmation_required')
   denied(lab.bearer('admin'),'admin_assign_driver',{'p_order':oid,'p_driver':lab.uid('driver1')})
   with lab.db()as db:ok(db.execute('select status,driver_id,cash_collected from orders where id=%s',(oid,)).fetchone()[0:2]==('pending',None),'old merchant/admin/assignment routes cannot prepare or authorize courier before approval')
   denied(c,'customer_confirm_order',{'p_order':oid,'p_revision':0,'p_request':str(uuid.uuid4())},'approval_changed')
   denied(lab.bearer('outsider'),'merchant_review_order',{'p_order':oid,'p_minutes':12,'p_request':str(uuid.uuid4())},'not_allowed')
   key=str(uuid.uuid4());r=review(oid,12,key=key);r2=review(oid,12,key=key);a=state(c,oid)
   ok(r==r2 and a['revision']==1 and a['state']=='awaiting_customer'and a['snapshot']['total']==65 and a['snapshot']['address']=='DEMO Rudaki 1'and a['snapshot']['prep_minutes']==12,'merchant availability stores authoritative total/address/time; same-key replay stable')
   denied(lab.bearer('outsider'),'customer_confirm_order',{'p_order':oid,'p_revision':1,'p_request':str(uuid.uuid4())},'not_allowed')
   ok(lab.rpc(lab.bearer('outsider'),'order_approval_states',{'p_order_ids':[oid]})==[]and lab.rpc(lab.bearer('accountant'),'order_approval_states',{'p_order_ids':[oid]})==[],'cross-customer and finance-only account cannot read approval snapshots')
   denied(c,'place_order',{'p_store':lab.STORE,'p_items':[{'item_id':lab.ITEM,'qty':2}],'p_payment':'cash','p_address':'DEMO Rudaki 1','p_lat':lab.LAT,'p_lng':lab.LNG,'p_key':'second_before_approval','p_fee':15},'first_cash_pending')
   with lab.db()as db:ok(lab.q(db,'select count(*)from orders where customer_id=%s',(lab.uid('confirmcustomer'),))==1,'parallel/extra order cannot bypass first cash by creating a subsequent request')
   r=review(oid,15);denied(c,'customer_confirm_order',{'p_order':oid,'p_revision':1,'p_request':str(uuid.uuid4())},'approval_changed')
   ok(state(c,oid)['revision']==2,'stale customer version cannot accept updated merchant time')
   config(120,10,True,True);review(oid,15)
   with lab.db()as db:db.execute("update fulfillment_private.order_approvals set deadline=now()-interval'1 second'where order_id=%s",(oid,))
   denied(c,'customer_confirm_order',{'p_order':oid,'p_revision':3,'p_request':str(uuid.uuid4())},'confirmation_expired')
   with lab.db()as db:ok(lab.q(db,'select status from orders where id=%s',(oid,))=='pending','expiry never consents, starts preparation, cancels or refunds')
   denied(lab.bearer('accountant'),'configure_order_confirmation',{'p_timeout_seconds':120,'p_material_delay_minutes':10},'not_allowed')
   config();r=review(oid,15);a=state(c,oid);ok(a['deadline']is None,'unapproved timeout remains unscheduled after explicit review renewal')
   request=str(uuid.uuid4());barrier=threading.Barrier(2)
   def accept(_):barrier.wait();return confirm(c,oid,a['revision'],request)
   with concurrent.futures.ThreadPoolExecutor(max_workers=2)as pool:answers=list(pool.map(accept,range(2)))
   with lab.db()as db:events=lab.q(db,"select count(*)from fulfillment_private.approval_events where order_id=%s and kind='customer_confirm'",(oid,));status=lab.q(db,'select status from orders where id=%s',(oid,))
   ok(answers[0]==answers[1]and events==1 and status=='preparing','two actual REST confirmations with one key create one acceptance and one preparation',{'request':request,'responses':answers,'events':events})
   before=answers[0];state(c,oid)
   with lab.db()as db:ok(lab.q(db,"select count(*)from fulfillment_private.approval_events where order_id=%s and kind='customer_confirm'",(oid,))==1,'status recovery is read-only and leaves acceptance effect unchanged')
  oid2=lab.order(c);ok(state(c,oid2)['state']=='checkout_accepted','subsequent unchanged cash uses checkout; no second mandatory approval')
  lab.rpc(lab.bearer('merchant'),'set_prep_time',{'p_id':oid2,'p_min':12});lab.rpc(lab.bearer('merchant'),'set_order_status',{'p_id':oid2,'p_to':'preparing'})
  review(oid2,12);r=review(oid2,18);ok(r['needs_customer']and state(c,oid2)['snapshot']['reason']=='delay_policy_unapproved','unset material-delay policy never silently authorizes an increase')
  denied(lab.bearer('merchant'),'set_order_status',{'p_id':oid2,'p_to':'ready'},'customer_confirmation_required')
  denied(lab.bearer('admin'),'admin_assign_driver',{'p_order':oid2,'p_driver':lab.uid('driver1')},'customer_confirmation_required')
  confirm(c,oid2,r['revision']);config(None,10,False,True)
  small=review(oid2,23);large=review(oid2,28)
  ok(not small['needs_customer']and large['needs_customer'],'configured ten-minute example uses cumulative delay from last customer acceptance; not five-plus-five bypass')
  confirm(c,oid2,large['revision'])
  denied(lab.bearer('merchant'),'set_prep_time',{'p_id':oid2,'p_min':29},'order_change_requires_confirmation')
  with lab.db()as db:db.execute('update menu_items set price=30 where id=%s',(lab.ITEM,))
  items=[{'item_id':lab.ITEM,'qty':3,'options':[]}];quote=lab.rpc(lab.bearer('merchant'),'order_change_quote',{'p_order':oid2,'p_items':items});r=review(oid2,28,items)
  with lab.db()as db:ok(quote['total']==105 and lab.q(db,'select total from orders where id=%s',(oid2,))==65,'item/price proposal is server-priced and does not change cash obligation before acceptance',quote)
  with lab.db()as db:
   try:db.execute('update orders set total=99 where id=%s',(oid2,));raise AssertionError('direct_price_write_allowed')
   except lab.psycopg.Error as e:assert 'order_change_requires_confirmation'in str(e)
   try:db.execute('update order_items set qty=4 where order_id=%s',(oid2,));raise AssertionError('direct_line_write_allowed')
   except lab.psycopg.Error as e:assert 'order_change_requires_confirmation'in str(e)
  ok(True,'direct price/item mutations cannot bypass customer revision acceptance')
  with lab.db()as db:
   baseline=db.execute('select total,subtotal,commission from orders where id=%s',(oid2,)).fetchone()
   db.execute("create function public.confirmation_fail_probe()returns trigger language plpgsql as $$begin if new.kind='customer_confirm'then raise exception'synthetic_confirmation_fail';end if;return new;end$$;create trigger confirmation_fail_probe before insert on fulfillment_private.approval_events for each row execute function public.confirmation_fail_probe()")
  denied(c,'customer_confirm_order',{'p_order':oid2,'p_revision':r['revision'],'p_request':str(uuid.uuid4())},'synthetic_confirmation_fail')
  with lab.db()as db:
   ok(db.execute('select total,subtotal,commission from orders where id=%s',(oid2,)).fetchone()==baseline and state(c,oid2)['state']=='awaiting_customer','acceptance storage failure rolls back applied lines, money fields, state and event together')
   db.execute('drop trigger confirmation_fail_probe on fulfillment_private.approval_events;drop function public.confirmation_fail_probe()')
  confirm(c,oid2,r['revision'])
  with lab.db()as db:ok(db.execute('select total,subtotal,commission,driver_payout from orders where id=%s',(oid2,)).fetchone()==(105,90,18,15),'accepted change atomically stores exact total/lines/commission without changing courier pay')
  config();RESULT['pass']=True;save()
  # Separate fresh identity/order for actual new UI checks, not a rerun of these cases.
  ui=fresh('confirmationui',601);ui_order=lab.order(ui);lab.save(lab.HERE/'.runtime-confirmation-ui.json',{'order':ui_order,'account':'confirmationui'})
 except Exception as e:
  RESULT['pass']=False;RESULT['error']=str(e)[:400];RESULT['traceback']=traceback.format_exc();save();raise

if __name__=='__main__':
 if os.environ.get('CONFIRM_UI_FIXTURE'):
  lab.wait(lambda:lab.request(3000,'/')[0]==200,'rest');ui=fresh('confirmationui',601);oid=lab.order(ui)
  lab.save(lab.HERE/'.runtime-confirmation-ui.json',{'order':oid,'account':'confirmationui'})
 else:main()
