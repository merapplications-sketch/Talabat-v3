const fs=require('node:fs'),assert=require('node:assert/strict');
const r=JSON.parse(fs.readFileSync(process.argv[2]))[0].result;
assert.equal(r.active_stats,2);assert.equal(r.active_create,true);
assert.deepEqual(r.active_sync,{added:0,updated:0});assert.equal(r.foreign_denied,true);
assert.equal(r.banned_enabled,false);assert.equal(r.banned_stats,0,'disabled owner must not read brand stats');
assert.equal(r.banned_create_accepted,false);assert.equal(r.banned_create_error,'account_blocked');
assert.equal(r.banned_sync_result,null);assert.equal(r.banned_sync_error,'account_blocked');
console.log('PASS: three brand operations deny banned owner, preserve active owner and deny foreign owner');
if(r.session_cases){
 assert.deepEqual(r.session_cases.map(x=>x.case),['reenabled_revoked','required_mfa_aal1','new_active_aal2']);
 for(const c of r.session_cases){const permitted=c.case==='new_active_aal2';assert.equal(c.allowed,permitted);assert.equal(c.create_accepted,permitted);assert.equal(c.sync_accepted,permitted);assert.equal(c.stats_rows,permitted?3:0);}
 console.log('PASS: reactivation preserves revocation, required MFA AAL1 denied, new AAL2 permitted');
}
