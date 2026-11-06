import sys,pathlib,importlib.util,json
sys.path.insert(0,str(pathlib.Path(__file__).resolve().parents[1]))
import lab
spec=importlib.util.spec_from_file_location('returns',lab.HERE/'driver-returns.py');r=importlib.util.module_from_spec(spec);spec.loader.exec_module(r)
r.setup();r.agreement()
# Existing synthetic accountant fixture only; never provision a real authorization.
print('Synthetic admission and restaurant agreement ready; no order created.')

import os
if os.environ.get('CASH_SETTLEMENT_ONLY')=='1':
 oid=lab.rpc(lab.bearer('customer'),'place_order',{'p_store':lab.STORE,'p_items':[{'item_id':lab.ITEM,'qty':1}],'p_payment':'cash','p_address':'DEMO Rudaki 1','p_lat':lab.LAT,'p_lng':lab.LNG,'p_key':'cash_settlement_fixture'})
 offer=r.cf.review(oid,15)
 if offer['needs_customer']:r.cf.confirm(lab.bearer('customer'),oid,offer['revision'])
 lab.rpc(lab.bearer('admin'),'admin_assign_driver',{'p_order':oid,'p_driver':lab.uid('driver1')})
 lab.rpc(lab.bearer('merchant'),'set_order_status',{'p_id':oid,'p_to':'ready'})
 lab.rpc(lab.bearer('driver1'),'set_order_status',{'p_id':oid,'p_to':'pickedup'})
 r.act('driver1',oid,'depart','DEMO-CASH-PAY-25',25)
 lab.rpc(lab.bearer('driver1'),'deliver_order',{'p_id':oid,'p_cash':40})
 lab.save(lab.HERE/'.runtime-cash-order.json',{'order':oid})
 print('Prepared delivered fixture for unfinished accountant screen only; prior UI checks not rerun.')
