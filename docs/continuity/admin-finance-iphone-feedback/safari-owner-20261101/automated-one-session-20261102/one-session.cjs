const fs=require('fs'),path=require('path'),crypto=require('crypto'),assert=require('assert');
const {chromium,webkit}=require('playwright');
const root=__dirname,out=path.join(root,'evidence');fs.mkdirSync(out,{recursive:true});
const source=path.join(root,'source/iphone-isolated-preview.html'),buf=fs.readFileSync(source);
const expectedBlob='e9727d1430d97b7c2891174d76864f631d5b31dc';
const actualBlob=crypto.createHash('sha1').update(Buffer.from('blob '+buf.length+'\0')).update(buf).digest('hex');
assert.equal(actualBlob,expectedBlob,'test exact unchanged GitHub artifact');
const engineAvailability={webkit:{path:webkit.executablePath(),installed:fs.existsSync(webkit.executablePath())},chromium:{path:'/tmp/smile-browser/chromium',installed:fs.existsSync('/tmp/smile-browser/chromium')}};
const events=[],network=[],errors=[],checks=[];let browser,context,page;
const save=(name,v)=>fs.writeFileSync(path.join(out,name),JSON.stringify(v,null,2)+'\n');
const event=(action,detail={})=>{events.push({sequence:events.length+1,at:new Date().toISOString(),action,...detail});save('events.json',events)};
const ok=(condition,name)=>{checks.push({name,pass:!!condition});save('checks.json',checks);assert(condition,name)};
const counts=s=>({execute:s.calls.filter(x=>x[0]==='finance_execute').length,status:s.calls.filter(x=>x[0]==='finance_command_status').length,effects:s.effects.length});
const snap=async name=>{const s=await page.evaluate(()=>({at:new Date().toISOString(),scenario:__DEMO_MODE,command:TLB.financeCommandState('settle_cash',__FD),calls:JSON.parse(JSON.stringify(__calls)),effects:JSON.parse(JSON.stringify(__effects)),cash:TLB.cash(__FD),cashHealth:TLB.cashHealth(),button:{disabled:document.querySelector('.f-write').disabled,text:document.querySelector('.f-write').innerText},commandText:document.querySelector('.f-command').innerText}));save(name+'.json',s);event('snapshot',{name,counts:counts(s),state:s.command.state,key:s.command.key});return s};
(async()=>{
try{
 browser=await chromium.launch({executablePath:engineAvailability.chromium.path,headless:true,args:['--no-sandbox','--disable-dev-shm-usage','--disable-gpu']});
 context=await browser.newContext({viewport:{width:390,height:844},deviceScaleFactor:1,isMobile:true,hasTouch:true});
 page=await context.newPage();page.on('pageerror',e=>errors.push(e.message));
 await page.route(/^https?:\/\//,r=>{network.push({url:r.request().url(),method:r.request().method()});return r.abort()});
 page.on('framenavigated',f=>{if(f===page.mainFrame())event('main_frame_navigation',{url:f.url()})});
 save('environment.json',{base:'0b228829e9772ec473072848f21d80f0d0aabc69',source:'docs/continuity/admin-finance-readiness/iphone-isolated-preview.html',sourceGitBlob:actualBlob,sourceSha256:crypto.createHash('sha256').update(buf).digest('hex'),sourceModified:false,engine:'Chromium',version:browser.version(),availability:engineAvailability,platform:process.platform,node:process.version,viewport:{width:390,height:844},input:'Five physical mouse-input down/up clicks at disabled button center in a touch-enabled mobile viewport; not physical touch hardware',origin:'file:// exact self-contained GitHub artifact, mode=unresolved',network:'CSP connect-src none plus HTTP/HTTPS requests aborted',hosted_attempt:'Cloud Chrome reached private ChatGPT sign-in gate; no hosted session acceptance',scope:'Only missing unresolved five-click then one status sequence; no closed suites rerun',safariAcceptance:false,live:false});
 await page.goto('file://'+source+'?mode=unresolved');
 await page.waitForFunction(()=>typeof TLB!=='undefined'&&typeof __FD!=='undefined'&&TLB.financeCommandState('settle_cash',__FD).state==='unresolved'&&document.querySelector('.f-write')?.disabled&&document.querySelector('.f-command')?.innerText.includes('Результат операции не подтверждён'));
 await page.locator('.f-write').first().scrollIntoViewIfNeeded();
 const initial=await snap('01-before-clicks');const key=initial.command.key;
 ok(initial.command.state==='unresolved'&&initial.command.result==null&&initial.button.disabled&&initial.button.text.includes('Заблокировано до проверки'),'actual command unresolved and disabled before any status');
 ok(JSON.stringify(counts(initial))===JSON.stringify({execute:1,status:0,effects:1}),'baseline one execution zero status reads one effect');
 await page.screenshot({path:path.join(out,'01-unresolved.jpg'),type:'jpeg',quality:48});
 for(let i=1;i<=5;i++){
   const prior=await page.evaluate(()=>({state:TLB.financeCommandState('settle_cash',__FD).state,status:__calls.filter(x=>x[0]==='finance_command_status').length}));
   assert.equal(prior.state,'unresolved');assert.equal(prior.status,0);
   const rect=await page.locator('.f-write').first().boundingBox();assert(rect);const x=rect.x+rect.width/2,y=rect.y+rect.height/2;
   event('receipt_press_attempt',{number:i,coordinates:{x,y},beforeState:prior.state,beforeStatusReads:prior.status});
   await page.mouse.click(x,y);
   const s=await snap('02-attempt-'+i);
   ok(s.command.state==='unresolved'&&s.command.key===key&&s.button.disabled&&counts(s).execute===1&&counts(s).status===0&&JSON.stringify(s.effects)===JSON.stringify(initial.effects),'attempt '+i+' remains unresolved with same key, no execute/status/effect added');
 }
 const after=await snap('03-after-five-before-status');await page.screenshot({path:path.join(out,'02-after-five.jpg'),type:'jpeg',quality:48});
 ok(JSON.stringify(after.calls.slice(0,initial.calls.length))===JSON.stringify(initial.calls)&&after.calls.slice(initial.calls.length).every(x=>!['finance_execute','finance_command_status'].includes(x[0])),'between baseline and five attempts only read-side scheduler calls allowed');
 event('result_check_click',{number:1,key});
 await page.getByRole('button',{name:'Проверить результат',exact:true}).click();
 await page.waitForFunction(()=>TLB.financeCommandState('settle_cash',__FD).state==='success'&&!FUI.checks['settle_cash:'+__FD]&&TLB.cashHealth().state==='ok'&&!TLB.cashHealth().dirty);
 const final=await snap('04-after-one-status');
 ok(JSON.stringify(counts(final))===JSON.stringify({execute:1,status:1,effects:1}),'one result check leaves one execute, adds one status, preserves one effect');
 const execute=final.calls.find(x=>x[0]==='finance_execute'),status=final.calls.find(x=>x[0]==='finance_command_status');
 ok(key===execute[1].p_request&&key===status[1].p_request&&key===final.effects[0].request&&key===final.command.key&&key===final.command.result.request,'request key matches command, execution, status, effect and successful result');
 ok(JSON.stringify(final.effects)===JSON.stringify(initial.effects),'effect unchanged byte-for-byte across all snapshots');
 const prefix=JSON.stringify(final.calls.slice(0,after.calls.length))===JSON.stringify(after.calls),delta=final.calls.slice(after.calls.length);
 ok(prefix&&delta.filter(x=>x[0]==='finance_command_status').length===1&&delta.every(x=>x[0]!=='finance_execute'),'result-check delta contains one same-key status and reads only');
 ok(final.command.result.amount===57&&final.cash===0,'successful result57 and refreshed cash0 remain distinct');
 await page.locator('#demo-trace summary').click();
 const journal=JSON.parse(await page.locator('#demo-trace pre').innerText());save('05-visible-demo-journal.json',journal);
 ok(journal.calls.filter(x=>x[0]==='finance_execute').length===1&&journal.calls.filter(x=>x[0]==='finance_command_status').length===1&&journal.effects.length===1&&journal.effects[0].request===key,'visible DEMO journal corroborates final counts and key');
 await page.screenshot({path:path.join(out,'03-confirmed-and-journal.jpg'),type:'jpeg',quality:48});
 ok(events.filter(x=>x.action==='main_frame_navigation').length===1,'one page navigation; no reload, scenario or tab change');
 ok(network.length===0&&errors.length===0,'zero external requests and page errors');
 save('result.json',{status:'passed',checks:checks.length,request:key,sequence:[{stage:'unresolved-before',...counts(initial)},{stage:'unresolved-after-five',...counts(after)},{stage:'success-after-one-check',...counts(final)}],fiveAttemptsWhileUnresolved:true,sameKey:true,unchangedEffect:true,resultCheckReadOnly:true,mainNavigations:1,environment:'Chromium '+browser.version()+' Linux file-origin self-contained artifact; no Safari/WebKit installed',safariDeviceAcceptance:'open',live:false,scope:'Only remaining sequence; no closed tests rerun'});
 console.log(JSON.stringify({status:'passed',checks:checks.length,request:key,sequence:[counts(initial),counts(after),counts(final)],browser:browser.version(),output:out}));
}catch(e){save('failure.json',{error:String(e),stack:e.stack,events,network,errors});throw e}
finally{save('network.json',network);save('page-errors.json',errors);if(context)await context.close();if(browser)await browser.close()}
})().catch(e=>{console.error(e);process.exit(1)});
