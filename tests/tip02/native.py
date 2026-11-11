"""Manual-tip contract on disposable PostgreSQL17.6; synthetic fixtures only."""
import os,json,unittest
from decimal import Decimal
from pathlib import Path
assert os.environ.get('TIP02_ISOLATED')=='yes'
ns={'__name__':'tip01_base'}
exec(compile(Path('tests/tip01/native.py').read_text(),'tip01_base','exec'),ns)
Base=ns['Tip01'];call=ns['call'];args=ns['args'];ENTRIES=ns['ENTRIES'];pg=ns['psycopg']
class ManualTip(Base):
 def upgrade(self):
  super().upgrade()
  if os.environ.get('TIP02_BASELINE')!='yes':self.a.execute(Path('tests/tip02/acceptance.sql').read_text())
 def test_manual_boundaries_all_entries(self):
  self.upgrade();self.policy(200,200)
  for i,fn in enumerate(ENTRIES):
   for tip in [0,1,3,5,10,20,99,100]:
    with self.subTest(entry=fn,tip=tip):
     p=args('tip02_'+str(i)+'_'+str(tip));p[2]=tip;p[10]=0
     c=self.tx(private=fn.startswith('security_private.'));r=self.outcome(c,p,fn);c.close();oid=r if isinstance(r,int) else r.get('id');self.assertIsNotNone(oid,r)
     self.consent();self.a.execute("update orders set status='delivered',created_at=now()-interval '2 hours' where id=%s",(oid,))
     self.assertEqual(self.a.execute('select tip,total,commission,driver_payout from orders where id=%s',(oid,)).fetchone(),(tip,22+tip,2,Decimal('1.50')+tip))
 def test_invalid_numeric_rejected_without_effect(self):
  self.upgrade();self.policy(200,200)
  for i,fn in enumerate(ENTRIES):
   for j,tip in enumerate(['0.5','10.5','-1','101','NaN','Infinity','-Infinity']):
    p=args('tip02_invalid_'+str(i)+'_'+str(j));p[2]=tip;before=self.snapshot()
    c=self.tx(private=fn.startswith('security_private.'));r=self.outcome(c,p,fn);c.close()
    if fn in ['place_order','security_private.create_order103']:self.assertEqual(r['message'],'bad_value')
    else:self.assertEqual(r['status'],'rejected');self.assertEqual(r['reason'],'bad_value')
    self.assertEqual(before,self.snapshot());self.assertEqual(self.counts(),(0,0,0,0))
 def test_nonnumeric_wire_value_rejected_by_numeric_signature(self):
  self.upgrade();before=self.snapshot()
  for fn in ENTRIES:
   for value in ['abc','',True,{'tip':3}]:
    p=args('tip02_bad_text');p[2]=json.dumps(value) if not isinstance(value,str) else value
    c=self.tx(private=fn.startswith('security_private.'));r=self.outcome(c,p,fn);c.close();self.assertEqual(r['sqlstate'],'22P02')
  self.assertEqual(before,self.snapshot());self.assertEqual(self.rows(),0)
 def test_historical_invalid_payload_recovered_before_new_validation(self):
  Base.upgrade(self);self.policy(200,200);saved=[]
  for i,value in enumerate([1,'10.5',-1,101,None]):
   p=args('tip02_old_'+str(i));p[2]=value
   with self.actor() as c:r=call(c,p,'place_order104')
   self.assertEqual(r['status'],'created');self.assertEqual(self.a.execute('select tip from orders where id=%s',(r['id'],)).fetchone()[0],0);saved.append((p,r['id']));self.consent()
  self.upgrade();before=self.snapshot()
  for p,oid in saved:
   for fn in ENTRIES:
    c=self.tx(private=fn.startswith('security_private.'));r=self.outcome(c,p,fn);c.close();self.assertEqual(str(r if isinstance(r,int) else r['id']),str(oid))
  self.assertEqual(before,self.snapshot())
 def test_default_and_explicit_null_are_distinct_fingerprints(self):
  self.upgrade();self.policy(200,200)
  # Numeric default remains0; explicit NULL keeps pre-existing behavior, not new policy acceptance.
  p=args('tip02_explicit_null');p[2]=None
  with self.actor() as c:r=call(c,p,'place_order104')
  self.assertEqual(r['status'],'created');self.assertEqual(self.a.execute('select tip from orders').fetchone()[0],0)
  changed=list(p);changed[2]=0
  with self.actor() as c:self.assertEqual(call(c,changed,'place_order104')['status'],'conflict')
  self.consent()
  with self.actor() as c:r=c.execute("select place_order104(p_store=>%s,p_items=>%s::jsonb,p_address=>'synthetic',p_lat=>38.5,p_lng=>68.7,p_key=>'tip02_omitted')",(p[0],json.dumps(p[1]))).fetchone()[0]
  self.assertEqual(r['status'],'created');self.assertEqual(self.a.execute('select tip from orders where id=%s',(r['id'],)).fetchone()[0],0)
 def test_manual_replay_changed_tip_group_schedule_and_wallet(self):
  self.upgrade();self.policy(200,200)
  for i,mode in enumerate(['normal','group','scheduled']):
   extra=None
   if mode=='group':self.group();extra={'group':'60000000-0000-4000-8000-000000000092'}
   if mode=='scheduled':extra={'at':self.a.execute("select now()+interval '1 hour'").fetchone()[0].isoformat()}
   p=args('tip02_mode_'+mode,extra);p[2]=[1,3,100][i]
   with self.actor() as c:r=call(c,p,'place_order104')
   self.assertEqual(r['status'],'created');before=self.snapshot()
   with self.actor() as c:self.assertEqual(call(c,p,'place_order104')['id'],r['id'])
   q=list(p);q[2]=99
   with self.actor() as c:self.assertEqual(call(c,q,'place_order104')['status'],'conflict')
   self.assertEqual(before,self.snapshot());self.consent()
  self.assertEqual(self.counts(),(3,3,-15,3))
 def test_manual99_rollback_reupgrade_and_invalid_closed_key(self):
  self.upgrade();self.policy(200,200);p=args('tip02_rollback99');p[2]=99
  with self.actor() as c:r=call(c,p,'place_order104')
  self.assertEqual(r['status'],'created');self.consent();before=self.snapshot()
  self.a.execute(Path('tests/native104/rollback.sql').read_text())
  with self.actor() as c:self.assertEqual(call(c,p,'place_order104')['id'],r['id'])
  self.assertEqual(before,self.snapshot());self.upgrade()
  with self.actor() as c:self.assertEqual(call(c,p,'place_order104')['id'],r['id'])
  self.assertEqual(before,self.snapshot())
  invalid=args('tip02_closed_bad');invalid[2]=101
  with self.actor() as c:closed=call(c,invalid,'place_order104')
  self.assertEqual(closed['status'],'rejected');self.assertTrue(closed['closed']);before=self.snapshot();invalid[2]=3
  with self.actor() as c:again=call(c,invalid,'place_order104')
  self.assertEqual(again['closure_id'],closed['closure_id']);self.assertEqual(before,self.snapshot());self.assertEqual(self.counts(),(1,1,-5,1))
if __name__=='__main__':
 names=[n for n in ManualTip.__dict__ if n.startswith('test_')]
 if os.environ.get('TIP02_BASELINE')=='yes':names=['test_manual_boundaries_all_entries']
 r=unittest.TextTestRunner(verbosity=2).run(unittest.TestSuite(ManualTip(n) for n in names))
 Path('tip02-native.json').write_text(json.dumps({'tests':r.testsRun,'passed':r.wasSuccessful(),'failures':[t.id() for t,_ in r.failures+r.errors]},indent=2));raise SystemExit(not r.wasSuccessful())
