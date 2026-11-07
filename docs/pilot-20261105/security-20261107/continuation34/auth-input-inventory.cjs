const fs=require('node:fs'),vm=require('node:vm'),assert=require('node:assert/strict'),crypto=require('node:crypto');
const s=fs.readFileSync(process.argv[2],'utf8');
function part(a,b){const start=s.indexOf(a),end=s.indexOf(b,start);assert(start>=0&&end>start);return s.slice(start,end);}
const code=part('  function authTabs()', '  function showSignupDone(')+part('  var recoveryPending = false;', '  var AF =');
const evidence=[];
for(const need of ['customer','merchant','driver','admin']){
 for(const [mode,action,expected] of [
  ['in','login',['tlb-em','tlb-pw']],
  ['up','signup',need==='admin'?['tlb-em','tlb-pw']:['tlb-nm','tlb-ph','tlb-em','tlb-pw']],
  ['in','reset',['tlb-rem']],['in','new-password',['tlb-newpw','tlb-newpw2']]]){
  let nodes={},rendered='';
  const ctx={need,authMode:mode,IN:'',BT:'',t:x=>x,esc:x=>x,bootHide(){},$:(id)=>nodes[id]||null,
   overlay(html){rendered=html;for(const m of html.matchAll(/id="([^"]+)"/g))nodes[m[1]]={value:'',style:{}};}};
  vm.createContext(ctx);vm.runInContext(code,ctx);
  if(action==='reset')ctx.showResetRequest();else if(action==='new-password')ctx.showPasswordRecovery();else ctx.showLogin('',mode);
  const inputs=[...rendered.matchAll(/<input\b[^>]*\bid="([^"]+)"/g)].map(x=>x[1]);
  assert.deepEqual(inputs,expected,need+':'+action);
  evidence.push({role:need,action,inputs});
 }
}
// Explicit distinction: these are fixed password-creation rules, not hints
// derived from the user's existing password or knowledge-based authentication.
assert(s.includes("authPwHint:'At least 8 characters'"));
assert(s.includes("authPwHint2:'At least 8 characters. Create a NEW password for Talabat — do not use your email password.'"));
console.log(JSON.stringify({result:'PASS',source_sha256:crypto.createHash('sha256').update(s).digest('hex'),forms:evidence,
 scope:'Actual shared application forms rendered without submitting credentials; provider account support procedures are outside this source test'},null,2));
