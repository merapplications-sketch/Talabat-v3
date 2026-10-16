"""Patch 36 operations on a local PostgreSQL: the read-only verification queries run and change nothing; the rollback refuses
while website requests / partner banners exist, then restores patch 19/26 exactly; the patch can be applied again afterwards.
  python3 tools/patch36_ops_check.py [database]   (default t36; rebuilt with sql/test_patch36.sql first)"""
import subprocess,sys,os,re
DB=sys.argv[1] if len(sys.argv)>1 else 't36';root=os.path.abspath(os.path.join(os.path.dirname(__file__),'..'));fails=[]
def ok(c,m):
    print(('PASS ' if c else 'FAIL ')+m)
    if not c: fails.append(m)
def run(args,inp=None): r=subprocess.run(['psql','-d',DB,'-X']+args,capture_output=True,text=True,cwd=root,input=inp);return r.stdout+r.stderr
def q(sql): return subprocess.run(['psql','-d',DB,'-X','-At','-c',sql],capture_output=True,text=True).stdout.strip()
r=run(['-q','-f','sql/test_patch36.sql']);m=re.search(r'PATCH36 (\d+)/(\d+)',r);ok(bool(m) and m.group(1)==m.group(2),'test database built')
snap=lambda:q("select md5(string_agg(t,'|' order by t)) from (select row_to_json(s)::text t from store_requests s union all select row_to_json(b)::text from banners b union all select row_to_json(x)::text from lead_settings x) z")
s0=snap();out=run(['-f','sql/verify_patch36_readonly.sql'])
ok('ERROR' not in out and 'ROLLBACK' in out,'read-only verification queries run without error')
ok(snap()==s0,'... and change nothing')
ok('banners_link_ck' in out and 'pg_cron' not in out.split('ROLLBACK')[0][-5:],'... banner check and store_requests state listed')
# simple banner check again (as most likely in production), patch applied on it
q("alter table banners drop constraint if exists banners_link_ck; delete from banners where link_type is not null and link_type not in ('none','store','category'); alter table banners add constraint banners_link_type_ck check (link_type is null or link_type in ('none','store','category'))")
run(['-q','-f','sql/schema_patch36.sql'])
ok("'partner'::text" in q("select pg_get_constraintdef(oid) from pg_constraint where conname='banners_link_type_ck'"),'patch adds partner to the simple banner check')
n_leads=int(q("select count(*) from store_requests where kind='lead'"))
out=run(['-f','sql/rollback_patch36.sql'])
ok('website requests exist' in out and q("select to_regproc('lead_submit') is not null")=='t','rollback refuses while %d website requests exist; nothing changed'%n_leads)
q("insert into banners(title, link_type) values ('promo','partner')")
out=run(['-f','sql/rollback_patch36.sql'],None)
out=subprocess.run(['psql','-d',DB,'-X','-c',"set patch36.drop_leads = 'yes'",'-f','sql/rollback_patch36.sql'],capture_output=True,text=True,cwd=root);out=out.stdout+out.stderr
ok('banners link to the partner page' in out and q("select to_regproc('lead_submit') is not null")=='t','rollback refuses while a banner links to the partner page; nothing changed')
q("delete from banners where link_type='partner'")
n_branch=q("select count(*) from store_requests where kind='branch'")
out=subprocess.run(['psql','-d',DB,'-X','-c',"set patch36.drop_leads = 'yes'",'-f','sql/rollback_patch36.sql'],capture_output=True,text=True,cwd=root);out=out.stdout+out.stderr
ok('ERROR' not in out,'rollback with the explicit flag runs %s'%out.strip().splitlines()[-1:])
ok(q("select count(*) from pg_proc where proname like 'lead\\_%'")=='0' and q("select to_regclass('lead_attempts') is null and to_regclass('lead_settings') is null")=='t','lead functions and tables removed')
ok(q("select string_agg(column_name||':'||is_nullable,',' order by column_name) from information_schema.columns where table_name='store_requests' and column_name in ('kind','updated_at','updated_by','user_id','lat','lng')")=='lat:NO,lng:NO,user_id:NO','store_requests back to patch 19/26 (no kind; owner and location required)')
ok(q("select pg_get_constraintdef(oid) from pg_constraint where conname='store_requests_status_check'")=="CHECK ((status = ANY (ARRAY['pending'::text, 'approved'::text, 'rejected'::text])))",'status check restored')
ok(q("select count(*) from store_requests")==n_branch,'branch requests kept (%s)'%n_branch)
ok(q("select pg_get_constraintdef(oid) from pg_constraint where conname='banners_link_type_ck'")=="CHECK (((link_type IS NULL) OR (link_type = ANY (ARRAY['none'::text, 'store'::text, 'category'::text]))))",'banner check back to its original values')
r=q("set role authenticated; select set_config('request.jwt.claim.sub','e0000000-0000-0000-0000-00000000000e',false); select (request_store('After rollback','rest','+992900000055','',38.5,68.7) is not null)::text")
ok(r.endswith('true'),'a branch request still works after the rollback')
out=run(['-q','-f','sql/schema_patch36.sql'])
ok('ERROR' not in out and q("select to_regproc('lead_submit') is not null")=='t','patch 36 can be applied again after the rollback')
print('PATCH36 OPS FAILS',len(fails));sys.exit(1 if fails else 0)
