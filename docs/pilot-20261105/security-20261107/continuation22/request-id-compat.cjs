const fs=require('node:fs'),vm=require('node:vm'),assert=require('node:assert/strict'),{webcrypto}=require('node:crypto');
const s=fs.readFileSync('public/talabat-core.js','utf8');
const helper=(s.match(/  function secureRequestId\(\) \{[\s\S]*?\n  \}/)||[''])[0];
const approval=s.slice(s.indexOf('  async function approvalWrite('),s.indexOf('  function rpc(',s.indexOf('  async function approvalWrite(')));
const ret=s.slice(s.indexOf('    writeOrderReturn: async function'),s.indexOf('    driverAccept:',s.indexOf('    writeOrderReturn: async function'))).trim().replace(/^writeOrderReturn: async function/,'async function writeOrderReturn').replace(/,$/,'');
const fin=s.match(/  function finCommand\([^\n]+/)[0];
const UUID=/^[0-9a-f]{8}-[0-9a-f]{4}-4[0-9a-f]{3}-[89ab][0-9a-f]{3}-[0-9a-f]{12}$/i;
function setup(crypto){const calls=[],data=new Map(),st={state:'idle'},ctx={crypto,window:{crypto},Uint8Array,TextEncoder,UUID,ME:{id:'synthetic'},DB:{approvalReady:true},localStorage:{getItem:k=>data.get(k)||null,setItem:(k,v)=>data.set(k,v),removeItem:k=>data.delete(k)},sb:{rpc:async(name,args)=>{calls.push({name,args:{...args}});return{data:{request:args.p_request}};}},refresh:async()=>{},errKey:e=>e.message,FIN:{access:{execute:true,receipts:true},cash:{}},finSlot:()=>st,finPersist:()=>true,fireSoon:()=>{},finSafe:p=>p,toast:()=>{},t:x=>x};vm.createContext(ctx);vm.runInContext(helper+'\n'+approval+'\n'+ret+'\n'+fin,ctx);return{ctx,calls,st};}
(async()=>{
 const crypto={getRandomValues:a=>webcrypto.getRandomValues(a),subtle:webcrypto.subtle};
 const {ctx,calls}=setup(crypto);
 const a=await ctx.approvalWrite('customer_confirm_order',{p_order:99,p_revision:1},1);assert.equal(a.error,undefined,'approval must work without randomUUID');
 await ctx.approvalWrite('customer_confirm_order',{p_order:99,p_revision:1},1);assert.equal(calls[0].args.p_request,calls[1].args.p_request,'approval retry keeps key');
 await ctx.writeOrderReturn(99,'confirm',null,1,'cash');await ctx.writeOrderReturn(99,'confirm',null,1,'cash');assert.equal(calls[2].args.p_request,calls[3].args.p_request,'return retry keeps key');
 const result=await ctx.finCommand('settle_cash','synthetic',null,null);assert.equal(result.ok,true);for(const c of calls)assert.match(c.args.p_request,UUID);
 const no=setup({subtle:webcrypto.subtle});assert.equal((await no.ctx.approvalWrite('confirm',{},1)).error,'storage_unavailable');await no.ctx.writeOrderReturn(99,'confirm');assert.equal((await no.ctx.finCommand('settle_cash','x')).error,'storage_unavailable');assert.equal(no.calls.length,0,'no weak randomness or RPC if crypto absent');
 const held=setup(crypto);held.st.state='unresolved';assert.equal((await held.ctx.finCommand('settle_cash','x')).unresolved,true);assert.equal(held.calls.length,0);
 const native=setup(webcrypto);assert.equal((await native.ctx.finCommand('settle_cash','x')).ok,true);assert.match(native.calls[0].args.p_request,UUID);
 console.log('PASS: three request paths, stable approval/return retries, unresolved finance guard, native path and fail-closed crypto absence');
})().catch(e=>{console.error(e);process.exitCode=1;});
