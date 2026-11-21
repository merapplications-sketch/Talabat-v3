/* TALABOT / NOTIFY-01 — shared visual safety for the original core 2.3s toast.
 * Four apps, NO changes to money, RPC, timing, permissions or other alert semantics.
 * Convert the core's bottom:96px fixed toast into a normal-flow status element;
 * insertion shifts the affected content rather than covering text or buttons.
 * Driver map errors are delegated to F-09's existing map status region.
 */
(function(){
 'use strict';
 if(window.__talabotSafeToast)return;
 const css=document.createElement('style');css.id='talabot-safe-toast';
 css.textContent=
 '.t15-flow-toast{position:static!important;inset:auto!important;left:auto!important;right:auto!important;top:auto!important;bottom:auto!important;transform:none!important;'+
 'z-index:auto!important;display:block!important;width:fit-content!important;min-height:0!important;max-width:min(86%,320px)!important;'+
 'box-sizing:border-box!important;overflow-wrap:break-word!important;white-space:normal!important;margin:8px auto 12px!important;'+
 'text-align:center!important;font-size:13px!important;line-height:18px!important;border-radius:22px!important;'+
 'pointer-events:none!important}';
 document.head.appendChild(css);
 function isCoreToast(e){
   if(!e||e.nodeType!==1||e.tagName!=='DIV'||e.parentElement!==document.body)return false;
   // Strictly recognize the ONE app-core toast primitive, independent of
   // Safari's normalized transform/left style serialization.
   const p=e.style.position||getComputedStyle(e).position;
   const z=Number(e.style.zIndex||getComputedStyle(e).zIndex);
   const b=parseFloat(e.style.bottom||getComputedStyle(e).bottom);
   return p==='fixed'&&z===10001&&Number.isFinite(b)&&Math.abs(b-96)<1;
 }
 function target(){
   // Product note and choices are scrolled together. New notice follows the note
   // in normal flow, never overlaying "Халапеньо" or "Пожелания".
   const options=document.querySelector('#app .d6s .osh');
   if(options){const note=options.querySelector('.d6-nt');return {container:options,after:note||null};}
   // Every modal owns its own scroller. An in-flow notification cannot cover
   // its footer buttons, even when the visual viewport is keyboard-reduced.
   const modal=document.querySelector('#app .ov .md,#app .sheet .asheet,#app .f07-reject');
   if(modal)return {container:modal};
   const mission=document.querySelector('#app #a-sheet-body');
   if(mission)return {container:mission};
   const main=document.querySelector('#app .pg,#app main,#app .a-utility,#app');
   return main?{container:main}:null;
 }
 /* AI-05 flow anchor: customer Home/menu only; keep the existing notice design. */
 function customerFlowContent(container){
   if(!container||container!==document.getElementById('app')||
      !/(?:^|\/)customer\.html$/i.test(location.pathname)||typeof S==='undefined'||
      !['home','menu'].includes(S.v)||document.querySelector('dialog[open],#app .sheet,#app .ov'))return null;
   return container.querySelector(':scope > .d6h,:scope > .d6m');
 }
 function customerFlowAnchor(container){
   const node=customerFlowContent(container);
   // At the document top, retain the original visible in-flow notification.
   return node&&scrollY>0?{node,container,view:S.v,top:node.getBoundingClientRect().top}:null;
 }
 function restoreCustomerFlowAnchor(anchor){
   if(!anchor||!anchor.node.isConnected||S.v!==anchor.view||customerFlowContent(anchor.container)!==anchor.node)return;
   const delta=anchor.node.getBoundingClientRect().top-anchor.top;
   // Measure what remains after native anchoring; newer WebKit may already be at zero.
   if(Math.abs(delta)>.5)window.scrollBy(0,delta);
 }
 function guardCustomerToastRemoval(notice,container){
   if(!customerFlowContent(container))return;
   const remove=notice.remove;
   notice.remove=function(){
     const anchor=customerFlowAnchor(this.parentElement);
     remove.call(this);
     restoreCustomerFlowAnchor(anchor);
   };
 }
 /* End AI-05 flow anchor. */
 /* Closed-customer ordering feedback does not belong in courier/merchant workflows. */
 function suppressClosedMerchantDriver(msg){
   if(!/(?:^|\/)(?:driver|merchant)\.html$/i.test(location.pathname))return false;
   const value=String(msg||'').trim();
   return /^(?:Ресторан сейчас закрыт|The restaurant is closed|Restaurant is currently closed)/i.test(value);
 }
 function place(e){
   if(!isCoreToast(e))return false;
   if(suppressClosedMerchantDriver(e.textContent)){e.remove();return true;}
   if(document.body.classList.contains('a-mission')&&
      typeof window.__talabotF09MapNotice==='function'&&
      window.__talabotF09MapNotice(e))return true;
   const dest=target();if(!dest)return false;
   const anchor=customerFlowAnchor(dest.container); // AI-05 flow anchor
   e.classList.add('t15-flow-toast');
   e.setAttribute('role',e.style.backgroundColor==='rgb(231, 76, 60)'?'alert':'status');
   e.setAttribute('aria-live','polite');
   if(dest.after&&dest.after.parentNode===dest.container)dest.after.after(e);
   else dest.container.prepend(e);
   restoreCustomerFlowAnchor(anchor);guardCustomerToastRemoval(e,dest.container); // AI-05 flow anchor
   // Keep focus where the user was typing. No scroll-to-top and no button clicks.
   return true;
 }
 function sweep(){
   if(!document.body)return;
   // On slow first loads, a failing Leaflet script may have emitted a toast
   // BEFORE this final script was parsed. MutationObserver does not replay it.
   for(const n of [...document.body.children])if(isCoreToast(n))place(n);
 }
 const obs=new MutationObserver(rs=>{
   for(const r of rs)for(const n of r.addedNodes)if(isCoreToast(n))place(n);
 });
 if(document.body){
   obs.observe(document.body,{childList:true});
   sweep();requestAnimationFrame(sweep);
   document.addEventListener('DOMContentLoaded',sweep,{once:true});
   window.addEventListener('pageshow',sweep);
 }
 // Intercept only *future explicit* map-failure toasts at their API entry;
 // internal core Leaflet callbacks are still caught by the observer and sweep.
 if(window.TLB&&typeof TLB.toast==='function'){
   const original=TLB.toast;
   TLB.toast=function(message,bad){
     const msg=String(message);
     if(suppressClosedMerchantDriver(msg))return;
     if(document.body.classList.contains('a-mission')&&
       (msg===TLB.t('mapFail')||msg===TLB.t('locMapFail'))&&
       typeof window.__talabotF09MapNotice==='function'){
       const virtual=document.createElement('div');virtual.textContent=msg;
       if(window.__talabotF09MapNotice(virtual))return;
     }
     return original.apply(this,arguments);
   };
 }
 window.__talabotSafeToast={isCoreToast,place,sweep};
})();
