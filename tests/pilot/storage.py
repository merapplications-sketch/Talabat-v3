"""New real Supabase Storage API / private proof / file+metadata restore coverage.
Only Docker loopback endpoints. This does not verify hosted Storage settings.
"""
import base64, hashlib, json, os, pathlib, subprocess, sys, time, urllib.request, urllib.error
import lab

# Synthetic JPEG, not a customer or driver photo.
JPEG=base64.b64decode('/9j/4AAQSkZJRgABAQEASABIAAD/2wBDAP//////////////////////////////////////////////////////////////////////////////////////2wBDAf//////////////////////////////////////////////////////////////////////////////////////wAARCAABAAEDASIAAhEBAxEB/8QAFQABAQAAAAAAAAAAAAAAAAAAAAf/xAAUEAEAAAAAAAAAAAAAAAAAAAAA/9oADAMBAAIQAxAAAAF//8QAFBABAAAAAAAAAAAAAAAAAAAAAP/aAAgBAQABBQJ//8QAFBEBAAAAAAAAAAAAAAAAAAAAAP/aAAgBAwEBPwF//8QAFBEBAAAAAAAAAAAAAAAAAAAAAP/aAAgBAgEBPwF//8QAFBABAAAAAAAAAAAAAAAAAAAAAP/aAAgBAQAGPwJ//8QAFBABAAAAAAAAAAAAAAAAAAAAAP/aAAgBAQABPyF//9oADAMBAAIAAwAAABD/xAAUEQEAAAAAAAAAAAAAAAAAAAAA/9oACAEDAQE/EB//xAAUEQEAAAAAAAAAAAAAAAAAAAAA/9oACAECAQE/EB//xAAUEAEAAAAAAAAAAAAAAAAAAAAA/9oACAEBAAE/EB//2Q==')
COMPOSE=['docker','compose','--env-file',str(lab.HERE/'.runtime.env'),'-f',str(lab.HERE/'compose.yml')]

def prepare():
 with (lab.HERE/'.runtime.env').open('a')as f:
  f.write('LAB_STORAGE_ANON='+lab.jwt('anon')+'\nLAB_STORAGE_SERVICE='+lab.jwt('service_role')+'\n')


def call(token,method,path,data=None,mime=None,port=5000):
 assert port in(5000,5001)
 if isinstance(data,dict):data=json.dumps(data).encode();mime='application/json'
 headers={'Authorization':'Bearer '+token}if token else{}
 if mime:headers['Content-Type']=mime
 req=urllib.request.Request(f'http://127.0.0.1:{port}'+path,data=data,headers=headers,method=method)
 try:
  with urllib.request.urlopen(req,timeout=20)as r:return r.status,r.read()
 except urllib.error.HTTPError as e:return e.code,e.read()


def setup_policy():
 lab.wait(lambda:call(None,'GET','/status')[0]==200,'storage_api',90)
 source=(lab.ROOT/'sql/schema_patch34.sql').read_text();start=source.index('do $$',source.index('-- ---------- private photo bucket'))
 end=source.index('end $$;',start)+len('end $$;')
 with lab.db()as c:c.execute(source[start:end],prepare=False)


def test():
 result={'source':os.environ.get('GITHUB_SHA'),'environment':'real Supabase Storage API1.81.0 + native PostgreSQL, actual patch34 private proof policies, synthetic JPEG and real GoTrue JWTs','live':False,'hosted_Storage':False,'checks':[]}
 def ok(v,name):
  assert v,name
  result['checks'].append({'name':name,'pass':True});print('PASS storage '+name,flush=True)
 try:
  setup_policy();oid=lab.order(lab.bearer('outsider'));lab.rpc(lab.bearer('merchant'),'set_order_status',{'p_id':oid,'p_to':'preparing'});lab.rpc(lab.bearer('admin'),'admin_assign_driver',{'p_order':oid,'p_driver':lab.uid('driver1')});lab.rpc(lab.bearer('merchant'),'set_order_status',{'p_id':oid,'p_to':'ready'});lab.rpc(lab.bearer('driver1'),'set_order_status',{'p_id':oid,'p_to':'pickedup'})
  key=lab.uid('driver1')+'/'+str(oid)+'/syntheticproof01.jpg';result['object_path']=key;result['object_sha256']=hashlib.sha256(JPEG).hexdigest()
  for actor in['customer','driver2']:
   status,_=call(lab.bearer(actor),'POST','/object/proofs/'+key,JPEG,'image/jpeg');ok(status not in(200,201,204),'non-assigned '+actor+' cannot upload proof for another courier')
  status,_=call(lab.bearer('driver1'),'POST','/object/proofs/'+key,JPEG,'image/jpeg');ok(status in(200,201),'assigned courier uploads to actual private bucket')
  status,_=call(lab.bearer('driver1'),'POST','/object/proofs/'+key,JPEG,'image/jpeg');ok(status not in(200,201,204),'duplicate upload without upsert cannot replace proof')
  for actor in['customer','driver2','merchant']:
   status,_=call(lab.bearer(actor),'GET','/object/authenticated/proofs/'+key);ok(status!=200,'unrelated '+actor+' cannot read proof')
  status,body=call(lab.bearer('outsider'),'GET','/object/authenticated/proofs/'+key);ok(status==200 and body==JPEG,'order customer retrieves exact original private bytes')
  status,_=call(None,'GET','/object/public/proofs/'+key);ok(status!=200,'public URL cannot disclose private proof')
  status,body=call(lab.bearer('outsider'),'POST','/object/sign/proofs/'+key,{'expiresIn':1});ok(status==200,'authorized customer gets short-lived signed URL')
  signed=json.loads(body)['signedURL'];status,body=call(None,'GET',signed if signed.startswith('/object/')else'/object'+signed);ok(status==200 and body==JPEG,'signed URL reads exact uploaded bytes')
  time.sleep(2);status,_=call(None,'GET',signed if signed.startswith('/object/')else'/object'+signed);ok(status!=200,'expired signed link no longer reads proof')
  # A well-shaped but missing path must not serve as a proof of delivery.
  ghost=lab.uid('driver1')+'/'+str(oid)+'/missingproof0001.jpg'
  code,value=lab.request(3000,'/rpc/deliver_order',{'p_id':oid,'p_cash':65,'p_photo':ghost},lab.bearer('driver1'))
  result['nonexistent_proof_submission']={'status':code,'accepted':code in(200,204),'message':value.get('message')if isinstance(value,dict)else None}
  ok(code>=400,'server rejects a photo path with no stored proof object')
  lab.rpc(lab.bearer('driver1'),'deliver_order',{'p_id':oid,'p_cash':65,'p_photo':key})
  ok(True,'actual stored proof completes delivery through existing API')
  status,_=call(lab.bearer('driver1'),'DELETE','/object/proofs',{'prefixes':[key]});
  status,body=call(lab.bearer('outsider'),'GET','/object/authenticated/proofs/'+key);ok(status==200 and body==JPEG,'courier cannot erase retained delivery proof')
  result['pass']=True
 except Exception as e:result['pass']=False;result['error']=str(e)[:180];print('FAIL storage '+result['error'],flush=True)
 finally:lab.save(lab.HERE/'result-storage.json',result)
 if not result['pass']:raise SystemExit(1)


