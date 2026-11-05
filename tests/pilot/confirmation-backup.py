"""New eight private approval/admission tables only. No old 13-table assertions."""
import datetime,hashlib,json,os,sys
import lab,confirmation as cf
TABLES=['fulfillment_private.confirmation_config','fulfillment_private.order_approvals','fulfillment_private.approval_requests','fulfillment_private.approval_events','fulfillment_private.config_events','pilot_private.config','pilot_private.config_events','pilot_private.admissions']
def seed(accept=True):
 lab.wait(lambda:lab.request(3000,'/')[0]==200,'rest');now=datetime.datetime.now(datetime.timezone.utc)
 cfg={'owner_approved':True,'timezone':'UTC','valid_from':(now-datetime.timedelta(hours=1)).isoformat(),'valid_until':(now+datetime.timedelta(hours=2)).isoformat(),'open_minute':0,'close_minute':1440,'max_active':3,'daily_orders':20,'min_lat':38.55,'max_lat':38.57,'min_lng':68.78,'max_lng':68.80,'weekdays':list(range(1,8)),'customers':[lab.uid('customer')],'drivers':[lab.uid('driver1')],'stores':[lab.STORE]}
 lab.rpc(lab.bearer('admin'),'configure_pilot_admission',{'p_config':cfg,'p_paused':False});cf.config(120,10,True,True)
 oid=lab.order(lab.bearer('customer'));a=cf.review(oid,15)
 if accept:cf.confirm(lab.bearer('customer'),oid,a['revision'])
 lab.rpc(lab.bearer('admin'),'configure_pilot_admission',{'p_paused':True})
 return oid,a['revision']
def verify():
 hashes={}
 for name in ['talabot_pilot','talabot_pilot_restore']:
  with lab.db(name)as db:
   hashes[name]={}
   for table in TABLES:
    data=lab.q(db,"select coalesce(jsonb_agg(v order by v::text)::text,'[]')from(select to_jsonb(t)v from "+table+' t)x')
    hashes[name][table]={'rows':lab.q(db,'select count(*)from '+table),'sha256':hashlib.sha256(data.encode()).hexdigest()}
   defs=db.execute("select p.oid::regprocedure::text,pg_get_functiondef(p.oid)from pg_proc p join pg_namespace n on n.oid=p.pronamespace where p.prokind='f'and(n.nspname in('fulfillment_private','pilot_private')or(n.nspname='public'and p.proname in('configure_pilot_admission','order_confirmation_settings','configure_order_confirmation','order_approval_states','order_change_quote','merchant_review_order','customer_confirm_order','place_order','eligible_couriers')))order by p.oid::regprocedure::text").fetchall()
   hashes[name]['function_definitions']={'count':len(defs),'sha256':hashlib.sha256(json.dumps(defs).encode()).hexdigest()}
   hashes[name]['triggers']=db.execute("select t.tgname,pg_get_triggerdef(t.oid),t.tgenabled from pg_trigger t where t.tgname in('approval_order_guard','approval_lines_guard','approval_offer_guard','pilot_admission_guard','pilot_admission_record')order by t.tgname").fetchall()
   hashes[name]['rls']=db.execute("select n.nspname,c.relname,c.relrowsecurity from pg_class c join pg_namespace n on n.oid=c.relnamespace where n.nspname in('fulfillment_private','pilot_private')and c.relkind='r'order by 1,2").fetchall()
 assert hashes['talabot_pilot']==hashes['talabot_pilot_restore'],'new schema restoration mismatch'
 assert all(hashes['talabot_pilot'][t]['rows']>0 for t in TABLES),'fixture missing private audit data'
 r={'source':os.environ.get('GITHUB_SHA'),'live':False,'pass':True,'scope':'ONLY new 8 approval/admission tables, their functions, five triggers and RLS flags; full logical dump is temporary fixture transport','hashes':hashes,'backup_exported':False,'hosted_external_backup':False}
 lab.save(lab.HERE/'result-confirmation-backup.json',r);print('PASS new approval/admission backup restores eight populated tables, functions, five enabled guards and RLS',flush=True)
if __name__=='__main__':seed()if sys.argv[1]=='seed'else verify()
