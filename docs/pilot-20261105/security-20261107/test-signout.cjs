const fs=require('node:fs'),vm=require('node:vm');
const source=fs.readFileSync(process.argv[2],'utf8');
const vendor=fs.readFileSync(process.argv[3],'utf8');
const vc={console,URL,URLSearchParams,TextEncoder,TextDecoder,setTimeout,clearTimeout};vm.createContext(vc);vm.runInContext(vendor,vc);const sdk=vc.supabase;
const mode=process.argv[4]||'error';
(async()=>{
 let cleared=false,serverRevoked=false;
 const fake={_useSession:fn=>fn({data:{session:{access_token:'synthetic-local-only'}},error:null}),_removeSession:async()=>{cleared=true},_returnResult:x=>x,admin:{signOut:async()=>({error:mode==='success'?null:new sdk.AuthApiError('synthetic-server-failure',503,'server_error')})}};
 const result=await sdk.AuthClient.prototype._signOut.call(fake,{scope:'global'});
 let reloaded=false,logoutMessage=null;
 const context={t:x=>x,showLogin:message=>{logoutMessage=message},sb:{auth:{signOut:async()=>{if(mode==='reject')throw Error('synthetic-rejection');return result;}}},location:{reload:()=>{reloaded=true}}};
 const logout=source.split('\n').find(line=>line.includes('function logout()'));
 vm.runInNewContext(logout+';logout()',context);await new Promise(r=>setImmediate(r));
 // Exercise actual recovery renderer with synthetic DOM fields and auth calls.
 let loginMessage=null,scope=null;const fields={};const get=id=>fields[id]||(fields[id]={value:'SyntheticPassword1!',style:{},disabled:false});
 const recovery=source.slice(source.indexOf('  function showPasswordRecovery()'),source.indexOf('  function showLogin(',source.indexOf('  function showPasswordRecovery()')));
 const rc={$:id=>id==='tlb-newpw'&&!fields[id]?null:get(id),bootHide:()=>{},overlay:()=>{fields['tlb-newpw']={value:'SyntheticPassword1!'};get('tlb-newpw2');},IN:'',BT:'',t:x=>x,showLogin:message=>{loginMessage=message},authErr:()=> 'err_generic',sb:{auth:{updateUser:async()=>({error:null}),signOut:async options=>{scope=options.scope;if(mode==='reject')throw Error('synthetic-rejection');return result;}}}};
 vm.runInNewContext(recovery+';showPasswordRecovery()',rc);get('tlb-savepw').onclick();await new Promise(r=>setImmediate(r));
 console.log(JSON.stringify({vendor:{errorReturned:!!result.error,localSessionCleared:cleared,serverRevocationNotConfirmed:mode!=='success'},logout:{reloadedDespiteError:reloaded,errorShown:logoutMessage==='signoutIncomplete'},recovery:{scope,loginMessage,completionShownDespiteRevocationError:mode!=='success'&&loginMessage==='resetDone',errorShown:!!loginMessage&&loginMessage.includes('signoutIncomplete')}},null,2));
})();
