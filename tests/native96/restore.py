import os,json,hashlib
from pathlib import Path
import psycopg
assert os.environ.get('PGHOST')=='127.0.0.1'
def digest(db):
 with psycopg.connect(dbname=db) as c:
  tables=c.execute("select schemaname,tablename from pg_tables where schemaname in ('public','finance_private','fulfillment_private','security_private') order by 1,2").fetchall()
  result={}
  for schema,table in tables:
   rows=c.execute(psycopg.sql.SQL("select coalesce(jsonb_agg(to_jsonb(t) order by to_jsonb(t)::text),'[]'::jsonb) from {}.{} t").format(psycopg.sql.Identifier(schema),psycopg.sql.Identifier(table))).fetchone()[0]
   result[schema+'.'+table]=hashlib.sha256(json.dumps(rows,sort_keys=True).encode()).hexdigest()
  return result
before=digest('postgres');after=digest('native95_restored');assert before==after
Path('native95-restore.json').write_text(json.dumps({'passed':True,'tables':len(before),'synthetic_only':True,'scope':'pg_dump restored to separate database on isolated CI service; not provider backup or disaster recovery'},indent=2))
# Relations, uniqueness, function behavior and transaction rollback in restored DB.
with psycopg.connect(dbname='native95_restored',autocommit=True) as c:
 row=c.execute("select id,customer_id,client_key,store_id from orders order by id limit 1").fetchone()
 for name,sql,args,expected in [
  ('foreign key',"insert into order_items(order_id,qty) values(-1,1)",(), '23503'),
  ('one wallet spend',"insert into wallet_entries(user_id,amount,kind,order_id) values(%s,-5,'spend',%s)",(row[1],row[0]),'23505')]:
  try:c.execute(sql,args);raise AssertionError(name+' was not enforced')
  except psycopg.Error as e:assert e.sqlstate==expected
 original=c.execute("select pg_get_functiondef('happy_hour_pct(uuid)'::regprocedure)").fetchone()[0]
 c.execute('begin');c.execute("create or replace function happy_hour_pct(uuid) returns int language sql as $$select 99$$");c.execute('rollback')
 assert c.execute("select pg_get_functiondef('happy_hour_pct(uuid)'::regprocedure)").fetchone()[0]==original
 c.execute("select set_config('request.jwt.claims',%s,false)",(json.dumps({'sub':str(row[1]),'aal':'aal1','session_id':'50000000-0000-4000-8000-000000000092'}),));c.execute('set role authenticated')
 got=c.execute("select place_order(p_store=>%s::uuid,p_items=>'[]'::jsonb,p_address=>'synthetic',p_lat=>38.5,p_lng=>68.7,p_key=>%s)",(row[3],row[2])).fetchone()[0]
 assert got==row[0]
assert digest('postgres')==digest('native95_restored')
Path('native96-restore.json').write_text(json.dumps({'passed':True,'tables':len(before),'foreign_key':'23503','unique_spend':'23505','order_replay':True,'function_transaction_rollback':True,'limits':['same CI server separate database','not provider restore','transaction rollback is not deployed release rollback']},indent=2))
print('PASS synthetic restore relations, uniqueness, replay and transaction rollback')
