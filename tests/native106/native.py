"""Closed-key isolation contract; independent PostgreSQL connections, synthetic fixture."""
import json,unittest,threading,time
from pathlib import Path
ns={'__name__':'fixture106'}
exec(compile(Path('tests/native105/native.py').read_text(),'native105-fixture','exec'),ns)
Base=ns['Resources105'];call=ns['call'];args=ns['args'];psycopg=ns['ns']['psycopg'];B=ns['B'];O=ns['O']
ENTRIES=['place_order','place_order103','place_order104','security_private.create_order103']
LEVELS=['read committed','read uncommitted','repeatable read','serializable']
PATCH=Path('tests/native106/isolation.sql').read_text()
class Isolation106(Base):
 def upgrade(self):super().upgrade();self.a.execute(PATCH)
 def tx(self,level='read committed',private=False):
  c=psycopg.connect(dbname='candidate103',sslmode='disable');c.execute('set transaction isolation level '+level);c.execute("set statement_timeout='10s'");c.execute("select set_config('request.jwt.claims',%s,false)",(json.dumps({'sub':B}),));
  if not private:c.execute('set role authenticated')
  c.execute('select pg_current_snapshot()');return c
 def outcome(self,c,p,fn):
  try:
   r=call(c,p,fn);c.commit();return r
  except psycopg.Error as e:
   state=e.sqlstate;message=e.diag.message_primary;c.rollback();return {'sqlstate':state,'message':message}
 def assert_no_creation(self,r,level,fn):
  if level in ['repeatable read','serializable']:
   if fn=='place_order':self.assertEqual(r,{'sqlstate':'P0001','message':'order_outcome_unknown'})
   else:self.assertEqual(r['status'],'unresolved');self.assertEqual(r['reason'],'unsupported_transaction_isolation');self.assertNotIn('closed',r);self.assertNotIn('id',r)
  else:
   if fn=='place_order104':self.assertEqual(r['status'],'rejected');self.assertTrue(r['closed'])
   elif fn=='place_order103':self.assertEqual(r['status'],'rejected')
   else:self.assertEqual(r['sqlstate'],'P0001')
 def test_s03_all_entries_all_isolation_levels(self):
  self.upgrade();self.policy(100,100)
  for level in LEVELS:
   for i,fn in enumerate(ENTRIES):
    with self.subTest(level=level,entry=fn):
     key='s03_'+level.replace(' ','_')+'_'+str(i);c=self.tx(level,fn.startswith('security_private.'));receipt=self.reject(key);self.assertTrue(receipt['closed']);before=self.snapshot();n=self.rows();r=self.outcome(c,args(key),fn);c.close();self.assert_no_creation(r,level,fn);self.assertEqual(before,self.snapshot());self.assertEqual(self.rows(),n);self.assertEqual(self.counts(),(0,0,0,0))
 def test_supported_isolations_create_once_then_recover(self):
  self.upgrade();self.policy(100,100)
  for level in LEVELS[:2]:
   for i,fn in enumerate(ENTRIES):
    key='supported106_'+level.replace(' ','_')+str(i);p=args(key);c=self.tx(level,fn.startswith('security_private.'));r=self.outcome(c,p,fn);c.close();oid=r if fn=='place_order' else r['id'];self.assertIsNotNone(oid);before=self.snapshot();c=self.tx(level,fn.startswith('security_private.'));again=self.outcome(c,p,fn);c.close();self.assertEqual(str(again if fn=='place_order' else again['id']),str(oid));self.assertEqual(self.snapshot(),before);self.consent();self.a.execute("update orders set status='delivered' where client_key=%s",(key,))
  self.assertEqual(self.counts(),(8,8,-40,8));self.assertEqual(self.rows(),0)
 def test_unsupported_isolation_rejects_new_and_invalid_before_any_effect(self):
  self.upgrade();self.policy();before=self.snapshot()
  for level in LEVELS[2:]:
   for fn in ENTRIES:
    for address in ['synthetic address','']:
     p=args('unsupported106_key');p[4]=address;c=self.tx(level,fn.startswith('security_private.'));r=self.outcome(c,p,fn);c.close();self.assert_no_creation(r,level,fn);self.assertEqual(self.snapshot(),before);self.assertEqual(self.rows(),0)
 def test_committed_closure_and_fresh_transaction_cannot_reopen(self):
  self.upgrade();self.policy();key='closed106_prior';receipt=self.reject(key)
  for fn in ENTRIES:
   c=self.tx(private=fn.startswith('security_private.'));r=self.outcome(c,args(key),fn);c.close();self.assert_no_creation(r,'read committed',fn)
  self.assertEqual(self.counts(),(0,0,0,0));self.assertEqual(self.rows(),1)
  with self.actor() as c:self.assertEqual(c.execute('select order_request_status104(%s)',(key,)).fetchone()[0]['closure_id'],receipt['closure_id'])
 def test_success_wins_race_no_false_closure(self):
  self.upgrade();self.policy(100,100)
  for i,fn in enumerate(ENTRIES):
   key='successrace106_'+str(i);a=self.tx(private=fn.startswith('security_private.'));created=call(a,args(key),fn);other=self.actor();out={};p=args(key);p[4]=''
   def close():
    try:out['r']=call(other,p,'place_order104');other.commit()
    except Exception as e:out['error']=str(e);other.rollback()
   t=threading.Thread(target=close);t.start();blocked=False
   for _ in range(200):
    blocked=a.info.backend_pid in self.a.execute('select pg_blocking_pids(%s)',(other.info.backend_pid,)).fetchone()[0]
    if blocked:break
    time.sleep(.01)
   self.assertTrue(blocked);a.commit();a.close();t.join(10);self.assertFalse(t.is_alive());other.close();self.assertNotIn('error',out);self.assertIn(out['r']['status'],['conflict','replayed']);self.assertNotIn('closed',out['r']);self.assertEqual(self.rows(),0);self.consent()
  self.assertEqual(self.counts(),(4,4,-20,4))
 def test_closure_wins_waiting_create_no_spend(self):
  self.upgrade();self.policy(100,100)
  for i,fn in enumerate(ENTRIES):
   key='closerace106_'+str(i);a=self.actor();p=args(key);p[4]='';receipt=call(a,p,'place_order104');self.assertTrue(receipt['closed']);b=self.tx(private=fn.startswith('security_private.'));out={}
   t=threading.Thread(target=lambda:out.update(r=self.outcome(b,args(key),fn)));t.start();blocked=False
   for _ in range(200):
    blocked=a.info.backend_pid in self.a.execute('select pg_blocking_pids(%s)',(b.info.backend_pid,)).fetchone()[0]
    if blocked:break
    time.sleep(.01)
   self.assertTrue(blocked);a.commit();a.close();t.join(10);self.assertFalse(t.is_alive());b.close();self.assert_no_creation(out['r'],'read committed',fn)
  self.assertEqual(self.counts(),(0,0,0,0));self.assertEqual(self.rows(),4)
 def test_unsupported_then_explicit_fresh_rc_recovery_original_key(self):
  self.upgrade();self.policy();key='recovery106_same';receipt=self.reject(key);c=self.tx('repeatable read');r=self.outcome(c,args(key),'place_order104');c.close();self.assert_no_creation(r,'repeatable read','place_order104')
  with self.actor() as c:r=c.execute('select order_request_status104(%s)',(key,)).fetchone()[0];self.assertEqual(r['closure_id'],receipt['closure_id'])
  self.assertEqual(self.counts(),(0,0,0,0));self.assertEqual(self.rows(),1)
 def test_rollback_and_atomic_reupgrade_preserve_fence(self):
  self.upgrade();self.policy();receipt=self.reject('rollback106_key');self.a.execute(Path('tests/native104/rollback.sql').read_text());before=self.snapshot()
  for level in LEVELS:
   for fn in ENTRIES:
    c=self.tx(level,fn.startswith('security_private.'));r=self.outcome(c,args('rollback106_key'),fn);c.close();self.assertFalse(isinstance(r,int));self.assertNotIn('id',r);self.assertEqual(before,self.snapshot())
  self.upgrade();self.assertEqual(self.reject('rollback106_key')['closure_id'],receipt['closure_id']);self.assertEqual(self.counts(),(0,0,0,0))
 def test_catalog_and_grants_no_unlisted_candidate_creator(self):
  self.upgrade();catalog=self.a.execute("select n.nspname,p.proname,pg_get_function_identity_arguments(p.oid),has_function_privilege('authenticated',p.oid,'execute'),has_function_privilege('anon',p.oid,'execute') from pg_proc p join pg_namespace n on n.oid=p.pronamespace where n.nspname in ('public','security_private') and (p.proname like 'place_order%' or p.proname like 'create_order%') order by 1,2").fetchall()
  self.assertEqual([n+'.'+p for n,p,*_ in catalog],['public.place_order','public.place_order103','public.place_order104','security_private.create_order103']);self.assertTrue(all(not row[4] for row in catalog));self.assertTrue(all(row[3] for row in catalog[:3]));self.assertFalse(catalog[-1][3]);self.assertFalse(self.a.execute("select has_table_privilege('authenticated','public.orders','insert')").fetchone()[0]);Path('native106-catalog.json').write_text(json.dumps(catalog,indent=2))
 def test_real_40001_fault_after_creation_rolls_back_all_effects(self):
  self.upgrade();self.policy(100,100)
  for i,fn in enumerate(ENTRIES):
   key='fault40001_106_'+str(i);before=self.snapshot();c=self.tx(private=fn.startswith('security_private.'));r=call(c,args(key),fn);self.assertTrue(isinstance(r,int) or r.get('status')=='created')
   # Explicit synthetic failure on real PostgreSQL after order/wallet/binding writes.
   with self.assertRaises(psycopg.errors.SerializationFailure):c.execute("do $$begin raise serialization_failure;end$$")
   c.rollback();c.close();self.assertEqual(before,self.snapshot());self.assertEqual(self.rows(),0)
   with self.actor() as check:self.assertEqual(check.execute('select order_request_status104(%s)',(key,)).fetchone()[0]['status'],'unresolved')
   with self.actor() as retry:self.assertEqual(call(retry,args(key),'place_order104')['status'],'created')
   self.assertEqual(self.a.execute("select count(*),sum(amount) from wallet_entries where kind='spend' and order_id in(select id from orders where client_key=%s)",(key,)).fetchone(),(1,-5));self.consent()
if __name__=='__main__':
 suite=unittest.TestSuite(Isolation106(n) for n in Isolation106.__dict__ if n.startswith('test_'));r=unittest.TextTestRunner(verbosity=2).run(suite);Path('native106-results.json').write_text(json.dumps({'passed':r.wasSuccessful(),'tests':r.testsRun,'entries':ENTRIES,'isolation_levels':LEVELS,'failures':[t.id() for t,_ in r.failures+r.errors]},indent=2));raise SystemExit(not r.wasSuccessful())
