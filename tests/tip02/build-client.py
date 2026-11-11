"""Generate isolated TIP-02 on the pinned105 functional client; no historical edits."""
from pathlib import Path
import sys,subprocess
root,out=map(Path,sys.argv[1:3]);subprocess.run([sys.executable,'tests/native105/build-client.py',str(root),str(out)],check=True)
def once(s,old,new):
 assert s.count(old)==1,('source drift',old,s.count(old));return s.replace(old,new,1)
contract=Path('tests/tip02/contract.js').read_text();ui=Path('tests/tip02/ui.js').read_text()
p=out/'customer.html';s=p.read_text()
s=once(s,'function ensureDraft105(){',contract+'\n'+ui+'\nfunction ensureDraft105(){')
s=once(s,"'cart','cartAt','cartStore','tip','pay'","'cart','cartAt','cartStore','tip','tipMode02','tipRaw02','tipSentKey02','pay'")
s=once(s,'tip:S.tip,pay:S.pay,key:S.okey','tip:S.tip,tipMode02:S.tipMode02,tipRaw02:S.tipRaw02,tipSentKey02:S.tipSentKey02,pay:S.pay,key:S.okey')
s=once(s,'S.tip=[0,5,10,20].includes(+d.tip)?+d.tip:0;','tipRestore02(d);')
old='<div class="card"><h3>${t(\'tip\')}</h3><div class="tipr">${[0,5,10,20].map(v=>`<div class="tip ${S.tip==v?\'on\':\'\'}" onclick="S.tip=${v};render()">${v?v+\' TJS\':t(\'none\')}</div>`).join(\'\')}</div></div>'
s=once(s,old,'${tipPanel02()}')
# Recovery branch deliberately precedes new-input validation.
s=once(s,"  if(!ME.phone){alert(t('needPh'));", "  const tip02=tipGet02();if(!tip02.ok){alert(tipText02('error'));return;}\n  if(!ME.phone){alert(t('needPh'));")
s=once(s,'    if(!S.okey)S.okey=newKey();render();',"    if(!tipGet02().ok){alert(tipText02('error'));return;}\n    if(!S.okey)S.okey=newKey();render();")
s=once(s,'    const sentCart104=cartToken104();','    S.tipSentKey02=S.okey;cartSave();\n    const sentCart104=cartToken104();')
# Complete the owned tip and detach the completed key in ONE draft write.
# Rejected attempts use the unchanged two-argument path; no tip was consumed.
s=once(s,'function retireDraft105(key,seq){if(!draftResponse105(key,seq))return false;S.okey=null;cartSave();return true;}',
 'function retireDraft105(key,seq,completedTip=false){if(!draftResponse105(key,seq))return false;if(completedTip)tipComplete02(key,false);S.okey=null;cartSave();return true;}')
s=once(s,'        if(!retireDraft105(recoverKey105,seq105))return;','        if(!retireDraft105(recoverKey105,seq105,true))return;')
s=once(s,'    if(!retireDraft105(sentKey105,seq105))return;','    if(!retireDraft105(sentKey105,seq105,true))return;')
# Emptying a draft must not silently carry a tip into a later cart. Attempts live separately.
s=once(s,"if(!cartCount()){S.promo=null;", "if(!cartCount()){S.tip=0;S.tipMode02='quick';S.tipRaw02='';S.tipSentKey02=null;S.promo=null;")
p.write_text(s)
p=out/'talabat-core.js';s=p.read_text()
s=once(s,'p_tip: o.tip || 0,',"p_tip: Object.prototype.hasOwnProperty.call(o,'tip') ? o.tip : 0,")
# Preserve old/pending attempts before considering NEW invalid non-null input.
needle='    let a=s.attempts[key];'
s=once(s,needle,needle+"\n    if(!a&&fresh===true&&payload.p_tip!==null&&!tipNumber02(payload.p_tip===undefined?0:payload.p_tip).ok)return{stop:{status:'rejected',error:'bad_value',keepCart:true,closed:false}};")
p.write_text(contract+'\n'+s)
print('TIP-02: manual1..100, default0, explicit NULL forwarded unchanged; new-attempt validation after active-owner check')
