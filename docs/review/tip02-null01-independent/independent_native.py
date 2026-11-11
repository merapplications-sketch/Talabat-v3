"""Independent TIP02 + NULL01 QA; disposable local PostgreSQL only."""
import os,json,unittest,threading,time,uuid,hashlib,difflib
from pathlib import Path
from decimal import Decimal as D
from datetime import datetime,timezone
assert os.environ.get('TIP_FINAL_QA')=='fresh-local' and os.environ.get('PGHOST')=='127.0.0.1'
ns={'__name__':'fixture_only'}
exec(compile(Path('tests/native106/native.py').read_text(),'pinned106-fixture','exec'),ns)
Base=ns['Isolation106']; call=ns['call']; args=ns['args']; pg=ns['psycopg']; B=ns['B']; O=ns['O']; ENTRIES=ns['ENTRIES']; LEVELS=ns['LEVELS']
TIP1=Path('tests/tip01/acceptance.sql').read_text();TIP2=Path('tests/tip02/acceptance.sql').read_text();FINAL=Path('tests/tip02-null01/acceptance.sql').read_text()
def p(key,tip=37,extra=None):
 a=args(key,extra);a[2]=tip;a[10]=7;a[4]='Independent QA / Душанбе / اختبار';return a
def oid(r):return str(r if isinstance(r,int) else r['id'])
class QA(Base):
 def setUp(self):
  super().setUp();self.a.execute("update wallet_entries set amount=1000 where kind='adjust'")
  self.a.execute("select setval(pg_get_serial_sequence('orders','id'),10000,false)")
 def upgrade(self):
  Base.upgrade(self);self.a.execute(TIP1);self.a.execute(TIP2);self.a.execute(FINAL)
 def ready(self):self.upgrade();self.policy(200,200)
 def done(self):
  self.consent();self.a.execute("update orders set status='delivered',created_at=now()-interval '2 hours'")
 def invoke(self,a,fn='place_order104',level='read committed'):
  c=self.tx(level,fn.startswith('security_private.'))
  try:return self.outcome(c,a,fn)
  finally:c.close()
 def state(self):return {'data':self.snapshot(),'closures':self.a.execute('select customer_id,client_key,closure_id,state_version,reason,closed_at from security_private.order_attempt_closures104 order by customer_id,client_key').fetchall()}
 def rejected(self,r,fn,reason='bad_value'):
  self.assertEqual(r.get('message') if fn in ['place_order','security_private.create_order103'] else r.get('reason'),reason)
  self.assertNotIn('id',r)
 def test_01_complete_definition_and_effective_catalog(self):
  Base.upgrade(self);self.a.execute(TIP1);self.a.execute(TIP2)
  q="select n.nspname,p.proname,pg_get_function_identity_arguments(p.oid),p.proowner,p.prosecdef,p.proconfig,p.proacl::text,p.prosrc from pg_proc p join pg_namespace n on n.oid=p.pronamespace where n.nspname in ('public','security_private','finance_private','fulfillment_private','auth') order by 1,2,3"
  before=self.a.execute(q).fetchall();self.a.execute(FINAL);after=self.a.execute(q).fetchall()
  changed=[(a,b) for a,b in zip(before,after) if a!=b];self.assertEqual(len(before),len(after));self.assertEqual(len(changed),1)
  a,b=changed[0];self.assertEqual(a[:7],b[:7]);self.assertEqual(a[:2],('security_private','create_order103'))
  self.assertEqual(a[7].replace('-- Explicit NULL retains legacy behavior pending its separate owner contract.','-- NULL-01 owner decision: explicit NULL is rejected only for NEW creation.').replace('if p_tip is not null and (p_tip < 0 or p_tip > 100 or p_tip <> trunc(p_tip)) then','if p_tip is null or p_tip < 0 or p_tip > 100 or p_tip <> trunc(p_tip) then'),b[7])
  self.assertTrue(b[4]);self.assertIn('search_path=pg_catalog, public',b[5]);self.assertIn('extra_float_digits=3',b[5])
  self.assertFalse(self.a.execute("select has_function_privilege('authenticated','security_private.create_order103(uuid,jsonb,numeric,text,text,float8,float8,text,text,numeric,numeric,int,jsonb)','execute')").fetchone()[0])
 def test_02_new_domain_four_entries_three_modes(self):
  self.ready();self.a.execute('update menu_items set price=27.45');self.a.execute('update stores set discount_pct=10')
  n=0
  for i,fn in enumerate(ENTRIES):
   for mode in ['normal','group','scheduled']:
    for tip in [0,1,3,5,10,20,37,99,100]:
     extra=None
     if mode=='group':
      gid=str(uuid.uuid4());self.a.execute("insert into group_orders(id,host_id,status,store_id,expires_at) values(%s,%s,'open',%s,now()+interval '1 hour')",(gid,B,args()[0]));extra={'group':gid}
     if mode=='scheduled':extra={'at':self.a.execute("select now()+interval '2 hours'").fetchone()[0].isoformat()}
     a=p(f'finalqa_{i}_{mode}_{tip}',tip,extra);r=self.invoke(a,fn)
     expected=(D(tip),D('26.70')+tip,D('2.47'),D('1.50')+tip,D('24.70'),D(7))
     self.assertEqual(self.a.execute('select tip,total,commission,driver_payout,subtotal-discount-promo_discount-points_value,wallet_used from orders where id=%s',(oid(r),)).fetchone(),expected)
     before=self.state();self.assertEqual(oid(self.invoke(a,fn)),oid(r));self.assertEqual(self.state(),before);n+=1;self.done()
  self.assertEqual(n,108);self.assertEqual(self.counts(),(108,108,-756,108))
 def test_03_invalid_new_values_all_entries_no_finance(self):
  self.ready()
  vals=[None,D('-0.00001'),-1,D('0.5'),D('1.000001'),D('99.999999'),D('100.00001'),101,D('NaN'),D('Infinity'),D('-Infinity')]
  for i,fn in enumerate(ENTRIES):
   for j,v in enumerate(vals):
    before=self.snapshot();r=self.invoke(p(f'invalidqa_{i}_{j}',v),fn);self.rejected(r,fn);self.assertEqual(self.snapshot(),before);self.assertEqual(self.counts(),(0,0,0,0))
  self.assertEqual(self.rows(),len(vals))
 def test_04_default_zero_and_null_hmac_all_entries(self):
  self.ready()
  for i,fn in enumerate(ENTRIES):
   a=p('defaultqa_'+str(i),0);c=self.tx(private=fn.startswith('security_private.'))
   r=c.execute('select '+fn+'(p_store=>%s,p_items=>%s::jsonb,p_address=>%s,p_lat=>38.5,p_lng=>68.7,p_key=>%s,p_wallet=>7)',(a[0],json.dumps(a[1]),a[4],a[8])).fetchone()[0];c.commit();c.close()
   before=self.state();self.assertEqual(oid(self.invoke(a,fn)),oid(r));a[2]=D('0.000');self.assertEqual(oid(self.invoke(a,fn)),oid(r));a[2]=None;got=self.invoke(a,fn)
   self.assertEqual(got.get('message') if fn=='place_order' else got.get('reason'),'idempotency_mismatch');self.assertEqual(self.state(),before);self.done()
  self.assertEqual(self.counts(),(4,4,-28,4))
 def test_05_bound_legacy_null_and_invalid_payloads_unchanged(self):
  Base.upgrade(self);self.a.execute(TIP1);self.policy(200,200);saved=[]
  for i,tip in enumerate([None,3,20,D('10.5'),-1,101]):
   a=p('oldboundqa_'+str(i),tip);r=self.invoke(a);saved.append((a,oid(r)));self.done()
  self.assertEqual(self.a.execute('select tip from orders order by id').fetchall(),[(0,),(3,),(20,),(0,),(0,),(0,)])
  before=self.state();self.upgrade()
  for a,ident in saved:
   for fn in ENTRIES:
    r=self.invoke(a,fn);self.assertEqual(oid(r),ident)
    if fn!='place_order':self.assertEqual(r['status'],'replayed');self.assertTrue(r['input_match'])
  self.assertEqual(self.state(),before);a=saved[0][0].copy();a[2]=0;self.assertEqual(self.invoke(a)['status'],'conflict');self.assertEqual(self.state(),before)
 def test_06_pre_tip01_raw20_and_unbound_null_readonly(self):
  # True pre-binding fixture creation, not a fabricated historical fingerprint.
  a=p('unboundnullqa',None)
  with self.actor() as c:ident=call(c,a,'place_order')
  self.done();Base.upgrade(self);self.policy(200,200);b=p('old20qa_key',20);r=self.invoke(b);self.assertEqual(self.a.execute('select tip from orders where id=%s',(oid(r),)).fetchone()[0],0)
  self.done();before=self.state();self.upgrade()
  for fn in ENTRIES:
   rr=self.invoke(a,fn);self.assertEqual(oid(rr),str(ident))
   if fn!='place_order':self.assertEqual(rr['status'],'historical_recovered');self.assertIsNone(rr['input_match'])
   self.assertEqual(oid(self.invoke(b,fn)),oid(r))
  self.assertEqual(self.state(),before);self.assertEqual(self.counts(),(2,2,-14,1))
 def test_07_identity_account_and_original_group_authorization(self):
  Base.upgrade(self);self.a.execute(TIP2);self.policy(200,200);self.group();a=p('authnullqa',None,{'group':'60000000-0000-4000-8000-000000000092'});r=self.invoke(a);self.upgrade();before=self.state()
  for fn in ENTRIES:
   c=self.tx(private=fn.startswith('security_private.'));c.execute("select set_config('request.jwt.claims','{}',false)");res=self.outcome(c,a,fn);c.close();self.assertNotIn('id',res)
   with self.actor(O) as c:res=call(c,a,'place_order104')
   self.assertNotIn('id',res);self.assertEqual(res['status'],'rejected')
  # Another account may receive its own rejection fence; financial state stays identical.
  self.assertEqual(self.snapshot(),before['data']);self.a.execute('update group_orders set host_id=%s',(O,));denied=self.invoke(a);self.assertNotIn('id',denied);self.assertEqual(self.counts(),(1,1,-7,1))
 def race(self,first_tip,second_tip,fn,key):
  a=self.actor();one=p(key,first_tip);first=call(a,one,'place_order104');b=self.tx(private=fn.startswith('security_private.'));out={}
  def worker():
   try:out['r']=self.outcome(b,p(key,second_tip),fn)
   except Exception as e:out['error']=repr(e)
  t=threading.Thread(target=worker);t.start()
  try:
   waiting=False
   for _ in range(250):
    waiting=a.info.backend_pid in self.a.execute('select pg_blocking_pids(%s)',(b.info.backend_pid,)).fetchone()[0]
    if waiting:break
    time.sleep(.01)
   self.assertTrue(waiting,'did not prove independent blocked transaction');a.commit();t.join(12);self.assertFalse(t.is_alive());self.assertNotIn('error',out);return first,out['r']
  finally:
   a.close();b.close();t.join(1)
 def test_08_deterministic_null_closure_wins_four_entries(self):
  self.ready()
  for i,fn in enumerate(ENTRIES):
   r,rr=self.race(None,0,fn,'nullwinsqa_'+str(i));self.assertTrue(r['closed']);self.assert_no_creation(rr,'read committed',fn)
   if fn=='place_order104':self.assertEqual(rr['closure_id'],r['closure_id'])
  self.assertEqual(self.counts(),(0,0,0,0));self.assertEqual(self.rows(),4)
 def test_09_deterministic_zero_commit_wins_four_entries(self):
  self.ready()
  for i,fn in enumerate(ENTRIES):
   r,rr=self.race(0,None,fn,'zerowinsqa_'+str(i));self.assertEqual(r['status'],'created');self.assertEqual(rr.get('message') if fn=='place_order' else rr.get('reason'),'idempotency_mismatch');self.assertEqual(self.rows(),0);self.done()
  self.assertEqual(self.counts(),(4,4,-28,4))
 def test_10_tcp_cut_create_and_rejection_before_after_commit(self):
  from tcp_proxy import CutProxy
  self.ready()
  for tip in [99,None]:
   for mode in ['before','after']:
    key=f'tcpqa_{tip}_{mode}';a=p(key,tip);proxy=CutProxy(mode);c=self.actor(port=proxy.port);r=call(c,a,'place_order104');proxy.arm=True
    with self.assertRaises((pg.OperationalError,pg.InterfaceError)):c.commit()
    c.close();proxy.join();self.assertTrue(proxy.cut)
    with self.actor() as check:state=check.execute('select order_request_status104(%s)',(key,)).fetchone()[0]
    self.assertEqual(state['status'],('replayed' if tip is not None else 'rejected') if mode=='after' else 'unresolved')
    again=self.invoke(a)
    if tip is None:
     self.assertTrue(again['closed'])
     if mode=='after':self.assertEqual(again['closure_id'],r['closure_id'])
    else:
     self.assertIn(again['status'],['created','replayed'])
     if mode=='after':self.assertEqual(oid(again),oid(r))
     self.done()
    before=self.state();self.invoke(a);self.assertEqual(self.state(),before)
  self.assertEqual(self.counts(),(2,2,-14,2));self.assertEqual(self.rows(),2)
 def test_11_raw_null_success_ack_before_upgrade(self):
  from tcp_proxy import CutProxy
  Base.upgrade(self);self.a.execute(TIP2);self.policy(200,200);a=p('oldacknullqa',None);proxy=CutProxy('after');c=self.actor(port=proxy.port);r=call(c,a,'place_order104');proxy.arm=True
  with self.assertRaises((pg.OperationalError,pg.InterfaceError)):c.commit()
  c.close();proxy.join();self.upgrade();before=self.state();self.assertEqual(oid(self.invoke(a)),oid(r));self.assertEqual(self.state(),before);self.assertEqual(self.counts(),(1,1,-7,1))
 def test_12_isolation_closed_key_and_resource_fail_closed(self):
  self.ready()
  for level in LEVELS:
   for i,fn in enumerate(ENTRIES):
    key='isoqa_'+level.replace(' ','_')+str(i);before=self.snapshot();r=self.invoke(p(key,None),fn,level);self.assert_no_creation(r,level,fn);self.assertEqual(self.snapshot(),before)
  self.assertEqual(self.counts(),(0,0,0,0));self.assertEqual(self.rows(),2)
  self.policy(2,2);r=self.invoke(p('resourcefullqa',None));self.assertEqual(r['status'],'unresolved');self.assertNotIn('closed',r);self.assertEqual(self.rows(),2)
  # An existing terminal fence survives exhaustion and attempted correction.
  key='isoqa_read_committed2';a=p(key,100);r=self.invoke(a);self.assertTrue(r['closed']);self.assertEqual(self.counts(),(0,0,0,0))
 def test_13_atomic_promo_points_wallet_and_full_tip(self):
  self.ready();self.a.execute(Path('tests/native103/dependencies.sql').read_text());self.a.execute('update menu_items set price=37.35')
  self.a.execute("insert into promo_codes values('QAEXACT',true,null,null,0,1,'fixed',4)");self.a.execute("insert into promo_attempts values(%s,true,'QAEXACT',now())",(B,));self.a.execute("insert into loyalty_lots(user_id,points_left,expires_at) values(%s,100,now()+interval '1 day')",(B,))
  a=p('atomicmanualqa',100);a[7]='QAEXACT';a[11]=100
  self.a.execute("create function security_private.qa_fail() returns trigger language plpgsql as $$begin raise exception 'independent_binding_failure';end$$;create trigger qa_fail before insert on security_private.order_request_fingerprints103 for each row execute function security_private.qa_fail()")
  before=self.snapshot();r=self.invoke(a,'place_order103');self.assertEqual(r['status'],'rejected');self.assertEqual(self.snapshot(),before);self.assertEqual(self.a.execute('select points_left from loyalty_lots').fetchone()[0],100);self.assertEqual(self.a.execute('select count(*) from loyalty_ledger').fetchone()[0],0)
  self.a.execute('drop trigger qa_fail on security_private.order_request_fingerprints103');r=self.invoke(a);self.assertEqual(r['status'],'created')
  self.assertEqual(self.a.execute('select total,commission,driver_payout,subtotal-discount-promo_discount-points_value from orders').fetchone(),(D('125.35'),D('3.74'),D('101.5'),D('23.35')))
  before=self.state();self.invoke(a);self.assertEqual(self.state(),before);self.assertEqual(self.counts(),(1,1,-7,1));self.assertEqual(self.a.execute('select count(*),sum(points) from loyalty_ledger').fetchone(),(1,-100))
 def test_14_rollback_reupgrade_and_canonical_history(self):
  Base.upgrade(self);self.a.execute(TIP2);self.policy(200,200);a=p('rollbacknullqa',None);old=self.invoke(a);self.done();self.upgrade();b=p('rollbackmanualqa',100);new=self.invoke(b);closed=self.invoke(p('rollbackclosedqa',None));before=self.state()
  for rolling in [True,False]:
   if rolling:self.a.execute(Path('tests/native104/rollback.sql').read_text())
   else:self.upgrade()
   for fn in ENTRIES[:3]:
    for digits in [-3,0,3]:
     c=self.tx();c.execute('set extra_float_digits='+str(digits));rr=self.outcome(c,a,fn);c.close();self.assertEqual(oid(rr),oid(old))
     equivalent=b.copy();equivalent[2]=D('100.0000');self.assertEqual(oid(self.invoke(equivalent,fn)),oid(new))
    c=self.actor();receipt=c.execute('select order_request_status104(%s)',('rollbackclosedqa',)).fetchone()[0];c.commit();c.close();self.assertEqual(receipt['closure_id'],closed['closure_id'])
    fresh=self.invoke(p('rollbacknewqa',None),fn);self.assertNotIn('id',fresh)
    if rolling:self.assertTrue(fresh.get('status')=='unresolved' or fresh.get('message')=='order_outcome_unknown')
   # No modifications to original orders, monetary effects or fingerprints.
   self.assertEqual(self.snapshot(),before['data'])
  self.assertEqual(self.invoke(p('rollbackclosedqa',100))['closure_id'],closed['closure_id']);self.assertEqual(self.counts(),(2,2,-14,2))
 def test_15_same_manual_key_three_connections_one_spend(self):
  self.ready();bar=threading.Barrier(3);out=[];errors=[]
  def worker():
   try:
    with self.actor() as c:bar.wait(5);out.append(call(c,p('threeconnqa',100),'place_order104'))
   except Exception as e:errors.append(repr(e))
  ts=[threading.Thread(target=worker) for _ in range(3)]
  for t in ts:t.start()
  for t in ts:t.join(15);self.assertFalse(t.is_alive())
  self.assertFalse(errors,errors);self.assertEqual(sorted(r['status'] for r in out),['created','replayed','replayed']);self.assertEqual(len({oid(r) for r in out}),1);self.assertEqual(self.counts(),(1,1,-7,1))
 def test_16_order_limit_preserved_at_new_manual_boundary(self):
  self.ready()
  for i in range(5):self.assertEqual(self.invoke(p('limitqa_'+str(i),100))['status'],'created');self.consent()
  before=self.snapshot();r=self.invoke(p('limitqa_rejected',100));self.assertEqual(r['reason'],'too_many_orders');self.assertEqual(self.snapshot(),before);self.assertEqual(self.counts(),(5,5,-35,5))
