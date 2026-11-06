import sys,pathlib,json
sys.path.insert(0,str(pathlib.Path(__file__).resolve().parents[1]))
import lab
p=lab.ROOT/'docs/pilot-20261105/cash/result.json';v=json.loads(p.read_text());assert v['pass'];oid=v['order']
with lab.db() as c:
 row=c.execute('select o.payment,o.total,o.cash_collected,o.cash_settled_at is not null,r.paid,r.payment_ref,r.cancelled_at from orders o join return_private.cases r on r.order_id=o.id where o.id=%s',(oid,)).fetchone()
 assert row==('cash',40,40,True,25,'DEMO-CASH-PAY-25',None),row
 assert lab.q(c,'select count(*) from finance_private.commands')==1
 assert lab.q(c,'select count(*) from finance_private.settlement_receipts')==1
 assert lab.q(c,'select count(*) from wallet_entries')==0
 assert lab.q(c,'select count(*) from return_private.refunds')==0
 v['database_evidence']={'cash_due':40,'cash_collected':40,'office_handover':40,'driver_paid':25,'driver_payment_reference':'DEMO-CASH-PAY-25','one_receipt_one_command':True,'wallet_movements':0,'refunds_created':0,'advance_reimbursed_or_wage_paid':False}
lab.save(p,v);print('CASH_FINAL='+__import__('base64').b64encode(__import__('zlib').compress(json.dumps(v).encode())).decode())
