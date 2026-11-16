/* TALABOT BRIEF-8: cash-only UI adapter after device-notes-v3.js.
 * Preserves EXACT approved confirmDeliver(), reportDriverCashShort(), Q14 and RPC. */
(function(){
 'use strict';
 if(typeof modal!=='function'||typeof render!=='function'||!window.__deviceNotesV3)return;
 const oldModal=modal,oldRender=render,money=window.__deviceNotesV3.money;
 const options=['short','dispute','missing','other'];
 TLB.addDict({
  b8Title:'Приём наличных',b8Due:'К оплате',b8Full:'Получено полностью {n} TJS',
  b8Different:'Другая сумма',b8Amount:'Получено наличными (TJS)',b8Reasons:'Причина различия',
  b8Select:'Коснитесь одной причины',b8Other:'Другая причина (словами)',
  b8Short:'Недоплата: доставка НЕ завершится; будет отправлено обращение в поддержку.',
  b8Exact:'Полная сумма — подтвердите доставку.',b8Over:'Сумма выше необходимой. Излишек не принимается.',
  b8AmountError:'Введите сумму с максимум двумя десятичными знаками.',
  b8ReasonError:'Выберите причину; для «Другое» нужны слова.',
  b8Confirm:'Подтвердить сумму',b8Cancel:'Отмена',
  b8ShortReason:'У клиента недостаточно наличных',b8Dispute:'Спор по заказу',
  b8Missing:'Не хватает товаров',b8OtherLabel:'Другое'
 },{
  b8Title:'Cash received',b8Due:'Amount due',b8Full:'Received full amount {n} TJS',
  b8Different:'Different amount',b8Amount:'Actual cash received (TJS)',b8Reasons:'Reason for difference',
  b8Select:'Select one reason',b8Other:'Other reason in words',
  b8Short:'Cash short: delivery will NOT complete; a support report will be sent.',
  b8Exact:'Full amount — confirm delivery.',b8Over:'Amount exceeds what is due. Excess is not accepted.',
  b8AmountError:'Enter amount with at most two decimals.',
  b8ReasonError:'Choose a reason; Other requires words.',
  b8Confirm:'Confirm amount',b8Cancel:'Cancel',
  b8ShortReason:'Customer has insufficient cash',b8Dispute:'Dispute about the order',
  b8Missing:'Missing items',b8OtherLabel:'Other'
 });
 const reasonLabel={short:'b8ShortReason',dispute:'b8Dispute',missing:'b8Missing',other:'b8OtherLabel'};
 const css=document.createElement('style');
 css.textContent='.b8-ov{position:fixed!important;left:0!important;right:0!important;top:var(--b8-top,0px)!important;bottom:auto!important;height:var(--b8-vh,100dvh)!important;display:flex!important;align-items:flex-end!important;overflow:hidden}.b8-sheet{width:min(430px,100%);height:min(610px,calc(var(--b8-vh,100dvh) - 12px));max-height:calc(var(--b8-vh,100dvh) - 12px)!important;min-height:0;display:flex;flex-direction:column;overflow:hidden!important;padding:12px 16px calc(10px + env(safe-area-inset-bottom,0px))!important;box-sizing:border-box;border-radius:16px 16px 0 0;transition:height .18s ease}.b8-head,.b8-footer{flex:none}.b8-content{flex:1;overflow-y:auto;min-height:0;overscroll-behavior:contain;-webkit-overflow-scrolling:touch}.b8-title{font-size:18px;margin:0 0 4px}.b8-actions{display:grid;grid-template-columns:1fr 1fr;gap:8px;margin:10px 0 6px}.b8-actions .b{min-width:0;min-height:48px;margin:0;padding:8px;white-space:normal}.b8-reserved{height:268px;min-height:268px;box-sizing:border-box;overflow:visible}.b8-reserved[aria-hidden=true]{visibility:hidden;pointer-events:none}.b8-label{font-weight:700;font-size:14px;display:block;margin:7px 0 5px}.b8-amt{display:block;width:100%;font-size:20px!important;height:52px;min-height:52px;margin:0;box-sizing:border-box}.b8-reason-slot{height:188px;min-height:188px;box-sizing:border-box;visibility:hidden;pointer-events:none}.b8-reason-slot.active{visibility:visible;pointer-events:auto}.b8-chips{display:grid;grid-template-columns:repeat(2,minmax(0,1fr));gap:6px;margin-top:6px}.b8-chip{min-height:44px;margin:0;border-radius:10px;padding:6px 8px;white-space:normal;overflow-wrap:anywhere;border:1px solid var(--line);background:#fff;color:var(--ink);font-size:12px;line-height:16px}.b8-chip[aria-pressed=true]{border:2px solid var(--o);background:var(--tint);font-weight:700}.b8-other-slot{height:50px;visibility:hidden;pointer-events:none}.b8-other-slot.active{visibility:visible;pointer-events:auto}.b8-other-input{width:100%;min-height:44px;height:44px;box-sizing:border-box;font-size:16px}.b8-policy{min-height:36px;font-size:12px;line-height:17px;margin:5px 0;color:var(--mut);font-weight:600}.b8-policy.short{color:#a72d25}.b8-sheet button:focus-visible,.b8-sheet input:focus-visible{outline:3px solid var(--o);outline-offset:2px}@media(max-width:370px){.b8-sheet{padding-left:12px!important;padding-right:12px!important}.b8-chip{font-size:11px}}@media(prefers-reduced-motion:reduce){.b8-sheet{transition:none}}';
 document.head.appendChild(css);
 const locked=()=>!DV||DV.up||DV.reportBusy||DLV[DV.id]||(DV.photo&&!DV.ph);
 const valid=()=>DV?money(DV.amt):null;
 const isDiff=()=>DV&&valid()!==null&&Math.abs(valid()-DV.total)>=0.005;
 const isShort=()=>DV&&valid()!==null&&valid()<DV.total-0.004;
 let frame=0;
 function position(){
  if(frame)return;
  frame=requestAnimationFrame(()=>{
   frame=0;
   const e=document.getElementById('b8-ov');if(!e)return;
   const v=window.visualViewport;
   e.style.setProperty('--b8-top',Math.max(0,v?v.offsetTop:0)+'px');
   e.style.setProperty('--b8-vh',Math.max(1,v?v.height:window.innerHeight)+'px');
  });
 }
 window.visualViewport?.addEventListener('resize',position);
 window.visualViewport?.addEventListener('scroll',position);
 window.addEventListener('resize',position);
 function paint(){
  if(!DV||!DV.cash)return;
  const mode=DV.cashMode==='different',diff=!!(mode&&isDiff());
  const reserv=document.getElementById('b8-reserved'),slot=document.getElementById('b8-reason-slot');
  if(reserv)reserv.setAttribute('aria-hidden',String(!mode));
  if(slot){slot.classList.toggle('active',diff);slot.setAttribute('aria-hidden',String(!diff));}
  const other=document.getElementById('b8-other-slot');
  if(other)other.classList.toggle('active',diff&&DV.b8Reason==='other');
  document.querySelectorAll('.b8-chip').forEach(e=>{
    e.setAttribute('aria-pressed',String(DV.b8Reason===e.dataset.reason));
    e.disabled=!diff||locked();
  });
  const note=document.getElementById('b8-policy');
  if(note){note.textContent=mode?(isShort()?t('b8Short'):
    valid()!==null&&valid()>DV.total+0.004?t('b8Over'):t('b8Exact')):t('b8Exact');
    note.classList.toggle('short',!!(mode&&isShort()));}
 }
 window.b8ChooseDifferent=function(){
  if(locked())return;
  DV.cashMode='different';DV.amt='';DV.note='';DV.b8Reason='';DV.b8Other='';
  render();
  requestAnimationFrame(()=>{try{$('cashAmt')?.focus({preventScroll:true})}catch(_){$('cashAmt')?.focus()}});
 };
 window.b8Full=function(){
  if(locked())return;
  DV.cashMode='full';DV.amt=String(DV.total);DV.note='';
  return confirmDeliver(); // existing approved financial handler
 };
 window.b8AmountChanged=function(el){
  if(!DV||!el||locked())return;
  DV.amt=el.value;
  if(!isDiff()){DV.b8Reason='';DV.b8Other='';DV.note='';}
  paint(); // NO rerender: controls are already in reserved fixed-height slot
 };
 window.b8ReasonChosen=function(id){
  if(locked()||!options.includes(id)||DV.cashMode!=='different'||!isDiff())return;
  DV.b8Reason=id;DV.b8Other=id==='other'?(DV.b8Other||''):'';
  DV.note=id==='other'?'':t(reasonLabel[id]);
  paint();
  if(id==='other')requestAnimationFrame(()=>{try{$('cashNote')?.focus({preventScroll:true})}catch(_){$('cashNote')?.focus()}});
 };
 window.b8OtherChanged=function(e){
  if(!DV||!e||locked()||DV.b8Reason!=='other')return;
  DV.b8Other=e.value;DV.note=e.value;
 };
 window.b8Confirm=function(){
  if(locked()||DV.cashMode!=='different')return;
  const n=valid();
  if(n===null){TLB.toast(t('b8AmountError'),true);$('cashAmt')?.focus();return}
  if(n>DV.total+0.004){TLB.toast(t('b8Over'),true);return}
  if(n<DV.total-0.004){
   if(!options.includes(DV.b8Reason)){TLB.toast(t('b8ReasonError'),true);return}
   const note=DV.b8Reason==='other'?String(DV.b8Other||'').trim():t(reasonLabel[DV.b8Reason]);
   if(!/\p{L}/u.test(note)){TLB.toast(t('b8ReasonError'),true);return}
   DV.note=note;
  }else DV.note='';
  DV.amt=String(n);
  return confirmDeliver(); // short -> reportDriverCashShort, never finish()
 };
 modal=function(){
  if(!DV||!DV.cash||CXL)return oldModal();
  const o=TLB.order(DV.id),busy=locked(),d=DV.cashMode==='different';
  let h='<div class="ov b8-ov" id="b8-ov"><div class="md b8-sheet" id="b8-sheet" role="dialog" aria-modal="true" aria-labelledby="b8-title">';
  h+='<div class="b8-head"><h3 class="b8-title" id="b8-title">'+esc(t('b8Title'))+'</h3><p class="xs mut">'+
    esc(t('b8Due'))+': <strong>'+DV.total.toFixed(2)+' TJS</strong></p></div><div class="b8-content">';
  if(DV.photo){
   h+='<h3>'+esc(t('photoT'))+'</h3><p class="xs mut">'+esc(t('photoS'))+'</p>';
   if(DV.ph)h+='<div class="php"><img src="'+esc(DV.ph.preview)+'" alt="'+esc(t('photoT'))+'"></div>';
   h+='<label class="phb">'+esc(t(DV.ph?'photoRe':'photoB'))+
     '<input type="file" accept="image/*" capture="environment" onchange="takePhoto(this)"'+(DV.up?' disabled':'')+' style="display:none"></label>';
  }
  if(o)h+=cashBox(o);
  h+='<div class="b8-actions"><button type="button" class="b g" id="b8-full" onclick="b8Full()"'+(busy?' disabled':'')+'>'+
    esc(t('b8Full').replace('{n}',DV.total.toFixed(2)))+'</button>'+
    '<button type="button" class="b s" id="b8-different" onclick="b8ChooseDifferent()"'+(busy?' disabled':'')+'>'+
    esc(t('b8Different'))+'</button></div>';
  h+='<div class="b8-reserved" id="b8-reserved" aria-hidden="'+(!d)+'"><label for="cashAmt" class="b8-label">'+
    esc(t('b8Amount'))+'</label>'+
    '<input id="cashAmt" class="b8-amt" type="text" inputmode="decimal" pattern="[0-9]+([.,][0-9]{1,2})?"'+
    ' enterkeyhint="done" autocomplete="off" placeholder="0.00" value="'+esc(d?DV.amt:'')+'"'+
    ' oninput="b8AmountChanged(this)"'+(!d||busy?' disabled':'')+'>'+
    '<div class="b8-reason-slot" id="b8-reason-slot"><span class="b8-label">'+esc(t('b8Reasons'))+'</span>'+
    '<div class="b8-chips" role="group" aria-label="'+esc(t('b8Select'))+'">'+
    options.map(id=>'<button type="button" class="b8-chip" data-reason="'+id+'" aria-pressed="'+(DV.b8Reason===id)+
      '" onclick="b8ReasonChosen(\''+id+'\')">'+esc(t(reasonLabel[id]))+'</button>').join('')+
    '</div><div class="b8-other-slot" id="b8-other-slot"><input class="b8-other-input" id="cashNote" type="text"'+
    ' maxlength="200" autocomplete="off" placeholder="'+esc(t('b8Other'))+'" value="'+esc(DV.b8Other||'')+'"'+
    ' oninput="b8OtherChanged(this)"'+(busy?' disabled':'')+'></div></div></div>'+
    '<p id="b8-policy" class="b8-policy" role="status"></p></div>';
  h+='<div class="b8-footer"><div class="b8-actions"><button class="b g" type="button" id="b8-confirm"'+
    ' onclick="b8Confirm()"'+(!d||busy?' disabled':'')+'>'+esc(t('b8Confirm'))+'</button>'+
    '<button class="b s" type="button" onclick="DV=null;render()">'+esc(t('b8Cancel'))+'</button></div></div></div></div>';
  return h;
 };
 render=function(){const out=oldRender.apply(this,arguments);paint();position();return out;};
 window.__brief8Cash={valid,isDiff,isShort,position};
 if(DV&&DV.cash)render();
})();