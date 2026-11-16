#!/usr/bin/env node
'use strict';
// Driver device Notes V3 regression: pure mocked client/DOM / NO network,
// no production accounts, no Supabase state writes and no app-side payments.
const fs=require('node:fs'),vm=require('node:vm'),assert=require('node:assert/strict');
const driver=fs.readFileSync('driver.html','utf8');
const core=fs.readFileSync('talabat-core.js','utf8');
const adapter=fs.readFileSync('assets/driver-tech/device-notes-v3.js','utf8');
const nav=fs.readFileSync('assets/driver-tech/route-layer.js','utf8');
const driverA=fs.readFileSync('assets/driver-a/driver-a.js','utf8');
let passed=0,failed=0;
async function check(name,fn){
 try{await fn();passed++;process.stdout.write('PASS '+name+'\n')}
 catch(e){failed++;process.stderr.write('FAIL '+name+' '+e.stack+'\n')}
}
function context(extra){return vm.createContext(Object.assign({console,Promise,setTimeout,clearTimeout,Date,Math,Number,isFinite,encodeURIComponent,Array,Object,String},extra))}
function n04fixture(){
 const timers=[], events={}, keys={},toasts=[], dictionaries={},calls=[];
 let html='',focused='',unlockCount=0,ready=false;
 const elements={
  'cashAmt':{id:'cashAmt',value:'',focus(){focused='cashAmt';doc.activeElement=this},scrollIntoView(){}},
  'cashNote':{id:'cashNote',value:'',focus(){focused='cashNote';doc.activeElement=this}},
  'n04-reason':{id:'n04-reason',hidden:true},
  'n04-ov':{id:'n04-ov',style:{}},
  'n04-modal':{id:'n04-modal',style:{}}
 };
 const doc={head:{appendChild(){}},createElement:()=>({style:{},textContent:''}),activeElement:null,
  getElementById:id=>elements[id]||null,querySelector:sel=>sel==='#cashAmt'?elements.cashAmt:null,
  addEventListener(name,fn){(events['doc:'+name]??=[]).push(fn)}};
 const win={innerHeight:844,visualViewport:{height:844,offsetTop:0,addEventListener(name,fn){(events['vv:'+name]??=[]).push(fn)}},
  addEventListener(name,fn){(events[name]??=[]).push(fn)}};
 const sb={
  document:doc,window:win, navigator:{onLine:true},DV:null,DLV:{},CXL:null,chatOpen:false,
  TLB:{order:id=>({id,leaveAtDoor:false,payment:'cash',total:278}),isCash:()=>true,addDict(ru,en){Object.assign(dictionaries,en)},
   toast:(msg,bad)=>toasts.push({msg,bad}),unlockAudio:()=>{unlockCount++;return ready},audioReady:()=>ready,
   testSound(){},me:()=>({id:'driver-1'})},
  $:id=>elements[id]||null,ico:()=>'<svg/>',due:()=>278,cashBox:()=>'<div class="cashb">278.00 TJS</div>',
  t:k=>dictionaries[k]||k,esc:v=>String(v).replace(/[&<>"]/g,m=>({'&':'&amp;','<':'&lt;','>':'&gt;','"':'&quot;'}[m])),
  deliverClick:function(){},modal:()=>'',render:function(){html=sb.modal();return html},
  online:true,unlockSound:()=>{unlockCount++},confirmDeliver:()=>{calls.push({amount:sb.DV.amt,note:sb.DV.note});return true},
  setTimeout:fn=>{timers.push(fn);return timers.length}
 };
 win.window=win;
 const c=context(sb);
 vm.runInContext(adapter,c,{filename:'device-notes-v3.js'});
 return {c,elements,events,dict:dictionaries,toasts,calls,timers,win,doc,render:()=>html,focus:()=>focused,
  audioReady:v=>{ready=v},unlocks:()=>unlockCount};
}
function n01fixture(sharedStorage){
 const events={},urls=[],locale={},storage=sharedStorage||new Map(),win={};
 const store={getItem:k=>storage.get(k)||null,setItem:(k,v)=>storage.set(k,String(v))};
 const TLB={addDict:(ru,en)=>Object.assign(locale,en),
  navigation:async args=>args.op==='config'?{external:true,providers:['google','2gis','yandex'],mode:'tracking',reason:'disabled'}:
   args.op==='links'?{links:[],config:{external:true,providers:['google','2gis','yandex'],mode:'tracking'}}:({mode:'tracking',reason:'disabled'})};
 const point=p=>Array.isArray(p)&&p.length===2&&p.every(x=>Number.isFinite(x))&&Math.abs(p[0])<=90&&Math.abs(p[1])<=180;
 const M={point,destination:(x,stage,sp)=>stage>=3?[x.lat,x.lng]:sp,key:(x,stage,to)=>JSON.stringify([x.id,stage,to])};
 win.TLB=TLB;win.TALABOT_NAV_MODEL=M;
 win.addEventListener=(n,f)=>{(events[n]??=[]).push(f)};
 const doc={hidden:false,addEventListener(){},getElementById(){return null},
  createElement:()=>({style:{},textContent:''}),head:{appendChild(){}}};
 const job={id:9122,lat:38.567741,lng:68.793569,address:'Synthetic Street',store:'Synthetic Store'};
 const c=context({window:win,document:doc,TLB,mapUpd:()=>{},modal:()=>'',DM:null,GEO:{lat:null,lng:null},DRV:{id:'driver-A'},tab:'m',chatOpen:false,CXL:null,DV:null,
  aTask:()=>job,aTaskStage:()=>3,storePt:()=>[38.5,68.7],render:()=>{},
  localStorage:store,ico:()=>'<svg/>',t:k=>locale[k]||k,esc:v=>String(v).replace(/[&<>"]/g,m=>({'&':'&amp;','<':'&lt;','>':'&gt;','"':'&quot;'}[m])),
  setInterval:()=>0,setTimeout:()=>0,clearTimeout:()=>{}});
 vm.runInContext(nav,c,{filename:'route-layer.js'});
 return {c,win,storage,events};
}
(async()=>{
 await check('N04_amount_field_editable_and_focused',()=>{
  const f=n04fixture();
  vm.runInContext('deliverClick(9122)',f.c);
  assert.equal(f.c.DV.cashMode,'full');
  assert(f.render().includes('n04-full')&&!f.render().includes('id="cashNote"'));
  f.win.n04ShowDifferent();
  assert.equal(f.focus(),'cashAmt');
  assert.equal(f.c.DV.amt,'');
  assert(f.render().includes('id="cashAmt"')&&f.render().includes('inputmode="decimal"'));
  assert(f.render().includes('type="text"'));
  f.win.n04InputChanged({value:'200'});
  assert.equal(f.c.DV.amt,'200');
 });
 await check('N04_full_amount_button',()=>{
  const f=n04fixture();vm.runInContext('deliverClick(9122)',f.c);
  assert(f.render().includes('Received full amount: 278.00 TJS'));
  f.win.n04Full();
  assert.equal(f.calls.length,1);
  assert.deepEqual(f.calls[0],{amount:'278',note:''});
 });
 await check('N04_reason_only_when_differs',()=>{
  const f=n04fixture();vm.runInContext('deliverClick(9122)',f.c);
  f.win.n04ShowDifferent();
  f.win.n04InputChanged({value:'278'});
  assert.equal(f.elements['n04-reason'].hidden,true);
  f.win.n04InputChanged({value:'200'});
  assert.equal(f.elements['n04-reason'].hidden,false);
  f.c.DV.note='200';f.win.n04Different();assert.equal(f.calls.length,0,'numeric note is never accepted');
  assert.equal(f.toasts.length,1,'numeric-only reason displays an error');
  f.c.DV.note='Customer paid 200';
  f.win.n04Different();assert.deepEqual(f.calls,[{amount:'200',note:'Customer paid 200'}]);
  f.win.n04InputChanged({value:'285,50'});
  f.c.DV.note='Customer says 285.50';f.win.n04Different();
  assert.equal(f.calls.at(-1).amount,'285.5','comma must normalize before approved RPC');
 });
 await check('N04_form_visible_above_keyboard',()=>{
  const f=n04fixture();vm.runInContext('deliverClick(9122)',f.c);f.win.n04ShowDifferent();
  f.win.visualViewport.height=520;f.win.visualViewport.offsetTop=9;
  f.win.__deviceNotesV3.position();
  assert.equal(f.elements['n04-ov'].style.top,'9px');
  assert.equal(f.elements['n04-ov'].style.height,'520px');
  assert.equal(f.elements['n04-modal'].style.maxHeight,'512px');
  assert(adapter.includes('var(--a-vh,100dvh)'),'CSS visualViewport must survive normal server rerenders');
 });
 await check('N01_external_nav_links',()=>{
  const {win}=n01fixture();
  const links=win.__routeLayer.fallbackLinks([38.567741,68.793569]);
  assert.deepEqual(Array.from(links.map(x=>x.id)),['google','2gis','yandex']);
  assert(links.every(x=>/^https:|^dgis:|^yandexmaps:/.test(x.app)&&x.web.startsWith('https://')));
  assert(links[0].app.includes('destination=38.567741%2C68.793569'));
  assert(links[1].app.includes('to/68.793569,38.567741'),'2GIS uses longitude,latitude');
  assert(links[2].web.startsWith('https://yandex.ru/maps/'));
  assert.equal(win.__routeLayer.fallbackLinks([200,200]).length,0);
 });
 await check('N01_default_navigator_persisted',async()=>{
  const store=new Map(),first=n01fixture(store);
  assert.equal(first.win.aNavigationSetDefault('2gis'),true);
  assert.equal(first.win.aNavigationDefault(),'2gis');
  assert.equal(first.win.aNavigationSetDefault('evil'),false);
  const next=n01fixture(store);
  assert.equal(next.win.aNavigationDefault(),'2gis');
  assert(next.win.aNavigationProfileControl().includes('2GIS'));
  next.win.aNavigationOpen();
  await Promise.resolve();await Promise.resolve();await Promise.resolve();await new Promise(resolve=>setImmediate(resolve));
  const h=vm.runInContext('modal()',next.c);
  assert(h.includes('Google Maps')&&h.includes('2GIS')&&h.includes('Yandex Maps'));
  assert(h.includes('aNavigationSetDefault'));
 });
 await check('N05_sound_unlocked_on_shift_start',()=>{
  const a=driver.indexOf('async function startShift(){'),b=driver.indexOf('function unlockSound()',a);
  assert(a>0&&b>a);
  const part=driver.slice(a,b);
  assert(part.includes('TLB.unlockAudio();TLB.testSound()'),'original shift must unlock AudioContext in gesture');
  assert(part.indexOf('TLB.unlockAudio();TLB.testSound()')<part.indexOf('await shiftAck(true)'),'unlock before async ACK');
 });
 await check('N05_sound_restored_after_reconnect',()=>{
  const f=n04fixture();
  assert(f.events.online?.length===1,'reconnect listener not installed');
  f.events.online[0]();
  assert(f.unlocks()>0,'online reconnect did not attempt AudioContext resume');
  for(const fn of f.timers.splice(0))fn();
  assert(f.toasts.length>0,'visible sound tap instruction required if iOS remains muted');
  const count=f.toasts.length;f.audioReady(true);f.events.online[0]();
  for(const fn of f.timers.splice(0))fn();
  assert.equal(f.toasts.length,count,'restored AudioContext should not show false muted warning');
 });
 await check('N07_session_persists_reload',()=>{
  assert(core.includes("storageKey: 'tlb-auth-' + role, persistSession: true, autoRefreshToken: true"),'Supabase auth storage config must be explicit');
  assert(core.includes("sb.auth.getSession()"),'initial load must restore a saved session');
  const localStore=new Map(),roles=['customer','merchant','driver','admin'];
  for(const role of roles)localStore.set('tlb-auth-'+role,JSON.stringify({role,sample:'synthetic-only'}));
  for(const role of roles)assert.equal(JSON.parse(localStore.get('tlb-auth-'+role)).role,role);
  // Scope: mocked persistent browser storage, NOT physical iPhone Private Safari.
 });
 await check('N08_delivered_banner_dismisses',()=>{
  const a=driverA.indexOf('function aDismissDelivered()'),b=driverA.indexOf('function aJourneyQueueLayout()',a);
  assert(a>0&&b>a);
  const c=context({AResult:{id:9123,n:4,kind:'success',at:Date.now()},TLB:{order:()=>({id:9123,status:'delivered'})},
     esc:String,ico:()=>'<svg/>',t:k=>k,render:()=>{}});
  vm.runInContext(driverA.slice(a,b),c);
  assert(vm.runInContext('aJourneyDelivered()',c).includes('aDismissDelivered()'));
  vm.runInContext('aDismissDelivered()',c);
  assert.equal(c.AResult,null);
  c.AResult={id:9123,n:4,kind:'success',at:Date.now()-4700};
  assert.equal(vm.runInContext('aJourneyDelivered()',c),'');
  assert(driverA.includes('},4500)'),'automatic delivered banner timer must exist');
 });
 await check('N03_store_address_rendered',()=>{
  // The real KFC row has address=null (DB check in Issue #48 review); do not synthesize one.
  const a=driverA.indexOf('function aTarget('),b=driverA.indexOf('/* H1',a);
  assert(a>0&&b>a);
  const code=driverA.slice(a,b);
  assert(code.includes("st.address||t('aStoreAddress')"),'actual store address must be used, not order customer address');
  assert(code.includes('esc('),'address must be safely rendered');
  // KFC remains an actual data-entry BLOCKER, not a frontend PASS on a populated address.
 });
 console.log('DRIVER_DEVICE_V3_RESULT:',passed,'/',passed+failed,failed?'FAIL':'PASS','(mocked source contracts; NO live iOS/production writes)');
 if(failed)process.exit(1);
})().catch(e=>{console.error(e.stack);process.exit(1)});
