"""Native server only. Synthetic IDs; all app SQL is executed in disposable databases."""
import os,json,time,threading,unittest,hashlib,sys
from pathlib import Path
import psycopg
sys.path.insert(0,'tests/native102')
from tcp_proxy import CutProxy
assert os.environ.get('PGHOST')=='127.0.0.1'
B='10000000-0000-4000-8000-000000000092';O='20000000-0000-4000-8000-000000000092';S='30000000-0000-4000-8000-000000000092';I='40000000-0000-4000-8000-000000000092';G='60000000-0000-4000-8000-000000000092'
SIG='(uuid,jsonb,numeric,text,text,float8,float8,text,text,numeric,numeric,int,jsonb)'
BASE=Path('tests/native98/setup.sql').read_text().replace('create role authenticated;create role anon;','')+Path('tests/native102/constraints.sql').read_text()+Path('tests/native103/fidelity.sql').read_text()
MIGRATION=''.join(Path('tests/native103/'+p).read_text() for p in ['schema.sql','functions.sql','migrate102.sql'])
ROOT=psycopg.connect(autocommit=True)
for role in ['authenticated','anon']:
 if not ROOT.execute('select 1 from pg_roles where rolname=%s',(role,)).fetchone():ROOT.execute('create role '+role)
def args(key='request103_default',extra=None,qty=1,uid=None):return [S,[{'item_id':I,'qty':qty,'options':[]}],0,'cash','synthetic address',38.5,68.7,None,key,None,5,None,extra]
def call(c,a,fn='place_order103'):
 v=list(a);v[1]=json.dumps(v[1]) if v[1] is not None else None;v[12]=json.dumps(v[12]) if v[12] is not None else None
 return c.execute('select '+fn+'(%s::uuid,%s::jsonb,%s::numeric,%s::text,%s::text,%s::float8,%s::float8,%s::text,%s::text,%s::numeric,%s::numeric,%s::int,%s::jsonb)',v).fetchone()[0]
