import sys,pathlib,importlib.util,json
sys.path.insert(0,str(pathlib.Path(__file__).resolve().parents[1]))
import lab
spec=importlib.util.spec_from_file_location('returns',lab.HERE/'driver-returns.py');r=importlib.util.module_from_spec(spec);spec.loader.exec_module(r)
r.setup();r.agreement()
# Existing synthetic accountant fixture only; never provision a real authorization.
print('Synthetic admission and restaurant agreement ready; no order created.')

with lab.db() as c:
 c.execute("insert into finance_private.cash_delivery_policy values(%s,5,'DEMO owner example 10/5')",(lab.STORE,))
