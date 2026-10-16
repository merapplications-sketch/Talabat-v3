// Edge Function partner-lead, run in Node 22 with fake Turnstile / database answers (nothing leaves this machine).
//   node tools/partner_fn_check.mjs
import { makeHandler } from '../supabase/functions/partner-lead/handler.js';
import { createHmac } from 'node:crypto';
let fails = 0;
const ok = (c, m) => { console.log((c ? 'PASS ' : 'FAIL ') + m); if (!c) fails++; };
const ENV = { TURNSTILE_SECRET_KEY: 'test-ts-secret', LEAD_HASH_KEY: 'k'.repeat(40), SUPABASE_URL: 'https://example.supabase.co',
  SUPABASE_SERVICE_ROLE_KEY: 'sb_secret_test', PARTNER_ORIGINS: 'https://merapplications-sketch.github.io' };
const ORIGIN = 'https://merapplications-sketch.github.io';
function setup(env, ts, db) {
  const calls = [], logs = [];
  const fetch = async (url, o) => {
    calls.push({ url, o });
    if (url.includes('turnstile')) { if (ts === 'throw') throw new Error('net'); return new Response(JSON.stringify(ts), { status: 200 }); }
    if (db === 'throw') throw new Error('net');
    if (db === 500) return new Response('{}', { status: 500 });
    return new Response(JSON.stringify(db), { status: 200 });
  };
  return { h: makeHandler(env, { fetch, log: (x) => logs.push(JSON.stringify(x)) }), calls, logs };
}
const good = { success: true, action: 'partner_lead', hostname: 'merapplications-sketch.github.io' };
const body = (o) => JSON.stringify(Object.assign({ name: 'Чайхана Роҳат', category: 'rest', phone: '90 123 45 67', token: 'tok-123' }, o || {}));
const req = (b, o) => new Request('https://example.supabase.co/functions/v1/partner-lead', Object.assign({ method: 'POST', body: b,
  headers: { origin: ORIGIN, 'content-type': 'application/json', 'x-forwarded-for': '5.6.7.8, 10.0.0.1' } }, o || {}));
const res = async (r) => [r.status, (await r.json()).result];
const hm = (t) => createHmac('sha256', ENV.LEAD_HASH_KEY).update(t).digest('hex');

{ const s = setup(ENV, good, 'ok'); const [st, r] = await res(await s.h(req(body())));
  ok(st === 200 && r === 'ok', 'valid request: Turnstile passed, database said ok → 200 ok');
  const ts = s.calls[0], db = s.calls[1], p = JSON.parse(db.o.body);
  ok(ts.url.includes('challenges.cloudflare.com/turnstile/v0/siteverify') && ts.o.body.get('secret') === 'test-ts-secret' && ts.o.body.get('response') === 'tok-123' && ts.o.body.get('remoteip') === '5.6.7.8', 'Turnstile checked by the server with the secret, the token and the client address');
  ok(db.url === 'https://example.supabase.co/rest/v1/rpc/lead_submit' && db.o.headers.apikey === 'sb_secret_test' && !db.o.headers.Authorization, 'database called with the service key (new sb_secret_ key in apikey only)');
  ok(p.p_phone === '+992901234567' && p.p_phone_key === hm('phone:+992901234567') && p.p_client_key === hm('ip:5.6.7.8'), 'phone normalized; phone and address sent only as HMAC keys made with LEAD_HASH_KEY');
  ok(!s.logs.join(' ').match(/90123|Чайхана|tok-123|5\.6\.7\.8|test-ts-secret|kkkk|sb_secret/), 'log has only the result code: ' + s.logs.join(' ')); }
{ const s = setup(Object.assign({}, ENV, { SUPABASE_SERVICE_ROLE_KEY: 'eyJhbGciOi.test' }), good, 'ok'); await s.h(req(body()));
  ok(s.calls[1].o.headers.Authorization === 'Bearer eyJhbGciOi.test', 'legacy JWT service key also sent as Bearer'); }
