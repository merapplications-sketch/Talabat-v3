from pathlib import Path
import sys,subprocess
root,out=Path(sys.argv[1]),Path(sys.argv[2])
subprocess.run([sys.executable,'tests/native103/build-client.py',str(root),str(out)],check=True)
core=(out/'talabat-core.js').read_text();old=Path('tests/native103/client.js').read_text();assert core.startswith(old);core=Path('tests/native104/client.js').read_text()+core[len(old):]
core=core.replace('globalThis.TalabotOrder103({','globalThis.TalabotOrder104({',1)
core=core.replace('storage:localStorage,readOrder:',"store:globalThis.TalabotAttemptStore104(globalThis.indexedDB),uuid:function(){return crypto.randomUUID();},readOrder:",1)
core=core.replace('o.freshAttempt===true);','o.freshAttempt===true,{cartToken:o.cartToken});',1)
needle='    recoverOrder103: function(key)'
assert needle in core;core=core.replace(needle,"    endRejected104: function(key,approved){return orderClient103().endRejected(key,approved);},\n"+needle,1)
(out/'talabat-core.js').write_text(core)
html=(out/'customer.html').read_text();start=html.index('async function place(){');end=html.index("let phErr=''",start);block=html[start:end]
# Snapshot is separate from frozen RPC payload; compare live cart and context again at completion.
helper="""function cartToken104(){return JSON.stringify([S.cart,S.cartAt,S.cartStore,S.tip,S.pay,S.note,S.promo,S.pcode,S.gift,S.door,S.subst,S.usePts,S.useWallet,S.at,S.addrId,S.tmp,S.useTmp,S.gCheckout,S.gNotes]);}
function cartForeign104(){try{if(S.cart104Watch&&localStorage.getItem(CK())!==S.cart104Disk)S.cart104Foreign=true;}catch(e){S.cart104Foreign=true;}return S.cart104Foreign===true;}
"""
block=block.replace('  if(S.busy)return;',"  if(S.busy)return;\n  if(cartForeign104()){alert(TLB.lang()==='ru'?'Корзина изменена в другой вкладке. Обновите страницу.':'Cart changed in another tab. Reload before continuing.');return;}",1)
needle="      if(recovered.id&&['created','replayed','historical_recovered'].includes(recovered.status)){"
insert="""      if(recovered.status==='rejected'&&recovered.closed===true&&TLB.endRejected104){
        if(confirm(TLB.lang()==='ru'?'Заказ не создан. Завершить отклонённую попытку, чтобы исправить данные?':'No order was created. End this rejected attempt so you can correct the details?')){
          const ended=await TLB.endRejected104(S.okey,true);
          if(ended.closed&&ended.status==='ended_rejected'){S.okey=null;render();alert(TLB.lang()==='ru'?'Корзина сохранена. Исправьте данные и подтвердите новый заказ.':'Cart preserved. Correct the details and confirm a new order.');return;}
          alert(errMsg(ended));return;
        }
      }
"""
assert needle in block;block=block.replace(needle,insert+needle)
block=block.replace('    const r=await TLB.placeOrder(',"    const sentCart104=cartToken104();S.cart104Watch=true;try{S.cart104Disk=localStorage.getItem(CK());}catch(e){S.cart104Foreign=true;}\n    const r=await TLB.placeOrder(",1)
block=block.replace('freshAttempt:true});','freshAttempt:true,cartToken:sentCart104});',1)
block=block.replace('    if(r.keepCart){',"    if(cartToken104()!==sentCart104||cartForeign104())r.keepCart=true;\n    if(r.keepCart){",1)
html=html[:start]+helper+block+html[end:]
# Guard legacy cart mirror from stale tab overwrites while a watched attempt is unresolved/completing.
html=html.replace('function cartSave(){','function cartSave(){if(cartForeign104())return;try{cartSave104Original();}finally{try{S.cart104Disk=localStorage.getItem(CK());}catch(e){S.cart104Foreign=true;}}}\nfunction cartSave104Original(){',1)
(out/'customer.html').write_text(html)
print('104 functional overlay generated; no CSS/layout modification')
