const fs=require('node:fs'),path=require('node:path'),os=require('node:os'),cp=require('node:child_process'),assert=require('node:assert/strict');
const root=path.resolve(__dirname,'..'),tmp=fs.mkdtempSync(path.join(os.tmpdir(),'talabot-gate-'));
try {
 for(const p of ['public','scripts','tests','worker','.openai','security'])fs.cpSync(path.join(root,p),path.join(tmp,p),{recursive:true});
 const p=path.join(tmp,'public/customer.html'),s=fs.readFileSync(p,'utf8');
 assert(s.includes('esc(JSON.stringify(s.n))'),'guarded customer sink must be present');
 fs.writeFileSync(p,s.replace('esc(JSON.stringify(s.n))',`JSON.stringify(s.n).replace(/"/g,'&quot;')`));
 fs.mkdirSync(path.join(tmp,'dist/server'),{recursive:true});fs.writeFileSync(path.join(tmp,'dist/server/index.js'),'STALE_BUNDLE');
 const r=cp.spawnSync(process.execPath,['scripts/build.mjs'],{cwd:tmp,encoding:'utf8',timeout:60000});
 assert.notEqual(r.status,0,'regressed source must block build');
 assert((r.stderr||'').includes('Security regression gate failed: customer-handler'),'must fail the actual regression case');
 assert.equal(fs.existsSync(path.join(tmp,'dist')),false,'failed build must remove stale publishable output');
 console.log(JSON.stringify({mutated_fixture_only:true,regressed_handler_rejected:true,stale_bundle_removed:true,source_unchanged:fs.readFileSync(path.join(root,'public/customer.html'),'utf8')===s}));
} finally {fs.rmSync(tmp,{recursive:true,force:true});}
