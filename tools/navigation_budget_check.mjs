// Local check of proposed patch 40 (shared routing budget) on a real PostgreSQL 16 engine (PGlite, in-process) and of its
// binding to the route Edge Function handler. NOT the live project; nothing is applied anywhere.
//   node tools/navigation_budget_check.mjs <path to node_modules/@electric-sql/pglite/dist/index.js>
import fs from 'node:fs';
import { randomUUID } from 'node:crypto';
import { makeHandler } from '../supabase/functions/route/handler.js';
const { PGlite } = await import(process.argv[2]);
let fails = 0, n = 0;
const ok = (c, m) => { n++; console.log((c ? 'PASS ' : 'FAIL ') + m); if (!c) fails++; };
const db = new PGlite();
await db.exec(`create role anon nologin; create role authenticated nologin; create role service_role nologin bypassrls;`);
const patch = fs.readFileSync(new URL('../sql/proposed/patch40_navigation_budget.sql', import.meta.url), 'utf8');
await db.exec(patch); await db.exec(patch);   // safe to run again
ok(true, 'patch 40 applies twice without error (idempotent DDL)');
const call = async (credits, cap = 10, rps = 4, id = randomUUID(), provider = 'geoapify') =>
  (await db.query('select public.navigation_reserve_budget($1,$2,$3,$4,$5::uuid) as r', [provider, credits, cap, rps, id])).rows[0].r;
const used = async () => +(await db.query(`select coalesce(sum(credits),0) as s from navigation_budget_hours`)).rows[0].s;
const resetRate = () => db.exec(`update navigation_budget_state set sec = to_timestamp(0), sec_count = 0`);

// 1) cap across "drivers / cities": callers carry no user or city, one ledger for all
let allowed = 0;
for (let i = 0; i < 7; i++) { await resetRate(); if ((await call(2)).allowed) allowed++; }
ok(allowed === 5 && await used() === 10, `cap 10, 2 credits each: exactly 5 reservations, 10 credits used (${allowed}, ${await used()})`);
await resetRate(); let r = await call(2);
ok(r.allowed === false && r.reason === 'quota' && r.retryAfterS >= 60, 'next request refused: quota + retryAfterS (' + JSON.stringify(r) + ')');
await resetRate(); r = await call(0);
ok(r.allowed === false && r.reason === 'quota', 'zero-credit (cache) check is refused once exhausted');
await db.exec(`delete from navigation_budget_hours; delete from navigation_budget_requests`);
await resetRate(); r = await call(0);
ok(r.allowed === true && await used() === 0, 'zero-credit check allowed while budget remains, consumes nothing');
// 2) idempotency
const id = randomUUID(); await resetRate(); const a = await call(3, 10, 4, id); await resetRate(); const b = await call(3, 10, 4, id);
ok(a.allowed && b.allowed && await used() === 3, 'same request id twice: same answer, reserved once (' + await used() + ')');
// 3) per-second rate (actual upstream requests only)
await db.exec(`update navigation_budget_state set sec = date_trunc('second', clock_timestamp()), sec_count = 4`);
r = await call(1);
ok(r.allowed === false && r.reason === 'rate' && r.retryAfterS === 1, 'rps 4 already used in this second: refused «rate»');
await db.exec(`update navigation_budget_state set sec = date_trunc('second', clock_timestamp()), sec_count = 4`);
r = await call(0);
ok(r.allowed === true, 'cache check does not count against the per-second rate');
// 4) hard limits inside SQL
await db.exec(`delete from navigation_budget_hours; delete from navigation_budget_requests`);
await db.exec(`insert into navigation_budget_hours values ('geoapify', date_trunc('hour', now()), 2999)`);
await resetRate(); r = await call(2, 999999, 99);
ok(r.allowed === false && r.reason === 'quota', 'caller cap 999 999 is clamped to 3 000 in SQL');
for (const [c, cap, rps, prov] of [[-1, 10, 4, 'geoapify'], [101, 10, 4, 'geoapify'], [1, -1, 4, 'geoapify'], [1, 10, 0, 'geoapify'], [1, 10, 4, 'paid-other']]) {
  r = await call(c, cap, rps, randomUUID(), prov);
  ok(r.allowed === false && r.reason === 'bad_value', `bad input refused (credits ${c}, cap ${cap}, rps ${rps}, provider ${prov})`);
}
// 5) rolling window never shorter than 24 h
await db.exec(`delete from navigation_budget_hours; delete from navigation_budget_requests;
  insert into navigation_budget_hours values ('geoapify', date_trunc('hour', now()) - interval '24 hours', 10)`);