class Recorded(unittest.TextTestResult):
 def addSuccess(self,t):super().addSuccess(t);records.append({'case':t._testMethodName,'result':'PASS'})
 def addFailure(self,t,e):super().addFailure(t,e);records.append({'case':t._testMethodName,'result':'FAIL','detail':self._exc_info_to_string(e,t)})
 def addError(self,t,e):super().addError(t,e);records.append({'case':t._testMethodName,'result':'ERROR','detail':self._exc_info_to_string(e,t)})
records=[];start=datetime.now(timezone.utc).isoformat();names=[n for n in QA.__dict__ if n.startswith('test_')]
if os.environ.get('QA_CASES'):names=os.environ['QA_CASES'].split(',')
r=unittest.TextTestRunner(verbosity=2,resultclass=Recorded).run(unittest.TestSuite(QA(n) for n in names))
Path(os.environ.get('QA_RESULT','qa-native-results.json')).write_text(json.dumps({'start_utc':start,'end_utc':datetime.now(timezone.utc).isoformat(),'candidate':'3279fefd7ac135ea5554a5ff76404a6ae510eb65','scope':'NATIVE POSTGRESQL 17.6, partial synthetic fixture, independent assertions','tests':r.testsRun,'passed':r.wasSuccessful(),'results':records},indent=2))
raise SystemExit(not r.wasSuccessful())
