-- Self-contained test for patch 30 on an EMPTY local PostgreSQL (not Supabase):  psql -q -f sql/test_patch30.sql  -> "PATCH30 n/n"
-- The real old check_promo is not in this repository, so the guard is tested against THREE possible old behaviours for a wrong
-- code:  A) raises 'promo_invalid' (rolls back its own failed-attempt row)  B) answers {"ok":false,"error":"invalid"}
--        C) raises 'not_found'          A28) like A but patch 28 was run before patch 30.
-- In every case the 11th wrong code must be refused with too_many, real codes must keep working.
\set QUIET on
\pset tuples_only on
drop schema if exists r30 cascade; create schema r30; create table r30.res(n serial, ok boolean, scen text, label text, got text);
\set scen A
\i sql/test_patch30_case.sql
\set scen B
\i sql/test_patch30_case.sql
\set scen C
\i sql/test_patch30_case.sql
\set scen A28
\i sql/test_patch30_case.sql
\pset tuples_only off
select n, case when ok then 'PASS' else 'FAIL' end as r, scen, label, left(got, 50) as got from r30.res order by n;
select 'PATCH30 ' || count(*) filter (where ok) || '/' || count(*) from r30.res;
