const fs=require('node:fs'),vm=require('node:vm'),assert=require('node:assert/strict');
const src=fs.readFileSync(process.argv[2],'utf8');
const start=src.includes('const CD={},CS={},CE={};')?src.indexOf('const CD={},CS={},CE={};'):src.indexOf('function sendChat(id)');
const code=src.slice(start,src.indexOf('function sendLoc(id)',start));
let resolve, calls=0;const input={value:'offline draft'};
const ctx=vm.createContext({$:()=>input,render(){if(code.includes('const CD='))input.value=vm.runInContext('CD[4]||""',ctx)},TLB:{chat(){calls++;return new Promise(r=>resolve=r)}}});
vm.runInContext(code,ctx);
(async()=>{const p=ctx.sendChat(4);assert.equal(input.value,'offline draft','draft must remain while awaiting server');await ctx.sendChat(4);assert.equal(calls,1,'second tap must not insert twice');resolve({error:'offline'});await p;assert.equal(input.value,'offline draft','failed send must retain draft');const q=ctx.sendChat(4);resolve({ok:true});await q;assert.equal(input.value,'','confirmed send clears matching draft');console.log('PASS driver draft retention, duplicate tap, manual retry success')})().catch(e=>{console.error(e.message);process.exitCode=1});
