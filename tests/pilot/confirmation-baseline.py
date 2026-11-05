"""Only newly identified subsequent-order timing baseline edges."""
import os
import lab,confirmation as cf
import importlib.util
from pathlib import Path
spec=importlib.util.spec_from_file_location('backup_fixture',Path(__file__).with_name('confirmation-backup.py'));fixture=importlib.util.module_from_spec(spec);spec.loader.exec_module(fixture)
r={'source':os.environ.get('GITHUB_SHA'),'live':False,'checks':[],'environment':'native PG17 GoTrue/PostgREST isolated'}
def ok(v,n):
 assert v,n
 r['checks'].append({'name':n,'pass':True});lab.save(lab.HERE/'result-confirmation-baseline.json',r);print('PASS timing baseline '+n,flush=True)
fixture.seed();cf.config();lab.rpc(lab.bearer('admin'),'configure_pilot_admission',{'p_paused':False})
c=lab.bearer('customer');oid=lab.order(c);a=cf.state(c,oid)
ok(a['state']=='checkout_accepted'and a['snapshot']['prep_minutes']==20,'subsequent checkout keeps existing server preparation baseline; no mandatory extra consent for unchanged offer')
cf.denied(lab.bearer('merchant'),'set_prep_time',{'p_id':oid,'p_min':45},'order_change_requires_confirmation');r1=cf.review(oid,45)
ok(r1['needs_customer']and cf.state(c,oid)['state']=='awaiting_customer','first restaurant review cannot silently lengthen subsequent checkout from 20 to 45 minutes')
oid2=lab.order(c);r2=cf.review(oid2,12);r3=cf.review(oid2,18)
ok(not r2['needs_customer']and r3['needs_customer'],'a shortened promise becomes the conservative delay baseline; later increases still require consent when threshold is unapproved')
r['pass']=True;lab.save(lab.HERE/'result-confirmation-baseline.json',r)
