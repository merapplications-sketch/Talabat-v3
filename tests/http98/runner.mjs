import {identities} from '../http97/runner.mjs';
const fields=['online','last_seen','lat','lng','loc_acc','loc_updated'];
export async function runFixture(t,role){
 // Deliberately cannot target hosted accounts. Live transport approval remains separate.
 if(!t)return {status:'BLOCKED',reason:'approved transport missing'};
 if(t.environment!=='isolated-synthetic')return {status:'BLOCKED',reason:'mutating cases are isolated-fixture only'};
 if(!Object.hasOwn(identities,role))throw Error('unreserved_role');
 let u;try{u=await t.identity()}catch{throw Error('identity_unavailable')}
 if(u.id!==identities[role])throw Error('identity_mismatch');
 const results=[];let saved;
 const request=async(method,path,body,query)=>t.request({method,path,body,query});
 const read=async()=>{const r=await request('GET','/rest/v1/profiles',undefined,{id:'eq.'+u.id,select:['id','name',...fields].join(',')});if(r.status!==200||r.data?.length!==1||r.data[0].id!==u.id)throw Error('baseline_missing');return r.data[0]};
 const record=(id,r,ok)=>results.push({id,http:r.status,status:ok?'PASS':'FAIL',error:['42501','PGRST301','not_allowed','account_blocked'].includes(r.code)?r.code:null});
 try{
  saved=await read();
  for(const field of fields){const body={[field]:field==='online'?!saved[field]:field.includes('seen')||field.includes('updated')?'2026-01-01T00:00:00Z':42};const r=await request('PATCH','/rest/v1/profiles',body,{id:'eq.'+u.id});record('deny-'+field,r,r.status===403&&r.code==='42501'&&JSON.stringify(await read())===JSON.stringify(saved))}
  let r=await request('PATCH','/rest/v1/profiles',{name:'Synthetic98',online:!saved.online},{id:'eq.'+u.id});record('mixed-atomic',r,r.status===403&&r.code==='42501'&&JSON.stringify(await read())===JSON.stringify(saved));
  r=await request('PATCH','/rest/v1/profiles',{name:'Synthetic98'},{id:'eq.'+u.id});record('allowed-name',r,[200,204].includes(r.status)&&(await read()).name==='Synthetic98');
  r=await request('POST','/rest/v1/rpc/finance_settlement_receipts',{p_order_ids:['980001']});record('receipt-access',r,r.status===200&&Array.isArray(r.data)&&(role==='finance'?r.data.length===1&&r.data[0].order_id==='980001'&&r.data[0].receipt?.amount===5:r.data.length===0));
  r=await request('POST','/rest/v1/rpc/finance_customers',{p_q:'',p_limit:1,p_offset:0},{id:'eq.'+identities.outsider,select:'id'});record('finance-orders-separation',r,r.status===200&&Array.isArray(r.data)&&(role==='finance'?r.data.length===1&&r.data[0].id===identities.outsider:r.data.length===0));
  if(role==='finance'){r=await request('POST','/rest/v1/rpc/finance_audit',{});record('empty-audit-allowlist',r,r.status===200&&Array.isArray(r.data)&&r.data.length===0)}
 }catch{results.push({id:'measurement',status:'ERROR',error:'bounded_measurement_failure'})}
 finally{
  if(saved){try{const r=await request('PATCH','/rest/v1/profiles',{name:saved.name},{id:'eq.'+u.id});record('cleanup-name',r,[200,204].includes(r.status)&&JSON.stringify(await read())===JSON.stringify(saved))}catch{results.push({id:'cleanup-name',status:'FAIL'})}}
 }
 // Local mock invalidation only; never invokes provider Auth admin or disables an account.
 if(t.invalidateSyntheticSession){await t.invalidateSyntheticSession();for(const path of ['/auth/v1/user','/rest/v1/profiles']){const r=await request('GET',path,undefined,path.includes('profiles')?{id:'eq.'+u.id,select:'id'}:undefined);record('expired-'+path,r,r.status===401)}}
 return {scope:'synthetic adapter contract only; not live HTTP or Auth revocation proof',results};
}
