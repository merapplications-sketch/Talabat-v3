const fs=require('node:fs'),vm=require('node:vm'),assert=require('node:assert/strict');
const s=fs.readFileSync(process.argv[2]+'/public/talabat-core.js','utf8');
const fn=s.slice(s.indexOf('  function showPasswordRecovery()'),s.indexOf('  function showLogin(msg, mode)'));
const tick=()=>new Promise(r=>setImmediate(r));
async function test(kind){const nodes={},events=[];let release;const ctx={recoveryPending:false,$:id=>nodes[id],bootHide(){},IN:'',BT:'',t:x=>x,authErr:()=> 'safe_error',showLogin:m=>events.push('login:'+m),overlay:()=>['tlb-newpw','tlb-newpw2','tlb-rerr','tlb-savepw'].forEach(k=>nodes[k]={value:'fixture-password-not-real',textContent:'',disabled:false}),sb:{auth:{updateUser:()=>{events.push('update');return new Promise(r=>release=r);},signOut:async options=>{events.push('signout:'+options.scope);return kind==='logout-error'?{error:{}}:{};}}}};
vm.createContext(ctx);vm.runInContext(fn+';this.show=showPasswordRecovery;',ctx);ctx.show();
if(kind==='mismatch')nodes['tlb-newpw2'].value='different-fixture';
nodes['tlb-savepw'].onclick();nodes['tlb-savepw'].onclick();
if(kind==='mismatch'){assert.deepEqual(events,[]);assert.equal(nodes['tlb-rerr'].textContent,'resetMismatch');return;}
assert.deepEqual(events,['update']);assert.equal(nodes['tlb-savepw'].disabled,true);
release(kind==='update-error'?{error:{}}:{});await tick();await tick();
if(kind==='update-error'){assert.deepEqual(events,['update']);assert.equal(nodes['tlb-savepw'].disabled,false);assert.equal(ctx.recoveryPending,true);}
else {assert.equal(events[1],'signout:global');assert.equal(events[2],kind==='logout-error'?'login:resetDone signoutIncomplete':'login:resetDone');assert.equal(ctx.recoveryPending,false);}
assert.equal(/mfa\.unenroll|enterAuthorized/.test(fn),false);
}
(async()=>{for(const k of ['mismatch','update-error','success','logout-error'])await test(k);console.log('4 offline recovery cases passed: mismatch, pending duplicate, update failure, fresh login/global signout outcome. No mail delivery/device/live MFA claim.');})().catch(e=>{console.error(e);process.exitCode=1;});
