-- Self-contained test for patch 33 (free delivery threshold, scheduled orders, group/office orders) on an EMPTY local
-- PostgreSQL:  psql -q -f sql/test_patch33.sql  -> "PATCH33 n/n". Same stand-in database as tests 29/32, patches 28 -> 33.
\set QUIET on
\pset tuples_only on
drop schema if exists auth cascade; drop schema public cascade; create schema public; grant usage on schema public to public;
do $$ begin create role anon; exception when duplicate_object then null; end $$;
do $$ begin create role authenticated; exception when duplicate_object then null; end $$;
grant usage on schema public to anon, authenticated;
alter default privileges in schema public grant all on tables to anon, authenticated;
alter default privileges in schema public grant execute on functions to anon, authenticated;
create schema auth; grant usage on schema auth to anon, authenticated;
create function auth.uid() returns uuid language sql stable as $$ select nullif(current_setting('request.jwt.claim.sub', true), '')::uuid $$;
grant execute on function auth.uid() to anon, authenticated;

-- ---------- stand-in of the existing database ----------
create table profiles (id uuid primary key, role text, name text, phone text, banned_at timestamptz);
create table stores (id uuid primary key, name text, owner_id uuid, is_active boolean default true, is_open boolean default true, discount_pct int default 0,
  fee_type text default 'fixed', fee_base numeric default 10, commission_pct numeric default 10);
create table menu_items (id uuid primary key, store_id uuid, name text, price numeric, discount_pct int default 0, available boolean default true, approved boolean default true);
create table orders (id bigint generated always as identity primary key, store_id uuid, customer_id uuid, customer_name text, payment text, address text, lat float8, lng float8,
  client_key text, driver_id uuid, status text default 'pending', subtotal numeric default 0, discount numeric default 0, delivery_fee numeric default 0, tip numeric default 0,
  delivery_base numeric, delivery_extra numeric, delivery_km numeric, promo_code text, promo_discount numeric default 0, total numeric default 0, commission_pct numeric,
  commission numeric, driver_payout numeric, wallet_used numeric not null default 0, wallet_returned_at timestamptz, created_at timestamptz default now(), done_at timestamptz);
create table order_items (id bigint generated always as identity primary key, order_id bigint, item_id uuid, name text, price numeric, qty int, note text, options jsonb);
create table order_customer_phone (order_id bigint primary key, phone text);
create table promo_attempts (id bigint generated always as identity, user_id uuid, code text, ok boolean, at timestamptz default now());
create table app_settings (key text primary key check (key in ('delivery_free_km', 'delivery_step_km', 'delivery_step_price', 'delivery_max_km', 'delivery_road_factor')),
  value numeric not null, updated_at timestamptz not null default now(), updated_by uuid);
insert into app_settings values ('delivery_free_km', 3), ('delivery_step_km', 0.5), ('delivery_step_price', 2), ('delivery_max_km', 15), ('delivery_road_factor', 1.3);
create table wallet_entries (id bigint generated always as identity primary key, user_id uuid not null, amount numeric(12,2) not null check (amount <> 0),
  kind text not null check (kind in ('refund', 'spend', 'return', 'adjust')), order_id bigint, ticket_id bigint, note text, created_by uuid, created_at timestamptz not null default now());
create unique index wallet_one_spend_per_order on wallet_entries (order_id) where kind = 'spend';
create unique index wallet_one_return_per_order on wallet_entries (order_id) where kind = 'return';
create table ratings (id bigint generated always as identity primary key, order_id bigint, customer_id uuid, store_id uuid, store_stars int, driver_stars int, created_at timestamptz default now());
create table order_events (id bigint generated always as identity, order_id bigint, kind text, at timestamptz default now());
create type order_status as enum ('pending','preparing','ready','pickedup','delivered','rejected','cancelled');
create function owns_store(p uuid) returns boolean language sql stable as $$ select exists(select 1 from stores where id = p and owner_id = auth.uid()) $$;
create function has_perm(p text) returns boolean language sql stable as $$ select false $$;
create function is_admin() returns boolean language sql stable as $$ select exists(select 1 from profiles where id = auth.uid() and role = 'admin') $$;
create function norm_phone(p text) returns text language sql immutable as $$ select nullif(p, '') $$;
create function delivery_calc(p_store uuid, p_lat float8, p_lng float8, p_user uuid) returns jsonb language sql as $$ select '{"fee":10,"fee_full":10,"base":10,"extra":0,"km":2}'::jsonb $$;
create function price_line(p_item uuid, p_opts jsonb) returns jsonb language sql as $$ select jsonb_build_object('unit', (select price from menu_items where id = p_item), 'snap', '[]'::jsonb) $$;
create function promo_eval(p_code text, p_base numeric, p_user uuid, p_strict boolean, p_gate numeric) returns numeric language sql as $$ select round(p_base * 0.1, 2) $$;
create function wallet_balance(p_user uuid default null) returns numeric language sql stable security definer as $$ select coalesce(sum(amount), 0) from wallet_entries where user_id = coalesce(p_user, auth.uid()) $$;
create function check_promo(p_code text, p_store uuid, p_items jsonb) returns jsonb language plpgsql security definer set search_path = public as $$
begin
  if upper(p_code) = 'GOOD' then insert into promo_attempts(user_id, code, ok) values (auth.uid(), 'GOOD', true); return '{"ok":true,"discount":5,"base":50}'::jsonb; end if;
  raise exception 'promo_invalid';
