import os,json,unittest
from pathlib import Path
assert os.environ.get('PRICE01_QA')=='fresh-local'
for k in ['PRICE01_ISOLATED','TIP02_NULL_ISOLATED','TIP02_ISOLATED','TIP01_ISOLATED']:os.environ[k]='yes'
ns={'__name__':'price_boundary_fixture'};exec(compile(Path('tests/price01-impl/native.py').read_text(),'fixture','exec'),ns)
Base=ns['Price01'];entries=ns['ENTRIES'];records=[]
class Boundary(Base):
 def test_Q13_new_price_mismatch_four_entries(self):
  self.a.execute('update menu_items set price=31')
  for i,fn in enumerate(entries):
   before=self.snapshot();p=ns['request']('qa_fresh_mismatch_'+str(i));r=self.invoke(p,fn)
   if fn in ['place_order','security_private.create_order103']:self.assertEqual(r.get('message'),'price_changed')
   else:self.assertEqual(r['reason'],'price_changed');self.assertEqual(r['status'],'rejected')
   self.assertEqual(before,self.snapshot())
  self.assertEqual(self.counts(),(0,0,0,0))
 def test_Q14_full_fingerprint_sources_and_creator_metadata(self):
  q="select n.nspname,p.proname,pg_get_function_identity_arguments(p.oid),p.prosecdef,p.proconfig,p.proacl::text,p.proowner from pg_proc p join pg_namespace n on n.oid=p.pronamespace where (n.nspname='security_private' and p.proname='create_order103') or (n.nspname='public' and p.proname in ('place_order','place_order103','place_order104')) order by 1,2"
  h="select p.proname,pg_get_functiondef(p.oid) from pg_proc p join pg_namespace n on n.oid=p.pronamespace where n.nspname='security_private' and p.proname in ('canonical103','request_payload103','mac103','resolve103') order by 1"
  metadata=self.a.execute(q).fetchall();fingerprints=self.a.execute(h).fetchall();self.assertEqual(len(metadata),4);self.assertEqual(len(fingerprints),4)
  next(c for c in type(self).__mro__ if c.__name__=='NullDecision').upgrade(self)
  self.assertEqual(self.a.execute(q).fetchall(),metadata);self.assertEqual(self.a.execute(h).fetchall(),fingerprints)
class Result(unittest.TextTestResult):
 def addSuccess(self,t):super().addSuccess(t);records.append({'case':t._testMethodName,'status':'PASS'})
 def addFailure(self,t,e):super().addFailure(t,e);records.append({'case':t._testMethodName,'status':'FAIL','detail':self._exc_info_to_string(e,t)})
 def addError(self,t,e):super().addError(t,e);records.append({'case':t._testMethodName,'status':'ERROR','detail':self._exc_info_to_string(e,t)})
res=unittest.TextTestRunner(verbosity=2,resultclass=Result).run(unittest.TestSuite(Boundary(n) for n in Boundary.__dict__ if n.startswith('test_Q')))
Path('qa-native-boundaries.json').write_text(json.dumps({'scope':'NativePG17.6/synthetic catalog','results':records},indent=2)+'\n');raise SystemExit(not res.wasSuccessful())
