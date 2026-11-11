"""Isolated PRICE01 overlay after accepted TIP02; no historical file changes."""
from pathlib import Path
import subprocess,sys
base,out=map(Path,sys.argv[1:3]);subprocess.run([sys.executable,'tests/tip02/build-client.py',str(base),str(out)],check=True)
def once(s,a,b):
 assert s.count(a)==1,('source drift',a,s.count(a));return s.replace(a,b,1)
contract=Path('tests/price01-impl/contract.js').read_text();ui=Path('tests/price01-impl/ui.js').read_text()
p=out/'customer.html';s=p.read_text()
s=once(s,'function ensureDraft105(){',contract+'\n'+ui+'\nfunction ensureDraft105(){')
s=once(s,"  const tip02=tipGet02();", "  let pricePrepared01;try{pricePrepared01=pricePrepare01();}catch(e){render();alert(TLB.lang()==='ru'?'Обновите цены перед подтверждением.':'Refresh prices before confirming.');return;}\n  const tip02=tipGet02();")
s=once(s,'    if(!S.okey)S.okey=newKey();render();',"    if(pricePrepared01.context!==priceContext01()||cartForeign104()){alert(TLB.lang()==='ru'?'Корзина или цена изменились. Подтвердите снова.':'Cart or price changed. Confirm again.');return;}\n    if(!S.okey)S.okey=newKey();render();")
s=once(s,'extra:optExtra(),key:S.okey',"extra:Object.assign({},optExtra(),{price01:pricePrepared01.value}),key:S.okey")
s=once(s,"    if(r.error){if(r.error=='wallet_changed')", "    if(r.error){if(ownsDraft105&&r.error==='price_changed'&&priceReceive01(r,sentKey105,seq105,pricePrepared01)){render();return;}if(r.error=='wallet_changed')")
# Earlier financial guards still reject as before; refresh catalog for the next
# explicit checkout, without editing the failed payload or generating a new key.
s=once(s,"if(r.error=='wallet_changed')TLB.loadWallet(true);", "if(r.error=='wallet_changed'){TLB.loadWallet(true);if(ownsDraft105&&TLB.reload)TLB.reload().then(render);}")
s=once(s,'if(completedTip)tipComplete02(key,false);','if(completedTip){tipComplete02(key,false);S.priceConsent01=null;S.priceReview01=null;}')
s=once(s,'function vPay(){const c=calc();',"function vPay(){const review01=priceReviewView01();if(review01)return review01;priceRememberDisplayed01();const c=calc();")
s=once(s,'<div class="pg d67-checkout">','<div class="pg d67-checkout">${priceDisplayLines01()}')
p.write_text(s)
p=out/'talabat-core.js';s=p.read_text()
s=once(s,"closureId:closed(d)?d.closure_id:null", "closureId:closed(d)?d.closure_id:null,priceReview:closed(d)&&d.reason==='price_changed'&&priceValid01(d.price_review)?priceCopy01(d.price_review):null")
p.write_text(contract+'\n'+s)
print('PRICE01 generated client: explicit price review, immutable sent evidence, original recovery first.')
