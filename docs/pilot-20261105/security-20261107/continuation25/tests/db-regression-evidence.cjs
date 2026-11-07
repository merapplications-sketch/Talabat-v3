const fs=require('node:fs'),crypto=require('node:crypto'),assert=require('node:assert/strict');
const base='security/db/',a=JSON.parse(fs.readFileSync(base+'tested-evidence.json'));
assert.equal(a.project,'fsvrsvqfknogwmhccera');
for(const [p,h]of Object.entries(a.sha256))assert.equal(crypto.createHash('sha256').update(fs.readFileSync(base+p)).digest('hex'),h,`DB evidence stale: ${p}; rerun authorized rollback test and review before updating attestation`);
for(const file of ['cash-after.json','price-after.json'])for(const r of JSON.parse(fs.readFileSync(base+file))[0].results){const good=['0','40','10.25'].includes(r.input);assert.equal(r.outcome==='accepted_then_rolled_back',good);assert.equal((r.stored??r.stored_cash)!=null,good);}
const cleanup=JSON.parse(fs.readFileSync(base+'cash-rollback.json'))[0].verification;
assert.equal(cleanup.synthetic_auth_remaining,0);assert.equal(cleanup.synthetic_order_remaining,0);assert.equal(cleanup.synthetic_store_remaining,0);assert.equal(cleanup.synthetic_allowlist_remaining,false);
assert.equal(cleanup.protected_orders.find(x=>x.id===3).settled,null);
console.log('PASS: hashes bind DB migrations/tests to recorded rollback evidence; this does not rerun live SQL');
