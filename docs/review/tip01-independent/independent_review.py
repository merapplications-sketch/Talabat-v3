"""Independent TIP01 delta QA. Fresh local cluster only; no hosted credentials/data."""
import os,sys,json,unittest,threading,time,uuid,hashlib,subprocess
from pathlib import Path
from decimal import Decimal as D
from datetime import datetime,timezone
assert os.environ.get('TIP_QA_LOCAL')=='fresh-cluster' and os.environ.get('PGHOST')=='127.0.0.1'
ns={'__name__':'fixture_only'}
exec(compile(Path('tests/native106/native.py').read_text(),'unchanged106-fixture','exec'),ns)
Base=ns['Isolation106'];call=ns['call'];args=ns['args'];B=ns['B'];O=ns['O'];pg=ns['psycopg']
ENTRIES=ns['ENTRIES'];LEVELS=ns['LEVELS'];PATCH=Path('tests/tip01/acceptance.sql').read_text()
S='30000000-0000-4000-8000-000000000092'
def p(key='qa_tip_default',tip=20,extra=None):
 v=args(key,extra);v[2]=tip;v[10]=7;v[4]='QA مستقل / Душанбе 😀';v[5]=38.123456789012344;return v
def oid(r):return str(r if isinstance(r,int) else r['id'])
class QA(Base):
 def setUp(self):
  super().setUp();self.a.execute("update wallet_entries set amount=1000 where kind='adjust'")
 def upgrade(self):super().upgrade();self.a.execute(PATCH)
 def fresh(self):self.upgrade();self.policy(200,200)
 def done(self):
  self.consent();self.a.execute("update orders set status='delivered'")
 def invoke(self,a,fn='place_order104',level='read committed'):
  c=self.tx(level,fn.startswith('security_private.'))
  try:return self.outcome(c,a,fn)
  finally:c.close()
 def metrics(self):
  return self.a.execute("select (select count(*) from orders),(select count(*) from wallet_entries where kind='spend'),(select coalesce(sum(amount),0) from wallet_entries where kind='spend'),(select count(*) from security_private.order_request_fingerprints103),(select count(*) from security_private.order_attempt_closures104)").fetchone()
 def ledger(self):
  tables=['orders','order_items','wallet_entries','order_customer_phone','order_recipient','group_orders','fulfillment_private.order_approvals','security_private.order_request_fingerprints103','security_private.order_attempt_closures104']
  return {t:self.a.execute('select coalesce(jsonb_agg(to_jsonb(x) order by to_jsonb(x)::text),\'[]\'::jsonb) from '+t+' x').fetchone()[0] for t in tables}
 def test_01_baseline_and_catalog_delta(self):
  Base.upgrade(self);self.policy(200,200)
  for i,fn in enumerate(ENTRIES):
   r=self.invoke(p('qa_red_'+str(i)),fn)
   self.assertEqual(self.a.execute('select tip,total,driver_payout from orders where id=%s',(oid(r),)).fetchone(),(0,22,D('1.5')));self.done()
  query="select n.nspname,p.proname,pg_get_function_identity_arguments(p.oid),pg_get_userbyid(p.proowner),p.prosecdef,p.proconfig,p.proacl::text,p.prosrc from pg_proc p join pg_namespace n on n.oid=p.pronamespace where n.nspname in ('public','security_private','finance_private','fulfillment_private','auth') order by 1,2,3"
  before=self.a.execute(query).fetchall();self.a.execute(PATCH);after=self.a.execute(query).fetchall()
  changed=[(a,b) for a,b in zip(before,after) if a!=b];self.assertEqual(len(before),len(after));self.assertEqual(len(changed),1)
  a,b=changed[0];self.assertEqual(a[:7],b[:7]);self.assertEqual(a[7].replace('p_tip in (0,3,5,10)','p_tip in (0,3,5,10,20)'),b[7]);self.assertEqual(a[:2],('security_private','create_order103'))
  self.assertTrue(a[4]);self.assertIn('search_path=pg_catalog, public',a[5]);self.assertIn('extra_float_digits=3',a[5])
  self.assertFalse(self.a.execute("select has_function_privilege('authenticated','security_private.create_order103(uuid,jsonb,numeric,text,text,float8,float8,text,text,numeric,numeric,int,jsonb)','execute')").fetchone()[0])
  self.assertFalse(self.a.execute("select has_table_privilege('authenticated','orders','insert')").fetchone()[0])
 def test_02_matrix_48_cases_distinct_financial_fixture(self):
  self.fresh();self.a.execute('update menu_items set price=37.35');self.a.execute('update stores set discount_pct=10')
  for i,fn in enumerate(ENTRIES):
   for mode in ['normal','group','scheduled']:
    for tip in [0,5,10,20]:
     extra={};key=f'qa_m_{i}_{mode}_{tip}'
     if mode=='group':
      g=str(uuid.uuid4());self.a.execute("insert into group_orders(id,host_id,status,store_id,expires_at) values(%s,%s,'open',%s,now()+interval '1 hour')",(g,B,S));extra={'group':g}
     if mode=='scheduled':extra={'at':self.a.execute("select now()+interval '2 hours'").fetchone()[0].isoformat()}
     a=p(key,tip,extra);r=self.invoke(a,fn);ident=oid(r)
     # Independent Decimal arithmetic:37.35-3.74=33.61;delivery2;commission3.36;driver1.5+tip.
     expected=(D(str(tip)),D('35.61')+tip,D('3.36'),D('1.5')+tip,D('33.61'),D(7))
     actual=self.a.execute('select tip,total,commission,driver_payout,subtotal-discount-promo_discount-points_value,wallet_used from orders where id=%s',(ident,)).fetchone();self.assertEqual(actual,expected,(fn,mode,tip))
     before=self.ledger();self.assertEqual(oid(self.invoke(a,fn)),ident);self.assertEqual(before,self.ledger());self.done()
     # Synthetic time-aging keeps this functional matrix separate from hourly quota tests.
     self.a.execute("update orders set created_at=now()-interval '2 hours'")
  self.assertEqual(self.metrics(),(48,48,-336,48,0))
 def test_03_bound_history_3_and_sent20_stored0(self):
  Base.upgrade(self);self.policy(200,200);saved=[]
  for tip in [3,20]:
   a=p('qa_bound_'+str(tip),tip);r=self.invoke(a);saved.append((a,oid(r)));self.done()
  self.assertEqual(self.a.execute('select tip from orders order by id').fetchall(),[(3,),(0,)])
  before=self.ledger();self.a.execute(PATCH)
  for a,ident in saved:
   for fn in ENTRIES:self.assertEqual(oid(self.invoke(a,fn)),ident)
  self.assertEqual(before,self.ledger());self.assertEqual(self.metrics(),(2,2,-14,2,0))
 def test_04_unbound_historical_recovery_not_match_claim(self):
  saved=[]
  for tip in [3,20]:
   a=p('qa_historical_'+str(tip),tip)
   with self.actor() as c:ident=call(c,a,'place_order')
   saved.append((a,str(ident)));self.done()
  self.fresh();before=self.ledger()
  for a,ident in saved:
   r=self.invoke(a);self.assertEqual(r['status'],'historical_recovered');self.assertIsNone(r['input_match']);self.assertEqual(oid(r),ident)
  self.assertEqual(before,self.ledger());self.assertEqual(self.metrics(),(2,2,-14,0,0))
  self.assertEqual(self.a.execute('select tip from orders order by id').fetchall(),[(3,),(0,)])
 def test_05_payload_conflict_canonical_and_float_context(self):
  self.fresh()
  for i,fn in enumerate(ENTRIES):
   a=p('qa_binding_'+str(i));r=self.invoke(a,fn);before=self.ledger()
   for digits in [-3,0,3]:
    c=self.tx(private=fn.startswith('security_private.'));c.execute('set extra_float_digits='+str(digits));a[2]=D('20.00');rr=self.outcome(c,a,fn);c.close();self.assertEqual(oid(rr),oid(r))
   a[2]=10;rr=self.invoke(a,fn)
   self.assertEqual(rr.get('message') if fn=='place_order' else rr.get('reason'),'idempotency_mismatch')
   self.assertEqual(before,self.ledger());self.done()
  self.assertEqual(self.metrics(),(4,4,-28,4,0))
 def test_06_same_key_accounts_and_group_authorization(self):
  self.fresh();a=p('qa_accounts');r=self.invoke(a)
  with self.actor(O) as c:
   status=c.execute('select order_request_status104(%s)',(a[8],)).fetchone()[0];self.assertNotIn('id',status)
   other=call(c,a,'place_order104');self.assertNotEqual(oid(r),oid(other));self.assertEqual(other['status'],'created')
  self.done();self.group();a=p('qa_group_auth',extra={'group':'60000000-0000-4000-8000-000000000092'});r=self.invoke(a);before=self.ledger()
  with self.actor(O) as c:
   rr=call(c,a,'place_order103');self.assertEqual(rr['status'],'rejected');self.assertNotIn('id',rr)
  self.assertEqual(before,self.ledger())
 def test_07_binding_failure_atomic_wallet_points_then_retry(self):
  self.fresh();self.a.execute(Path('tests/native103/dependencies.sql').read_text());self.a.execute('update menu_items set price=37.35')
  self.a.execute("insert into promo_codes values('QADELTA',true,null,null,0,1,'fixed',4)");self.a.execute("insert into promo_attempts values(%s,true,'QADELTA',now())",(B,));self.a.execute("insert into loyalty_lots(user_id,points_left,expires_at) values(%s,100,now()+interval '1 day')",(B,))
  a=p('qa_atomic');a[7]='QADELTA';a[11]=100
  self.a.execute("create function security_private.qa_fail() returns trigger language plpgsql as $$begin raise exception 'qa_binding_failure';end$$;create trigger qa_fail before insert on security_private.order_request_fingerprints103 for each row execute function security_private.qa_fail()")
  before=self.ledger();r=self.invoke(a,'place_order103');self.assertEqual(r['status'],'rejected');self.assertEqual(before,self.ledger());self.assertEqual(self.a.execute('select points_left from loyalty_lots').fetchone()[0],100);self.assertEqual(self.a.execute('select count(*) from loyalty_ledger').fetchone()[0],0)
  self.a.execute('drop trigger qa_fail on security_private.order_request_fingerprints103');r=self.invoke(a)
  self.assertEqual(r['status'],'created');self.assertEqual(self.a.execute('select total,commission,driver_payout,subtotal-discount-promo_discount-points_value from orders').fetchone(),(D('45.35'),D('3.74'),D('21.5'),D('23.35')))
  before=self.ledger();self.assertEqual(oid(self.invoke(a)),oid(r));self.assertEqual(before,self.ledger());self.assertEqual(self.metrics(),(1,1,-7,1,0));self.assertEqual(self.a.execute('select count(*),sum(points) from loyalty_ledger').fetchone(),(1,-100))
 def test_08_stale_snapshot_closed_key_all_entries(self):
  self.fresh()
  for level in LEVELS:
   for i,fn in enumerate(ENTRIES):
    key='qa_closed_'+level.replace(' ','_')+str(i);a=p(key);c=self.tx(level,fn.startswith('security_private.'));receipt=self.reject(key);self.assertTrue(receipt['closed']);before=self.ledger();rr=self.outcome(c,a,fn);c.close();self.assert_no_creation(rr,level,fn);self.assertEqual(before,self.ledger())
  self.assertEqual(self.metrics(),(0,0,0,0,16))
 def test_09_supported_create_and_unsupported_no_effect(self):
  self.fresh()
  for level in LEVELS:
   for i,fn in enumerate(ENTRIES):
    a=p('qa_isolation_'+level.replace(' ','_')+str(i));before=self.ledger();r=self.invoke(a,fn,level)
    if level in LEVELS[:2]:self.assertIsNotNone(oid(r));self.assertEqual(self.a.execute('select tip from orders where id=%s',(oid(r),)).fetchone()[0],20);self.done()
    else:self.assert_no_creation(r,level,fn);self.assertEqual(before,self.ledger())
  self.assertEqual(self.metrics(),(8,8,-56,8,0))
 def test_10_three_concurrent_retries_plus_conflicting_tip(self):
  self.fresh();a=p('qa_three');bar=threading.Barrier(3);out=[];errors=[]
  def worker(tip):
   try:
    c=self.actor();aa=list(a);aa[2]=tip;bar.wait(10);rr=call(c,aa,'place_order104');c.commit();c.close();out.append(rr)
   except Exception as e:errors.append(type(e).__name__)
  ts=[threading.Thread(target=worker,args=(20,)) for _ in range(3)]
  for t in ts:t.start()
  for t in ts:t.join(15);self.assertFalse(t.is_alive())
  self.assertFalse(errors);self.assertEqual(sorted(r['status'] for r in out),['created','replayed','replayed']);self.assertEqual(len({oid(r) for r in out}),1);self.assertEqual(self.metrics(),(1,1,-7,1,0))
  a[2]=10;self.assertEqual(self.invoke(a)['status'],'conflict');self.assertEqual(self.metrics(),(1,1,-7,1,0))
 def test_11_real_tcp_cut_before_after_commit(self):
  from tcp_proxy import CutProxy
  self.fresh()
  for mode in ['before','after']:
   proxy=CutProxy(mode);c=self.actor(port=proxy.port);a=p('qa_tcp_'+mode);call(c,a,'place_order104');proxy.arm=True
   with self.assertRaises((pg.OperationalError,pg.InterfaceError)):c.commit()
   c.close();proxy.join();self.assertTrue(proxy.cut)
   for _ in range(100):
    n=self.a.execute('select count(*) from orders where client_key=%s',(a[8],)).fetchone()[0]
    if n==(0 if mode=='before' else 1):break
    time.sleep(.01)
   self.assertEqual(n,0 if mode=='before' else 1);r=self.invoke(a);self.assertEqual(r['status'],'created' if mode=='before' else 'replayed');self.done()
  self.assertEqual(self.metrics(),(2,2,-14,2,0))
 def test_12_closure_budget_and_no_false_terminal(self):
  self.fresh();self.policy(1,1);receipt=self.reject('qa_budget_full');self.assertTrue(receipt['closed']);before=self.ledger();rr=self.reject('qa_budget_new');self.assertEqual(rr['status'],'unresolved');self.assertNotIn('closed',rr);self.assertEqual(before,self.ledger())
  r=self.invoke(p('qa_valid_budget'));self.assertEqual(r['status'],'created');before=self.ledger();self.assertEqual(oid(self.invoke(p('qa_valid_budget'))),oid(r));self.assertEqual(before,self.ledger())
  self.assertEqual(self.reject('qa_budget_full')['closure_id'],receipt['closure_id']);self.assertEqual(self.metrics(),(1,1,-7,1,1))
 def test_13_order_limits_open_and_hour(self):
  self.fresh()
  for i in range(5):self.assertEqual(self.invoke(p('qa_open_'+str(i)))['status'],'created');self.consent()
  before=self.snapshot();r=self.invoke(p('qa_open_rejected'));self.assertEqual(r['reason'],'too_many_orders');self.assertEqual(before,self.snapshot());self.assertEqual(self.metrics()[:4],(5,5,-35,5));self.done()
  for i in range(15):self.assertEqual(self.invoke(p('qa_hour_'+str(i)))['status'],'created');self.done()
  before=self.snapshot();r=self.invoke(p('qa_hour_rejected'));self.assertEqual(r['reason'],'too_many_orders');self.assertEqual(before,self.snapshot());self.assertEqual(self.metrics()[:4],(20,20,-140,20))
 def test_14_rollback_reupgrade_preserves_keys_and_fences(self):
  self.fresh();a=p('qa_before_rollback');r=self.invoke(a);receipt=self.reject('qa_rollback_closed');before=self.ledger()
  self.a.execute(Path('tests/native104/rollback.sql').read_text())
  for fn in ENTRIES[:3]:
   self.assertEqual(oid(self.invoke(a,fn)),oid(r));rr=self.invoke(p('qa_new_downgraded'),fn);self.assertNotIn('id',rr)
  self.assertEqual(before,self.ledger())
  # Privileged owner remains capable: rollback requires writer quiescence; no public grant is added.
  self.assertFalse(self.a.execute("select has_function_privilege('authenticated','security_private.create_order103(uuid,jsonb,numeric,text,text,float8,float8,text,text,numeric,numeric,int,jsonb)','execute')").fetchone()[0])
  self.upgrade();self.assertEqual(before,self.ledger());self.assertEqual(self.reject('qa_rollback_closed')['closure_id'],receipt['closure_id']);self.assertEqual(oid(self.invoke(a)),oid(r));self.done();rr=self.invoke(p('qa_after_reupgrade'));self.assertEqual(rr['status'],'created');self.assertEqual(self.a.execute('select tip from orders where id=%s',(oid(rr),)).fetchone()[0],20)
 def test_15_unsupported_inputs_unchanged_not_approved(self):
  Base.upgrade(self);self.policy(200,200);baseline={}
  for i,tip in enumerate([3,None,7,-1,D('10.5')]):
   r=self.invoke(p('qa_compat_old_'+str(i),tip));baseline[i]=self.a.execute('select tip,total,commission,driver_payout from orders where id=%s',(oid(r),)).fetchone();self.done()
  self.a.execute(PATCH)
  for i,tip in enumerate([3,None,7,-1,D('10.5')]):
   r=self.invoke(p('qa_compat_new_'+str(i),tip));self.assertEqual(self.a.execute('select tip,total,commission,driver_payout from orders where id=%s',(oid(r),)).fetchone(),baseline[i]);self.done()
 def test_16_separate_database_dump_restore(self):
  self.fresh();a=p('qa_restore');r=self.invoke(a);receipt=self.reject('qa_restore_closed');before=self.ledger()
  dump=Path('runtime/qa-private-synthetic.dump');subprocess.run(['pg_dump','-Fc','-d','candidate103','-f',str(dump)],check=True,capture_output=True)
  root=pg.connect(dbname='postgres',autocommit=True);root.execute('create database qa_tip_restore');root.close();subprocess.run(['pg_restore','-d','qa_tip_restore',str(dump)],check=True,capture_output=True)
  original=self.a;self.a=pg.connect(dbname='qa_tip_restore',autocommit=True)
  try:
   self.assertEqual(before,self.ledger())
   with pg.connect(dbname='qa_tip_restore') as c:
    c.execute("select set_config('request.jwt.claims',%s,false)",(json.dumps({'sub':B}),));c.execute('set role authenticated');rr=call(c,a,'place_order104');self.assertEqual(oid(rr),oid(r));self.assertEqual(rr['status'],'replayed');closed=call(c,p('qa_restore_closed'),'place_order104');self.assertEqual(closed['closure_id'],receipt['closure_id'])
   self.assertEqual(before,self.ledger());self.assertEqual(self.metrics(),(1,1,-7,1,1))
  finally:self.a.close();self.a=original
