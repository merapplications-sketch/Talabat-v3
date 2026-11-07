import { readFile, writeFile, mkdir, readdir, rm } from 'node:fs/promises';
import path from 'node:path';
import {inputs, outputs, equal} from './release-integrity.mjs';
import {runChecks} from './security-gate.mjs';
import { assetPolicy, FALLBACK_CSP } from './csp-policy.mjs';
const root = path.resolve(import.meta.dirname, '..');
// Remove stale publishable output before testing; failure must not leave an old bundle.
await rm(path.join(root,'dist'),{recursive:true,force:true});
await rm(path.join(root,'.security/last-build.json'),{force:true});
const initialInputs=inputs(root);
const regressionResults=runChecks(root);
const assets = Object.create(null);
const types = {'':'text/plain; charset=utf-8','.txt':'text/plain; charset=utf-8','.html':'text/html; charset=utf-8','.js':'text/javascript; charset=utf-8','.css':'text/css; charset=utf-8','.json':'application/json; charset=utf-8','.webp':'image/webp','.jpg':'image/jpeg','.jpeg':'image/jpeg','.png':'image/png','.svg':'image/svg+xml','.ico':'image/x-icon','.woff2':'font/woff2','.mp3':'audio/mpeg','.wav':'audio/wav'};
async function walk(dir, prefix='') {
 for (const e of (await readdir(dir, {withFileTypes:true})).sort((a,b)=>a.name.localeCompare(b.name))) {
  const relative = `${prefix}/${e.name}`;
  if(e.isSymbolicLink()) throw Error('Symlinks are not supported');
  if(e.isDirectory()) { await walk(path.join(dir,e.name), relative); continue; }
  const bytes = await readFile(path.join(dir,e.name));
  const ext=path.extname(e.name);
  if(!types[ext]) throw Error(`Unknown content type: ${relative}`);
  assets[relative] = { body:bytes.toString('base64'), type:types[ext], csp:assetPolicy(bytes,ext) };
 }
}
await walk(path.join(root,'public'));
const manifest=JSON.parse(await readFile(path.join(root,'.openai/hosting.json'),'utf8'));
if(manifest.static) throw Error('Worker manifest cannot contain static');
await mkdir(path.join(root,'dist/server'),{recursive:true});
await mkdir(path.join(root,'dist/.openai'),{recursive:true});
await writeFile(path.join(root,'dist/server/index.js'), `const ASSETS = ${JSON.stringify(assets)};\nconst FALLBACK_CSP = ${JSON.stringify(FALLBACK_CSP)};\n${await readFile(path.join(root,'worker/index.js'),'utf8')}`);
await writeFile(path.join(root,'dist/.openai/hosting.json'),JSON.stringify(manifest,null,2)+'\n');
try {
 const workerResults=runChecks(root,[['headers','node',['--test','tests/headers.test.mjs']],['csp-report','node',['--test','tests/csp-report.test.mjs']]]);
 if(!equal(initialInputs,inputs(root)))throw Error('Build inputs changed during tests');
 await mkdir(path.join(root,'.security'),{recursive:true});
 await writeFile(path.join(root,'.security/last-build.json'),JSON.stringify({format:2,source:initialInputs,output:outputs(root),checks:[...regressionResults,...workerResults],scope:'Local regression only; live/provider checks are separate'},null,2)+'\n');
} catch(error) { await rm(path.join(root,'dist'),{recursive:true,force:true}); throw error; }
console.log(`Embedded ${Object.keys(assets).length} assets`);
