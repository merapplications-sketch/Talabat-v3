import fs from 'node:fs';import vm from 'node:vm';import assert from 'node:assert/strict';
const source=fs.readFileSync('tests/native104/client.js','utf8');const results=[];
for(const mode of ['unsupported_transaction_isolation','40001','transport']){
 const g={setTimeout,clearTimeout,TextEncoder,crypto:globalThis.crypto};vm.createContext(g);vm.runInContext(source,g);let state={version:1,revision:0,active:null,attempts:{}};const calls=[];
 const client=g.TalabotOrder104({user:()=> 'synthetic106',uuid:()=> 'attempt106',store:{transact:async(uid,fn)=>fn(state)},readOrder:async()=>true,rpc:async(n,p)=>{calls.push({n,p});if(mode==='transport')throw Error('synthetic disconnect');return mode==='40001'?{error:{code:'40001'}}:{data:{status:'unresolved',reason:mode,key:p.p_key}}}});
 const payload={p_key:'isolation106_original',p_items:[{qty:2}],p_address:'synthetic frozen'};const r=await client.submit(payload,true);assert.equal(r.status,'unresolved');assert.equal(r.keepCart,true);assert.equal(state.active,payload.p_key);assert.deepEqual(JSON.parse(JSON.stringify(state.attempts[payload.p_key].payload)),payload);assert.equal(calls.length,1);
 const next=await client.submit({...payload,p_key:'isolation106_new'},true);assert.equal(next.recoveryKey,payload.p_key);assert.equal(calls.length,1);
 const end=await client.endRejected(payload.p_key,true);assert.equal(end.status,'unresolved');assert.equal(state.active,payload.p_key);assert.equal(calls.filter(c=>c.n==='place_order104').length,1);assert(calls.every(c=>c.p.p_key===payload.p_key));results.push({mode,passed:true,scope:'unchanged104 controller, in-memory test store and synthetic RPC; not hosted HTTP or new IndexedDB proof'});
}
console.log(JSON.stringify(results,null,2));fs.writeFileSync('native106-client.json',JSON.stringify(results,null,2));
