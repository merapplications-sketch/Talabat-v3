// Actual .31 recovery handlers, isolated DOM/Auth doubles: no email or live API.
const fs=require('node:fs'),vm=require('node:vm'),assert=require('node:assert/strict'),crypto=require('node:crypto');
const source=fs.readFileSync(process.argv[2],'utf8');
const start=source.indexOf('  var recoveryPending = false;'),end=source.indexOf('  function showLogin(msg, mode)',start);
assert(start>=0&&end>start,'recovery source boundaries missing');
const fragment=source.slice(start,end);
function harness(){
 const nodes={},calls=[],logins=[];let resolve,reject;
 const ctx={IN:'',BT:'',location:{origin:'https://fixture.invalid',pathname:'/customer',search:'?redirect=https://untrusted.invalid',hash:'#secret'},
  $:id=>nodes[id]||null,t:x=>x,bootHide(){},authErr:()=> 'sanitized',
  overlay(html){for(const m of html.matchAll(/id="([^"]+)"/g))nodes[m[1]]={value:'',disabled:false,textContent:'',hidden:true};},
  showLogin:(...x)=>logins.push(x),signOutRemote:async opts=>{calls.push(['logout',opts]);return {};},
  sb:{auth:{resetPasswordForEmail:(...x)=>{calls.push(['reset',...x]);return new Promise((a,b)=>{resolve=a;reject=b});},
  updateUser:(...x)=>{calls.push(['update',...x]);return new Promise((a,b)=>{resolve=a;reject=b});}}}};
 vm.createContext(ctx);vm.runInContext(fragment,ctx);
 return {ctx,nodes,calls,logins,resolve:x=>resolve(x),reject:x=>reject(x)};
}
const flush=()=>new Promise(r=>setImmediate(r));
(async()=>{
 let h=harness();h.ctx.showResetRequest();h.nodes['tlb-rem'].value='bad';h.nodes['tlb-rgo'].onclick();assert.equal(h.calls.length,0);
 h.nodes['tlb-rem'].value='  SYNTHETIC@TALABOT-TEST.INVALID ';h.nodes['tlb-rgo'].onclick();h.nodes['tlb-rgo'].onclick();
 assert.equal(h.calls.length,1);assert.equal(h.calls[0][1],'synthetic@talabot-test.invalid');assert.equal(h.calls[0][2].redirectTo,'https://fixture.invalid/customer');
 h.resolve({});await flush();assert.equal(h.nodes['tlb-rsent'].hidden,false);assert.equal(h.nodes['tlb-rgo'].disabled,true);
 h=harness();h.ctx.showResetRequest();h.nodes['tlb-rem'].value='x@talabot-test.invalid';h.nodes['tlb-rgo'].onclick();h.reject(Error('SECRET'));await flush();
 assert.equal(h.nodes['tlb-rerr'].textContent,'err_generic');assert.equal(h.nodes['tlb-rgo'].disabled,false);h.nodes['tlb-rgo'].onclick();assert.equal(h.calls.length,2);h.resolve({});await flush();
 h=harness();h.ctx.showResetRequest();h.nodes['tlb-rem'].value='x@talabot-test.invalid';h.nodes['tlb-rgo'].onclick();h.resolve({error:{status:429,message:'SECRET'}});await flush();assert.equal(h.calls.length,1);assert.equal(h.nodes['tlb-rerr'].textContent,'sanitized');
 function ready(){const h=harness();h.ctx.showPasswordRecovery();h.nodes['tlb-newpw'].value='Synthetic-only-123';h.nodes['tlb-newpw2'].value='different';return h;}
 h=ready();h.nodes['tlb-savepw'].onclick();assert.equal(h.calls.length,0);assert.equal(h.nodes['tlb-rerr'].textContent,'resetMismatch');
 h.nodes['tlb-newpw2'].value=h.nodes['tlb-newpw'].value;h.nodes['tlb-savepw'].onclick();h.nodes['tlb-savepw'].onclick();assert.equal(h.calls.length,1);
 h.resolve({});await flush();assert.equal(h.calls[1][0],'logout');assert.equal(h.calls[1][1].scope,'global');assert.equal(h.logins[0][0],'resetDone');assert.equal(h.ctx.recoveryPending,false);
 h=ready();h.nodes['tlb-newpw2'].value=h.nodes['tlb-newpw'].value;h.nodes['tlb-savepw'].onclick();h.resolve({error:{message:'SECRET'}});await flush();assert.equal(h.logins.length,0);assert.equal(h.calls.length,1);assert.equal(h.nodes['tlb-savepw'].disabled,false);
 for(const rejectLogout of [false,true]){
  h=ready();h.ctx.signOutRemote=()=>rejectLogout?Promise.reject(Error('SECRET')):Promise.resolve({error:{message:'SECRET'}});
  h.nodes['tlb-newpw2'].value=h.nodes['tlb-newpw'].value;h.nodes['tlb-savepw'].onclick();h.resolve({});await flush();assert.equal(h.logins[0][0],'resetDone signoutIncomplete');
 }
 console.log(JSON.stringify({result:'PASS',source_sha256:crypto.createHash('sha256').update(source).digest('hex'),
  covered:['invalid_email_no_request','normalization','redirect_excludes_query_and_hash','double_click_single_request','generic_success','network_failure_manual_retry','429_no_automatic_retry','password_mismatch_no_write','password_update_single_write','global_signout_requested','update_failure_no_login','signout_failure_warning'],
  limitations:['Auth responses mocked','no mail delivery','no token expiry/reuse proof','no provider session revocation proof','no MFA recovery closure','no device compatibility proof']},null,2));
})().catch(e=>{console.error(e);process.exitCode=1;});
