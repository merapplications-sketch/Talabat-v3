"""Offline source inventory; not a claim about installed live functions or ACLs."""
import json,re,hashlib
from pathlib import Path
root=Path(__file__).resolve().parents[2]
records=[]
pattern=re.compile(r'create\s+(?:or\s+replace\s+)?function\s+((?:public\.)?[a-z_][a-z_0-9]*)\s*\((.*?)\)(.*?)\bas\s+(\$[a-z_0-9]*\$)(.*?)\4',re.I|re.S)
for p in sorted((root/'sql').glob('schema_patch*.sql'),key=lambda p:int(re.search(r'patch(\d+)',p.name)[1])):
 for m in pattern.finditer(p.read_text()):
  name,args,attr,tag,body=m.groups()
  writes=sorted(set(re.findall(r'(?:insert\s+into|update|delete\s+from)\s+(?:public\.)?(orders|wallet_entries)\b',body,re.I)))
  if not writes:continue
  records.append({'file':str(p.relative_to(root)),'line':p.read_text()[:m.start()].count('\n')+1,'function':name,'arguments':re.sub(r'\s+',' ',args).strip(),'writes':writes,'security_definer':bool(re.search('security\\s+definer',attr,re.I)),'finance_guard':bool(re.search(r"has_perm\('finance'\)",body,re.I)),'support_guard':bool(re.search(r"has_perm\('support'\)",body,re.I)),'assigned_driver_guard':bool(re.search('driver_id.*auth.uid',body,re.I))})
client=[]
for p in [root/'talabat-core.js',root/'admin.html',root/'driver.html',root/'customer.html',root/'merchant.html']:
 if not p.exists():continue
 for i,line in enumerate(p.read_text().splitlines(),1):
  for m in re.finditer(r"\.from\(['\"](orders|wallet_entries)['\"]\)\s*\.([a-z]+)\(",line):
   client.append({'file':p.name,'line':i,'table':m[1],'first_operation':m[2]})
assert all(r['first_operation']=='select' for r in client), 'Review newly detected direct runtime mutation'
out={'base':'81c067c6f3697b805f4db2df05511a397a027abe','scope':'Static schema_patch17..34 and runtime direct table-call inventory, not complete live schema; regex may omit dynamic/indirect SQL. Historical versions are listed, not assumed installed.','historical_function_writers':records,'runtime_direct_calls':client,'live_snapshot_definitions':[f['proname'] for f in json.loads((root/'docs/continuity/admin-finance-audit/live-metadata.json').read_text())['functions']],'live_blockers':['Complete current pg_proc signatures/overloads and SECURITY DEFINER bodies absent from saved metadata','Current effective PUBLIC/role-inheritance/table/column ACLs and complete RLS absent','External/legacy client dependencies and frozen schema presence unverified'],'sha256':{str(p.relative_to(root)):hashlib.sha256(p.read_bytes()).hexdigest() for p in (root/'sql').glob('schema_patch*.sql')}}
(root/'docs/continuity/admin-finance-fix/compatibility-inventory.json').write_text(json.dumps(out,indent=2)+'\n')
print(json.dumps({'historical_writers':len(records),'runtime_direct_reads':len(client),'direct_runtime_writes':0,'live_inventory':'not executed'}))
