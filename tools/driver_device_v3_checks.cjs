#!/usr/bin/env node
'use strict';
/* Pure offline tests against the exact, currently checked out TALABOT driver source.
   No GitHub, Supabase, Cloudflare, external origin, payment or test credential needed. */
const fs=require('node:fs'),vm=require('node:vm'),assert=require('node:assert/strict');
const files={
 driver:fs.readFileSync('driver.html','utf8'),
 core:fs.readFileSync('talabat-core.js','utf8'),
 adapter:fs.readFileSync('assets/driver-a/driver-a.js','utf8'),
 device:fs.readFileSync('assets/driver-tech/device-notes-v3.js','utf8'),
 route:fs.readFileSync('assets/driver-tech/route-layer.js','utf8')
};
const completed=[];
async function check(name,fn){
 try{await fn();completed.push(name);console.log('PASS '+name);}
 catch(err){console.error('FAIL '+name+': '+err.stack);process.exitCode=1;}
}
function createDeviceFixture(){
 const listeners={},messages=[],confirmed=[],timers=[],els={};
 for(const id of ['cashAmt','cashNote','n04-reason','n04-ov','n04-modal']){
   els[id]={id,style:{},value:'',hidden:false,focus(){this.focused=true;this.focusCount=(this.focusCount||0)+1;},
    scrollIntoView(){this.scrolled=true;}};
 }
 const vv={offsetTop:0,height:844,addEventListener(type,fn){(listeners['viewport-'+type]??=[]).push(fn);}};
 const state={};
 const c={
  window:null,document:{head:{appendChild(){}},createElement:()=>({style:{},textContent:''}),
    getElementById:id=>els[id]||null,addEventListener(type,fn){(listeners[type]??=[]).push(fn);},
    get activeElement(){return state.activeElement||null;},hidden:false},
  localStorage:{getItem(){return null;},setItem(){}},
  DV:null,CXL:null,DLV:{},online:true,innerHeight:844,
  visualViewport:vv,Date,Math,Number,String,console,Promise,
  setTimeout(fn){timers.push(fn);return timers.length;},
  ico:()=>'<svg></svg>',esc:s=>String(s).replace(/&/g,'&amp;').replace(/</g,'&lt;').replace(/"/g,'&quot;'),
  t:k=>k, due:()=>278,cashBox:()=>'<div class="cashb">278.00 TJS</div>',
  modal:()=>'',render:()=>{},unlockSound:()=>{},deliverClick:()=>{},startShift:()=>Promise.resolve(),
  confirmDeliver:()=>{confirmed.push({amt:c.DV?.amt,note:c.DV?.note});return Promise.resolve();},
  TLB:{addDict(){},order:id=>({id,leaveAtDoor:false}),isCash:()=>true,
      toast:(msg,bad)=>messages.push({msg,bad}),unlockAudio:()=>{c.unlocks=(c.unlocks||0)+1;},
      audioReady:()=>false},
  $:id=>els[id],takePhoto:()=>{},finish:()=>Promise.resolve(true)
 };
 c.window=c;c.window.visualViewport=vv;
 c.window.addEventListener=(name,fn)=>{(listeners[name]??=[]).push(fn);};
 c.render=()=>{c.lastHtml=c.modal();};
 vm.createContext(c);
 vm.runInContext(files.device,c,{timeout:1500,filename:'device-notes-v3.js'});
 return {c,els,vv,confirmed,messages,listeners,timers};
}
function createRouteFixture(storage,external=true){
 const listeners={};
 const c={
  window:null,TLB:{
   addDict(){},me:()=>({id:'synthetic-driver'}),navigation:async(body)=>{
    if(body.op==='config')return {mode:'tracking',reason:'disabled',external,providers:['google','2gis','yandex'],configTtlMs:30000};
    if(body.op==='links')return {mode:'tracking',reason:'disabled',links:[]};
    return {mode:'tracking',reason:'disabled'};
   }
  },
  aTask:()=>null,aTaskStage:()=>3,storePt:()=>[38.56,68.78],vMe:()=>'<div>PROFILE</div>',
  mapUpd:()=>{},render:()=>{},modal:()=>'',DM:null,L:null,tab:'m',DRV:{id:'synthetic-driver'},
  CXL:null,DV:null,chatOpen:false,document:{hidden:false,getElementById:()=>null,
   createElement:()=>({textContent:''}),head:{appendChild(){}},
   addEventListener(type,fn){(listeners[type]??=[]).push(fn);},
   querySelector:()=>null},
  localStorage:storage,Date,Math,Number,String,Promise,console,
  t:s=>s,esc:s=>String(s),ico:()=>'<svg></svg>',
  setInterval:()=>0,AbortController,
 };
 c.window=c;
 c.window.TALABOT_NAV_MODEL={point:p=>Array.isArray(p)&&p.length===2,destination:()=>[38.56,68.78],key:()=>'',progress:()=>({mode:'tracking'})};
 c.window.addEventListener=(type,fn)=>{(listeners[type]??=[]).push(fn);};
 vm.createContext(c);
 vm.runInContext(files.route,c,{timeout:1500,filename:'route-layer.js'});
 return c;
}
(async()=>{
 await check('N04_amount_field_editable_and_focused',()=>{
  const {c,els}=createDeviceFixture();
  c.deliverClick(9122);
  assert.equal(c.DV.amt,'278');
  assert.match(c.lastHtml,/id="n04-full"/);
  c.n04ShowDifferent();
  assert.equal(c.DV.cashMode,'different');
  assert.match(c.lastHtml,/id="cashAmt" type="text" inputmode="decimal"/);
  assert.match(c.lastHtml,/for="cashAmt"/);
  assert.ok(els.cashAmt.focused,'amount field must be focused from direct option tap');
  c.n04InputChanged({value:'200'});
  assert.equal(c.DV.amt,'200');
  assert.equal(els['n04-reason'].hidden,false);
 });
 await check('N04_full_amount_button',async()=>{
  const {c,confirmed}=createDeviceFixture();
  c.deliverClick(9122);
  await c.n04Full();
  assert.equal(confirmed.length,1);
  assert.equal(confirmed[0].amt,'278');
  assert.equal(confirmed[0].note,'');
 });
 await check('N04_reason_only_when_differs',async()=>{
  const {c,els,confirmed,messages}=createDeviceFixture();
  c.deliverClick(9122);c.n04ShowDifferent();
  assert.match(c.lastHtml,/id="n04-reason" hidden/);
  c.n04InputChanged({value:'200'});
  assert.equal(els['n04-reason'].hidden,false);
  c.DV.note='200';await c.n04Different();
  assert.equal(confirmed.length,0);
  assert.ok(messages.some(m=>m.msg==='n04ReasonErr'));
  c.DV.note='Customer paid less';
  await c.n04Different();
  assert.equal(confirmed.length,1);
  assert.equal(confirmed[0].amt,'200');
  assert.equal(confirmed[0].note,'Customer paid less');
  c.n04InputChanged({value:'278'});
  assert.equal(els['n04-reason'].hidden,true);
  assert.equal(c.DV.note,'');
  c.n04InputChanged({value:'200.123'});
  await c.n04Different();
  assert.equal(confirmed.length,1,'invalid precision must not confirm');
 });
 await check('N04_form_visible_above_keyboard',()=>{
  const {c,els,vv}=createDeviceFixture();
  c.deliverClick(9122);c.n04ShowDifferent();
  vv.height=470;vv.offsetTop=25;
  c.__deviceNotesV3.position();
  assert.equal(els['n04-ov'].style.height,'470px');
  assert.equal(els['n04-ov'].style.top,'25px');
  assert.equal(els['n04-modal'].style.maxHeight,'462px');
 });
 await check('N01_external_nav_links',()=>{
  const store=new Map();
  const c=createRouteFixture({getItem:k=>store.get(k)||null,setItem:(k,v)=>store.set(k,v)});
  const links=c.__routeLayer.fallbackLinks([38.56,68.78]);
  assert.deepEqual(Array.from(links,x=>x.id),['google','2gis','yandex']);
  assert.match(links[0].app,/google\.com\/maps\/dir\/\?api=1/);
  assert.match(links[1].web,/2gis\.ru\/directions\/tab\/car/);
  assert.match(links[2].web,/yandex\.ru\/maps/);
  assert.ok(links.every(x=>x.app&&!x.app.includes('undefined')&&x.web));
 });
 await check('N01_default_navigator_persisted',()=>{
  const store=new Map(),storage={getItem:k=>store.get(k)||null,setItem:(k,v)=>store.set(k,v)};
  const a=createRouteFixture(storage);
  assert.equal(a.aNavigationSetDefault('2gis'),true);
  assert.equal(a.aNavigationDefault(),'2gis');
  const b=createRouteFixture(storage);
  assert.equal(b.aNavigationDefault(),'2gis','must survive app script reload');
  assert.equal(b.aNavigationSetDefault('untrusted://url'),false,'unexpected provider must be rejected');
  assert.match(b.aNavigationProfileControl(),/2GIS/);
 });
 await check('N05_sound_unlocked_on_shift_start',()=>{
  assert.ok(files.driver.includes('TLB.unlockAudio();TLB.testSound()'));
  assert.ok(files.core.includes('function unlockNow()'));
  assert.ok(files.device.includes("unlockSound=function()"));
 });
 await check('N05_sound_restored_after_reconnect',()=>{
  const {c,listeners,timers,messages}=createDeviceFixture();
  assert.ok(listeners.online?.length);
  listeners.online[0]();
  assert.ok(c.unlocks>=1,'must attempt resuming AudioContext after online');
  timers.splice(0).forEach(fn=>fn());
  assert.ok(messages.some(x=>x.msg==='n05Tap'),'user-gesture fallback prompt required on iOS');
 });
 await check('N07_session_persists_reload',()=>{
  assert.ok(files.core.includes("storageKey: 'tlb-auth-' + role, persistSession: true, autoRefreshToken: true"));
  for(const role of ['customer','merchant','driver','admin']){
   assert.match(fs.readFileSync(role+'.html','utf8'),new RegExp("TLB\\.start\\('"+role+"'"));
  }
  console.log('INFO N07 physical normal Safari persistence NOT established by source/mocks; Private browsing is ephemeral.');
 });
 await check('N08_delivered_banner_dismisses',()=>{
  assert.match(files.adapter,/Date\.now\(\)-r\.at<4500/);
  assert.match(files.adapter,/aDismissDelivered\(\)/);
  assert.match(files.adapter,/setTimeout\(\(\)=>\{if\(AResult\?\.kind==='success'/);
 });
 await check('N02_earnings_visible',()=>{
  assert.ok(files.adapter.includes("aEarn"));
  assert.ok(files.adapter.includes("aAmount(x.payout)"));
 });
 await check('N03_store_address_rendered',()=>{
  assert.ok(files.adapter.includes("aStore(x).address||t('aStoreAddress')"));
  console.log('INFO N03 KFC address missing in live public store record; no real records edited.');
 });
 for(const [n,file] of Object.entries(files)){
  try{new vm.Script(file,{filename:n});}catch(e){if(n==='driver')continue;throw e;}
 }
 console.log('DEVICE_V3_CHECKS:',completed.length+'/12 PASS');
 if(completed.length!==12||process.exitCode)process.exitCode=1;
})().catch(e=>{console.error(e);process.exitCode=1});
