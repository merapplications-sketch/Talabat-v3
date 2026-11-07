#!/usr/bin/env python3
import pathlib,sys,subprocess,json
p=pathlib.Path(__file__).parent
source,vendor=sys.argv[1:3]
subprocess.run(['node','--check',source],check=True)
base=json.loads(subprocess.check_output(['node',str(p/'test-auth-telemetry.cjs'),source]))
assert base['passed']==base['total']
results=[]
for mode in ['success','error','reject']:
 r=json.loads(subprocess.check_output(['node',str(p/'test-signout.cjs'),source,vendor,mode]))
 assert r['logout']['reloadedDespiteError']==(mode=='success')
 assert r['logout']['errorShown']==(mode!='success')
 assert r['recovery']['errorShown']==(mode!='success')
 assert r['recovery']['loginMessage'].startswith('resetDone')
 results.append({'mode':mode,'passed':True,'result':r})
print(json.dumps({'auth_telemetry':base,'signout':results,'total_passed':base['total']+len(results)},indent=2))