await resetRate(); r = await call(1);
ok(r.allowed === false, 'credits from 24 h ago still count (window >= 24 h)');
await db.exec(`update navigation_budget_hours set hour = date_trunc('hour', now()) - interval '25 hours'`);
await resetRate(); r = await call(1);
ok(r.allowed === true, 'credits older than 25 h no longer count');
// 6) privileges: browser roles cannot call or touch the ledger (incl. TRUNCATE, which RLS does not cover)
const priv = (await db.query(`select
  has_function_privilege('anon','public.navigation_reserve_budget(text,integer,integer,integer,uuid)','execute') fa,
  has_function_privilege('authenticated','public.navigation_reserve_budget(text,integer,integer,integer,uuid)','execute') fu,
  has_function_privilege('service_role','public.navigation_reserve_budget(text,integer,integer,integer,uuid)','execute') fs,
  has_table_privilege('authenticated','public.navigation_budget_hours','select,insert,update,delete,truncate') tu,
  has_table_privilege('anon','public.navigation_budget_requests','select,insert,update,delete,truncate') ta`)).rows[0];
ok(!priv.fa && !priv.fu && priv.fs && !priv.tu && !priv.ta, 'execute: service_role only; anon / authenticated: no table privilege at all (' + JSON.stringify(priv) + ')');
// 7) binding: the route handler with this ledger (exact index.ts mapping) — shared by two users in two cities
await db.exec(`delete from navigation_budget_hours; delete from navigation_budget_requests`); await resetRate();
const reserveBudget = async v => { await resetRate(); return call(v.credits, v.dailyCap, v.rps, v.requestId, v.provider); };
let upstream = 0;
const fetch = async () => { upstream++; return new Response(JSON.stringify({ features: [{ properties: { distance: 4210, time: 611, legs: [{ steps: [] }] }, geometry: { type: 'LineString', coordinates: [[69.24, 41.29], [69.25, 41.30]] } }] }), { status: 200 }); };
const env = { GEOAPIFY_KEY: 'k', ALLOWED_ORIGINS: 'https://app.example', NAVIGATION_CONFIG: JSON.stringify({ internal: true, provider: 'geoapify', dailyCredits: 6, reservationCredits: 2, rps: 4 }) };
const req = (from, to) => new Request('https://fn/route', { method: 'POST', headers: { authorization: 'Bearer x', origin: 'https://app.example', 'content-type': 'application/json' }, body: JSON.stringify({ from, to }) });
const hDushanbe = makeHandler({ fetch, env, getUser: async () => 'driver-dushanbe', reserveBudget });
const hKhujand = makeHandler({ fetch, env, getUser: async () => 'driver-khujand', reserveBudget });
const modes = [];
modes.push((await (await hDushanbe(req([38.56, 68.78], [38.57, 68.79]))).json()).mode);
modes.push((await (await hKhujand(req([40.28, 69.62], [40.29, 69.63]))).json()).mode);
modes.push((await (await hDushanbe(req([38.56, 68.78], [38.58, 68.80]))).json()).mode);
const last = await (await hKhujand(req([40.28, 69.62], [40.30, 69.64]))).json();
ok(modes.join() === 'internal,internal,internal' && last.mode === 'tracking' && last.reason === 'quota' && upstream === 3,
  'two cities share one budget (6 credits = 3 routes); the 4th falls back to tracking «quota», no upstream call (' + modes + ' / ' + last.reason + ', upstream ' + upstream + ')');
ok(!('coords' in last) && !('duration_s' in last), 'tracking fallback carries no route / ETA');
const noLedger = makeHandler({ fetch, env, getUser: async () => 'u' });
const nl = await (await noLedger(req([38.56, 68.78], [38.57, 68.79]))).json();
ok(nl.mode === 'tracking' && nl.reason === 'budget_unavailable' && upstream === 3, 'no ledger bound: routing refused («budget_unavailable»), upstream never called');
const broken = makeHandler({ fetch, env, getUser: async () => 'u', reserveBudget: async () => { throw new Error('rpc missing'); } });
const br = await (await broken(req([38.56, 68.78], [38.57, 68.79]))).json();
ok(br.mode === 'tracking' && br.reason === 'budget_unavailable' && upstream === 3, 'ledger error (RPC missing / timeout): routing refused, upstream never called');
console.log(`\nNAVIGATION BUDGET CHECK ${fails ? 'FAILS ' + fails + ' of ' + n : 'OK (' + n + ')'}`); process.exit(fails ? 1 : 0);