for (const k of ['TURNSTILE_SECRET_KEY', 'LEAD_HASH_KEY', 'SUPABASE_URL', 'SUPABASE_SERVICE_ROLE_KEY', 'PARTNER_ORIGINS']) {
  const e = Object.assign({}, ENV); delete e[k]; if (k === 'PARTNER_ORIGINS') e.PARTNER_ORIGINS = ORIGIN + ',x'; // keep origin allowed to reach the check
  const s = setup(k === 'PARTNER_ORIGINS' ? Object.assign({}, ENV, { PARTNER_ORIGINS: '' }) : e, good, 'ok'); const [st, r] = await res(await s.h(req(body())));
  ok((k === 'PARTNER_ORIGINS' ? st === 403 : st === 503 && r === 'unavailable') && s.calls.length === 0, 'setting missing (' + k + ') → refused (' + st + ' ' + r + '), nothing called, no success');
}
{ const s = setup(Object.assign({}, ENV, { LEAD_HASH_KEY: 'short' }), good, 'ok'); const [st, r] = await res(await s.h(req(body())));
  ok(st === 503 && r === 'unavailable', 'hash key shorter than 32 chars → refused'); }
const cases = [
  ['no token', body({ token: '' }), good, 403, 'verify_failed', 0],
  ['Turnstile says no', body(), { success: false, 'error-codes': ['invalid-input-response'] }, 403, 'verify_failed', 1],
  ['token reused (Cloudflare: timeout-or-duplicate)', body(), { success: false, 'error-codes': ['timeout-or-duplicate'] }, 403, 'verify_failed', 1],
  ['token made for another action', body(), Object.assign({}, good, { action: 'login' }), 403, 'verify_failed', 1],
  ['token made on another site', body(), Object.assign({}, good, { hostname: 'evil.example' }), 403, 'verify_failed', 1],
  ['Turnstile unreachable', body(), 'throw', 503, 'unavailable', 1],
  ['hidden field filled (bot)', body({ website: 'http://x' }), good, 403, 'verify_failed', 0],
  ['bad phone', body({ phone: '12345' }), good, 400, 'bad_phone', 0],
  ['bad category', body({ category: 'cars' }), good, 400, 'bad_value', 0],
  ['name too short', body({ name: 'K' }), good, 400, 'bad_value', 0],
  ['not JSON', 'name=x', good, 400, 'bad_value', 0],
  ['body too large', body({ name: 'x'.repeat(5000) }), good, 400, 'bad_value', 0],
];
for (const [label, b, ts, wst, wr, ncalls] of cases) {
  const s = setup(ENV, ts, 'ok'); const [st, r] = await res(await s.h(req(b)));
  ok(st === wst && r === wr && s.calls.length === ncalls && !s.calls.some((c) => c.url.includes('lead_submit')), label + ' → ' + st + ' ' + r + ', database not called');
}
for (const [db, wst, wr] of [['busy', 429, 'busy'], ['bad_value', 400, 'bad_value'], [500, 503, 'unavailable'], ['throw', 503, 'unavailable'], ['something', 503, 'unavailable']]) {
  const s = setup(ENV, good, db); const [st, r] = await res(await s.h(req(body())));
  ok(st === wst && r === wr, 'database answer ' + JSON.stringify(db) + ' → ' + st + ' ' + r + ' (never a success the server did not confirm)');
}
{ const s = setup(ENV, good, 'ok');
  const [st] = await res(await s.h(req(body(), { headers: { origin: 'https://evil.example', 'content-type': 'application/json' } })));
  ok(st === 403 && s.calls.length === 0, 'other site origin → 403, nothing called');
  const pre = await s.h(new Request('https://x/', { method: 'OPTIONS', headers: { origin: ORIGIN } }));
  ok(pre.status === 204 && pre.headers.get('access-control-allow-origin') === ORIGIN, 'preflight from the partner page allowed');
  const g = await s.h(new Request('https://x/', { method: 'GET', headers: { origin: ORIGIN } }));
  ok(g.status === 405, 'GET refused'); }
{ const s = setup(ENV, good, 'ok'); await s.h(req(body(), { headers: { origin: ORIGIN, 'content-type': 'application/json' } }));
  ok(JSON.parse(s.calls[1].o.body).p_client_key === hm('ip:unknown'), 'no client address → one shared "unknown" bucket (strict, not skipped)'); }
console.log('PARTNER FN FAILS ' + fails); process.exit(fails ? 1 : 0);
