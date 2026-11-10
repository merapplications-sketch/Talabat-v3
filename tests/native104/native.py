import os,sys,json,unittest,hashlib
from pathlib import Path
sys.path.insert(0,'tests/native103')
# Original19 assertions retained; wire104 overlay and rollback as the candidate under test.
namespace={'__name__':'regression104'}
source=Path('tests/native103/test_sql.py').read_text().replace("Path('tests/native103/rollback.sql')","Path('tests/native104/rollback.sql')")
exec(compile(source,'native103-assertions-on104','exec'),namespace)
BASE=namespace['SQL103'];call=namespace['call'];args=namespace['args'];B=namespace['B'];O=namespace['O'];psycopg=namespace['psycopg']
overlay=''.join(Path('tests/native104/'+n).read_text() for n in ['schema.sql','functions.sql','lifecycle.sql'])
namespace['MIGRATION']+=overlay
class New104(BASE):
 def test_float_context_rollback_reupgrade(self):
  self.upgrade();p=args('float104_context',{'unicode':'Таджикистан / طَلَب 😀','nested':{'b':1.00,'a':None}});p[5]=38.123456789012344;p[6]=68.12345678901234
  with self.actor() as c:c.execute('set extra_float_digits=0');r=call(c,p,'place_order104');self.assertEqual(r['status'],'created')
  for rollback in [False,True,False]:
   self.a.execute(Path('tests/native104/rollback.sql').read_text() if rollback else namespace['MIGRATION'])
   for digits in [-3,0,1,3]:
    with self.actor() as c:
     c.execute('set extra_float_digits='+str(digits));c.execute("set timezone='Asia/Dushanbe'");c.execute("set datestyle='SQL, DMY'");got=call(c,p,'place_order104');self.assertEqual(got['status'],'replayed');self.assertEqual(got['id'],r['id'])
  self.assertEqual(self.counts(),(1,1,-5,1))
 def test_existing103_fingerprint_preserved(self):
  original=''.join(Path('tests/native103/'+n).read_text() for n in ['schema.sql','functions.sql','migrate102.sql']);self.a.execute(original);self.a.execute('insert into security_private.order_request_keys103 values(1,%s,true)',(os.urandom(32),));p=args('existing103_key');p[5]=38.123456789012344
  with self.actor() as c:self.assertEqual(call(c,p)['status'],'created')
  before=self.snapshot();self.a.execute(overlay)
  for sql in ['',Path('tests/native104/rollback.sql').read_text()]:
   if sql:self.a.execute(sql)
   with self.actor() as c:c.execute('set extra_float_digits=0');self.assertEqual(call(c,p,'place_order104')['status'],'replayed')
  self.assertEqual(before,self.snapshot())
 def test_rejected_fence_and_correction(self):
  self.upgrade();p=args('rejected104_key');p[4]='';before=self.snapshot()
  with self.actor() as c:r=call(c,p,'place_order104');self.assertEqual(r['status'],'rejected');self.assertTrue(r['closed']);self.assertTrue(r['no_effects']);receipt=r['closure_id']
  self.assertEqual(before,self.snapshot())
  p[4]='corrected synthetic address'
  with self.actor() as c:r=call(c,p,'place_order104');self.assertEqual(r['closure_id'],receipt)
  with self.actor() as c:self.assertEqual(call(c,p,'place_order103')['status'],'rejected')
  with self.actor() as c:r=c.execute('select order_request_status104(%s)',(p[8],)).fetchone()[0];self.assertEqual(r['closure_id'],receipt)
  self.assertEqual(self.counts(),(0,0,0,0));p[8]='corrected104_key'
  with self.actor() as c:self.assertEqual(call(c,p,'place_order104')['status'],'created')
  self.assertEqual(self.counts(),(1,1,-5,1))
 def test_unresolved_never_gets_closure(self):
  self.upgrade();holder=self.actor();holder.execute('select pg_advisory_xact_lock(hashtextextended(%s,0))',(B+':'+args()[8],))
  with self.actor() as c:c.execute("set lock_timeout='100ms'");r=call(c,args(),'place_order104');self.assertEqual(r['status'],'unresolved');self.assertNotIn('closed',r)
  holder.rollback();holder.close();self.assertEqual(self.a.execute('select count(*) from security_private.order_attempt_closures104').fetchone()[0],0)
  with self.actor() as c:self.assertEqual(call(c,args(),'place_order104')['status'],'created')
 def test_rejection_fence_concurrency(self):
  import threading,time
  self.upgrade();p=args('fence104_key');p[4]='';c=self.actor();r=call(c,p,'place_order104');self.assertTrue(r['closed']);out=[]
  fixed=args('fence104_key')
  def late():
   with self.actor() as other:out.append(call(other,fixed,'place_order104'))
  t=threading.Thread(target=late);t.start();time.sleep(.15);self.assertTrue(t.is_alive());c.commit();c.close();t.join(10);self.assertFalse(t.is_alive());self.assertEqual(out[0]['closure_id'],r['closure_id']);self.assertEqual(self.counts(),(0,0,0,0))
 def test_closure_acl_and_other_account(self):
  self.upgrade();p=args();p[4]=''
  with self.actor() as c:r=call(c,p,'place_order104');self.assertTrue(r['closed'])
  with self.actor(O) as c:r=c.execute('select order_request_status104(%s)',(p[8],)).fetchone()[0];self.assertEqual(r['status'],'unresolved');self.assertNotIn('closure_id',r)
  with self.actor() as c:
   with self.assertRaises(psycopg.errors.InsufficientPrivilege):c.execute('select * from security_private.order_attempt_closures104')
 def test_closure_survives_rollback_reupgrade(self):
  self.upgrade();p=args();p[4]=''
  with self.actor() as c:r=call(c,p,'place_order104');receipt=r['closure_id']
  self.a.execute(Path('tests/native104/rollback.sql').read_text());self.a.execute(namespace['MIGRATION'])
  with self.actor() as c:self.assertEqual(call(c,args(),'place_order104')['closure_id'],receipt)
  self.assertEqual(self.counts(),(0,0,0,0))
