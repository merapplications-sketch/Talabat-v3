import os,json,unittest,copy,threading,time
from pathlib import Path
from decimal import Decimal
assert os.environ['PGHOST']=='127.0.0.1'
for k in ['PRICE01_ISOLATED','TIP02_NULL_ISOLATED','TIP02_ISOLATED','TIP01_ISOLATED']:os.environ[k]='yes'
ns={'__name__':'fixture'};exec(compile(Path('independent_price_native.py').read_text().split('class Result')[0],'prior-independent','exec'),ns)
Base=ns['Base'];I=ns['I'];OP=ns['OP'];OG=ns['OG'];ENTRIES=ns['ENTRIES'];args=ns['args'];call=ns['call'];req=ns['req'];obs=[]
class Delta(Base):
 def test_options_complete_all_entries(self):
  self.a.execute("insert into item_option_groups values(%s,%s,'synthetic',2,false,0,now())",(OG,I));self.a.execute("insert into item_options values(%s,%s,'synthetic',0,true,0)",(OP,OG))
  other='71000000-0000-4000-8000-000000000092'
  cases=[('added',[{'id':OP,'p':0},{'id':other,'p':0}]),('removed',[]),('duplicate',[{'id':OP,'p':0}]*2),('identity',[{'id':other,'p':0}]),('offset',[{'id':OP,'p':1},{'id':other,'p':-1}])]
  for label,actual in cases:
   self.a.execute("create function security_private.qa_delta_options() returns trigger language plpgsql as $$begin update order_items set options='"+json.dumps(actual)+"'::jsonb where order_id=NEW.order_id;return NEW;end$$;create trigger qa_delta_options after insert on security_private.order_request_fingerprints103 for each row execute function security_private.qa_delta_options()")
   for n,fn in enumerate(ENTRIES):
    p=req('delta_'+label+str(n));p[1][0]['options']=[OP];p[12]['price01']['lines'][0]['options']=[{'id':OP,'price_delta':'0'}];before=self.snapshot();r=self.invoke(p,fn)
    self.assertEqual(r.get('reason',r.get('message')),'price_changed',r);self.assertEqual(before,self.snapshot());self.assertEqual(self.counts(),(0,0,0,0));obs.append({'case':label,'entry':fn,'result':r.get('reason',r.get('message')),'effects':0})
   self.a.execute('drop trigger qa_delta_options on security_private.order_request_fingerprints103;drop function security_private.qa_delta_options()')
 def test_real_client_proofs_four_entries_and_replay(self):
  self.a.execute("insert into item_option_groups values(%s,%s,'synthetic',2,false,0,now())",(OG,I));self.a.execute("insert into item_options values(%s,%s,'synthetic',0,true,0)",(OP,OG))
  for case in json.loads(Path('delta-proofs.json').read_text()):
   self.a.execute('update menu_items set price=%s',(Decimal(str(case['base'])),));self.a.execute('update stores set discount_pct=%s',(case['rd'],));self.a.execute('create or replace function happy_hour_pct(uuid) returns int language sql as $$select '+str(case['hh'])+'$$')
   if case['opt'] is not None:self.a.execute('update item_options set price_delta=%s',(Decimal(str(case['opt'])),))
   for n,fn in enumerate(ENTRIES):
    p=args('delta_'+case['name']+str(n),{},qty=case['q']);p[10]=0;p[12]={'price01':copy.deepcopy(case['proof'])}
    if case['opt'] is not None:p[1][0]['options']=[OP]
    r=self.invoke(p,fn);oid=r if isinstance(r,int) else r.get('id');self.assertIsNotNone(oid,r)
    self.assertEqual(self.a.execute('select subtotal,total from orders where id=%s',(oid,)).fetchone(),(Decimal(case['gross']),Decimal(case['total'])))
    before=self.snapshot();again=self.invoke(p,fn);self.assertEqual(str(again if isinstance(again,int) else again['id']),str(oid));self.assertEqual(before,self.snapshot());obs.append({'case':case['name'],'entry':fn,'created_once':True,'replay_unchanged':True});self.retire()
 def test_concurrent_decimal_payload_then_changed_proof(self):
  p=args('delta_concurrent',{},qty=3);p[12]={'price01':json.loads(Path('delta-proofs.json').read_text())[0]['proof']};p[12]['price01']['totals'].update(wallet_used='5',cash_due='57.3');self.a.execute('update menu_items set price=20.1');bar=threading.Barrier(3);out=[];err=[]
  def work():
   try:bar.wait(5);out.append(self.invoke(copy.deepcopy(p)))
   except Exception as e:err.append(str(e))
  ts=[threading.Thread(target=work) for _ in range(3)]
  for t in ts:t.start()
  for t in ts:t.join(20);self.assertFalse(t.is_alive())
  self.assertFalse(err);self.assertEqual(sorted(x['status'] for x in out),['created','replayed','replayed']);self.assertEqual(self.counts(),(1,1,-5,1));before=self.snapshot();p[12]['price01']['lines'][0]['base_price']='20.2';r=self.invoke(p);self.assertNotIn(r['status'],['created','replayed']);self.assertEqual(before,self.snapshot());obs.append({'case':'race','responses':out,'changed_proof':r})
 def test_tcp_loss_and_recovery(self):
  from tcp_proxy import CutProxy
  pg=ns['pg'];p=args('delta_ack',{},qty=3);p[12]={'price01':json.loads(Path('delta-proofs.json').read_text())[0]['proof']};p[12]['price01']['totals'].update(wallet_used='5',cash_due='57.3')
  for mode in ['before','after']:
   self.a.execute('update menu_items set price=20.1');p[8]='delta_ack_'+mode;proxy=CutProxy(mode);c=self.actor(port=proxy.port);r=call(c,p,'place_order104');self.assertEqual(r['status'],'created');proxy.arm=True
   with self.assertRaises((pg.OperationalError,pg.InterfaceError)):c.commit()
   c.close();proxy.join();self.assertTrue(proxy.cut);time.sleep(.05);n=self.a.execute('select count(*) from orders where client_key=%s',(p[8],)).fetchone()[0];self.assertEqual(n,1 if mode=='after' else 0)
   if mode=='after':self.a.execute('update menu_items set price=21')
   recovered=self.invoke(p);self.assertEqual(recovered['status'],'replayed' if mode=='after' else 'created');self.assertEqual(self.a.execute('select count(*) from wallet_entries where kind=\'spend\'').fetchone()[0],1 if mode=='before' else 2);self.retire();obs.append({'case':'tcp_'+mode,'orders_at_loss':n,'recovery':recovered['status']})
records=[]
class R(unittest.TextTestResult):
 def addSuccess(self,t):super().addSuccess(t);records.append({'case':t._testMethodName,'status':'PASS'})
 def addFailure(self,t,e):super().addFailure(t,e);records.append({'case':t._testMethodName,'status':'FAIL','detail':self._exc_info_to_string(e,t)})
 def addError(self,t,e):super().addError(t,e);records.append({'case':t._testMethodName,'status':'ERROR','detail':self._exc_info_to_string(e,t)})
suite=unittest.TestSuite(Delta(n) for n in Delta.__dict__ if n.startswith('test_'))
b={};exec(compile(Path('independent_price_boundaries.py').read_text().split('class Result')[0],'prior-boundary','exec'),b);suite.addTest(b['Boundary']('test_Q14_full_fingerprint_sources_and_creator_metadata'))
r=unittest.TextTestRunner(verbosity=2,resultclass=R).run(suite);Path('delta-native-results.json').write_text(json.dumps({'source':'50b796985112002f4c47aa4dd2bd1373ffd7aeff','scope':'Native PostgreSQL17.6; synthetic fixture; loopback TCP','results':records,'observations':obs},indent=2,default=str));raise SystemExit(not r.wasSuccessful())
