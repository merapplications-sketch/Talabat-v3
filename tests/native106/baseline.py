"""S03 proof on unmodified105 in disposable PostgreSQL17.6 only."""
import json
from pathlib import Path
ns={'__name__':'baseline106'}
exec(compile(Path('tests/native105/native.py').read_text(),'native105-fixture','exec'),ns)
b=ns['Resources105']('test_account_cap_and_same_key_ack_replay');b.setUp()
try:
 b.upgrade();b.policy();a=b.actor();a.rollback();a.execute('set transaction isolation level repeatable read');a.execute("select set_config('request.jwt.claims',%s,false)",(json.dumps({'sub':ns['B']}),));a.execute('set role authenticated');a.execute('select pg_current_snapshot()')
 key='s03baseline106';closure=b.reject(key);assert closure['closed'] is True
 r=ns['call'](a,ns['args'](key),'place_order104');assert r['status']=='created';a.commit();a.close()
 assert b.rows()==1;assert b.counts()==(1,1,-5,1)
 report={'baseline':'unmodified105','version':b.a.execute('show server_version').fetchone()[0],'isolation':'repeatable read','closure_committed_before_create':True,'response':r['status'],'closure_rows':b.rows(),'orders_spends_amount_bindings':[int(x) for x in b.counts()],'S03_reproduced':True}
 Path('native106-baseline.json').write_text(json.dumps(report,indent=2));print(json.dumps(report))
finally:b.tearDown()
