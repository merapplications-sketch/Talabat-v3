import os,json
from pathlib import Path
import psycopg
assert os.environ.get('PGHOST')=='127.0.0.1'
B='10000000-0000-4000-8000-000000000092'
with psycopg.connect(dbname='candidate102_restored') as c:
 before=c.execute("select count(*),(select count(*) from wallet_entries where kind='spend') from orders").fetchone()
 assert before==(1,1)
 uid,key,oid,request=c.execute('select customer_id,client_key,order_id,request from security_private.order_request_bindings').fetchone()
 assert str(uid)==B and key=='request102_deadlock'
 c.execute("select set_config('request.jwt.claims',%s,false)",(json.dumps({'sub':B}),));c.execute('set role authenticated')
 values=list(request);values[1]=json.dumps(values[1]);values[11]=json.dumps(values[11]);values.insert(8,key)
 result=c.execute('select place_order(%s::uuid,%s::jsonb,%s::numeric,%s::text,%s::text,%s::float8,%s::float8,%s::text,%s::text,%s::numeric,%s::numeric,%s::int,%s::jsonb)',values).fetchone()[0]
 assert result==oid
 c.execute('reset role');assert c.execute("select count(*),(select count(*) from wallet_entries where kind='spend') from orders").fetchone()==before
Path('native102-restore.json').write_text(json.dumps({'passed':True,'orders':1,'spends':1,'binding_restored':True,'scope':'separate native synthetic database, not provider backup or Storage restore'}))
