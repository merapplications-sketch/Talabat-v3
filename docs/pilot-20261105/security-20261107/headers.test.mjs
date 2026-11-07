import test from 'node:test';
import assert from 'node:assert/strict';
import {readFile,readdir} from 'node:fs/promises';
import path from 'node:path';
import worker from '../dist/server/index.js';
const root=path.resolve(import.meta.dirname,'../public');
const request=(p,method='GET')=>worker.fetch(new Request(`https://test.example${p}`,{method}));
function secure(r) {
 assert.equal(r.headers.get('x-frame-options'),'DENY');
 assert.equal(r.headers.get('strict-transport-security'),'max-age=86400');
 assert.equal(r.headers.get('x-content-type-options'),'nosniff');
 assert.match(r.headers.get('content-security-policy'),/frame-ancestors 'none'/);
}
async function files(dir,prefix='') {const out=[];for(const e of await readdir(dir,{withFileTypes:true})) {const p=prefix+'/'+e.name;if(e.isDirectory())out.push(...await files(path.join(dir,e.name),p));else out.push(p);}return out;}
for(const p of await files(root)) {
 test(`exact bytes and security headers: ${p}`,async()=>{
  const route=p==='/index.html'?'/':p.replace(/\.html$/,'');
  const bytes=await readFile(path.join(root,p));
  const r=await request(route+'?v=unchanged');
  assert.equal(r.status,200);secure(r);assert.deepEqual(Buffer.from(await r.arrayBuffer()),bytes);
  if(p.endsWith('.html')) {
   const meta=bytes.toString().match(/http-equiv="Content-Security-Policy"\s+content="([^"]+)"/i)?.[1];
   if(meta) assert.equal(r.headers.get('content-security-policy'),meta+"; frame-ancestors 'none'");
  }
  const head=await request(route,'HEAD');assert.equal(head.status,200);secure(head);assert.equal(await head.text(),'');
 });
}
test('canonical HTML URLs keep query and safe relative redirect',async()=>{
 for(const p of ['/customer.html','/customer/','/merchant.html','/driver.html','/admin.html','/review.html','/safari-check.html','/index.html']) {
  const r=await request(p+'?v=1');assert.equal(r.status,307);secure(r);
  const expected=p==='/index.html'?'/':p.replace(/\.html$|\/$/,'');
  assert.equal(r.headers.get('location'),expected+'?v=1');
 }
});
test('error responses remain protected',async()=>{
 for(const [p,method,status] of [['//evil.test/index.html','GET',404],['/%2F%2Fevil.test/index.html','GET',404],['/missing','GET',404],['/%FF','GET',400],['/customer','POST',405],['/__proto__','GET',404],['/constructor','GET',404],['/missing','HEAD',404]]) {
  const r=await request(p,method);assert.equal(r.status,status);secure(r);
  if(method==='HEAD')assert.equal(await r.text(),'');
 }
});
