// Local check of proposed patch 40 (shared routing budget) on a real PostgreSQL 16 engine (PGlite, in-process) and of its
// binding to the route Edge Function handler. NOT the live project; nothing is applied anywhere.
//   node tools/navigation_budget_check.mjs <path to node_modules/@electric-sql/pglite/dist/index.js>
import fs from 'node:fs';
import { randomUUID } from 'node:crypto';
import { makeHandler } from '../supabase/functions/route/handler.js';
import { routeCredits } from '../supabase/functions/route/config.js';
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
  has_function_privilege('authenticated','public.navigation_settle_budget(text,uuid,integer)','execute') su,
  has_table_privilege('authenticated','public.navigation_budget_hours','select,insert,update,delete,truncate') tu,
  has_table_privilege('anon','public.navigation_budget_requests','select,insert,update,delete,truncate') ta`)).rows[0];
ok(!priv.fa && !priv.fu && !priv.su && priv.fs && !priv.tu && !priv.ta, 'execute: service_role only; anon / authenticated: no table privilege at all (' + JSON.stringify(priv) + ')');
// 7) binding: the route handler with this ledger (exact index.ts mapping) — shared by two users in two cities
await db.exec(`delete from navigation_budget_hours; delete from navigation_budget_requests`); await resetRate();
const reserveBudget = async v => { await resetRate(); return call(v.credits, v.dailyCap, v.rps, v.requestId, v.provider); };
const settleBudget = async v => (await db.query('select public.navigation_settle_budget($1,$2::uuid,$3) r', [v.provider, v.requestId, v.credits])).rows[0].r;
let upstream = 0, lastUrl = '';
const route = m => new Response(JSON.stringify({ features: [{ properties: { distance: m, time: 611, legs: [{ steps: [] }] }, geometry: { type: 'LineString', coordinates: [[69.24, 41.29], [69.25, 41.30]] } }] }), { status: 200 });
const fetch = async u => { upstream++; lastUrl = u; return route(4210); };
const cfg = x => JSON.stringify({ internal: true, provider: 'geoapify', rps: 4, ...x });
const env = { GEOAPIFY_KEY: 'k', ALLOWED_ORIGINS: 'https://app.example', NAVIGATION_CONFIG: cfg({ dailyCredits: 3 }) };
const req = (from, to) => new Request('https://fn/route', { method: 'POST', headers: { authorization: 'Bearer x', origin: 'https://app.example', 'content-type': 'application/json' }, body: JSON.stringify({ from, to }) });
const hDushanbe = makeHandler({ fetch, env, getUser: async () => 'driver-dushanbe', reserveBudget, settleBudget });
const hKhujand = makeHandler({ fetch, env, getUser: async () => 'driver-khujand', reserveBudget, settleBudget });
const modes = [];
modes.push((await (await hDushanbe(req([38.56, 68.78], [38.57, 68.79]))).json()).mode);
modes.push((await (await hKhujand(req([40.28, 69.62], [40.29, 69.63]))).json()).mode);
modes.push((await (await hDushanbe(req([38.56, 68.78], [38.58, 68.80]))).json()).mode);
const last = await (await hKhujand(req([40.28, 69.62], [40.30, 69.64]))).json();
ok(modes.join() === 'internal,internal,internal' && last.mode === 'tracking' && last.reason === 'quota' && upstream === 3,
  'two cities share one budget (3 credits = 3 routes); the 4th falls back to tracking «quota», no upstream call (' + modes + ' / ' + last.reason + ', upstream ' + upstream + ')');
ok(!('coords' in last) && !('duration_s' in last), 'tracking fallback carries no route / ETA');
const noLedger = makeHandler({ fetch, env, getUser: async () => 'u' });
const nl = await (await noLedger(req([38.56, 68.78], [38.57, 68.79]))).json();
ok(nl.mode === 'tracking' && nl.reason === 'budget_unavailable' && upstream === 3, 'no ledger bound: routing refused («budget_unavailable»), upstream never called');
const broken = makeHandler({ fetch, env, getUser: async () => 'u', reserveBudget: async () => { throw new Error('rpc missing'); }, settleBudget });
const br = await (await broken(req([38.56, 68.78], [38.57, 68.79]))).json();
ok(br.mode === 'tracking' && br.reason === 'budget_unavailable' && upstream === 3, 'ledger error (RPC missing / timeout): routing refused, upstream never called');
const noSettle = makeHandler({ fetch, env: { ...env, NAVIGATION_CONFIG: cfg({ dailyCredits: 100 }) }, getUser: async () => 'u', reserveBudget });
const ns = await (await noSettle(req([38.56, 68.78], [38.57, 68.79]))).json();
ok(ns.reason === 'budget_unavailable' && upstream === 3, 'settlement not bound: no upstream call (cost could not be recorded)');

// 8) cost before the call (review of f174ce9, blocker 1) — evidence independent of routeCredits():
//    the request sent has only the options of the published price; the published example (630 340 m = 2 credits) is met.
const q = new URL(lastUrl).searchParams;
ok([...q.keys()].sort().join() === 'apiKey,lang,mode,waypoints' && q.get('waypoints').split('|').length === 2 && q.get('mode') === 'drive',
  'upstream request restricted: 2 waypoints, mode drive, no `details` (no unpublished surcharge): ' + [...q.keys()].sort().join());
ok(routeCredits(630340) === 2, 'Geoapify docs example: route of 630 340 m costs 2 credits -> ' + routeCredits(630340));
ok(routeCredits(4210) === 1 && routeCredits(0) === 1, 'one pair under 500 km: 1 credit (docs: 1 credit per waypoint pair)');

// 9) settlement bound to the call (blocker 2) — reservation + settlement are one ledger row
const rows = async () => (await db.query(`select request_id, credits, allowed, settled, final_credits from navigation_budget_requests order by created_at`)).rows;
await db.exec(`delete from navigation_budget_hours; delete from navigation_budget_requests`); await resetRate();
const ids = []; const spy = f => async v => { ids.push(v.requestId); return f(v); };
const envBig = { ...env, NAVIGATION_CONFIG: cfg({ dailyCredits: 100 }) };
const hLong = makeHandler({ fetch: async () => { upstream++; return route(630340); }, env: envBig, getUser: async () => 'u', reserveBudget: spy(reserveBudget), settleBudget: spy(settleBudget) });
const lr = await (await hLong(req([38.56, 68.78], [38.57, 68.79]))).json(); let rw = await rows();
ok(lr.mode === 'internal' && ids.length === 2 && ids[0] === ids[1] && rw.length === 1 && rw[0].request_id === ids[0],
  'one request id for the reservation and its settlement; one ledger row (' + rw.length + ')');
ok(rw[0].settled && rw[0].final_credits === 2 && await used() === 2, '630 340 m route: reserved 1, settled total 2, booked 2 (' + await used() + ')');
let sr = await settleBudget({ provider: 'geoapify', requestId: ids[0], credits: 2 });
ok(sr.recorded === true && sr.repeat === true && await used() === 2, 'repeat settlement of the same call: recorded, not booked twice');
sr = await settleBudget({ provider: 'geoapify', requestId: ids[0], credits: 5 });
ok(sr.recorded === false && sr.reason === 'conflict' && await used() === 2, 'different total for an already settled call: refused «conflict»');
sr = await settleBudget({ provider: 'geoapify', requestId: randomUUID(), credits: 3 });
ok(sr.recorded === false && sr.reason === 'unknown_request' && await used() === 2, 'settlement without its reservation (random id): refused, nothing booked');
// over the cap: booked truthfully, then everything refused
await db.exec(`update navigation_budget_hours set credits = 99`); await resetRate();
const id9 = randomUUID(); r = await call(1, 100, 4, id9);
sr = await settleBudget({ provider: 'geoapify', requestId: id9, credits: 4 });
ok(r.allowed && sr.recorded && sr.extra === 3 && await used() === 103, 'settlement above the cap is booked truthfully (' + await used() + ')');
await resetRate(); r = await call(0, 100);
ok(r.allowed === false && r.reason === 'quota', 'after an over-cap settlement every further request is refused');

// settlement failure / ambiguity (handler): route withheld, retried with the same id, never booked twice
await db.exec(`delete from navigation_budget_hours; delete from navigation_budget_requests`); await resetRate();
let tries = 0; const failing = async () => { tries++; throw new Error('rpc error'); };
const hFail = makeHandler({ fetch, env: envBig, getUser: async () => 'u', reserveBudget, settleBudget: failing });
const fr = await (await hFail(req([38.56, 68.78], [38.57, 68.79]))).json(); rw = await rows();
ok(fr.mode === 'tracking' && fr.reason === 'budget_unavailable' && !('coords' in fr) && tries === 3 && rw.length === 1 && rw[0].settled === false,
  'settlement RPC error: 3 tries, route withheld, reservation kept as «unsettled» (tries ' + tries + ')');
tries = 0; const unconfirmed = async () => { tries++; return { ok: 1 }; };
const hAmb = makeHandler({ fetch, env: envBig, getUser: async () => 'u', reserveBudget, settleBudget: unconfirmed });
const ar = await (await hAmb(req([38.56, 68.78], [38.58, 68.79]))).json();
ok(ar.reason === 'budget_unavailable' && !('coords' in ar) && tries === 3, 'answer without recorded:true is not accepted (route withheld)');
// lost answer: first settlement commits but the reply is lost, the retry (same id) is a «repeat» -> booked once
tries = 0; const lost = async v => { tries++; const x = await settleBudget(v); if (tries === 1) throw new Error('timeout after commit'); return x; };
const hLost = makeHandler({ fetch: async () => { upstream++; return route(630340); }, env: envBig, getUser: async () => 'u', reserveBudget, settleBudget: lost });
const before9 = await used(); const lo = await (await hLost(req([38.56, 68.78], [38.59, 68.79]))).json();
ok(lo.mode === 'internal' && tries === 2 && await used() - before9 === 2, 'reply lost after commit: retry with the same id, cost booked once (' + (await used() - before9) + ')');
// unsettled guard: once older than 60 s, every new request (all instances, cache included) is refused, no upstream call
const up9 = upstream; await resetRate(); r = await call(1, 100);
ok(r.allowed === true, 'unsettled row younger than 60 s: not yet blocking');
await db.exec(`update navigation_budget_requests set created_at = created_at - interval '61 seconds' where not settled`);
const hAny = makeHandler({ fetch, env: envBig, getUser: async () => 'other-driver', reserveBudget, settleBudget });
const gr = await (await hAny(req([40.28, 69.62], [40.29, 69.63]))).json();
await resetRate(); const g0 = await call(0, 100);
ok(gr.mode === 'tracking' && gr.reason === 'budget_unavailable' && upstream === up9 && g0.allowed === false && g0.reason === 'unsettled',
  'unsettled call older than 60 s: every new request refused «unsettled» (cache too), no upstream call');
await db.exec(`update navigation_budget_requests set created_at = created_at - interval '4 days' where not settled`); await resetRate(); await call(1, 100);
ok((await db.query(`select count(*)::int n from navigation_budget_requests where not settled`)).rows[0].n >= 1, 'housekeeping (> 3 days) never deletes an unsettled row');
for (const u of (await db.query(`select request_id from navigation_budget_requests where not settled`)).rows) await settleBudget({ provider: 'geoapify', requestId: u.request_id, credits: 1 });
await resetRate(); r = await call(1, 100);
ok(r.allowed === true, 'after the owner settles the open rows, reservations resume');
// config change while upstream pending: the call is settled BEFORE «config_changed» is returned
await db.exec(`delete from navigation_budget_hours; delete from navigation_budget_requests`); await resetRate();
const envC = { ...envBig }; let releaseC; const gate = new Promise(res => releaseC = res);
const hC = makeHandler({ fetch: async () => { upstream++; await gate; return route(630340); }, env: envC, getUser: async () => 'u', reserveBudget, settleBudget });
const pc = hC(req([38.56, 68.78], [38.57, 68.79])); await new Promise(res => setTimeout(res, 50));
envC.NAVIGATION_CONFIG = cfg({ dailyCredits: 100, internal: false }); releaseC(); const cr = await (await pc).json(); rw = await rows();
ok(cr.reason === 'config_changed' && rw[0].settled && rw[0].final_credits === 2 && await used() === 2, 'config changed during the call: settled (2 credits) before «config_changed»');
// upstream failure: settled with the reservation kept (no refund)
await db.exec(`delete from navigation_budget_hours; delete from navigation_budget_requests`); await resetRate();
const hDown = makeHandler({ fetch: async () => new Response('', { status: 500 }), env: envBig, getUser: async () => 'u', reserveBudget, settleBudget });
const dr = await (await hDown(req([38.56, 68.78], [38.57, 68.79]))).json(); rw = await rows();
ok(dr.reason === 'upstream' && rw[0].settled && rw[0].final_credits === 1 && await used() === 1, 'upstream error: call settled at the reserved 1 credit (no refund)');

// 10) quota test setting: dailyCredits 0 refuses at once and leaves the ledger exactly as it was
await db.exec(`delete from navigation_budget_hours; delete from navigation_budget_requests;
  insert into navigation_budget_hours values ('geoapify', date_trunc('hour', now()), 7)`); await resetRate();
const before = JSON.stringify((await db.query('select provider, hour, credits from navigation_budget_hours order by hour')).rows);
const env0 = { ...env, NAVIGATION_CONFIG: cfg({ dailyCredits: 0 }) };
const h0 = makeHandler({ fetch, env: env0, getUser: async () => 'u', reserveBudget, settleBudget });
const up0 = upstream, q0 = await (await h0(req([38.56, 68.78], [38.57, 68.79]))).json();
const after = JSON.stringify((await db.query('select provider, hour, credits from navigation_budget_hours order by hour')).rows);
ok(q0.mode === 'tracking' && q0.reason === 'quota' && upstream === up0, 'dailyCredits 0: «quota» at once, no upstream call');
ok(before === after, 'dailyCredits 0 test: booked hour credits unchanged (a refused request row is logged, nothing booked)');
console.log(`\nNAVIGATION BUDGET CHECK ${fails ? 'FAILS ' + fails + ' of ' + n : 'OK (' + n + ')'}`); process.exit(fails ? 1 : 0);
