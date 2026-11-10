/* Candidate-only transport state machine. No design/layout change; no automatic mutation retry. */
(function(g){'use strict';g.TalabotOrder103=function(deps){
 const pending=new Map();
 const unknown=(reason)=>({status:'unresolved',error:'order_outcome_unknown',reason,keepCart:true});
 const slot=(uid,key)=>'tlb-order103:'+uid+':'+key;
 function normalize(r,key){
  const d=r&&!r.error&&r.data;
  if(!d||d.key!==key||!['created','replayed','historical_recovered','conflict','unresolved','rejected'].includes(d.status))return unknown('unverified_response');
  if(['created','replayed','historical_recovered'].includes(d.status)){
   if(!/^[1-9][0-9]*$/.test(String(d.id||'')))return unknown('unverified_id');
   return {status:d.status,id:String(d.id),input_match:d.input_match,keepCart:d.status==='historical_recovered'};
  }
  return {status:d.status,error:d.status==='conflict'?'idempotency_mismatch':d.status==='unresolved'?'order_outcome_unknown':d.reason||'creation_rejected',reason:d.reason,keepCart:true};
 }
 async function submit(payload,fresh){
  const uid=deps.user(),key=payload&&payload.p_key;
  if(!uid||!/^[A-Za-z0-9_-]{8,64}$/.test(key||''))return unknown('identity_or_key_missing');
  const name=slot(uid,key);if(pending.has(name))return unknown('pending');
  let record;
  try{const raw=deps.storage.getItem(name);record=raw?JSON.parse(raw):null;
   if(!record){record={version:1,user:uid,key,payload:JSON.parse(JSON.stringify(payload)),state:fresh?'new':'unresolved'};deps.storage.setItem(name,JSON.stringify(record));}
   if(record.user!==uid||record.key!==key||record.version!==1)return unknown('stored_request_invalid');
  }catch(e){return unknown('storage_unavailable');}
  pending.set(name,true);
  try{
   const create=(fresh===true&&record.state==='new')||(fresh==='retry'&&record.sent===true&&record.reason==='not_visible');
   if(create)record.sent=true;
   record.state='pending';deps.storage.setItem(name,JSON.stringify(record));
   const r=await deps.rpc(create?'place_order103':'order_request_status103',create?record.payload:{p_key:key});
   if(deps.user()!==uid)return unknown('identity_changed');
   const result=normalize(r,key);
   result.keepCart=result.keepCart||JSON.stringify(payload)!==JSON.stringify(record.payload);
   record.state=result.status;record.reason=result.reason||null;record.orderId=result.id||null;deps.storage.setItem(name,JSON.stringify(record));
   if(!result.keepCart&&result.id)deps.storage.removeItem(name);
   return result;
  }catch(e){record.state='unresolved';try{deps.storage.setItem(name,JSON.stringify(record));}catch(_){}return unknown('transport_or_storage');}
  finally{pending.delete(name);}
 }
 async function retrySaved(key,approved){
  if(approved!==true)return unknown('explicit_confirmation_required');
  let record;try{record=JSON.parse(deps.storage.getItem(slot(deps.user(),key))||'null');}catch(e){return unknown('storage_unavailable');}
  if(!record||!record.sent)return unknown('original_payload_unavailable');
  const check=await submit(record.payload,false);
  if(check.status!=='unresolved'||check.reason!=='not_visible')return check;
  return submit(record.payload,'retry');
 }
 return {submit,recover:key=>submit({p_key:key},false),retrySaved};
};})(typeof globalThis==='object'?globalThis:window);
