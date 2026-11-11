function tipText02(k){const ru=TLB.lang()==='ru';return ({other:ru?'Другая сумма':'Other amount',label:ru?'Сумма чаевых (TJS)':'Tip amount (TJS)',help:ru?'По желанию. Целое число от 1 до 100. Все чаевые получает курьер.':'Optional. Whole number from 1 to 100. The driver keeps the full tip.',error:ru?'Введите целое число от 1 до 100 или выберите «Нет».':'Enter a whole number from 1 to 100, or choose None.'})[k];}
function tipGet02(){
 if(S.tipMode02==='other'){
  const raw=String(S.tipRaw02??'').trim();const n=Number(raw);
  return {ok:/^[0-9]+$/.test(raw)&&tipNumber02(n).ok&&n>=1,value:n};
 }
 return tipNumber02(S.tip);
}
function tipSelect02(value){
 if(cartForeign104())return;
 S.tipMode02=value==='other'?'other':'quick';S.tipSentKey02=null;
 if(value==='other'){S.tipRaw02='';}else{S.tip=value;S.tipRaw02='';}
 cartSave();render();
}
function tipInput02(raw){
 if(cartForeign104())return;
 S.tipMode02='other';S.tipRaw02=String(raw);S.tipSentKey02=null;
 const parsed=tipGet02();if(parsed.ok)S.tip=parsed.value;
 cartSave();render();
 if(typeof document!=='undefined'){const e=document.getElementById('tip02-amount');if(e){e.focus();e.setSelectionRange(e.value.length,e.value.length);}}
}
function tipComplete02(key){
 // A deliberate later selection belongs to the preserved draft, not the completed order.
 if(S.tipSentKey02===null||S.tipSentKey02&&S.tipSentKey02!==key)return;
 S.tip=0;S.tipMode02='quick';S.tipRaw02='';S.tipSentKey02=null;cartSave();
}
function tipRestore02(d){
 if(!Object.prototype.hasOwnProperty.call(d,'tip')){S.tip=0;S.tipMode02='quick';S.tipRaw02='';S.tipSentKey02=undefined;return;}
 S.tipMode02=d.tipMode02==='other'?'other':'quick';S.tipRaw02=typeof d.tipRaw02==='string'?d.tipRaw02:'';
 S.tipSentKey02=Object.prototype.hasOwnProperty.call(d,'tipSentKey02')?d.tipSentKey02:undefined;
 if(tipNumber02(d.tip).ok){S.tip=d.tip;if(!d.tipMode02&&![0,5,10,20].includes(d.tip)){S.tipMode02='other';S.tipRaw02=String(d.tip);}}
 else {S.tipMode02='other';S.tipRaw02=String(d.tip??'');}
}
function tipPanel02(){const valid=tipGet02();return `<div class="card"><h3>${t('tip')}</h3><div class="tipr" style="flex-wrap:wrap">${[0,5,10,20].map(v=>`<button type="button" class="tip ${S.tipMode02!=='other'&&S.tip===v?'on':''}" aria-pressed="${S.tipMode02!=='other'&&S.tip===v}" onclick="tipSelect02(${v})">${v?v+' TJS':t('none')}</button>`).join('')}<button type="button" class="tip ${S.tipMode02==='other'?'on':''}" aria-pressed="${S.tipMode02==='other'}" onclick="tipSelect02('other')">${tipText02('other')}</button></div>${S.tipMode02==='other'?`<label for="tip02-amount" style="display:block;margin-top:12px">${tipText02('label')}</label><input class="fld" id="tip02-amount" type="text" inputmode="numeric" autocomplete="off" value="${esc(S.tipRaw02||'')}" aria-invalid="${!valid.ok}" aria-describedby="tip02-help tip02-error" oninput="tipInput02(this.value)" style="font-size:16px">`:''}<p id="tip02-help" class="xs mut" style="margin-top:8px">${tipText02('help')}</p><p id="tip02-error" role="status" style="color:var(--bad)">${valid.ok?'':tipText02('error')}</p></div>`;}
