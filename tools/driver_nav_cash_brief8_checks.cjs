#!/usr/bin/env node
'use strict';
/* BRIEF-8: real source + mocked DOM transitions; NEVER live network/orders.
 * Backend underpayment proof is the existing genuine LOCAL HTTP Gate1 E08. */
const assert=require('node:assert/strict'),fs=require('node:fs'),vm=require('node:vm');
const route=fs.readFileSync('assets/driver-tech/route-layer.js','utf8');
const cash=fs.readFileSync('assets/driver-tech/nav-cash-brief8.js','utf8');
const driver=fs.readFileSync('driver.html','utf8');
let done=0,errors=0;
async function check(label,fn){
 try{await fn();done++;console.log('PASS '+label)}catch(e){errors++;console.error('FAIL '+label,e.stack)}
}
const esc=x=>String(x).replace(/[&<>"]/g,ch=>({'&':'&amp;','<':'&lt;','>':'&gt;','"':'&quot;'}[ch]));
function navFixture(store=new Map()){
 const urls=[],events={},lang={},win={};
 const storage={getItem:k=>store.has(k)?store.get(k):null,setItem:(k,v)=>store.set(k,String(v))};
 const dest=[38.567741,68.793569],task={id:9122,lat:dest[0],lng:dest[1],address:'Synthetic destination',store:'Synthetic Store'};
 const M={point:p=>Array.isArray(p)&&p.length===2&&p.every(Number.isFinite)&&Math.abs(p[0])<=90&&Math.abs(p[1])<=180&&!(p[0]===0&&p[1]===0),destination:(x,n,sp)=>n>=3?[x.lat,x.lng]:sp,key:(x,n,to)=>JSON.stringify([x.id,n,to])};
 const TLB={addDict:(ru,en)=>Object.assign(lang,en),
  navigation:async q=>q.op==='config'?{external:true,providers:['google','2gis','yandex'],mode:'tracking',reason:'disabled'}:({links:[],mode:'tracking',reason:'disabled'})};
 const doc={hidden:false,visibilityState:'visible',head:{appendChild(){}},
  createElement:()=>({style:{},textContent:''}),getElementById:()=>null,
  addEventListener:(type,fn)=>{(events[type]??=[]).push(fn)}};
 Object.assign(win,{TLB,TALABOT_NAV_MODEL:M,location:{assign:url=>urls.push(url)},addEventListener:(type,fn)=>{(events[type]??=[]).push(fn)}});
 let context=vm.createContext({window:win,document:doc,TLB,navigator:{userAgent:'iPhone',platform:'iPhone'},
  localStorage:storage,mapUpd:()=>{},modal:()=>'',GEO:{lat:null,lng:null},DM:null,
  DRV:{id:'synthetic-driver'},tab:'o',chatOpen:false,CXL:null,DV:null,
  aTask:()=>task,aTaskStage:()=>3,storePt:()=>[38.5,68.7],render:()=>{},
  t:key=>lang[key]||key,esc,ico:()=>'<svg/>',setInterval:()=>0,setTimeout:()=>0,clearTimeout:()=>{},
  Promise,Date,Math,Number,String,Array,isFinite,encodeURIComponent});
 vm.runInContext(route,context,{filename:'route-layer.js'});
 return{win,context,urls,storage:store};
}
function cashFixture(){
 const dict={},frames=[],msgs=[],calls=[],body={html:'',renders:0},attrs={},classes={};
 const makeClass=key=>({toggle(name,on){classes[key+':'+name]=!!on;}});
 const elements={
  'b8-ov':{style:{setProperty(k,v){attrs[k]=v}}},
  'b8-reserved':{setAttribute(k,v){attrs['reserved-'+k]=v}},
  'b8-reason-slot':{setAttribute(k,v){attrs['slot-'+k]=v},classList:makeClass('reason')},
  'b8-other-slot':{classList:makeClass('other')},
  'b8-policy':{classList:makeClass('policy'),textContent:''},
  'cashAmt':{focus(){attrs.focus='cashAmt'}},
  'cashNote':{focus(){attrs.focus='cashNote'}}
 };
 const chips=['short','dispute','missing','other'].map(id=>({dataset:{reason:id},setAttribute(k,v){attrs['chip-'+id+'-'+k]=v;}}));
 const doc={head:{appendChild(){}},createElement:()=>({textContent:''}),
  getElementById:id=>elements[id]||null,
  querySelectorAll:selector=>selector==='.b8-chip'?chips:[]};
 const vv={height:780,offsetTop:0,events:{},addEventListener(name,fn){this.events[name]=fn}};
 const win={innerHeight:780,visualViewport:vv,addEventListener(){}};
 const TLB={lang:()=> 'en',order:id=>({id,payment:'cash',total:278,leaveAtDoor:false}),
  addDict:(ru,en)=>Object.assign(dict,en),
  toast:(msg)=>msgs.push(msg)};
 let ctx;
 const sample={id:9122,cash:true,photo:false,total:278,amt:'278',cashMode:'full',note:'',up:false,ph:null};
 ctx=vm.createContext({window:win,document:doc,TLB,DLV:{},CXL:null,DV:sample,
  render(){body.renders++;body.html=ctx.modal();return body.html},
  modal:()=>'',cashBox:()=>'<div class="cashb">278 TJS</div>',
  confirmDeliver(){let v=Number(ctx.DV.amt),n=ctx.DV.note;
    if(v<278)calls.push({method:'reportDriverCashShort',amount:v,note:n});
    else if(v===278)calls.push({method:'deliver',amount:v,note:n});return true;},
  requestAnimationFrame(fn){frames.push(fn);return frames.length},
  t:key=>dict[key]||key,esc,ico:()=>'<svg/>',$:id=>elements[id]||null,
  Promise,Math,Number,String,Array,windowOuter:null});
 win.__deviceNotesV3={money(v){v=String(v).trim().replace(',','.');if(!/^\d+(?:\.\d{1,2})?$/.test(v))return null;const n=Number(v);return Number.isFinite(n)&&n>=0?n:null;}};
 vm.runInContext(cash,ctx,{filename:'nav-cash-brief8.js'});
 const flush=()=>{while(frames.length)frames.shift()()};
 return{ctx,win,doc,body,dict,msgs,calls,attrs,classes,chip:chips,flush,el:elements};
}
(async()=>{
 await check('NAV_three_icons_row',()=>{
   const icons=['google-maps','2gis','yandex-maps'];
   for(const id of icons){
     const raw=fs.readFileSync('assets/driver-tech/map-icons/'+id+'.svg','utf8');
     assert(raw.includes('<svg')&&!/<script|onload=|javascript:/i.test(raw),id+' real local SVG');
   }
   const f=navFixture();assert.equal(f.win.aNavigationDefault(),null);
   f.win.aNavigationOpen();
   const h=vm.runInContext('modal()',f.context);
   assert(h.includes('class="n-map-icons"')&&h.includes('data-nav-provider="google"'));
   assert.equal((h.match(/data-nav-provider="/g)||[]).length,3,'exactly three provider cells');
   assert.equal((h.match(/class="n-map-link"/g)||[]).length,3);
   assert(!h.includes('class="n-open"')&&!h.includes('class="n-web"'),'duplicated Open/Web actions removed');
 });
 await check('NAV_default_green_dot_persisted',()=>{
   const store=new Map(),first=navFixture(store);
   assert(first.win.aNavigationSetDefault('yandex'));
   const second=navFixture(store);
   assert.equal(second.win.aNavigationDefault(),'yandex','saved across context reload');
   assert.equal(second.win.aNavigationSetDefault('evil'),false,'unlisted app rejected');
   second.win.aNavigationOpenPoint(38.567741,68.793569);
   const markup=vm.runInContext('modal()',second.context);
   assert(markup.includes('n-map-default-indicator'));
   assert.equal((markup.match(/n-map-default-indicator/g)||[]).length,1);
   assert(markup.includes('data-nav-provider="yandex"'));
   assert(markup.includes('aria-pressed="true"'));
 });
 await check('NAV_navigate_opens_default',()=>{
   const f=navFixture();f.win.aNavigationSetDefault('2gis');
   f.win.aNavigationOpen();
   assert(f.urls.length===1&&f.urls[0].startsWith('dgis://'),'iOS direct link first');
   assert.equal(vm.runInContext('modal()',f.context),'','chooser not forced after selection');
   assert(f.win.__routeLayer.fallbackLinks([400,100]).length===0,'invalid coordinates fail closed');
 });
 await check('CASH_numeric_keypad',()=>{
   const f=cashFixture();f.flush();f.win.b8ChooseDifferent();f.flush();
   assert(f.body.html.includes('inputmode="decimal"'));
   assert(f.body.html.includes('pattern="[0-9]+([.,][0-9]{1,2})?"'));
   assert(f.body.html.includes('id="cashAmt"')&&f.body.html.includes('type="text"'));
   assert.equal(f.attrs.focus,'cashAmt');
 });
 await check('CASH_sheet_no_layout_jump',()=>{
   const f=cashFixture();f.flush();f.win.b8ChooseDifferent();f.flush();
   const prev=f.body.renders,html=f.body.html;
   f.win.b8AmountChanged({value:'200'});
   assert.equal(f.body.renders,prev,'typing should not reconstruct modal');
   assert.equal(f.body.html,html,'same markup retained on difference');
   assert.equal(f.classes['reason:active'],true,'reserved reason slot becomes visible');
   f.win.b8ReasonChosen('short');
   assert.equal(f.body.renders,prev,'choosing a chip must not reconstruct the sheet');
   assert(cash.includes('height:268px;min-height:268px')&&cash.includes('height:188px;min-height:188px'));
   f.win.visualViewport.height=445;f.win.visualViewport.offsetTop=6;
   f.win.visualViewport.events.resize();f.flush();
   assert.equal(f.attrs['--b8-vh'],'445px');
   assert.equal(f.attrs['--b8-top'],'6px');
 });
 await check('CASH_reason_chips_no_typing',()=>{
   const f=cashFixture();f.flush();f.win.b8ChooseDifferent();f.flush();
   f.win.b8AmountChanged({value:'200'});
   f.win.b8ReasonChosen('short');
   assert.equal(f.ctx.DV.note,f.dict.b8ShortReason,'preset reason inserted without keyboard text');
   f.win.b8Confirm();
   assert.equal(f.calls.length,1);
   assert.equal(f.calls[0].method,'reportDriverCashShort','short payment cannot deliver');
   f.win.b8ReasonChosen('other');f.win.b8OtherChanged({value:'200'});f.win.b8Confirm();
   assert(f.msgs.includes(f.dict.b8ReasonError),'numeric-only other reason rejected');
   f.win.b8OtherChanged({value:'Customer disputes the amount'});f.win.b8Confirm();
   assert.equal(f.calls.at(-1).note,'Customer disputes the amount');
   f.win.b8AmountChanged({value:'278.00'});f.win.b8Confirm();
   assert.equal(f.calls.at(-1).method,'deliver','only exact cash can complete');
 });
 await check('CASH_short_amount_reports_not_delivers',()=>{
   const f=cashFixture();f.flush();f.win.b8ChooseDifferent();f.flush();
   f.win.b8AmountChanged({value:'200'});f.win.b8ReasonChosen('missing');
   f.win.b8Confirm();
   assert.deepEqual(f.calls.map(c=>c.method),['reportDriverCashShort']);
   assert(f.ctx.DV.note.includes('Missing'), 'reason passed to unchanged financial handler');
   const source=fs.readFileSync('driver.html','utf8');
   const s=source.slice(source.indexOf('async function confirmDeliver()'),source.indexOf('/* the 4 steps of a delivery'));
   assert(s.includes('await TLB.reportDriverCashShort(DV.id,amt,DV.note)'));
   assert(s.indexOf('await TLB.reportDriverCashShort')<s.indexOf('if(await finish('));
   // Genuine LOCAL HTTP backend check is E08 from exactly one tools/check_all.sh run.
 });
 console.log('BRIEF8_SOURCE_RESULT:',done,'/',done+errors,errors?'FAIL':'PASS','(mocked UI; backend via separate existing LOCAL HTTP E08)');
 if(errors)process.exit(1);
})().catch(e=>{console.error(e.stack);process.exit(1)});
