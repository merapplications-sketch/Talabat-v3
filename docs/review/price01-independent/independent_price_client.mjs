import fs from 'node:fs';import vm from 'node:vm';import assert from 'node:assert/strict';import {randomUUID,webcrypto} from 'node:crypto';
// Reuse the pinned VM scaffolding only, not developer cases/assertions.
const scaffolding=fs.readFileSync('tests/price01-impl/client.test.mjs','utf8');
const prefix=scaffolding.slice(scaffolding.indexOf('const html='),scaffolding.indexOf('const results=[];'));
const {app,ctl,review}=Function('fs','vm','assert','randomUUID','webcrypto','process','setImmediate','setTimeout','clearTimeout',prefix+'\nreturn {app,ctl,review};')(fs,vm,assert,randomUUID,webcrypto,process,setImmediate,setTimeout,clearTimeout);
const I='40000000-0000-4000-8000-000000000092',OP='70000000-0000-4000-8000-000000000092';
const results=[],observations=[];
async function test(name,f){if(process.env.QA_CASES&&!process.env.QA_CASES.split(',').some(x=>name.startsWith(x)))return;try{await f();results.push({name,result:'PASS'})}catch(e){results.push({name,result:'FAIL',error:String(e),stack:e.stack})}}
await test('U01 finite small option must serialize to supported decimal',async()=>{
 const x=app();x.c.S.cart={[I]:1};x.c.pk=k=>({id:k,ops:[OP]});x.c.TLB.optionsOf=()=>[{name:'Group',options:[{id:OP,price:0.0000001,name:'Synthetic fraction'}]}];
 x.c.priceRememberDisplayed01();observations.push({case:'U01',shown:x.c.S.priceShown01,optionPrice:0.0000001});
 assert(x.c.S.priceShown01,'valid finite option value became unusable price evidence');
});
await test('U02 unchanged cent prices must not create floating point price drift',async()=>{
 const x=app();x.c.S.cart={[I]:1};x.c.pk=k=>({id:k,ops:[OP]});x.c.menuOf=()=>[{id:I,price:19.9,discount:0,name:'Synthetic'}];x.c.TLB.optionsOf=()=>[{name:'Group',options:[{id:OP,price:.2,name:'Synthetic option'}]}];
 x.c.priceRememberDisplayed01();const sent=x.c.pricePrepare01().value;observations.push({case:'U02',sent});fs.writeFileSync('qa-client-price-proof.json',JSON.stringify(sent,null,2)+'\n');
 assert.equal(sent.lines[0].unit_price,'20.1');assert.equal(sent.lines[0].net_items,'20.1');
});
await test('U03 catalog changes during quote await cause no create or key',async()=>{
 const x=app();let finish;x.c.ensureQuote=()=>new Promise(r=>finish=r);const p=x.c.place();await x.tick();x.c.menuOf=()=>[{id:I,price:30,discount:0,name:'Synthetic'}];finish({fee:2});await p;assert.equal(x.calls.length,0);assert.equal(x.c.S.okey,null);
});
await test('U04 review cannot replace unresolved payload after ACK loss',async()=>{
 const x=app(),driver=ctl();driver.rpc(async()=>{throw Error('ACK lost')});x.c.TLB.placeOrder=o=>driver.client.submit({p_key:o.key,p_items:o.lines,p_tip:o.tip,p_extra:o.extra},true);
 await x.c.place();const key=driver.state().active,prior=structuredClone(driver.state().attempts[key].payload);x.c.S.cart[I]=3;x.c.priceRememberDisplayed01();
 const next=await driver.client.submit({p_key:'qa_price_alternate',p_items:[],p_extra:{price01:review(40)}},true);assert.equal(next.reason,'previous_attempt_unresolved');assert.equal(driver.calls.length,1);assert.equal(JSON.stringify(driver.state().attempts[key].payload),JSON.stringify(prior));
});
await test('U05 fresh controller after loss retains exact price payload',async()=>{
 const shared={states:new Map(),queue:Promise.resolve()},a=ctl(shared);const p={p_key:'qa_price_restart',p_tip:0,p_extra:{price01:review(20)}};a.rpc(async()=>{throw Error('lost')});await a.client.submit(p,true);
 const reopened=ctl(shared);reopened.rpc(async(n,q)=>({data:n==='order_request_status104'?{key:q.p_key,status:'unresolved',reason:'not_visible'}:{key:q.p_key,status:'created',id:'15041'}}));const r=await reopened.client.retrySaved(p.p_key,true);assert.equal(r.status,'created');assert.deepEqual(reopened.calls.at(-1).payload,p);assert.equal(reopened.calls.filter(c=>c.name==='place_order104').length,1);
});
await test('U06 late success preserves newer cart and explicit same tip',async()=>{
 const x=app();x.c.tipSelect02('other');x.c.tipInput02('99');x.c.priceRememberDisplayed01();const p=x.c.place();await x.tick();x.c.S.cart[I]=4;x.c.tipInput02('99');x.c.cartSave();x.finish({status:'created',id:'15042'});await p;assert.equal(x.c.S.cart[I],4);assert.equal(x.c.S.tip,99);assert.equal(x.c.S.okey,null);
});
await test('U07 equal-total component changes need explicit approval then confirm',async()=>{
 const x=app(),j='41000000-0000-4000-8000-000000000092';x.c.S.cart={[I]:1,[j]:1};x.c.menuOf=()=>[{id:I,price:20,discount:0},{id:j,price:20,discount:0}];x.c.priceRememberDisplayed01();const p=x.c.place();await x.tick();const key=x.calls[0].key,id=randomUUID(),r=review(20);r.lines=[{...r.lines[0],qty:1,base_price:'25',unit_price:'25',net_items:'25'},{...r.lines[0],item_id:j,qty:1,base_price:'15',unit_price:'15',net_items:'15'}];
 x.c.TLB.endRejected104=async()=>({status:'ended_rejected',closed:true,closureId:id});x.finish({status:'rejected',error:'price_changed',closed:true,closureId:id,priceReview:r});await p;assert(x.c.S.priceReview01);assert.equal(x.calls.length,1);await x.c.priceApprove01();assert.equal(x.calls.length,1);assert.equal(x.c.S.okey,null);const next=x.c.place();await x.tick();assert.notEqual(x.calls[1].key,key);assert.deepEqual(x.calls[1].extra.price01,r);x.finish({status:'created',id:'15043'});await next;
});
await test('U08 changed closure receipt cannot retire original key',async()=>{
 const x=app(),p=x.c.place();await x.tick();const key=x.calls[0].key;x.finish({status:'rejected',error:'price_changed',closed:true,closureId:randomUUID(),priceReview:review(30)});await p;x.c.TLB.endRejected104=async()=>({status:'ended_rejected',closed:true,closureId:randomUUID()});await x.c.priceApprove01();assert.equal(x.c.S.okey,key);assert(!x.c.S.priceConsent01);assert.equal(x.calls.length,1);
});
await test('U09 quantity three cent price remains exact in consent',async()=>{
 const x=app();x.c.S.cart={[I]:3};x.c.menuOf=()=>[{id:I,price:20.1,discount:0,name:'Synthetic'}];x.c.priceRememberDisplayed01();const sent=x.c.pricePrepare01().value;
 observations.push({case:'U09',sent});fs.writeFileSync('qa-client-quantity-proof.json',JSON.stringify(sent,null,2)+'\n');assert.equal(sent.lines[0].net_items,'60.3');assert.equal(sent.totals.subtotal,'60.3');
});
fs.writeFileSync(process.env.QA_RESULT||'qa-client-results.json',JSON.stringify({scope:'Node VM / exact generated UI + controller / mocked RPC and persistence',source:'bb01f11b855a2898f3f0b0f8908de827be68844b',results,observations},null,2)+'\n');console.log(JSON.stringify(results,null,2));process.exitCode=results.every(r=>r.result==='PASS')?0:1;
