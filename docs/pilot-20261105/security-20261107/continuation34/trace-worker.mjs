import assert from 'node:assert/strict';
import {pathToFileURL} from 'node:url';
const {default:worker}=await import(pathToFileURL(process.argv[2]));
// Request() prohibits TRACE in Fetch clients; use an incoming-request-shaped
// object to exercise the actual server dispatch, not to bypass a network rule.
const paths=['/','/customer','/merchant','/driver','/admin','/csp-report','/missing'];
for(const path of paths){
 const r=await worker.fetch({url:'https://fixture.invalid'+path,method:'TRACE'});
 assert.equal(r.status,405,path);assert.equal(await r.text(),'');
}
for(const method of ['GET','HEAD']){
 const r=await worker.fetch(new Request('https://fixture.invalid/customer',{method}));
 assert.equal(r.status,200);const body=await r.text();
 assert.equal(body.length>0,method==='GET');
}
console.log(JSON.stringify({result:'PASS',trace_paths:paths,allowed_methods:['GET','HEAD'],scope:'actual built worker; deployed probes recorded separately'}));
