const fs=require('fs'),path=require('path'),assert=require('assert');
const base=process.env.BASE_LAB_DIR||path.resolve(__dirname,'base-lab');const {PGlite}=require(path.join(base,'node_modules/@electric-sql/pglite'));const out=path.join(__dirname,'evidence');fs.mkdirSync(out,{recursive:true});
const checks=[],save=(n,x)=>fs.writeFileSync(path.join(out,n+'.json'),JSON.stringify(x,null,2)+'\n'),ok=(v,n)=>{assert(v,n);checks.push({name:n,pass:true})};
(async()=>{const db=new PGlite();const ids=JSON.parse(fs.readFileSync(path.join(base,'web/ids.json')));const actor=(id,sql,args=[])=>db.transaction(async tx=>{await tx.exec('set local role authenticated');await tx.query("select set_config('request.jwt.claim.sub',$1,true)",[id]);return tx.query(sql,args)});const call=(id,fn,args)=>actor(id,'select '+fn+'($1,$2,$3,$4,$5) v',args).then(r=>r.rows[0].v);const key='b0000000-0000-4000-8000-000000000001',key2='b0000000-0000-4000-8000-000000000002';
try{
for(const n of ['bootstrap','seed','patch-a'])await db.exec(fs.readFileSync(path.join(base,'web',n+'.sql'),'utf8'));
await actor(ids.admin,'select staff_set($1,$2,true)',['accountant@synthetic.invalid',['finance']]);
await db.query("insert into orders(id,store_id,customer_id,driver_id,status,payment,cash_collected,cash_settled_at,done_at) overriding system value values(7000,$1,$2,$3,'delivered','cash',19,'2026-11-01T10:00:00Z',now())",[ids.store,ids.customer,ids.driver]);
const legacyBefore=(await db.query('select cash_settled_at from orders where id=7000')).rows;
await db.exec(fs.readFileSync(path.resolve(__dirname,'../sql/proposed/admin_finance_receipts_20261102.sql'),'utf8'));
ok((await db.query('select count(*) n from finance_private.settlement_receipts')).rows[0].n===0,'R1 creates no historical receipts');
const result=await call(ids.accountant,'finance_execute',[key,'settle_cash',ids.driver,null,null]);save('issued',result);
ok(result.receipt.number==='TS-000000000001'&&result.receipt.amount===57&&result.receipt.currency==='TJS'&&result.receipt.driver===ids.driver&&result.receipt.actor===ids.accountant&&result.receipt.request===key,'receipt has unique number, exact amount, currency, driver, actor and request');
ok(result.receipt.orders.length===1&&result.receipt.orders[0].id==='7001'&&result.receipt.orders[0].amount===57&&Date.parse(result.receipt.at)===Date.parse(result.at),'receipt snapshots exact included orders and command server timestamp');
const replay=await call(ids.accountant,'finance_execute',[key,'settle_cash',ids.driver,null,null]);const status=(await actor(ids.accountant,'select finance_command_status($1) v',[key])).rows[0].v;
ok(JSON.stringify(result)===JSON.stringify(replay)&&JSON.stringify(result)===JSON.stringify(status),'same key replay and status return identical stored receipt');
ok((await db.query('select count(*) n from finance_private.settlement_receipts')).rows[0].n===1&&(await db.query('select count(*) n from finance_private.commands')).rows[0].n===1,'replay adds no receipt or command');
await db.query("insert into orders(id,store_id,customer_id,driver_id,status,payment,cash_collected,done_at) overriding system value values(7002,$1,$2,$3,'delivered','cash',43,now())",[ids.store,ids.customer,ids.driver]);
await db.exec("create function finance_private.lab_fail() returns trigger language plpgsql as $$begin raise exception 'synthetic_receipt_failure';end$$;create trigger lab_fail before insert on finance_private.settlement_receipts for each row execute function finance_private.lab_fail()");
try{await call(ids.accountant,'finance_execute',[key2,'settle_cash',ids.driver,null,null]);throw Error('unexpected accepted')}catch(e){ok(e.message==='synthetic_receipt_failure','receipt storage failure propagates');}
ok((await db.query('select cash_settled_at from orders where id=7002')).rows[0].cash_settled_at===null&&(await db.query('select count(*) n from finance_private.commands where request=$1',[key2])).rows[0].n===0&&(await db.query('select count(*) n from finance_private.settlement_receipts')).rows[0].n===1,'storage failure rolls back settlement, command and receipt atomically');
await db.exec('drop trigger lab_fail on finance_private.settlement_receipts;drop function finance_private.lab_fail()');
const second=await call(ids.accountant,'finance_execute',[key2,'settle_cash',ids.driver,null,null]);
ok(second.receipt.number!==result.receipt.number&&(await db.query('select count(*) n from finance_private.settlement_receipt_orders')).rows[0].n===2,'retry after rollback produces one unique receipt and one link per order; number gaps allowed');
const hist=(await actor(ids.driver,'select * from finance_settlement_receipts($1)',[['7000','7001','7002']])).rows;
ok(hist.length===2&&hist.every(r=>r.receipt.driver===ids.driver)&&!hist.some(r=>r.order_id==='7000'),'driver can read only issued own receipts; old settlement has none');
ok((await actor(ids.customer,'select * from finance_settlement_receipts($1)',[['7001','7002']])).rows.length===0,'other person cannot read driver receipts');
for(const sql of ['select * from finance_private.settlement_receipts','select finance_private.receipt_json(1)']){try{await actor(ids.accountant,sql);throw Error('unexpected accepted')}catch(e){ok(/permission denied/.test(e.message),'private receipt storage/helper not exposed: '+sql)}}
try{await db.exec("update finance_private.settlement_receipts set amount=1");throw Error('unexpected accepted')}catch(e){ok(e.message==='receipt_immutable','issued receipt immutable even through owner SQL mutation');}
await db.query("update profiles set name='Renamed later' where id=$1",[ids.accountant]);await actor(ids.admin,'select staff_set($1,$2,false)',['accountant@synthetic.invalid',['finance']]);
const frozen=(await actor(ids.driver,'select * from finance_settlement_receipts($1)',[['7001']])).rows[0].receipt;
ok(frozen.actor_name===result.receipt.actor_name&&frozen.actor===ids.accountant&&JSON.stringify(frozen)===JSON.stringify(result.receipt),'rename/revocation preserves receipt name snapshot, historical actor and content');
const delegation=(await db.query("select user_id,at,action from audit_log where action='STAFF_SET' order by id")).rows;
ok(delegation.length===2&&delegation.every(r=>r.user_id===ids.admin&&r.at),'grant and withdrawal record authorized actor and server time');
try{await actor(ids.driver,'select staff_set($1,$2,true)',['accountant@synthetic.invalid',['finance']]);throw Error('unexpected accepted')}catch(e){ok(e.message==='not_allowed','unauthorized person cannot grant finance');}
ok(JSON.stringify((await db.query('select cash_settled_at from orders where id=7000')).rows)===JSON.stringify(legacyBefore),'legacy settlement timestamp remains untouched');
save('sql-result',{pass:true,checks,engine:(await db.query('select version() v')).rows[0].v,first:result.receipt,second:second.receipt,history:hist,delegation,live:false});
}catch(e){save('sql-failure',{message:e.message,stack:e.stack,checks});console.error(e);process.exitCode=1}finally{await db.close()}})();
