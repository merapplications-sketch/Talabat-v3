import os,json
from pathlib import Path
import psycopg
import sys
sys.path.insert(0,'tests/native103')
from test_sql import BASE,MIGRATION,args,call,B
MIGRATION+=''.join(Path('tests/native104/'+p).read_text() for p in ['schema.sql','functions.sql','lifecycle.sql'])
MIGRATION+=Path('tests/native105/resources.sql').read_text()+"insert into security_private.closure_policy105(singleton,max_rows,max_account_rows,max_reason_bytes) values(true,4,2,128);"
MIGRATION+=Path('tests/native106/isolation.sql').read_text()
assert os.environ.get('PGHOST')=='127.0.0.1'
if os.environ.get('PREPARE_RESTORE')=='1':
 a=psycopg.connect(autocommit=True);a.execute('create database restore106_source');a.close()
 with psycopg.connect(dbname='restore106_source') as c:
  c.execute(BASE);c.execute('create schema extensions;create extension pgcrypto with schema extensions');c.execute(MIGRATION);c.execute('insert into security_private.order_request_keys103 values(1,%s,true)',(os.urandom(32),));c.execute("select set_config('request.jwt.claims',%s,false)",(json.dumps({'sub':B}),));c.execute('set role authenticated');assert call(c,args())['status']=='created'
  rejected=args('restore106_rejected');rejected[4]='';assert call(c,rejected,'place_order104')['closed'] is True
else:
 with psycopg.connect(dbname='restore106_target') as c:
  c.execute("select set_config('request.jwt.claims',%s,false)",(json.dumps({'sub':B}),));c.execute('set role authenticated');r=call(c,args());assert r['status']=='replayed' and r['input_match'] is True;c.execute('reset role');assert c.execute("select count(*),(select count(*) from wallet_entries where kind='spend') from orders").fetchone()==(1,1)
 with psycopg.connect(dbname='restore106_target') as c:
  c.execute("select set_config('request.jwt.claims',%s,false)",(json.dumps({'sub':B}),));c.execute('set role authenticated');assert call(c,args('restore106_rejected'),'place_order104')['closed'] is True
 with psycopg.connect(dbname='restore106_target') as c:
  assert c.execute('select max_rows,max_account_rows from security_private.closure_policy105').fetchone()==(4,2)
  assert c.execute("select count(*) from pg_trigger where tgname in ('closure_budget105','closure_no_truncate105')").fetchone()[0]==2
 Path('native106-restore.json').write_text(json.dumps({'passed':True,'binding_and_key_restored':True,'rejection_fence_restored':True,'orders':1,'spends':1,'scope':'separate synthetic database, not provider/Storage backup'}))