class SQL103(unittest.TestCase):
 def setUp(self):
  ROOT.execute('drop database if exists candidate103 with (force)');ROOT.execute('create database candidate103')
  self.a=psycopg.connect(dbname='candidate103',autocommit=True);self.a.execute(BASE);self.a.execute('create schema extensions;create extension pgcrypto with schema extensions')
 def tearDown(self):self.a.close()
 def upgrade(self):
  self.a.execute(MIGRATION)
  if not self.a.execute('select 1 from security_private.order_request_keys103').fetchone():self.a.execute('insert into security_private.order_request_keys103 values(1,%s,true)',(os.urandom(32),))
 def actor(self,uid=B,port=5432):
  c=psycopg.connect(dbname='candidate103',port=port,sslmode='disable');c.execute("set statement_timeout='15s'");c.execute("select set_config('request.jwt.claims',%s,false)",(json.dumps({'sub':uid,'aal':'aal1','session_id':'50000000-0000-4000-8000-000000000092'}),));c.execute('set role authenticated');return c
 def group(self):self.a.execute("insert into group_orders(id,host_id,status,store_id,expires_at)values(%s,%s,'open',%s,now()+interval '1 hour')",(G,B,S))
 def snapshot(self):
  tables=['orders','order_items','wallet_entries','order_customer_phone','order_recipient','group_orders','fulfillment_private.order_approvals']
  if self.a.execute("select to_regclass('security_private.order_request_fingerprints103')").fetchone()[0]:tables+=['security_private.order_request_fingerprints103']
  return {t:self.a.execute("select coalesce(jsonb_agg(to_jsonb(t) order by to_jsonb(t)::text),'[]'::jsonb) from "+t+' t').fetchone()[0] for t in tables}
 def counts(self):return self.a.execute("select (select count(*) from orders),(select count(*) from wallet_entries where kind='spend'),(select coalesce(sum(amount),0) from wallet_entries where kind='spend'),(select count(*) from security_private.order_request_fingerprints103)").fetchone()
 def consent(self):self.a.execute("update fulfillment_private.order_approvals set state='accepted',customer_at=now()")
 def test_historical_normal_group_scheduled_readonly(self):
  for mode in ['normal','group','scheduled']:
   with self.subTest(mode=mode):
    if mode=='group':self.group()
    extra={'group':G} if mode=='group' else {'at':(self.a.execute("select now()+interval '40 minutes 1 second'").fetchone()[0]).isoformat()} if mode=='scheduled' else None
    aa=args('historical103_'+mode,extra)
    with self.actor() as c:oid=call(c,aa,'place_order')
    self.consent()
  self.upgrade();time.sleep(1.1)
  before=self.snapshot()
  with self.actor() as c:
   c.execute('set transaction read only') if False else None
   for mode in ['normal','group','scheduled']:
    # Deliberately different/invalid new payload: historical retrieval does not assert old content equality.
    aa=args('historical103_'+mode,{'at':'invalid'},qty=3);r=call(c,aa);self.assertEqual(r['status'],'historical_recovered');self.assertIsNone(r['input_match'])
    self.assertEqual(c.execute('select order_request_status103(%s)',(aa[8],)).fetchone()[0]['id'],r['id'])
  self.assertEqual(before,self.snapshot());self.assertEqual(self.counts(),(3,3,-15,0))
  # Genuine server READ ONLY transaction proves this recovery branch does not write.
  with psycopg.connect(dbname='candidate103') as c:
   c.execute('set transaction read only');c.execute("select set_config('request.jwt.claims',%s,false)",(json.dumps({'sub':B}),));c.execute('set role authenticated');self.assertEqual(call(c,args('historical103_normal'))['status'],'historical_recovered')
 def test_normal_group_schedule_verified_replay(self):
  self.upgrade()
  for mode in ['normal','group','scheduled']:
   if mode=='group':self.group()
   extra={'group':G} if mode=='group' else {'at':self.a.execute("select now()+interval '40 minutes 1 second'").fetchone()[0].isoformat()} if mode=='scheduled' else None
   aa=args('new103_'+mode,extra)
   with self.actor() as c:r=call(c,aa);self.assertEqual(r['status'],'created')
   before=self.snapshot()
   if mode=='scheduled':time.sleep(1.1)
   with self.actor() as c:
    replay=call(c,aa);self.assertEqual(replay['status'],'replayed');self.assertTrue(replay['input_match']);self.assertEqual(replay['id'],r['id'])
    changed=list(aa);changed[1]=[{'item_id':I,'qty':2,'options':[]}];self.assertEqual(call(c,changed)['status'],'conflict')
   self.assertEqual(before,self.snapshot());self.consent()
 def test_canonical_equivalence_and_difference(self):
  self.upgrade();aa=args(extra=None)
  with self.actor() as c:self.assertEqual(call(c,aa)['status'],'created')
  before=self.snapshot()
  with self.actor() as c:
   bb=list(aa);bb[12]={};bb[1]=[{'options':[],'qty':1.0,'item_id':I}];bb[2]='0.00';self.assertEqual(call(c,bb)['status'],'replayed')
   for pos,value in [(4,'different address'),(5,38.50001),(10,6),(12,{'door':False}),(7,'OTHER'),(3,'card')]:
    bb=list(aa);bb[pos]=value;self.assertEqual(call(c,bb)['status'],'conflict')
  self.assertEqual(before,self.snapshot())
  # Arrays retain order; nested null differs from absence. No lossy rounding/truncation.
  canonical=lambda x:self.a.execute('select security_private.canonical103(%s::jsonb)',(json.dumps(x),)).fetchone()[0]
  self.assertNotEqual(canonical([1,2]),canonical([2,1]));self.assertNotEqual(canonical({'x':None}),canonical({}))
 def test_identity_revocation_and_group_access(self):
  self.upgrade();self.group();aa=args(extra={'group':G})
  with self.actor() as c:self.assertEqual(call(c,aa)['status'],'created')
  before=self.snapshot()
  with self.actor(O) as c:self.assertEqual(call(c,aa)['status'],'rejected');self.assertEqual(c.execute('select order_request_status103(%s)',(aa[8],)).fetchone()[0]['status'],'unresolved')
  self.a.execute('insert into security_private.revoked_sessions values(%s,%s)',(B,'50000000-0000-4000-8000-000000000092'))
  with self.actor() as c:self.assertEqual(call(c,aa)['reason'],'account_blocked')
  self.assertEqual(before,self.snapshot())
 def test_binding_failure_atomicity_and_missing_binding(self):
  self.upgrade();self.a.execute("create function security_private.fail103() returns trigger language plpgsql as $$begin raise exception 'synthetic_binding_failure';end$$;create trigger fail103 before insert on security_private.order_request_fingerprints103 for each row execute function security_private.fail103()")
  before=self.snapshot()
  with self.actor() as c:self.assertEqual(call(c,args())['status'],'rejected')
  self.assertEqual(before,self.snapshot());self.a.execute('drop trigger fail103 on security_private.order_request_fingerprints103')
  with self.actor() as c:self.assertEqual(call(c,args())['status'],'created')
  self.assertEqual(self.counts(),(1,1,-5,1));self.a.execute('delete from security_private.order_request_fingerprints103')
  with self.actor() as c:self.assertEqual(call(c,args())['status'],'unresolved')
  self.assertEqual(self.counts(),(1,1,-5,0))
 def test_key_rotation_privacy_and_acl(self):
  self.upgrade()
  with self.actor() as c:self.assertEqual(call(c,args())['status'],'created')
  self.a.execute('update security_private.order_request_keys103 set active=false');self.a.execute('insert into security_private.order_request_keys103 values(2,%s,true)',(os.urandom(32),))
  with self.actor() as c:self.assertEqual(call(c,args())['status'],'replayed')
  self.consent()
  with self.actor() as c:self.assertEqual(call(c,args('rotated103'))['status'],'created')
  self.assertEqual(self.a.execute('select array_agg(key_id order by key_id) from security_private.order_request_fingerprints103').fetchone()[0],[1,2])
  row=str(self.a.execute('select to_jsonb(f) from security_private.order_request_fingerprints103 f').fetchall());self.assertNotIn('synthetic address',row);self.assertNotIn('38.5',row)
  for role in ['authenticated','anon']:
   with psycopg.connect(dbname='candidate103') as c:
    c.execute('set role '+role)
    for sql in ['select * from security_private.order_request_keys103','select * from security_private.order_request_fingerprints103',"select security_private.canonical103('{}')"]:
     with self.assertRaises(psycopg.errors.InsufficientPrivilege):c.execute(sql)
     c.rollback();c.execute('set role '+role)
 def test_invalid_inputs_and_unknown_status(self):
  self.upgrade();before=self.snapshot()
  for items in [None,{},[],[{'item_id':'bad'}],[{'item_id':I,'qty':1},{'item_id':O,'qty':1}]]:
   aa=args();aa[1]=items
   with self.actor() as c:self.assertEqual(call(c,aa)['status'],'rejected')
  with self.actor() as c:self.assertEqual(c.execute("select order_request_status103('missing103')").fetchone()[0]['status'],'unresolved')
  self.assertEqual(before,self.snapshot())
 def test_conversion_existing102_no_historical_fabrication(self):
  self.a.execute(Path('tests/native102/candidate.sql').read_text())
  with self.actor() as c:oid=call(c,args(),'place_order')
  self.upgrade()
  with self.actor() as c:self.assertEqual(call(c,args())['status'],'unresolved')
  self.assertEqual(self.a.execute('select security_private.convert_bindings102_to103()').fetchone()[0],1)
  self.assertEqual(self.a.execute('select count(*) from security_private.order_request_bindings').fetchone()[0],0)
  self.assertEqual(self.a.execute('select security_private.convert_bindings102_to103()').fetchone()[0],0)
  with self.actor() as c:r=call(c,args());self.assertEqual(r['status'],'replayed');self.assertEqual(int(r['id']),oid)
 def test_rollback_reupgrade_and_interrupted_migration(self):
  self.upgrade()
  with self.actor() as c:oid=call(c,args())['id']
  self.a.execute(Path('tests/native103/rollback.sql').read_text());before=self.snapshot()
  with self.actor() as c:
   self.assertEqual(call(c,args('rollback_new103'))['reason'],'rollback_read_only')
   changed=args(qty=2);self.assertEqual(call(c,changed)['status'],'conflict')
  with self.actor() as c:self.assertEqual(c.execute('select order_request_status103(%s)',(args()[8],)).fetchone()[0]['id'],oid)
  self.a.execute(MIGRATION);self.assertEqual(before,self.snapshot())
  with self.actor() as c:self.assertEqual(call(c,args())['status'],'replayed')
  # Transactional DDL interruption: all candidate objects stay at previous valid state.
  with psycopg.connect(dbname='candidate103') as c:
   c.execute(MIGRATION);c.rollback()
  self.assertEqual(before,self.snapshot())
 def test_concurrent_same_group_and_different_keys(self):
  self.upgrade();self.group();aa=args(extra={'group':G});c1=self.actor();c2=self.actor();first=call(c1,aa);out={}
  def run():
   try:out['r']=call(c2,aa);c2.commit()
   finally:c2.close()
  t=threading.Thread(target=run);t.start();blocked=False
  for _ in range(200):
   blocked=c1.info.backend_pid in self.a.execute('select pg_blocking_pids(%s)',(c2.info.backend_pid,)).fetchone()[0]
   if blocked:break
   time.sleep(.01)
  self.assertTrue(blocked);c1.commit();c1.close();t.join(15);self.assertFalse(t.is_alive());self.assertEqual(out['r']['id'],first['id']);self.assertEqual(out['r']['status'],'replayed');self.assertEqual(self.counts(),(1,1,-5,1))
  with self.actor() as c:self.assertEqual(call(c,args('different103',{'group':G}))['reason'],'bad_group')
 def test_tcp_before_after_commit(self):
  self.upgrade()
  for mode in ['before','after']:
   self.consent();proxy=CutProxy(mode);c=self.actor(port=proxy.port);aa=args('tcp103_'+mode);r=call(c,aa);self.assertEqual(r['status'],'created');proxy.arm=True
   with self.assertRaises((psycopg.OperationalError,psycopg.InterfaceError)):c.commit()
   c.close();proxy.join();self.assertTrue(proxy.cut)
   for _ in range(100):
    count=self.a.execute('select count(*) from orders where client_key=%s',(aa[8],)).fetchone()[0]
    if count==(1 if mode=='after' else 0):break
    time.sleep(.01)
   self.assertEqual(count,1 if mode=='after' else 0)
   with self.actor() as retry:r2=call(retry,aa)
   self.assertEqual(r2['status'],'replayed' if mode=='after' else 'created')
   self.assertEqual(self.a.execute("select count(*),sum(amount) from wallet_entries where order_id=%s and kind='spend'",(r2['id'],)).fetchone(),(1,-5))
 def test_lock_timeout_preserves_key_without_retry(self):
  self.upgrade();hold=psycopg.connect(dbname='candidate103');hold.execute('select * from profiles where id=%s for update',(B,))
  with self.actor() as c:
   c.execute("set lock_timeout='100ms'");r=call(c,args());self.assertEqual(r['status'],'unresolved');self.assertEqual(r['reason'],'55P03')
  hold.rollback();hold.close();self.assertEqual(self.counts(),(0,0,0,0))
  with self.actor() as c:self.assertEqual(call(c,args())['status'],'created')
 def test_old_writer_overlap_and_no_duplicate(self):
  # Preserve exact98 function as an explicitly test-only legacy writer.
  legacy=Path('tests/native98/place_order.fixed.sql').read_text().replace('public.place_order(', 'public.legacy_writer103(',1)
  self.a.execute(legacy);self.upgrade();c1=self.actor();c2=self.actor();aa=args('mixed103_writer');oid=call(c1,aa,'legacy_writer103');out={}
  def newer():
   try:out['r']=call(c2,aa);c2.commit()
   finally:c2.close()
  t=threading.Thread(target=newer);t.start();blocked=False
  for _ in range(200):
   blocked=c1.info.backend_pid in self.a.execute('select pg_blocking_pids(%s)',(c2.info.backend_pid,)).fetchone()[0]
   if blocked:break
   time.sleep(.01)
  self.assertTrue(blocked);c1.commit();c1.close();t.join(15);self.assertFalse(t.is_alive());self.assertEqual(out['r']['status'],'historical_recovered');self.assertEqual(int(out['r']['id']),oid);self.assertEqual(self.counts(),(1,1,-5,0))
 def test_deadlock_reports_unknown_without_blind_retry(self):
  self.upgrade();self.group();aa=args(extra={'group':G});hold=psycopg.connect(dbname='candidate103');hold.execute("set deadlock_timeout='100ms'");hold.execute('select * from profiles where id=%s for update',(B,));c=self.actor();out={}
  def waiter():
   try:out['r']=call(c,aa);c.commit()
   finally:c.close()
  t=threading.Thread(target=waiter);t.start();blocked=False
  for _ in range(200):
   blocked=hold.info.backend_pid in self.a.execute('select pg_blocking_pids(%s)',(c.info.backend_pid,)).fetchone()[0]
   if blocked:break
   time.sleep(.01)
  self.assertTrue(blocked);code=None
  try:hold.execute('select * from group_orders where id=%s for update',(G,))
  except psycopg.Error as e:code=e.sqlstate
  finally:hold.rollback();hold.close()
  t.join(15);self.assertFalse(t.is_alive());self.assertTrue(code=='40P01' or out['r'].get('reason')=='40P01')
  if out['r']['status']=='unresolved':self.assertEqual(self.counts(),(0,0,0,0))
  # Explicit outcome read, then explicit same-key retry only if no visible result.
  with self.actor() as c:state=c.execute('select order_request_status103(%s)',(aa[8],)).fetchone()[0]
  with self.actor() as c:r=call(c,aa)
  self.assertIn(r['status'],['created','replayed']);self.assertEqual(self.counts(),(1,1,-5,1))
 def test_promo_loyalty_wallet_atomic_with_captured_helpers(self):
  self.upgrade();self.a.execute(Path('tests/native103/dependencies.sql').read_text())
  self.a.execute("insert into promo_codes values('TEST103',true,null,null,0,1,'fixed',5)");self.a.execute("insert into promo_attempts values(%s,true,'TEST103',now())",(B,))
  self.a.execute("insert into loyalty_lots(user_id,points_left,expires_at)values(%s,100,now()+interval '1 day')",(B,))
  aa=args('deps103_case');aa[7]='TEST103';aa[11]=100
  self.a.execute("create function security_private.faildeps103() returns trigger language plpgsql as $$begin raise exception 'synthetic_binding_failure';end$$;create trigger faildeps103 before insert on security_private.order_request_fingerprints103 for each row execute function security_private.faildeps103()")
  before=self.snapshot()
  with self.actor() as c:self.assertEqual(call(c,aa)['status'],'rejected')
  self.assertEqual(before,self.snapshot());self.assertEqual(self.a.execute('select points_left from loyalty_lots').fetchone()[0],100);self.assertEqual(self.a.execute('select count(*) from loyalty_ledger').fetchone()[0],0)
  self.a.execute('drop trigger faildeps103 on security_private.order_request_fingerprints103')
  with self.actor() as c:r=call(c,aa);self.assertEqual(r['status'],'created')
  self.assertEqual(self.a.execute('select promo_discount,points_used,points_value,total,wallet_used from orders').fetchone(),(5,100,10,7,5))
  self.assertEqual(self.a.execute('select points_left from loyalty_lots').fetchone()[0],0);self.assertEqual(self.a.execute('select count(*),sum(points) from loyalty_ledger').fetchone(),(1,-100))
  before=self.snapshot()
  with self.actor() as c:self.assertEqual(call(c,aa)['status'],'replayed')
  self.assertEqual(before,self.snapshot());self.assertEqual(self.a.execute('select count(*) from loyalty_ledger').fetchone()[0],1)
 def test_target_identity_uuid_fk_overlay(self):
  self.upgrade()
  self.assertEqual(self.a.execute("select attidentity from pg_attribute where attrelid='orders'::regclass and attname='id'").fetchone()[0],'a')
  self.assertEqual(self.a.execute("select format_type(atttypid,atttypmod) from pg_attribute where attrelid='order_items'::regclass and attname='id'").fetchone()[0],'uuid')
  with self.assertRaises(psycopg.errors.ForeignKeyViolation):self.a.execute("insert into group_orders(id,host_id,status,store_id,expires_at)values(%s,%s,'open',%s,now())",(G,I,S))
 def test_first_install_interrupted_rolls_back_schema_and_function(self):
  with psycopg.connect(dbname='candidate103') as c:c.execute(MIGRATION);c.rollback()
  self.assertIsNone(self.a.execute("select to_regclass('security_private.order_request_fingerprints103')").fetchone()[0])
  self.upgrade()
  with self.actor() as c:self.assertEqual(call(c,args())['status'],'created')
 def test_hmac_independent_vector_and_immutable_key(self):
  import hmac
  self.upgrade();secret=os.urandom(32)
  payload=[S,[],0,'cash','synthetic',38.5,68.7,None,None,5,None,None]
  normalized=payload[:-1]+[{}]
  expected=hmac.new(secret,json.dumps(['TALABOT/order-create',1,B,'request103_vector',normalized],separators=(',',':')).encode(),hashlib.sha256).digest()
  actual=self.a.execute('select security_private.mac103(%s::jsonb,%s::uuid,%s,%s)',(json.dumps(payload),B,'request103_vector',secret)).fetchone()[0]
  self.assertEqual(bytes(actual),expected)
  with self.assertRaises(psycopg.errors.RaiseException):self.a.execute('update security_private.order_request_keys103 set secret=%s where key_id=1',(os.urandom(32),))
 def test_other_account_same_key_never_recovers_first_id(self):
  self.upgrade()
  with self.actor() as c:first=call(c,args())
  with self.actor(O) as c:second=call(c,args())
  self.assertEqual(first['status'],'created');self.assertEqual(second['status'],'created');self.assertNotEqual(first['id'],second['id']);self.assertEqual(self.counts(),(2,2,-10,2))
if __name__=='__main__':
 suite=unittest.defaultTestLoader.loadTestsFromTestCase(SQL103)
 names=[t.id() for t in suite]
 result=unittest.TextTestRunner(verbosity=2).run(suite)
 Path('native103-tests.json').write_text(json.dumps({'tests':result.testsRun,'passed':result.wasSuccessful(),'cases':names,'failures':[t.id() for t,_ in result.failures+result.errors],'scope':'PostgreSQL17.6 independent connections; partial synthetic schema; pgcrypto HMAC; no hosted HTTP','source_sha256':{p:hashlib.sha256(Path('tests/native103/'+p).read_bytes()).hexdigest() for p in ['schema.sql','functions.sql','migrate102.sql','rollback.sql']}},indent=2))
 sys.exit(0 if result.wasSuccessful() else 1)
