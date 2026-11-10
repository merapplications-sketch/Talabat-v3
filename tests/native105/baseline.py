"""Observe bounded sample growth on unchanged104; no candidate SQL loaded."""
import os,json
from pathlib import Path
ns={'__name__':'baseline105'}
exec(compile(Path('tests/native104/native.py').read_text().split('# Prove S01')[0],'native104-baseline','exec'),ns)
b=ns['BASE']('test_invalid_inputs_and_unknown_status');b.setUp()
try:
 b.upgrade();rows=[]
 for i in range(12):
  p=ns['args']('growth105_'+str(i));p[4]=''
  with b.actor() as c:r=ns['call'](c,p,'place_order104');assert r['closed'] and r['no_effects']
  rows.append(b.a.execute('select count(*) from security_private.order_attempt_closures104').fetchone()[0])
 assert rows==list(range(1,13));assert b.counts()==(0,0,0,0)
 result={'baseline':'unchanged104','sample':12,'closure_rows':rows,'orders_and_spends':list(b.counts()),'observation':'every fresh rejected key adds a durable row; no closure admission cap in104; sample is not a production limit'}
 Path('native105-baseline.json').write_text(json.dumps(result,indent=2));print(json.dumps(result))
finally:b.tearDown()
