import sys,pathlib,importlib.util,json
sys.path.insert(0,str(pathlib.Path(__file__).resolve().parents[1]))
import lab
spec=importlib.util.spec_from_file_location('returns',lab.HERE/'driver-returns.py');r=importlib.util.module_from_spec(spec);spec.loader.exec_module(r)
r.setup();r.agreement()
# Existing synthetic accountant fixture only; never provision a real authorization.
print('Synthetic admission and restaurant agreement ready; no order created.')

with lab.db() as c:
 c.execute("insert into finance_private.cash_delivery_policy values(%s,5,'DEMO owner example 10/5')",(lab.STORE,))

# Resume only unfinished UI scope; earlier successful UI evidence remains in run42179733573.
import os,uuid
if os.environ.get('CASH_ALLOCATION_RESUME')=='1':
 scenarios=[];receipt=None
 for share in [5,0]:
  with lab.db() as c:c.execute('update finance_private.cash_delivery_policy set platform_amount=%s,reference=%s where store_id=%s',(share,'DEMO resume '+str(share),lab.STORE))
  oid=lab.rpc(lab.bearer('customer'),'place_order',{'p_store':lab.STORE,'p_items':[{'item_id':lab.ITEM,'qty':1}],'p_payment':'cash','p_address':'DEMO Rudaki 1','p_lat':lab.LAT,'p_lng':lab.LNG,'p_key':'cash_allocation_'+str(share)})
  with lab.db() as c:c.execute('update finance_private.cash_delivery_policy set platform_amount=%s where store_id=%s',(0 if share else 5,lab.STORE))
  offer=r.cf.review(oid,15)
  if offer['needs_customer']:r.cf.confirm(lab.bearer('customer'),oid,offer['revision'])
  else:lab.rpc(lab.bearer('merchant'),'set_order_status',{'p_id':oid,'p_to':'preparing'})
  lab.rpc(lab.bearer('admin'),'admin_assign_driver',{'p_order':oid,'p_driver':lab.uid('driver1')})
  lab.rpc(lab.bearer('merchant'),'set_order_status',{'p_id':oid,'p_to':'ready'})
  lab.rpc(lab.bearer('driver1'),'set_order_status',{'p_id':oid,'p_to':'pickedup'})
  if share:
   r.act('driver1',oid,'depart','DEMO-CASH-PAY-25-5',25)
   lab.rpc(lab.bearer('driver1'),'deliver_order',{'p_id':oid,'p_cash':40})
   receipt=lab.rpc(lab.bearer('accountant'),'finance_execute',{'p_request':str(uuid.uuid4()),'p_operation':'settle_cash','p_target':lab.uid('driver1')})['receipt']
  scenarios.append({'order':oid,'platform':share})
 lab.save(lab.HERE/'.runtime-cash-order.json',{'scenarios':scenarios,'receipt':receipt})
 print('Reconstructed prior successful states via original RPC; continuing zero-share payment screen only.')
