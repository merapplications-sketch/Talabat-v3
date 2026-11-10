import {identities} from '../http97/runner.mjs';
const isolated='https://fsvrsvqfknogwmhccera.supabase.co';
export function createTransport({origin,token,apiKey,uid,role,loopback=false,timeoutMs=5000,receiptOrderId='980001'}){
 const base=new URL(origin);
 if(base.origin!==origin || (origin!==isolated&&!(loopback&&base.protocol==='http:'&&base.hostname==='127.0.0.1')))throw Error('origin_not_approved');
 if(identities[role]!==uid||!token||!apiKey)throw Error('identity_configuration');
 if(!Number.isInteger(timeoutMs)||timeoutMs<20||timeoutMs>30000)throw Error('timeout_configuration');
 if(!/^\d+$/.test(receiptOrderId)||BigInt(receiptOrderId)<=3n)throw Error('receipt_scope');
 async function request({method,path,query={},body}){
  const profile=path==='/rest/v1/profiles',auth=path==='/auth/v1/user';
  const rpc=path.startsWith('/rest/v1/rpc/')?path.slice(13):'';
  if(!((auth&&method==='GET')||(profile&&['GET','PATCH'].includes(method))||(method==='POST'&&['finance_audit','finance_customers','finance_settlement_receipts'].includes(rpc))))throw Error('route_scope');
  if(profile&&(query.id!=='eq.'+uid||Object.keys(query).some(k=>!['id','select'].includes(k))))throw Error('profile_scope');
  if(method==='PATCH'&&(!body||Object.keys(body).length===0||Object.keys(body).some(k=>!['name','online','last_seen','lat','lng','loc_acc','loc_updated'].includes(k))))throw Error('patch_scope');
  if(rpc==='finance_audit'&&(role!=='finance'||JSON.stringify(body)!=='{}'))throw Error('audit_scope');
  if(rpc==='finance_customers'&&(JSON.stringify(body)!==JSON.stringify({p_q:'',p_limit:1,p_offset:0})||query.id!=='eq.'+identities.outsider||query.select!=='id'||Object.keys(query).length!==2))throw Error('customers_scope');
  if(rpc==='finance_settlement_receipts'&&(JSON.stringify(body)!==JSON.stringify({p_order_ids:[receiptOrderId]})||Object.keys(query).length))throw Error('receipt_scope');
  const url=new URL(path,base);for(const[k,v]of Object.entries(query))url.searchParams.set(k,v);
  for(let attempt=0;attempt<(method==='GET'?2:1);attempt++){
   const controller=new AbortController(),timer=setTimeout(()=>controller.abort(),timeoutMs);
   try{
    const r=await fetch(url,{method,headers:{apikey:apiKey,Authorization:'Bearer '+token,'Content-Type':'application/json'},body:body===undefined?undefined:JSON.stringify(body),redirect:'error',signal:controller.signal});
    const reader=r.body?.getReader();let chunks=[],size=0;
    if(reader)while(true){const{done,value}=await reader.read();if(done)break;size+=value.length;if(size>65536){await reader.cancel();throw Error('bounded_response')}chunks.push(value)}
    const raw=Buffer.concat(chunks).toString('utf8'),data=raw?JSON.parse(raw):null;
    return {status:r.status,data,code:['42501','PGRST301','not_allowed','account_blocked'].includes(data?.code)?data.code:null};
   }catch{if(method!=='GET')throw Error('mutation_outcome_unknown');if(attempt===1)throw Error('transport_unavailable')}
   finally{clearTimeout(timer)}
  }
 }
 return {environment:'isolated-http',request,identity:async()=>{const r=await request({method:'GET',path:'/auth/v1/user'});if(r.status!==200||r.data?.id!==uid)throw Error('identity_unavailable');return{id:uid}},scope:'HTTP transport; authorization evidence requires real user sessions'};
}
