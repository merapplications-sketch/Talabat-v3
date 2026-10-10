-- Self-contained test for patch 32 (batch 1: vouchers, minimum order, rating reward, per-restaurant cashback, order options,
-- best dishes, preparation speed) on an EMPTY local PostgreSQL:  psql -q -f sql/test_patch32.sql  -> "PATCH32 n/n"
-- Same stand-in database as test_patch29, then patches 28 -> 32 in the order the owner runs them (32 twice).
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

\i sql/schema_patch28.sql
\i sql/schema_patch29.sql
\i sql/schema_patch30.sql
\i sql/schema_patch31.sql
\i sql/schema_patch32.sql
\i sql/schema_patch32.sql
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


-- Plov 50, Salad 20 (-10% dish). Cart :PL = 2 Plov + 1 Salad -> dishes 118 TJS after the dish discount
select chk('defaults: 1000 points = 10 TJS, vouchers of 1000, minimum order 30, +10 for a rating',
  (select string_agg(key || '=' || value::text, ',' order by key) from app_settings where key in ('loyalty_points_per_tjs','loyalty_voucher_points','loyalty_min_order','loyalty_rate_reward'))
  = 'loyalty_min_order=30,loyalty_points_per_tjs=100,loyalty_rate_reward=10,loyalty_voucher_points=1000',
  (select string_agg(key || '=' || value::text, ',' order by key) from app_settings where key in ('loyalty_points_per_tjs','loyalty_voucher_points','loyalty_min_order','loyalty_rate_reward')));
-- earning rounded UP: 118 TJS -> 1180; an order of 20*0.9 = 18 TJS... use a 12.35 TJS line to see the rounding
insert into menu_items values ('10000000-0000-0000-0000-000000000009', '50000000-0000-0000-0000-000000000001', 'Tea', 12.35, 0);
select po(:Z, :K, '[{"item_id":"10000000-0000-0000-0000-000000000009","qty":1}]') as r1 \gset
select deliver(:'r1'::bigint);
select chk('earning rounded up for the customer: 12.35 TJS -> 124 points (not 123)', (select points_earned from orders where id = :'r1'::bigint) = 124, (select points_earned::text from orders where id = :'r1'::bigint));
-- give 2500 points
insert into loyalty_lots(user_id, points, points_left, expires_at, kind) values (:Z, 2376, 2376, now() + interval '30 days', 'earn');
select chk('balance 2500', q(:Z, $$select loyalty_summary()->>'balance'$$) = '2500', q(:Z, $$select loyalty_summary()::text$$));
select chk('summary tells the app the voucher size and minimum order', q(:Z, $$select (loyalty_summary()->>'voucher_points') || '/' || (loyalty_summary()->>'min_order')$$) = '1000/30');
select chk('2500 points: not a whole voucher amount (2500) refused', po(:Z, :K, :PL, 2500) = 'ERR:points_changed');
select po(:Z, :K, :PL, 2000) as r2 \gset
select chk('2 vouchers = 2000 points = 20 TJS off: total 128 - 20 = 108', (select points_used = 2000 and points_value = 20 and total = 108 from orders where id = :'r2'::bigint),
  (select format('pts %s val %s total %s', points_used, points_value, total) from orders where id = :'r2'::bigint));
