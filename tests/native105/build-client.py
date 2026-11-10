from pathlib import Path
import sys,subprocess
root,out=Path(sys.argv[1]),Path(sys.argv[2])
subprocess.run([sys.executable,'tests/native104/build-client.py',str(root),str(out)],check=True)
p=out/'customer.html';html=p.read_text()
helper=r'''
// Versions catch edit-away/edit-back (ABA), including nested object edits.
function ensureDraft105(){
 if(S.draftWatch105)return;
 const fields=new Set(['cart','cartAt','cartStore','tip','pay','note','promo','perr','pcode','pm','gift','door','subst','usePts','useWallet','at','addrId','tmp','useTmp','quote','quoteErr','gCheckout','gNotes','gKeep','gid','grp','group']);
 let revision=0;const cache=new WeakMap();
 function nested(x){if(!x||typeof x!=='object')return x;if(cache.has(x))return cache.get(x);const p=new Proxy(x,{get(t,k){return nested(t[k]);},set(t,k,v){revision++;t[k]=v;return true;},deleteProperty(t,k){revision++;delete t[k];return true;}});cache.set(x,p);cache.set(p,p);return p;}
 const target=S;target.draftWatch105=true;S=new Proxy(target,{get(t,k){if(k==='draftRevision105')return revision;return fields.has(k)?nested(t[k]):t[k];},set(t,k,v){if(fields.has(k))revision++;t[k]=v;return true;},deleteProperty(t,k){if(fields.has(k))revision++;delete t[k];return true;}});
}
function draftResponse105(key,seq){return S.okey===key&&S.checkoutSeq105===seq;}
function retireDraft105(key,seq){if(!draftResponse105(key,seq))return false;S.okey=null;cartSave();return true;}
'''
# Keep all prior helpers and templates. No visual changes.
html=html.replace('async function place(){',helper+'\nasync function place(){\n  ensureDraft105();',1)
html=html.replace('  if(S.okey&&TLB.recoverOrder103){','  const seq105=S.checkoutSeq105=(S.checkoutSeq105||0)+1;\n  if(S.okey&&TLB.recoverOrder103){\n    const recoverKey105=S.okey;',1)
html=html.replace('TLB.recoverOrder103(S.okey)','TLB.recoverOrder103(recoverKey105)',1).replace('TLB.retryOrder103(S.okey,true)','TLB.retryOrder103(recoverKey105,true)',1).replace('TLB.endRejected104(S.okey,true)','TLB.endRejected104(recoverKey105,true)',1)
html=html.replace("if(ended.closed&&ended.status==='ended_rejected'){S.okey=null;", "if(ended.closed&&ended.status==='ended_rejected'&&retireDraft105(recoverKey105,seq105)){",1)
needle="      if(recovered.id&&['created','replayed','historical_recovered'].includes(recovered.status)){"
html=html.replace(needle,needle+'\n        if(!retireDraft105(recoverKey105,seq105))return;',1)
html=html.replace('    const r=await TLB.placeOrder(', '    const sentKey105=S.okey,sentRevision105=S.draftRevision105;\n    const r=await TLB.placeOrder(',1)
# A reply cannot mutate a newer attempt. Preserve error behavior only for its unedited draft.
needle="    if(!r||!['created','replayed','historical_recovered'].includes(r.status)||!r.id)"
html=html.replace(needle,"    if(!draftResponse105(sentKey105,seq105))return;\n    const ownsDraft105=S.draftRevision105===sentRevision105&&!cartForeign104();\n"+needle,1)
for old,new in [
 ("if(r.error=='fee_changed'||r.error=='too_far'){","if(ownsDraft105&&(r.error=='fee_changed'||r.error=='too_far')){"),
 ("if(/^promo_|too_many$/.test(r.error)){","if(ownsDraft105&&/^promo_|too_many$/.test(r.error)){"),
 ("if(r.error=='bad_time')S.at=null;","if(ownsDraft105&&r.error=='bad_time')S.at=null;"),
 ("if(r.error=='bad_group'){","if(ownsDraft105&&r.error=='bad_group'){"),
 ("if(r.error=='unavailable'||r.error=='bad_options'){","if(ownsDraft105&&(r.error=='unavailable'||r.error=='bad_options')){")]:
 assert old in html;html=html.replace(old,new,1)
html=html.replace('    if(cartToken104()!==sentCart104||cartForeign104())r.keepCart=true;', '    if(!ownsDraft105||cartToken104()!==sentCart104||cartForeign104())r.keepCart=true;\n    if(!retireDraft105(sentKey105,seq105))return;',1)
p.write_text(html)
print('105 client: completed key detached; version-owned draft mutations; unchanged layout')
