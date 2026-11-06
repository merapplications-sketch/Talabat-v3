import sys,pathlib,importlib.util,json
sys.path.insert(0,str(pathlib.Path(__file__).resolve().parents[1]))
import lab
spec=importlib.util.spec_from_file_location('returns',lab.HERE/'driver-returns.py');r=importlib.util.module_from_spec(spec);spec.loader.exec_module(r)
r.setup();r.agreement()
# Existing synthetic accountant fixture only; never provision a real authorization.
print('Synthetic admission and restaurant agreement ready; no order created.')

import os
if os.environ.get('CASH_SETTLEMENT_ONLY')=='1':
 oid=r.pickup()
 r.act('driver1',oid,'depart','DEMO-CASH-PAY-25',25)
 lab.rpc(lab.bearer('driver1'),'deliver_order',{'p_id':oid,'p_cash':40})
 lab.save(lab.HERE/'.runtime-cash-order.json',{'order':oid})
 print('Prepared delivered fixture for unfinished accountant screen only; prior UI checks not rerun.')