select chk('500 points left', q(:Z, $$select loyalty_summary()->>'balance'$$) = '500');
update orders set status = 'cancelled' where id = :'r2'::bigint;
-- minimum order: 1 Salad = 18 TJS < 30
select chk('dishes below the minimum (18 < 30 TJS): points refused', po(:Z, :K, '[{"item_id":"10000000-0000-0000-0000-000000000002","qty":1}]', 1000) = 'ERR:points_min_order');
select chk('customer cannot set a restaurant minimum', q(:Z, $$select set_store_loyalty('50000000-0000-0000-0000-000000000001', 10, null)::text$$) like 'ERR:not_allowed%');
select chk('admin sets this restaurant minimum to 15 TJS', q(:A, $$select set_store_loyalty('50000000-0000-0000-0000-000000000001', 15, null)::text$$) = '');
select po(:Z, :K, '[{"item_id":"10000000-0000-0000-0000-000000000002","qty":1}]', 1000) as r3 \gset
select chk('... now 18 TJS of dishes is enough; 1000 points = 10 TJS', (select points_value = 10 from orders where id = :'r3'::bigint), :'r3');
update orders set status = 'cancelled' where id = :'r3'::bigint;
-- per-restaurant cashback, paid by the restaurant
update stores set owner_id = 'c0000000-0000-0000-0000-000000000002' where id = '50000000-0000-0000-0000-000000000002';
select chk('a customer cannot set another restaurant cashback', q(:Z, $$select set_my_cashback('50000000-0000-0000-0000-000000000002', 5)::text$$) like 'ERR:not_allowed%');
select chk('the owner sets 5% cashback for his restaurant', q(:B, $$select set_my_cashback('50000000-0000-0000-0000-000000000002', 5)::text$$) = '');
select po(:Z, '50000000-0000-0000-0000-000000000002', '[{"item_id":"10000000-0000-0000-0000-000000000003","qty":1}]') as r4 \gset
select deliver(:'r4'::bigint);
select chk('cashback 5% of 100 TJS = 5.00 to the wallet (the app-wide % is 0)', (select amount from wallet_entries where order_id = :'r4'::bigint and kind = 'cashback') = 5,
  (select coalesce(amount::text, 'none') from wallet_entries where order_id = :'r4'::bigint and kind = 'cashback'));
-- rating reward
insert into ratings(order_id, customer_id, store_id, store_stars) values (:'r4'::bigint, :Z, '50000000-0000-0000-0000-000000000002', 5);
insert into ratings(order_id, customer_id, store_id, driver_stars) values (:'r4'::bigint, :Z, '50000000-0000-0000-0000-000000000002', 4);
select chk('rating gives +10 points, once per order', (select count(*) from loyalty_lots where order_id = :'r4'::bigint and kind = 'reward') = 1
  and (select points from loyalty_lots where order_id = :'r4'::bigint and kind = 'reward') = 10);
-- order options
select po(:Z, :K, :PL, null, null, null, '{"door":true,"subst":"replace","gift":{"name":"Мадина","phone":"+992901112233"}}') as r5 \gset
select chk('options stored: leave at the door, replace a missing dish, gift', (select leave_at_door and substitution = 'replace' and is_gift from orders where id = :'r5'::bigint), :'r5');
select chk('recipient stored', (select name || ' ' || phone from order_recipient where order_id = :'r5'::bigint) = 'Мадина +992901112233');
select chk('bad substitution refused', po(:Z, :K, :PL, null, null, null, '{"subst":"steal"}') = 'ERR:bad_value');
select chk('gift without a phone refused', po(:Z, :K, :PL, null, null, null, '{"gift":{"name":"A","phone":""}}') = 'ERR:bad_gift');
select chk('the customer reads his gift recipient', q(:Z, $$select count(*)::text from order_recipient$$) = '1');
select chk('another customer cannot read it', q(:B, $$select count(*)::text from order_recipient$$) = '0');
select chk('nobody can write recipients directly', q(:Z, $$insert into order_recipient values (1, 'xx', '1') returning order_id::text$$) like 'ERR:%');
-- best dishes / speed
select po(:B, :K, '[{"item_id":"10000000-0000-0000-0000-000000000001","qty":3}]') as r6 \gset
select deliver(:'r6'::bigint);
insert into order_events(order_id, kind, at) select id, 'preparing', created_at from orders where status = 'delivered';
insert into order_events(order_id, kind, at) select id, 'ready', created_at + interval '12 minutes' from orders where status = 'delivered';
select chk('best dishes: Plov (sold 2+) is listed', q(:Z, $$select string_agg(item_id::text, ',') from best_dishes()$$) like '%10000000-0000-0000-0000-000000000001%', q(:Z, $$select string_agg(item_id::text || ':' || cnt, ',') from best_dishes()$$));
select chk('preparation speed: Kebab about 12 minutes', q(:Z, $$select avg_min::text from store_speed() where store_id = '50000000-0000-0000-0000-000000000001'$$) = '12.0', q(:Z, $$select string_agg(store_id || ':' || avg_min || ':' || n, ',') from store_speed()$$));
select chk('anonymous cannot call best_dishes', (select not has_function_privilege('anon', 'best_dishes(uuid,int)', 'execute')));

\pset tuples_only off
select n, case when ok then 'PASS' else 'FAIL' end as r, label, left(got, 60) as got from res order by n;
select 'PATCH32 ' || count(*) filter (where ok) || '/' || count(*) from res;
