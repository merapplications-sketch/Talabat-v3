/* TALABOT / NOTIFY-01 — shared visual safety for the original core 2.3s toast.
 * Four apps, NO changes to money, RPC, text, timing, permissions or alert semantics.
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
 'z-index:auto!important;display:block!important;width:auto!important;min-height:36px!important;max-width:100%!important;'+
 'box-sizing:border-box!important;overflow-wrap:anywhere!important;white-space:normal!important;margin:8px 0 12px!important;'+
 'text-align:center!important;font-size:13px!important;line-height:18px!important;border-radius:12px!important;'+
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
 function place(e){
   if(!isCoreToast(e))return false;
   if(document.body.classList.contains('a-mission')&&
      typeof window.__talabotF09MapNotice==='function'&&
      window.__talabotF09MapNotice(e))return true;
   const dest=target();if(!dest)return false;
   e.classList.add('t15-flow-toast');
   e.setAttribute('role',e.style.backgroundColor==='rgb(231, 76, 60)'?'alert':'status');
   e.setAttribute('aria-live','polite');
   if(dest.after&&dest.after.parentNode===dest.container)dest.after.after(e);
   else dest.container.prepend(e);
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