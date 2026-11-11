"""NULL decision delta only. Disposable local PostgreSQL17.6 and synthetic fixture."""
import os,json,unittest,threading,time
from pathlib import Path
assert os.environ.get('TIP02_NULL_ISOLATED')=='yes'
ns={'__name__':'tip02_fixture'}
exec(compile(Path('tests/tip02/native.py').read_text(),'tip02_fixture','exec'),ns)
Base=ns['ManualTip'];call=ns['call'];args=ns['args'];ENTRIES=ns['ENTRIES'];pg=ns['pg']
class NullDecision(Base):
 def upgrade(self):
  super().upgrade()
  if os.environ.get('TIP02_NULL_BASELINE')!='yes':self.a.execute(Path('tests/tip02-null01/acceptance.sql').read_text())
 def invoke(self,p,fn='place_order104'):
  c=self.tx(private=fn.startswith('security_private.'))
  try:return self.outcome(c,p,fn)
  finally:c.close()
 def test_new_null_rejected_all_entries_no_financial_effect(self):
  self.upgrade();self.policy(200,200)
  for i,fn in enumerate(ENTRIES):
   with self.subTest(entry=fn):
    p=args('null01_new_'+str(i));p[2]=None;before=self.snapshot();r=self.invoke(p,fn)
    self.consent()
    if fn in ['place_order','security_private.create_order103']:self.assertEqual(r.get('message') if isinstance(r,dict) else None,'bad_value')
    else:self.assertEqual(r['status'],'rejected');self.assertEqual(r['reason'],'bad_value')
    self.assertEqual(before,self.snapshot());self.assertEqual(self.counts(),(0,0,0,0))
 def test_omitted_and_zero_equivalent_but_null_conflicts_all_entries(self):
  self.upgrade();self.policy(200,200)
  for i,fn in enumerate(ENTRIES):
   p=args('null01_default_'+str(i));c=self.tx(private=fn.startswith('security_private.'))
   r=c.execute('select '+fn+"(p_store=>%s,p_items=>%s::jsonb,p_address=>%s,p_lat=>38.5,p_lng=>68.7,p_key=>%s,p_wallet=>5)",(p[0],json.dumps(p[1]),p[4],p[8])).fetchone()[0];c.commit();c.close()
   oid=r if isinstance(r,int) else r['id'];before=self.snapshot();again=self.invoke(p,fn)
   self.assertEqual(str(again if isinstance(again,int) else again['id']),str(oid));p[2]=None;changed=self.invoke(p,fn)
   if fn=='place_order':self.assertEqual(changed['message'],'idempotency_mismatch')
   else:self.assertEqual(changed['status'],'conflict')
   self.assertEqual(before,self.snapshot());self.assertEqual(self.a.execute('select tip from orders where id=%s',(oid,)).fetchone()[0],0);self.consent()
  self.assertEqual(self.counts(),(4,4,-20,4))
 def historical(self,bound):
  if bound:Base.upgrade(self);self.policy(200,200)
  p=args('null01_historical');p[2]=None
  with self.actor() as c:r=call(c,p,'place_order104' if bound else 'place_order')
  oid=r['id'] if bound else r;self.consent();self.upgrade();self.policy(200,200);before=self.snapshot()
  for fn in ENTRIES:
   r=self.invoke(p,fn);self.assertEqual(str(r if isinstance(r,int) else r['id']),str(oid))
   if fn!='place_order':self.assertEqual(r['status'],'replayed' if bound else 'historical_recovered');self.assertEqual(r['input_match'],True if bound else None)
  self.assertEqual(before,self.snapshot());self.assertEqual(self.a.execute('select tip from orders').fetchone()[0],0);self.assertEqual(self.counts(),(1,1,-5,1 if bound else 0))
  if bound:
   p[2]=0;r=self.invoke(p);self.assertEqual(r['status'],'conflict');self.assertEqual(before,self.snapshot())
 def test_historical_raw_null_bound(self):self.historical(True)
 def test_historical_raw_null_unbound(self):self.historical(False)
 def test_closure_precedes_null_and_cannot_reopen(self):
  self.upgrade();self.policy(200,200);p=args('null01_closed');p[2]=None;r=self.invoke(p)
  self.assertTrue(r['closed']);self.assertEqual(r['reason'],'bad_value');before=self.snapshot()
  for fn in ENTRIES:
   again=self.invoke(p,fn)
   if fn=='place_order104':self.assertEqual(again['closure_id'],r['closure_id'])
   elif fn=='security_private.create_order103':self.assertEqual(again['message'],'attempt_closed')
   elif fn=='place_order':self.assertEqual(again['message'],'creation_rejected')
   else:self.assertEqual(again['status'],'rejected')
  p[2]=3;again=self.invoke(p);self.assertEqual(again['closure_id'],r['closure_id']);self.assertEqual(before,self.snapshot());self.assertEqual(self.counts(),(0,0,0,0))
 def test_auth_and_other_account_do_not_expose_historical_null(self):
  Base.upgrade(self);self.policy(200,200);p=args('null01_private');p[2]=None
  with self.actor() as c:self.assertEqual(call(c,p,'place_order104')['status'],'created')
  self.upgrade();before=self.snapshot()
  with self.actor('20000000-0000-4000-8000-000000000092') as c:r=call(c,p,'place_order104')
  self.assertEqual(r['status'],'rejected');self.assertNotIn('id',r);self.assertEqual(before,self.snapshot())
  c=self.tx(private=True);c.execute("select set_config('request.jwt.claims','{}',false)");r=self.outcome(c,p,'security_private.create_order103');c.close();self.assertEqual(r['message'],'auth');self.assertEqual(before,self.snapshot())
 def test_concurrent_null_and_zero_same_key(self):
  self.upgrade();self.policy(200,200);bar=threading.Barrier(2);out=[];errors=[]
  def run(tip):
   try:
    p=args('null01_race');p[2]=tip
    with self.actor() as c:bar.wait(5);out.append((tip,call(c,p,'place_order104')))
   except Exception as e:errors.append(repr(e))
  ts=[threading.Thread(target=run,args=(v,)) for v in [None,0]]
  for t in ts:t.start()
  for t in ts:t.join(15);self.assertFalse(t.is_alive())
  self.assertFalse(errors,errors);self.assertEqual(len(out),2)
  null=next(r for t,r in out if t is None);zero=next(r for t,r in out if t==0)
  if zero['status']=='created':self.assertEqual(null['status'],'conflict');self.assertEqual(self.counts(),(1,1,-5,1));self.assertEqual(self.rows(),0)
  else:self.assertEqual(zero['closure_id'],null['closure_id']);self.assertEqual(null['status'],'rejected');self.assertEqual(self.counts(),(0,0,0,0));self.assertEqual(self.rows(),1)
 def test_rejection_ack_before_after_commit_same_closure_no_spend(self):
  from tcp_proxy import CutProxy
  self.upgrade();self.policy(200,200)
  for mode in ['before','after']:
   p=args('null01_ack_'+mode);p[2]=None;prior=self.rows();proxy=CutProxy(mode);c=self.actor(port=proxy.port);r=call(c,p,'place_order104');self.assertEqual(r['status'],'rejected');self.assertTrue(r['closed']);proxy.arm=True
   with self.assertRaises((pg.OperationalError,pg.InterfaceError)):c.commit()
   c.close();proxy.join();self.assertTrue(proxy.cut)
   for _ in range(100):
    n=self.rows()
    if n==prior+(1 if mode=='after' else 0):break
    time.sleep(.01)
   self.assertEqual(n,prior+(1 if mode=='after' else 0))
   with self.actor() as c:state=c.execute('select order_request_status104(%s)',(p[8],)).fetchone()[0]
   self.assertEqual(state['status'],'rejected' if mode=='after' else 'unresolved')
   retry=self.invoke(p);self.assertTrue(retry['closed'])
   if mode=='after':self.assertEqual(retry['closure_id'],r['closure_id'])
   self.assertEqual(self.invoke(p)['closure_id'],retry['closure_id']);self.assertEqual(self.rows(),prior+1);self.assertEqual(self.counts(),(0,0,0,0))
 def test_historical_null_ack_then_upgrade_recovery(self):
  from tcp_proxy import CutProxy
  Base.upgrade(self);self.policy(200,200);p=args('null01_old_ack');p[2]=None;proxy=CutProxy('after');c=self.actor(port=proxy.port);r=call(c,p,'place_order104');self.assertEqual(r['status'],'created');proxy.arm=True
  with self.assertRaises((pg.OperationalError,pg.InterfaceError)):c.commit()
  c.close();proxy.join();self.upgrade();before=self.snapshot();got=self.invoke(p);self.assertEqual(got['status'],'replayed');self.assertEqual(got['id'],r['id']);self.assertEqual(before,self.snapshot());self.assertEqual(self.counts(),(1,1,-5,1))
 def test_null_keeps_106_isolation_contract(self):
  self.upgrade();self.policy(200,200)
  for level in ['read committed','read uncommitted','repeatable read','serializable']:
   for i,fn in enumerate(ENTRIES):
    p=args('null01_iso_'+level.replace(' ','_')+str(i));p[2]=None;before=self.snapshot();c=self.tx(level,fn.startswith('security_private.'));r=self.outcome(c,p,fn);c.close()
    self.assert_no_creation(r,level,fn);self.assertEqual(before,self.snapshot());self.assertEqual(self.counts(),(0,0,0,0))
 def test_null_rollback_reupgrade_history_and_closure(self):
  Base.upgrade(self);self.policy(200,200);old=args('null01_rollback_history');old[2]=None
  with self.actor() as c:r=call(c,old,'place_order104')
  self.upgrade();new=args('null01_rollback_closed');new[2]=None;closed=self.invoke(new);self.assertTrue(closed['closed']);before=self.snapshot();n=self.rows()
  self.a.execute(Path('tests/native104/rollback.sql').read_text());self.assertEqual(self.invoke(old)['id'],r['id']);self.assertEqual(self.invoke(new)['status'],'unresolved')
  with self.actor() as c:receipt=c.execute('select order_request_status104(%s)',(new[8],)).fetchone()[0]
  self.assertEqual(receipt['closure_id'],closed['closure_id'])
  fresh=args('null01_rollback_fresh');fresh[2]=None;self.assertEqual(self.invoke(fresh)['status'],'unresolved');self.assertEqual(before,self.snapshot())
  self.upgrade();self.assertEqual(self.invoke(old)['id'],r['id']);self.assertEqual(self.invoke(new)['closure_id'],closed['closure_id']);self.assertEqual(before,self.snapshot());self.assertEqual(self.rows(),n)
  self.assertEqual(self.invoke(fresh)['reason'],'bad_value');self.assertEqual(self.counts(),(1,1,-5,1))
if __name__=='__main__':
 names=[n for n in NullDecision.__dict__ if n.startswith('test_')]
 if os.environ.get('TIP02_NULL_BASELINE')=='yes':names=['test_new_null_rejected_all_entries_no_financial_effect']
 r=unittest.TextTestRunner(verbosity=2).run(unittest.TestSuite(NullDecision(n) for n in names))
 Path('tip02-null-results.json').write_text(json.dumps({'tests':r.testsRun,'passed':r.wasSuccessful(),'failures':[t.id() for t,_ in r.failures+r.errors]},indent=2));raise SystemExit(not r.wasSuccessful())
