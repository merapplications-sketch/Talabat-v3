const fs=require('node:fs'),vm=require('node:vm');
const source=fs.readFileSync(process.argv[2],'utf8');
const block=source.slice(source.indexOf('  var proofObjectUrls ='),source.indexOf('  function bootFail('));
let release,created=[],revoked=[],listeners={};
const context={sb:{storage:{from(){return{download(){return new Promise(r=>release=r)}}}}},URL:{createObjectURL(){const u='blob:synthetic-'+(created.length+1);created.push(u);return u;},revokeObjectURL:u=>revoked.push(u)},window:{addEventListener:(event,fn)=>listeners[event]=fn}};
vm.createContext(context);vm.runInContext(block,context);
(async()=>{
 const pending=context.authenticatedProofUrl('synthetic/path.jpg');
 // Same callback invoked by SIGNED_OUT and pagehide in the inspected source.
 context.clearProofUrls();
 release({data:{type:'image/jpeg',size:32}});
 const result=await pending;
 console.log(JSON.stringify({result,created,revoked,remainingUrls:context.proofObjectUrls,clearedBeforeDownloadResolved:true},null,2));
})();
