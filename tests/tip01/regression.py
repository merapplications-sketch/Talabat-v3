"""Run retained103/104/105/106 assertions on TIP-01, without editing historical tests."""
import os, json, unittest
from pathlib import Path
assert os.environ.get('TIP01_ISOLATED')=='yes'
assert os.environ.get('PGHOST')=='127.0.0.1'
patch=Path('tests/tip01/acceptance.sql').read_text()
source=Path('tests/native104/native.py').read_text().split('# Prove S01')[0]
needle="namespace['MIGRATION']+=overlay"
extra="overlay+=Path('tests/native105/resources.sql').read_text()+\"insert into security_private.closure_policy105 values(true,10000,1000,1000) on conflict do nothing;\"\n"
extra+="overlay+=Path('tests/native106/isolation.sql').read_text()+Path('tests/tip01/acceptance.sql').read_text()\n"
assert source.count(needle)==1
retained={'__name__':'retained_tip01'}
exec(compile(source.replace(needle,extra+needle),'retained103_104_on_tip01','exec'),retained)
suite=unittest.TestSuite([unittest.defaultTestLoader.loadTestsFromTestCase(retained['BASE']),*(retained['New104'](n) for n in retained['New104'].__dict__ if n.startswith('test_'))])
isolation={'__name__':'isolation_tip01'}
exec(compile(Path('tests/native106/native.py').read_text(),'retained106','exec'),isolation)
isolation['PATCH']+=patch
suite.addTests(isolation['Isolation106'](n) for n in isolation['Isolation106'].__dict__ if n.startswith('test_'))
resources=isolation['ns']
resources['PATCH']+=Path('tests/native106/isolation.sql').read_text()+patch
# Preserve the already-accepted106 replacement of the old105 RR contract.
# Same exclusion as tests/native106/resources.py;106 no-effect matrix runs above.
superseded='test_repeatable_read_cannot_over_admit_stale_snapshot'
suite.addTests(resources['Resources105'](n) for n in resources['Resources105'].__dict__ if n.startswith('test_') and n!=superseded)
result=unittest.TextTestRunner(verbosity=2).run(suite)
Path('tip01-regression.json').write_text(json.dumps({'passed':result.wasSuccessful(),'tests':result.testsRun,'failures':[t.id() for t,_ in result.failures+result.errors],'scope':'retained assertions; PostgreSQL17.6; partial synthetic fixture; no hosted HTTP'},indent=2))
raise SystemExit(not result.wasSuccessful())