def restore():
 # New coverage only: Storage metadata + actual file bytes + authenticated read after restore.
 result={'source':os.environ.get('GITHUB_SHA'),'live':False,'scope':'isolated Storage metadata and actual local file restore; no live data or hosted buckets','checks':[]}
 def ok(v,name):
  assert v,name
  result['checks'].append({'name':name,'pass':True});print('PASS storage restore '+name,flush=True)
 try:
  before=json.loads((lab.HERE/'result-storage.json').read_text());key=before['object_path']
  with (lab.HERE/'.runtime-storage.dump').open('wb')as out:subprocess.run(COMPOSE+['exec','-T','db','pg_dump','-U','postgres','-Fc','talabot_pilot'],stdout=out,check=True)
  subprocess.run(COMPOSE+['exec','-T','db','createdb','-U','postgres','talabot_pilot_restore'],check=True)
  with (lab.HERE/'.runtime-storage.dump').open('rb')as inp:subprocess.run(COMPOSE+['exec','-T','db','pg_restore','-U','postgres','-d','talabot_pilot_restore','--exit-on-error'],stdin=inp,check=True)
  metadata=[]
  for name in['talabot_pilot','talabot_pilot_restore']:
   with lab.db(name)as c:
    rows=c.execute("select bucket_id,name,metadata from storage.objects order by bucket_id,name").fetchall();metadata.append(hashlib.sha256(json.dumps(rows,default=str).encode()).hexdigest())
  ok(metadata[0]==metadata[1],'restored Storage object metadata exactly matches original')
  with (lab.HERE/'.runtime-storage.tar').open('wb')as out:subprocess.run(COMPOSE+['exec','-T','storage','tar','-C','/var/lib/storage','-cf','-','.'],stdout=out,check=True)
  with (lab.HERE/'.runtime-storage.tar').open('rb')as inp:subprocess.run(COMPOSE+['run','--rm','--no-deps','--entrypoint','sh','storage-restore','-c','tar -C /var/lib/storage -xf -'],stdin=inp,check=True)
  subprocess.run(COMPOSE+['up','-d','storage-restore'],check=True)
  lab.wait(lambda:call(None,'GET','/status',port=5001)[0]==200,'restored_storage',90)
  status,body=call(lab.bearer('outsider'),'GET','/object/authenticated/proofs/'+key,port=5001);ok(status==200 and hashlib.sha256(body).hexdigest()==before['object_sha256'],'restored service returns identical proof bytes to authorized customer')
  status,_=call(lab.bearer('customer'),'GET','/object/authenticated/proofs/'+key,port=5001);ok(status!=200,'restored service retains cross-customer read denial')
  result['metadata_sha256']=metadata[0];result['file_sha256']=before['object_sha256'];result['backup_exported']=False;result['pass']=True
 except Exception as e:result['pass']=False;result['error']=type(e).__name__+':'+str(e)[:120];print('FAIL storage restore '+result['error'],flush=True)
 finally:lab.save(lab.HERE/'result-storage-restore.json',result)
 if not result['pass']:raise SystemExit(1)

if __name__=='__main__':{'prepare':prepare,'test':test,'restore':restore}[sys.argv[1]]()
