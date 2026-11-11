// Baseline price-consent evidence. Real adapter/controller; simulated RPC/store.
// Does not change the client or prove browser/IndexedDB/HTTP behavior.
import fs from 'node:fs';
import vm from 'node:vm';
import assert from 'node:assert/strict';
import {randomUUID,webcrypto} from 'node:crypto';
const core=fs.readFileSync(process.env.PRICE01_CORE,'utf8');
const results=[];
async function check(name,fn){if(process.env.PRICE01_CASE&&!name.startsWith(process.env.PRICE01_CASE))return;try{await fn();results.push({name,assertions:'PASS'});}catch(e){results.push({name,assertions:'FAIL',error:String(e)});}}
const plain=x=>JSON.parse(JSON.stringify(x));
await check('different displayed prices and totals produce identical wire payload',async()=>{
 const start=core.indexOf('    placeOrder: function (o) {'),end=core.indexOf('\n    checkPromo:',start);
 assert(start>0&&end>start);
 const fn=core.slice(start,end).replace('    placeOrder: ','').trim().replace(/,$/,'');
 const ls=core.indexOf('  function linesOf('),le=core.indexOf('  function errKey(',ls);
 assert(ls>0&&le>ls);
 let sent;
 const c={DB:{approvalReady:true},UUID:/^[0-9a-f-]{36}$/i,storeByName:()=>({id:'30000000-0000-4000-8000-000000000092'}),num:Number,
  orderClient103:()=>({submit:p=>{sent=p;return p}})};
 vm.createContext(c);vm.runInContext(core.slice(ls,le)+'\nplace=('+fn+')',c);
 const input={store:'synthetic',lines:[{item_id:'40000000-0000-4000-8000-000000000092',qty:1,options:[],note:'',price:20}],tip:0,payment:'cash',address:'synthetic',lat:38.5,lng:68.7,key:'price01_client_key',fee:2,wallet:5,points:null,extra:null,total:22};
 c.place(input);const first=plain(sent);
 const next=structuredClone(input);next.lines[0].price=30;next.total=32;c.place(next);
 assert.deepEqual(first,plain(sent));assert.deepEqual(Object.keys(first.p_items[0]),['item_id','qty','options','note']);
 assert(!('p_total' in first));assert.equal(first.p_extra,null);
});
await check('delivery quote calls only delivery_quote with store and coordinates',async()=>{
 // Locate the exact known method, preserving source rather than reconstructing it.
 const match=core.match(/quote: function\s*\([^]*?\n    },/);
 assert(match,'quote method must exist');
 const code=match[0].replace(/^quote: /,'').replace(/,$/,'');
 const calls=[];const c={storeByName:()=>({id:'synthetic-store'}),num:Number,errKey:()=> 'error',sb:{rpc:async(n,p)=>{calls.push({n,p});return{data:{fee:2},error:null}}}};
 vm.createContext(c);vm.runInContext('quote=('+code+')',c);await c.quote('synthetic',38.5,68.7);
 assert.equal(calls[0].n,'delivery_quote');assert.deepEqual(Object.keys(calls[0].p).sort(),['p_lat','p_lng','p_store']);
});
await check('unknown attempt retries original payload without adding price data',async()=>{
 const end=core.indexOf('})(globalThis);');assert(end>0);
 const c={setTimeout,clearTimeout,TextEncoder,crypto:webcrypto};vm.createContext(c);vm.runInContext(core.slice(0,end+'})(globalThis);'.length),c);
 let state={version:1,revision:0,active:null,attempts:{}},mode='lost';const calls=[];
 const ctl=c.TalabotOrder104({user:()=> 'synthetic-account',uuid:randomUUID,
  store:{transact:async(u,fn)=>fn(state)},readOrder:async()=>true,
  rpc:async(n,p)=>{calls.push({n,p:plain(p)});if(mode==='lost')throw Error('synthetic lost ACK');return{data:n==='order_request_status104'?{key:p.p_key,status:'unresolved',reason:'not_visible'}:{key:p.p_key,status:'created',id:'15001'}};}});
 const original={p_key:'price01_unknown_key',p_tip:0,p_items:[{item_id:'synthetic',qty:1,options:[]}],p_extra:null};
 assert.equal((await ctl.submit(original,true)).status,'unresolved');
 mode='retry';assert.equal((await ctl.retrySaved(original.p_key,true)).status,'created');
 assert.equal(calls.length,3);assert.equal(calls[1].n,'order_request_status104');assert.deepEqual(calls[2].p,original);
});
const output={scope:'LOCAL Node VM; real generated adapter/controller, synthetic dependencies; baseline only',price01_fix_implemented:false,results};
fs.writeFileSync(process.env.PRICE01_RESULT||'price01-client.json',JSON.stringify(output,null,2)+'\n');
console.log(JSON.stringify(output,null,2));process.exitCode=results.every(x=>x.assertions==='PASS')?0:1;
