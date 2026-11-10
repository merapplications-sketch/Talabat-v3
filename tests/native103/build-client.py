"""Generate isolated functional candidate from pinned recovered source; never modifies original."""
from pathlib import Path
import hashlib,json,sys
root=Path(sys.argv[1]);out=Path(sys.argv[2]);out.mkdir(parents=True,exist_ok=True)
hashes=json.loads(Path('tests/native103/ui-source-hashes.json').read_text())
for p,digest in hashes.items():assert hashlib.sha256((root/p).read_bytes()).hexdigest()==digest,'candidate input drift: '+p
core=(root/'public/talabat-core.js').read_text();html=(root/'public/customer.html').read_text()
start=core.index('      return rpc(\'place_order\',');end=core.index('\n    },',start)
old=core[start:end];payload=old[old.index('{ p_store:'):old.index(' })')+2]
new="      return orderClient103().submit("+payload+",o.freshAttempt===true);"
core=core[:start]+new+core[end:]
anchor='    placeOrder: function (o) {'
core=core.replace(anchor,"    recoverOrder103: function(key){return orderClient103().recover(key);},\n    retryOrder103: function(key,approved){return orderClient103().retrySaved(key,approved);},\n"+anchor,1)
# Helper lies inside core closure so auth follows the current ME, not a stale captured identity.
pos=core.index('  function finCommand(')
core=core[:pos]+"  var client103; function orderClient103(){return client103||(client103=globalThis.TalabotOrder103({user:function(){return ME&&ME.id;},storage:localStorage,readOrder:function(id){return sb.from('orders').select('id').eq('id',id).eq('customer_id',ME.id).maybeSingle().then(function(r){if(r.error||!r.data||String(r.data.id)!==String(id))return false;return refresh('orders').then(function(){return true;});}).catch(function(){return false;});},rpc:function(n,p){return sb.rpc(n,p);}}));}\n"+core[pos:]
core=Path('tests/native103/client.js').read_text()+'\n'+core
start=html.index('async function place(){');end=html.index("let phErr=''",start);block=html[start:end]
block=block.replace('  if(S.busy)return;', '''  if(S.busy)return;
  if(S.okey&&TLB.recoverOrder103){
    S.busy=true;render();
    try{
      let recovered=await TLB.recoverOrder103(S.okey);
      if(recovered.status==='unresolved'&&recovered.reason==='not_visible'&&confirm(TLB.lang()==='ru'?'Результат пока не подтверждён. Повторить сохранённую попытку с тем же ключом?':'Result is not yet confirmed. Retry the saved attempt with the same key?'))recovered=await TLB.retryOrder103(S.okey,true);
      if(recovered.id&&['created','replayed','historical_recovered'].includes(recovered.status)){
        alert(TLB.lang()==='ru'?'Открыт сохранённый заказ. Текущая корзина сохранена.':'Opening the saved order. Your current cart is preserved.');go('track',{tid:recovered.id});
      }else alert(errMsg(recovered));
    }catch(e){alert(t('err_generic'));}finally{S.busy=false;if(S.v==='pay')render();}
    return;
  }''',1)
block=block.replace('S.busy=true;if(!S.okey)S.okey=newKey();render();','S.busy=true;render();')
block=block.replace('    const r=await TLB.placeOrder(', '    if(!S.okey)S.okey=newKey();render();\n    const r=await TLB.placeOrder(')
block=block.replace('key:S.okey});','key:S.okey,freshAttempt:true});')
block=block.replace('    if(r.error){',"    if(!r||!['created','replayed','historical_recovered'].includes(r.status)||!r.id){if(r&&r.recoveryKey)S.okey=r.recoveryKey;if(r&&!r.error)r.error='order_outcome_unknown';if(!r){alert(t('err_generic'));return;}\n    if(r.error){",1)
block=block.replace('alert(errMsg(r));return}\n    S.cart=',"alert(errMsg(r));return}}\n    if(r.keepCart){alert(TLB.lang()==='ru'?'Открыт сохранённый заказ. Корзина сохранена.':'Opening the saved order. Cart preserved.');go('track',{tid:r.id});return;}\n    S.cart=",1)
html=html[:start]+block+html[end:]
(out/'talabat-core.js').write_text(core);(out/'customer.html').write_text(html)
print(json.dumps({'source_verified':True,'output':str(out),'design_layout_css_changes':False}))