end $$;
-- a place_order with the patch 22 signature, so patch 29 must replace it
create function place_order(p_store uuid, p_items jsonb, p_tip numeric default 0, p_payment text default 'cash', p_address text default '', p_lat float8 default null,
  p_lng float8 default null, p_promo text default null, p_key text default null, p_fee numeric default null, p_wallet numeric default null) returns bigint language sql as $$ select 0::bigint $$;

insert into profiles values ('a0000000-0000-0000-0000-00000000000a', 'admin', 'Admin', '+992900000001', null),
  ('c0000000-0000-0000-0000-000000000001', 'customer', 'Zarina', '+992900000002', null),
  ('c0000000-0000-0000-0000-000000000002', 'customer', 'Bahrom', '+992900000003', null);
insert into stores values ('50000000-0000-0000-0000-000000000001', 'Kebab', null, true, true, 0, 'fixed', 10, 10),
                          ('50000000-0000-0000-0000-000000000002', 'Pizza', null, true, true, 0, 'fixed', 10, 10);
insert into menu_items values ('10000000-0000-0000-0000-000000000001', '50000000-0000-0000-0000-000000000001', 'Plov', 50, 0),
                              ('10000000-0000-0000-0000-000000000002', '50000000-0000-0000-0000-000000000001', 'Salad', 20, 10),
                              ('10000000-0000-0000-0000-000000000003', '50000000-0000-0000-0000-000000000002', 'Pizza', 100, 0);

-- like patch 17: stores readable column by column (commission is private)
revoke select on stores from authenticated; grant select (id, name, is_open, discount_pct) on stores to authenticated;
\i sql/schema_patch28.sql
\i sql/schema_patch29.sql
\i sql/schema_patch30.sql
\i sql/schema_patch31.sql
\i sql/schema_patch32.sql
\i sql/schema_patch33.sql
\i sql/schema_patch33.sql
-- ---------- helpers ----------
create table res(n serial, ok boolean, label text, got text);
create function chk(label text, cond boolean, got text default '') returns void language sql as $$ insert into res(ok, label, got) values (coalesce(cond, false), label, got) $$;
create function as_user(uid text) returns void language plpgsql as $$ begin perform set_config('request.jwt.claim.sub', uid, false); end $$;
create function po(uid text, store text, items jsonb, points int default null, promo text default null, wallet numeric default null, extra jsonb default null) returns text language plpgsql as $f$
declare r text;
begin
  perform set_config('request.jwt.claim.sub', uid, true); set local role authenticated;
  begin r := place_order(store::uuid, items, 0, 'cash', 'Rudaki 1', 38.5, 68.7, promo, null, 10, wallet, points, extra)::text; exception when others then r := 'ERR:' || sqlerrm; end;
  reset role; return r;
end $f$;
create function deliver(o bigint) returns void language sql as $$ update orders set status = 'delivered' where id = o $$;
create function q(uid text, sql text) returns text language plpgsql as $f$
declare r text;
begin perform set_config('request.jwt.claim.sub', uid, true); set local role authenticated;
  begin execute sql into r; exception when others then r := 'ERR:' || sqlerrm; end; reset role; return coalesce(r, ''); end $f$;
