/* Isolated104 candidate. IndexedDB transactions own state; RPC runs outside them. */
(function(g){'use strict';
 const copy=x=>JSON.parse(JSON.stringify(x));
 g.TalabotAttemptStore104=function(factory){
  const dbp=new Promise((resolve,reject)=>{if(!factory)return reject(Error('indexeddb_unavailable'));const q=factory.open('talabot-attempts104',1);q.onupgradeneeded=()=>q.result.createObjectStore('accounts');q.onerror=()=>reject(q.error);q.onblocked=()=>reject(Error('indexeddb_blocked'));q.onsuccess=()=>resolve(q.result);});
  return {transact:async(uid,reduce)=>{const db=await dbp;return new Promise((resolve,reject)=>{let answer,tx;try{tx=db.transaction('accounts','readwrite',{durability:'strict'});}catch(e){reject(e);return;}const table=tx.objectStore('accounts');const q=table.get(uid);q.onsuccess=()=>{try{const state=q.result||{version:1,revision:0,active:null,attempts:{}};if(state.version!==1)throw Error('state_version');answer=reduce(state);state.revision++;table.put(state,uid);}catch(e){tx.abort();reject(e);}};tx.oncomplete=()=>resolve(answer);tx.onerror=()=>reject(tx.error);tx.onabort=()=>reject(tx.error||Error('transaction_aborted'));});}};
 };
 g.TalabotOrder104=function(deps){
  const unknown=reason=>({status:'unresolved',error:'order_outcome_unknown',reason,keepCart:true});
  const current=uid=>deps.user()===uid;
  const transact=(uid,fn)=>deps.store.transact(uid,fn);
  const keyOK=k=>typeof k==='string'&&/^[A-Za-z0-9_-]{8,64}$/.test(k);
  const closed=d=>d.status==='rejected'&&d.closed===true&&d.no_effects===true&&d.state_version===1&&/^[0-9a-f]{8}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{12}$/i.test(d.closure_id||'');
  function normalize(r,key){const d=r&&!r.error&&r.data;if(!d||d.key!==key)return unknown('unverified_response');
   if(['created','replayed','historical_recovered'].includes(d.status)){if(typeof d.id!=='string'||!/^[1-9][0-9]*$/.test(d.id))return unknown('unverified_id');return{status:d.status,id:d.id,input_match:d.input_match,keepCart:d.status==='historical_recovered'};}
   if(['conflict','unresolved','rejected'].includes(d.status))return{status:d.status,error:d.status==='conflict'?'idempotency_mismatch':d.status==='unresolved'?'order_outcome_unknown':d.reason||'creation_rejected',reason:d.reason,keepCart:true,closed:closed(d),closureId:closed(d)?d.closure_id:null};
   return unknown('unverified_response');
  }
  async function submit(payload,fresh=false,context={}){
   const uid=deps.user(),key=payload&&payload.p_key;if(!uid||!keyOK(key))return unknown('identity_or_key_missing');let claim;
   try{claim=await transact(uid,s=>{
    if(!current(uid))return{stop:unknown('identity_changed')};
    if(s.active&&s.active!==key)return{stop:Object.assign(unknown('previous_attempt_unresolved'),{recoveryKey:s.active})};
    let a=s.attempts[key];
    if(!a){const id=deps.uuid();if(!id)throw Error('attempt_id_unavailable');a=s.attempts[key]={id,key,version:0,state:fresh===true?'new':'unresolved',payload:copy(payload),sent:false,cartToken:context.cartToken||null};}
    if(a.state==='ended_rejected')return{stop:{status:'rejected',error:'attempt_closed',reason:'attempt_closed',keepCart:true,ended:true}};
    // A committed success may be re-read; it cannot resurrect a create.
    const create=(fresh===true&&a.state==='new')||(fresh==='retry'&&a.sent&&a.state==='unresolved'&&a.reason==='not_visible');
    if(create&&!a.payload)return{stop:unknown('original_payload_unavailable')};
    a.version++;a.state='pending';if(create)a.sent=true;s.active=key;
    return{id:a.id,version:a.version,key,create,payload:copy(a.payload||{p_key:key}),cartToken:a.cartToken};
   });if(claim.stop)return claim.stop;}catch(e){return unknown('durable_state_unavailable');}
   let result;
   try{
    const r=await deps.rpc(claim.create?'place_order104':'order_request_status104',claim.create?claim.payload:{p_key:key});
    if(!current(uid))return unknown('identity_changed');result=normalize(r,key);
    if(result.id&&(typeof deps.readOrder!=='function'||await deps.readOrder(result.id)!==true))result=unknown('saved_order_reload_failed');
    if(!current(uid))return unknown('identity_changed');
   }catch(e){result=unknown('transport_or_storage');}
   try{return await transact(uid,s=>{
    if(!current(uid))return unknown('identity_changed');const a=s.attempts[key];
    if(!a||a.id!==claim.id||a.version!==claim.version)return unknown('stale_reply');
    a.version++;a.state=result.status;a.reason=result.reason||null;a.closureId=result.closureId||null;a.closed=result.closed===true;
    result.keepCart=result.keepCart||!claim.create||context.cartToken!==undefined&&context.cartToken!==claim.cartToken||JSON.stringify(payload)!==JSON.stringify(claim.payload);
    if(result.id){a.orderId=result.id;a.payload=null;a.cartToken=null;if(s.active===key)s.active=null;}
    return result;
   });}catch(e){return unknown('durable_state_unavailable');}
  }
  async function retrySaved(key,approved){if(approved!==true)return unknown('explicit_confirmation_required');const uid=deps.user();let a;try{a=await transact(uid,s=>copy(s.attempts[key]||null));}catch(e){return unknown('durable_state_unavailable');}if(!current(uid)||!a||!a.sent||!a.payload)return unknown('original_payload_unavailable');const check=await submit(a.payload,false);if(check.status!=='unresolved'||check.reason!=='not_visible')return check;return submit(a.payload,'retry');}
  async function endRejected(key,approved){if(approved!==true)return unknown('explicit_confirmation_required');const uid=deps.user();const checked=await submit({p_key:key},false);if(!current(uid)||checked.status!=='rejected'||!checked.closed||!checked.closureId)return unknown('rejection_not_proven');
   try{return await transact(uid,s=>{if(!current(uid))return unknown('identity_changed');const a=s.attempts[key];if(!a||a.state!=='rejected'||a.closureId!==checked.closureId||!a.closed||s.active!==key)return unknown('closure_changed');a.version++;a.state='ended_rejected';a.payload=null;a.cartToken=null;s.active=null;return{status:'ended_rejected',key,closed:true,keepCart:true,closureId:a.closureId};});}catch(e){return unknown('durable_state_unavailable');}
  }
  return {submit,recover:key=>submit({p_key:key},false),retrySaved,endRejected};
 };
})(globalThis);
