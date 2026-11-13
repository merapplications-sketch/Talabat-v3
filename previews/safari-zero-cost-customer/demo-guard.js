/* Visual preview only: no order, finance, authentication or messaging mutations. */
(function(){'use strict';
window.__demoBlockedActions=0;
var noAction=function(){window.__demoBlockedActions++;var isEn=window.TLB&&TLB.lang()==='en';if(window.TLB&&TLB.toast)TLB.toast(isEn?'DEMO: No real orders or payments':'ДЕМО: Заказы и оплата отключены',true);return Promise.resolve({error:'demo_only'})};
['placeOrder','confirmOrder','writeOrderReturn','setStatus','deliver','chat','uploadProof','settleCash','groupCreate','setMyPhone'].forEach(function(k){if(window.TLB&&typeof TLB[k]==='function')TLB[k]=noAction});
window.addEventListener('load',function(){
  if(typeof window.place==='function')window.place=noAction;
  if(typeof window.holdOk==='function')window.holdOk=noAction;
  var banner=document.getElementById('tlb-demo-banner');
  function update(){if(banner&&window.TLB)banner.textContent=TLB.lang()==='en'?'VISUAL DEMO · Fake data · No real orders or payments':'ДЕМО-ВЕРСИЯ · Вымышленные данные · Заказы и оплата отключены'}
  update();
  if(window.TLB&&typeof TLB.setLang==='function'){var set=TLB.setLang;TLB.setLang=function(l){set.call(this,l);update()}}
});
})();
