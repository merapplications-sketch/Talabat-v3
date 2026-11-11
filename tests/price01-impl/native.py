"""Real PostgreSQL17.6 / synthetic local fixture. Only PRICE01 affected tests."""
import copy,json,os,unittest,threading,time
from pathlib import Path
from decimal import Decimal
assert os.environ.get('PRICE01_ISOLATED')=='yes'
ns={'__name__':'price01_base'}
exec(compile(Path('tests/tip02-null01/native.py').read_text(),'retained-null01','exec'),ns)
Base,call,args,ENTRIES,pg=(ns[k] for k in ['NullDecision','call','args','ENTRIES','pg'])
B='10000000-0000-4000-8000-000000000092';I='40000000-0000-4000-8000-000000000092'
OP='70000000-0000-4000-8000-000000000092';OG='80000000-0000-4000-8000-000000000092'
def amount(n):return format(Decimal(str(n)),'f')
def proof(price=20,qty=1,tip=0,wallet=5,discount=0,hh=0,promo=0,points=0,fee=2,options=None,item=I):
 # Independent decimal oracle for synthetic inputs; never calls candidate pricing.
 options=options or [];unit=Decimal(str(price))+sum(Decimal(o['price_delta']) for o in options)
 line=unit*qty;rd=(line*Decimal(discount)/100).quantize(Decimal('.01'),rounding='ROUND_HALF_UP')
 ad=(line*Decimal(max(discount,hh))/100).quantize(Decimal('.01'),rounding='ROUND_HALF_UP');hd=ad-rd
 total=max(Decimal(5),line-ad-Decimal(str(promo))-Decimal(str(points))+Decimal(str(fee))+Decimal(str(tip)))
 return {'version':1,'lines':[{'item_id':item,'qty':qty,'base_price':amount(price),'options':options,'unit_price':amount(unit),'restaurant_discount':amount(rd),'happy_hour_discount':amount(hd),'net_items':amount(line-ad)}],
 'totals':dict(zip(['subtotal','restaurant_discount','happy_hour_discount','promo_discount','points_value','delivery_fee','tip','wallet_used','cash_due','total'],map(amount,[line,rd,hd,promo,points,fee,tip,wallet,total-Decimal(str(wallet)),total])))}
def request(key='price01_test',consent=None,extra=None):
 p=args(key,dict(extra or {}));p[12]['price01']=copy.deepcopy(consent if consent is not None else proof());return p
