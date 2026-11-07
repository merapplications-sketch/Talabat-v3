const fs=require('node:fs'),vm=require('node:vm'),assert=require('node:assert/strict');
const source=fs.readFileSync(process.argv[2],'utf8');
const block=source.slice(source.indexOf('  var proofObjectUrls ='),source.indexOf('  function bootFail('));
const pending=[],created=[],revoked=[];
const ctx={sb:{storage:{from(){return{download(path){return new Promise(resolve=>pending.push({path,resolve}))}}}}},URL:{createObjectURL(){const u='blob:synthetic-'+(created.length+1);created.push(u);return u;},revokeObjectURL:u=>revoked.push(u)},window:{addEventListener(){}}};
vm.createContext(ctx);vm.runInContext(block,ctx);
const ok=()=>({data:{type:'image/jpeg',size:32}});
(async()=>{
 const old=ctx.authenticatedProofUrl('old');ctx.clearProofUrls();
 const fresh=ctx.authenticatedProofUrl('new');
 pending[1].resolve(ok());const freshUrl=await fresh;assert.equal(freshUrl,'blob:synthetic-1');
 pending[0].resolve(ok());assert.equal(await old,null,'late previous epoch must fail closed');assert.equal(created.length,1,'old response must not create object URL');
 ctx.clearProofUrls();assert.deepEqual(revoked,[freshUrl]);assert.equal(ctx.proofObjectUrls.length,0);
 const current=ctx.authenticatedProofUrl('current');pending[2].resolve(ok());assert.equal(await current,'blob:synthetic-2');assert.equal(ctx.proofObjectUrls.length,1);
 const late=ctx.authenticatedProofUrl('late');ctx.clearProofUrls();pending[3].resolve(ok());assert.equal(await late,null);assert.equal(created.length,2);assert.equal(ctx.proofObjectUrls.length,0);
 console.log(JSON.stringify({result:'pass',cases:['overlapping_old_and_new_epoch','normal_authorized_completion','clear_revokes_current_url','fresh_epoch_completion','late_resolution_after_clear'],objectURLsCreated:created.length,objectURLsRevoked:revoked.length},null,2));
})().catch(e=>{console.error(e);process.exitCode=1;});
