"""Independent cross-layer and final-snapshot probes; local synthetic only."""
import os,json,unittest,copy
from pathlib import Path
assert os.environ.get('PRICE01_QA')=='fresh-local'
for k in ['PRICE01_ISOLATED','TIP02_NULL_ISOLATED','TIP02_ISOLATED','TIP01_ISOLATED']:os.environ[k]='yes'
ns={'__name__':'price_fixture'};exec(compile(Path('tests/price01-impl/native.py').read_text(),'fixture','exec'),ns)
Base=ns['Price01'];I=ns['I'];OP=ns['OP'];OG=ns['OG'];args=ns['args']
obs=[]
class Followup(Base):
 def test_Q09_real_UI_unchanged_price_must_be_accepted(self):
  p=args('qa_real_ui_proof',{},qty=3);p[10]=0;p[12]={'price01':json.loads(Path('qa-client-quantity-proof.json').read_text())};self.a.execute('update menu_items set price=20.1');r=self.invoke(p);obs.append({'case':'Q09','response':r,'counts':self.counts()})
  self.assertEqual(r['status'],'created','unchanged20.1 x3 was wrongly rejected as price_changed')
 def test_Q10_explicit_server_decimal_review_can_then_succeed(self):
  p=args('qa_exact_price_review',{},qty=3);p[10]=0;p[12]={'price01':json.loads(Path('qa-client-quantity-proof.json').read_text())};self.a.execute('update menu_items set price=20.1');r=self.invoke(p);self.assertEqual(r['reason'],'price_changed');self.assertTrue(r['closed']);p[8]='qa_exact_price_approved';p[12]['price01']=r['price_review'];created=self.invoke(p);self.assertEqual(created['status'],'created');self.assertEqual(self.counts(),(1,0,0,1))
 def test_Q11_final_removed_zero_option_must_not_be_hidden(self):
  self.a.execute("insert into item_option_groups values(%s,%s,'synthetic',1,false,0,now())",(OG,I));self.a.execute("insert into item_options values(%s,%s,'synthetic',0,true,0)",(OP,OG))
  p=ns['request']('qa_removed_free_option');p[1][0]['options']=[OP];p[12]['price01']['lines'][0]['options']=[{'id':OP,'price_delta':'0'}]
  self.a.execute("create function security_private.qa_remove_option() returns trigger language plpgsql as $$begin update order_items set options='[]' where order_id=NEW.order_id;return NEW;end$$;create trigger qa_remove_option after insert on security_private.order_request_fingerprints103 for each row execute function security_private.qa_remove_option()")
  before=self.snapshot();r=self.invoke(p);self.assertEqual(r['status'],'rejected');self.assertEqual(before,self.snapshot())
 def test_Q12_final_unrequested_offset_pair_must_not_be_hidden(self):
  self.a.execute("create function security_private.qa_offset_options() returns trigger language plpgsql as $$begin update order_items set options=options||jsonb_build_array(jsonb_build_object('id','71000000-0000-4000-8000-000000000092','p',1),jsonb_build_object('id','72000000-0000-4000-8000-000000000092','p',-1)) where order_id=NEW.order_id;return NEW;end$$;create trigger qa_offset_options after insert on security_private.order_request_fingerprints103 for each row execute function security_private.qa_offset_options()")
  r=self.invoke(ns['request']('qa_offset_late_opts'));obs.append({'case':'Q12','response':r,'counts':self.counts()});self.assertEqual(r['status'],'rejected')
records=[]
class Result(unittest.TextTestResult):
 def addSuccess(self,t):super().addSuccess(t);records.append({'case':t._testMethodName,'status':'PASS'})
 def addFailure(self,t,e):super().addFailure(t,e);records.append({'case':t._testMethodName,'status':'FAIL','detail':self._exc_info_to_string(e,t)})
 def addError(self,t,e):super().addError(t,e);records.append({'case':t._testMethodName,'status':'ERROR','detail':self._exc_info_to_string(e,t)})
res=unittest.TextTestRunner(verbosity=2,resultclass=Result).run(unittest.TestSuite(Followup(n) for n in Followup.__dict__ if n.startswith('test_Q')))
Path('qa-native-followup.json').write_text(json.dumps({'scope':'NativePG17.6 / synthetic fixture / independent new probes','results':records,'observations':obs},indent=2,default=str)+'\n');raise SystemExit(not res.wasSuccessful())
