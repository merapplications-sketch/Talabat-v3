// Only ephemeral review/approval UI. Durable sent evidence lives in original attempt payload.
function priceSnapshot01(){
 const c=calc(),st=ALLS.find(x=>x.n===S.cartStore)||{},menu=menuOf(S.cartStore);
 const dec=v=>{if(typeof v!=='number'||!Number.isFinite(v))throw Error('price unavailable');return String(v);};
 const lines=Object.keys(S.cart).map(key=>{const p=pk(key),it=menu.find(x=>x.id===p.id);if(!it)throw Error('item unavailable');const q=S.cart[key],u=baseOf(it,p.ops),lt=u*q,rd=pctC(lt,Math.max(+st.rd||0,+it.discount||0)),ad=pctC(lt,Math.max(+st.rd||0,+it.discount||0,+st.hh||0)),ops=optRecs(it.id,p.ops);
  return{item_id:p.id,qty:q,base_price:dec(it.price),options:p.ops.map(id=>{const o=ops.find(x=>x.id===id);if(!o)throw Error('option unavailable');return{id,price_delta:dec(o.price)};}),unit_price:dec(u),restaurant_discount:dec(rd),happy_hour_discount:dec(ad-rd),net_items:dec(lt-ad)};});
 const v={version:1,lines,totals:{subtotal:dec(c.sub),restaurant_discount:dec(c.d),happy_hour_discount:dec(c.h),promo_discount:dec(c.p),points_value:dec(c.pv),delivery_fee:dec(c.fee),tip:dec(S.tip),wallet_used:dec(c.w),cash_due:dec(c.due),total:dec(c.total)}};
 if(!priceValid01(v))throw Error('price evidence unavailable');return v;
}
function priceContext01(){return JSON.stringify([ME.id,cartToken104(),curAddr(),priceSnapshot01()]);}
function priceApproval01(){const a=S.priceConsent01;try{return a&&a.context===priceContext01()&&!cartForeign104()&&priceValid01(a.value)?a:null;}catch(e){return null;}}
function priceRememberDisplayed01(){try{const context=priceContext01();if(S.priceConsent01&&S.priceConsent01.context!==context)S.priceConsent01=null;S.priceShown01={context,value:priceSnapshot01()};}catch(e){S.priceShown01=null;}}
function pricePrepare01(){const context=priceContext01(),a=priceApproval01(),shown=S.priceShown01;if(S.priceConsent01&&!a)throw Error('approved price context changed');if(!a&&(!shown||shown.context!==context))throw Error('displayed price context changed');return{context,value:priceCopy01(a?a.value:shown.value)};}
function priceDisplayLines01(){const s=S.priceShown01;if(!s)return'';return `<div class="card">${s.value.lines.map(l=>{const it=menuOf(S.cartStore).find(x=>x.id===l.item_id);return `<div class="row"><span>${l.qty} × ${esc(it?it.name:l.item_id)}</span><span>${esc(l.unit_price)} TJS → <b>${esc(l.net_items)} TJS</b></span></div>${l.options.map(o=>{const op=optRecs(l.item_id,[o.id])[0];return `<div class="xs">${esc(op?op.name:o.id)} · ${esc(o.price_delta)} TJS</div>`;}).join('')}`;}).join('')}</div>`;}
function priceReceive01(r,key,seq,prepared){
 if(r.status!=='rejected'||r.closed!==true||!r.closureId||!draftResponse105(key,seq)||cartForeign104()||prepared.context!==priceContext01()||!priceSelection01(prepared.value,r.priceReview))return false;
 S.priceConsent01=null;S.priceReview01={key,seq,context:prepared.context,before:priceCopy01(prepared.value),value:priceCopy01(r.priceReview),closureId:r.closureId};return true;
}
async function priceApprove01(){
 const r=S.priceReview01;if(S.busy||!r||!draftResponse105(r.key,r.seq)||cartForeign104()||r.context!==priceContext01())return;
 S.busy=true;render();
 try{
  const result=await TLB.endRejected104(r.key,true);
  if(result.status!=='ended_rejected'||result.closed!==true||result.closureId!==r.closureId||!draftResponse105(r.key,r.seq)||cartForeign104())return;
  // End only the proven rejected attempt. Cart edits during the await survive.
  const unchanged=r.context===priceContext01();
  if(!retireDraft105(r.key,r.seq))return;
  S.priceReview01=null;S.priceConsent01=unchanged?{context:r.context,before:r.before,value:r.value}:null;
 }catch(e){alert(TLB.lang()==='ru'?'Результат не подтверждён. Проверьте попытку.':'Outcome unconfirmed. Check the original attempt.');}
 finally{S.busy=false;render();}
}
function priceReviewView01(){
 const approved=priceApproval01();let r=S.priceReview01;
 try{if(r&&(!draftResponse105(r.key,r.seq)||r.context!==priceContext01()||cartForeign104()))r=null;}catch(e){r=null;}
 if(!r&&!approved)return'';r=r||approved;
 const ru=TLB.lang()==='ru',label=(a,b)=>ru?a:b;
 const names={base_price:label('Цена блюда','Item price'),unit_price:label('Цена с опциями','Unit with options'),restaurant_discount:label('Скидка ресторана','Restaurant discount'),happy_hour_discount:'Happy Hour',net_items:label('Сумма блюд','Net items'),subtotal:label('Подытог','Subtotal'),promo_discount:label('Промокод','Promo'),points_value:label('Баллы','Points'),delivery_fee:label('Доставка','Delivery'),tip:label('Чаевые','Tip'),wallet_used:label('Кошелёк','Wallet'),cash_due:label('Наличными','Cash due'),total:label('Итого','Total')};
 const pair=(name,old,value)=>`<div class="row"><span>${esc(name)}</span><span>${esc(String(old))} → <b>${esc(String(value))} TJS</b></span></div>`;
 const lines=r.value.lines.map((l,i)=>{const old=r.before.lines[i],it=menuOf(S.cartStore).find(x=>x.id===l.item_id);return `<div class="card"><h3>${l.qty} × ${esc(it?it.name:l.item_id)}</h3>${['base_price','unit_price','restaurant_discount','happy_hour_discount','net_items'].map(k=>pair(names[k],old[k],l[k])).join('')}${l.options.map((o,j)=>pair(label('Опция ','Option ')+o.id,old.options[j].price_delta,o.price_delta)).join('')}</div>`;}).join('');
 return `<div class="pg"><h2>${approved?label('Цена подтверждена','Price approved'):label('Цена изменилась','Price changed')}</h2><p>${label('Заказ не создан. Проверьте цены и новую сумму.','No order was created. Review the prices and new total.')}</p>${lines}<div class="card">${Object.keys(names).filter(k=>k in r.value.totals).map(k=>pair(names[k],r.before.totals[k],r.value.totals[k])).join('')}</div><button class="btn big" ${S.busy?'disabled':''} onclick="${approved?'place()':'priceApprove01()'}">${approved?label('Подтвердить заказ','Confirm order'):label('Согласиться с новыми ценами','Approve new prices')} · ${esc(r.value.totals.total)} TJS</button><button class="btn t" onclick="go('cart')">${label('Вернуться в корзину','Return to cart')}</button></div>`;
}
