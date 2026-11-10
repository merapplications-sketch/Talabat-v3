import fs from 'node:fs';import path from 'node:path';import {spawnSync} from 'node:child_process';
const dest=path.resolve(process.argv[2]);fs.mkdirSync(dest,{recursive:true});const results=[];
function run(id,args,env={}){const r=spawnSync(process.execPath,args,{encoding:'utf8',timeout:180000,maxBuffer:8*1024*1024,env:{...process.env,...env}});fs.writeFileSync(path.join(dest,id+'.log'),(r.stdout||'')+(r.stderr||''));results.push({id,status:r.status===0&&!r.error?'passed':'failed',exit:r.status});}
try{
 run('worker-test-assembly',['scripts/ci99/worker-fixture.mjs']);
 run('headers',['--test','tests/headers.test.mjs']);run('csp-report',['--test','tests/csp-report.test.mjs']);
 run('qa-sessions52',['tests/qa-sessions52.cjs']);run('driver-permissions',['tests/driver-permissions-isolated.mjs']);
 run('order-transaction92-fixed',['tests/order-transaction92.mjs'],{ORDER_FUNCTION:'docs/review/continuation92/place_order.fixed.sql'});
 run('http99-transport',['--test','tests/http99/transport.test.mjs']);run('http99-wire-fixture',['--test','tests/http99/integration.test.mjs']);
}finally{fs.rmSync('dist',{recursive:true,force:true});}
const blocked=[{id:'build-gate',reason:'missing recovered .openai configuration; original build also requires private db-evidence-binding; assertions retained'},{id:'fixture-cache56',reason:'functions/qa-proof-cache56/index.ts absent from recovered source and remote tree'},{id:'db-evidence-binding',reason:'private attestation and protected evidence intentionally not exported'},{id:'hosted-http-rbac',reason:'authorized user sessions unavailable'},{id:'provider-storage-revocation',reason:'same-URL provider authorization evidence unavailable'}];
fs.writeFileSync(path.join(dest,'report.json'),JSON.stringify({scope:'public isolated test subset; not full release acceptance',results,blocked,production_ready:false},null,2));console.log(JSON.stringify({results,blocked}));if(results.some(x=>x.status!=='passed'))process.exitCode=1;
