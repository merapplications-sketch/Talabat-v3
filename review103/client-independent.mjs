import fs from 'node:fs';import vm from 'node:vm';import assert from 'node:assert/strict';
const root=process.env.SOURCE_ROOT||'recovery/isolated97';const code=fs.readFileSync(root+'/tests/native103/client.js','utf8');
const ctx={};vm.createContext(ctx);vm.runInContext(code,ctx);
const results=[];const obs=(id,ok,detail)=>results.push({id,expected_protection:ok,detail});
function storage(){const m=new Map();return{getItem:k=>m.get(k)||null,setItem:(k,v)=>m.set(k,v),removeItem:k=>m.delete(k)}}
const defer=()=>{let resolve;const promise=new Promise(r=>resolve=r);return{promise,resolve}};
const ok=(key,id='501')=>({data:{status:'created',key,id,input_match:true}});
function factory(st,rpc){return ctx.TalabotOrder103({storage:st,user:()=> 'synthetic-user',rpc,readOrder:async()=>true})}
// Two separate tab controllers share origin storage; delayed responses use a real async boundary.
{
 const st=storage(),ack=defer(),second=defer();let thirdWrites=0;
 const A=factory(st,()=>ack.promise),B=factory(st,async(n,p)=>n==='order_request_status103'?ok(p.p_key):second.promise);
 const p=A.submit({p_key:'review103_first'},true);
 await B.recover('review103_first'); // another tab verifies committed first operation
 const p2=B.submit({p_key:'review103_second'},true); // legitimate next order, still in flight
 ack.resolve(ok('review103_first'));await p;
 const active=st.getItem('tlb-order103-active:synthetic-user');
 const C=factory(st,async(n,p)=>{if(n==='place_order103')thirdWrites++;return{data:{status:'unresolved',reason:'not_visible',key:p.p_key}}});
 await C.submit({p_key:'review103_third'},true);
 obs('QA103-C01',active==='review103_second'&&thirdWrites===0,{activeAfterLateFirstAck:active,thirdCreateRPCs:thirdWrites});
 second.resolve({data:{status:'unresolved',reason:'not_visible',key:'review103_second'}});await p2;
}
// Rejected request followed by corrected input cannot progress or be explicitly ended through exposed API.
{
 const st=storage();let writes=0;const c=factory(st,async(n,p)=>{if(n==='place_order103'){writes++;return{data:{status:'rejected',reason:'address_required',key:p.p_key}}}return{data:{status:'unresolved',reason:'not_visible',key:p.p_key}}});
 await c.submit({p_key:'review103_reject',p_address:''},true);
 const corrected=await c.submit({p_key:'review103_reject',p_address:'corrected'},true);
 const replacement=await c.submit({p_key:'review103_correct',p_address:'corrected'},true);
 obs('QA103-C03',false,{writes,corrected:corrected.status,replacement:replacement.reason,api:Object.keys(c),note:'No reconciliation-aware cancel/edit API; safety retained but flow stuck'});
}
// Generate and execute the actual customer place() body, not a parallel implementation.
const ui=fs.readFileSync(process.env.CANDIDATE_UI||'/tmp/review103-client/customer.html','utf8');
const body=ui.slice(ui.indexOf('async function place(){'),ui.indexOf("let phErr=''"));
{
 const ack=defer(),started=defer();const c={Date,JSON,Object,Math,String,Promise,console,S:{cart:{original:1},cartStore:'store',tip:0,pay:'cash',v:'pay',okey:null},ME:{phone:'synthetic'},render(){},alert(){},confirm:()=>false,t:x=>x,closedNow:()=>false,badKeys:()=>[],curAddr:()=>({lat:38,lng:68}),newKey:()=> 'review103_cart',ensureQuote:async()=>({fee:2}),lineNotes:()=>[''],pk:()=>({id:'item',ops:[]}),addrText:()=> 'synthetic',calc:()=>({fw:0,w:0,pts:0}),optExtra:()=>null,errMsg:r=>r.error,prefSave(){},grpEnd(){},go(v,o){c.S.v=v},TLB:{placeOrder:async()=>{started.resolve();return ack.promise}}};vm.createContext(c);vm.runInContext(body,c);
 const run=c.place();await started.promise;c.S.cart={edited:3};ack.resolve({status:'created',id:'501',keepCart:false});await run;
 obs('QA103-C02',c.S.cart.edited===3,{cartAfterReply:c.S.cart,note:'VM mutation during asynchronous send; not a real browser UI journey'});
}
fs.writeFileSync('review103/client-results.json',JSON.stringify(results,null,2));console.log(JSON.stringify(results,null,2));
