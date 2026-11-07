const fs=require('node:fs'),vm=require('node:vm'),assert=require('node:assert/strict');
const src=fs.readFileSync(require('node:path').join(__dirname,'../dist/talabat-core.js'),'utf8');
const a=src.indexOf('  async function readMerchantReport('),b=src.indexOf('  /* merchant report end */',a);
assert.ok(a>=0,'merchant report must read beyond the live order window');
const rows=Array.from({length:501},(_,i)=>({id:i+1,status:'delivered',subtotal:25,discount:0,commission:2,points_value:1,cashback:0.5,fee_waived:0}));
let fail=false;
const sb={from(table){assert.equal(table,'orders');let cursor=0;return {select(){return this},eq(k,v){assert.equal(k,'store_id');assert.equal(v,'owned');return this},in(k,v){assert.equal(k,'status');return this},gte(k,v){assert.equal(k,'done_at');return this},lte(k,v){assert.equal(k,'done_at');return this},order(k){assert.equal(k,'id');return this},gt(k,v){cursor=v;return this},limit(n){return Promise.resolve(fail?{error:{message:'offline'}}:{data:rows.filter(r=>r.id>cursor).slice(0,n)})}}}};
const ctx=vm.createContext({sb,Date,Math,Number,Error});vm.runInContext(src.slice(a,b),ctx);
(async()=>{const r=await ctx.readMerchantReport('owned',30);assert.equal(r.delivered,501);assert.equal(r.revenue,12525);assert.equal(r.net,10771.5);fail=true;await assert.rejects(()=>ctx.readMerchantReport('owned',30));console.log('merchant report: pagination, stored deductions, failure passed')})().catch(e=>{console.error(e);process.exitCode=1});
