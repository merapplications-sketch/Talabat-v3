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
print('PASS synthetic dump/restore, '+str(len(before))+' tables')
