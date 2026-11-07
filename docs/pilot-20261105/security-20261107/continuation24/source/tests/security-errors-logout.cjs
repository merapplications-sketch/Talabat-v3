const fs=require('node:fs'),vm=require('node:vm'),assert=require('node:assert/strict');
const src=fs.readFileSync('public/talabat-core.js','utf8'),html=fs.readFileSync('public/customer.html','utf8');
const rpc=src.slice(src.indexOf('  function rpc('),src.indexOf('  function done('));
const err=src.slice(src.indexOf('  function errKey('),src.indexOf('  /* Versioned fulfillment'));
const boot=src.slice(src.indexOf('  function bootFail('),src.indexOf('  function logout('));
const marker='INTERNAL_ONLY_MARKER query failed SELECT secret_column';
(async()=>{
 let refreshes=0,logs=[],response={error:{message:marker}},ctx={sb:{rpc:()=>Promise.resolve(response)},console:{error:(...x)=>logs.push(x)},refresh:async()=>{refreshes++;},toast:()=>{},t:x=>x};vm.createContext(ctx);vm.runInContext(err+rpc,ctx);
 const result=await ctx.rpc('test',{});assert.equal(result.error,'generic');assert.equal(JSON.stringify(result).includes(marker),false,'RPC must not return internal text');assert.equal(JSON.stringify(logs).includes(marker),false,'RPC must not log raw internal text');assert.equal(refreshes,0);
 response={error:{message:'note_required'}};assert.equal((await ctx.rpc('test',{})).error,'note_required');assert.equal(refreshes,0);
 response={data:{ok:true}};assert.equal((await ctx.rpc('test',{})).data.ok,true);assert.equal(refreshes,1);
 const fn=html.match(/const errMsg=r=>[^\n]+/)[0];const render={t:x=>x};vm.createContext(render);vm.runInContext(fn+'\nglobalThis.renderError=errMsg',render);assert.equal(render.renderError({error:'generic',detail:marker}).includes(marker),false,'customer must ignore unexpected raw details');
 let called=0,removed=0,reloaded=0;const nodes={'tlb-rl':{},'tlb-rs2':{}};const b={lastErr:'',bootHide:()=>{},clearProofUrls:()=>{},showLogin:()=>{},lang:'en',BT:'',overlay:()=>{},$:x=>nodes[x],logout:()=>{called++;return Promise.resolve();},authStorageKey:'synthetic',localStorage:{removeItem:()=>removed++},location:{reload:()=>reloaded++}};vm.createContext(b);vm.runInContext(boot,b);b.bootFail('network');await nodes['tlb-rs2'].onclick();assert.equal(called,1,'boot signout must invoke existing server logout');assert.equal(removed,0);assert.equal(reloaded,0);
 console.log('PASS: sanitized RPC/customer error, domain error and success retained; boot logout delegates to existing server flow');
})().catch(e=>{console.error(e);process.exitCode=1;});