# Prove S01 red against unmodified103 first; separate disposable DB.
probe=BASE('test_invalid_inputs_and_unknown_status');probe.setUp()
try:
 original=''.join(Path('tests/native103/'+p).read_text() for p in ['schema.sql','functions.sql','migrate102.sql']);probe.a.execute(original);probe.a.execute('insert into security_private.order_request_keys103 values(1,%s,true)',(os.urandom(32),));p=args();p[5]=38.123456789012344
 with probe.actor() as c:c.execute('set extra_float_digits=0');assert call(c,p)['status']=='created'
 probe.a.execute(Path('tests/native103/rollback.sql').read_text())
 with probe.actor() as c:c.execute('set extra_float_digits=0');assert call(c,p)['status']=='conflict'
 print('S01 baseline103 reproduced: identical typed input falsely conflicts after rollback')
finally:probe.tearDown()
suite=unittest.TestSuite([unittest.defaultTestLoader.loadTestsFromTestCase(BASE),*(New104(n) for n in New104.__dict__ if n.startswith('test_'))]);cases=[t.id() for part in suite for t in part] if False else []
r=unittest.TextTestRunner(verbosity=2).run(suite)
Path('native104-results.json').write_text(json.dumps({'tests':r.testsRun,'passed':r.wasSuccessful(),'baseline103_S01_reproduced':True,'failures':[t.id() for t,_ in r.errors+r.failures],'scope':'real PostgreSQL17.6 partial synthetic schema; no hosted HTTP','sha256':{n:hashlib.sha256(Path('tests/native104/'+n).read_bytes()).hexdigest() for n in ['schema.sql','functions.sql','lifecycle.sql','rollback.sql']}},indent=2));sys.exit(0 if r.wasSuccessful() else 1)
