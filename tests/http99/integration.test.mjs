// Real HTTP wire, synthetic server. Does NOT prove Supabase RLS or Auth.
import {test} from 'node:test';import assert from 'node:assert/strict';import {createServer} from 'node:http';
import {createTransport} from './transport.mjs';import {runIntegration} from './runner.mjs';import {identities} from '../http97/runner.mjs';
for(const role of Object.keys(identities))for(const loseAck of [false,true])test(role+' wire integration, lost PATCH ACK='+loseAck,async()=>{
 const uid=identities[role],row={id:uid,name:'Original',online:false,last_seen:null,lat:1,lng:2,loc_acc:3,loc_updated:null};let nameWrites=0;
 const server=createServer(async(q,r)=>{
  let raw='';for await(const c of q)raw+=c;
  const body=raw?JSON.parse(raw):{},url=new URL(q.url,'http://localhost');let data;
  if(q.headers.authorization==='Bearer expired'){r.writeHead(401);r.end('{}');return}
  if(url.pathname==='/auth/v1/user')data={id:uid};
  else if(url.pathname==='/rest/v1/profiles'){
   if(url.searchParams.get('id')!=='eq.'+uid){r.writeHead(403);r.end('{}');return}
   if(q.method==='PATCH'){
    if(Object.keys(body).some(k=>k!=='name')){r.writeHead(403);r.end(JSON.stringify({code:'42501'}));return}
    row.name=body.name;nameWrites++;
    if(loseAck&&body.name==='Synthetic98'){q.socket.destroy();return}
    r.writeHead(204);r.end();return
   }data=[row];
  }else if(url.pathname.endsWith('/finance_audit'))data=[];
  else if(url.pathname.endsWith('/finance_customers'))data=role==='finance'?[{id:identities.outsider}]:[];
  else if(url.pathname.endsWith('/finance_settlement_receipts'))data=role==='finance'?[{order_id:'980001',receipt:{amount:5}}]:[];
  else{r.writeHead(404);r.end('{}');return}
  r.setHeader('content-type','application/json');r.end(JSON.stringify(data));
 });await new Promise(r=>server.listen(0,'127.0.0.1',r));
 try{
  const opts={origin:`http://127.0.0.1:${server.address().port}`,loopback:true,token:'synthetic',apiKey:'synthetic',uid,role,timeoutMs:500};
  const t=createTransport(opts);t.expiredRequest=createTransport({...opts,token:'expired'}).request;
  const result=await runIntegration(t,role,{receiptOrderId:'980001',receiptAmount:5});
  assert.equal(row.name,'Original');assert.equal(nameWrites,2,'one attempted write and one cleanup, no mutation retry');
  assert.equal(result.results.find(x=>x.id==='cleanup-name').status,'PASS');
  if(loseAck)assert.ok(result.results.some(x=>x.status==='ERROR'));else assert.ok(result.results.every(x=>x.status==='PASS'),JSON.stringify(result));
 }finally{server.closeAllConnections();await new Promise(r=>server.close(r))}
});
