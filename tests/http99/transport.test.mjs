import {test} from 'node:test';
import assert from 'node:assert/strict';
import {createServer} from 'node:http';
const module=await import('./transport.mjs').catch(()=>({}));
test('transport is implemented',()=>assert.equal(typeof module.createTransport,'function'));
const uid='68091852-942b-4997-ace1-e28229327ae8';
if(module.createTransport){
 const {createTransport}=module;
 test('real loopback HTTP: GET retries connection loss, PATCH never retries',async()=>{
  let gets=0,patches=0;
  const server=createServer((q,r)=>{if(q.method==='PATCH'){patches++;q.socket.destroy();return}if(++gets===1){q.socket.destroy();return}r.setHeader('content-type','application/json');r.end(JSON.stringify([{id:uid}]))});
  await new Promise(r=>server.listen(0,'127.0.0.1',r));
  try{const t=createTransport({origin:`http://127.0.0.1:${server.address().port}`,loopback:true,token:'synthetic',apiKey:'synthetic',uid,role:'finance',timeoutMs:100});
   assert.equal((await t.request({method:'GET',path:'/rest/v1/profiles',query:{id:'eq.'+uid}})).status,200);assert.equal(gets,2);
   await assert.rejects(t.request({method:'PATCH',path:'/rest/v1/profiles',query:{id:'eq.'+uid},body:{name:'Synthetic'}}),/mutation_outcome_unknown/);assert.equal(patches,1);
  }finally{server.closeAllConnections();await new Promise(r=>server.close(r))}
 });
 test('timeout covers response body and sanitizes failures',async()=>{
  const server=createServer((q,r)=>{r.writeHead(200,{'content-type':'application/json'});r.write('[')});await new Promise(r=>server.listen(0,'127.0.0.1',r));
  try{const t=createTransport({origin:`http://127.0.0.1:${server.address().port}`,loopback:true,token:'SENSITIVE',apiKey:'SENSITIVE',uid,role:'finance',timeoutMs:50});const at=Date.now();await assert.rejects(t.request({method:'GET',path:'/auth/v1/user'}),/^Error: transport_unavailable$/);assert.ok(Date.now()-at<2000)}finally{server.closeAllConnections();await new Promise(r=>server.close(r))}
 });
 test('origin, identity, route and audit scope fail closed before network',async()=>{
  assert.throws(()=>createTransport({origin:'https://production.example',token:'x',apiKey:'x',uid,role:'finance'}),/origin/);
  const t=createTransport({origin:'https://fsvrsvqfknogwmhccera.supabase.co',token:'x',apiKey:'x',uid:'77fecb51-6632-462c-a05e-6aae2e9c11fe',role:'orders'});
  for(const c of [{method:'GET',path:'https://evil.example'},{method:'POST',path:'/rest/v1/rpc/finance_audit',body:{}},{method:'PATCH',path:'/rest/v1/profiles',query:{id:'eq.'+uid},body:{name:'x'}}])await assert.rejects(t.request(c),/scope/);
 });
 test('redirect is not followed with credentials',async()=>{
  let targetHits=0;const server=createServer((q,r)=>{if(q.url==='/auth/v1/user'){r.writeHead(302,{location:'/leak'});r.end()}else{targetHits++;r.end('[]')}});await new Promise(r=>server.listen(0,'127.0.0.1',r));
  try{const t=createTransport({origin:`http://127.0.0.1:${server.address().port}`,loopback:true,token:'synthetic',apiKey:'synthetic',uid,role:'finance'});await assert.rejects(t.request({method:'GET',path:'/auth/v1/user'}),/transport_unavailable/);assert.equal(targetHits,0)}finally{server.closeAllConnections();await new Promise(r=>server.close(r))}
 });
}
