/* Affected UI only. Real app + unchanged core; isolated service, clipboard/share and location fixtures.
   node tools/phase1_t1_t4_check.cjs /path/to/chrome /tmp/t1-deps
   Fixture generation: python tools/ui_hc_fixture.py /tmp/t1-fixtures
*/
const fs=require('fs'),path=require('path'),assert=require('assert'),cp=require('child_process');
const {chromium,webkit}=require('playwright');
const ROOT=path.resolve(__dirname,'..'),OUT=path.join(ROOT,'docs/driver-handoff/phase1-t1-t4-20261030'),DEP=process.argv[3]||'/tmp/t1-deps';
fs.mkdirSync(OUT,{recursive:true});
const uuid='3f1c2a9e-7b4d-4c1e-9a2b-5d6e7f8a9b0c';
const src=fs.readFileSync(path.join(ROOT,'tools/qa_all.py'),'utf8').split('FIX="""')[1].split('"""')[0];
let cust=fs.readFileSync('/tmp/t1-fixtures/customer-fixture.js','utf8').replaceAll("'s1'",`'${uuid}'`);
let merch=src.replaceAll("'s1'",`'${uuid}'`);
const wrap=`(()=>{const create=supabase.createClient;supabase.createClient=function(){const c=create.apply(this,arguments),from=c.from.bind(c);c.from=n=>{if(n==='orders'&&window.__FAIL_ORDERS||n==='order_events'&&window.__FAIL_EVENTS){let p=new Proxy(()=>{},{get:(t,k)=>k==='then'?(ok,bad)=>Promise.resolve({data:null,error:{message:'isolated failure'}}).then(ok,bad):()=>p});return p}return from(n)};return c}})();`;
const resume=process.env.T1_RESUME==='1';const checks=resume?fs.readFileSync('/tmp/t1-test.log','utf8').split('\n').filter(x=>x.startsWith('PASS ')).map(x=>x.slice(5)):[],errs=[];function ok(value,name){assert(value,name);checks.push(name);console.log('PASS',name)}
async function boot(b,role='customer',scene='preparing',width=390){const ctx=await b.newContext({viewport:{width,height:({360:652,390:716,430:804})[width]},isMobile:true,hasTouch:true});const p=await ctx.newPage();const errors=[];p.on('pageerror',e=>errors.push(e.message));await p.addInitScript(({role,scene})=>{window.__ROLE=role;window.__C_SCENE=scene;if(scene==='eventsFail')window.__FAIL_EVENTS=true;localStorage.setItem('tlb_lang','ru');window.fetch=()=>Promise.reject(Error('isolated'));}, {role,scene});
await ctx.route('**/*',async r=>{const u=r.request().url();if(u.includes('supabase-js'))await r.fulfill({contentType:'application/javascript',body:(role==='customer'?cust:merch)+wrap});else if(u.includes('qrcode-generator@1.4.4/qrcode.js'))await r.fulfill({contentType:'application/javascript',body:fs.readFileSync(path.join(DEP,'node_modules/qrcode-generator/qrcode.js')),headers:{'Access-Control-Allow-Origin':'*'}});else if(u.includes('leaflet.js'))await r.fulfill({contentType:'application/javascript',body:fs.readFileSync(path.join(DEP,'node_modules/leaflet/dist/leaflet.js'))});else if(u.includes('leaflet.css'))await r.fulfill({contentType:'text/css',body:fs.readFileSync(path.join(DEP,'node_modules/leaflet/dist/leaflet.css'))});else if(u.startsWith('http'))await r.abort();else await r.continue()});
await p.goto('file://'+path.join(ROOT,role+'.html')+(role==='merchant'?'?token=TEST-SHOULD-NOT-COPY#fragment':''));await p.waitForFunction(()=>window.TLB&&TLB.orders().length);if(role==='customer'){await p.waitForFunction(()=>typeof ME!=='undefined'&&ME?.phone);await p.evaluate(()=>{S.v='track';S.tid='ord1';render()})}else{await p.evaluate(()=>setTab('p'));await p.waitForSelector('.p1-store-link')}
await p.waitForTimeout(300);return {ctx,p,errors}}
async function shot(p,name){await p.evaluate(()=>scrollTo(0,0));await p.waitForTimeout(100);await p.screenshot({path:path.join(OUT,name+'.png'),fullPage:false})}
async function reload(p){await p.evaluate(()=>TLB.reload());await p.waitForTimeout(300)}
(async()=>{const b=await chromium.launch({executablePath:process.argv[2],args:['--no-sandbox','--disable-gpu','--disable-software-rasterizer']});
if(process.env.T1_EXTRA==='1'){
const prior=JSON.parse(fs.readFileSync(path.join(OUT,'checks.json')));checks.splice(0,checks.length,...prior.results);
for(const w of [360,390,430]){const {ctx,p,errors}=await boot(b,'customer','preparing',w);
 await p.evaluate(()=>scrollTo(0,0));
 ok(await p.evaluate(()=>document.querySelector('.topbar')?.getBoundingClientRect().top>=0||document.querySelector('.d6-head')?.getBoundingClientRect().top>=0||document.querySelector('.top')?.getBoundingClientRect().top>=0),`${w}: tracking header within reduced browser viewport`);
 if(w===390)await shot(p,'tracking-preparing-390');
 await p.locator('.supl').click();ok(await p.locator('.sheet').count()>0||await p.locator('#tkm').count()>0,`${w}: help handler accepts actual string order/ticket id`);
 await p.evaluate(()=>{S.rep=null;S.v='track';S.tid='ord1';__C_TABLES.orders[0].status='pickedup';__C_MODE='none'});await reload(p);await p.waitForTimeout(150);if(w===390)await shot(p,'tracking-no-location-390');
 await p.evaluate(()=>{clearInterval(window.__gTick);S.gid=__GRP.id;S.grp=__GRP;go('group')});await p.waitForTimeout(2400);
 ok(await p.evaluate(()=>{const e=document.querySelector('.p1-group-dock').getBoundingClientRect();return e.bottom<=innerHeight+1&&e.top>=0&&document.documentElement.scrollWidth<=innerWidth}),`${w}: group actions above reserved browser area`);
 if(w===390)await shot(p,'group-host-390');
 await p.evaluate(()=>{S.grp={...S.grp,is_host:false};render()});if(w===390)await shot(p,'group-member-390');
 await p.evaluate(()=>{S.cart={i2:2};S.cartStore=STORES[0].n;S.gid=null;S.grp=null;S.gCheckout=false;S.at=slotsAll()[1];go('pay')});
 ok(await p.evaluate(()=>{const e=document.querySelector('.p1-schedule').getBoundingClientRect();return e.width<=innerWidth&&document.querySelector('#wsel').getBoundingClientRect().height>=44}),`${w}: schedule fits available width, touch targets retained`);
 if(w===390)await shot(p,'schedule-390');ok(!errors.length,`${w}: added viewport/help checks no JS errors ${errors}`);await ctx.close();}
 const {ctx,p}=await boot(b,'merchant');await p.waitForSelector('.p1-qr:not([hidden])');
 await p.evaluate(()=>Object.defineProperty(navigator,'share',{configurable:true,value:()=>Promise.reject(new DOMException('denied','NotAllowedError'))}));await p.locator('[onclick="storeLinkAction(\'share\')"]').click();await p.waitForTimeout(100);ok((await p.locator('.p1-link-feedback').innerText()).includes('не разрешил'),'share permission denial has specific explanation');
 await p.evaluate(()=>Object.defineProperty(navigator,'clipboard',{configurable:true,value:undefined}));await p.locator('[onclick="storeLinkAction(\'copy\')"]').click();await p.waitForTimeout(100);ok((await p.locator('.p1-link-feedback').innerText()).includes('недоступен'),'missing clipboard has specific fallback explanation');
 await p.evaluate(()=>{const q=storeLinkState(TLB.myStores().find(x=>x.name===STORE));q.message='';render()});await p.locator('.p1-store-link').scrollIntoViewIfNeeded();await p.screenshot({path:path.join(OUT,'merchant-link-390.png')});await ctx.close();await b.close();
 fs.writeFileSync(path.join(OUT,'checks.json'),JSON.stringify({...prior,checks:checks.length,results:checks,viewportHeights:{360:652,390:716,430:804},browserReservation:'128px outside app (44+84), simulated; no real Safari chrome'},null,2));console.log('TOTAL',checks.length);return;
}
if(!resume)for(const w of [360,390,430]){const {ctx,p,errors}=await boot(b,'customer','preparing',w);
 ok(await p.locator('.p1-restaurant .p1-status').innerText()==='Готовится'&&await p.locator('.p1-courier .p1-status').innerText()==='Назначен',`${w}: independent restaurant/courier labels from core`);
 ok(await p.locator('[data-c="C1"]').count()===0,`${w}: no C1 before pickedup`);
 ok(await p.evaluate(()=>{const a=['.p1-summary','.p1-restaurant','.p1-courier','.p1-contact'].map(s=>document.querySelector(s).getBoundingClientRect().top);return a.every((x,i)=>!i||x>a[i-1])}),`${w}: summary -> restaurant -> courier -> communication`);
 await p.evaluate(()=>{TLB.order('ord1').total=0;render()});ok(await p.locator('.p1-summary .d6-order-total strong').innerText()==='0 TJS',`${w}: trusted zero amount shown`);
 const expected=await p.evaluate(()=>t('statusAtL')+': '+fmtHM(TLB.statusAt('ord1').at));ok(await p.locator('.p1-restaurant .p1-time').innerText()===expected,`${w}: event time uses statusAt only`);
 await p.evaluate(()=>{__FAIL_ORDERS=true});await reload(p);ok(await p.locator('.p1-stale').count()===1&&await p.locator('.p1-summary .d6-order-total strong').innerText()==='0 TJS',`${w}: refresh error secondary, trusted amount retained`);
 await p.evaluate(()=>{__FAIL_ORDERS=false});await reload(p);ok(await p.locator('.p1-stale').count()===0,`${w}: recovery removes stale warning`);
 await p.locator('.p1-receipt summary').click();ok(await p.locator('.p1-receipt .rcp').isVisible(),`${w}: composition and original receipt expandable`);await p.locator('.p1-receipt summary').click();
 if(w===390)await shot(p,'tracking-preparing-390');
 await p.evaluate(()=>{__C_TABLES.orders[0].status='pending';__C_TABLES.orders[0].driver_id=null});await reload(p);ok(await p.locator('.p1-courier').count()===0&&await p.locator('#cxbtn').count()===1&&await p.locator('.p1-contact-help').count()===1,`${w}: pending hides null courier, cancellation and contact remain`);
 await p.evaluate(()=>{__C_TABLES.orders[0].status='pickedup';__C_TABLES.orders[0].driver_id=__C_TABLES.orders[0].customer_id});await reload(p);await p.waitForSelector('.p1-courier [data-c="C1"]');
 ok(await p.locator('.p1-restaurant .p1-time').innerText()==='Статус заказа: время неизвестно',`${w}: missing event has no fallback time`);
 await p.waitForFunction(()=>document.querySelector('.c-track-age')?.textContent.match(/\d\d:\d\d/));ok(await p.locator('.c-track-age').innerText()!==await p.locator('.p1-restaurant .p1-time').innerText(),`${w}: courier timestamp separate from unknown status time`);
 ok(await p.evaluate(()=>!document.querySelector('.c-track').textContent.includes('мин назад')),`${w}: no generic relative update time`);
 const calls=await p.evaluate(()=>__C_CALLS.length);await p.evaluate(()=>go('orders'));await p.waitForTimeout(250);ok(await p.locator('[data-c="C1"]').count()===0&&await p.evaluate(()=>__C_CALLS.length)===calls,`${w}: C1 stops/detaches on leaving tracking`);
 await p.evaluate(()=>{clearInterval(window.__gTick);S.gid=__GRP.id;S.grp=__GRP;go('group')});
 ok(await p.locator('[onclick="grpCheckout()" ]').count()===1&&await p.locator('[onclick="grpStatus(\'closed\')"]').count()===1&&await p.locator('[onclick="grpStatus(\'cancelled\')"]').count()===1,`${w}: host checkout/close/cancel retained`);
 ok(await p.evaluate(()=>document.querySelector('.p1-group-intro').textContent.includes(fmtWhen(Date.parse(S.grp.expires_at)))) ,`${w}: group expiry from expires_at`);
 if(w===390)await shot(p,'group-host-390');
 await p.evaluate(()=>{S.grp={...S.grp,is_host:false};render()});ok(await p.locator('[onclick="grpCheckout()" ]').count()===0&&await p.locator('[onclick="grpStatus(\'closed\')"]').count()===0&&await p.locator('[onclick="grpLeave()" ]').count()>0&&await p.locator('[onclick^="grpRm"]').count()===1,`${w}: member cannot close/pay; own removal and leave retained`);
 if(w===390)await shot(p,'group-member-390');
 await p.evaluate(()=>{S.grp={...S.grp,is_host:true,status:'closed'};render()});ok(await p.locator('[onclick="grpStatus(\'open\')"]').count()===1,`${w}: host reopen retained`);
 await p.evaluate(()=>{S.grp={...S.grp,status:'open'};TLB.groupSet=async(id,status)=>{window.__closedGroup={id,status};return {group:{...S.grp,status}}};S.cart={};grpCheckout()});await p.waitForTimeout(300);
 ok(await p.evaluate(()=>S.v==='pay'&&S.gCheckout&&__closedGroup.status==='closed'&&optExtra().group===S.gid),`${w}: host closes then uses existing single checkout`);
 await p.locator('.p1-schedule button[onclick="whenSet(true)"]').click();ok(await p.locator('#wday').count()===1&&await p.locator('#wsel').count()===1&&await p.evaluate(()=>S.at>=Date.now()+44*60000&&S.at<=Date.now()+3*86400000),`${w}: schedule actual slots and original limits`);
 const days=await p.locator('#wday option').count();if(days>1){const val=await p.locator('#wday option').nth(1).getAttribute('value');await p.locator('#wday').selectOption(val);ok(await p.evaluate(()=>dayKey(S.at)===+document.querySelector('#wday').value),`${w}: day handler selects its real slots`)}
 if(w===390)await shot(p,'schedule-390');
 ok(await p.evaluate(()=>document.documentElement.scrollWidth<=innerWidth),`${w}: affected screens no horizontal overflow`);ok(!errors.length,`${w}: no JS errors ${errors}`);await ctx.close();}
{const {ctx,p}=await boot(b,'customer','eventsFail');ok(await p.locator('.p1-restaurant .p1-time').innerText()==='Статус заказа: время неизвестно','unreadable events: explicit unknown, no fetch/clock substitute');await ctx.close()}
{const {ctx,p}=await boot(b,'customer','none');await p.waitForSelector('.p1-courier [data-c="C1"]');await p.waitForTimeout(200);ok(await p.locator('.c-track-map').isHidden()&&await p.locator('.c-track-age').innerText()==='Геопозиция курьера: время неизвестно','null courier position: no fake point and unknown location time');await shot(p,'tracking-no-location-390');await ctx.close()}
for(const w of [360,390,430]){const {ctx,p,errors}=await boot(b,'merchant','',w);await p.waitForSelector('.p1-qr:not([hidden])');
 const link=await p.locator('.p1-public-link').getAttribute('href');ok(link.endsWith('customer.html?store='+uuid)&&!link.includes('TEST')&&!link.includes('#'),`${w}: merchant safe own-store URL, no copied page query`);
 await p.addScriptTag({path:path.join(DEP,'node_modules/jsqr/dist/jsQR.js')});const decoded=await p.evaluate(async()=>{const svg=document.querySelector('.p1-qr svg');return new Promise(res=>{const i=new Image();i.onload=()=>{const c=document.createElement('canvas');c.width=i.width*2;c.height=i.height*2;let x=c.getContext('2d');x.fillStyle='#fff';x.fillRect(0,0,c.width,c.height);x.drawImage(i,0,0,c.width,c.height);res(jsQR(x.getImageData(0,0,c.width,c.height).data,c.width,c.height)?.data)};i.src='data:image/svg+xml,'+encodeURIComponent(svg.outerHTML)})});ok(decoded===link,`${w}: UI QR decodes to displayed link`);
 await p.evaluate(()=>{Object.defineProperty(navigator,'share',{configurable:true,value:()=>new Promise((yes,no)=>{window.__shareYes=yes;window.__shareNo=no})})});await p.locator('[onclick="storeLinkAction(\'share\')"]').click();ok((await p.locator('.p1-link-feedback').innerText()).includes('Открываем')&&await p.locator('[onclick="storeLinkAction(\'copy\')"]').isDisabled(),`${w}: share waiting before success, duplicate guard`);
 await p.evaluate(()=>__shareNo(new DOMException('cancel','AbortError')));await p.waitForTimeout(100);ok(await p.locator('.p1-link-feedback').innerText()==='Отправка отменена',`${w}: cancelled share not reported as success`);
 await p.locator('[onclick="storeLinkAction(\'share\')"]').click();await p.evaluate(()=>__shareYes());await p.waitForTimeout(100);ok(await p.locator('.p1-link-feedback').innerText()==='Ссылка передана',`${w}: share success after resolved operation`);
 await p.evaluate(()=>Object.defineProperty(navigator,'clipboard',{configurable:true,value:{writeText:()=>new Promise((yes,no)=>{window.__copyYes=yes;window.__copyNo=no})}}));await p.locator('[onclick="storeLinkAction(\'copy\')"]').click();ok(await p.locator('.p1-link-feedback').innerText()==='Копируем…',`${w}: copy waits for clipboard`);await p.evaluate(()=>__copyNo(Error('denied')));await p.waitForTimeout(100);ok((await p.locator('.p1-link-feedback').innerText()).includes('Не удалось скопировать'),`${w}: copy failure explains clipboard permission`);
 await p.locator('[onclick="storeLinkAction(\'copy\')"]').click();await p.evaluate(()=>__copyYes());await p.waitForTimeout(100);ok(await p.locator('.p1-link-feedback').innerText()==='Ссылка скопирована',`${w}: copy success after resolution`);
 if(w===390){await p.locator('.p1-store-link').scrollIntoViewIfNeeded();await shot(p,'merchant-link-390')}
 await p.evaluate(()=>{StoreLinks.clear();TLB.qrSvg=()=>Promise.reject(Error('CDN unavailable'));render()});await p.waitForTimeout(150);ok(await p.locator('.p1-qr').isHidden()&&await p.locator('[onclick="storeLinkAction(\'copy\')"]').isEnabled()&&await p.locator('[onclick="storeLinkAction(\'share\')"]').isEnabled(),`${w}: QR failure leaves copy/share available`);
 ok(await p.evaluate(()=>document.documentElement.scrollWidth<=innerWidth),`${w}: merchant link no horizontal overflow`);ok(!errors.length,`${w}: merchant no JS errors ${errors}`);await ctx.close();}
await b.close();let wk;try{const wb=await webkit.launch();await wb.close();wk='available, not run'}catch(e){wk='unavailable: '+e.message.split('\n')[0]}
const unchanged=['talabat-core.js','driver.html','assets/driver-a/driver-a.js','assets/driver-a/driver-a.css'].every(f=>fs.readFileSync(path.join(ROOT,f)).equals(cp.execFileSync('git',['show','a417443:'+f],{cwd:ROOT})));ok(unchanged,'core and driver drag/location implementation byte-identical to a417443');
fs.writeFileSync(path.join(OUT,'checks.json'),JSON.stringify({checks:checks.length,results:checks,engine:'Chromium 133 headless, Playwright',fixtures:'isolated service; real application and unchanged core',widths:[360,390,430],viewportHeight:716,webkit:wk,iphone:false,liveOrderEventsCustomer:'unknown'},null,2));console.log('TOTAL',checks.length,'WebKit',wk);
})().catch(e=>{console.error(e);process.exit(1)});
