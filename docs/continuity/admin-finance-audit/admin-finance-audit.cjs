const fs=require('node:fs');
const vm=require('node:vm');
const assert=require('node:assert/strict');
const p=JSON.parse(fs.readFileSync('audit-parts.json','utf8'));
const out=[];
const ev=(s,c)=>vm.runInNewContext('('+s+')',c);
async function check(name,f){await f();out.push({name,result:'REPRODUCED'});}
(async()=>{
 await check('wallet actor present in response is discarded',async()=>{
  const entry={id:1,amount:25,kind:'adjust',created_by:'accountant-synthetic',created_at:'2026-11-01T00:00:00Z'};
  const sb={rpc:async()=>({data:25}),from:()=>({select(){return this},eq(){return this},order(){return this},limit:async()=>({data:[entry]})})};
  const r=await ev(p.walletOf,{sb})( 'customer-synthetic');assert.equal(r.balance,25);assert.equal(r.entries[0].created_by,undefined);assert.equal(r.entries[0].at,Date.parse(entry.created_at));
 });
 await check('wallet transport failure becomes zero and empty history',async()=>{
  const sb={rpc:async()=>({error:{message:'synthetic denied'}}),from:()=>({select(){return this},eq(){return this},order(){return this},limit:async()=>({error:{message:'synthetic denied'}})})};
  const r=await ev(p.walletOf,{sb})('customer-synthetic');assert.equal(r.balance,0);assert.equal(r.entries.length,0);assert.equal(r.error,undefined);
 });
 await check('audit permission/load error becomes empty history',async()=>{
  const sb={from:()=>({select(){return this},order(){return this},limit:async()=>({error:{message:'synthetic denied'}})})};
  const r=await ev(p.audit,{sb})(100);assert.equal(r.length,0);
 });
 await check('accounting staff audit actor displays truncated UUID',()=>{
  const nm=vm.runInNewContext(p.nm+';nm',{TLB:{drivers:()=>[{id:'driver-synthetic',name:'Courier'}]},esc:x=>x});
  assert.equal(nm('accountant-synthetic'),'accounta');assert.equal(nm('driver-synthetic'),'Courier');
 });
 await check('cash load failure overwrites last known cash balance',async()=>{
  const DB={cash:{'driver-synthetic':57},orders:[],chat:[],contacts:{},myOffers:[]};
  const sb={rpc:async()=>({error:{message:'synthetic unavailable'}})};
  const fn=ev(p.loadOrders,{DB,sb,ME:{role:'admin'},ordersQuery:()=>Promise.resolve({data:[]}),ACTIVE:[],extraOrders:{},changed:()=>true});
  await fn();assert.equal(DB.cash['driver-synthetic'],undefined);assert.equal(DB.cash['driver-synthetic']||0,0);
 });
 await check('delegated finance staff customer role skips cash RPC',async()=>{
  let calls=0;
  const DB={cash:{},orders:[],chat:[],contacts:{},myOffers:[]};
  const sb={rpc:async()=>{calls++;return {data:[]}}};
  const fn=ev(p.loadOrders,{DB,sb,ME:{role:'customer'},MYPERMS:['finance'],ordersQuery:()=>Promise.resolve({data:[]}),ACTIVE:[],extraOrders:{},changed:()=>true});
  await fn();assert.equal(calls,1); // active_contacts only, cash_balances was skipped
  assert.equal(Object.keys(DB.cash).length,0);
 });
 await check('two settlement clicks start two RPCs while first pending',async()=>{
  let calls=0;const pending=[];
  const sb={rpc:()=>{calls++;return new Promise(resolve=>pending.push(resolve))}};
  const settleCash=ev(p.settleCash,{sb,toast:()=>{},t:x=>x,refresh:async()=>{},console,errKey:()=>''});
  const promises=[];
  const settle=vm.runInNewContext(p.settle+';settle',{confirm:()=>true,t:x=>x,run:x=>promises.push(x),TLB:{settleCash}});
  settle('driver-synthetic',57);settle('driver-synthetic',57);assert.equal(calls,2);
  pending.forEach(resolve=>resolve({data:57}));await Promise.all(promises);
 });
 console.log(JSON.stringify({scope:'Isolated Node VM; exact function slices; no network or database; reproduced defects, not successful accounting actions',checks:out},null,2));
})().catch(e=>{console.error(e);process.exitCode=1});
