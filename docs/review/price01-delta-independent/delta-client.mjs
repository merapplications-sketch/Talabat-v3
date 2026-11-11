import fs from 'node:fs';import vm from 'node:vm';import assert from 'node:assert/strict';import {randomUUID,webcrypto} from 'node:crypto';
// Reuse the pinned VM scaffolding only, not developer cases/assertions.
const scaffolding=fs.readFileSync('tests/price01-impl/client.test.mjs','utf8');
const prefix=scaffolding.slice(scaffolding.indexOf('const html='),scaffolding.indexOf('const results=[];'));
const {app,ctl,review}=Function('fs','vm','assert','randomUUID','webcrypto','process','setImmediate','setTimeout','clearTimeout',prefix+'\nreturn {app,ctl,review};')(fs,vm,assert,randomUUID,webcrypto,process,setImmediate,setTimeout,clearTimeout);
const I='40000000-0000-4000-8000-000000000092',OP='70000000-0000-4000-8000-000000000092';

const proofs=[],results=[];
function test(name,f){try{f();results.push({name,status:'PASS'})}catch(e){results.push({name,status:'FAIL',error:String(e)})}}
for(const v of [
 {name:'quantity',base:20.1,q:3,opt:null,rd:0,hh:0,gross:'60.3',r:'0',h:'0',net:'60.3',total:'62.3'},
 {name:'positive-option',base:19.9,q:3,opt:.2,rd:0,hh:0,gross:'60.3',r:'0',h:'0',net:'60.3',total:'62.3'},
 {name:'negative-option',base:20.3,q:3,opt:-.2,rd:0,hh:0,gross:'60.3',r:'0',h:'0',net:'60.3',total:'62.3'},
 {name:'discount-hh',base:20.1,q:3,opt:null,rd:5,hh:10,gross:'60.3',r:'3.02',h:'3.01',net:'54.27',total:'56.27'},
 {name:'boundary-quantity',base:.29,q:50,opt:null,rd:0,hh:0,gross:'14.5',r:'0',h:'0',net:'14.5',total:'16.5'}])test(v.name,()=>{
 const x=app();x.c.S.cart={[I]:v.q};x.c.ALLS[0].rd=v.rd;x.c.ALLS[0].hh=v.hh;x.c.menuOf=()=>[{id:I,price:v.base,discount:0}];
 if(v.opt!==null){x.c.pk=k=>({id:k,ops:[OP]});x.c.TLB.optionsOf=()=>[{options:[{id:OP,price:v.opt}]}]}
 x.c.priceRememberDisplayed01();const proof=x.c.pricePrepare01().value;
 for(const [k,e] of Object.entries({net_items:v.net,restaurant_discount:v.r,happy_hour_discount:v.h}))assert.equal(proof.lines[0][k],e);
 assert.equal(proof.totals.subtotal,v.gross);assert.equal(proof.totals.total,v.total);proofs.push({...v,proof});
});
test('codec exact finite exponents and no tolerance',()=>{const x=app();for(const [n,s] of [[1e-7,'0.0000001'],[20.0000001,'20.0000001'],[-.2,'-0.2'],[1e21,'1000000000000000000000']])assert.equal(x.c.priceText01(x.c.priceDecimal01(n)),s);for(const n of [NaN,Infinity,-Infinity,1e128,1e-130])assert.throws(()=>x.c.priceText01(x.c.priceDecimal01(n)));assert.notEqual(x.c.priceText01(x.c.priceDecimal01(20.0000001)),x.c.priceText01(x.c.priceDecimal01(20.0000002)));});
fs.writeFileSync('delta-proofs.json',JSON.stringify(proofs,null,2));fs.writeFileSync('delta-client-new.json',JSON.stringify({source:'50b796985112002f4c47aa4dd2bd1373ffd7aeff',scope:'NODE VM / MOCK RPC',results},null,2));console.log(results);process.exitCode=results.some(r=>r.status!=='PASS')?1:0;
