import unittest,json
from pathlib import Path
ns={'__name__':'retained105'}
exec(compile(Path('tests/native105/native.py').read_text(),'native105-retained','exec'),ns)
ns['PATCH']+=Path('tests/native106/isolation.sql').read_text()
# This prior quota-epoch test assumes RR closure creation is supported.106 instead rejects
# all creation endpoints under RR BEFORE quota admission. The stronger no-effect matrix
# in native.py explicitly replaces that contract-specific expectation; do not edit105.
excluded='test_repeatable_read_cannot_over_admit_stale_snapshot'
C=ns['Resources105'];names=[n for n in C.__dict__ if n.startswith('test_') and n!=excluded]
r=unittest.TextTestRunner(verbosity=2).run(unittest.TestSuite(C(n) for n in names))
Path('native106-resources.json').write_text(json.dumps({'tests':r.testsRun,'passed':r.wasSuccessful(),'retained_cases':names,'superseded':excluded,'replacement':'native106 test_s03_all_entries_all_isolation_levels + unsupported atomic no-effects'},indent=2));raise SystemExit(not r.wasSuccessful())
