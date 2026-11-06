import sys,pathlib,json,uuid,concurrent.futures
sys.path.insert(0,str(pathlib.Path(__file__).resolve().parents[1]))
import lab
p=lab.ROOT/'docs/pilot-20261105/cash/result.json';v=json.loads(p.read_text());assert v['pass']
with lab.db() as c:
 for x in v['scenarios']:
  row=c.execute('select o.payment,o.total,o.cash_collected,o.cash_settled_at is not null,r.paid,r.payment_ref,o.cash_platform_share,o.cash_driver_delivery_share,o.driver_payout,o.commission from orders o join return_private.cases r on r.order_id=o.id where o.id=%s',(x['order'],)).fetchone()
  assert row==('cash',40,40,x['platform']>0,25,'DEMO-CASH-PAY-25',x['platform'],15-x['platform'],15-x['platform'],5),row
  try:c.execute('update orders set cash_platform_share=0,cash_driver_delivery_share=15 where id=%s',(v['scenarios'][0]['order'],));raise AssertionError('snapshot mutated')
  except Exception as e:assert 'cash_allocation_immutable' in str(e),str(e)
 assert lab.q(c,'select count(*) from finance_private.commands')==1
 assert lab.q(c,'select count(*) from finance_private.settlement_receipts')==1
 assert lab.q(c,'select amount from finance_private.settlement_receipts')==5
 assert lab.q(c,'select count(*) from wallet_entries')==0
 assert lab.q(c,'select count(*) from return_private.refunds')==0
args={'p_request':v['receipt']['request'],'p_operation':'settle_cash','p_target':lab.uid('driver1')}
with concurrent.futures.ThreadPoolExecutor(max_workers=6) as pool:
 replies=list(pool.map(lambda _:lab.rpc(lab.bearer('accountant'),'finance_execute',args),range(6)))
assert all(r['amount']==5 and r['receipt']['number']==v['receipt']['number'] for r in replies)
args['p_request']=str(uuid.uuid4())
try:lab.rpc(lab.bearer('accountant'),'finance_execute',args);raise AssertionError('duplicate settled')
except Exception as e:assert 'nothing_to_settle' in str(e),str(e)
for who in ['driver1','merchant','customer']:
 try:lab.rpc(lab.bearer(who),'finance_execute',args);raise AssertionError('unauthorized settlement')
 except Exception as e:assert 'not_allowed' in str(e),str(e)
with lab.db() as c:
 assert lab.q(c,'select count(*) from finance_private.commands')==1
 assert lab.q(c,'select count(*) from finance_private.settlement_receipts')==1
 assert lab.q(c,'select sum(balance) from cash_balances()') in (None,0)
v['database_evidence']={'scenarios':v['scenarios'],'meal_advance_each':25,'gross_each':40,'platform_receipt':5,'restaurant_commission_each_separate':5,'snapshot_survives_policy_change':True,'snapshot_mutation_rejected':True,'concurrent_same_request_retries':6,'new_request_cannot_settle_again':True,'unauthorized_roles_rejected':True,'one_receipt_one_command':True,'wallet_movements':0,'refunds_created':0}
lab.save(p,v);print('CASH_FINAL='+__import__('base64').b64encode(__import__('zlib').compress(json.dumps(v).encode())).decode())
