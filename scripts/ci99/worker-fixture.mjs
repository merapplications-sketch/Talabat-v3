// Test-only assembly. Never calls build.mjs, never emits a release attestation.
// Original headers/CSP tests use dist/server/index.js inside the isolated export.
import {readFile,writeFile,mkdir,readdir} from 'node:fs/promises';
import path from 'node:path';
import {assetPolicy,FALLBACK_CSP} from '../csp-policy.mjs';
const types={'.html':'text/html; charset=utf-8','.js':'text/javascript; charset=utf-8','.css':'text/css; charset=utf-8'};
const assets=Object.create(null);
async function walk(dir,prefix=''){for(const e of await readdir(dir,{withFileTypes:true})){if(e.isSymbolicLink())throw Error('symlink');const rel=prefix+'/'+e.name;if(e.isDirectory())await walk(path.join(dir,e.name),rel);else{const bytes=await readFile(path.join(dir,e.name)),ext=path.extname(e.name);if(!types[ext])throw Error('unsupported fixture asset');assets[rel]={body:bytes.toString('base64'),type:types[ext],csp:assetPolicy(bytes,ext)}}}}
await walk('public');await mkdir('dist/server',{recursive:true});
await writeFile('dist/server/index.js',`// CI99 TEST FIXTURE ONLY — NOT RELEASE OUTPUT\nconst ASSETS=${JSON.stringify(assets)};\nconst FALLBACK_CSP=${JSON.stringify(FALLBACK_CSP)};\n${await readFile('worker/measure79.js','utf8')}\n${await readFile('worker/index.js','utf8')}`);
