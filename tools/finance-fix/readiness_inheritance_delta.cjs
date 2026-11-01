/* Only the new inherited-grant guard on the retained local snapshot clone. */
const fs=require('fs'),path=require('path'),assert=require('assert'),{Client}=require('/tmp/talabot-finance-pg/node_modules/pg');
(async()=>{const c=new Client({host:'127.0.0.1',port:55439,user:'nobody',database:'talabot_readiness_lab'});await c.connect();const root=path.resolve(__dirname,'../..'),results=[];try{
await c.query('create role finance_readiness_inherited nologin');await c.query('grant finance_readiness_inherited to authenticated');await c.query('grant update on orders to finance_readiness_inherited');
const before=(await c.query("select pg_get_functiondef('finance_access()'::regprocedure) d")).rows[0].d;
try{await c.query(fs.readFileSync(path.join(root,'sql/proposed/admin_finance_integrity_20261101.sql'),'utf8'));throw Error('unexpected accepted inherited grant')}catch(e){assert.equal(e.message,'finance_inherited_acl_conflict');results.push('inherited write privilege aborts proposal with explicit conflict');await c.query('rollback')}
assert.equal((await c.query("select pg_get_functiondef('finance_access()'::regprocedure) d")).rows[0].d,before);results.push('failed deployment rolls capability change back atomically');
assert.equal((await c.query('select count(*) n from finance_private.commands')).rows[0].n,'1');results.push('failed deployment preserves existing command evidence');
await c.query('revoke finance_readiness_inherited from authenticated');await c.query('revoke all on orders from finance_readiness_inherited');await c.query('drop role finance_readiness_inherited');assert.equal((await c.query("select has_any_column_privilege('authenticated','orders','UPDATE') v")).rows[0].v,false);results.push('synthetic inherited grant removed; no residual client write');
fs.writeFileSync(path.join(root,'docs/continuity/admin-finance-readiness/inheritance-delta-results.json'),JSON.stringify({checks:results.length,results,live:false},null,2)+'\n');console.log('PASS',results.length,'inheritance guard checks');
}finally{await c.end()}})().catch(e=>{console.error(e);process.exit(1)});
