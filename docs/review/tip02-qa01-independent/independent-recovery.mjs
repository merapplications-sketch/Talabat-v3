import fs from 'node:fs';import vm from 'node:vm';import assert from 'node:assert/strict';import {randomUUID,webcrypto} from 'node:crypto';
// Reuse only our pinned previous harness. New assertions below are independently authored.
const prior=fs.readFileSync('docs/review/tip02-null01-independent/independent_client.mjs','utf8');
let harness=prior.slice(prior.indexOf('const html='),prior.indexOf("await test('UI_01"));
harness=harness.replace("'generated/customer.html'","(process.env.QA_UI||'generated/customer.html')").replace("'generated/talabat-core.js'","(process.env.QA_CORE||'generated/talabat-core.js')");
const {setup,ctl}=Function('fs','vm','assert','randomUUID','webcrypto','process','setImmediate','setTimeout','clearTimeout',harness+'\nreturn {setup,ctl};')(fs,vm,assert,randomUUID,webcrypto,process,setImmediate,setTimeout,clearTimeout);
const results=[],points=[];let scenarioCount=0;const timeout=p=>Promise.race([p,new Promise((_,j)=>{const t=setTimeout(()=>j(Error('harness deadline')),4000);t.unref();})]);
async function test(id,fn){if(process.env.QA_CASES&&!process.env.QA_CASES.split(',').includes(id))return;try{await timeout(fn());results.push({id,result:'PASS'});}catch(e){results.push({id,result:'FAIL',error:String(e),stack:e.stack});}}
const plain=x=>JSON.parse(JSON.stringify(x));
function manual(x,n){x.c.tipSelect02('other');x.c.tipInput02(String(n));}
function restore(disk){const x=setup(disk);x.c.S.cart={};x.c.cartLoaded=false;x.c.cartLoad();return x;}
function diskOf(value){return new Map([['qa-cart',value]]);}
async function started(){const x=setup();manual(x,99);const waiting=x.c.place();await x.tick();assert.equal(x.calls.length,1);return {x,waiting,key:x.calls[0].key};}
async function nextCheck(snapshot,key,expected,cart,id){
 const y=restore(snapshot);assert.deepEqual(plain(y.c.S.cart),cart);assert.equal(y.calls.length,0,'restore does not create');
 if(y.c.S.okey){assert.equal(y.c.S.okey,key);let read=0;y.c.TLB.recoverOrder103=async k=>{assert.equal(k,key);read++;return{status:'replayed',id:'15001',keepCart:true};};await y.c.place();assert.equal(read,1);assert.equal(y.calls.length,0,'resolve original before next confirmation');}
 assert.equal(y.c.S.okey,null);assert.deepEqual(plain(y.c.S.cart),cart);
 if(expected==='invalid'){assert.equal(y.c.S.tipRaw02,'invalid');await y.c.place();assert.equal(y.calls.length,0);return;}
 assert.equal(y.c.S.tip,expected,id);const again=y.c.place();await y.tick();assert.equal(y.calls.length,1);const req=y.calls[0];assert.notEqual(req.key,key);assert.equal(req.tip,expected,id);assert.deepEqual(req.lines.map(l=>[l.item_id,l.qty]),Object.entries(cart));y.finish({status:'created',id:'15002'});await again;
}
await test('R01_all_persisted_checkpoints_direct_and_recovery',async()=>{
 for(const path of ['direct','recovery'])for(const status of ['created','replayed','historical_recovered'])for(const later of [null,3,99,'invalid']){
  scenarioCount++;let {x,waiting,key}=await started();
  if(path==='recovery'){x.finish({status:'unresolved',error:'order_outcome_unknown'});await waiting;x=restore(x.disk);let resolve;x.c.TLB.recoverOrder103=()=>new Promise(r=>resolve=r);waiting=x.c.place();await x.tick();x.finish=resolve;}
  x.c.S.cart={newitem:3,added:1};x.c.cartSave();if(later!==null)manual(x,later);
  const before=new Map(x.disk),start=x.writes.length;x.finish({status,id:'15001',keepCart:true});await waiting;
  const writes=x.writes.slice(start);assert(writes.length>0);const snapshots=[{where:'before_completion',disk:before},...writes.map((w,i)=>({where:'after_setItem_'+i,disk:diskOf(w.value)}))];
  for(const snap of snapshots){const d=JSON.parse(snap.disk.get('qa-cart'));if(d.key===null&&later===null){assert.equal(d.tip,0,'detached key cannot retain consumed amount');assert.equal(d.tipSentKey02,null);assert.equal(d.tipRaw02,'');}
   await nextCheck(snap.disk,key,later===null?0:later,{newitem:3,added:1},path+'/'+status+'/'+later+'/'+snap.where);points.push({path,status,later,where:snap.where,keyPresent:!!d.key,tip:d.tip,raw:d.tipRaw02});}
 }
});
await test('R02_one_record_retirement_after_ownership_check',async()=>{
 for(const completed of [true,false])for(const later of [null,99]){
  const x=setup();manual(x,99);x.c.S.okey='owned_recovery_key';x.c.S.checkoutSeq105=7;x.c.S.tipSentKey02=x.c.S.okey;x.c.cartSave();if(later!==null)manual(x,later);const n=x.writes.length;
  assert.equal(x.c.retireDraft105('owned_recovery_key',7,completed),true);const w=x.writes.slice(n);assert.equal(w.length,1);const d=JSON.parse(w[0].value);assert.equal(d.key,null);assert.equal(d.tip,completed&&later===null?0:99);
 }
 const x=setup();manual(x,99);x.c.S.okey='current_recovery_key';x.c.S.checkoutSeq105=4;const before=new Map(x.disk),n=x.writes.length;assert.equal(x.c.retireDraft105('other_recovery_key',4,true),false);assert.equal(x.c.retireDraft105('current_recovery_key',3,true),false);assert.equal(x.writes.length,n);assert.deepEqual(x.disk,before);assert.equal(x.c.S.tip,99);
});
await test('R03_completion_storage_failure_once_or_persistent',async()=>{
 for(const mode of ['once','persistent'])for(const later of [null,99,3]){
  const {x,waiting,key}=await started();x.c.S.cart={newitem:4};x.c.cartSave();if(later!==null)manual(x,later);const before=new Map(x.disk),real=x.c.localStorage.setItem;let calls=0;x.c.localStorage.setItem=(k,v)=>{calls++;if(mode==='persistent'||calls===1)throw Error('synthetic quota failure');real(k,v);};
  x.finish({status:'created',id:'15001',keepCart:true});await waiting;assert(calls>0);if(mode==='persistent')assert.deepEqual(x.disk,before);
  await nextCheck(x.disk,key,later===null?0:later,{newitem:4},mode+'/'+later);
 }
});
await test('R04_foreign_tab_disk_unchanged_and_stale_tab_cannot_submit',async()=>{
 const {x,waiting}=await started(),y=restore(x.disk);y.c.S.cart={otherTab:2};y.c.S.okey='foreign_pending_key';manual(y,99);const newer=y.disk.get('qa-cart');x.disk.set('qa-cart',newer);x.finish({status:'created',id:'15001'});await waiting;assert.equal(x.disk.get('qa-cart'),newer);const count=x.calls.length;await x.c.place();assert.equal(x.calls.length,count);assert.equal(x.disk.get('qa-cart'),newer);
 const z=restore(x.disk);assert.equal(z.c.S.okey,'foreign_pending_key');assert.equal(z.c.S.tip,99);assert.equal(z.c.S.cart.otherTab,2);
});
await test('R05_storage_read_failure_fails_closed',async()=>{
 const {x,waiting}=await started();x.c.S.cart={newitem:3};x.c.cartSave();const before=new Map(x.disk);x.c.localStorage.getItem=()=>{throw Error('synthetic storage read failure');};x.finish({status:'created',id:'15001'});await waiting;assert.deepEqual(x.disk,before);const n=x.calls.length;await x.c.place();assert.equal(x.calls.length,n);
});
await test('R06_stale_key_and_stale_sequence_cannot_clear_newer_tip',async()=>{
 for(const newerKey of [false,true]){
  const {x,waiting,key}=await started();if(newerKey)x.c.S.okey='newer_recovery_key';else x.c.S.checkoutSeq105++;x.c.S.cart={latest:7};manual(x,99);x.finish({status:'created',id:'15001'});await waiting;const y=restore(x.disk);assert.equal(y.c.S.okey,newerKey?'newer_recovery_key':key);assert.equal(y.c.S.tip,99);assert.equal(y.c.S.cart.latest,7);
 }
});
await test('R07_unresolved_conflict_rejection_preserve_original_attempt',async()=>{
 for(const outcome of [{status:'unresolved',error:'order_outcome_unknown'},{status:'conflict',error:'idempotency_mismatch'},{status:'rejected',error:'bad_value'}]){
  const {x,waiting,key}=await started();x.c.S.cart={nextcart:5};manual(x,3);x.finish(outcome);await waiting;const y=restore(x.disk);y.c.TLB.recoverOrder103=async k=>{assert.equal(k,key);return outcome;};await y.c.place();assert.equal(y.calls.length,0);assert.equal(y.c.S.okey,key);assert.equal(y.c.S.tip,3);assert.equal(y.c.S.cart.nextcart,5);assert.equal(x.calls[0].tip,99);
 }
});
await test('R08_integrated_ack_lost_snapshot_and_original_payload',async()=>{
 const x=setup(),shared={states:new Map(),queue:Promise.resolve()},c=ctl(shared);c.rpc(async()=>{throw Error('lost ACK');});x.c.TLB.placeOrder=o=>c.client.submit({p_key:o.key,p_tip:o.tip,p_items:o.lines},true,{cartToken:o.cartToken});manual(x,99);await x.c.place();const key=c.state().active;assert(key);const payload=plain(c.state().attempts[key].payload);x.c.S.cart={newitem:3};manual(x,99);
 const y=restore(x.disk),fresh=ctl(shared);fresh.rpc(async(n,p)=>({data:{key:p.p_key,status:n==='order_request_status104'?'unresolved':'replayed',reason:'not_visible',id:n==='place_order104'?'15001':undefined}}));
 y.c.TLB.recoverOrder103=k=>fresh.client.recover(k);await y.c.place();assert.equal(y.c.S.okey,key);assert.equal(fresh.calls.filter(r=>r.name==='place_order104').length,0);const blocked=await fresh.client.submit({p_key:'alternate_attempt_key',p_tip:1},true);assert.equal(blocked.recoveryKey,key);
 const r=await fresh.client.retrySaved(key,true);assert.equal(r.status,'replayed');assert.deepEqual(fresh.calls.at(-1).payload,payload);assert.equal(payload.p_tip,99);assert.equal(fresh.calls.at(-1).payload.p_key,key);assert.equal(fresh.state().active,null);
 y.c.TLB.recoverOrder103=async()=>r;await y.c.place();assert.equal(y.c.S.tip,99,'explicit same-value selection is new intent');assert.equal(y.c.S.cart.newitem,3);assert.equal(y.c.S.okey,null);
});
await test('R09_integrated_controller_completed_then_crash_every_save',async()=>{
 const x=setup(),shared={states:new Map(),queue:Promise.resolve()},c=ctl(shared);let release,entered;const reached=new Promise(r=>entered=r);c.rpc((n,p)=>new Promise(r=>{release=()=>r({data:{key:p.p_key,status:'created',id:'15001'}});entered();}));x.c.TLB.placeOrder=o=>c.client.submit({p_key:o.key,p_tip:o.tip,p_items:o.lines},true,{cartToken:o.cartToken});manual(x,99);const done=x.c.place();await reached;const key=c.calls[0].payload.p_key;x.c.S.cart={after:2};x.c.cartSave();const start=x.writes.length;release();await done;assert.equal(c.state().active,null);
 for(const w of x.writes.slice(start)){const y=restore(diskOf(w.value)),next=ctl(shared);y.c.TLB.placeOrder=o=>next.client.submit({p_key:o.key,p_tip:o.tip,p_items:o.lines},true,{cartToken:o.cartToken});assert.equal(y.c.S.tip,0);assert.equal(y.c.S.okey,null);assert.equal(next.calls.length,0);await y.c.place();const req=next.calls.find(r=>r.name==='place_order104');assert(req);assert.notEqual(req.payload.p_key,key);assert.equal(req.payload.p_tip,0);assert.equal(req.payload.p_items[0].item_id,'after');}
});
await test('R10_ended_rejection_retains_unconsumed_tip_and_requires_confirmation',async()=>{
 for(const approved of [false,true]){const x=setup();manual(x,99);x.c.S.okey='closed_recovery_key';x.c.S.tipSentKey02=x.c.S.okey;x.c.cartSave();x.c.confirm=()=>approved;let ended=0;x.c.TLB.recoverOrder103=async()=>({status:'rejected',closed:true});x.c.TLB.endRejected104=async()=>{ended++;return{status:'ended_rejected',closed:true};};await x.c.place();assert.equal(ended,approved?1:0);const y=restore(x.disk);assert.equal(y.c.S.tip,99);assert.equal(y.c.S.okey,approved?null:'closed_recovery_key');assert.equal(y.calls.length,0);}
});
await test('R11_C04_late_rejections_preserve_newer_context_and_same_value_intent',async()=>{
 const inputs=[['bad_time','at',Date.now()+3600000,Date.now()+7200000],['promo_invalid','promo',{code:'OLD'},{code:'NEW'}],['bad_group','gNotes',{old:1},{later:2}],['fee_changed','quote',{fee:2},{fee:9}],['bad_time','addrId','old','new'],['bad_time','gift',{name:'Synthetic',phone:'+992123456789'},{name:'Changed',phone:'+992123456789'}]];
 for(const [error,field,old,value]of inputs){const x=setup();x.c.S.at=Date.now()+7200000;x.c.S[field]=old;manual(x,99);const done=x.c.place();await x.tick();assert.equal(x.calls.length,1);x.c.S[field]=value;x.c.S.cart={newitem:3};x.finish({status:'rejected',error});await done;assert.deepEqual(plain(x.c.S[field]),value);assert.equal(x.c.S.tip,99);assert.equal(x.c.S.okey,x.calls[0].key);assert.equal(x.c.S.cart.newitem,3);}
 const x=setup();const original=Date.now()+7200000;x.c.S.at=original;manual(x,99);const done=x.c.place();await x.tick();x.c.S.at=original+60000;x.c.S.at=original;x.finish({status:'rejected',error:'bad_time'});await done;assert.equal(x.c.S.at,original);
});
await test('R12_back_to_cart_and_reload_keeps_unresolved_tip',async()=>{
 const {x,waiting,key}=await started();x.c.S.cart={newitem:3};x.finish({status:'unresolved',error:'order_outcome_unknown'});await waiting;x.c.go('cart');x.c.go('pay');const y=restore(x.disk);assert.equal(y.c.S.okey,key);assert.equal(y.c.S.tip,99);assert.equal(y.c.S.cart.newitem,3);assert.equal(y.calls.length,0);
});
await test('R13_plain_success_removes_old_cart_without_sending_another_order',async()=>{
 const {x,waiting}=await started();x.finish({status:'created',id:'15001'});await waiting;assert.equal(x.c.S.tip,0);assert.equal(x.c.S.okey,null);assert.equal(Object.keys(x.c.S.cart).length,0);assert.equal(x.disk.has('qa-cart'),false);assert.equal(x.calls.length,1);
});
const out={source:'d76269c9f3e5c02fe0be379ac8ba6356e624f9b8',scope:'LOCAL Node VM; generated UI/controller; mocked RPC/localStorage/serialized store; NOT Chromium/IndexedDB/HTTP',time_utc:new Date().toISOString(),tests:results.length,pass:results.filter(x=>x.result==='PASS').length,fail:results.filter(x=>x.result==='FAIL').length,matrix_scenarios:scenarioCount,matrix_persisted_states:points.length,results,points};
fs.writeFileSync(process.env.QA_RESULT||'independent-results.json',JSON.stringify(out,null,2));console.log(JSON.stringify({...out,points:undefined},null,2));process.exitCode=out.fail?1:0;
