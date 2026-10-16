"""Patch 36: requests sent AT THE SAME MOMENT (parallel database sessions) on a local PostgreSQL.
Builds the test database with sql/test_patch36.sql first, then fires parallel lead_submit calls as service_role.
  python3 tools/lead_race_check.py [database]      (default database: t36; needs a local superuser for psql)"""
import subprocess,sys,os,hashlib
DB=sys.argv[1] if len(sys.argv)>1 else 't36';root=os.path.abspath(os.path.join(os.path.dirname(__file__),'..'))
fails=[]
def ok(c,m):
    print(('PASS ' if c else 'FAIL ')+m)
    if not c: fails.append(m)
def psql(sql):
    return subprocess.run(['psql','-d',DB,'-At','-c',sql],capture_output=True,text=True).stdout.strip()
k=lambda t:hashlib.md5(t.encode()).hexdigest()+hashlib.md5((t+'#').encode()).hexdigest()
r=subprocess.run(['psql','-d',DB,'-q','-f','sql/test_patch36.sql'],capture_output=True,text=True,cwd=root).stdout
import re as _re
m=_re.search(r'PATCH36 (\d+)/(\d+)',r)
ok(bool(m) and m.group(1)==m.group(2),'base test database built (%s)'%r.strip().splitlines()[-2:-1])
def race(n,calls):
    ps=[subprocess.Popen(['psql','-d',DB,'-At','-c',"set role service_role; select lead_submit('%s','rest','%s','%s',%s)"%(nm,ph,k(ph),("'%s'"%k('ip:'+cl)) if cl else 'null')],
        stdout=subprocess.PIPE,stderr=subprocess.PIPE,text=True) for nm,ph,cl in calls]
    return [p.communicate()[0].strip().splitlines()[-1] if p.wait()==0 else 'ERR' for p in ps]
psql("truncate lead_attempts; delete from store_requests where kind='lead'; update lead_settings set value=1000 where key in ('per_phone_day','per_client_hour','per_client_day','global_hour')")
# 1. 20 sessions, same phone, different clients
out=race(20,[('Race Cafe','+992931112233','10.0.0.%d'%i) for i in range(20)])
ok(out==['ok']*20,'20 parallel sends of one phone: every answer is the same «ok» (%s)'%sorted(set(out)))
ok(psql("select count(*) from store_requests where kind='lead' and phone='+992931112233'")=='1','... exactly ONE request created')
ok(psql("select string_agg(outcome||':'||n,',' order by outcome) from (select outcome,count(*) n from lead_attempts group by 1) x")=='created:1,duplicate:19','... 20 attempts counted: created 1, duplicate 19')
# 2. phone limit under a race: limit 3 → 1 created, 2 duplicate, rest limit (no window overrun)
psql("truncate lead_attempts; update lead_settings set value=3 where key='per_phone_day'")
out=race(12,[('Race Two','+992931112244','10.1.0.%d'%i) for i in range(12)])
ok(out==['ok']*12,'12 parallel sends, phone limit 3: all answers «ok» (nothing tells the phone apart)')
ok(psql("select string_agg(outcome||':'||n,',' order by outcome) from (select outcome,count(*) n from lead_attempts group by 1) x")=='created:1,duplicate:2,limit_phone:9','... limit kept exactly: created 1, duplicate 2, limit 9')
# 3. one client, many phones at once: client limit 5 per hour → exactly 5 accepted
psql("truncate lead_attempts; update lead_settings set value=1000 where key='per_phone_day'; update lead_settings set value=5 where key='per_client_hour'")
out=race(12,[('Race X%d'%i,'+99293200%04d'%i,'10.9.9.9') for i in range(12)])
ok(sorted(out)==['busy']*7+['ok']*5,'12 parallel sends from one client, limit 5: 5 ok, 7 busy (%s)'%sorted(out))
ok(psql("select count(*) from store_requests where kind='lead' and name like 'Race X%'")=='5','... exactly 5 requests created')
psql("update lead_settings set value=5 where key='per_client_hour'; update lead_settings set value=3 where key='per_phone_day'")
print('LEAD RACE FAILS',len(fails));sys.exit(1 if fails else 0)
