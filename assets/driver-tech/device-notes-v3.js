/* TALABOT driver device N-04 / N-05 — presentation adapter.
   Source financial RPC/Q14/Gate1 logic is NOT changed. No server, network or SQL action. */
(function(){
  'use strict';
  if(typeof deliverClick!=='function'||typeof modal!=='function'||typeof render!=='function')return;
  TLB.addDict({
    n04Full:'Получил всю сумму: {n} TJS',n04Other:'Другая сумма',n04Amount:'Фактически получено наличными (TJS)',
    n04AmountHint:'Введите реально полученную сумму здесь, НЕ в поле причины.',
    n04Reason:'Причина разницы (словами, не сумма)',n04ReasonHint:'Опишите причину словами. Только цифры не принимаются.',
    n04ReasonErr:'Укажите причину словами. Поле причины не предназначено для суммы.',
    n04AmountErr:'Введите сумму с максимум двумя знаками после запятой.',
    n04DifferentConfirm:'Подтвердить указанную сумму',n05Tap:'Звук заблокирован iOS — нажмите значок звука.',
    n04NavBack:'Отмена'
  },{
    n04Full:'Received full amount: {n} TJS',n04Other:'Different amount',n04Amount:'Actual cash received (TJS)',
    n04AmountHint:'Enter the amount actually received HERE, not in the reason field.',
    n04Reason:'Reason for difference (words, not amount)',n04ReasonHint:'Describe the difference in words. Numbers alone are invalid.',
    n04ReasonErr:'Enter a reason in words, not a number.',
    n04AmountErr:'Enter an amount with up to two decimal places.',
    n04DifferentConfirm:'Confirm entered amount',n05Tap:'iOS muted audio — tap the sound icon to restore it.',
    n04NavBack:'Cancel'
  });
  var css=document.createElement('style');
  css.textContent='.n04-overlay{position:fixed!important;left:0;right:0;top:var(--a-vtop,0px)!important;height:var(--a-vh,100dvh)!important;bottom:auto!important;align-items:flex-end}.n04-modal{max-height:82dvh;overflow-y:auto;overscroll-behavior:contain;-webkit-overflow-scrolling:touch}.n04-options{display:flex;flex-direction:column;gap:8px}.n04-options button{margin:0;min-height:50px}.n04-amount-label,.n04-reason-label{display:block;font-size:14px;font-weight:700;margin:10px 0 6px}.n04-decimal{font-size:20px!important;min-height:54px;font-weight:700}.n04-hint{font-size:12px;color:var(--mut);line-height:1.45;margin:3px 0 9px}.n04-reason[hidden]{display:none}.n04-modal button:disabled{opacity:.5}';
  document.head.appendChild(css);
  var priorDeliver=deliverClick,priorModal=modal,priorRender=render,priorUnlock=unlockSound;
  function money(value){
    var v=String(value==null?'':value).trim().replace(',','.');
    if(!/^\d+(?:\.\d{1,2})?$/.test(v))return null;
    var n=Number(v);return Number.isFinite(n)&&n>=0?n:null;
  }
  function differs(){
    var amount=DV?money(DV.amt):null;
    return !!(DV&&DV.cashMode==='different'&&amount!==null&&Math.abs(amount-DV.total)>=0.005);
  }
  function position(){
    var ov=document.getElementById('n04-ov'),panel=document.getElementById('n04-modal');
    if(!ov||!panel)return;
    var vv=window.visualViewport,top=vv?vv.offsetTop:0,height=vv?vv.height:window.innerHeight;
    ov.style.top=Math.max(0,top)+'px';ov.style.height=Math.max(1,height)+'px';ov.style.bottom='auto';
    panel.style.maxHeight=Math.max(140,height-8)+'px';
    if(document.activeElement&&document.activeElement.id==='cashAmt'){
      document.activeElement.scrollIntoView({block:'nearest'});
    }
  }
  window.visualViewport?.addEventListener('resize',position);
  window.visualViewport?.addEventListener('scroll',position);
  window.addEventListener('resize',position);
  deliverClick=function(id){
    var o=TLB.order(id);
    if(!o||DLV[id])return;
    if(!TLB.isCash(o))return priorDeliver(id);
    DV={id:id,cash:true,photo:!!o.leaveAtDoor,total:due(o),amt:String(due(o)),cashMode:'full',
        note:'',ph:null,up:false};
    render();
  };
  window.n04ShowDifferent=function(){
    if(!DV||!DV.cash||DV.up||DV.reportBusy||DLV[DV.id])return;
    DV.cashMode='different';DV.amt='';DV.note='';render();position();
    var e=$('cashAmt');
    if(e){try{e.focus({preventScroll:true})}catch(x){e.focus()}}
  };
  window.n04InputChanged=function(e){
    if(!DV||!e)return;
    DV.amt=e.value;var row=$('n04-reason');if(row)row.hidden=!differs();
    if(!differs()){DV.note='';var f=$('cashNote');if(f)f.value=''}
  };
  window.n04Full=function(){
    if(!DV||!DV.cash||DV.up||DV.reportBusy||DLV[DV.id])return;
    DV.amt=String(DV.total);DV.note='';DV.cashMode='full';
    return confirmDeliver();
  };
  window.n04Different=function(){
    if(!DV||!DV.cash||DV.cashMode!=='different'||DV.up||DV.reportBusy||DLV[DV.id])return;
    var amt=money(DV.amt);
    if(amt===null){TLB.toast(t('n04AmountErr'),true);$('cashAmt')?.focus();return}
    if(differs()){
      var note=String(DV.note||'').trim();
      if(!note||!/[^\d\s.,+\-]/u.test(note)||!/\p{L}/u.test(note)){
        TLB.toast(t('n04ReasonErr'),true);$('cashNote')?.focus();return;
      }
      DV.note=note;
    }else DV.note='';
    DV.amt=String(amt); // normalize decimal comma before the approved confirmDeliver().
    return confirmDeliver();
  };
  modal=function(){
    if(!DV||!DV.cash||CXL)return priorModal();
    var o=TLB.order(DV.id),locked=!!(DV.up||DV.reportBusy||(DV.photo&&!DV.ph)||DLV[DV.id]);
    var html='<div class="ov n04-overlay" id="n04-ov"><div class="md n04-modal" id="n04-modal" role="dialog" aria-modal="true" aria-label="'+esc(t('recvQ'))+'">';
    if(DV.photo){
      html+='<h3>'+esc(t('photoT'))+'</h3><p class="xs mut">'+esc(t('photoS'))+'</p>';
      if(DV.ph)html+='<div class="php"><img src="'+esc(DV.ph.preview)+'" alt="'+esc(t('photoT'))+'"></div>';
      html+='<label class="phb">'+(DV.up?esc(t('photoUp')):ico('cam',18)+' '+esc(DV.ph?t('photoRe'):t('photoB')))+
        '<input type="file" accept="image/*" capture="environment" style="display:none" onchange="takePhoto(this)" '+(DV.up?'disabled':'')+'></label>';
    }
    if(o)html+=cashBox(o);
    html+='<h3>'+esc(t('recvQ'))+'</h3><div class="n04-options">'+
      '<button type="button" class="b g" id="n04-full" onclick="n04Full()" '+(locked?'disabled':'')+'>'+esc(t('n04Full').replace('{n}',DV.total.toFixed(2)))+'</button>'+
      '<button type="button" class="b s" id="n04-other" onclick="n04ShowDifferent()" '+(locked?'disabled':'')+'>'+esc(t('n04Other'))+'</button></div>';
    if(DV.cashMode==='different'){
      html+='<label class="n04-amount-label" for="cashAmt">'+esc(t('n04Amount'))+'</label>'+
        '<input id="cashAmt" type="text" inputmode="decimal" enterkeyhint="done" autocomplete="off" class="n04-decimal" placeholder="0.00" value="'+esc(DV.amt)+'" oninput="n04InputChanged(this)" '+(locked?'disabled':'')+'>'+
        '<p class="n04-hint">'+esc(t('n04AmountHint'))+'</p>'+
        '<div class="n04-reason" id="n04-reason" '+(differs()?'':'hidden')+'>'+
          '<label class="n04-reason-label" for="cashNote">'+esc(t('n04Reason'))+'</label>'+
          '<input type="text" id="cashNote" maxlength="200" placeholder="'+esc(t('n04ReasonHint'))+'" value="'+esc(DV.note)+'" oninput="DV.note=this.value"></div>'+
        '<button type="button" class="b g" id="n04-confirm" onclick="n04Different()" '+(locked?'disabled':'')+'>'+esc(t('n04DifferentConfirm'))+'</button>';
    }
    html+='<button type="button" class="b s" id="n04-cancel" onclick="DV=null;render()">'+esc(t('cancelB'))+'</button></div></div>';
    return html;
  };
  render=function(){
    var x=priorRender.apply(this,arguments);position();return x;
  };
  // AudioContext must be unlocked by a real gesture on iOS; retry once after
  // online, then show the original sound button + an explicit reason if suspended.
  function checkSound(){
    if(!online)return;
    TLB.unlockAudio();
    setTimeout(function(){
      if(!online)return;
      if(!TLB.audioReady())TLB.toast(t('n05Tap'),true);
      render();
    },420);
  }
  unlockSound=function(){
    priorUnlock();
    setTimeout(function(){if(online&&!TLB.audioReady())TLB.toast(t('n05Tap'),true);render()},420);
  };
  window.addEventListener('online',checkSound);
  document.addEventListener('visibilitychange',function(){if(!document.hidden&&online&&!TLB.audioReady())checkSound()});
  // Export pure/harmless diagnostics for isolated source/browser tests.
  window.__deviceNotesV3={money:money,differs:differs,position:position};
})();
