"""Targeted regression; real loopback PG17.6, synthetic dependencies only.
Q04/Q09/Q12 reproduce independent QA 7ed6708 without using the price oracle.
"""
import os, json, copy, unittest
from pathlib import Path
assert os.environ.get('PGHOST') == '127.0.0.1'
for k in ['PRICE01_ISOLATED','TIP02_NULL_ISOLATED','TIP02_ISOLATED','TIP01_ISOLATED']:
 os.environ[k]='yes'
ns={'__name__':'fixture_only'}
exec(compile(Path('tests/price01-impl/native.py').read_text(),'fixture_only','exec'),ns)
Base, args, ENTRIES = (ns[k] for k in ['Price01','args','ENTRIES'])
I, OP, OG = (ns[k] for k in ['I','OP','OG'])
EX='71000000-0000-4000-8000-000000000092'
EY='72000000-0000-4000-8000-000000000092'
def request(key):
 p=args(key,{})
 p[12]={'price01':{'version':1,'lines':[{'item_id':I,'qty':1,'base_price':'20','options':[],'unit_price':'20','restaurant_discount':'0','happy_hour_discount':'0','net_items':'20'}],
 'totals':dict(subtotal='20',restaurant_discount='0',happy_hour_discount='0',promo_discount='0',points_value='0',delivery_fee='2',tip='0',wallet_used='5',cash_due='17',total='22')}}
 return p
