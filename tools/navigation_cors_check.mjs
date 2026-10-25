// Real-browser CORS check of the route function's handler — LOCAL only (no project): Chromium + the app's own supabase-js
// 2.117.2 UMD; page origin http://127.0.0.1:8001 calls the handler served on :8002 exactly as sb.functions.invoke does.
//   node tools/navigation_cors_check.mjs <supabase.js UMD path> <dir with node_modules/playwright or '' for global>
import http from 'node:http'; import fs from 'node:fs'; import { createRequire } from 'node:module';
import { makeHandler } from '../supabase/functions/route/handler.js';
const { chromium } = createRequire(import.meta.url)('playwright');
const UMD = fs.readFileSync(process.argv[2]); const PAGE = 'http://127.0.0.1:8001';
let fails = 0; const ok = (c, m) => { console.log((c ? 'PASS ' : 'FAIL ') + m); if (!c) fails++; };
let env = {}, log = [], warns = []; const warn0 = console.warn; console.warn = m => warns.push(String(m));
const h = req => makeHandler({ fetch: async () => { throw Error('no upstream allowed'); }, env, getUser: async a => a.startsWith('Bearer ') ? 'driver' : null,
  reserveBudget: async () => { throw Error('no ledger'); }, settleBudget: async () => { throw Error('no ledger'); } })(req);
const fn = http.createServer(async (req, res) => {
  const body = await new Promise(r => { let d = ''; req.on('data', c => d += c); req.on('end', () => r(d)); });
  const r = await h(new Request('http://fn' + req.url, { method: req.method, headers: req.headers, body: req.method === 'POST' ? body : undefined }));
  const hd = {}; r.headers.forEach((v, k) => hd[k] = v);
  log.push({ m: req.method, s: r.status, acrh: req.headers['access-control-request-headers'] || '', allowH: hd['access-control-allow-headers'] });
  res.writeHead(r.status, hd); res.end(await r.text());
}).listen(8002);
const page = http.createServer((req, res) => {
  if (req.url === '/sb.js') { res.writeHead(200, { 'content-type': 'application/javascript' }); return res.end(UMD); }
  res.writeHead(200, { 'content-type': 'text/html' });
  res.end('<script src="/sb.js"></script><script>const sb=supabase.createClient("http://127.0.0.1:8002","sb_publishable_test",{global:{headers:{Authorization:"Bearer signed-in-user"}}});' +
    'window.go=b=>sb.functions.invoke("route",{body:b}).then(r=>({data:r.data,error:r.error&&r.error.name}));</script>');
}).listen(8001);
const b = await chromium.launch(); let pg;
const run = async (allowedOrigins) => { env = { NAVIGATION_CONFIG: '{"internal":false,"external":true}', GEOAPIFY_KEY: '', ALLOWED_ORIGINS: allowedOrigins }; log = [];
  if (pg) await pg.context().close(); pg = await (await b.newContext()).newPage(); await pg.goto(PAGE);   // fresh context: no cached preflight
  const c = await pg.evaluate("go({op:'config'})"); const l = await pg.evaluate("go({op:'links',to:[38.56,68.78]})"); return { c, l, log: [...log] }; };
let r = await run('https://merapplications-sketch.github.io,' + PAGE);
const asked = r.log.find(x => x.m === 'OPTIONS').acrh.split(',').map(s => s.trim()), allowedH = r.log.find(x => x.m === 'OPTIONS').allowH.split(',').map(s => s.trim());
ok(asked.every(x => allowedH.includes(x)), 'headers the app actually requests (' + asked + ') are all allowed (' + allowedH + ')');
ok(r.log.filter(x => x.m === 'POST').length === 2 && r.c.data?.mode === 'tracking' && r.c.data?.reason === 'disabled' && r.c.data?.external === true,
  'allowed origin: preflight then POST reaches the function; config internal off, external on');
ok(r.l.data?.links?.map(x => x.id).join() === 'yandex,2gis,google', 'links: yandex,2gis,google');
r = await run('https://merapplications-sketch.github.io');
ok(r.log.every(x => x.m === 'OPTIONS') && r.log.every(x => x.s === 403) && r.c.error === 'FunctionsFetchError',
  'origin missing from ALLOWED_ORIGINS (the live symptom: no POST) -> preflight now answers 403, visible in the log (' + r.log.map(x => x.m + ' ' + x.s) + ')');
const w = warns.at(-1) || '', wj = JSON.parse(w || '{}');
ok(wj.route_cors === 'refused' && wj.origin === JSON.stringify(PAGE) && wj.allowed.join() === 'https://merapplications-sketch.github.io' && !/Bearer|signed-in|apikey|sb_publishable|38\.56/.test(w),
  'refusal log line: received origin + parsed allow-list only, no key / session / coordinates: ' + w);
for (const v of [' ' + PAGE + '/ ', '"' + PAGE + '"', PAGE + '/driver.html']) {
  r = await run('https://merapplications-sketch.github.io,' + v);
  ok(r.l.data?.links?.length === 3, 'secret entry ' + JSON.stringify(v) + ' is reduced to the origin and accepted');
}
await b.close(); fn.close(); page.close();
console.log(`\nNAVIGATION CORS CHECK ${fails ? 'FAILS ' + fails : 'OK'}`); process.exit(fails ? 1 : 0);