class Recorded(unittest.TextTestResult):
 def startTest(self,t):super().startTest(t);self.started=time.time()
 def addSuccess(self,t):super().addSuccess(t);results.append({'case':t._testMethodName,'result':'PASS','seconds':round(time.time()-self.started,3)})
 def addFailure(self,t,e):super().addFailure(t,e);results.append({'case':t._testMethodName,'result':'FAIL'})
 def addError(self,t,e):super().addError(t,e);results.append({'case':t._testMethodName,'result':'ERROR'})
results=[];start=datetime.now(timezone.utc).isoformat()
version=pg.connect(dbname='postgres',autocommit=True).execute('select version()').fetchone()[0]
suite=unittest.TestSuite(QA(n) for n in QA.__dict__ if n.startswith('test_'))
r=unittest.TextTestRunner(verbosity=2,resultclass=Recorded).run(suite)
Path('qa-results.json').write_text(json.dumps({'start_utc':start,'end_utc':datetime.now(timezone.utc).isoformat(),'server':version,'candidate':'bcf651a7784617545354d2c6d7fe3d74d026c611','source':'independent_review.py; fixture from106; explicit synthetic financial values','scope':'NATIVE POSTGRESQL; not hosted HTTP or browser','tests':r.testsRun,'passed':r.wasSuccessful(),'results':results},indent=2))
raise SystemExit(not r.wasSuccessful())
