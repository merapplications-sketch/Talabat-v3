"""Only the new upgrade boundary: synthetic historical rows, no live SQL."""
import sys,pathlib,importlib.util,json,uuid,hashlib,os
sys.path.insert(0,str(pathlib.Path(__file__).parent))
import lab
spec=importlib.util.spec_from_file_location('returns',lab.HERE/'driver-returns.py');r=importlib.util.module_from_spec(spec);spec.loader.exec_module(r)
OUT=lab.ROOT/'docs/pilot-20261105/candidate/integration.json'
OUT.parent.mkdir(parents=True,exist_ok=True)
v={'source':os.environ.get('GITHUB_SHA'),'live':False,'checks':[],'prior_closed_run':42183718520 if os.environ.get('CANDIDATE_REMAINING') else None}
remaining=bool(os.environ.get('CANDIDATE_REMAINING'))
def ok(x,name):
 assert x,name
 v['checks'].append(name);lab.save(OUT,v);print('PASS '+name,flush=True)
def snapshot(c):
 return {t:lab.q(c,'select coalesce(jsonb_agg(to_jsonb(t) order by id),\'[]\'::jsonb) from '+t+' t') for t in ['public.orders','finance_private.settlement_receipts','public.wallet_entries']}
r.setup();r.agreement()
# Two synthetic legacy records: settled gross receipt and unsettled balance.
legacy=[]
for i in range(2):
 oid=r.pickup();r.act('driver1',oid,'depart','upgrade-proof-'+str(i),50)
 lab.rpc(lab.bearer('driver1'),'deliver_order',{'p_id':oid,'p_cash':65});legacy.append(oid)
 if i==0:receipt=lab.rpc(lab.bearer('accountant'),'finance_execute',{'p_request':str(uuid.uuid4()),'p_operation':'settle_cash','p_target':lab.uid('driver1')})['receipt']
if not remaining:
 with lab.db() as c:
  before=snapshot(c)
  functions=lab.q(c,"select jsonb_object_agg(p.oid::text,md5(pg_get_functiondef(p.oid))) from pg_proc p join pg_namespace n on n.oid=p.pronamespace where n.nspname='return_private' and p.prokind='f'")
  c.execute((lab.ROOT/'sql/proposed/pilot_zzzz_cash_allocation_20261106.sql').read_text(),prepare=False)
  after=snapshot(c)
  for row in after['public.orders']:
   for k in ['cash_allocation_version','cash_platform_share','cash_driver_delivery_share','cash_allocation_reference']:row.pop(k)
  ok(before==after,'upgrade preserves all pre-existing order fields, receipt rows and wallet rows')
  ok(functions==lab.q(c,"select jsonb_object_agg(p.oid::text,md5(pg_get_functiondef(p.oid))) from pg_proc p join pg_namespace n on n.oid=p.pronamespace where n.nspname='return_private' and p.prokind='f'"),'return function bodies unchanged')
  ok(lab.q(c,"select count(*) from orders where cash_allocation_version is not null")==0,'no historical allocation backfill')
  c.execute('notify pgrst, \'reload schema\'')
 old=lab.rpc(lab.bearer('accountant'),'finance_settlement_receipts',{'p_order_ids':[str(legacy[0])]})[0]['receipt']
 ok(old['amount']==65 and old['basis']=='legacy','legacy receipt retained and labelled historical, never repriced to new delivery share')
 r.cf.denied(lab.bearer('driver1'),'cash_balances',{},'legacy_cash_reconciliation_required')
 r.cf.denied(lab.bearer('accountant'),'finance_execute',{'p_request':str(uuid.uuid4()),'p_operation':'settle_cash','p_target':lab.uid('driver1')},'legacy_cash_reconciliation_required')
 ok(True,'unallocated old debt blocks automatic settlement; no gross reinterpretation')
else:
 with lab.db() as c:c.execute((lab.ROOT/'sql/proposed/pilot_zzzz_cash_allocation_20261106.sql').read_text(),prepare=False)
with lab.db() as c:count=lab.q(c,'select count(*) from orders')
r.cf.denied(lab.bearer('customer'),'place_order',{'p_store':lab.STORE,'p_items':[{'item_id':lab.ITEM,'qty':1}],'p_address':'DEMO Rudaki 1','p_payment':'cash','p_lat':lab.LAT,'p_lng':lab.LNG,'p_key':'candidate_missing_policy'},'cash_allocation_required')
with lab.db() as c:
 ok(count==lab.q(c,'select count(*) from orders'),'missing allocation rejects atomically without partial order')
 c.execute("insert into finance_private.cash_delivery_policy values(%s,5,'DEMO integration only')",(lab.STORE,))
oid=lab.rpc(lab.bearer('customer'),'place_order',{'p_store':lab.STORE,'p_items':[{'item_id':lab.ITEM,'qty':1}],'p_address':'DEMO Rudaki 1','p_payment':'cash','p_lat':lab.LAT,'p_lng':lab.LNG,'p_key':'candidate_new_policy'})
with lab.db() as c:
 ok(c.execute('select cash_platform_share,cash_driver_delivery_share from orders where id=%s',(oid,)).fetchone()==(5,10),'new allocation works alongside untouched legacy orders')
for method in ['card','apple']:
 r.cf.denied(lab.bearer('customer'),'place_order',{'p_store':lab.STORE,'p_items':[{'item_id':lab.ITEM,'qty':1}],'p_address':'DEMO Rudaki 1','p_payment':method,'p_lat':lab.LAT,'p_lng':lab.LNG,'p_key':'candidate_'+method+'_guard'},'payment_not_configured')
ok(True,'combined place_order retains server payment gate; simulation not promoted to live provider')
v['pass']=True;v['historical_fixture_only']=True;v['preserved_legacy_receipt_amount']=65
lab.save(OUT,v);print('CANDIDATE_RESULT='+json.dumps(v))
