"""Retained admission assertions at tip20; no changes to historical tests."""
import os
from pathlib import Path
assert os.environ.get('TIP01_ISOLATED')=='yes'
src=Path('tests/native106/admission.py').read_text()
needle="Path('tests/native103/setup.generated.sql').write_text(setup)"
assert src.count(needle)==1
src=src.replace(needle,"setup+=Path('tests/tip01/acceptance.sql').read_text()\n"+needle)
needle="try:exec(compile(s,"
assert src.count(needle)==1
injection="s=s.replace(\"p_wallet=>5)\",\"p_wallet=>5,p_tip=>20)\")\n"
injection+="s=s.replace(\"results.append({\",\"assert a.execute(\\\"select count(*) from orders where client_key like 'request98_%' and tip is distinct from 20\\\").fetchone()[0]==0\\n results.append({\")\n"
src=src.replace(needle,injection+needle).replace('native106-admission.json','tip01-admission.json')
exec(compile(src,'retained_admission_at_tip20','exec'),{'__name__':'__main__'})
