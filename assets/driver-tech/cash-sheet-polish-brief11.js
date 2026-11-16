/* TALABOT BRIEF-11 — Safari-visible cash sheet/layout adapter.
 * UI ONLY. Original confirmDeliver, report_driver_cash_short RPC, Q14/CASH-01 remain unchanged. */
(function(){
 'use strict';
 if(!window.__brief8Cash||typeof render!=='function'||typeof modal!=='function')return;
 TLB.addDict({
  b11Waiting:'Обращение в поддержку отправлено — ожидайте решения. Доставка НЕ завершена.',
  b11Call:'Позвонить в поддержку',b11NoPhone:'Номер поддержки пока не указан. Дождитесь решения.',
  b11Already:'Обращение уже отправлено. Ожидайте решения поддержки.'
 },{
  b11Waiting:'Reported to support — awaiting a decision. Delivery NOT completed.',
  b11Call:'Call support',b11NoPhone:'Support phone is not configured. Await a decision.',
  b11Already:'Shortfall already reported. Await support decision.'
 });
 const sheetCSS=document.createElement('style');
 sheetCSS.id='b11-safari-layout';
 sheetCSS.textContent=[
  'body.b11-cash-open #app .a-dock,body.b11-cash-open #app .a-ready-recentre,body.b11-cash-open #app .w-grip>svg{visibility:hidden!important}',
  'body.b11-cash-open{overscroll-behavior:none}',
  '.b8-ov{position:fixed!important;top:var(--b11-top,0px)!important;left:0!important;right:0!important;bottom:auto!important;height:var(--b11-height,100dvh)!important;max-width:100vw!important;align-items:flex-end!important;justify-content:center!important;overflow:hidden!important;z-index:20000!important;pointer-events:auto!important;background:rgba(19,31,48,.78)!important}',
  '.b8-sheet{position:relative!important;width:min(430px,100%)!important;max-width:100vw!important;height:auto!important;min-height:0!important;max-height:calc(var(--b11-height,100dvh) - 6px)!important;flex:0 1 auto!important;display:flex!important;flex-direction:column!important;padding:10px max(12px,env(safe-area-inset-right)) calc(8px + env(safe-area-inset-bottom,0px)) max(12px,env(safe-area-inset-left))!important;box-sizing:border-box!important;overflow:hidden!important;margin:0 auto!important;border-radius:16px 16px 0 0!important;transition:max-height .18s ease!important}',
  '.b8-head,.b8-footer{flex:none!important;min-width:0;position:relative;z-index:1;background:#fff}',
  '.b8-head{padding-bottom:4px}.b8-content{flex:1 1 auto!important;min-height:0!important;overflow-y:auto!important;overflow-x:hidden!important;overscroll-behavior:contain;-webkit-overflow-scrolling:touch;scroll-padding-bottom:12px}',
  '.b8-footer{padding-top:4px;border-top:1px solid var(--line,#e0e5ec)}.b8-footer .b8-actions{margin:4px 0 0!important}',
  '.b8-reserved{height:auto!important;min-height:0!important;overflow:visible!important}',
  '.b8-reserved[aria-hidden=true]{display:none!important}',
  '.b8-reason-slot{display:none!important;height:auto!important;min-height:0!important;visibility:visible!important;pointer-events:auto!important}',
  '.b8-reason-slot.active{display:block!important}',
  '.b8-other-slot{display:none!important;height:auto!important;min-height:0!important;visibility:visible!important;pointer-events:auto!important}',
  '.b8-other-slot.active{display:block!important}',
  '.b8-policy{min-height:0!important;margin:5px 0 4px!important;overflow-wrap:anywhere!important}',
  '.b8-actions{grid-template-columns:minmax(0,1fr) minmax(0,1fr)!important;min-width:0;gap:8px}',
  '.b8-actions .b{max-width:100%;min-width:0!important;overflow-wrap:anywhere;white-space:normal;font-size:13px}',
  '.b8-amt,.b8-other-input{max-width:100%;min-width:0;scroll-margin:12px 0 90px;box-sizing:border-box}',
  '.b11-inline-alert{display:none;border-radius:10px;padding:8px 10px;background:#fff4f1;color:#8c2924;font-size:12px;line-height:17px;font-weight:600;overflow-wrap:anywhere}',
  '.b11-inline-alert:not(:empty){display:block;margin:6px 0}',
  '.n-chooser{position:fixed!important;left:0!important;right:0!important;width:100vw!important;max-width:100vw!important;z-index:20000!important;box-sizing:border-box!important;overflow-x:hidden!important;pointer-events:auto!important}',
  '.n-chooser .md{box-sizing:border-box!important;width:min(430px,100%)!important;max-width:100vw!important;margin:0 auto!important;padding-left:max(12px,env(safe-area-inset-left))!important;padding-right:max(12px,env(safe-area-inset-right))!important;min-width:0!important;max-height:calc(100dvh - 12px)!important;overflow-x:hidden!important}',
  '.n-chooser .n-body,.n-chooser .n-map-icons,.n-chooser .n-map-item,.n-chooser .n-map-link,.n-chooser .n-map-label{min-width:0!important;max-width:100%!important;box-sizing:border-box!important}',
  '.n-chooser .n-map-label,.n-chooser .n-hint,.n-chooser .n-note,.n-chooser .n-destination{white-space:normal!important;overflow-wrap:anywhere!important}',
  '.n-chooser .n-map-icons{grid-template-columns:repeat(3,minmax(0,1fr))!important}',
  '.n-chooser .n-map-link,.n-chooser .n-map-radio{min-height:44px!important}',
  '.b11-waiting{border:1px solid #bddfcb;background:#effaf2;border-radius:12px;padding:10px 12px;margin:6px 0;color:#145634;overflow-wrap:anywhere;line-height:19px;font-size:13px}',
  '.b11-waiting strong{display:block;font-weight:700}.b11-waiting .b11-support{display:inline-flex;align-items:center;justify-content:center;min-height:44px;border-radius:10px;padding:8px 12px;margin-top:8px;background:var(--o,#f1511b);color:white;font-weight:700;text-decoration:none;border:0}',
  '.b11-waiting .b11-support:disabled{background:#949ca4;color:white}',
  '.b11-waiting small{display:block;line-height:17px;margin-top:5px}',
  '@media(max-width:370px){.b8-actions{gap:6px}.b8-actions .b{font-size:12px}.n-chooser .n-map-icons{gap:4px!important}}',
  '@media(prefers-reduced-motion:reduce){.b8-sheet{transition:none!important}}'
 ].join('');
 document.head.appendChild(sheetCSS);
 const priorRender=render,priorToast=TLB.toast,priorConfirm=window.b8Confirm,priorReport=TLB.reportDriverCashShort,priorClick=deliverClick;
 let successfulReport=null,viewportFrame=0;
 const reportKey=id=>'talabot:b11:short:'+String(DRV&&DRV.id||'unknown')+':'+String(id);
 const hasReport=id=>{
   try{return sessionStorage.getItem(reportKey(id))==='1'}catch(_){return false}
 };
 const remember=id=>{
   try{sessionStorage.setItem(reportKey(id),'1')}catch(_){}
 };
 const activeSheet=()=>document.body.querySelector(':scope > #b8-ov');
 function syncViewport(){
   viewportFrame=0;
   const sheet=activeSheet();if(!sheet)return;
   const v=window.visualViewport;
   sheet.style.setProperty('--b11-top',Math.max(0,v?v.offsetTop:0)+'px');
   sheet.style.setProperty('--b11-height',Math.max(1,v?v.height:window.innerHeight)+'px');
   const active=document.activeElement;
   if(active&&(active.id==='cashAmt'||active.id==='cashNote'))scrollFocused(active);
 }
 function scheduleViewport(){
   if(viewportFrame)return;
   viewportFrame=requestAnimationFrame(syncViewport);
 }
 function scrollFocused(el){
   const sc=document.querySelector('.b8-content');if(!sc||!sc.contains(el))return;
   const r=el.getBoundingClientRect(),c=sc.getBoundingClientRect(),pad=10;
   if(r.bottom>c.bottom-pad)sc.scrollTop+=r.bottom-(c.bottom-pad);
   if(r.top<c.top+pad)sc.scrollTop-=c.top+pad-r.top;
 }
 function restoreFocus(){
   scheduleViewport();
   requestAnimationFrame(syncViewport);
   setTimeout(syncViewport,90);
   setTimeout(syncViewport,260);
 }
 window.visualViewport?.addEventListener('resize',restoreFocus);
 window.visualViewport?.addEventListener('scroll',scheduleViewport);
 window.addEventListener('resize',restoreFocus);
 document.addEventListener('focusin',function(ev){
   if(ev.target.id==='cashAmt'||ev.target.id==='cashNote')restoreFocus();
 });
 document.addEventListener('input',function(ev){
   if(ev.target.id==='cashAmt'||ev.target.id==='cashNote')scheduleViewport();
 });
 function supportPhone(){
   let raw='';
   try{raw=String(TLB.supportInfo?.().phone||'')}catch(_){}
   if(!/^\+?[\d ()-]{7,22}$/.test(raw))return '';
   const clean=raw.replace(/[^\d+]/g,'');
   return /^\+?\d{7,17}$/.test(clean)?clean:'';
 }
 function updateWaitingCard(){
   const card=document.querySelector('#app .a-sheet.a-compact-card')||document.querySelector('#app .sht');
   if(!card)return;
   const order=typeof mine==='function'?mine():null;
   if(!order||order.status!=='pickedup'||!hasReport(order.id))return;
   const body=card.querySelector('#a-sheet-body')||card.querySelector('.shb')||card;
   let node=body.querySelector('.b11-waiting');
   if(!node){node=document.createElement('section');node.className='b11-waiting';node.setAttribute('role','status');body.prepend(node);}
   const title=document.createElement('strong');title.textContent=t('b11Waiting');
   node.replaceChildren(title);
   const phone=supportPhone();
   if(phone){const a=document.createElement('a');a.className='b11-support';a.href='tel:'+phone;a.textContent=t('b11Call');node.appendChild(a);}
   else{const btn=document.createElement('button');btn.className='b11-support';btn.disabled=true;btn.textContent=t('b11Call');node.appendChild(btn);
     const hint=document.createElement('small');hint.textContent=t('b11NoPhone');node.appendChild(hint);}
   const action=document.querySelector('#app #a-dock .a-step-button');
   if(action&&typeof aTaskStage==='function'&&aTaskStage(order)===4){
     action.disabled=true;action.textContent=t('b11Already');
   }
 }
 function moveOverlay(id){
   const found=document.querySelector('#app '+id);
   if(found)document.body.appendChild(found);
 }
 render=function(){
   const oldCash=activeSheet(),oldNav=document.body.querySelector(':scope > .n-chooser');
   if(oldCash)oldCash.remove();
   if(oldNav)oldNav.remove();
   const out=priorRender.apply(this,arguments);
   moveOverlay('#b8-ov');moveOverlay('.n-chooser');
   const opened=!!activeSheet();
   document.body.classList.toggle('b11-cash-open',opened);
   if(opened){const head=activeSheet().querySelector('.b8-head');
     if(head&&!head.querySelector('.b11-inline-alert')){
       const a=document.createElement('p');a.className='b11-inline-alert';a.setAttribute('role','status');a.setAttribute('aria-live','polite');head.appendChild(a);
     }
     syncViewport();
   }
   updateWaitingCard();
   return out;
 };
 TLB.toast=function(msg,bad){
   const sheet=activeSheet();
   if(sheet){
     const a=sheet.querySelector('.b11-inline-alert');
     if(a){a.textContent=String(msg);a.dataset.error=bad?'true':'false';scheduleViewport();return;}
   }
   return priorToast.apply(this,arguments);
 };
 if(typeof priorReport==='function'){
   TLB.reportDriverCashShort=function(id){
     const out=priorReport.apply(this,arguments);
     return Promise.resolve(out).then(function(response){
       if(response&&!response.error&&response.ticket_id!=null){
         successfulReport=String(id);
       }
       return response;
     });
   };
 }
 window.b8Confirm=async function(){
   const id=DV&&DV.id;
   if(id!=null&&hasReport(id)){TLB.toast(t('b11Already'),true);return;}
   successfulReport=null;
   const outcome=priorConfirm.apply(this,arguments);
   await outcome;
   if(id!=null&&successfulReport===String(id)&&DV&&String(DV.id)===String(id)){
     remember(id);
     DV=null;
     render();
   }
   return outcome;
 };
 deliverClick=function(id){
   if(hasReport(id)){TLB.toast(t('b11Already'),true);return;}
   return priorClick.apply(this,arguments);
 };
 window.__brief11={syncViewport:syncViewport,hasReport:hasReport,scrollFocused:scrollFocused,supportPhone:supportPhone};
 if(DV&&DV.cash)render();
})();