-- Self-contained test for patch 35 (admin order search) on an EMPTY local PostgreSQL: psql -q -f sql/test_patch35.sql -> "PATCH35 n/n"
\set QUIET on
\pset tuples_only on
drop schema if exists auth cascade; drop schema public cascade; create schema public; grant usage on schema public to public;
do $$ begin create role authenticated; exception when duplicate_object then null; end $$;
do $$ begin create role anon; exception when duplicate_object then null; end $$;
grant usage on schema public to anon, authenticated;
create schema auth; grant usage on schema auth to authenticated, anon;
create function auth.uid() returns uuid language sql stable as $$ select nullif(current_setting('request.jwt.claim.sub', true), '')::uuid $$;
grant execute on function auth.uid() to authenticated, anon;
create type order_status as enum ('pending','preparing','ready','pickedup','delivered','rejected','cancelled');
create table profiles (id uuid primary key, role text);
create table staff_members (user_id uuid, perms text[], active boolean);
create function has_perm(p text) returns boolean language sql stable security definer set search_path = public as $$
  select auth.uid() is not null and (exists(select 1 from profiles where id = auth.uid() and role = 'admin')
    or exists(select 1 from staff_members s where s.user_id = auth.uid() and s.active and p = any(s.perms))) $$;
create table orders (id bigint primary key, customer_name text, status order_status, created_at timestamptz);
create table order_customer_phone (order_id bigint primary key, phone text);
revoke all on orders, order_customer_phone from authenticated, anon;
insert into profiles values ('a0000000-0000-0000-0000-00000000000a','admin'),('c0000000-0000-0000-0000-000000000001','customer'),
  ('50000000-0000-0000-0000-000000000001','customer'),('50000000-0000-0000-0000-000000000002','customer');
insert into staff_members values ('50000000-0000-0000-0000-000000000001','{support}',true),('50000000-0000-0000-0000-000000000002','{content}',true);
-- 400 orders: the searched ones are old (outside the 300 newest the panel loads)
insert into orders select g, case when g = 12 then 'Зарина Каримова' when g = 13 then '50%_off\x' else 'Клиент ' || g end,
  (case when g % 3 = 0 then 'cancelled' else 'delivered' end)::order_status, now() - (g || ' hours')::interval from generate_series(1, 400) g;
insert into order_customer_phone select g, '+992 90 ' || lpad(g::text, 7, '0') from generate_series(1, 400) g;
\i sql/schema_patch35.sql
\i sql/schema_patch35.sql
create table res(n serial, ok boolean, label text, got text);
create function chk(l text, c boolean, g text default '') returns void language sql as $$ insert into res(ok, label, got) values (coalesce(c, false), l, g) $$;
create function s(uid text, q text, st text default null) returns text language plpgsql as $f$
declare r text;
begin perform set_config('request.jwt.claim.sub', uid, true); set local role authenticated;
  begin select string_agg(id::text, ',' order by x) into r from (select id, row_number() over () x from admin_search_orders(q, st)) z; exception when others then r := 'ERR:' || sqlerrm; end;
  reset role; return coalesce(r, ''); end $f$;
\set A '''a0000000-0000-0000-0000-00000000000a'''
\set C '''c0000000-0000-0000-0000-000000000001'''
\set SUP '''50000000-0000-0000-0000-000000000001'''
\set CON '''50000000-0000-0000-0000-000000000002'''
select chk('by order number (an old order outside the newest 300)', s(:A, '390') = '390', s(:A, '390'));
select chk('number with #', s(:A, '#390') = '390');
select chk('by customer name, any case', s(:A, 'зарина') = '12', s(:A, 'зарина'));
select chk('by phone digits, any format (spaces, +992)', s(:A, '+992 90 000 0012') = '12' and s(:A, '900000012') = '12', s(:A, '+992 90 000 0012'));
select chk('by the last digits of the phone', position('399' in s(:A, '0399')) > 0, s(:A, '0399'));
select chk('% and _ are literal, not wildcards', s(:A, '50%_off') = '13' and s(:A, '%') = '', s(:A, '%'));
select chk('status filter combined with the search', s(:A, '390', 'delivered') = '' and s(:A, '390', 'cancelled') = '390');
select chk('newest first', s(:A, 'Клиент 39') like '39,%', left(s(:A, 'Клиент 39'), 30));
select chk('at most 100 results', (select count(*) from (select 1 from unnest(string_to_array(s(:A, 'Клиент'), ','))) x) <= 50);
select chk('support staff may search', s(:SUP, '390') = '390');
select chk('staff without orders/support may not', s(:CON, '390') like 'ERR:not_allowed%');
select chk('a customer may not', s(:C, '390') like 'ERR:not_allowed%');
select chk('anonymous may not call it', not has_function_privilege('anon', 'admin_search_orders(text, text, integer)', 'execute'));
select chk('empty text refused', s(:A, '  ') like 'ERR:bad_value%');
select chk('unknown status refused', s(:A, '390', 'lost') like 'ERR:bad_value%');
select chk('read-only: no data changed', (select count(*) from orders) = 400 and (select count(*) from order_customer_phone) = 400);
\pset tuples_only off
select n, case when ok then 'PASS' else 'FAIL' end r, label, left(got, 50) got from res order by n;
select 'PATCH35 ' || count(*) filter (where ok) || '/' || count(*) from res;
