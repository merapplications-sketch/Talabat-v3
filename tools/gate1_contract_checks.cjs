#!/usr/bin/env node
'use strict';
// TALABOT Gate1: deterministic source-bound local regression. No network or real data.
const fs=require('node:fs'), vm=require('node:vm'), assert=require('node:assert/strict');
const driver=fs.readFileSync('driver.html','utf8');
const core=fs.readFileSync('talabat-core.js','utf8');
const sql=fs.readFileSync('sql/proposed/gate1_cash_and_idempotent_delivery.sql','utf8');
let passed=0, failed=0;
function check(v,n){if(!v)throw Error(n)}
async function run(name, fn){try{await fn();console.log('PASS '+name);passed++;}catch(e){console.error('FAIL '+name+' '+e.stack);failed++;}}
function slice(s,a,b){let x=s.indexOf(a),y=s.indexOf(b,x+a.length);check(x>=0&&y>x,'anchors '+a);return s.slice(x,y)}
function ctx(o){return vm.createContext(Object.assign({Promise,setTimeout,clearTimeout,console,alert(){},confirm:()=>true},o))}
async function F01(){
 let queue=[], geo=0, errors=[];
 const context=ctx({TLB:{ping:()=>queue.shift()(),unlockAudio(){},testSound(){},ring(){},toast:x=>errors.push(x)},t:x=>x,
    render(){},stopGeo(){},releaseAwake(){},startGeo(){geo++},keepAwake(){},flashTitle(){},
    mine:()=>null,shiftSummary:()=>({count:0}),SUM:null});
 let code='let online=false;\n'+slice(driver,'let shiftPending=false;','function startGeo()').replace('const SHIFT_ACK_TIMEOUT_MS=8000;','const SHIFT_ACK_TIMEOUT_MS=30;')
   +slice(driver,'async function endShift(){','function unlockSound()');
 vm.runInContext(code,context);
 const call=code=>vm.runInContext(code,context);
 queue.push(()=>Promise.resolve({ok:false}));
 await call('startShift()');check(!call('online')&&geo===0,'failed ACK must remain offline');
 queue.push(()=>new Promise(()=>{}));
 await call('startShift()');check(!call('online')&&geo===0,'timeout must remain offline');
 queue.push(()=>Promise.resolve({ok:true}));
 await call('startShift()');check(call('online')&&geo===1,'only successful ACK permits online');
 queue.push(()=>Promise.resolve({ok:false}));
 await call('endShift()');check(call('online'),'failed OFF ACK must keep online');
 queue.push(()=>Promise.resolve({ok:true}));
 await call('endShift()');check(!call('online'),'OFF ACK accepted');
 check(errors.length>=3,'retry notifications');
 check(!vm.runInContext('online',ctx({online:false})),'reload offline by default');
}
async function F02(){
 check(sql.includes('WHERE id = p_id FOR UPDATE')&&sql.includes("o.status = 'delivered'"),'server lock/idempotency');
 check(sql.includes("WHERE id=p_id AND status='pickedup'"),'guarded status update');
 check(sql.includes('RETURN;')&&sql.includes("RAISE EXCEPTION 'already_delivered'"),'retry or conflict');
 check(!sql.includes('CREATE TRIGGER'),'no new financial trigger/receipt');
 const obj=Object.create(null);let calls=0,resolveReq;
 const rpc=()=>{calls++;return new Promise(r=>{resolveReq=r})};
 const fragment=slice(core,'deliver: function (id, cash, note, photo) {','reportDriverCashShort: function');
 const fn=new Function('gate1DeliveryFlights','rpc','console','return ({'+fragment+' reportDriverCashShort: function(){}}).deliver')(obj,rpc,console);
 const a=fn(99,12,null,null),b=fn(99,12,null,null);
 check(a===b,'same pending promise');await Promise.resolve();
 check(calls===1,'exactly one pending RPC');
 resolveReq({data:null});await Promise.all([a,b]);
 const c=fn(99,12,null,null);await Promise.resolve();check(calls===2,'post-ACK retry reaches server idempotency');resolveReq({data:null});await c;
}
async function F03(){
 const stored=new Map(),ls={getItem:k=>stored.get(k)||null,setItem:(k,v)=>stored.set(k,v),removeItem:k=>stored.delete(k)};
 let response={error:'network'},elt={value:'Заметка с адресом'},renders=0;
 const fixture={DRV:{id:'fake-driver'},localStorage:ls,TLB:{chat:async()=>response},render:()=>{renders++},
     $:()=>elt};
 const s=slice(driver,'const chatDraft={},chatSending={},chatFailed={};','function sendLoc(');
 let a=ctx(fixture);vm.runInContext(s,a);await vm.runInContext('sendChat(101)',a);
 check(stored.get('tlb-driver-draft-v1:fake-driver:101')===elt.value,'failed chat retained');
 const reload=ctx({...fixture,TLB:{chat:async()=>({ok:true})}});
 vm.runInContext(s,reload);
 check(vm.runInContext('chatDraftGet(101)',reload)===elt.value,'reload restored draft');
 await vm.runInContext('sendChat(101)',reload);check(!stored.has('tlb-driver-draft-v1:fake-driver:101'),'ACK clears draft');
 check(driver.includes("oninput=\"chatDraftSet("),'input persists before send');
 check(driver.includes("value=\"\${esc(chatDraftGet(a.id))}\""),'UI restores draft');
 check(renders>0,'feedback render');
}
async function F04(){
 check(sql.includes("RAISE EXCEPTION 'cash_short'")&&sql.includes('report_driver_cash_short'),'server short block and report');
 check(sql.includes("v_due <> round(v_due,2)"),'Q13 no silent rounding');
 check(sql.includes("RAISE EXCEPTION 'cash_over_policy'"),'no invented excess-to-wallet');
 let delivered=0,reported=0,notices=[];
 const base={TLB:{reportDriverCashShort:async()=>{reported++;return{ticket_id:7}},toast:x=>notices.push(x)},
   t:x=>x,DLV:{},render(){},finish:async()=>{delivered++;return true}};
 const code=slice(driver,'async function confirmDeliver(){','/* the 4 steps');
 async function invoke(amt){const c=ctx({...base,DV:{id:9,cash:true,photo:false,total:100,amt:String(amt),note:''}});vm.runInContext(code,c);await vm.runInContext('confirmDeliver()',c);}
 await invoke(95);check(delivered===0&&reported===1,'short does not deliver and reports');
 await invoke(100);check(delivered===1,'exact cash delivers');
 await invoke(101);check(delivered===1,'excess blocked');
 await invoke(100.001);check(delivered===1,'precision blocked');
 check(notices.length>=3,'visible error/success feedback');
}
async function main(){
 await run('F01_online_requires_ack',F01);
 await run('F02_single_delivery',F02);
 await run('F03_chat_draft_kept',F03);
 await run('F04_cash_q14',F04);
 console.log(JSON.stringify({result:failed?'FAIL':'PASS',pass:passed,fail:failed,scope:'mocked source functions + SQL source invariants, not database E2E'}));
 if(failed)process.exitCode=1;
}
main().catch(e=>{console.error(e);process.exitCode=1});
