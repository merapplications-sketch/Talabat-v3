import fs from 'node:fs';import vm from 'node:vm';import assert from 'node:assert/strict';import {pathToFileURL}from'node:url';
const root=process.argv[2];if(!root)throw Error('source root required');const worker=(await import(pathToFileURL(root+'/dist/server/index.js'))).default;let count=0;
for(const [route,status,location]of [
['/%63ustomer',200],['/%2563ustomer',404],['/customer%2ehtml?q=%2527',307,'/customer?q=%2527'],['/customer%252ehtml',404],['/customer%3Fignored',404],['/customer%23ignored',404],['/customer%2F',307,'/customer'],['/customer%252F',404],['/a/%2e%2e/customer',200],['/a/%252e%252e/customer',404],['/%C0%AFcustomer',400],['/%',400]]){const r=await worker.fetch(new Request('https://synthetic.invalid'+route));assert.equal(r.status,status,route);if(location)assert.equal(r.headers.get('location'),location);count++}
const html=fs.readFileSync(root+'/public/customer.html','utf8');const c=vm.createContext({});vm.runInContext(html.slice(html.indexOf("const SEP='~'"),html.indexOf('/* the restaurant comment travels')),c);
for(const note of ['%27','%2527','caret^quote\'','عربي русский e\u0301','  trim\n spaces ','&#39;']){c.input=note;assert.equal(vm.runInContext("pk(lk('dish',['z','a'],input)).note",c),note.replace(/\s+/g,' ').trim().slice(0,120));count++}
assert.equal(vm.runInContext("pk('dish^%FF').note",c),'');count++;
const ds=html.match(/const deepStore=([^\n]+);/)[1];const uuid='90000000-0000-0000-0000-000000002731';
for(const [q,value]of [['?store='+uuid,uuid],['?store='+uuid.replaceAll('-','%2D'),uuid],['?store='+uuid.replaceAll('-','%252D'),null],['?store=bad&store='+uuid,null],['?store='+uuid+'&store=bad',uuid],['?store=+'+uuid,null]]){assert.equal(vm.runInNewContext(ds,{URLSearchParams,location:{search:q}}),value);count++}
console.log(JSON.stringify({passed_cases:count,scope:'Actual local Worker routes and extracted cart/deepStore parsers; no network or database effects; no whole V1.1.1 acceptance.'}));
