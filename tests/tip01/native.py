"""TIP-01 behavioral tests. Disposable local PostgreSQL only; synthetic data."""
import os, json, unittest, threading, time, uuid
from decimal import Decimal
from pathlib import Path
assert os.environ.get('TIP01_ISOLATED') == 'yes'
assert os.environ.get('PGHOST') == '127.0.0.1'
ns = {'__name__': 'tip01_fixture'}
exec(compile(Path('tests/native106/native.py').read_text(), 'retained106', 'exec'), ns)
Base, call, args = ns['Isolation106'], ns['call'], ns['args']
ENTRIES = ns['ENTRIES']
psycopg=ns['psycopg']; B=ns['B']
def tipargs(key='tip01_default',extra=None):
 p=args(key,extra);p[2]=20;return p
class Tip01(Base):
 def upgrade(self):
  super().upgrade()
  if os.environ.get('TIP01_BASELINE') != 'yes':
   self.a.execute(Path('tests/tip01/acceptance.sql').read_text())
 def test_tip20_persisted_all_entries(self):
  self.upgrade(); self.policy(100,100)
  for i, fn in enumerate(ENTRIES):
   with self.subTest(entry=fn):
    p=args('tip01_twenty_'+str(i)); p[2]=20
    c=self.tx(private=fn.startswith('security_private.'))
    r=self.outcome(c,p,fn); c.close()
    oid=r if isinstance(r,int) else r.get('id')
    self.assertIsNotNone(oid, r)
    self.consent()
    self.assertEqual(self.a.execute('select tip,total,commission,driver_payout,wallet_used,cash_platform_share,cash_driver_delivery_share from orders where id=%s',(oid,)).fetchone(),(20,42,2,21.5,5,.5,1.5))
 def test_tip20_closed_key_all_entries_all_isolations(self):
  self.upgrade();self.policy(100,100)
  for level in ns['LEVELS']:
   for i,fn in enumerate(ENTRIES):
    key='tip01_closed_'+level.replace(' ','_')+str(i)
    c=self.tx(level,fn.startswith('security_private.'));self.assertTrue(self.reject(key)['closed'])
    before=self.snapshot();closures=self.rows();r=self.outcome(c,tipargs(key),fn);c.close()
    self.assert_no_creation(r,level,fn);self.assertEqual(before,self.snapshot());self.assertEqual(self.rows(),closures);self.assertEqual(self.counts(),(0,0,0,0))
 def test_decimal_money_and_floor_unchanged(self):
  self.upgrade();self.policy(100,100)
  self.a.execute('update menu_items set price=20.05');self.a.execute('update stores set discount_pct=10')
  p=tipargs();p[10]=Decimal('5.005')
  with self.actor() as c:r=call(c,p,'place_order104')
  self.assertEqual(r['status'],'created')
  self.assertEqual(self.a.execute('select subtotal,discount,total,commission,driver_payout,wallet_used from orders').fetchone(),tuple(map(Decimal,['20.05','2.01','40.04','1.80','21.50','5.01'])))
  before=self.snapshot()
  with self.actor() as c:self.assertEqual(call(c,p,'place_order104')['status'],'replayed')
  self.assertEqual(before,self.snapshot());self.assertEqual(self.counts(),(1,1,Decimal('-5.01'),1));self.consent()
  self.a.execute('update menu_items set price=1');self.a.execute('update stores set discount_pct=0')
  for tip,total in [(0,5),(20,23)]:
   p=tipargs('tip01_floor_'+str(tip));p[2]=tip;p[10]=0
   with self.actor() as c:r=call(c,p,'place_order104')
   self.assertEqual(r['status'],'created');self.assertEqual(self.a.execute('select total,commission from orders where id=%s',(r['id'],)).fetchone(),(total,Decimal('.10')));self.consent()
 def test_replay_conflict_and_numeric_equivalence(self):
  self.upgrade();self.policy(100,100)
  for i,fn in enumerate(ENTRIES):
   p=tipargs('tip01_replay_'+str(i));c=self.tx(private=fn.startswith('security_private.'));r=self.outcome(c,p,fn);c.close()
   oid=r if isinstance(r,int) else r['id'];before=self.snapshot()
   p[2]=Decimal('20.00');c=self.tx(private=fn.startswith('security_private.'));again=self.outcome(c,p,fn);c.close()
   self.assertEqual(str(again if isinstance(again,int) else again['id']),str(oid))
   p[2]=10;c=self.tx(private=fn.startswith('security_private.'));changed=self.outcome(c,p,fn);c.close()
   if fn=='place_order':self.assertEqual(changed['message'],'idempotency_mismatch')
   else:self.assertEqual(changed['status'],'conflict')
   self.assertEqual(self.snapshot(),before);self.consent()
  self.assertEqual(self.counts(),(4,4,-20,4))
 def test_preupgrade_bound_orders_never_repriced(self):
  Base.upgrade(self);self.policy(100,100);saved=[]
  for i,tip in enumerate([3,20]):
   p=tipargs('tip01_old_bound_'+str(i));p[2]=tip
   with self.actor() as c:r=call(c,p,'place_order104')
   self.assertEqual(self.a.execute('select tip from orders where id=%s',(r['id'],)).fetchone()[0],3 if tip==3 else 0)
   saved.append((p,r['id']));self.consent()
  before=self.snapshot();self.upgrade()
  for p,oid in saved:
   for fn in ENTRIES:
    c=self.tx(private=fn.startswith('security_private.'));r=self.outcome(c,p,fn);c.close()
    self.assertEqual(str(r if isinstance(r,int) else r['id']),str(oid))
  self.assertEqual(before,self.snapshot())
 def test_historical_tip3_and_sent20_stored0_readonly(self):
  saved=[]
  for i,tip in enumerate([3,20]):
   p=tipargs('tip01_legacy_'+str(i));p[2]=tip
   with self.actor() as c:oid=call(c,p,'place_order')
   saved.append((p,oid));self.consent()
  self.upgrade();before=self.snapshot()
  for p,oid in saved:
   with self.actor() as c:r=call(c,p,'place_order104')
   self.assertEqual(r['status'],'historical_recovered');self.assertIsNone(r['input_match']);self.assertEqual(int(r['id']),oid)
  self.assertEqual(before,self.snapshot());self.assertEqual(self.counts(),(2,2,-10,0))
  self.assertEqual(self.a.execute('select tip from orders order by id').fetchall(),[(3,),(0,)])
 def test_unresolved_contract_inputs_preserve_106_behavior(self):
  Base.upgrade(self);self.policy(100,100);baseline=[]
  for i,tip in enumerate([3,None,7,-1]):
   p=tipargs('tip01_compat_before_'+str(i));p[2]=tip
   with self.actor() as c:r=call(c,p,'place_order104')
   self.assertEqual(r['status'],'created');baseline.append(self.a.execute('select tip,total,commission,driver_payout from orders where id=%s',(r['id'],)).fetchone());self.consent()
  self.upgrade()
  for i,tip in enumerate([3,None,7,-1]):
   p=tipargs('tip01_compat_after_'+str(i));p[2]=tip
   with self.actor() as c:r=call(c,p,'place_order104')
   self.assertEqual(r['status'],'created');self.assertEqual(self.a.execute('select tip,total,commission,driver_payout from orders where id=%s',(r['id'],)).fetchone(),baseline[i]);self.consent()
   self.a.execute("update orders set status='delivered' where id=%s",(r['id'],))
 def test_three_concurrent_retries_one_spend(self):
  self.upgrade();self.policy(100,100);barrier=threading.Barrier(3);out=[];errors=[]
  def run():
   try:
    with self.actor() as c:barrier.wait(timeout=10);out.append(call(c,tipargs(),'place_order104'))
   except Exception as e:errors.append(repr(e))
  ts=[threading.Thread(target=run) for _ in range(3)]
  for t in ts:t.start()
  for t in ts:t.join(20);self.assertFalse(t.is_alive())
  self.assertFalse(errors,errors);self.assertEqual(len(out),3);self.assertEqual(len({r['id'] for r in out}),1)
  self.assertEqual(sorted(r['status'] for r in out),['created','replayed','replayed']);self.assertEqual(self.counts(),(1,1,-5,1))
 def test_tip20_tcp_before_after_commit(self):
  self.upgrade();self.policy(100,100)
  from tcp_proxy import CutProxy
  for mode in ['before','after']:
   self.consent();proxy=CutProxy(mode);c=self.actor(port=proxy.port);p=tipargs('tip01_tcp_'+mode)
   self.assertEqual(call(c,p,'place_order104')['status'],'created');proxy.arm=True
   with self.assertRaises((psycopg.OperationalError,psycopg.InterfaceError)):c.commit()
   c.close();proxy.join();self.assertTrue(proxy.cut)
   for _ in range(100):
    count=self.a.execute('select count(*) from orders where client_key=%s',(p[8],)).fetchone()[0]
    if count==(1 if mode=='after' else 0):break
    time.sleep(.01)
   self.assertEqual(count,1 if mode=='after' else 0)
   with self.actor() as c:r=call(c,p,'place_order104')
   self.assertEqual(r['status'],'replayed' if mode=='after' else 'created')
   self.assertEqual(self.a.execute('select tip,total from orders where id=%s',(r['id'],)).fetchone(),(20,42))
   self.assertEqual(self.a.execute("select count(*),sum(amount) from wallet_entries where kind='spend' and order_id=%s",(r['id'],)).fetchone(),(1,-5))
 def test_tip20_rollback_reupgrade_no_repricing(self):
  self.upgrade();self.policy(100,100)
  with self.actor() as c:r=call(c,tipargs(),'place_order104')
  self.assertEqual(r['status'],'created');before=self.snapshot()
  self.a.execute(Path('tests/native104/rollback.sql').read_text())
  with self.actor() as c:
   self.assertEqual(call(c,tipargs(),'place_order104')['id'],r['id'])
   self.assertEqual(call(c,tipargs('tip01_new_during_rollback'),'place_order104')['status'],'unresolved')
  self.assertEqual(before,self.snapshot());self.upgrade()
  with self.actor() as c:self.assertEqual(call(c,tipargs(),'place_order104')['id'],r['id'])
  self.assertEqual(before,self.snapshot());self.consent()
  with self.actor() as c:self.assertEqual(call(c,tipargs('tip01_new_after_reupgrade'),'place_order104')['status'],'created')
  self.assertEqual(self.a.execute('select tip from orders order by id').fetchall(),[(20,),(20,)])
 def test_tip20_binding_failure_promo_points_wallet_atomic(self):
  self.upgrade();self.policy(100,100);self.a.execute(Path('tests/native103/dependencies.sql').read_text())
  self.a.execute("insert into promo_codes values('TIP01',true,null,null,0,1,'fixed',5)");self.a.execute("insert into promo_attempts values(%s,true,'TIP01',now())",(B,))
  self.a.execute("insert into loyalty_lots(user_id,points_left,expires_at)values(%s,100,now()+interval '1 day')",(B,))
  p=tipargs();p[7]='TIP01';p[11]=100
  self.a.execute("create function security_private.failtip() returns trigger language plpgsql as $$begin raise exception 'synthetic_binding_failure';end$$;create trigger failtip before insert on security_private.order_request_fingerprints103 for each row execute function security_private.failtip()")
  before=self.snapshot()
  with self.actor() as c:self.assertEqual(call(c,p,'place_order103')['status'],'rejected')
  self.assertEqual(before,self.snapshot());self.assertEqual(self.a.execute('select points_left from loyalty_lots').fetchone()[0],100);self.assertEqual(self.a.execute('select count(*) from loyalty_ledger').fetchone()[0],0)
  self.a.execute('drop trigger failtip on security_private.order_request_fingerprints103')
  with self.actor() as c:r=call(c,p,'place_order104')
  self.assertEqual(r['status'],'created')
  self.assertEqual(self.a.execute('select tip,promo_discount,points_used,points_value,total,commission,driver_payout,wallet_used from orders').fetchone(),(20,5,100,10,27,2,Decimal('21.5'),5))
  before=self.snapshot()
  with self.actor() as c:self.assertEqual(call(c,p,'place_order104')['status'],'replayed')
  self.assertEqual(before,self.snapshot());self.assertEqual(self.a.execute('select count(*),sum(points) from loyalty_ledger').fetchone(),(1,-100));self.assertEqual(self.counts(),(1,1,-5,1))
