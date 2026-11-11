// Independent local source-extraction test. No network, browser, auth or hosted API.
import fs from 'node:fs';
import vm from 'node:vm';
import assert from 'node:assert/strict';
import crypto from 'node:crypto';
const dir = new URL('.', import.meta.url);
const read = p => fs.readFileSync(new URL(p,dir),'utf8');
const merchant = read('source/merchant.html'), core = read('source/talabat-core.js');
const hashes = {};
for (const [path, expected] of Object.entries({
  'source/merchant.html':'5f09dd5cc3d5abc9d6b0d3afa031342b05f5212c',
  'source/talabat-core.js':'f639bec1d23a812866e06eb1110940c77563387c'
})) {
  const b=fs.readFileSync(new URL(path,dir));
  const sha=crypto.createHash('sha1').update(`blob ${b.length}\0`).update(b).digest('hex');
  assert.equal(sha,expected); hashes[path]=sha;
}
// Extract exact functions by known declaration boundaries; no production logic copied/reimplemented.
const valid = core.slice(core.indexOf('  function validItem('),core.indexOf('  function cleanPct('));
const single = name => core.split('\n').find(s=>s.includes(`function ${name}(`));
const method = name => core.split('\n').find(s=>s.trimStart().startsWith(`${name}: function`)).trim().replace(/,$/,'');
const save = merchant.slice(merchant.indexOf('async function saveSheet()'),merchant.indexOf('async function addG()'));
const calls=[], checks=[];
const ctx=vm.createContext({
  STORE:'Synthetic Restaurant', MX:()=>100, t:x=>x, alert:()=>{}, render:()=>{},
  storeByName:()=>({id:'10000000-0000-4000-8000-000000000001'}),
  badStore:()=>({error:'bad_value'}), done:r=>r,
  sb:{from:table=>({
    insert:body=>{calls.push({table,op:'insert',json:JSON.stringify(body)});return Promise.resolve({ok:true});},
    update:body=>({eq:(field,id)=>{calls.push({table,op:'update',id,json:JSON.stringify(body)});return Promise.resolve({ok:true});}})
  })}
});
vm.runInContext([valid,single('cleanPct'),single('cleanSection'),`var TLB={${['addItem','updateItem','addOption','updateOption'].map(method).join(',')}};`,save].join('\n'),ctx);
async function sheet(price,id=null){ctx.SH={name:'Synthetic precision item',price,disc:'0',pop:false,section:'',image:null,changed:false,id};await vm.runInContext('saveSheet()',ctx);}
function check(id,fn){fn();checks.push({id,status:'PASS'});}
await sheet('12.00000001');
check('JS01-add-price-survives-Number-and-JSON',()=>assert.equal(JSON.parse(calls.at(-1).json).price,12.00000001));
const insert=calls.at(-1);
await sheet('12.00000001','20000000-0000-4000-8000-000000000001');
check('JS02-update-price-survives-Number-and-JSON',()=>assert.equal(JSON.parse(calls.at(-1).json).price,12.00000001));
const update=calls.at(-1);
check('JS03-handler-does-not-enforce-step',()=>{assert.match(merchant,/type="number"[^\n]*step="0\.5"/);assert.doesNotMatch(save,/checkValidity|reportValidity|stepMismatch/);assert.match(merchant,/onclick="saveSheet\(\)"/);});
for(const p of ['-1','0','Infinity','100000.00000001']){
  const n=calls.length;await sheet(p);check(`JS04-rejected-price-${p}`,()=>assert.equal(calls.length,n));
}
await vm.runInContext(`TLB.addOption('group',{name:'Synthetic option',price:0.00000001})`,ctx);
check('JS05-option-add-rounds-independently',()=>assert.equal(JSON.parse(calls.at(-1).json).price_delta,0));
await vm.runInContext(`TLB.updateOption('option',{price:0.00000001})`,ctx);
check('JS06-option-update-rounds-independently',()=>assert.equal(JSON.parse(calls.at(-1).json).price_delta,0));
const result={kind:'LOCAL NODE VM / mocked transport; no DOM, IndexedDB or HTTP',runtime:process.version,created_at:new Date().toISOString(),source_git_blobs:hashes,checks,insert,update};
fs.writeFileSync(new URL('input-results.json',dir),JSON.stringify(result,null,2)+'\n');
console.log(JSON.stringify(result));
