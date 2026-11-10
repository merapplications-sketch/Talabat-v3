import {test} from 'node:test';import assert from 'node:assert/strict';
const m=await import('./gate.mjs').catch(()=>({}));
test('acceptance evaluator exists',()=>assert.equal(typeof m.evaluate,'function'));
if(m.evaluate){
 const sha='a'.repeat(40),names=['publicCI','privateDB','hostedRBAC','roleE2E','storageRevocation','providerRecovery','safariDevice','sqlQA'];
 const valid=()=>Object.fromEntries(names.map(n=>[n,{status:'passed',commit:sha,evidence:'private://review/'+n,kind:'actual'}]));
 test('every mandatory gate blocks when absent, failed, skipped or simulated',()=>{for(const n of names)for(const status of [undefined,'failed','skipped','blocked']){const x=valid();if(status)x[n].status=status;else delete x[n];assert.equal(m.evaluate(sha,x).eligible,false,n)}for(const n of ['hostedRBAC','roleE2E','storageRevocation','providerRecovery','safariDevice']){const x=valid();x[n].kind='mock';assert.equal(m.evaluate(sha,x).eligible,false,n)}});
 test('wrong commit and absent evidence cannot qualify',()=>{for(const n of names){const x=valid();x[n].commit='b'.repeat(40);assert.equal(m.evaluate(sha,x).eligible,false);x[n].commit=sha;x[n].evidence='';assert.equal(m.evaluate(sha,x).eligible,false)}});
 test('complete evidence qualifies only for independent review, never production READY',()=>{const r=m.evaluate(sha,valid());assert.equal(r.eligible,true);assert.equal(r.status,'REQUIRES_INDEPENDENT_REVIEW');assert.equal(r.productionReady,false)});
 test('malformed inputs fail closed',()=>{for(const x of [null,[],42,'x'])assert.equal(m.evaluate(sha,x).eligible,false);assert.equal(m.evaluate('bad',valid()).eligible,false)});
}
