/* Changed functions/ACL only, fixed loopback retained synthetic fixture. No financial suites rerun. */
const fs=require('fs'),path=require('path'),assert=require('assert'),{Client}=require('/tmp/talabot-finance-pg/node_modules/pg');
const root=path.resolve(__dirname,'../..'),out=path.join(root,'docs/continuity/admin-finance-fix'),checks=[];
function ok(v,n){assert(v,n);checks.push(n);console.log('PASS',n)}
(async()=>{const c=new Client({host:'127.0.0.1',port:55439,user:'nobody',database:'postgres'});await c.connect();try{
// Deliberately grant both table and column access via PUBLIC in this disposable fixture.
await c.query('grant update on orders to public; grant update(cash_settled_at) on orders to public,authenticated; grant insert(amount),update(amount) on wallet_entries to public,authenticated');
await c.query(fs.readFileSync(path.join(root,'sql/proposed/admin_finance_integrity_20261101.sql'),'utf8'));
await c.query('begin');const A='10000000-0000-0000-0000-000000000002',D='10000000-0000-0000-0000-000000000004';
await c.query('update staff_members set active=true where user_id=$1',[A]);
await c.query("insert into orders(id,driver_id,status,cash_collected,cash_settled_at) values(910001,$1,'delivered',1,'2026-01-01T09:00:00.123456Z'),(910002,$1,'delivered',1,'2026-02-01T09:00:00Z')",[D]);
await c.query("insert into audit_log(user_id,at,table_name,row_id,details) values($1,'2026-01-01T09:00:00Z','orders','910001','{\"cash_settled_at\":{\"to\":\"2026-01-01T14:00:00.123456+05:00\"},\"secret\":\"not exposed\"}'),($1,now(),'orders','910001','{\"cash_settled_at\":{\"to\":\"2026-01-01T09:00:00.123455Z\"}}'),($1,now(),'orders','910001','{\"cash_settled_at\":{\"to\":\"invalid date\"}}')",[A]);
await c.query("insert into audit_log(at,table_name,row_id,details) select now(),'other',n::text,'{}' from generate_series(1,150) n");
await c.query('set local role authenticated');await c.query("select set_config('request.jwt.claim.sub',$1,true)",[A]);
const rows=(await c.query('select * from finance_settlement_events($1::text[])',[['910001','910002']])).rows;
ok(rows.length===1&&rows[0].row_id==='910001'&&rows[0].user_id===A,'old event outside global window found for displayed order');
ok(rows[0].details.cash_settled_at.to.endsWith('+05:00'),'timezone and microsecond exact matching chooses actual recorded event');
ok(!('secret' in rows[0].details),'attribution projection excludes unrelated historical details');
ok((await c.query('select * from finance_settlement_events($1::text[])',[['910002']])).rowCount===0,'missing event is empty without inventing actor');
ok((await c.query('select * from finance_settlement_events($1::text[])',[Array(30).fill('910002').concat('910001')])).rowCount===0,'request restricted to first 30 displayed order ids');
let access=(await c.query('select finance_access() a')).rows[0].a;ok(access.version===2&&access.execute&&access.capabilities.includes('settlement_events'),'v2 contract identifies delegated accountant and changed reader');
await c.query("select set_config('request.jwt.claim.sub','10000000-0000-0000-0000-000000000005',true)");ok((await c.query('select * from finance_settlement_events($1::text[])',[['910001']])).rowCount===0,'unprivileged customer cannot read settlement actor');
await c.query("select set_config('request.jwt.claim.sub','10000000-0000-0000-0000-000000000001',true)");access=(await c.query('select finance_access() a')).rows[0].a;ok(!access.execute,'admin role alone still cannot execute with v2');ok((await c.query('select * from finance_settlement_events($1::text[])',[['910001']])).rowCount===1,'admin read-only history remains available');
await c.query('reset role');
for(const role of ['anon','authenticated']){let v=(await c.query("select has_table_privilege($1,'orders','UPDATE') t,has_column_privilege($1,'orders','cash_settled_at','UPDATE') u,has_column_privilege($1,'wallet_entries','amount','INSERT') i,has_column_privilege($1,'wallet_entries','amount','UPDATE') w",[role])).rows[0];ok(!v.t&&!v.u&&!v.i&&!v.w,role+' cannot bypass through PUBLIC table or column ACL');}
ok(!(await c.query("select has_function_privilege('anon','finance_settlement_events(text[])','EXECUTE') v")).rows[0].v,'anonymous settlement reader execute denied');
ok(!(await c.query("select has_function_privilege('authenticated','finance_private.settlement_time(text)','EXECUTE') v")).rows[0].v,'private parsing helper not exposed');
await c.query('rollback');fs.writeFileSync(path.join(out,'attribution-pg-results.json'),JSON.stringify({checks:checks.length,results:checks,version:(await c.query('select version() v')).rows[0].v,live:false,scope:'Changed reader/capability/ACL on retained local synthetic PG fixture only. Prior 28 checks not rerun.'},null,2)+'\n');
}finally{await c.end()}})().catch(e=>{console.error(e);process.exit(1)});
