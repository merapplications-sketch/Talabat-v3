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
  ok(!secs || ok2 <= 4, `40 parallel calls inside one second with rps 4: ${ok2} allowed${secs ? '' : ' (burst crossed a second boundary — bound is 4 per second)'}`);
  await pool.end();
} catch (e) { console.log('FAIL ' + e.message); fails++; }
console.log(`\nNAVIGATION BUDGET CONCURRENCY CHECK ${fails ? 'FAILS ' + fails : 'OK'}`); process.exit(fails ? 1 : 0);
