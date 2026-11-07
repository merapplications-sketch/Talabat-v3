import test from 'node:test';import assert from 'node:assert/strict';import fs from 'node:fs';import os from 'node:os';import path from 'node:path';
import {inputs,outputs,verify} from '../scripts/release-integrity.mjs';
function fixture(){const root=fs.mkdtempSync(path.join(os.tmpdir(),'talabot-integrity-'));for(const p of ['public','scripts','tests','worker','security','.openai','dist/server','dist/.openai','.security'])fs.mkdirSync(path.join(root,p),{recursive:true});for(const p of ['public/app.js','scripts/build.mjs','tests/auth.cjs','worker/index.js','security/test.sql','.openai/hosting.json','dist/server/index.js','dist/.openai/hosting.json'])fs.writeFileSync(path.join(root,p),'synthetic');const r={format:2,source:inputs(root),output:outputs(root),checks:[{id:'required',status:'passed'}]};fs.writeFileSync(path.join(root,'.security/last-build.json'),JSON.stringify(r));return{root,r,close(){fs.rmSync(root,{recursive:true,force:true})}};}
for(const [name,change]of [
 ['allowed exact build',()=>{}],
 ['changed source',x=>fs.appendFileSync(path.join(x.root,'public/app.js'),'changed')],
 ['changed test',x=>fs.appendFileSync(path.join(x.root,'tests/auth.cjs'),'weakened')],
 ['changed DB evidence',x=>fs.appendFileSync(path.join(x.root,'security/test.sql'),'changed')],
 ['added root module',x=>fs.writeFileSync(path.join(x.root,'new-module.js'),'new')],
 ['added asset',x=>fs.writeFileSync(path.join(x.root,'public/new.js'),'new')],
 ['stale bundle',x=>fs.writeFileSync(path.join(x.root,'dist/server/index.js'),'old')],
 ['missing bundle',x=>fs.unlinkSync(path.join(x.root,'dist/server/index.js'))],
 ['failed receipt',x=>{x.r.checks[0].status='failed';fs.writeFileSync(path.join(x.root,'.security/last-build.json'),JSON.stringify(x.r))}],
 ['missing test receipt',x=>{x.r.checks=[];fs.writeFileSync(path.join(x.root,'.security/last-build.json'),JSON.stringify(x.r))}]
])test(name,()=>{const x=fixture();try{change(x);if(name.startsWith('allowed'))assert.doesNotThrow(()=>verify(x.root,['required']));else assert.throws(()=>verify(x.root,['required']));}finally{x.close()}});
