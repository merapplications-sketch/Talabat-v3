const fs=require('fs'),vm=require('vm'),assert=require('node:assert/strict');
const source=fs.readFileSync(process.argv[2],'utf8');
const block=source.slice(source.indexOf('  var signOutPending ='),source.indexOf('  var authMode ='));
assert(block.includes('function handleAuthSignedOut'));
function make(identity=true){
 const state={clears:0,reloads:0,timers:[],warnings:[]};
 const ctx={Promise,ME:identity?{id:'synthetic'}:null,document:{body:{style:{}}},clearProofUrls(){state.clears++;},setTimeout(fn){state.timers.push(fn);},location:{reload(){state.reloads++;}},showLogin(msg){state.warnings.push(msg);},t:x=>x,sb:{auth:{signOut:()=>Promise.resolve({error:null})}}};
 vm.createContext(ctx);vm.runInContext(block,ctx);return {ctx,state};
}
(async()=>{
 let {ctx,state}=make();ctx.handleAuthSignedOut();assert.equal(ctx.document.body.style.visibility,'hidden');assert.equal(state.timers.length,1);ctx.handleAuthSignedOut();assert.equal(state.timers.length,1);state.timers[0]();assert.equal(state.reloads,1);
 ({ctx,state}=make(false));ctx.handleAuthSignedOut();assert.equal(state.timers.length,0);assert.equal(ctx.document.body.style.visibility,undefined);
 for(const mode of ['error-result','reject','throw']){
  ({ctx,state}=make());ctx.sb.auth.signOut=()=>{ctx.handleAuthSignedOut();if(mode==='throw')throw new Error('synthetic');if(mode==='reject')return Promise.reject(new Error('synthetic'));return Promise.resolve({error:{message:'synthetic'}});};
  await ctx.logout();assert.equal(state.timers.length,0);assert.equal(state.reloads,0);assert.equal(ctx.document.body.style.visibility,undefined);assert.deepEqual(state.warnings,['signoutIncomplete']);assert.equal(ctx.signOutPending,0);
  ctx.handleAuthSignedOut();assert.equal(state.timers.length,1);
 }
 ({ctx,state}=make());let options;ctx.sb.auth.signOut=x=>{options=x;ctx.handleAuthSignedOut();return Promise.resolve({error:null});};await ctx.signOutRemote({scope:'global'});assert.equal(options.scope,'global');assert.equal(ctx.signOutPending,0);assert.equal(state.timers.length,0);
 console.log(JSON.stringify({result:'pass',cases:['passive_immediate_hide_and_single_reload','repeat_event_deduplicated','initial_no_identity_no_reload','explicit_error_result_warning_preserved','explicit_rejection_warning_preserved','synchronous_throw_warning_preserved','counter_recovers','global_scope_forwarded'],limit:'Extracted application helpers with synthetic DOM/Auth. Does not prove real provider events, browser navigation completion, or erasure of memory before reload.'},null,2));
})().catch(e=>{console.error(e);process.exitCode=1;});
