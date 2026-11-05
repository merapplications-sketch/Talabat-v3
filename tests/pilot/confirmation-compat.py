"""NEW activation compatibility edges only; no old functional suites."""
import concurrent.futures,json,threading,uuid,os
import lab,confirmation as cf
r={'source':os.environ.get('GITHUB_SHA'),'live':False,'environment':'native PostgreSQL17 + GoTrue/PostgREST isolated','checks':[]}
def ok(v,n):
 assert v,n
 r['checks'].append({'name':n,'pass':True});lab.save(lab.HERE/'result-confirmation-compat.json',r);print('PASS consent compat '+n,flush=True)
def main():
 lab.wait(lambda:lab.request(3000,'/')[0]==200,'rest');customer=cf.fresh('confirmrace',602);barrier=threading.Barrier(2)
 def place(n):
  barrier.wait();return lab.request(3000,'/rpc/place_order',{'p_store':lab.STORE,'p_items':[{'item_id':lab.ITEM,'qty':2}],'p_payment':'cash','p_address':'SYNTHETIC race','p_lat':lab.LAT,'p_lng':lab.LNG,'p_key':'confirmation_race_'+str(n),'p_fee':15},customer)
 with concurrent.futures.ThreadPoolExecutor(max_workers=2)as pool:responses=list(pool.map(place,[1,2]))
 with lab.db()as db:count=lab.q(db,'select count(*)from orders where customer_id=%s',(lab.uid('confirmrace'),))
 ok(sorted(x[0]for x in responses)==[200,400]and count==1 and any(isinstance(v,dict)and v.get('message')=='first_cash_pending'for _,v in responses),'two different checkout keys racing cannot bypass the first-cash hold')
 with lab.db()as db:
  with db.transaction():
   oid=db.execute("insert into orders(store_id,customer_id,status,payment,subtotal,total,delivery_fee,commission_pct,commission,driver_payout,address)values(%s,%s,'pending','cash',50,65,15,20,10,15,'SYNTHETIC legacy')returning id",(lab.STORE,lab.uid('customer'))).fetchone()[0]
   db.execute('insert into order_items(order_id,item_id,name,price,qty,options)values(%s,%s,%s,25,2,%s)',(oid,lab.ITEM,'DEMO legacy','[]'))
 # New browser will exercise the actual patched core against this previously-existing order.
 lab.save(lab.HERE/'.runtime-confirmation-legacy.json',{'order':oid})
 key=str(uuid.uuid4());a=cf.review(oid,12,key=key);cf.denied(lab.bearer('merchant'),'merchant_review_order',{'p_order':oid,'p_minutes':13,'p_request':key,'p_note':'SYNTHETIC review'},'request_conflict')
 with lab.db()as db:events=lab.q(db,'select count(*)from fulfillment_private.approval_events where order_id=%s',(oid,))
 ok(a['state']=='checkout_accepted'and events==1,'legacy order migration records a current review, no invented historical customer acceptance; changed payload/key conflicts')
 lab.rpc(lab.bearer('admin'),'admin_assign_driver',{'p_order':oid,'p_driver':lab.uid('driver1')}) if False else None
 # Separate native legacy fixtures avoid changing already accepted contract or financial tests.
 for field,value in [('wallet_used',5),('driver_id',lab.uid('driver1'))]:
  with lab.db()as db:
   with db.transaction():
    oid2=db.execute('insert into orders(store_id,customer_id,status,payment,subtotal,total,delivery_fee,'+field+")values(%s,%s,'preparing','cash',50,65,15,%s)returning id",(lab.STORE,lab.uid('customer'),value)).fetchone()[0]
    db.execute('insert into order_items(order_id,item_id,name,price,qty,options)values(%s,%s,%s,25,2,%s)',(oid2,lab.ITEM,'DEMO legacy','[]'))
  cf.denied(lab.bearer('merchant'),'order_change_quote',{'p_order':oid2,'p_items':[{'item_id':lab.ITEM,'qty':3,'options':[]}]},'change_requires_support')
  with lab.db()as db:ok(lab.q(db,'select total from orders where id=%s',(oid2,))==65 and lab.q(db,'select count(*)from fulfillment_private.order_approvals where order_id=%s',(oid2,))==0,field+' reprice fails closed without partial money or approval effects')
 r['pass']=True;lab.save(lab.HERE/'result-confirmation-compat.json',r)
if __name__=='__main__':
 if os.environ.get('CONFIRM_COMPAT_CORE_FIXTURE'):
  lab.wait(lambda:lab.request(3000,'/')[0]==200,'rest')
  with lab.db()as db:
   with db.transaction():
    oid=db.execute("insert into orders(store_id,customer_id,status,payment,subtotal,total,delivery_fee,commission_pct,commission,driver_payout,address)values(%s,%s,'pending','cash',50,65,15,20,10,15,'SYNTHETIC legacy untouched')returning id",(lab.STORE,lab.uid('customer'))).fetchone()[0]
    db.execute('insert into order_items(order_id,item_id,name,price,qty,options)values(%s,%s,%s,25,2,%s)',(oid,lab.ITEM,'DEMO legacy','[]'))
  lab.save(lab.HERE/'.runtime-confirmation-legacy.json',{'order':oid})
 else:main()
