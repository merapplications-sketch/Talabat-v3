import {test} from 'node:test';import assert from 'node:assert/strict';
const m=await import('./storage.mjs').catch(()=>({}));
test('storage evaluator exists',()=>assert.equal(typeof m.assessStorage,'function'));
if(m.assessStorage){
 const row=method=>({method,url:'https://fixture.invalid/object',tokenHash:'same-session',baseline:method==='RANGE'?206:200,warmed:true,revoked:{url:'https://fixture.invalid/object',tokenHash:'same-session',status:403,bytes:0},revocationIndependentlyVerified:true,control:method==='RANGE'?206:200,outsider:403});
 test('cached 200/206/304, changed URL or token and missing methods never pass',()=>{for(const status of [200,206,304]){const rows=['GET','HEAD','RANGE'].map(row);rows[0].revoked.status=status;assert.equal(m.assessStorage(rows).passed,false)}for(const field of ['url','tokenHash']){const rows=['GET','HEAD','RANGE'].map(row);rows[0].revoked[field]='different';assert.equal(m.assessStorage(rows).passed,false)}assert.equal(m.assessStorage([row('GET')]).passed,false)});
 test('all exact URL denial observations pass only record validation',()=>{const r=m.assessStorage(['GET','HEAD','RANGE'].map(row));assert.equal(r.passed,true);assert.equal(r.providerFixProven,false)});
}
