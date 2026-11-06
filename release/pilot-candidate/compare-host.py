"""Offline declaration/hash comparison. Never connects to a host or runs SQL."""
import json,pathlib,sys
root=pathlib.Path(__file__).parent
m=json.loads((root/'manifest.json').read_text());h=json.loads(pathlib.Path(sys.argv[1]).read_text())
missing=[];mismatched=[]
for f in m['files']:
 if f['group'] not in ['runtime','upgrade']:continue
 values=h.get('runtime_hashes' if f['group']=='runtime' else 'applied_patch_hashes',{})
 if f['path'] not in values:missing.append(f['path'])
 elif values[f['path']]!=f['sha256']:mismatched.append(f['path'])
gates=[x for x in ['isolated','full_schema_reviewed','auth_smtp_redirects_reviewed','rest_realtime_storage_reviewed','operational_acceptance_complete'] if h.get(x) is not True]
result={'hashes_match':not missing and not mismatched,'missing':missing,'mismatched':mismatched,'unaccepted_gates':gates,'ready':not missing and not mismatched and not gates,'limit':'Supplied declarations only; not independent host inspection or permission to deploy'}
print(json.dumps(result,indent=2));sys.exit(0 if result['ready'] else 2)
