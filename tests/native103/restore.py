import os,json
from pathlib import Path
import psycopg
from test_sql import BASE,MIGRATION,args,call,B
assert os.environ.get('PGHOST')=='127.0.0.1'
if os.environ.get('PREPARE_RESTORE')=='1':
 a=psycopg.connect(autocommit=True);a.execute('create database restore103_source');a.close()
 with psycopg.connect(dbname='restore103_source') as c:
  c.execute(BASE);c.execute('create schema extensions;create extension pgcrypto with schema extensions');c.execute(MIGRATION);c.execute('insert into security_private.order_request_keys103 values(1,%s,true)',(os.urandom(32),));c.execute("select set_config('request.jwt.claims',%s,false)",(json.dumps({'sub':B}),));c.execute('set role authenticated');assert call(c,args())['status']=='created'
else:
 with psycopg.connect(dbname='restore103_target') as c:
  c.execute("select set_config('request.jwt.claims',%s,false)",(json.dumps({'sub':B}),));c.execute('set role authenticated');r=call(c,args());assert r['status']=='replayed' and r['input_match'] is True;c.execute('reset role');assert c.execute("select count(*),(select count(*) from wallet_entries where kind='spend') from orders").fetchone()==(1,1)
 Path('native103-restore.json').write_text(json.dumps({'passed':True,'binding_and_key_restored':True,'orders':1,'spends':1,'scope':'separate synthetic database, not provider/Storage backup'}))