OBS=[]
class Correction(Base):
 def fault(self, options):
  self.a.execute("create function security_private.qa_snapshot() returns trigger language plpgsql as $$begin update order_items set options='"+json.dumps(options)+"'::jsonb where order_id=NEW.order_id;return NEW;end$$;create trigger qa_snapshot after insert on security_private.order_request_fingerprints103 for each row execute function security_private.qa_snapshot()")
 def reject_all(self, key, options):
  self.fault(options)
  for i,fn in enumerate(ENTRIES):
   p=request(key+str(i));before=self.snapshot();r=self.reject_price(p,fn)
   self.assertEqual(before,self.snapshot());self.assertEqual(self.counts(),(0,0,0,0))
   OBS.append({'case':key,'entry':fn,'result':r,'counts':self.counts()})
 def test_Q04_added_zero_option(self):
  self.reject_all('qa_zero_extra',[{'id':EX,'p':0}])
 def test_Q12_offset_options(self):
  self.reject_all('qa_offset_extra',[{'id':EX,'p':1},{'id':EY,'p':-1}])
 def test_Q09_real_ui_quantity(self):
  p=args('qa_real_quantity',{},qty=3);p[10]=0
  p[12]={'price01':json.loads(Path(os.environ.get('QA_QUANTITY_PROOF','qa-client-quantity-proof.json')).read_text())}
  self.a.execute('update menu_items set price=20.1')
  for i,fn in enumerate(ENTRIES):
   p[8]='qa_real_quantity'+str(i);r=self.invoke(p,fn)
   oid=r if isinstance(r,int) else r.get('id');self.assertIsNotNone(oid,r)
   from decimal import Decimal
   self.assertEqual(self.a.execute('select subtotal,total,tip,wallet_used from orders where id=%s',(oid,)).fetchone(),(Decimal('60.3'),Decimal('62.3'),0,0))
   before=self.snapshot();again=self.invoke(p,fn)
   self.assertEqual(str(again if isinstance(again,int) else again['id']),str(oid));self.assertEqual(before,self.snapshot());self.retire()
  self.assertEqual(self.counts(),(4,0,0,4))
 def option_setup(self):
  self.a.execute("insert into item_option_groups values(%s,%s,'synthetic',2,false,0,now())",(OG,I))
  self.a.execute("insert into item_options values(%s,%s,'first',0,true,0),(%s,%s,'second',0,true,1)",(OP,OG,EX,OG))
 def test_option_identity_count_price_and_removal_all_entries(self):
  self.option_setup()
  for mode,actual in [('replace',[{'id':EY,'p':0}]),('duplicate',[{'id':OP,'p':0},{'id':OP,'p':0}]),('remove',[]),('price',[{'id':OP,'p':1}])]:
   with self.subTest(mode=mode):
    self.fault(actual)
    for i,fn in enumerate(ENTRIES):
     p=request('qa_option_'+mode+str(i));p[1][0]['options']=[OP];p[12]['price01']['lines'][0]['options']=[{'id':OP,'price_delta':'0'}]
     self.reject_price(p,fn);self.assertEqual(self.counts(),(0,0,0,0))
    self.a.execute('drop trigger qa_snapshot on security_private.order_request_fingerprints103;drop function security_private.qa_snapshot()')
 def test_known_option_offset_prices_same_total(self):
  self.option_setup();self.fault([{'id':OP,'p':1},{'id':EX,'p':-1}])
  for i,fn in enumerate(ENTRIES):
   p=request('qa_known_offset'+str(i));p[1][0]['options']=[OP,EX];p[12]['price01']['lines'][0]['options']=[{'id':OP,'price_delta':'0'},{'id':EX,'price_delta':'0'}]
   self.reject_price(p,fn);self.assertEqual(self.counts(),(0,0,0,0))
 def test_complete_options_different_storage_order_accept_replay(self):
  self.option_setup()
  for i,fn in enumerate(ENTRIES):
   p=request('qa_option_order'+str(i));p[1][0]['options']=[EX,OP];p[12]['price01']['lines'][0]['options']=[{'id':EX,'price_delta':'0'},{'id':OP,'price_delta':'0'}]
   r=self.invoke(p,fn);oid=r if isinstance(r,int) else r['id'];before=self.snapshot()
   self.assertEqual(len(self.a.execute('select options from order_items where order_id=%s',(oid,)).fetchone()[0]),2)
   again=self.invoke(p,fn);self.assertEqual(str(again if isinstance(again,int) else again['id']),str(oid));self.assertEqual(before,self.snapshot());self.retire()
  self.assertEqual(self.counts(),(4,4,-20,4))
 def test_real_client_decimal_matrix(self):
  from decimal import Decimal
  cases=json.loads(Path(os.environ.get('QA_CLIENT_PROOFS','price01-client-proofs.json')).read_text());self.assertEqual(len(cases),6)
  for i,case in enumerate(cases):
   with self.subTest(name=case['name']):
    self.a.execute('update menu_items set price=%s where id=%s',(case['price'],I));self.a.execute('update stores set discount_pct=%s',(case.get('rd',0),))
    self.a.execute('create or replace function happy_hour_pct(uuid) returns int language sql as $$select '+str(case.get('hh',0))+'$$')
    p=args('qa_cross_'+str(i),{},qty=case['qty']);p[10]=0;p[12]={'price01':case['value']}
    if 'option' in case:
     if not self.a.execute("select 1 from item_option_groups where id=%s",(OG,)).fetchone():
      self.a.execute("insert into item_option_groups values(%s,%s,'synthetic',2,false,0,now())",(OG,I))
      self.a.execute("insert into item_options values(%s,%s,'first',0,true,0)",(OP,OG))
     self.a.execute("update item_options set price_delta=%s where id=%s",(case['option'],OP));p[1][0]['options']=[OP]
    if 'second' in case:
     j='41000000-0000-4000-8000-000000000092'
     if self.a.execute('select 1 from menu_items where id=%s',(j,)).fetchone():self.a.execute('update menu_items set price=%s where id=%s',(case['second'],j))
     else:self.a.execute('insert into menu_items select %s,store_id,name,%s,available,approved,discount_pct from menu_items where id=%s',(j,Decimal(case['second']),I))
     p[1].append({'item_id':j,'qty':1,'options':[]})
    if 'promo' in case:
     self.a.execute(Path('tests/native103/dependencies.sql').read_text());self.a.execute("insert into promo_codes values('QAPROMO',true,null,null,0,null,'fixed',%s)",(case['promo'],));self.a.execute("insert into promo_attempts values(%s,true,'QAPROMO',now())",(ns['B'],));p[7]='QAPROMO'
    r=self.invoke(p);self.assertEqual(r['status'],'created',r);saved=self.a.execute('select subtotal,total from orders where id=%s',(r['id'],)).fetchone()
    self.assertEqual(saved,(Decimal(case['value']['totals']['subtotal']),Decimal(case['value']['totals']['total'])));before=self.snapshot();self.assertEqual(self.invoke(p)['id'],r['id']);self.assertEqual(before,self.snapshot());self.retire()
  self.assertEqual(self.counts(),(len(cases),0,0,len(cases)))
 def test_decimal_ack_concurrency_then_reprice(self):
  import threading,time
  from tcp_proxy import CutProxy
  from decimal import Decimal
  pg=ns['pg'];call=ns['call'];p=args('qa_decimal_race',{},qty=3);p[12]={'price01':json.loads(Path(os.environ.get('QA_QUANTITY_PROOF','qa-client-quantity-proof.json')).read_text())}
  p[12]['price01']['totals'].update(wallet_used='5',cash_due='57.3');self.a.execute('update menu_items set price=20.1')
  barrier=threading.Barrier(3);out=[];errors=[]
  def run():
   try:barrier.wait(5);out.append(self.invoke(p))
   except Exception as e:errors.append(repr(e))
  ts=[threading.Thread(target=run) for _ in range(3)]
  for t in ts:t.start()
  for t in ts:t.join(15);self.assertFalse(t.is_alive())
  self.assertFalse(errors);self.assertEqual(sorted(r['status'] for r in out),['created','replayed','replayed']);self.assertEqual(self.counts(),(1,1,-5,1));self.retire()
  for mode in ['before','after']:
   self.a.execute('update menu_items set price=20.1');p[8]='qa_decimal_ack_'+mode;proxy=CutProxy(mode);c=self.actor(port=proxy.port);r=call(c,p,'place_order104');self.assertEqual(r['status'],'created');proxy.arm=True
   with self.assertRaises((pg.OperationalError,pg.InterfaceError)):c.commit()
   c.close();proxy.join();self.assertTrue(proxy.cut)
   for _ in range(100):
    n=self.a.execute('select count(*) from orders where client_key=%s',(p[8],)).fetchone()[0]
    if n==(1 if mode=='after' else 0):break
    time.sleep(.01)
   self.assertEqual(n,1 if mode=='after' else 0);self.a.execute('update menu_items set price=20.2')
   if mode=='before':self.reject_price(p)
   else:
    before=self.snapshot();got=self.invoke(p);self.assertEqual(got['status'],'replayed');self.assertEqual(got['id'],r['id']);self.assertEqual(before,self.snapshot())
    self.assertEqual(self.a.execute('select subtotal from orders where id=%s',(r['id'],)).fetchone()[0],Decimal('60.3'))
  self.assertEqual(self.counts(),(2,2,-10,2))

if __name__=='__main__':
 names=os.environ.get('QA_NATIVE_CASES','').split(',') if os.environ.get('QA_NATIVE_CASES') else [n for n in Correction.__dict__ if n.startswith('test_')]
 records=[]
 class Result(unittest.TextTestResult):
  def addSuccess(self,t):super().addSuccess(t);records.append({'case':t._testMethodName,'status':'PASS'})
  def addFailure(self,t,e):super().addFailure(t,e);records.append({'case':t._testMethodName,'status':'FAIL','detail':self._exc_info_to_string(e,t)})
  def addError(self,t,e):super().addError(t,e);records.append({'case':t._testMethodName,'status':'ERROR','detail':self._exc_info_to_string(e,t)})
 result=unittest.TextTestRunner(verbosity=2,resultclass=Result).run(unittest.TestSuite(Correction(n) for n in names))
 Path(os.environ.get('QA_RESULT','price01-correction-native.json')).write_text(json.dumps({'scope':'PostgreSQL17.6 / synthetic schema, triggers and identities / no hosted services','results':records,'observations':OBS},indent=2,default=str)+'\n')
 raise SystemExit(not result.wasSuccessful())
