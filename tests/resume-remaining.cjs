const fs=require('fs'),path=require('path'),assert=require('assert'),crypto=require('crypto');
const {chromium,webkit}=require('playwright');
const root=path.resolve(__dirname,'..'),out=path.join(__dirname,'evidence');fs.mkdirSync(out,{recursive:true});
const checks=[],errors=[],network=[];
const save=(n,v)=>fs.writeFileSync(path.join(out,'operational-'+n+'.json'),JSON.stringify(v,null,2)+'\n');
const ok=(v,n)=>{checks.push({name:n,pass:!!v});save('checks',checks);assert(v,n)};
const counts=s=>({execute:s.calls.filter(x=>x[0]==='finance_execute').length,status:s.calls.filter(x=>x[0]==='finance_command_status').length,effects:s.effects.length});
const snapshot=async(p,name)=>{const s=await p.evaluate(()=>({command:TLB.financeCommandState('settle_cash',__FD),calls:JSON.parse(JSON.stringify(__calls)),effects:JSON.parse(JSON.stringify(__effects)),cash:TLB.cash(__FD),health:TLB.cashHealth(),disabled:document.querySelector('.f-write')?.disabled,text:document.querySelector('#app').innerText}));save(name,s);return s};
(async()=>{const browser=await chromium.launch({executablePath:process.env.CHROMIUM_EXECUTABLE||'/tmp/smile-browser/chromium',headless:true,args:['--no-sandbox','--disable-dev-shm-usage','--disable-gpu']});
const context=await browser.newContext({viewport:{width:390,height:844},isMobile:true,hasTouch:true});
const page=await context.newPage();page.on('pageerror',e=>errors.push(e.message));
await context.route(/^https?:\/\//,r=>{network.push({url:r.request().url(),method:r.request().method()});return r.abort()});
const open=async(query='mode=history')=>{await page.goto('file://'+path.join(__dirname,'generated/candidate-preview.html')+'?'+query);await page.waitForFunction(()=>window.TLB&&TLB.orders().length&&document.querySelector('.tabs'));};
try{
save('environment',{engine:'Chromium',version:browser.version(),webkitInstalled:fs.existsSync(webkit.executablePath()),node:process.version,platform:process.platform,viewport:{width:390,height:844},base:'ca8808dd6dee4f4815a266ae9bb9ea20a155f892',repair:'1e2249293c27e27c766e1273e81f205d15512e40',scope:'Changed selective candidate only; previous closure not reopened',network:'CSP connect-src none and HTTP/HTTPS abort',live:false,safariAccepted:false});
await open('mode=old-server&access=admin');await page.evaluate(()=>{tab='d';openDrvEdit(__FD)});
ok(await page.evaluate(()=>!TLB.financeAccess().execute&&document.querySelector('.f-write').disabled),'old server fails closed');
await page.evaluate(()=>TLB.settleCash(__FD));ok(await page.evaluate(()=>!__calls.some(x=>['finance_execute','settle_driver_cash','wallet_adjust'].includes(x[0]))),'old server has no legacy fallback or financial send');
// Full-admin operational views of deployed app remain reachable with the new shared core.
await page.evaluate(()=>sessionStorage.clear());await open('mode=history&access=admin');
const views=await page.evaluate(()=>{const result={};for(const [k,fn] of Object.entries({o:vOrders,s:vStores,d:vDrivers,b:vBanners,c:vPromos,y:vLoyalty,r:vRatings,h:vSupportA,u:vCustomers,g:vTexts,f:vStaff})){try{result[k]={ok:typeof fn()==='string'}}catch(e){result[k]={ok:false,error:e.message}}}return result});save('admin-views',views);ok(Object.values(views).every(x=>x.ok),'deployed full-admin operational views still render');
await page.evaluate(()=>{tab='d';openDrvEdit(__FD)});ok(await page.evaluate(()=>!!document.querySelector('[onclick*=setDriverStatus]')&&!!document.querySelector('[onclick*=saveLimit]')&&!TLB.financeAccess().execute),'full admin keeps operational controls without implicit finance authorization');
save('errors',errors);ok(errors.length===0,'no remaining candidate page exceptions');save('network',network);save('result',{pass:true,checks:checks.length,live:false});
}finally{await browser.close();}})().catch(e=>{save('failure',{message:e.message,stack:e.stack});console.error(e);process.exitCode=1});
