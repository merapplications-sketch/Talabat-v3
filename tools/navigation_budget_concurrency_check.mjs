// Concurrency check of proposed patch 40 on a real local PostgreSQL 17 server: 40 parallel connections
// reserve against one cap at the same moment; the cap must hold exactly. NOT the live project.
//   PGPORT=<port of a local throw-away postgres> node tools/navigation_budget_concurrency_check.mjs <dir with node_modules/pg>
import fs from 'node:fs'; import path from 'node:path'; import { randomUUID } from 'node:crypto';
import { createRequire } from 'node:module';
// argv[2]: a directory whose node_modules has `pg`; PGPORT env: a local, throw-away PostgreSQL server (started by the runner).
const req = createRequire(path.join(process.argv[2], 'x.js'));
const { Pool } = req('pg'), port = +process.env.PGPORT;
let fails = 0; const ok = (c, m) => { console.log((c ? 'PASS ' : 'FAIL ') + m); if (!c) fails++; };
try {
  const pool = new Pool({ host: '127.0.0.1', port, user: 'postgres', password: 'x', database: 'postgres', max: 40 });
  await pool.query(`do $$ begin create role anon nologin; exception when duplicate_object then null; end $$; do $$ begin create role authenticated nologin; exception when duplicate_object then null; end $$; do $$ begin create role service_role nologin bypassrls; exception when duplicate_object then null; end $$;`);
  await pool.query(fs.readFileSync(new URL('../sql/proposed/patch40_navigation_budget.sql', import.meta.url), 'utf8'));
  const fire = (credits, cap, rps) => pool.query('select public.navigation_reserve_budget($1,$2,$3,$4,$5::uuid) r', ['geoapify', credits, cap, rps, randomUUID()]).then(x => x.rows[0].r);
  // 40 simultaneous requests, 2 credits each, cap 6 (rate 5/s would allow 5) -> the CAP must stop it at exactly 3
  await pool.query('delete from navigation_budget_hours; delete from navigation_budget_requests; update navigation_budget_state set sec = to_timestamp(0), sec_count = 0');
  const res = await Promise.all(Array.from({ length: 40 }, () => fire(2, 6, 5).catch(e => ({ error: e.message }))));
  const allowed = res.filter(r => r.allowed).length, errors = res.filter(r => r.error).length;
  const used = +(await pool.query('select coalesce(sum(credits),0) s from navigation_budget_hours')).rows[0].s;
  const rate = res.filter(r => r.reason === 'rate').length;
  ok(errors === 0, `40 parallel calls: no deadlock / error (${errors})`);
  ok(used === 6 && allowed === 3, `cap 6 held exactly under 40 parallel calls: used ${used} = ${allowed} allowed × 2 (rate-refused ${rate})`);
  // same burst, rate limit 5/s: at most 5 upstream reservations inside one second
  await pool.query('delete from navigation_budget_hours; delete from navigation_budget_requests; update navigation_budget_state set sec = to_timestamp(0), sec_count = 0');
  const t0 = Date.now(), res2 = await Promise.all(Array.from({ length: 40 }, () => fire(1, 3000, 4)));
  const secs = Math.floor(t0 / 1000) === Math.floor(Date.now() / 1000);
  const ok2 = res2.filter(r => r.allowed).length;
  const perSec = (await pool.query(`select max(n)::int m from (select count(*) n from navigation_budget_requests where allowed and credits > 0 group by date_trunc('second', created_at)) x`)).rows[0].m;
  ok(perSec <= 4 && ok2 >= 1, `40 parallel calls, rps 4: ${ok2} allowed in total, at most ${perSec} in any one second${secs ? '' : ' (burst spanned two seconds)'}`);
  // Lock wait across an hour AND a second boundary: time must be taken after the lock (test-only clock in this local DB).
  await pool.query(`create table if not exists test_clock(t timestamptz); delete from test_clock;
    insert into test_clock values (date_trunc('hour', now()) + interval '59 minutes 59.9 seconds');
    create or replace function public.navigation_budget_clock() returns timestamptz language sql volatile as $$ select t from test_clock $$;`);
  const oldHour = (await pool.query(`select date_trunc('hour', t) h, date_trunc('second', t) s from test_clock`)).rows[0];
  // old window: a bucket 24 h before the old hour already uses the whole cap (5) -> refused at the old time;
  // the rate counter is full for the old second
  await pool.query(`delete from navigation_budget_hours; delete from navigation_budget_requests`);
  await pool.query(`insert into navigation_budget_hours values ('geoapify', $1::timestamptz - interval '24 hours', 5)`, [oldHour.h]);
  await pool.query(`update navigation_budget_state set sec = $1, sec_count = 4`, [oldHour.s]);
  const quotaAtOld = await fire(1, 5, 4);
  ok(quotaAtOld.allowed === false && quotaAtOld.reason === 'quota', 'before the boundary: refused (window full, rate full)');
  const holder = await pool.connect(); await holder.query('begin'); await holder.query(`select 1 from navigation_budget_state where provider = 'geoapify' for update`);
  const waiting = fire(1, 5, 4);                                   // blocks on the lock
  await new Promise(r => setTimeout(r, 400));
  await pool.query(`update test_clock set t = t + interval '0.3 seconds'`);   // the clock passes into the next hour and second
  await holder.query('commit'); holder.release();
  const res3 = await waiting;
  const booked = (await pool.query(`select hour, credits from navigation_budget_hours where credits = 1`)).rows[0];
  const st = (await pool.query(`select sec, sec_count from navigation_budget_state`)).rows[0];
  const newHour = new Date(oldHour.h.getTime() + 3600e3), newSec = new Date(oldHour.s.getTime() + 1000);
  ok(res3.allowed === true, 'request that waited for the lock across the boundary is judged at the new time: allowed (' + JSON.stringify(res3) + ')');
  ok(booked && booked.hour.getTime() === newHour.getTime(), 'booked in the new hour bucket (' + (booked && booked.hour.toISOString()) + ')');
  ok(st.sec.getTime() === newSec.getTime() && st.sec_count === 1, 'rate counter restarted in the new second (' + st.sec.toISOString() + ' × ' + st.sec_count + ')');
  // the reverse: lock released still inside the old second -> rate stays full
  await pool.query(`update test_clock set t = date_trunc('hour', now()) + interval '10 minutes 0.1 seconds';
    update navigation_budget_state set sec = date_trunc('second', (select t from test_clock)), sec_count = 4; delete from navigation_budget_hours`);
  const h2 = await pool.connect(); await h2.query('begin'); await h2.query(`select 1 from navigation_budget_state for update`);
  const w2 = fire(1, 5, 4); await new Promise(r => setTimeout(r, 300)); await pool.query(`update test_clock set t = t + interval '0.5 seconds'`);
  await h2.query('commit'); h2.release(); const r4 = await w2;
  ok(r4.allowed === false && r4.reason === 'rate', 'lock released within the same second: still refused «rate»');
  await pool.query(`create or replace function public.navigation_budget_clock() returns timestamptz language sql volatile security invoker set search_path = public as $$ select clock_timestamp() $$; drop table test_clock;`);
  await pool.end();
} catch (e) { console.log('FAIL ' + e.message); fails++; }
console.log(`\nNAVIGATION BUDGET CONCURRENCY CHECK ${fails ? 'FAILS ' + fails : 'OK'}`); process.exit(fails ? 1 : 0);
