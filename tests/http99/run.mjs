// Secret configuration must be supplied through an approved private file (0600).
// Do not put its contents in shell arguments, repository, logs or reports.
import fs from 'node:fs';
import {createTransport} from './transport.mjs';
import {runIntegration} from './runner.mjs';
import {identities} from '../http97/runner.mjs';
const filename=process.env.TALABOT_HTTP99_CONFIG;
if(!filename){console.log(JSON.stringify({status:'BLOCKED',reason:'approved private configuration and user sessions unavailable'}));process.exit(2)}
let config;try{const st=fs.lstatSync(filename);if(!st.isFile()||st.isSymbolicLink()||(st.mode&0o077)||st.size>32768)throw Error();config=JSON.parse(fs.readFileSync(filename,'utf8'))}catch{console.log(JSON.stringify({status:'BLOCKED',reason:'private configuration invalid'}));process.exit(2)}
if(config.origin!=='https://fsvrsvqfknogwmhccera.supabase.co'||config.approval!=='isolated-synthetic-fixtures-only'||config.auditAllowlist!=='verified-empty'||!config.fixture?.receiptOrderId||!config.sessions){console.log(JSON.stringify({status:'BLOCKED',reason:'isolated fixture approval missing'}));process.exit(2)}
const results=[];
// All identities verified before any PATCH. No admin key or account creation.
try{
 const transports={};
 for(const role of Object.keys(identities)){
  const t=createTransport({origin:config.origin,apiKey:config.apiKey,token:config.sessions[role]?.token,uid:identities[role],role,receiptOrderId:config.fixture.receiptOrderId});
  await t.identity();
  if(config.sessions[role]?.expiredToken){const expired=createTransport({origin:config.origin,apiKey:config.apiKey,token:config.sessions[role].expiredToken,uid:identities[role],role,receiptOrderId:config.fixture.receiptOrderId});t.expiredRequest=expired.request;}
  transports[role]=t;
 }
 for(const role of Object.keys(identities)){
  const result=await runIntegration(transports[role],role,config.fixture);
  results.push({role,...result,expiry:transports[role].expiredRequest?'measured':'BLOCKED: no existing expired token'});
  if(result.results.some(r=>r.id==='cleanup-name'&&r.status!=='PASS'))break;
 }
}catch{results.push({status:'ERROR',error:'bounded_integration_failure'})}
const failed=results.length!==3||results.some(r=>r.status==='ERROR'||r.results?.some(x=>x.status!=='PASS'));
console.log(JSON.stringify({scope:'hosted user HTTP; no production acceptance',status:failed?'FAIL':'PASS_EXECUTED_CASES',results},null,2));
process.exitCode=failed?1:0;