def matrix_case(fn,mode):
 def test(self):
  self.upgrade();self.policy(100,100)
  for i,tip in enumerate([0,5,10,20]):
   extra=None
   if mode=='group':
    gid=str(uuid.uuid4());self.a.execute("insert into group_orders(id,host_id,status,store_id,expires_at)values(%s,%s,'open',%s,now()+interval '1 hour')",(gid,B,args()[0]));extra={'group':gid}
   elif mode=='scheduled':extra={'at':self.a.execute("select now()+interval '1 hour'").fetchone()[0].isoformat()}
   p=args('tip01_matrix_'+str(i),extra);p[2]=tip;c=self.tx(private=fn.startswith('security_private.'));r=self.outcome(c,p,fn);c.close()
   oid=r if isinstance(r,int) else r.get('id');self.assertIsNotNone(oid,r)
   # Synthetic dish20 + delivery2, commission2, driver delivery1.50, wallet5.
   expected={0:(0,22,2,Decimal('1.5')),5:(5,27,2,Decimal('6.5')),10:(10,32,2,Decimal('11.5')),20:(20,42,2,Decimal('21.5'))}[tip]
   self.assertEqual(self.a.execute('select tip,total,commission,driver_payout from orders where id=%s',(oid,)).fetchone(),expected)
   before=self.snapshot();c=self.tx(private=fn.startswith('security_private.'));again=self.outcome(c,p,fn);c.close();self.assertEqual(str(again if isinstance(again,int) else again['id']),str(oid));self.assertEqual(before,self.snapshot());self.consent()
  self.assertEqual(self.counts(),(4,4,-20,4))
 return test
for entry in ENTRIES:
 for mode in ['normal','group','scheduled']:setattr(Tip01,'test_matrix_'+entry.replace('.','_')+'_'+mode,matrix_case(entry,mode))
if __name__ == '__main__':
 suite=unittest.TestSuite(Tip01(n) for n in Tip01.__dict__ if n.startswith('test_') and (os.environ.get('TIP01_BASELINE')!='yes' or n=='test_tip20_persisted_all_entries'))
 result=unittest.TextTestRunner(verbosity=2).run(suite)
 Path('tip01-results.json').write_text(json.dumps({'passed':result.wasSuccessful(),'tests':result.testsRun,'failures':[t.id() for t,_ in result.failures+result.errors]},indent=2))
 raise SystemExit(not result.wasSuccessful())
