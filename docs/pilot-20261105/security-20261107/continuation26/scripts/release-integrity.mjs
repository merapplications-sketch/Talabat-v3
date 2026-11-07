import {readFileSync,readdirSync,lstatSync} from 'node:fs';
import {createHash} from 'node:crypto';
import path from 'node:path';
export const digest=b=>createHash('sha256').update(b).digest('hex');
export function inputs(root) {
 const found={};
 function visit(rel){if(rel==='.git'||rel==='dist'||rel==='node_modules'||rel==='.security/last-build.json')return;const p=path.join(root,rel),s=lstatSync(p);if(s.isSymbolicLink())throw Error(`Symlink forbidden: ${rel}`);if(s.isDirectory()){for(const n of readdirSync(p).sort())visit(`${rel}/${n}`);}else found[rel]=digest(readFileSync(p));}
 for(const p of readdirSync(root).sort())visit(p);
 return found;
}
export function outputs(root){return Object.fromEntries(['server/index.js','.openai/hosting.json'].map(p=>[p,digest(readFileSync(path.join(root,'dist',p)))]));}
export function equal(a,b){return JSON.stringify(a)===JSON.stringify(b);}
export function verify(root,expected){
 const receipt=JSON.parse(readFileSync(path.join(root,'.security/last-build.json'),'utf8'));
 if(receipt.format!==2||!equal(receipt.source,inputs(root)))throw Error('Release blocked: source or tests changed since successful build');
 if(!equal(receipt.output,outputs(root)))throw Error('Release blocked: missing or altered build output');
 if(!equal(receipt.checks.map(x=>x.id),expected)||receipt.checks.some(x=>x.status!=='passed'))throw Error('Release blocked: incomplete test receipt');
 return receipt;
}
