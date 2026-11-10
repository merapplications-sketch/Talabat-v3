import fs from 'node:fs';import path from 'node:path';import {spawnSync} from 'node:child_process';import {createHash} from 'node:crypto';import {evaluate} from '../../tests/acceptance100/gate.mjs';
const dest=path.resolve(process.argv[2]);fs.mkdirSync(dest,{recursive:true});
fs.mkdirSync('functions/qa-proof-cache56',{recursive:true});fs.mkdirSync('.openai',{recursive:true});
fs.copyFileSync('tests/fixtures100/qa-proof-cache56.original.ts','functions/qa-proof-cache56/index.ts');fs.copyFileSync('tests/fixtures100/hosting.original.json','.openai/hosting.json');
const results=[];
for(const[id,args]of [['fixture-cache56',['tests/fixture-cache56.cjs']],['acceptance100',['--test',...fs.readdirSync('tests/acceptance100').filter(x=>x.endsWith('.test.mjs')).sort().map(x=>'tests/acceptance100/'+x)]]]){const r=spawnSync(process.execPath,args,{encoding:'utf8',timeout:120000,maxBuffer:4*1024*1024});fs.writeFileSync(path.join(dest,id+'.log'),(r.stdout||'')+(r.stderr||''));results.push({id,status:r.status===0?'passed':'failed'});if(r.status!==0)console.error(((r.stdout||'')+(r.stderr||'')).slice(-6000));}
const hashes={};for(const folder of ['tests/acceptance100','tests/fixtures100'])for(const f of fs.readdirSync(folder)){const p=folder+'/'+f;hashes[p]=createHash('sha256').update(fs.readFileSync(p)).digest('hex')}
const acceptance=evaluate(process.env.GITHUB_SHA||'f7244a94dfd74a3c2aca6cbc087849482511f6cc',{});
const report={scope:'public fixture tests and acceptance-validator tests; no hosted acceptance',results,hashes,acceptance,blocked:{buildGate:'original assertion fails before customer-handler because private evidence is missing',privateDB:'original private attestation required',hosted:'approved user-session transport unavailable'}};
fs.writeFileSync(path.join(dest,'report.json'),JSON.stringify(report,null,2));console.log(JSON.stringify(report));if(results.some(x=>x.status!=='passed'))process.exitCode=1;
