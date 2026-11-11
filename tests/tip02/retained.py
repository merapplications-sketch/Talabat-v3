"""TIP01 tests affected by creator replacement, plus manual-value ACK/concurrency."""
import os,json,unittest
from pathlib import Path
assert os.environ.get('TIP02_ISOLATED')=='yes'
ns={'__name__':'tip02_cases'}
exec(compile(Path('tests/tip02/native.py').read_text(),'tip02_cases','exec'),ns)
C=ns['ManualTip'];B=ns['Base']
names=['test_tip20_persisted_all_entries','test_replay_conflict_and_numeric_equivalence','test_preupgrade_bound_orders_never_repriced','test_historical_tip3_and_sent20_stored0_readonly','test_tip20_closed_key_all_entries_all_isolations','test_decimal_money_and_floor_unchanged','test_tip20_rollback_reupgrade_no_repricing','test_tip20_binding_failure_promo_points_wallet_atomic']
# Accepted original assertions are retained; only the two transport/concurrency payloads use99.
base_ns=B.test_three_concurrent_retries_one_spend.__globals__
original=base_ns['tipargs']
def manual_args(*a,**kw):
 p=original(*a,**kw);p[2]=99;return p
class ManualTransport(C):
 def test_manual99_three_connections(self):
  base_ns['tipargs']=manual_args
  try:B.test_three_concurrent_retries_one_spend(self)
  finally:base_ns['tipargs']=original
# Native source was exec-compiled: select its method text explicitly, preserving all assertions.
source=Path('tests/tip01/native.py').read_text();start=source.index(' def test_tip20_tcp_before_after_commit');end=source.index('\n def ',start+2)
method=source[start:end].replace('test_tip20_tcp_before_after_commit','test_manual99_tcp').replace('(20,42)','(99,121)')
base_ns['tipargs']=manual_args
scope=dict(base_ns,C=C);exec('class ManualTCP(C):\n'+method,scope)
base_ns['tipargs']=original
scope['tipargs']=manual_args
suite=unittest.TestSuite([*(C(n) for n in names),ManualTransport('test_manual99_three_connections'),scope['ManualTCP']('test_manual99_tcp')])
r=unittest.TextTestRunner(verbosity=2).run(suite)
Path('tip02-retained.json').write_text(json.dumps({'tests':r.testsRun,'passed':r.wasSuccessful(),'failures':[t.id() for t,_ in r.failures+r.errors],'tip01_compatibility_test_superseded':'only the unapproved invalid-value creation policy is replaced by the explicit TIP02 owner decision'},indent=2));raise SystemExit(not r.wasSuccessful())
