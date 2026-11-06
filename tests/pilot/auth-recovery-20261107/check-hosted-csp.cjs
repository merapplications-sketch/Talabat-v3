const fs=require('node:fs'),path=require('node:path'),assert=require('node:assert/strict');
const dir=process.argv[2];assert.ok(dir,'Usage: node check-hosted-csp.cjs DIST');
const core=fs.readFileSync(path.join(dir,'talabat-core.js'),'utf8');
const origin=core.match(/var SB_URL = '([^']+)'/)[1];
assert.equal(origin,'https://fsvrsvqfknogwmhccera.supabase.co','Must inspect approved test backend');
let failed=false;
for(const app of ['customer','merchant','driver','admin']){
 const html=fs.readFileSync(path.join(dir,app+'.html'),'utf8');
 const policy=html.match(/http-equiv="Content-Security-Policy" content="([^"]+)"/)[1];
 const allowed=policy.match(/(?:^|;)\s*connect-src\s+([^;]+)/)[1].trim().split(/\s+/);
 try{assert.deepEqual(allowed,["'self'",origin,origin.replace('https:','wss:')]);console.log('PASS '+app+' test-only HTTP + realtime policy');}
 catch(e){failed=true;console.error('FAIL '+app+': configured backend is blocked by connect-src: '+allowed.join(' '));}
}
if(failed)process.exitCode=1;
