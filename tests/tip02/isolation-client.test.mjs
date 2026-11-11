import fs from 'node:fs';
let source=fs.readFileSync('tests/native106/client.test.mjs','utf8');
const original="fs.readFileSync('tests/native104/client.js','utf8')";
if(!source.includes(original))throw Error('fixture drift');
source=source.replace(original,"fs.readFileSync(process.env.CANDIDATE_CORE,'utf8').split('})(globalThis);')[0]+'})(globalThis);'").replaceAll('native106-client.json','tip02-isolation-client.json');
await import('data:text/javascript;base64,'+Buffer.from(source).toString('base64'));
