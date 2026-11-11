import fs from 'node:fs';import vm from 'node:vm';import assert from 'node:assert/strict';import {randomUUID,webcrypto} from 'node:crypto';
const html=fs.readFileSync('generated/customer.html','utf8'),core=fs.readFileSync('generated/talabat-core.js','utf8');
const ui=html.slice(html.indexOf('function cartToken104(){'),html.indexOf("let phErr=''"));
const cart=html.slice(html.indexOf('function cartSave(){'),html.indexOf('function afterCart(){'));
const after=html.slice(html.indexOf('function afterCart(){'),html.indexOf('function delLine('));
const controller=core.slice(0,core.indexOf('})(globalThis);')+'})(globalThis);'.length);
const records=[];async function test(name,fn){if(process.env.QA_CASES&&!process.env.QA_CASES.split(',').includes(name))return;try{await fn();records.push({case:name,result:'PASS'})}catch(e){records.push({case:name,result:'FAIL',detail:String(e),stack:e.stack})}}
function setup(saved=new Map()){
 const disk=new Map(saved),writes=[],calls=[],alerts=[];let finish;
 const c={Date,JSON,Object,Math,String,Number,Promise,console,cartLoaded:true,ALLS:[{id:'store',n:'store'}],S:{cart:{item:2},cartStore:'store',tip:0,pay:'cash',v:'pay',okey:null},ME:{phone:'synthetic'},CK:()=> 'qa-cart',localStorage:{getItem:k=>disk.get(k)||null,setItem:(k,v)=>{disk.set(k,v);writes.push({key:k,value:v})},removeItem:k=>disk.delete(k)},render:()=>c.cartSave(),alert:m=>alerts.push(m),confirm:()=>false,t:x=>x,esc:x=>String(x).replaceAll('&','&amp;').replaceAll('"','&quot;').replaceAll('<','&lt;'),closedNow:()=>false,badKeys:()=>[],curAddr:()=>({lat:38,lng:68}),newKey:()=> 'qa_'+randomUUID().replaceAll('-',''),ensureQuote:async()=>({fee:2}),lineNotes:ks=>ks.map(()=>''),pk:k=>({id:k,ops:[]}),addrText:()=> 'QA synthetic',calc:()=>({fw:0,w:0,pts:0}),optExtra:()=>null,errMsg:r=>r.error,prefSave(){},grpEnd:()=>{c.S.gCheckout=false;c.S.gNotes=null},quoteNow(){},cartCount:()=>Object.values(c.S.cart).reduce((a,b)=>a+b,0),revalPromo(){},go(v){c.S.v=v;c.cartSave()},TLB:{lang:()=> 'en',isOpen:()=>true,placeOrder:a=>{calls.push(structuredClone(a));return new Promise(r=>finish=r)},recoverOrder103:async()=>({status:'replayed',id:'15001',keepCart:true})}};
 vm.createContext(c);vm.runInContext(cart+'\n'+ui+'\n'+after,c);return{c,calls,disk,writes,alerts,finish:r=>finish(r),tick:()=>new Promise(r=>setImmediate(r))};
}
function ctl(shared={states:new Map(),queue:Promise.resolve()},uid='account_a'){
 const g={setTimeout,clearTimeout,TextEncoder,crypto:webcrypto};vm.createContext(g);vm.runInContext(controller,g);const calls=[];let rpc=async(n,p)=>({data:{key:p.p_key,status:n==='place_order104'?'created':'replayed',id:'15001'}});
 const client=g.TalabotOrder104({user:()=>uid,uuid:()=>randomUUID(),store:{transact:(u,f)=>{const q=shared.queue.then(()=>{let s=shared.states.get(u);if(!s){s={version:1,revision:0,active:null,attempts:{}};shared.states.set(u,s)}return f(s)});shared.queue=q.catch(()=>{});return q;}},readOrder:async()=>true,rpc:async(n,p)=>{calls.push({name:n,payload:structuredClone(p)});return rpc(n,p)}});
 return{client,calls,shared,state:()=>shared.states.get(uid),rpc:f=>rpc=f};
}
await test('UI_01_all_integer_amounts_exact_and_no_automatic_next_tip',async()=>{
 for(let n=1;n<=100;n++){
  const x=setup();x.c.tipSelect02('other');x.c.tipInput02(String(n));const promise=x.c.place();await x.tick();assert.equal(x.calls[0].tip,n);x.finish({status:'created',id:'15001'});await promise;assert.equal(x.c.S.tip,0);assert.equal(x.c.S.tipMode02,'quick');assert.equal(x.c.S.tipRaw02,'');
 }
});
await test('UI_02_invalid_edit_preserved_no_new_rpc_or_key',async()=>{
 for(const raw of ['', '0','-1','1.5','1.000001','100.1','101','1e2','abc','NaN','Infinity','<script>','١٠']){
  const x=setup();x.c.tipSelect02(20);x.c.tipSelect02('other');x.c.tipInput02(raw);await x.c.place();assert.equal(x.calls.length,0);assert.equal(x.c.S.okey,null);assert.equal(x.c.S.tipRaw02,raw);const y=setup(x.disk);y.c.S.cart={};y.c.cartLoaded=false;y.c.cartLoad();assert.equal(y.c.S.tipRaw02,raw);assert.equal(y.c.tipGet02().ok,false);
 }
});
await test('UI_03_default_and_explicit_null_draft_distinct',async()=>{
 for(const v of [undefined,null,0,3,100]){
  const d={sid:'store',cart:{item:2},at:Date.now()};if(v!==undefined)d.tip=v;
  const x=setup(new Map([['qa-cart',JSON.stringify(d)]]));x.c.S.cart={};x.c.cartLoaded=false;x.c.cartLoad();assert.equal(x.c.tipGet02().ok,v!==null);if(v!==null)assert.equal(x.c.S.tip,v===undefined?0:v);
 }
});
await test('UI_04_valid_edit_during_quote_sends_latest_and_invalid_stops',async()=>{
 for(const raw of ['100','1.5']){const x=setup();let done;x.c.ensureQuote=()=>new Promise(r=>done=r);x.c.tipSelect02(5);const wait=x.c.place();await x.tick();x.c.tipSelect02('other');x.c.tipInput02(raw);done({fee:2});await x.tick();if(raw==='100'){assert.equal(x.calls[0].tip,100);x.finish({status:'created',id:'15001'})}else{assert.equal(x.calls.length,0);assert.equal(x.c.S.okey,null)}await wait;}
});
await test('UI_05_changed_cart_preserved_and_next_order_zero',async()=>{
 const x=setup();x.c.tipSelect02('other');x.c.tipInput02('100');const p=x.c.place();await x.tick();const key=x.calls[0].key;x.c.S.cart={newitem:3};x.finish({status:'created',id:'15001'});await p;assert.equal(x.c.S.cart.newitem,3);assert.equal(x.c.S.tip,0);const next=x.c.place();await x.tick();assert.equal(x.calls[1].tip,0);assert.notEqual(x.calls[1].key,key);x.finish({status:'created',id:'15002'});await next;
});
await test('UI_06_explicit_later_selection_preserved_after_success_or_replay',async()=>{
 for(const status of ['created','replayed','historical_recovered']){const x=setup();x.c.tipSelect02(5);const p=x.c.place();await x.tick();x.c.tipSelect02('other');x.c.tipInput02('37');x.finish({status,id:'15001',keepCart:status!=='created'});await p;assert.equal(x.c.S.tip,37);assert.equal(x.c.S.cart.item,2);}
});
await test('UI_07_rejection_and_unknown_keep_latest_draft_and_original_key',async()=>{
 for(const status of ['rejected','unresolved']){const x=setup();x.c.tipSelect02('other');x.c.tipInput02('100');const p=x.c.place();await x.tick();const key=x.c.S.okey;x.c.tipInput02('101');x.finish({status,error:status==='rejected'?'bad_value':'order_outcome_unknown'});await p;assert.equal(x.c.S.okey,key);assert.equal(x.c.S.tipRaw02,'101');assert.equal(x.calls[0].tip,100);}
});
await test('UI_08_reload_recovery_preserves_unresolved_invalid_draft',async()=>{
 const x=setup();x.c.tipSelect02('other');x.c.tipInput02('37');const p=x.c.place();await x.tick();x.finish({status:'unresolved'});await p;const y=setup(x.disk);y.c.S.cart={};y.c.cartLoaded=false;y.c.cartLoad();const key=y.c.S.okey;y.c.tipInput02('bad');let recovered=0;y.c.TLB.recoverOrder103=async k=>{recovered++;assert.equal(k,key);return{status:'unresolved',reason:'not_visible'}};await y.c.place();assert.equal(recovered,1);assert.equal(y.calls.length,0);assert.equal(y.c.S.tipRaw02,'bad');assert.equal(y.c.S.okey,key);
});
await test('UI_09_empty_cart_resets_tip_but_later_confirmation_still_needed',async()=>{
 const x=setup();x.c.tipSelect02('other');x.c.tipInput02('100');x.c.S.cart={};x.c.afterCart();assert.equal(x.c.S.tip,0);assert.equal(x.c.S.tipMode02,'quick');assert.equal(x.c.S.tipRaw02,'');assert.equal(x.calls.length,0);
});
await test('UI_10_stale_reply_cannot_clear_newer_attempt_tip',async()=>{
 const x=setup();x.c.tipSelect02(5);const p=x.c.place();await x.tick();x.c.S.okey='newer_qa_key';x.c.tipSelect02('other');x.c.tipInput02('100');x.finish({status:'created',id:'15001'});await p;assert.equal(x.c.S.tip,100);assert.equal(x.c.S.okey,'newer_qa_key');
});
await test('UI_11_success_crash_checkpoint_never_carries_consumed_tip',async()=>{
 const x=setup();x.c.tipSelect02('other');x.c.tipInput02('99');const p=x.c.place();await x.tick();const original=x.calls[0].key;x.c.S.cart={newitem:3};x.finish({status:'created',id:'15001'});await p;
 // Every recorded setItem is a durable state at which the process can terminate.
 const unsafe=x.writes.map(w=>JSON.parse(w.value)).find(d=>d.key===null&&d.tip===99&&d.cart.newitem===3&&d.tipSentKey02===original);
 if(unsafe){const y=setup(new Map([['qa-cart',JSON.stringify(unsafe)]]));y.c.S.cart={};y.c.cartLoaded=false;y.c.cartLoad();const next=y.c.place();await y.tick();const observed=y.calls[0];y.finish({status:'created',id:'15002'});await next;fs.writeFileSync('qa-crash-checkpoint.json',JSON.stringify({scope:'Node VM; simulated restart at actual localStorage write boundary',savedDraft:unsafe,previousKey:original,newRequest:observed},null,2));assert.equal(observed.tip,0,'consumed tip survives a durable success checkpoint and is sent with a NEW key');}
});
await test('CORE_01_all_valid_numbers_unchanged_invalid_no_durable_attempt',async()=>{
 for(const tip of [0,...Array.from({length:100},(_,i)=>i+1),null]){const x=ctl();await x.client.submit({p_key:'qa_valid_key',p_tip:tip},true);assert.equal(x.calls[0].payload.p_tip,tip)}
 for(const tip of [-1,101,1.5,NaN,Infinity,'37','',false,{},[]]){const x=ctl();const r=await x.client.submit({p_key:'qa_invalid_key',p_tip:tip},true);assert.equal(r.status,'rejected');assert.equal(r.closed,false);assert.equal(x.calls.length,0);assert.equal(Object.keys(x.state().attempts).length,0)}
});
await test('CORE_02_three_controllers_same_key_reverse_responses',async()=>{
 const shared={states:new Map(),queue:Promise.resolve()};const a=ctl(shared),b=ctl(shared),c=ctl(shared);let ra,rb,rc;a.rpc(()=>new Promise(r=>ra=r));b.rpc(()=>new Promise(r=>rb=r));c.rpc(()=>new Promise(r=>rc=r));
 const p=a.client.submit({p_key:'three_tabs_key',p_tip:100},true);await new Promise(r=>setImmediate(r));const q=b.client.submit({p_key:'three_tabs_key',p_tip:1},true);await new Promise(r=>setImmediate(r));const z=c.client.recover('three_tabs_key');await new Promise(r=>setImmediate(r));
 rc({data:{key:'three_tabs_key',status:'replayed',id:'15001'}});assert.equal((await z).status,'replayed');rb({data:{key:'three_tabs_key',status:'unresolved',reason:'not_visible'}});assert.equal((await q).reason,'stale_reply');ra({data:{key:'three_tabs_key',status:'created',id:'15001'}});assert.equal((await p).reason,'stale_reply');assert.equal(a.calls[0].name,'place_order104');assert.equal(b.calls[0].name,'order_request_status104');assert.equal(c.calls[0].name,'order_request_status104');assert.equal(a.state().attempts.three_tabs_key.orderId,'15001');
});
await test('CORE_03_ack_unknown_blocks_alternate_key_and_retries_frozen_payload',async()=>{
 const x=ctl();x.rpc(async()=>{throw Error('lost ACK')});await x.client.submit({p_key:'original_unknown_key',p_tip:99},true);const r=await x.client.submit({p_key:'replacement_key',p_tip:1},true);assert.equal(r.recoveryKey,'original_unknown_key');assert.equal(x.calls.length,1);
 x.rpc(async(n,p)=>({data:{key:p.p_key,status:n==='order_request_status104'?'unresolved':'replayed',reason:'not_visible',id:n==='place_order104'?'15001':undefined}}));const done=await x.client.retrySaved('original_unknown_key',true);assert.equal(done.status,'replayed');assert.equal(x.calls.at(-1).payload.p_tip,99);assert(x.calls.every(c=>c.payload.p_key==='original_unknown_key'));
});
await test('CORE_04_explicit_null_rejection_requires_committed_closure_to_end',async()=>{
 const x=ctl(),id=randomUUID();x.rpc(async(n,p)=>({data:{key:p.p_key,status:'rejected',reason:'bad_value',closed:true,no_effects:true,state_version:1,closure_id:id}}));let r=await x.client.submit({p_key:'null_qa_key',p_tip:null},true);assert.equal(r.error,'bad_value');assert.equal(r.closed,true);assert.equal(x.calls[0].payload.p_tip,null);
 r=await x.client.submit({p_key:'new_null_qa_key',p_tip:1},true);assert.equal(r.recoveryKey,'null_qa_key');assert.equal((await x.client.endRejected('null_qa_key',false)).status,'unresolved');assert.equal((await x.client.endRejected('null_qa_key',true)).status,'ended_rejected');assert.equal(x.state().active,null);assert.equal((await x.client.submit({p_key:'null_qa_key',p_tip:1},true)).reason,'attempt_closed');
});
await test('CORE_05_null_ack_loss_historical_recovery_no_new_create',async()=>{
 const x=ctl();x.rpc(async()=>{throw Error('lost ACK')});await x.client.submit({p_key:'old_null_ack_key',p_tip:null},true);x.rpc(async(n,p)=>({data:{key:p.p_key,status:'replayed',id:'15001'}}));const r=await x.client.retrySaved('old_null_ack_key',true);assert.equal(r.status,'replayed');assert.equal(x.calls.length,2);assert.equal(x.calls[1].name,'order_request_status104');assert.equal(x.calls[0].payload.p_tip,null);
});
await test('CORE_06_accounts_are_independent_without_cross_account_state',async()=>{
 const shared={states:new Map(),queue:Promise.resolve()},a=ctl(shared,'A'),b=ctl(shared,'B');a.rpc(async()=>{throw Error('unknown')});await a.client.submit({p_key:'same_account_key',p_tip:37},true);const r=await b.client.submit({p_key:'same_account_key',p_tip:1},true);assert.equal(r.status,'created');assert.equal(a.state().active,'same_account_key');assert.equal(b.state().active,null);
});
await test('CORE_07_adapter_omitted_zero_null_type_identity',async()=>{
 const start=core.indexOf('    placeOrder: function (o) {'),end=core.indexOf('\n    checkPromo:',start),fn=core.slice(start,end).replace('    placeOrder: ','').trim().replace(/,$/,'');let sent;
 const g={DB:{approvalReady:true},storeByName:()=>({id:'store'}),linesOf:x=>x,num:Number,orderClient103:()=>({submit:p=>{sent=p;return p}})};vm.createContext(g);vm.runInContext('place=('+fn+')',g);
 for(const [o,expected] of [[{},0],[{tip:0},0],[{tip:null},null],[{tip:100},100]]){g.place({...o,lines:[],key:'adapter_qa_key'});assert.equal(sent.p_tip,expected)}
});
await test('UI_12_integrated_controller_accepts_checkpoint_new_key',async()=>{
 const x=setup(),shared={states:new Map(),queue:Promise.resolve()},driver=ctl(shared);let release;
 driver.rpc((n,p)=>new Promise(r=>release=()=>r({data:{key:p.p_key,status:'created',id:'15001'}})));
 x.c.TLB.placeOrder=o=>driver.client.submit({p_key:o.key,p_tip:o.tip,p_items:o.lines},true,{cartToken:o.cartToken});
 x.c.tipSelect02('other');x.c.tipInput02('99');const pending=x.c.place();for(let i=0;i<8&&!release;i++)await x.tick();assert(release);const old=driver.calls[0].payload.p_key;x.c.S.cart={newitem:3};release();await pending;assert.equal(driver.state().active,null);
 const checkpoint=x.writes.map(w=>JSON.parse(w.value)).find(d=>d.key===null&&d.tip===99&&d.cart.newitem===3&&d.tipSentKey02===old);assert(checkpoint);
 const y=setup(new Map([['qa-cart',JSON.stringify(checkpoint)]])),nextController=ctl(shared);
 y.c.TLB.placeOrder=o=>nextController.client.submit({p_key:o.key,p_tip:o.tip,p_items:o.lines},true,{cartToken:o.cartToken});y.c.S.cart={};y.c.cartLoaded=false;y.c.cartLoad();await y.c.place();
 const sent=nextController.calls.find(c=>c.name==='place_order104');assert(sent);assert.notEqual(sent.payload.p_key,old);assert.equal(sent.payload.p_tip,99);assert.equal(driver.state().attempts[old].state,'created');
 fs.writeFileSync('qa-crash-integrated.json',JSON.stringify({finding:'TIP02-QA-01',reproduced:true,scope:'Generated UI + real candidate controller, mocked RPC and serialized transactional store; restart from saved checkpoint',priorAttemptState:driver.state().attempts[old].state,priorKey:old,newKey:sent.payload.p_key,carriedTip:sent.payload.p_tip,newItems:sent.payload.p_items,automaticExtraConfirmation:false},null,2));
});
fs.writeFileSync(process.env.QA_RESULT||'qa-client-results.json',JSON.stringify({candidate:'3279fefd7ac135ea5554a5ff76404a6ae510eb65',scope:'LOCAL Node VM, synthetic RPC and transactional store; NOT browser/IndexedDB/HTTP',utc:new Date().toISOString(),tests:records.length,passed:records.every(x=>x.result==='PASS'),results:records},null,2));console.log(JSON.stringify(records,null,2));process.exitCode=records.every(x=>x.result==='PASS')?0:1;