\set Z '''c0000000-0000-0000-0000-000000000001'''
\set B '''c0000000-0000-0000-0000-000000000002'''
\set A '''a0000000-0000-0000-0000-00000000000a'''
\set K '''50000000-0000-0000-0000-000000000001'''
\set PL '''[{"item_id":"10000000-0000-0000-0000-000000000001","qty":2},{"item_id":"10000000-0000-0000-0000-000000000002","qty":1}]'''



create function po2(uid text, items jsonb, fee numeric, extra jsonb default null) returns text language plpgsql as $f$
declare r text;
begin perform set_config('request.jwt.claim.sub', uid, true); set local role authenticated;
  begin r := place_order('50000000-0000-0000-0000-000000000001'::uuid, items, 0, 'cash', 'Rudaki 1', 38.5, 68.7, null, null, fee, null, null, extra)::text; exception when others then r := 'ERR:' || sqlerrm; end;
  reset role; return r; end $f$;
update stores set owner_id = 'c0000000-0000-0000-0000-000000000002' where id = '50000000-0000-0000-0000-000000000001';
-- ---------- free delivery threshold (dishes 118 TJS for :PL)
select po2(:Z, :PL, 10) as f0 \gset
select chk('threshold 0 = off: delivery 10 TJS', (select delivery_fee from orders where id = :'f0'::bigint) = 10, :'f0');
select chk('a customer cannot set the threshold', q(:Z, $$select set_my_free_delivery('50000000-0000-0000-0000-000000000001', 100)::text$$) like 'ERR:not_allowed%');
select chk('the owner sets free delivery from 100 TJS', q(:B, $$select set_my_free_delivery('50000000-0000-0000-0000-000000000001', 100)::text$$) = '');
select chk('the app showing 10 TJS is refused (fee changed)', po2(:Z, :PL, 10) = 'ERR:fee_changed');
select po2(:Z, :PL, 0) as f1 \gset
select chk('118 TJS >= 100: delivery 0, waived 10 (paid by the restaurant), courier still paid', (select delivery_fee = 0 and fee_waived = 10 and driver_payout = 10 and total = 118 from orders where id = :'f1'::bigint),
  (select format('fee %s waived %s pay %s total %s', delivery_fee, fee_waived, driver_payout, total) from orders where id = :'f1'::bigint));
