"""Independent PRICE01 delta cases; fresh loopback PostgreSQL17.6 only.
Imports candidate fixture setup, not developer test assertions or price oracle.
"""
import os,json,copy,threading,time,unittest
from pathlib import Path
assert os.environ.get('PRICE01_QA')=='fresh-local'
assert os.environ.get('PGHOST')=='127.0.0.1'
for k in ['PRICE01_ISOLATED','TIP02_NULL_ISOLATED','TIP02_ISOLATED','TIP01_ISOLATED']:os.environ[k]='yes'
ns={'__name__':'price_fixture_only'}
exec(compile(Path('tests/price01-impl/native.py').read_text(),'price_fixture_only','exec'),ns)
Base,call,args,ENTRIES,pg=(ns[k] for k in ['Price01','call','args','ENTRIES','pg'])
I='40000000-0000-4000-8000-000000000092';B='10000000-0000-4000-8000-000000000092'
OP='70000000-0000-4000-8000-000000000092';OG='80000000-0000-4000-8000-000000000092'
def consent():
 return {'version':1,'lines':[{'item_id':I,'qty':1,'base_price':'20','options':[],'unit_price':'20','restaurant_discount':'0','happy_hour_discount':'0','net_items':'20'}],
 'totals':dict(subtotal='20',restaurant_discount='0',happy_hour_discount='0',promo_discount='0',points_value='0',delivery_fee='2',tip='0',wallet_used='5',cash_due='17',total='22')}
def req(k):
 p=args(k,{});p[12]={'price01':consent()};return p
