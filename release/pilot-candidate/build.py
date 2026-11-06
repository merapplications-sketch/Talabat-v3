"""Build an exact, credential-free review package. No network or deployment."""
import pathlib,subprocess,json,hashlib,zipfile,sys
R=pathlib.Path(__file__).resolve().parents[2];BASE='b2f84d869c546bbffb09b3474ef11be1b9d9ccb2'
def git(*args):return subprocess.check_output(['git',*args],cwd=R)
paths=git('ls-tree','-r','--name-only',BASE).decode().splitlines()
order=['sql/proposed/admin_finance_integrity_20261101.sql','sql/proposed/admin_finance_receipts_20261102.sql']+sorted(x for x in paths if x.startswith('sql/proposed/pilot_'))
runtime=['customer.html','merchant.html','driver.html','admin.html','talabat-core.js']+[x for x in paths if x.startswith('assets/')]
chosen=runtime+order+[x for x in paths if x.startswith(('ops/','tests/pilot/','tests/base-lab/web/'))]+['tests/base-lab/package.json','tests/base-lab/package-lock.json']
files={p:git('show',BASE+':'+p) for p in sorted(set(chosen))}
manifest={'source_commit':BASE,'candidate_branch':'candidate/pilot-readiness-20261105','deployment_authorized':False,'live_baseline_matched':False,'upgrade_order':order,'files':[{'path':p,'group':'runtime' if p in runtime else 'upgrade' if p in order else 'lab_or_operations','sha256':hashlib.sha256(b).hexdigest()} for p,b in files.items()]}
(R/'release/pilot-candidate/manifest.json').write_text(json.dumps(manifest,indent=2)+'\n')
if len(sys.argv)>1:
 out=pathlib.Path(sys.argv[1]).resolve();out.parent.mkdir(parents=True,exist_ok=True)
 docs=[p for p in (R/'release/pilot-candidate').glob('*') if p.is_file() and p.suffix in ['.md','.py','.json']]+[R/'docs/OWNER-AGREEMENTS-AR.md',R/'docs/RESUME-AR.md',R/'tests/pilot/candidate-upgrade.py',R/'.github/workflows/pilot-candidate.yml']+list((R/'docs/pilot-20261105/candidate').glob('*'))
 package_hashes={p:hashlib.sha256(b).hexdigest() for p,b in files.items()}
 package_hashes.update({p.relative_to(R).as_posix():hashlib.sha256(p.read_bytes()).hexdigest() for p in docs if p.is_file()})
 with zipfile.ZipFile(out,'w',zipfile.ZIP_DEFLATED) as z:
  z.writestr('PACKAGE-CONTENTS.json',json.dumps(package_hashes,indent=2))
  z.writestr('START-HERE.txt','TALABOT isolated candidate; source '+BASE+'\nRead docs/pilot-20261105/candidate/HANDOFF.md and release/pilot-candidate/HOST-UPGRADE-ROLLBACK.md.\nDo not serve raw HTML against live Supabase. Use bash tests/pilot/cash/run.sh with Docker locally.\nNo production approval; no historical balances rewritten.\n')
  for p,b in files.items():z.writestr(p,b)
  for p in docs:
   if p.is_file():z.write(p,p.relative_to(R).as_posix())
 with zipfile.ZipFile(out) as z:assert z.testzip() is None
 print(json.dumps({'archive':str(out),'sha256':hashlib.sha256(out.read_bytes()).hexdigest(),'source_commit':BASE,'files':len(files)}))
else:print(json.dumps({'manifest_files':len(files),'source_commit':BASE}))
