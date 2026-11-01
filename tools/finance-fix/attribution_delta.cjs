/* Only attribution/recovery/capability paths; existing UI and PostgreSQL suites are not rerun. */
const fs=require('fs'),path=require('path'),assert=require('assert');
const root=path.resolve(__dirname,'../..'),out=path.join(root,'docs/continuity/admin-finance-fix');
let source=fs.readFileSync(path.join(__dirname,'ui_check.cjs'),'utf8').split('(async()=>{const b=')[0];
source=source.replace("if(name==='finance_access')return Promise.resolve({data:{execute:window.__FIN_ROLE==='accountant'}});", "if(name==='finance_access')return Promise.resolve({data:{execute:window.__FIN_ROLE==='accountant',version:window.__oldContract?1:2,capabilities:['commands','settlement_events']}});if(name==='finance_settlement_events'){const data=(window.__historicalEvents||__FT.audit_log).filter(e=>args.p_order_ids.includes(e.row_id));if(window.__settlementHold)return new Promise(r=>window.__releaseSettlement=()=>r({data}));return Promise.resolve({data})}");
const {boot,chromium}=new Function('require','__dirname',source+';return {boot,chromium};')(require,__dirname);
const checks=process.env.ATTRIBUTION_RECOVERY_ONLY?JSON.parse(fs.readFileSync(path.join(out,'attribution-ui-checkpoint.json'))):[];function ok(v,n){assert(v,n);checks.push(n);fs.writeFileSync(path.join(out,'attribution-ui-checkpoint.json'),JSON.stringify(checks,null,2)+'\n');console.log('PASS',n)}
(async()=>{const b=await chromium.launch({executablePath:process.argv[2]||'/tmp/polish-chrome',args:['--no-sandbox','--disable-gpu']});try{
if(!process.env.ATTRIBUTION_RECOVERY_ONLY){const {c,p,errors}=await boot(b);
await p.evaluate(()=>{__historicalEvents=__FT.audit_log.slice();__FT.audit_log=Array.from({length:100},(_,i)=>({id:i+100,table_name:'other',user_id:null,details:{}}));AUD={known:true,state:'ok',rows:__FT.audit_log};tab='d';openDrvEdit(__FD)});
await p.waitForFunction(()=>document.querySelector('#app').innerText.includes('Бухгалтер — тест'));
ok((await p.locator('#app').innerText()).includes('Бухгалтер — тест'),'direct history opening resolves event outside latest 100 audit rows');
ok(await p.evaluate(()=>__calls.filter(x=>x[0]==='finance_settlement_events').every(x=>x[1].p_order_ids.join(',')==='ord4')&&!__calls.some(x=>x[0]==='finance_audit')),'only displayed settled order ids fetched; no global audit prefetch');
await p.screenshot({path:path.join(out,'attribution-old-event-390.png'),fullPage:true});
await p.evaluate(async()=>{__readFail.finance_settlement_events=true;await fLoadSettlements(__FD,true);render()});
ok(await p.evaluate(()=>TLB.financeSettlementHealth(TLB.orders(o=>o.id==='ord4')[0]).state==='error'&&TLB.financeSettlementActor('ord4','2026-11-01T09:00:00Z')!==null),'failed targeted read preserves trusted attribution and marks stale');
ok((await p.locator('#app').innerText()).includes('Данные не обновлены'),'stale attribution warning displayed beside history');
await p.screenshot({path:path.join(out,'attribution-stale-retry-390.png'),fullPage:true});
const count=await p.evaluate(()=>__calls.filter(x=>x[0]==='finance_settlement_events').length);await p.evaluate(()=>{render();render()});
ok(await p.evaluate(n=>__calls.filter(x=>x[0]==='finance_settlement_events').length===n,count),'error rendering does not create an automatic retry loop');
await p.evaluate(()=>{__readFail={};AUD={state:'error',known:false,rows:[]};openDrvEdit(__FD)});await p.waitForFunction(()=>TLB.financeSettlementHealth(TLB.orders(o=>o.id==='ord4')[0]).state==='ok');
ok(await p.evaluate(n=>__calls.filter(x=>x[0]==='finance_settlement_events').length===n+1,count),'reopening with failed audit retries targeted attribution successfully');
await p.evaluate(async()=>{__settlementHold=true;const a=fLoadSettlements(__FD,true),b=fLoadSettlements(__FD,true);await new Promise(r=>setTimeout(r,10));window.__pendingChecks=[a,b]});
const calls=await p.evaluate(()=>__calls.filter(x=>x[0]==='finance_settlement_events').length);
await p.evaluate(async()=>{__releaseSettlement();await Promise.all(__pendingChecks);__settlementHold=false});
ok(await p.evaluate(n=>__calls.filter(x=>x[0]==='finance_settlement_events').length===n,calls),'concurrent opens coalesce into one targeted read');
await p.evaluate(async()=>{__historicalEvents=[];await fLoadSettlements(__FD,true);render()});
ok(await p.evaluate(()=>TLB.financeSettlementActor('ord4','2026-11-01T09:00:00Z')===null),'confirmed absent event clears old attribution without inventing actor');
await p.evaluate(async()=>{__historicalEvents=[{id:888,table_name:'orders',row_id:'ord4',user_id:__FA,details:{cash_settled_at:{to:'2026-10-01T09:00:00Z'}}}];await fLoadSettlements(__FD,true)});
ok(await p.evaluate(()=>!TLB.financeSettlementActor('ord4','2026-11-01T09:00:00Z')),'mismatched settlement timestamp never receives an actor');
await p.evaluate(async()=>{__oldContract=true;await TLB.financeRefreshAccess()});ok(await p.evaluate(()=>!TLB.financeAccess().execute),'old capability response disables writes');
await p.evaluate(async()=>{__oldContract=false;await TLB.financeRefreshAccess()});ok(await p.evaluate(()=>TLB.financeAccess().execute),'reviewed v2 capability enables explicitly delegated fixture');
ok(!errors.length,'no application JavaScript errors in changed journey');await c.close();}
const z=await boot(b,'accountant',390,{finance_settlement_events:true});await z.p.evaluate(()=>{tab='d';openDrvEdit(__FD)});await z.p.waitForFunction(()=>document.querySelector('#app').innerText.includes('Не удалось загрузить'));
ok((await z.p.locator('#app').innerText()).includes('Не удалось загрузить'),'first attribution failure is explicit without successful empty history');
await z.p.evaluate(()=>{__readFail={}});await z.p.getByRole('button',{name:'Повторить загрузку',exact:true}).last().click();await z.p.waitForFunction(()=>document.querySelector('#app').innerText.includes('Бухгалтер — тест'));
ok((await z.p.locator('#app').innerText()).includes('Бухгалтер — тест'),'inline retry recovers first failed attribution read');await z.c.close();
fs.writeFileSync(path.join(out,'attribution-ui-results.json'),JSON.stringify({base:'81c067c6f3697b805f4db2df05511a397a027abe',checks:checks.length,results:checks,live:false,engine:'Chromium 133; current app/core; isolated network fixture; no old suites rerun'},null,2)+'\n');
}finally{await b.close()}})().catch(e=>{console.error(e);process.exit(1)});
