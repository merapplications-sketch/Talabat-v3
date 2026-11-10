import {test} from 'node:test';import assert from 'node:assert/strict';import fs from 'node:fs';import os from 'node:os';import path from 'node:path';import {spawnSync} from 'node:child_process';
test('original build rejects missing private evidence and removes stale publishable output',()=>{
 const dir=fs.mkdtempSync(path.join(os.tmpdir(),'talabot-build100-'));
 try{for(const p of ['public','scripts','tests','worker','security','.openai'])fs.cpSync(p,path.join(dir,p),{recursive:true,filter:p=>!p.includes('node_modules')});
 fs.rmSync(path.join(dir,'security/db/tested-evidence.json'),{force:true});
 fs.mkdirSync(path.join(dir,'dist/server'),{recursive:true});fs.writeFileSync(path.join(dir,'dist/server/index.js'),'STALE');
 const r=spawnSync(process.execPath,['scripts/build.mjs'],{cwd:dir,encoding:'utf8',timeout:30000});
 assert.notEqual(r.status,0);assert.match(r.stderr,/Security regression gate failed: db-evidence-binding/);
 assert.equal(fs.existsSync(path.join(dir,'dist')),false);assert.equal(fs.existsSync(path.join(dir,'.security/last-build.json')),false);
 }finally{fs.rmSync(dir,{recursive:true,force:true})}
});