class Price01(Base):
 def setUp(self):
  super().setUp();self.assertEqual(self.a.execute('show server_version_num').fetchone()[0],'170006');self.upgrade();self.policy(200,200)
 def upgrade(self):
  super().upgrade()
  if os.environ.get('PRICE01_BASELINE')!='yes':self.a.execute(Path('tests/price01-impl/candidate.sql').read_text())
 def reject_price(self,p,fn='place_order104',reason='price_changed'):
  before=self.snapshot();r=self.invoke(p,fn)
  if fn in ['place_order','security_private.create_order103']:self.assertIsInstance(r,dict,'must reject, not return a saved order');self.assertEqual(r.get('message'),reason,r)
  else:self.assertEqual(r['status'],'rejected',r);self.assertEqual(r['reason'],reason,r)
  if fn=='place_order104':self.assertTrue(r['closed']);self.assertTrue(r['no_effects'])
  self.assertEqual(self.snapshot(),before);return r
 def retire(self):self.consent();self.a.execute("update orders set status='delivered',created_at=now()-interval '2 hours'")
 def test_01_up_down_all_entries_atomic(self):
  for n,fn in enumerate(ENTRIES):
   for price in [30,10]:
    self.a.execute('update menu_items set price=%s',(price,));r=self.reject_price(request('price01_drift_'+str(n)+'_'+str(price)),fn)
    if fn=='place_order104':self.assertEqual(Decimal(r['price_review']['totals']['total']),price+2)
  self.assertEqual(self.counts(),(0,0,0,0))
 def test_02_missing_consent_all_entries(self):
  for n,fn in enumerate(ENTRIES):self.reject_price(args('price01_missing_'+str(n)),fn,'price_confirmation_required')
  self.assertEqual(self.counts(),(0,0,0,0))
 def test_03_equal_total_opposite_changes(self):
  j='41000000-0000-4000-8000-000000000092'
  self.a.execute('insert into menu_items select %s,store_id,name,20,available,approved,discount_pct from menu_items where id=%s',(j,I))
  pr=proof();pr['lines']+=proof(item=j)['lines'];pr['totals'].update(subtotal='40',total='42',cash_due='37')
  p=request('price01_offset',pr);p[1].append({'item_id':j,'qty':1,'options':[]})
  self.a.execute('update menu_items set price=case when id=%s then 25 else 15 end',(I,))
  r=self.reject_price(p);self.assertEqual(Decimal(r['price_review']['totals']['total']),42)
 def test_04_exact_acceptance_all_entries_tip99_once(self):
  for n,fn in enumerate(ENTRIES):
   p=request('price01_accept_'+str(n),proof(tip=99));p[2]=99;r=self.invoke(p,fn);oid=r if isinstance(r,int) else r.get('id');self.assertIsNotNone(oid,r)
   self.assertEqual(self.a.execute('select total,tip,commission,driver_payout,wallet_used from orders where id=%s',(oid,)).fetchone(),(121,99,2,Decimal('100.5'),5))
   before=self.snapshot();again=self.invoke(p,fn);self.assertEqual(str(again if isinstance(again,int) else again['id']),str(oid));self.assertEqual(before,self.snapshot());self.retire()
  self.assertEqual(self.counts(),(4,4,-20,4))
 def test_05_invalid_evidence_no_effect(self):
  cases=[]
  for value in [None,{},[],{'version':2},'bad']:
   p=request();p[12]['price01']=value;cases.append(p)
  for value in ['NaN','Infinity','1e1',' 20','20 ',20,True,'1'*129]:
   p=request();p[12]['price01']['lines'][0]['base_price']=value;cases.append(p)
  p=request();p[12]['price01']['private_address']='must not echo';cases.append(p)
  for n,p in enumerate(cases):
   p[8]='price01_invalid_'+str(n);r=self.invoke(p);self.assertEqual(r['status'],'rejected');self.assertNotIn('price_review',r);self.assertNotIn('id',r)
  self.assertEqual(self.counts(),(0,0,0,0))
 def test_06_options_discount_hh_and_promo(self):
  self.a.execute('insert into item_option_groups values(%s,%s,\'synthetic\',1,false,0,now())',(OG,I));self.a.execute('insert into item_options values(%s,%s,\'synthetic\',3,true,0)',(OP,OG))
  for delta in [8,1]:
   self.a.execute('update item_options set price_delta=%s',(delta,));p=request('price01_opt_'+str(delta),proof(options=[{'id':OP,'price_delta':'3'}]));p[1][0]['options']=[OP]
   r=self.reject_price(p);self.assertEqual(Decimal(r['price_review']['totals']['total']),22+delta)
  for table in ['stores','menu_items']:
   for d in [25,0]:
    self.a.execute('update stores set discount_pct=0');self.a.execute('update menu_items set discount_pct=0');self.a.execute('update '+table+' set discount_pct=%s',(d,));self.reject_price(request('price01_disc_'+table+str(d),proof(discount=10)))
  self.a.execute('update stores set discount_pct=0');self.a.execute('update menu_items set discount_pct=0')
  self.a.execute('create or replace function happy_hour_pct(uuid) returns int language sql as $$select 25$$')
  self.reject_price(request('price01_hh',proof(hh=10)))
  self.a.execute('create or replace function happy_hour_pct(uuid) returns int language sql as $$select 0$$')
  self.a.execute(Path('tests/native103/dependencies.sql').read_text());self.a.execute("insert into promo_codes values('PRICE01',true,null,null,0,null,'fixed',8)");self.a.execute("insert into promo_attempts values(%s,true,'PRICE01',now())",(B,))
  p=request('price01_promo',proof(promo=5));p[7]='PRICE01';r=self.reject_price(p);self.assertEqual(r['price_review']['totals']['promo_discount'],'8');self.assertEqual(self.counts(),(0,0,0,0))
 def test_07_precision_no_tolerance_and_numeric_scale(self):
  self.a.execute('update menu_items set price=20.0000001');self.reject_price(request('price01_precision'))
  self.a.execute('update menu_items set price=20');pr=proof();pr['lines'][0]['base_price']='20.0000';r=self.invoke(request('price01_scale',pr));self.assertEqual(r['status'],'created')
 def test_08_final_persisted_mutation_is_rolled_back(self):
  self.a.execute("create function security_private.price01_fault() returns trigger language plpgsql as $$begin update order_items set price=price+1 where order_id=NEW.order_id;return NEW;end$$;create trigger price01_fault after insert on security_private.order_request_fingerprints103 for each row execute function security_private.price01_fault()")
  self.reject_price(request('price01_final'));self.assertEqual(self.counts(),(0,0,0,0))
 def test_09_points_promo_wallet_atomicity_and_acceptance(self):
  self.a.execute(Path('tests/native103/dependencies.sql').read_text());self.a.execute("insert into promo_codes values('PRICE01',true,null,null,0,1,'fixed',5)");self.a.execute("insert into promo_attempts values(%s,true,'PRICE01',now())",(B,));self.a.execute("insert into loyalty_lots(user_id,points_left,expires_at)values(%s,100,now()+interval '1 day')",(B,))
  p=request('price01_money',proof(points=10,promo=5));p[7]='PRICE01';p[11]=100
  self.a.execute('update menu_items set price=30');r=self.reject_price(p);self.assertEqual(self.a.execute('select points_left from loyalty_lots').fetchone()[0],100);self.assertEqual(self.a.execute('select count(*) from loyalty_ledger').fetchone()[0],0)
  p[8]='price01_money_approved';p[12]['price01']=proof(price=30,points=10,promo=5);r=self.invoke(p);self.assertEqual(r['status'],'created');self.assertEqual(self.a.execute('select points_left from loyalty_lots').fetchone()[0],0);self.assertEqual(self.a.execute('select count(*),sum(points) from loyalty_ledger').fetchone(),(1,-100));self.assertEqual(self.a.execute('select total,wallet_used,commission from orders').fetchone(),(17,5,3));self.assertEqual(self.counts(),(1,1,-5,1))
 def test_10_bound_and_unbound_history_null_tip3_and_ack(self):
  # Original writer first, then candidate upgrade. Never synthesize old bindings.
  for bound in [False,True]:
   # Bound TIP02 predates explicit-NULL rejection; old rawNULL/stored0 is preserved.
   ns['Base'].upgrade(self)
   for n,tip in enumerate([None,3]):
    p=args('price01_history_'+str(bound)+str(n));p[2]=tip
    if not bound:
     # Use existing native98 creator body (no version marker/binding), original public source.
     original=Path('tests/native98/setup.sql').read_text();body=original[original.index('CREATE OR REPLACE FUNCTION public.place_order('):original.index('insert into profiles values')]
     self.a.execute(body)
    with self.actor() as c:r=call(c,p,'place_order104' if bound else 'place_order')
    oid=r['id'] if bound else r;self.retire();self.upgrade();before=self.snapshot();self.a.execute('update menu_items set price=45')
    for fn in ENTRIES:
     got=self.invoke(p,fn);self.assertEqual(str(got if isinstance(got,int) else got['id']),str(oid))
    self.assertEqual(before,self.snapshot());self.a.execute('update menu_items set price=20');ns['Base'].upgrade(self)
   self.upgrade()
 def test_11_tcp_before_after_commit_then_price_change(self):
  from tcp_proxy import CutProxy
  for mode in ['before','after']:
   self.a.execute('update menu_items set price=20');p=request('price01_tcp_'+mode);proxy=CutProxy(mode);c=self.actor(port=proxy.port);r=call(c,p,'place_order104');self.assertEqual(r['status'],'created');proxy.arm=True
   with self.assertRaises((pg.OperationalError,pg.InterfaceError)):c.commit()
   c.close();proxy.join();self.assertTrue(proxy.cut)
   for _ in range(100):
    n=self.a.execute('select count(*) from orders where client_key=%s',(p[8],)).fetchone()[0]
    if n==(1 if mode=='after' else 0):break
    time.sleep(.01)
   self.assertEqual(n,1 if mode=='after' else 0);self.a.execute('update menu_items set price=30')
   if mode=='before':self.reject_price(p)
   else:
    before=self.snapshot();got=self.invoke(p);self.assertEqual(got['status'],'replayed');self.assertEqual(got['id'],r['id']);self.assertEqual(before,self.snapshot());self.retire()
  self.assertEqual(self.counts(),(1,1,-5,1))
 def test_12_concurrent_same_key_one_debit(self):
  barrier=threading.Barrier(3);out=[];errors=[];p=request('price01_race')
  def run():
   try:barrier.wait(5);out.append(self.invoke(p))
   except Exception as e:errors.append(str(e))
  ts=[threading.Thread(target=run) for _ in range(3)]
  for t in ts:t.start()
  for t in ts:t.join(15);self.assertFalse(t.is_alive())
  self.assertFalse(errors,errors);self.assertEqual(sorted(r['status'] for r in out),['created','replayed','replayed']);self.assertEqual(self.counts(),(1,1,-5,1))
 def test_13_lock_wait_price_change_and_closed_key(self):
  hold=pg.connect(dbname='candidate103');hold.execute('select id from profiles where id=%s for update',(B,));c=self.actor();out={};p=request('price01_wait')
  t=threading.Thread(target=lambda:out.update(r=self.outcome(c,p,'place_order104')));t.start()
  try:
   blocked=False
   for _ in range(200):
    blocked=hold.info.backend_pid in self.a.execute('select pg_blocking_pids(%s)',(c.info.backend_pid,)).fetchone()[0]
    if blocked:break
    time.sleep(.01)
   self.assertTrue(blocked);self.a.execute('update menu_items set price=35');hold.commit();t.join(15);self.assertFalse(t.is_alive());self.assertEqual(out['r']['reason'],'price_changed');self.assertTrue(out['r']['closed'])
  finally:hold.rollback();hold.close();t.join(16);c.close()
  p[12]['price01']=proof(price=35)
  for fn in ENTRIES:
   r=self.invoke(p,fn);self.assertFalse(isinstance(r,int));self.assertNotIn('id',r)
  self.assertEqual(self.counts(),(0,0,0,0));self.assertEqual(self.rows(),1)
 def test_14_isolation_all_entries_and_rollback_reupgrade(self):
  p=request('price01_saved');r=self.invoke(p);self.assertEqual(r['status'],'created');before=self.snapshot()
  self.a.execute(Path('tests/price01-impl/rollback.sql').read_text())
  for fn in ENTRIES:
   got=self.invoke(p,fn);self.assertEqual(str(got if isinstance(got,int) else got['id']),r['id'])
   got=self.invoke(request('price01_unseen'),fn);self.assertFalse(isinstance(got,int));self.assertNotIn('id',got)
  self.assertEqual(before,self.snapshot());self.upgrade()
  for level in ['repeatable read','serializable']:
   for fn in ENTRIES:
    c=self.tx(level,fn.startswith('security_private.'));got=self.outcome(c,request('price01_iso'),fn);c.close();self.assert_no_creation(got,level,fn)
  self.assertEqual(before,self.snapshot());self.retire()
  for n,fn in enumerate(ENTRIES):
   c=self.tx('read uncommitted',fn.startswith('security_private.'));got=self.outcome(c,request('price01_ru_'+str(n)),fn);c.close();self.assertTrue(isinstance(got,int) or got['status']=='created');self.retire()
 def test_15_group_schedule_null_and_fingerprint_conflict(self):
  self.group()
  for n,extra in enumerate([{}, {'group':'60000000-0000-4000-8000-000000000092'}, {'at':self.a.execute("select now()+interval '1 hour'").fetchone()[0].isoformat()}]):
   p=request('price01_mode_'+str(n),extra=extra);r=self.invoke(p);self.assertEqual(r['status'],'created');before=self.snapshot();changed=copy.deepcopy(p);changed[12]['price01']['totals']['tip']='1';self.assertEqual(self.invoke(changed)['status'],'conflict');self.assertEqual(self.invoke(p)['id'],r['id']);self.assertEqual(before,self.snapshot());self.retire()
  for n,fn in enumerate(ENTRIES):
   p=request('price01_null_'+str(n));p[2]=None;before=self.snapshot();got=self.invoke(p,fn);self.assertEqual(got.get('message') if fn in ['place_order','security_private.create_order103'] else got['reason'],'bad_value');self.assertEqual(before,self.snapshot())
 def test_16_resource_guard_auth_and_declared_privacy(self):
  self.policy(1,1);first=self.reject_price(args('price01_old_client'),reason='price_confirmation_required');r=self.invoke(args('price01_budget'));self.assertEqual(r['status'],'unresolved');self.assertEqual(r['reason'],'closure_resource_unavailable');self.assertEqual(self.rows(),1)
  self.assertEqual(self.invoke(args('price01_old_client'))['closure_id'],first['closure_id']);self.assertEqual(self.counts(),(0,0,0,0))
  c=self.tx(private=True);c.execute("select set_config('request.jwt.claims','{}',false)");r=self.outcome(c,request(),'security_private.create_order103');c.close();self.assertEqual(r['message'],'auth')
  for name in ['price01_normalize(jsonb)','price01_saved(bigint,uuid[],jsonb)']:
   self.assertFalse(self.a.execute("select has_function_privilege('authenticated',%s,'execute')",('security_private.'+name,)).fetchone()[0])
 def test_17_106_stale_snapshot_closed_key_regression(self):
  # Same preserved106 assertions, affected because all creators gained a guard.
  super().test_s03_all_entries_all_isolation_levels()
 def test_18_different_keys_near_admission_limit(self):
  for i in range(4):self.assertEqual(self.invoke(request('price01_open_'+str(i)))['status'],'created');self.consent()
  barrier=threading.Barrier(2);out=[];errors=[]
  def run(n):
   try:barrier.wait(5);out.append(self.invoke(request('price01_limit_'+str(n))))
   except Exception as e:errors.append(str(e))
  ts=[threading.Thread(target=run,args=(i,)) for i in range(2)]
  for t in ts:t.start()
  for t in ts:t.join(15);self.assertFalse(t.is_alive())
  self.assertFalse(errors);self.assertEqual(sorted(r['status'] for r in out),['created','rejected']);self.assertEqual(next(r['reason'] for r in out if r['status']=='rejected'),'too_many_orders');self.assertEqual(self.counts(),(5,5,-25,5))
 def test_19_different_accounts_same_key(self):
  barrier=threading.Barrier(2);out=[];errors=[]
  def run(uid):
   try:
    with self.actor(uid) as c:barrier.wait(5);out.append(call(c,request('price01_account_key'),'place_order104'))
   except Exception as e:errors.append(str(e))
  ts=[threading.Thread(target=run,args=(u,)) for u in [B,'20000000-0000-4000-8000-000000000092']]
  for t in ts:t.start()
  for t in ts:t.join(15);self.assertFalse(t.is_alive())
  self.assertFalse(errors,errors);self.assertEqual(len({r['id'] for r in out}),2);self.assertEqual(self.counts(),(2,2,-10,2))
 def test_20_rejection_ack_loss_reconciles_same_closure(self):
  from tcp_proxy import CutProxy
  self.a.execute('update menu_items set price=30')
  for mode in ['before','after']:
   p=request('price01_reject_ack_'+mode);proxy=CutProxy(mode);c=self.actor(port=proxy.port);r=call(c,p,'place_order104');self.assertTrue(r['closed']);proxy.arm=True
   with self.assertRaises((pg.OperationalError,pg.InterfaceError)):c.commit()
   c.close();proxy.join();self.assertTrue(proxy.cut)
   for _ in range(100):
    n=self.a.execute('select count(*) from security_private.order_attempt_closures104 where client_key=%s',(p[8],)).fetchone()[0]
    if n==(1 if mode=='after' else 0):break
    time.sleep(.01)
   got=self.reject_price(p)
   if mode=='after':self.assertEqual(got['closure_id'],r['closure_id']);self.assertNotIn('price_review',got)
  self.assertEqual(self.counts(),(0,0,0,0));self.assertEqual(self.rows(),2)
 def test_21_lock_timeout_and_40p01_fault_rollback(self):
  p=request('price01_timeout');hold=self.actor();hold.execute('select pg_advisory_xact_lock(hashtextextended(%s,0))',(B+':'+p[8],))
  with self.actor() as c:c.execute("set lock_timeout='100ms'");r=call(c,p,'place_order104')
  self.assertEqual(r['status'],'unresolved');self.assertEqual(r['reason'],'55P03');hold.rollback();hold.close();self.assertEqual(self.rows(),0);self.assertEqual(self.counts(),(0,0,0,0))
  self.a.execute("create function security_private.price01_deadlock() returns trigger language plpgsql as $$begin raise deadlock_detected;end$$;create trigger price01_deadlock after insert on security_private.order_request_fingerprints103 for each row execute function security_private.price01_deadlock()")
  r=self.invoke(p);self.assertEqual(r['status'],'unresolved');self.assertEqual(r['reason'],'40P01');self.assertEqual(self.counts(),(0,0,0,0));self.assertEqual(self.rows(),0)
  self.a.execute('drop trigger price01_deadlock on security_private.order_request_fingerprints103');self.assertEqual(self.invoke(p)['status'],'created');self.assertEqual(self.counts(),(1,1,-5,1))
 def test_22_wallet_full_decrease_fee_floor_and_success(self):
  p=request('price01_fullwallet',proof(wallet=22));p[10]=22;self.a.execute('update menu_items set price=10');before=self.snapshot();r=self.invoke(p);self.assertEqual(r['reason'],'wallet_changed');self.assertTrue(r['closed']);self.assertEqual(before,self.snapshot())
  p=request('price01_fullwallet_corrected',proof(price=10,wallet=12));p[10]=12;self.assertEqual(self.invoke(p)['status'],'created');self.retire()
  self.a.execute('update menu_items set price=1');p=request('price01_floor',proof(price=1,wallet=0));p[10]=0;self.assertEqual(self.invoke(p)['status'],'created');self.assertEqual(self.a.execute("select total from orders where client_key='price01_floor'").fetchone()[0],5)
  self.retire();self.a.execute('update menu_items set price=20');self.a.execute('update stores set free_delivery_min=15');p=request('price01_free',proof(fee=0));p[9]=0
  # Existing synthetic cash allocation .50 cannot be funded from fee0. Preserve
  # that guard; do not invent a funding policy to turn this scenario green.
  before=self.snapshot();r=self.invoke(p);self.assertEqual(r['reason'],'cash_allocation_exceeds_fee');self.assertTrue(r['closed']);self.assertEqual(before,self.snapshot())
  p=request('price01_free_wallet',proof(fee=0,wallet=20));p[9]=0;p[10]=20;self.assertEqual(self.invoke(p)['status'],'created');self.assertEqual(self.a.execute("select total,fee_waived from orders where client_key='price01_free_wallet'").fetchone(),(20,2))

 def test_23_historical_sent20_and_expired_group_schedule(self):
  # Genuine pre-TIP01 writer in this disposable fixture, not manufactured MACs.
  old=next(c for c in type(self).__mro__ if c.__name__=='Isolation106')
  old.upgrade(self);self.policy(200,200);self.group();saved=[]
  for n,extra in enumerate([{}, {'group':'60000000-0000-4000-8000-000000000092'}, {'at':self.a.execute("select now()+interval '40 minutes 1 second'").fetchone()[0].isoformat()}]):
   p=args('price01_pre_tip_'+str(n),extra);p[2]=20
   with self.actor() as c:r=call(c,p,'place_order104')
   self.assertEqual(r['status'],'created');self.assertEqual(self.a.execute('select tip from orders where id=%s',(r['id'],)).fetchone()[0],0);saved.append((p,r['id']));self.retire()
  self.upgrade();time.sleep(1.1);self.a.execute('update menu_items set price=80');before=self.snapshot()
  for p,oid in saved:
   for fn in ENTRIES:
    r=self.invoke(p,fn);self.assertEqual(str(r if isinstance(r,int) else r['id']),oid)
  self.assertEqual(before,self.snapshot());self.assertEqual(self.counts(),(3,3,-15,3))
 def test_24_interrupted_atomic_install_and_reapply(self):
  p=request('price01_install_saved');saved=self.invoke(p);closed=self.reject_price(args('price01_install_closed'),reason='price_confirmation_required');before=self.snapshot()
  catalog=lambda:self.a.execute("select n.nspname,p.proname,pg_get_functiondef(p.oid) from pg_proc p join pg_namespace n on n.oid=p.pronamespace where n.nspname='security_private' and p.prokind='f' order by p.oid").fetchall()
  definitions=catalog()
  with self.assertRaises(RuntimeError):
   with self.a.transaction():self.a.execute(Path('tests/price01-impl/rollback.sql').read_text());raise RuntimeError('simulated interrupted transaction')
  self.assertEqual(definitions,catalog());self.assertEqual(before,self.snapshot())
  self.a.execute(Path('tests/price01-impl/rollback.sql').read_text());rollback_defs=catalog()
  with self.assertRaises(RuntimeError):
   with self.a.transaction():self.a.execute(Path('tests/price01-impl/candidate.sql').read_text());raise RuntimeError('simulated interrupted re-upgrade')
  self.assertEqual(rollback_defs,catalog());self.assertEqual(before,self.snapshot())
  for fn in ENTRIES:self.assertNotIn('id',self.invoke(request('price01_install_unseen'),fn))
  for _ in range(2):
   with self.a.transaction():self.a.execute(Path('tests/price01-impl/candidate.sql').read_text())
   self.assertEqual(definitions,catalog());self.assertEqual(self.invoke(p)['id'],saved['id']);self.assertEqual(self.invoke(args('price01_install_closed'))['closure_id'],closed['closure_id']);self.assertEqual(before,self.snapshot())
 def test_25_removed_option_fee_and_points_guards(self):
  self.a.execute('insert into item_option_groups values(%s,%s,\'synthetic\',1,false,0,now())',(OG,I));self.a.execute('insert into item_options values(%s,%s,\'synthetic\',3,false,0)',(OP,OG))
  p=request('price01_removed_option',proof(options=[{'id':OP,'price_delta':'3'}]));p[1][0]['options']=[OP]
  before=self.snapshot();r=self.invoke(p);self.assertEqual(r['status'],'rejected');self.assertTrue(r['closed']);self.assertEqual(before,self.snapshot())
  p=request('price01_fee_changed');p[9]=3;r=self.invoke(p);self.assertEqual(r['reason'],'fee_changed');self.assertTrue(r['closed']);self.assertEqual(before,self.snapshot())
  self.a.execute(Path('tests/native103/dependencies.sql').read_text());self.a.execute("insert into loyalty_lots(user_id,points_left,expires_at)values(%s,200,now()+interval '1 day')",(B,));p=request('price01_points_changed',proof(points=10));p[11]=100;r=self.invoke(p);self.assertEqual(r['reason'],'points_changed');self.assertTrue(r['closed']);self.assertEqual(before,self.snapshot());self.assertEqual(self.a.execute('select points_left from loyalty_lots').fetchone()[0],200);self.assertEqual(self.a.execute('select count(*) from loyalty_ledger').fetchone()[0],0)

 def test_26_success_and_closure_win_contended_entries(self):
  for mode in ['success','closure']:
   for n,fn in enumerate(ENTRIES):
    key='price01_winner_'+mode+str(n);p=request(key);first=self.tx(private=fn.startswith('security_private.'));later=self.tx(private=fn.startswith('security_private.'));out={}
    if mode=='success':
     original=call(first,p,fn);other=copy.deepcopy(p);other[12]['price01']['totals']['total']='999';later_fn='place_order104'
    else:
     first.rollback();first.close();first=self.actor();original=call(first,args(key),'place_order104');self.assertTrue(original['closed']);other=p;later_fn=fn
    t=threading.Thread(target=lambda:out.update(r=self.outcome(later,other,later_fn)));t.start()
    try:
     blocked=False
     for _ in range(200):
      blocked=first.info.backend_pid in self.a.execute('select pg_blocking_pids(%s)',(later.info.backend_pid,)).fetchone()[0]
      if blocked:break
      time.sleep(.01)
     self.assertTrue(blocked);first.commit();t.join(15);self.assertFalse(t.is_alive())
    finally:first.rollback();first.close();t.join(16);later.close()
    if mode=='success':self.assertEqual(out['r']['status'],'conflict');self.assertNotIn('closed',out['r']);self.assertEqual(self.rows(),0);self.retire()
    else:self.assert_no_creation(out['r'],'read committed',fn);self.assertEqual(self.rows(),n+1)
  self.assertEqual(self.counts(),(4,4,-20,4))

if __name__=='__main__':
 names=sorted(n for n in Price01.__dict__ if n.startswith('test_'))
 if os.environ.get('PRICE01_CASES'):names=os.environ['PRICE01_CASES'].split(',')
 result=unittest.TextTestRunner(verbosity=2).run(unittest.TestSuite(Price01(n) for n in names))
 Path(os.environ.get('PRICE01_RESULT','price01-native.json')).write_text(json.dumps({'tests':result.testsRun,'passed':result.wasSuccessful(),'failures':[t.id() for t,_ in result.failures+result.errors]},indent=2)+'\n')
 raise SystemExit(not result.wasSuccessful())
