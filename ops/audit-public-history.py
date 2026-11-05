"""Offline detection across fetched Git objects; no credential validation or values.
Report only token kind, SHA256 fingerprint and blob/path; archives stay opaque.
"""
import base64,hashlib,json,os,pathlib,re,subprocess,time
started=time.monotonic()
rows=subprocess.check_output(['git','rev-list','--objects','--all'],text=True).splitlines()
objects={r.split(' ',1)[0]:(r.split(' ',1)[1]if' 'in r else'')for r in rows}
check=subprocess.run(['git','cat-file','--batch-check=%(objectname) %(objecttype) %(objectsize)'],input='\n'.join(objects)+'\n',text=True,capture_output=True,check=True)
blobs=[];skipped=[]
for row in check.stdout.splitlines():
 sha,kind,size=row.split();size=int(size)
 if kind=='blob':
  if size<=8*1024*1024:blobs.append((sha,size))
  else:skipped.append({'blob':sha,'path':objects[sha],'bytes':size})
patterns=[('github_token',re.compile(rb'gh[pousr]_[A-Za-z0-9_]{32,255}')),('github_fine_grained',re.compile(rb'github_pat_[A-Za-z0-9_]{40,255}')),('supabase_secret_key',re.compile(rb'sb_secret_[A-Za-z0-9_-]{12,255}')),('private_key_marker',re.compile(rb'-----BEGIN (?:RSA |EC |OPENSSH )?PRIVATE KEY-----'))]
jwts=re.compile(rb'eyJ[A-Za-z0-9_-]{8,}\.[A-Za-z0-9_-]{8,}\.[A-Za-z0-9_-]{10,}')
findings=[];total=0
# Stream only selected blobs to keep memory bounded and never print their content.
for sha,size in blobs:
 data=subprocess.check_output(['git','cat-file','blob',sha]);total+=len(data)
 hits=[]
 for kind,pat in patterns:hits.extend((kind,m.group(0))for m in pat.finditer(data))
 for m in jwts.finditer(data):
  try:
   payload=m.group(0).split(b'.')[1];obj=json.loads(base64.urlsafe_b64decode(payload+b'='*((4-len(payload)%4)%4)))
   if obj.get('role')=='service_role':hits.append(('service_role_jwt',m.group(0)))
  except Exception:pass
 for kind,value in hits:
  item={'kind':kind,'fingerprint_sha256':hashlib.sha256(value).hexdigest(),'blob':sha,'historical_path':objects[sha]}
  if item not in findings:findings.append(item)
result={'source':os.environ.get('GITHUB_SHA'),'live':False,'remote_credential_validation':False,'coverage':'all locally fetched public branch ancestry and Git blob contents; no provider secrets/settings or decompression of archive contents','refs':subprocess.check_output(['git','for-each-ref','--format=%(refname) %(objectname)','refs/remotes/origin'],text=True).splitlines(),'commits':int(subprocess.check_output(['git','rev-list','--all','--count'],text=True)),'scanned_blobs':len(blobs),'scanned_bytes':total,'oversize_skipped':skipped,'suspected_findings':findings,'no_findings':not findings,'duration_s':round(time.monotonic()-started,2)}
p=pathlib.Path('docs/pilot-20261105/followup');p.mkdir(parents=True,exist_ok=True);(p/'history-audit-result.json').write_text(json.dumps(result,indent=2)+'\n')
import zlib
print('HISTORY_AUDIT_ZLIB_BASE64='+base64.b64encode(zlib.compress(json.dumps(result).encode())).decode(),flush=True)
print(json.dumps({'commits':result['commits'],'blobs':len(blobs),'suspected_findings':len(findings),'oversize_skipped':len(skipped)}),flush=True)