select po2(:Z, '[{"item_id":"10000000-0000-0000-0000-000000000002","qty":1}]', 10) as f2 \gset
select chk('below the threshold (1 Salad 18 TJS): delivery 10', (select delivery_fee from orders where id = :'f2'::bigint) = 10, :'f2');
select chk('admin can set it too', q(:A, $$select set_store_free_delivery('50000000-0000-0000-0000-000000000001', 0)::text$$) = '');
-- ---------- scheduled orders
select chk('time too soon (10 min) refused', po2(:Z, :PL, 10, jsonb_build_object('at', now() + interval '10 minutes')) = 'ERR:bad_time');
select chk('time too far (4 days) refused', po2(:Z, :PL, 10, jsonb_build_object('at', now() + interval '4 days')) = 'ERR:bad_time');
select po2(:Z, :PL, 10, jsonb_build_object('at', now() + interval '3 hours')) as s1 \gset
select chk('scheduled in 3 hours: saved', (select scheduled_for > now() + interval '2 hours 59 minutes' from orders where id = :'s1'::bigint), :'s1');
select chk('restaurant cannot start it 3 hours early', q(:B, format($$select set_order_status(%s, 'preparing')::text$$, :'s1')) like 'ERR:too_early%', q(:B, format($$select set_order_status(%s, 'preparing')::text$$, :'s1')));
update orders set scheduled_for = now() + interval '50 minutes' where id = :'s1'::bigint;
select chk('... but can 50 minutes before', q(:B, format($$select set_order_status(%s, 'preparing')::text$$, :'s1')) = '');
select chk('normal orders unchanged: accept right away', q(:B, format($$select set_order_status(%s, 'preparing')::text$$, :'f1')) = '');
-- ---------- group / office order
select q(:Z, $$select group_create('50000000-0000-0000-0000-000000000001')->>'id'$$) as g \gset
select chk('host creates a group order', :'g' ~ '^[0-9a-f-]{36}$', :'g');
select chk('colleague (other account) joins with the link and adds 2 Plov', q(:B, format($$select jsonb_array_length(group_add(%L, '10000000-0000-0000-0000-000000000001', 2)->'items')::text$$, :'g')) = '1');
select chk('host adds 1 Salad', q(:Z, format($$select jsonb_array_length(group_add(%L, '10000000-0000-0000-0000-000000000002', 1)->'items')::text$$, :'g')) = '2');
select chk('a dish of another restaurant is refused', q(:B, format($$select group_add(%L, '10000000-0000-0000-0000-000000000003', 1)::text$$, :'g')) like 'ERR:unavailable%');
select chk('names are kept per dish', q(:Z, format($$select string_agg(x->>'user_name', ',' order by x->>'user_name') from jsonb_array_elements(group_get(%L)->'items') x$$, :'g')) = 'Bahrom,Zarina');
select id as hl from group_items where group_id = :'g'::uuid and item_id = '10000000-0000-0000-0000-000000000002' \gset
select chk('a colleague cannot remove the host dish', q(:B, format($$select group_remove(%s)::text$$, :'hl')) like 'ERR:not_allowed%');
select chk('a colleague cannot place the group order', po2(:B, :PL, 10, jsonb_build_object('group', :'g')) = 'ERR:bad_group');
select chk('the host closes it (no more dishes)', q(:Z, format($$select group_set(%L, 'closed')->>'status'$$, :'g')) = 'closed');
select chk('closed: adding is refused', q(:B, format($$select group_add(%L, '10000000-0000-0000-0000-000000000001', 1)::text$$, :'g')) like 'ERR:group_closed%');
select po2(:Z, '[{"item_id":"10000000-0000-0000-0000-000000000001","qty":2,"note":"Bahrom"},{"item_id":"10000000-0000-0000-0000-000000000002","qty":1,"note":"Zarina"}]', 10, jsonb_build_object('group', :'g')) as go1 \gset
select chk('host places ONE order for everybody, notes keep the names', (select string_agg(note, ',' order by note) from order_items where order_id = :'go1'::bigint) = 'Bahrom,Zarina', :'go1');
select chk('group marked placed with the order', q(:Z, format($$select (group_get(%L)->>'status') || '/' || (group_get(%L)->>'order_id')$$, :'g', :'g')) = 'placed/' || :'go1');
select chk('it cannot be placed twice', po2(:Z, :PL, 10, jsonb_build_object('group', :'g')) = 'ERR:bad_group');
select chk('nobody reads group tables directly', q(:Z, $$select count(*)::text from group_items$$) like 'ERR:permission denied%');
select chk('anonymous cannot open a group', (select not has_function_privilege('anon', 'group_get(uuid)', 'execute')));

select chk('customer app can read the restaurant rules (column grants)', q(:Z, $$select count(*)::text from (select free_delivery_min, points_min_order, cashback_pct from stores) x$$) = '2');
select chk('commission stays private', q(:Z, $$select commission_pct::text from stores limit 1$$) like 'ERR:permission denied%');
-- ---------- points (owner 10 Oct 19:21): 1000 points = 1 TJS; earn rate per restaurant (admin)
select chk('default value: 1000 points = 1 TJS', (select value from app_settings where key = 'loyalty_points_per_tjs') = 1000);
select chk('a customer cannot set a restaurant earn rate', q(:Z, $$select set_store_earn('50000000-0000-0000-0000-000000000001', 50)::text$$) like 'ERR:not_allowed%');
select chk('admin sets 20 points per TJS for this restaurant', q(:A, $$select set_store_earn('50000000-0000-0000-0000-000000000001', 20)::text$$) = '');
select po2(:B, :PL, null) as e1 \gset
select deliver(:'e1'::bigint);
select chk('earned with the restaurant rate (20/TJS)', (select points_earned = ceil((subtotal - discount) * 20 - 0.000001) from orders where id = :'e1'::bigint), (select points_earned::text from orders where id = :'e1'::bigint));
select q(:A, $$select set_store_earn('50000000-0000-0000-0000-000000000001', null)::text$$);
select po2(:B, :PL, null) as e2 \gset
select deliver(:'e2'::bigint);
select chk('empty again = the general 10/TJS', (select points_earned = ceil((subtotal - discount) * 10 - 0.000001) from orders where id = :'e2'::bigint), (select points_earned::text from orders where id = :'e2'::bigint));
select chk('the app can read the restaurant earn rate', q(:Z, $$select count(earn_per_tjs is null or true)::text from stores$$) = '2');
\pset tuples_only off
select n, case when ok then 'PASS' else 'FAIL' end as r, label, left(got, 60) as got from res order by n;
select 'PATCH33 ' || count(*) filter (where ok) || '/' || count(*) from res;
