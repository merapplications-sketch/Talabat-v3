/* Synthetic stateful server for affected UI journeys. No production connection. */
const fs=require('fs'),path=require('path');
let src=fs.readFileSync(path.join(__dirname,'ui_check.cjs'),'utf8').split('(async()=>{const b=')[0];
let base=new Function('require','__dirname',src+';return base;')(require,__dirname);
function replace(a,b){if(!base.includes(a))throw Error('Fixture source changed: '+a);base=base.replace(a,b)}
replace("window.__readFail={};window.__mode='ok';window.__receipts={};", "window.__readFail={};window.__mode='ok';window.__receipts={};window.__effects=[];window.__walletBalance=45.5;window.__holdCash=null;window.__oldCashReply=null;const pending={...__FT.orders[4],id:'ord7',cash_collected:57,cash_settled_at:null,payment:'cash',created_at:new Date().toISOString()};__FT.orders.push(pending);");
replace("if(name==='finance_access')return Promise.resolve({data:{execute:window.__FIN_ROLE==='accountant'}});", "if(name==='finance_access')return Promise.resolve({data:{execute:window.__FIN_ROLE==='accountant',version:2,capabilities:['commands','settlement_events']}});if(name==='finance_settlement_events')return Promise.resolve({data:__FT.audit_log.filter(e=>args.p_order_ids.includes(e.row_id))});");
replace("if(name==='cash_balances')return Promise.resolve({data:[{driver_id:'30000000-0000-0000-0000-000000000004',balance:57}]});", "if(name==='cash_balances'){const result={data:[{driver_id:__FD,balance:__FT.orders.filter(o=>o.driver_id===__FD&&o.status==='delivered'&&o.cash_collected!=null&&!o.cash_settled_at).reduce((n,o)=>n+o.cash_collected,0)}]};if(__holdCash){__holdCash=false;return new Promise(r=>__oldCashReply=()=>r(result))}return Promise.resolve(result)}");
replace("if(name==='wallet_balance')return Promise.resolve({data:45.5});", "if(name==='wallet_balance')return Promise.resolve({data:__walletBalance});");
const start=base.indexOf("if(name==='finance_execute'){"),end=base.indexOf('return rpc.call(c,name,args)',start);
if(start<0||end<0)throw Error('Missing execution stub');
base=base.slice(0,start)+`if(name==='finance_execute'){
 if(__receipts[args.p_request])return Promise.resolve({data:__receipts[args.p_request]});
 if(__mode==='reject')return Promise.resolve({error:{message:'not_allowed'}});
 const commit=()=>{const at=new Date().toISOString(),orders=[],actor=__FA;let amount=0,entry=null;
 if(args.p_operation==='settle_cash'){__FT.orders.filter(o=>o.driver_id===args.p_target&&o.status==='delivered'&&o.cash_collected!=null&&!o.cash_settled_at).forEach(o=>{amount+=o.cash_collected;o.cash_settled_at=at;orders.push(o.id);__FT.audit_log.unshift({id:'demo-audit-'+__effects.length+'-'+o.id,user_id:actor,at,action:'UPDATE',table_name:'orders',row_id:o.id,details:{cash_settled_at:{from:null,to:at}}})})}
 else {amount=args.p_amount;entry='demo-wallet-'+(__effects.length+1);__walletBalance+=amount;__FT.wallet_entries.unshift({id:entry,user_id:args.p_target,amount,kind:'adjust',note:args.p_note,created_by:actor,created_at:at});__FT.audit_log.unshift({id:'demo-audit-'+entry,user_id:actor,at,action:'INSERT',table_name:'wallet_entries',row_id:entry,details:{amount:{to:amount},note:{to:args.p_note}}})}
 const result={request:args.p_request,operation:args.p_operation,target:args.p_target,amount,orders,wallet_entry:entry,actor,at};__receipts[args.p_request]=result;__effects.push(result);return {data:result};};
 if(__mode==='pending')return new Promise(r=>window.__reply=()=>r(commit()));
 if(__mode==='lost'){commit();return Promise.reject(Error('synthetic response lost'))}
 return Promise.resolve(commit());}
 `+base.slice(end);
module.exports=base;
