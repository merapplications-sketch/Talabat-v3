import os,json,hashlib,hmac,sys
from pathlib import Path
import psycopg
assert os.environ.get('PGHOST')=='127.0.0.1'
R=Path('.');root=psycopg.connect(dbname='postgres',autocommit=True)
for role in ['authenticated','anon']:
 if not root.execute('select 1 from pg_roles where rolname=%s',(role,)).fetchone():root.execute('create role '+role)
BASE=Path('tests/native98/setup.sql').read_text().replace('create role authenticated;create role anon;','')+Path('tests/native102/constraints.sql').read_text()+Path('tests/native103/fidelity.sql').read_text()
UP=''.join(Path('tests/native103/'+f).read_text() for f in ['schema.sql','functions.sql','migrate102.sql'])
U='10000000-0000-4000-8000-000000000092';V='20000000-0000-4000-8000-000000000092';S='30000000-0000-4000-8000-000000000092';I='40000000-0000-4000-8000-000000000092';G='60000000-0000-4000-8000-000000000092'
def reset():
 root.execute('drop database if exists independent_review103 with(force)');root.execute('create database independent_review103')
 a=psycopg.connect(dbname='independent_review103',autocommit=True);a.execute(BASE);a.execute('create schema extensions;create extension pgcrypto with schema extensions');return a
def upgrade(a):a.execute(UP);a.execute('insert into security_private.order_request_keys103 values(1,%s,true)',(os.urandom(32),))
def actor(uid=U):
 c=psycopg.connect(dbname='independent_review103');c.execute("select set_config('request.jwt.claims',%s,false)",(json.dumps({'sub':uid}),));c.execute('set role authenticated');return c
def payload(k='qa103_native',extra=None):return [S,[{'item_id':I,'qty':1,'options':[]}],0,'cash','synthetic',38.123456789012344,68.12345678901234,None,k,None,5,None,extra]
def call(c,p,fn='place_order103'):
 q=list(p);q[1]=json.dumps(q[1]);q[12]=json.dumps(q[12]) if q[12] is not None else None
 return c.execute('select '+fn+'(%s::uuid,%s::jsonb,%s::numeric,%s::text,%s::text,%s::float8,%s::float8,%s::text,%s::text,%s::numeric,%s::numeric,%s::integer,%s::jsonb)',q).fetchone()[0]
def counts(a):return a.execute("select (select count(*) from orders),(select count(*) from wallet_entries where kind='spend'),(select count(*) from security_private.order_request_fingerprints103)").fetchone()
results=[]
def run(name,fn):
 a=reset()
 try:detail=fn(a);results.append({'case':name,'passed':True,'detail':detail})
 except Exception as e:results.append({'case':name,'passed':False,'error_type':type(e).__name__,'detail':str(e)[:300]})
 finally:a.close()
def history(a):
 ids=[]
 for mode in ['normal','group','scheduled']:
  extra=None
  if mode=='group':a.execute("insert into group_orders(id,host_id,status,store_id,expires_at)values(%s,%s,'open',%s,now()+interval '1 hour')",(G,U,S));extra={'group':G}
  if mode=='scheduled':extra={'at':a.execute("select now()+interval '60 minutes'").fetchone()[0].isoformat()}
  with actor() as c:ids.append(call(c,payload('qa103_old_'+mode,extra),'place_order'))
 upgrade(a);before=counts(a)
 with psycopg.connect(dbname='independent_review103') as c:
  c.execute('set transaction read only');c.execute("select set_config('request.jwt.claims',%s,false)",(json.dumps({'sub':U}),));c.execute('set role authenticated')
  for mode,oid in zip(['normal','group','scheduled'],ids):
   p=payload('qa103_old_'+mode,{'at':'invalid-new-input'});p[1]=[];r=call(c,p);assert r['status']=='historical_recovered' and r['id']==str(oid) and r['input_match'] is None,r
 with actor(V) as c:r=c.execute("select order_request_status103('qa103_old_normal')").fetchone()[0];assert r['status']=='unresolved' and 'id' not in r
 assert counts(a)==before==(3,3,0)
 return {'modes':3,'read_only':True,'no_bindings':True,'cross_account_hidden':True}
