// Run after preparing the isolated static bundle, before packaging/publishing.
// Fails closed unless both the manifest and core point to the approved test DB.
const fs=require('node:fs'),path=require('node:path'),assert=require('node:assert/strict');
const dir=process.argv[2];assert.ok(dir,'Usage: node tools/align-pilot-csp.cjs DIST');
const target='fsvrsvqfknogwmhccera';
const manifest=JSON.parse(fs.readFileSync(path.join(dir,'manifest.json'),'utf8'));
assert.equal(manifest.target,target,'Refusing a non-test bundle');
const core=fs.readFileSync(path.join(dir,'talabat-core.js'),'utf8');
const origin=core.match(/var SB_URL = '([^']+)'/)[1];
assert.equal(origin,'https://'+target+'.supabase.co','Refusing a non-test backend');
const updates=['customer','merchant','driver','admin'].map(app=>{
 const file=path.join(dir,app+'.html'),html=fs.readFileSync(file,'utf8');
 assert.equal((html.match(/http-equiv="Content-Security-Policy"/g)||[]).length,1,app+' needs exactly one policy');
 const updated=html.replace(/(http-equiv="Content-Security-Policy" content=")([^"]+)(")/,(_,a,c,b)=>{
  assert.equal((c.match(/connect-src /g)||[]).length,1,app+' needs one connect-src');
  return a+c.replace(/connect-src [^;]+/,"connect-src 'self' "+origin+' '+origin.replace('https:','wss:'))+b;
 });
 return {file,updated};
});
for(const {file,updated} of updates)fs.writeFileSync(file,updated);
console.log('Aligned four app policies to approved test HTTP and realtime origins; all other directives preserved.');
