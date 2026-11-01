/* QA of the new isolated review artifact, not a rerun of closed attribution tests. */
const fs=require('fs'),path=require('path'),assert=require('assert'),{chromium}=require('playwright');
const root=path.resolve(__dirname,'../..'),out=path.join(root,'docs/continuity/admin-finance-readiness'),results=[];
const ok=(v,n)=>{assert(v,n);results.push(n);console.log('PASS',n)};
(async()=>{const file=path.join(out,'iphone-isolated-preview.html'),html=fs.readFileSync(file,'utf8');ok(!html.includes('sb_publishable_')&&!html.includes('var SB_URL = \'https://dzy'),'review artifact contains no live endpoint configuration or key');ok(html.includes("connect-src 'none'")&&!/<script[^>]+src=/.test(html),'review artifact is self-contained with external connections forbidden');
const b=await chromium.launch({executablePath:'/tmp/polish-chrome',args:['--no-sandbox','--disable-gpu']});try{
for(const [mode,width,height] of [['history',390,844],['wallet',390,844],['stale',390,844],['unresolved',390,844],['old-server',390,844],['wallet',844,390]]){
 const c=await b.newContext({viewport:{width,height},isMobile:true,hasTouch:true}),p=await c.newPage(),errors=[],network=[];p.on('pageerror',e=>errors.push(e.message));p.on('request',r=>{if(/^https?:/.test(r.url()))network.push(r.url())});await c.route('https://**/*',r=>r.abort());await c.route('http://**/*',r=>r.abort());await p.goto('file://'+file+'?mode='+mode);await p.waitForFunction(()=>typeof TLB!=='undefined'&&TLB.orders().length&&document.querySelector('.tabs'));await p.waitForTimeout(300);
 ok(await p.locator('#demo-banner').isVisible(),mode+' '+width+' displays explicit artificial-data banner');
 ok(await p.evaluate(()=>document.scrollingElement.scrollWidth<=innerWidth),mode+' '+width+' preview has no horizontal overflow');
 if(mode==='wallet'){await p.locator('#cuwa').fill('12.50');await p.locator('#cuwn').fill('ДЕМО — проверка клавиатуры');await p.evaluate(()=>render());ok(await p.locator('#cuwa').inputValue()==='12.50'&&await p.locator('#cuwn').inputValue()==='ДЕМО — проверка клавиатуры','wallet inputs remain usable in '+width+' review viewport');}
 if(mode==='old-server')ok(await p.evaluate(()=>TLB.financeAccess().execute===false),'old-server demonstration keeps financial execution disabled');
 ok(!network.length,mode+' '+width+' makes no external HTTP requests');ok(!errors.length,mode+' '+width+' preview has no JS errors '+errors.join(';'));
 await p.screenshot({path:path.join(out,'iphone-preview-'+mode+'-'+width+'.png'),fullPage:true});await c.close();
}
fs.writeFileSync(path.join(out,'preview-qa-results.json'),JSON.stringify({checks:results.length,results,engine:'Chromium 133, touch/mobile viewports 390x844 and 844x390. NOT actual Safari/iPhone or native keyboard.',synthetic:true,live:false},null,2)+'\n');
}finally{await b.close()}})().catch(e=>{console.error(e);process.exit(1)});
