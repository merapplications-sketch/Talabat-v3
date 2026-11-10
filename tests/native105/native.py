"""New resource assertions. Production quotas are intentionally not populated."""
import os,json,unittest,threading,time
from pathlib import Path
ns={'__name__':'native105'}
exec(compile(Path('tests/native104/native.py').read_text().split('# Prove S01')[0],'retained104','exec'),ns)
B=ns['B'];O=ns['O'];call=ns['call'];args=ns['args'];BASE=ns['BASE']
PATCH=Path('tests/native105/resources.sql').read_text()
class Resources105(BASE):
 def upgrade(self):super().upgrade();self.a.execute(PATCH)
 def policy(self,global_n=4,account_n=2,reason_n=128):
  # Deliberately tiny synthetic test values, NOT production recommendations/defaults.
  self.a.execute('insert into security_private.closure_policy105(singleton,max_rows,max_account_rows,max_reason_bytes) values(true,%s,%s,%s) on conflict(singleton) do update set max_rows=excluded.max_rows,max_account_rows=excluded.max_account_rows,max_reason_bytes=excluded.max_reason_bytes',(global_n,account_n,reason_n))
 def reject(self,key,uid=B):
  p=args(key);p[4]=''
  with self.actor(uid) as c:return call(c,p,'place_order104')
 def rows(self):return self.a.execute('select count(*) from security_private.order_attempt_closures104').fetchone()[0]
 def test_unconfigured_never_claims_terminal_rejection(self):
  self.upgrade();r=self.reject('unconfigured105');self.assertEqual(r['status'],'unresolved');self.assertEqual(r['reason'],'closure_resource_unavailable');self.assertNotIn('closed',r);self.assertEqual(self.rows(),0);self.assertEqual(self.counts(),(0,0,0,0))
 def test_account_cap_and_same_key_ack_replay(self):
  self.upgrade();self.policy();r=self.reject('capacity105_a');self.reject('capacity105_b');excess=self.reject('capacity105_c');self.assertEqual(excess['status'],'unresolved');self.assertNotIn('closed',excess);self.assertEqual(self.rows(),2)
  self.assertEqual(self.reject('capacity105_a')['closure_id'],r['closure_id']);self.assertEqual(self.counts(),(0,0,0,0))
  with self.actor() as c:self.assertEqual(c.execute('select order_request_status104(%s)',('capacity105_a',)).fetchone()[0]['closure_id'],r['closure_id'])
  # A corrected payload cannot reopen a closed key, even at full capacity.
  with self.actor() as c:self.assertEqual(call(c,args('capacity105_a'),'place_order104')['closure_id'],r['closure_id'])
 def test_global_cap_across_accounts_concurrent(self):
  self.upgrade();self.policy(1,1);out=[];bar=threading.Barrier(3)
  def run(uid,key):bar.wait();out.append(self.reject(key,uid))
  ts=[threading.Thread(target=run,args=(uid,'global105_'+str(i))) for i,uid in enumerate([B,O])]
  for t in ts:t.start()
  bar.wait()
  for t in ts:t.join(10);self.assertFalse(t.is_alive())
  self.assertEqual(sorted(r['status'] for r in out),['rejected','unresolved']);self.assertEqual(self.rows(),1);self.assertEqual(self.counts(),(0,0,0,0))
 def test_same_account_distinct_keys_concurrent(self):
  self.upgrade();self.policy(2,1);out=[];bar=threading.Barrier(4)
  def run(i):bar.wait();out.append(self.reject('parallel105_'+str(i)))
  ts=[threading.Thread(target=run,args=(i,)) for i in range(3)]
  for t in ts:t.start()
  bar.wait()
  for t in ts:t.join(10);self.assertFalse(t.is_alive())
  self.assertEqual(sum(r['status']=='rejected' for r in out),1);self.assertEqual(self.rows(),1)
 def test_resource_retry_original_payload_and_success_replay(self):
  self.upgrade();self.policy(1,1);self.reject('filled105_key');r=self.reject('retry105_frozen');self.assertEqual(r['status'],'unresolved');self.policy(2,2);self.assertTrue(self.reject('retry105_frozen')['closed']);self.assertEqual(self.rows(),2)
  # Existing successful operation stays recoverable with no quota capacity.
  with self.actor() as c:r=call(c,args('success105_ack'),'place_order104');self.assertEqual(r['status'],'created')
  with self.actor() as c:self.assertEqual(call(c,args('success105_ack'),'place_order104')['id'],r['id'])
  self.assertEqual(self.counts(),(1,1,-5,1))
 def test_long_reason_does_not_write_or_claim_closure(self):
  self.upgrade();self.policy(4,4,1);r=self.reject('reason105_long');self.assertEqual(r['status'],'unresolved');self.assertEqual(self.rows(),0)
 def test_acl_and_no_delete_or_reopen(self):
  self.upgrade();self.policy();r=self.reject('immutable105_key')
  with self.assertRaises(Exception):self.a.execute('delete from security_private.order_attempt_closures104')
  with self.assertRaises(Exception):self.a.execute("update security_private.order_attempt_closures104 set client_key='changed105_key'")
  with self.assertRaises(Exception):self.a.execute('truncate security_private.order_attempt_closures104')
  for table in ['closure_policy105','order_attempt_closures104']:
   with self.actor() as c:
    with self.assertRaises(ns['psycopg'].errors.InsufficientPrivilege):c.execute('select * from security_private.'+table)
  self.assertEqual(self.reject('immutable105_key')['closure_id'],r['closure_id'])
 def test_rollback_and_reupgrade_preserve_fence_and_budget(self):
  self.upgrade();self.policy(1,1);r=self.reject('rollback105_key');self.a.execute(Path('tests/native104/rollback.sql').read_text());self.a.execute(PATCH)
  with self.actor() as c:self.assertEqual(c.execute('select order_request_status104(%s)',('rollback105_key',)).fetchone()[0]['closure_id'],r['closure_id'])
  self.a.execute(ns['namespace']['MIGRATION']);self.a.execute(PATCH);self.assertEqual(self.reject('rollback105_key')['closure_id'],r['closure_id']);self.assertEqual(self.reject('rollback105_new')['status'],'unresolved');self.assertEqual(self.rows(),1)
 def test_policy_lock_timeout_is_unresolved_without_closure(self):
  self.upgrade();self.policy();hold=ns['psycopg'].connect(dbname='candidate103');hold.execute('select * from security_private.closure_policy105 for update')
  p=args('policylock105');p[4]=''
  with self.actor() as c:c.execute("set lock_timeout='100ms'");r=call(c,p,'place_order104');self.assertEqual(r['status'],'unresolved');self.assertEqual(r['reason'],'55P03')
  hold.rollback();hold.close();self.assertEqual(self.rows(),0);self.assertTrue(self.reject('policylock105')['closed'])
 def test_closure_tcp_before_after_commit(self):
  self.upgrade();self.policy(4,4)
  for mode in ['before','after']:
   proxy=ns['namespace']['CutProxy'](mode);c=self.actor(port=proxy.port);p=args('closuretcp105_'+mode);p[4]='';r=call(c,p,'place_order104');self.assertTrue(r['closed']);proxy.arm=True
   with self.assertRaises((ns['psycopg'].OperationalError,ns['psycopg'].InterfaceError)):c.commit()
   c.close();proxy.join();self.assertTrue(proxy.cut)
   for _ in range(100):
    n=self.a.execute('select count(*) from security_private.order_attempt_closures104 where client_key=%s',(p[8],)).fetchone()[0]
    if n==(1 if mode=='after' else 0):break
    time.sleep(.01)
   self.assertEqual(n,1 if mode=='after' else 0);again=self.reject(p[8]);self.assertTrue(again['closed'])
   if mode=='after':self.assertEqual(again['closure_id'],r['closure_id'])
  self.assertEqual(self.rows(),2);self.assertEqual(self.counts(),(0,0,0,0))
 def test_repeatable_read_cannot_over_admit_stale_snapshot(self):
  self.upgrade();self.policy(1,1);c=self.actor(O);c.rollback();c.execute('set transaction isolation level repeatable read');c.execute("select set_config('request.jwt.claims',%s,false)",(json.dumps({'sub':O}),));c.execute('set role authenticated');c.execute('select count(*) from orders')
  self.reject('snapshot105_first');p=args('snapshot105_second');p[4]=''
  with self.assertRaises(ns['psycopg'].errors.SerializationFailure):call(c,p,'place_order104')
  c.rollback();c.close();self.assertEqual(self.rows(),1);self.assertEqual(self.counts(),(0,0,0,0))
if __name__=='__main__':
 suite=unittest.TestSuite(Resources105(n) for n in Resources105.__dict__ if n.startswith('test_'));r=unittest.TextTestRunner(verbosity=2).run(suite)
 Path('native105-resources.json').write_text(json.dumps({'tests':r.testsRun,'passed':r.wasSuccessful(),'failures':[t.id() for t,_ in r.failures+r.errors],'scope':'real isolated PostgreSQL synthetic schema and quota values'},indent=2));raise SystemExit(not r.wasSuccessful())
