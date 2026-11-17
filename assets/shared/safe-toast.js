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
   return e&&e.nodeType===1&&e.tagName==='DIV'&&e.parentElement===document.body&&
     e.style.position==='fixed'&&e.style.bottom==='96px'&&
     e.style.zIndex==='10001'&&e.style.left==='50%'&&
     String(e.style.transform).includes('translateX');
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
 const obs=new MutationObserver(rs=>{
   for(const r of rs)for(const n of r.addedNodes)if(isCoreToast(n))place(n);
 });
 if(document.body)obs.observe(document.body,{childList:true});
 window.__talabotSafeToast={isCoreToast,place};
})();