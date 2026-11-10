import fs from 'node:fs';import path from 'node:path';import{spawnSync}from'node:child_process';
import{checks as originalChecks}from'../../scripts/security-gate.mjs';
const checks=originalChecks.map(([id,cmd,args])=>[id,cmd,id==='cart-resume91'?args.map(a=>a==='tests/cart-resume91.test.mjs'?'tests/native104/cart-regression.test.mjs':a):args]);
const dest=path.resolve(process.argv[2]);fs.mkdirSync(dest,{recursive:true});const results=[];
const cases=['finance-lost-ack51','loyalty-settings-render','merchant-report-boundaries54','retired-pilot-consumers'].map(n=>[n,['tests/'+n+'.cjs']]);
cases.push(['qa-network67',['--test','tests/qa-network67.test.mjs']],['auth-telemetry',['tests/test-auth-telemetry.cjs','public/talabat-core.js']],['signout-error',['tests/test-signout.cjs','public/talabat-core.js','public/assets/vendor/supabase-2.117.2.js']],['http97-runner-unit',['--test','tests/http97/runner.test.mjs']]);
for(const[id,args]of cases){const r=spawnSync(process.execPath,args,{encoding:'utf8',timeout:30000});results.push({id,status:r.status===0?'passed':'failed'});fs.writeFileSync(path.join(dest,id+'.log'),(r.stdout||'')+(r.stderr||''));}
for(const[id,cmd,args]of checks.filter(x=>x[0]!=='db-evidence-binding')){const r=spawnSync(cmd,args,{encoding:'utf8',timeout:30000,maxBuffer:4*1024*1024});results.push({id,status:r.status===0?'passed':'failed'});fs.writeFileSync(path.join(dest,id+'.log'),(r.stdout||'')+(r.stderr||''));}
fs.writeFileSync(path.join(dest,'report.json'),JSON.stringify({scope:'local VM and test runner units; no hosted HTTP',results},null,2));console.log(JSON.stringify(results));if(results.some(x=>x.status!=='passed'))process.exitCode=1;
