const fs=require('node:fs'),crypto=require('node:crypto'),assert=require('node:assert/strict');
const base='security/db/',a=JSON.parse(fs.readFileSync(base+'tested-evidence.json'));
assert.equal(a.project,'fsvrsvqfknogwmhccera');
for(const [p,h]of Object.entries(a.sha256))assert.equal(crypto.createHash('sha256').update(fs.readFileSync(base+p)).digest('hex'),h,`DB evidence stale: ${p}; rerun authorized rollback test and review before updating attestation`);
for(const file of ['cash-after.json','price-after.json'])for(const r of JSON.parse(fs.readFileSync(base+file))[0].results){const good=['0','40','10.25'].includes(r.input);assert.equal(r.outcome==='accepted_then_rolled_back',good);assert.equal((r.stored??r.stored_cash)!=null,good);}
const cleanup=JSON.parse(fs.readFileSync(base+'cash-rollback.json'))[0].verification;
assert.equal(cleanup.synthetic_auth_remaining,0);assert.equal(cleanup.synthetic_order_remaining,0);assert.equal(cleanup.synthetic_store_remaining,0);assert.equal(cleanup.synthetic_allowlist_remaining,false);
assert.equal(cleanup.protected_orders.find(x=>x.id===3).settled,null);
console.log('PASS: hashes bind DB migrations/tests to recorded rollback evidence; this does not rerun live SQL');

const rr=JSON.parse(fs.readFileSync(base+'return-replay-regression.json'))[0].result;
assert.equal(rr.active.synthetic_marker,'cached_return');assert.equal(rr.banned.accepted,false);assert.equal(rr.banned.error,'not_allowed');
for(const r of rr.cases){assert.equal(r.accepted,r.case==='new_active_aal2');if(!r.accepted)assert.equal(r.error,'not_allowed');}
assert.deepEqual(rr.cases.map(r=>r.case),['reenabled_revoked','mfa_aal1','new_active_aal2']);
const rc=JSON.parse(fs.readFileSync(base+'return-cleanup.json'))[0].cleanup;
for(const [k,v]of Object.entries(rc))assert.equal(v,k==='pilot_restored'?true:0);
const guard=fs.readFileSync(base+'pilot_return_action_account_guard.sql','utf8');
assert.ok(guard.indexOf("if v_actor is null or not public.account_enabled() then raise exception 'not_allowed'; end if;")>0);
assert.ok(guard.indexOf('not public.account_enabled()')<guard.indexOf('select * into prior'));
console.log('PASS: return replay guard and active/revoked/MFA rollback evidence bound; live rerun remains separate');

const ar=JSON.parse(fs.readFileSync(base+'approval-replay-after.json'))[0].result;
for(const op of ['customer','merchant']){assert.equal(ar.active[op].accepted,true);assert.equal(ar.banned[op].accepted,false);assert.equal(ar.banned[op].error,'not_allowed');}
const ag=fs.readFileSync(base+'pilot_approval_account_guard.sql','utf8');
assert.equal((ag.match(/if not public\.account_enabled\(\) then raise exception 'not_allowed'; end if;/g)||[]).length,2);
console.log('PASS: customer/merchant approval replay active and banned evidence bound');

const mr=JSON.parse(fs.readFileSync(base+'merchant-role-after.json'))[0].result;
assert.equal(mr.active.owns_store,true);assert.equal(mr.active.merchant.accepted,true);assert.equal(mr.role_removed.owns_store,false);assert.equal(mr.role_removed.merchant.accepted,false);assert.equal(mr.role_removed.customer.accepted,true);
const cr=JSON.parse(fs.readFileSync(base+'return-role-after.json'))[0].result;
assert.equal(cr.active.synthetic_marker,'cached_return');assert.equal(cr.role_removed.accepted,false);assert.equal(cr.role_removed.error,'not_allowed');assert.equal(cr.account_banned,false);
const currentReturn=fs.readFileSync(base+a.latest_rpc_migrations.order_return_action,'utf8');
assert.ok(currentReturn.indexOf('case p_action')<currentReturn.indexOf('return prior.result'));
assert.ok(currentReturn.indexOf('not public.account_enabled()')<currentReturn.indexOf('return prior.result'));
const currentMerchant=fs.readFileSync(base+a.latest_rpc_migrations.merchant_review_order,'utf8');assert.ok(currentMerchant.indexOf('current_order.id=p_order')<currentMerchant.indexOf('return r.result'));
console.log('PASS: current resource access precedes cached merchant/return results; allowed ownership retained');
