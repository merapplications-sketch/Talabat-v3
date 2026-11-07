import {spawnSync} from 'node:child_process';
import {createHash} from 'node:crypto';
import {readFileSync} from 'node:fs';
const core='public/talabat-core.js';
const vendor='public/assets/vendor/supabase-2.117.2.js';
// Local regression coverage. Provider/live-UI evidence remains a separate gate.
export const checks = [
 ['db-evidence-binding','node',['tests/db-regression-evidence.cjs']],
 ['auth-logout-recovery','python3',['tests/test-all.py',core,vendor]],
 ['auth-error-redaction','node',['tests/auth-error-redaction.cjs']],
 ['rpc-errors-boot-logout','node',['tests/security-errors-logout.cjs']],
 ['passive-signout','node',['tests/passive-signout.cjs',core]],
 ['proof-generation','node',['tests/proof-epoch.cjs',core]],
 ['proof-access','node',['tests/proof-access.cjs']],
 ['customer-auth-scope','node',['tests/customer-auth-scope.cjs']],
 ['mfa','node',['tests/mfa.cjs']],
 ['request-id-retry','node',['tests/request-id-compat.cjs']],
 ['customer-handler','python3',['tests/customer-recommendation-encoding.py','.']],
 ['admin-handler','python3',['tests/test-inline-context.py','public/admin.html',core]],
 ['image-limits','node',['tests/image-limits.cjs']],
 ['admin-idle','node',['tests/admin-idle.cjs']],
 ['driver-chat','node',['tests/driver-chat.cjs','public/driver.html']],
 ['merchant-report','node',['tests/merchant-report.cjs']],
 ['return-receipt','node',['tests/return-receipt.cjs']],
 ['map-policy','node',['tests/map-policy.cjs']]
];
export function runChecks(root, list=checks) {
 const results=[];
 for(const [id,command,args] of list) {
  const r=spawnSync(command,args,{cwd:root,encoding:'utf8',timeout:30000,maxBuffer:4*1024*1024});
  if(r.error || r.status!==0) {
   process.stderr.write((r.stderr||r.stdout||r.error?.message||'').slice(-6000));
   throw new Error(`Security regression gate failed: ${id}`);
  }
  results.push({id,status:'passed',output_sha256:createHash('sha256').update(r.stdout).digest('hex')});
  console.log(`Security gate: ${id} passed`);
 }
 return results;
}
export function sourceFingerprint(root) {
 const paths=[core,'public/customer.html','public/admin.html','public/merchant.html','public/driver.html','public/assets/mfa.js',...checks.map(x=>x[2][0]),'scripts/security-gate.mjs','scripts/build.mjs','worker/index.js','scripts/csp-policy.mjs'];
 return Object.fromEntries([...new Set(paths)].sort().map(p=>[p,createHash('sha256').update(readFileSync(`${root}/${p}`)).digest('hex')]));
}