OBS=[]
class Independent(Base):
 def test_Q01_entries_proof_and_component_identity(self):
  for n,fn in enumerate(ENTRIES):
   p=req('qa_p01_'+str(n));r=self.invoke(p,fn);oid=r if isinstance(r,int) else r['id'];before=self.snapshot()
   changed=copy.deepcopy(p);changed[12]['price01']['lines'][0]['base_price']='19';changed[12]['price01']['lines'][0]['unit_price']='19'
   r2=self.invoke(changed,fn);self.assertFalse(isinstance(r2,int));self.assertNotIn('id',r2);self.assertEqual(before,self.snapshot())
   self.assertEqual(self.a.execute('select total,commission,driver_payout,wallet_used from orders where id=%s',(oid,)).fetchone(),(22,2,1.5,5));self.retire()
  self.assertEqual(self.counts(),(4,4,-20,4))
 def test_Q02_offset_base_and_option_same_unit_and_total(self):
  self.a.execute("insert into item_option_groups values(%s,%s,'synthetic',1,false,0,now())",(OG,I));self.a.execute("insert into item_options values(%s,%s,'synthetic',2,true,0)",(OP,OG));self.a.execute('update menu_items set price=18')
  p=req('qa_equal_parts');p[1][0]['options']=[OP];p[12]['price01']['lines'][0].update(base_price='17',options=[{'id':OP,'price_delta':'3'}])
  before=self.snapshot();r=self.invoke(p);self.assertEqual(r['reason'],'price_changed');self.assertTrue(r['closed']);self.assertEqual(r['price_review']['totals']['total'],'22');self.assertEqual(before,self.snapshot())
 def test_Q03_discount_split_same_total(self):
  self.a.execute('update stores set discount_pct=5');self.a.execute('create or replace function happy_hour_pct(uuid) returns int language sql as $$select 10$$')
  p=req('qa_discount_split');p[12]['price01']['lines'][0].update(restaurant_discount='2',happy_hour_discount='0',net_items='18');p[12]['price01']['totals'].update(restaurant_discount='2',happy_hour_discount='0',total='20',cash_due='15')
  before=self.snapshot();r=self.invoke(p);self.assertEqual(r['reason'],'price_changed');self.assertEqual(r['price_review']['totals']['total'],'20');self.assertEqual(r['price_review']['totals']['restaurant_discount'],'1');self.assertEqual(r['price_review']['totals']['happy_hour_discount'],'1');self.assertEqual(before,self.snapshot())
 def test_Q04_final_added_zero_option_must_not_be_hidden(self):
  # Adversarial synthetic writer, not a claim about a deployed target trigger.
  self.a.execute("create function security_private.qa_late_option() returns trigger language plpgsql as $$begin update order_items set options=options||jsonb_build_array(jsonb_build_object('id','71000000-0000-4000-8000-000000000092','p',0)) where order_id=NEW.order_id;return NEW;end$$;create trigger qa_late_option after insert on security_private.order_request_fingerprints103 for each row execute function security_private.qa_late_option()")
  before=self.snapshot();r=self.invoke(req('qa_late_free_option'));rows=self.a.execute('select options from order_items').fetchall();OBS.append({'case':'Q04','response':r,'saved_options':rows,'counts':self.counts()})
  self.assertEqual(r.get('status'),'rejected','persisted options differ from approved empty selection');self.assertEqual(before,self.snapshot())
 def test_Q05_final_wallet_and_loyalty_rollback(self):
  self.a.execute(Path('tests/native103/dependencies.sql').read_text());self.a.execute("insert into loyalty_lots(user_id,points_left,expires_at)values(%s,100,now()+interval '1 day')",(B,))
  self.a.execute("create function security_private.qa_final_price() returns trigger language plpgsql as $$begin update orders set total=total+1 where id=NEW.order_id;return NEW;end$$;create trigger qa_final_price after insert on security_private.order_request_fingerprints103 for each row execute function security_private.qa_final_price()")
  p=req('qa_final_money');p[11]=100;p[12]['price01']['totals'].update(points_value='10',total='12',cash_due='7');before=self.snapshot();r=self.invoke(p)
  self.assertEqual(r['reason'],'price_changed');self.assertTrue(r['no_effects']);self.assertEqual(before,self.snapshot());self.assertEqual(self.a.execute('select points_left from loyalty_lots').fetchone()[0],100);self.assertEqual(self.a.execute('select count(*) from loyalty_ledger').fetchone()[0],0)
 def test_Q06_no_price_old_payload_recovery_then_new_missing_reject(self):
  next(c for c in type(self).__mro__ if c.__name__=='NullDecision').upgrade(self)
  p=args('qa_before_price',{});saved=self.invoke(p);self.assertEqual(saved['status'],'created');self.upgrade();before=self.snapshot();self.a.execute('update menu_items set price=50')
  for fn in ENTRIES:
   r=self.invoke(p,fn);self.assertEqual(str(r if isinstance(r,int) else r['id']),saved['id'])
  self.assertEqual(before,self.snapshot());self.retire()
  for n,fn in enumerate(ENTRIES):
   r=self.invoke(args('qa_missing_price_'+str(n),{}),fn);self.assertFalse(isinstance(r,int));self.assertNotIn('id',r)
  self.assertEqual(self.counts(),(1,1,-5,1))
 def test_Q07_simultaneous_different_proofs_one_winner(self):
  bar=threading.Barrier(2);out=[];errors=[]
  def run(change):
   try:
    p=req('qa_race_price');
    if change:p[12]['price01']['lines'][0]['base_price']='19'
    bar.wait(5);out.append(self.invoke(p))
   except Exception as e:errors.append(repr(e))
  ts=[threading.Thread(target=run,args=(i,)) for i in [0,1]]
  for t in ts:t.start()
  for t in ts:t.join(15);self.assertFalse(t.is_alive())
  self.assertFalse(errors);n=self.counts()[0];self.assertIn(n,[0,1]);self.assertEqual(self.counts(),(n,n,-5*n,n));self.assertEqual(self.rows(),1-n)
  self.assertNotIn('unresolved',[r['status'] for r in out]);OBS.append({'case':'Q07','responses':out,'counts':self.counts()})
 def test_Q08_hmac_definition_acl_unchanged(self):
  query="select n.nspname,p.proname,pg_get_function_identity_arguments(p.oid),p.prosrc,p.prosecdef,p.proconfig,p.proacl::text from pg_proc p join pg_namespace n on n.oid=p.pronamespace where n.nspname='security_private' and p.proname in ('mac103','canonical103','request103','resolve103') order by p.proname"
  final=self.a.execute(query).fetchall();next(c for c in type(self).__mro__ if c.__name__=='NullDecision').upgrade(self);prior=self.a.execute(query).fetchall();self.assertEqual(final,prior);self.assertGreaterEqual(len(final),2)

class Result(unittest.TextTestResult):
 def startTest(self,t):super().startTest(t);self.started=time.monotonic()
 def addSuccess(self,t):super().addSuccess(t);records.append({'case':t._testMethodName,'status':'PASS','seconds':round(time.monotonic()-self.started,3)})
 def addFailure(self,t,e):super().addFailure(t,e);records.append({'case':t._testMethodName,'status':'FAIL','detail':self._exc_info_to_string(e,t)})
 def addError(self,t,e):super().addError(t,e);records.append({'case':t._testMethodName,'status':'ERROR','detail':self._exc_info_to_string(e,t)})
records=[]
names=[n for n in Independent.__dict__ if n.startswith('test_Q')]
suite=unittest.TestSuite(Independent(n) for n in names)
res=unittest.TextTestRunner(verbosity=2,resultclass=Result).run(suite)
Path('qa-native-results.json').write_text(json.dumps({'scope':'NATIVE POSTGRESQL17.6 / synthetic fixture / independent authored cases','source':'bb01f11b855a2898f3f0b0f8908de827be68844b','results':records,'observations':OBS},indent=2,default=str)+'\n')
raise SystemExit(not res.wasSuccessful())
