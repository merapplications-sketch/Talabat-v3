// Local check of supabase/functions/route/handler.js (no Deno, no network): fake fetch / env / auth.
//   node tools/route_function_check.mjs
import { makeHandler, LIMITS } from '../supabase/functions/route/handler.js';
let fails = 0, n = 0;
const ok = (c, m) => { n++; console.log((c ? 'PASS ' : 'FAIL ') + m); if (!c) fails++; };
const ORS = { features: [{ properties: { summary: { distance: 4210.4, duration: 611.2 } }, geometry: { coordinates: Array.from({ length: 900 }, (_, i) => [69.24 + i * 1e-5, 41.29 + i * 1e-5]) } }] };
let calls = [], mode = 'ok';
const fetch = async (url, init) => { calls.push({ url, init }); if (mode === 'quota') return new Response('', { status: 429 }); if (mode === 'down') throw new Error('net'); return new Response(JSON.stringify(ORS), { status: 200 }); };
const getUser = async (a) => (a === 'Bearer good' ? 'user-1' : null);
let clock = 1e12;
const H = (env = { ORS_KEY: 'secret-key', ALLOWED_ORIGINS: 'https://app.example' }) => makeHandler({ fetch, env, getUser, now: () => clock });
const req = (body, { auth = 'Bearer good', origin = 'https://app.example', method = 'POST' } = {}) =>
  new Request('https://fn/route', { method, headers: { authorization: auth, origin, 'content-type': 'application/json' }, body: method === 'POST' ? JSON.stringify(body) : undefined });
const A = [41.2995, 69.2401], B = [41.31, 69.28];
const h = H();
let r = await h(req({ from: A, to: B })), d = await r.json();
ok(r.status === 200 && d.distance_m === 4210 && d.duration_s === 611 && d.source === 'openrouteservice', 'route: distance / duration from the provider summary (%o)'.replace('%o', JSON.stringify({ s: r.status, m: d.distance_m, t: d.duration_s })));
ok(d.coords.length === LIMITS.maxPoints && d.coords[0][0] === 41.29 && d.coords[0][1] === 69.24, 'route: [lat,lng] order back to the app, thinned to ' + LIMITS.maxPoints + ' points');
const sent = JSON.parse(calls[0].init.body);
ok(sent.coordinates[0][0] === A[1] && sent.coordinates[0][1] === A[0], 'provider receives [lng,lat]');
ok(calls[0].init.headers.Authorization === 'secret-key' && !JSON.stringify(d).includes('secret-key'), 'key sent only to the provider, never returned to the app');
calls = []; r = await h(req({ from: A, to: B })); ok(r.status === 200 && calls.length === 0, 'same trip within 5 min: served from cache (no provider call)');
ok((await h(req({ from: A, to: B }, { auth: '' }))).status === 401, 'no sign-in: 401');
ok((await h(req({ from: A, to: B }, { origin: 'https://evil.example' }))).status === 403, 'foreign site: 403');
ok((await h(req({ from: [0, 0], to: B }))).status === 400 && (await h(req({ from: 'x', to: B }))).status === 400, 'bad points (0,0 / text): 400');
ok((await h(req({ from: A, to: [38.56, 68.78] }))).status === 422, 'Tashkent -> Dushanbe (>60 km straight): refused, quota kept');
ok((await H({ ORS_KEY: '' })(req({ from: A, to: B }))).status === 503, 'no key configured: 503 not_configured (app keeps the straight line)');
mode = 'quota'; clock += 10 * 60000; r = await h(req({ from: A, to: [41.32, 69.3] })); ok(r.status === 503 && (await r.json()).error === 'quota', 'provider quota reached: 503 quota');
mode = 'down'; r = await h(req({ from: A, to: [41.33, 69.31] })); ok(r.status === 502, 'provider unreachable: 502');
mode = 'ok'; clock += 60000; let last = 0;
for (let i = 0; i < LIMITS.perUserPerMinute + 2; i++) last = (await h(req({ from: A, to: [41.3 + i * 0.001, 69.3] }))).status;
ok(last === 429, 'more than ' + LIMITS.perUserPerMinute + ' trips / minute for one user: 429');
ok((await h(req(null, { method: 'OPTIONS' }))).status === 200, 'CORS preflight');
console.log(`\nROUTE FUNCTION CHECK ${fails ? 'FAILS ' + fails + ' of ' + n : 'OK (' + n + ')'}`); process.exit(fails ? 1 : 0);
