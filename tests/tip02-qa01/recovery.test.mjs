import fs from 'node:fs';
import vm from 'node:vm';
import assert from 'node:assert/strict';
import {randomUUID,webcrypto} from 'node:crypto';
// Reuse the pinned independent QA harness only; do not rerun its accepted suite.
const qa=fs.readFileSync('docs/review/tip02-null01-independent/independent_client.mjs','utf8');
let harness=qa.slice(qa.indexOf('const html='),qa.indexOf("await test('UI_01"));
harness=harness.replace("'generated/customer.html'",'process.env.CANDIDATE_UI').replace("'generated/talabat-core.js'",'process.env.CANDIDATE_CORE');
const {setup,ctl}=Function('fs','vm','assert','randomUUID','webcrypto','process','setImmediate','setTimeout','clearTimeout',harness+'\nreturn {setup,ctl};')(fs,vm,assert,randomUUID,webcrypto,process,setImmediate,setTimeout,clearTimeout);
const results=[],checkpoints=[];
async function test(name,fn){try{await fn();results.push({name,passed:true});}catch(e){results.push({name,passed:false,error:String(e),stack:e.stack});}}
function reload(disk){const x=setup(disk);x.c.S.cart={};x.c.cartLoaded=false;x.c.cartLoad();return x;}
function manual(x,value){x.c.tipSelect02('other');x.c.tipInput02(String(value));}
for(const status of ['created','replayed','historical_recovered'])for(const later of [null,3,99,'invalid']){
 await test(`${status}: every persisted completion checkpoint / later=${later}`,async()=>{
  const x=setup();manual(x,99);const p=x.c.place();await x.tick();const old=x.calls[0].key;
  x.c.S.cart={newitem:3};if(later!==null)manual(x,later);x.c.cartSave();
  const before=new Map(x.disk),start=x.writes.length;
  x.finish({status,id:'15001'});await p;
  const snapshots=[{boundary:'before completion save',disk:before},...x.writes.slice(start).map((w,i)=>({boundary:'after save '+i,disk:new Map([['qa-cart',w.value]])}))];
  assert(snapshots.length>1);
  for(const snap of snapshots){
   const y=reload(snap.disk),pending=y.c.S.okey===old;
   assert.equal(y.c.S.cart.newitem,3);
   if(pending){await y.c.place();assert.equal(y.calls.length,0,'recovery first, never create from pending key');}
   assert.equal(y.c.S.okey,null);
   const expected=later===null?0:later;
   checkpoints.push({status,later,boundary:snap.boundary,pending,tip:y.c.S.tip,raw:y.c.S.tipRaw02,cart:{...y.c.S.cart},key:y.c.S.okey});
   if(later==='invalid'){assert.equal(y.c.S.tipRaw02,'invalid');await y.c.place();assert.equal(y.calls.length,0);continue;}
   assert.equal(y.c.S.tip,expected,'consumed tip must not survive a detached-key checkpoint');
   const next=y.c.place();await y.tick();assert.equal(y.calls[0].tip,expected);assert.notEqual(y.calls[0].key,old);assert.equal(y.calls[0].lines[0].item_id,'newitem');y.finish({status:'created',id:'15002'});await next;
  }
 });
}
await test('recovery branch persists reset and detached key together',async()=>{
 const x=setup();manual(x,99);const p=x.c.place();await x.tick();const key=x.calls[0].key;x.c.S.cart={newitem:3};x.finish({status:'unresolved'});await p;
 const y=reload(x.disk),start=y.writes.length;await y.c.place();
 for(const w of y.writes.slice(start)){const d=JSON.parse(w.value);assert.equal(d.cart.newitem,3);if(d.key===null)assert.equal(d.tip,0);else assert.equal(d.key,key);}
});
await test('failed completion storage write restores old key then recovers safely',async()=>{
 const x=setup();manual(x,99);const p=x.c.place();await x.tick();const key=x.calls[0].key;x.c.S.cart={newitem:3};x.c.cartSave();
 x.c.localStorage.setItem=()=>{throw Error('synthetic storage unavailable');};x.finish({status:'created',id:'15001'});await p;
 const y=reload(x.disk);assert.equal(y.c.S.okey,key);assert.equal(y.c.S.tip,99);await y.c.place();assert.equal(y.calls.length,0);assert.equal(y.c.S.tip,0);assert.equal(y.c.S.cart.newitem,3);assert.equal(y.c.S.okey,null);
});
await test('late response cannot retire a newer key or explicit tip',async()=>{
 const x=setup();manual(x,99);const p=x.c.place();await x.tick();x.c.S.okey='newer_pending_key';x.c.S.cart={newitem:3};manual(x,20);x.finish({status:'created',id:'15001'});await p;
 const y=reload(x.disk);assert.equal(y.c.S.okey,'newer_pending_key');assert.equal(y.c.S.tip,20);assert.equal(y.c.S.cart.newitem,3);
});
await test('foreign-tab saved draft is not overwritten by late success',async()=>{
 const x=setup();manual(x,99);const p=x.c.place();await x.tick();const y=reload(x.disk);y.c.S.cart={otherTab:2};manual(y,3);const latest=y.disk.get('qa-cart');x.disk.set('qa-cart',latest);x.finish({status:'created',id:'15001'});await p;assert.equal(x.disk.get('qa-cart'),latest);
});
await test('real controller frozen payload survives ACK loss and edited draft',async()=>{
 const x=setup(),driver=ctl();driver.rpc(async()=>{throw Error('lost ACK');});
 x.c.TLB.placeOrder=o=>driver.client.submit({p_key:o.key,p_tip:o.tip,p_items:o.lines},true,{cartToken:o.cartToken});manual(x,99);await x.c.place();const old=driver.state().active;assert(old);
 x.c.S.cart={newitem:3};manual(x,3);const y=reload(x.disk);
 driver.rpc(async(n,p)=>({data:{key:p.p_key,status:n==='order_request_status104'?'unresolved':'replayed',reason:'not_visible',id:n==='place_order104'?'15001':undefined}}));
 y.c.TLB.recoverOrder103=k=>driver.client.recover(k);await y.c.place();assert.equal(y.c.S.okey,old);assert.equal(y.c.S.tip,3);
 const result=await driver.client.retrySaved(old,true);assert.equal(result.status,'replayed');assert.equal(driver.calls.at(-1).payload.p_tip,99);assert.equal(driver.calls.at(-1).payload.p_key,old);
 y.c.TLB.recoverOrder103=async()=>result;await y.c.place();assert.equal(y.c.S.tip,3);assert.equal(y.c.S.cart.newitem,3);assert.equal(y.c.S.okey,null);
});
await test('real controller permits next explicit confirmation only with cleared consumed tip',async()=>{
 const x=setup(),shared={states:new Map(),queue:Promise.resolve()},driver=ctl(shared);let release,signal;const entered=new Promise(r=>signal=r);
 driver.rpc((n,p)=>new Promise(r=>{release=()=>r({data:{key:p.p_key,status:'created',id:'15001'}});signal();}));
 x.c.TLB.placeOrder=o=>driver.client.submit({p_key:o.key,p_tip:o.tip,p_items:o.lines},true,{cartToken:o.cartToken});manual(x,99);const pending=x.c.place();await entered;assert(release);const old=driver.calls[0].payload.p_key;x.c.S.cart={newitem:3};const start=x.writes.length;release();await pending;assert.equal(driver.state().active,null);
 const snapshots=x.writes.slice(start).map(w=>JSON.parse(w.value)).filter(d=>d.key===null);assert(snapshots.length);
 for(const d of snapshots){const y=reload(new Map([['qa-cart',JSON.stringify(d)]])),next=ctl(shared);y.c.TLB.placeOrder=o=>next.client.submit({p_key:o.key,p_tip:o.tip,p_items:o.lines},true,{cartToken:o.cartToken});assert.equal(next.calls.length,0);await y.c.place();const sent=next.calls.find(c=>c.name==='place_order104');assert(sent);assert.notEqual(sent.payload.p_key,old);assert.equal(sent.payload.p_tip,0);assert.equal(sent.payload.p_items[0].item_id,'newitem');}
});
await test('older sequence with the same key cannot clear a later selection',async()=>{
 const x=setup();manual(x,99);const p=x.c.place();await x.tick();const key=x.c.S.okey;x.c.S.checkoutSeq105++;x.c.S.cart={newitem:3};manual(x,20);x.finish({status:'created',id:'15001'});await p;
 const y=reload(x.disk);assert.equal(y.c.S.okey,key);assert.equal(y.c.S.tip,20);assert.equal(y.c.S.cart.newitem,3);
});
await test('ending confirmed rejection detaches key without consuming chosen tip',async()=>{
 const x=setup();manual(x,99);x.c.S.okey='rejected_pending_key';x.c.S.tipSentKey02=x.c.S.okey;x.c.cartSave();x.c.confirm=()=>true;
 x.c.TLB.recoverOrder103=async()=>({status:'rejected',closed:true});x.c.TLB.endRejected104=async()=>({status:'ended_rejected',closed:true});await x.c.place();
 const y=reload(x.disk);assert.equal(y.c.S.okey,null);assert.equal(y.c.S.tip,99);assert.equal(y.c.S.cart.item,2);
});
const out={scope:'Node VM generated UI; synthetic localStorage/RPC/transactional store, NOT browser or IndexedDB',results,checkpoints};
fs.writeFileSync(process.env.RESULT_FILE||'tip02-qa01-results.json',JSON.stringify(out,null,2));console.log(JSON.stringify(results,null,2));process.exitCode=results.every(x=>x.passed)?0:1;