run('historical-read-only-independent',history)
def unicode(a):
 upgrade(a);secret=os.urandom(32);p=[S,[{'text':'Таджикистан / طَلَب 😀','nested':None,'escaped':'a\\b\n"'}],0,'cash','é',38.5,68.5,None,None,5,None,{}]
 msg=json.dumps(['TALABOT/order-create',1,U,'qa103_unicode',p],sort_keys=True,ensure_ascii=False,separators=(',',':')).encode()
 mac=bytes(a.execute('select security_private.mac103(%s::jsonb,%s::uuid,%s,%s)',(json.dumps(p),U,'qa103_unicode',secret)).fetchone()[0]);assert mac==hmac.new(secret,msg,hashlib.sha256).digest()
 p2=json.loads(json.dumps(p));p2[4]='e\u0301';other=bytes(a.execute('select security_private.mac103(%s::jsonb,%s::uuid,%s,%s)',(json.dumps(p2),U,'qa103_unicode',secret)).fetchone()[0]);assert other!=mac
 return {'unicode_python_oracle':True,'no_unicode_normalization':True}
run('unicode-hmac-independent-oracle',unicode)
def missing(a):
 upgrade(a)
 with actor() as c:r=call(c,payload());assert r['status']=='created'
 # Fault injection ONLY: missing historical secret after an incomplete private restore. FK normally prevents deletion.
 a.execute('alter table security_private.order_request_fingerprints103 drop constraint order_request_fingerprints103_key_id_fkey');a.execute('delete from security_private.order_request_keys103');before=counts(a)
 with actor() as c:r=call(c,payload());assert r['reason']=='verification_key_unavailable' and 'id' not in r
 with actor() as c:status=c.execute("select order_request_status103('qa103_native')").fetchone()[0];assert status['status']=='replayed' and status['input_match'] is None
 assert counts(a)==before
 return {'verify':'unresolved','status_only':'replayed-without-input-match','no_mutation':True,'fault_injection':'owner removed FK and secret in disposable DB'}
run('missing-old-secret-safe-classification',missing)
def rollback_float(a):
 upgrade(a)
 with actor() as c:c.execute('set extra_float_digits=0');original=call(c,payload());assert original['status']=='created';normal=call(c,payload());assert normal['status']=='replayed'
 a.execute(Path('tests/native103/rollback.sql').read_text())
 with actor() as c:c.execute('set extra_float_digits=0');r=call(c,payload())
 assert r['status']=='replayed',json.dumps({'same_typed_inputs':True,'normal':normal['status'],'after_rollback':r['status'],'reason':r.get('reason')})
 return r
run('QA103-S01-rollback-float-context',rollback_float)
def conversion_atomic(a):
 a.execute(Path('tests/native102/candidate.sql').read_text())
 for k in ['qa103_convert_a','qa103_convert_b']:
  with actor() as c:call(c,payload(k),'place_order')
 upgrade(a)
 a.execute("create function security_private.qa_fail103() returns trigger language plpgsql as $$begin if new.client_key='qa103_convert_b' then raise exception 'synthetic_conversion_failure';end if;return new;end$$;create trigger qa_fail103 before insert on security_private.order_request_fingerprints103 for each row execute function security_private.qa_fail103()")
 try:a.execute('select security_private.convert_bindings102_to103()');raise AssertionError('injection did not fire')
 except psycopg.errors.RaiseException:pass
 assert a.execute('select count(*) from security_private.order_request_bindings').fetchone()[0]==2
 assert counts(a)==(2,2,0)
 assert a.execute('select count(*) from orders where request_contract_version is not null').fetchone()[0]==0
 return {'old_bindings_retained':2,'new_bindings':0,'partial_markers':0}
run('conversion-failure-atomic-independent',conversion_atomic)
Path('review103/native-results.json').write_text(json.dumps(results,indent=2));print(json.dumps(results,indent=2));sys.exit(1 if any(not r['passed'] for r in results) else 0)
