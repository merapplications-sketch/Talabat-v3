-- Self-contained test for patch 29 (loyalty points, cashback, happy hour) on an EMPTY local PostgreSQL (not Supabase).
--   psql -q -f sql/test_patch29.sql      -> prints "PATCH29 n/n"
-- It builds a small stand-in of the real tables/functions place_order needs (same columns and rules as patches 17-22),
-- applies patch 28 and patch 29 (twice), then places, delivers, cancels orders as real users would.
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
  client_key text, status text default 'pending', subtotal numeric default 0, discount numeric default 0, delivery_fee numeric default 0, tip numeric default 0,
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
\i sql/schema_patch29.sql

-- ---------- helpers ----------
create table res(n serial, ok boolean, label text, got text);
create function chk(label text, cond boolean, got text default '') returns void language sql as $$ insert into res(ok, label, got) values (coalesce(cond, false), label, got) $$;
create function as_user(uid text) returns void language plpgsql as $$ begin perform set_config('request.jwt.claim.sub', uid, false); end $$;
create function po(uid text, store text, items jsonb, points int default null, promo text default null, wallet numeric default null) returns text language plpgsql as $f$
declare r text;
begin
  perform set_config('request.jwt.claim.sub', uid, true); set local role authenticated;
  begin r := place_order(store::uuid, items, 0, 'cash', 'Rudaki 1', 38.5, 68.7, promo, null, 10, wallet, points)::text; exception when others then r := 'ERR:' || sqlerrm; end;
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

-- 1) settings
select chk('defaults: 10 pts per TJS, 1000 pts = 1 TJS, min 1000, 90 days, cashback 0%',
  (select string_agg(key || '=' || value::text, ',' order by key) from app_settings where key like 'loyalty%' or key = 'cashback_pct') = 'cashback_pct=0,loyalty_earn_per_tjs=10,loyalty_expiry_days=90,loyalty_min_redeem=1000,loyalty_points_per_tjs=1000',
  (select string_agg(key || '=' || value::text, ',' order by key) from app_settings where key like 'loyalty%' or key = 'cashback_pct'));
select chk('customer cannot change settings', q(:Z, $$select set_setting('cashback_pct', 5)::text$$) like 'ERR:not_allowed%');
select chk('admin: bad value refused (cashback 80%)', q(:A, $$select set_setting('cashback_pct', 80)::text$$) like 'ERR:bad_value%');
select chk('admin sets cashback 5%', q(:A, $$select set_setting('cashback_pct', 5)::text$$) = '');
select chk('old delivery settings still work', q(:A, $$select set_setting('delivery_step_price', 3)::text$$) = '');

-- 2) normal order (no happy hour, no points): same totals as before. Plov 2x50 + Salad 20 (-10% dish) = sub 120, disc 2, fee 10
select po(:Z, :K, :PL) as o1 \gset
select chk('order placed', :'o1' ~ '^\d+$', :'o1');
select chk('totals unchanged without happy hour', (select subtotal = 120 and discount = 2 and hh_discount = 0 and total = 128 and commission = 11.8 from orders where id = :'o1'::bigint),
  (select format('sub %s disc %s hh %s total %s com %s', subtotal, discount, hh_discount, total, commission) from orders where id = :'o1'::bigint));
select chk('points not usable yet (0 < minimum 1000)', po(:Z, :K, :PL, 500) = 'ERR:points_min');

-- 3) delivered: 118 TJS paid for dishes -> 1180 points, cashback 5% = 5.90 TJS to the wallet, expire in 90 days
select deliver(:'o1'::bigint);
select chk('delivered: 1180 points earned', (select points_earned from orders where id = :'o1'::bigint) = 1180, (select points_earned::text from orders where id = :'o1'::bigint));
select chk('points expire in 90 days', (select abs(extract(epoch from expires_at - now()) - 90 * 86400) < 60 from loyalty_lots where order_id = :'o1'::bigint and kind = 'earn'));
select chk('cashback 5.90 TJS in the wallet', (select amount from wallet_entries where order_id = :'o1'::bigint and kind = 'cashback') = 5.90,
  (select amount::text from wallet_entries where order_id = :'o1'::bigint and kind = 'cashback'));
update orders set status = 'preparing' where id = :'o1'::bigint; select deliver(:'o1'::bigint);
select chk('delivered twice -> points and cashback given once', (select count(*) from loyalty_lots where order_id = :'o1'::bigint) = 1 and (select count(*) from wallet_entries where order_id = :'o1'::bigint and kind = 'cashback') = 1);
select chk('customer summary: balance 1180', q(:Z, $$select (loyalty_summary()->>'balance')$$) = '1180', q(:Z, $$select loyalty_summary()::text$$));
select chk('another customer sees 0', q(:B, $$select (loyalty_summary()->>'balance')$$) = '0');

-- 4) spending points: all usable = 1180 pts = 1.18 TJS (capped by the dishes)
select chk('wrong points amount refused (the app must ask again)', po(:Z, :K, :PL, 1000) = 'ERR:points_changed');
select po(:Z, :K, :PL, 1180) as o2 \gset
select chk('order with 1180 points: total 128 - 1.18 = 126.82', (select points_used = 1180 and points_value = 1.18 and total = 126.82 from orders where id = :'o2'::bigint),
  (select format('pts %s val %s total %s', points_used, points_value, total) from orders where id = :'o2'::bigint));
select chk('balance now 0', q(:Z, $$select (loyalty_summary()->>'balance')$$) = '0');
select chk('restaurant commission not reduced by points', (select commission = 11.8 from orders where id = :'o2'::bigint));
-- 5) cancelled: points come back, once
update orders set status = 'cancelled' where id = :'o2'::bigint;
update orders set status = 'rejected' where id = :'o2'::bigint;
select chk('cancelled order: 1180 points back, once', q(:Z, $$select (loyalty_summary()->>'balance')$$) = '1180' and (select count(*) from loyalty_lots where order_id = :'o2'::bigint) = 1,
  q(:Z, $$select (loyalty_summary()->>'balance')$$));
-- 6) expired points do not count
update loyalty_lots set expires_at = now() - interval '1 minute' where user_id = 'c0000000-0000-0000-0000-000000000001';
select chk('expired points are not counted', q(:Z, $$select (loyalty_summary()->>'balance')$$) = '0');
select chk('... and cannot be used', po(:Z, :K, :PL, 1180) = 'ERR:points_min');
update loyalty_lots set expires_at = now() + interval '10 days' where user_id = 'c0000000-0000-0000-0000-000000000001';

-- 7) happy hour (admin only), Dushanbe time, overnight windows
select chk('customer cannot create a happy hour', q(:Z, $$insert into happy_hours(title, start_time, end_time, discount_pct) values ('x', '10:00', '11:00', 20) returning id::text$$) like 'ERR:%');
select chk('admin creates "Lunch" Mon-Fri 12:00-15:00 -20% (Kebab)',
  q(:A, $$insert into happy_hours(title, store_id, days, start_time, end_time, discount_pct) values ('Lunch', '50000000-0000-0000-0000-000000000001', '{1,2,3,4,5}', '12:00', '15:00', 20) returning id::text$$) ~ '^\d+$');
select chk('admin creates "Night" every day 22:00-02:00 -30% (all)',
  q(:A, $$insert into happy_hours(title, start_time, end_time, discount_pct) values ('Night', '22:00', '02:00', 30) returning id::text$$) ~ '^\d+$');
select chk('Mon 13:00 Dushanbe (08:00 UTC): Kebab 20%', happy_hour_pct('50000000-0000-0000-0000-000000000001', '2026-10-12 08:00+00') = 20);
select chk('Mon 13:00: Pizza 0% (lunch is Kebab only)', happy_hour_pct('50000000-0000-0000-0000-000000000002', '2026-10-12 08:00+00') = 0);
select chk('Sat 13:00: Kebab 0% (weekdays only)', happy_hour_pct('50000000-0000-0000-0000-000000000001', '2026-10-10 08:00+00') = 0);
select chk('Mon 15:00 exactly: ended', happy_hour_pct('50000000-0000-0000-0000-000000000001', '2026-10-12 10:00+00') = 0);
select chk('Sun 01:30 (after Sat 22:00): night 30%', happy_hour_pct('50000000-0000-0000-0000-000000000002', '2026-10-10 20:30+00') = 30);
update happy_hours set active = false where title = 'Night';
select chk('Sun 01:30 with Night switched off: 0%', happy_hour_pct('50000000-0000-0000-0000-000000000002', '2026-10-10 20:30+00') = 0);
-- 8) order during a happy hour: every dish gets the best %, the extra is paid by the platform
insert into happy_hours(title, start_time, end_time, discount_pct) values ('Now', '00:00', '23:59:59', 25);
select po(:B, :K, :PL) as o3 \gset
select chk('happy hour order: discount 2 (restaurant) + 28 extra (platform), total 100',
  (select discount = 2 and hh_discount = 28 and hh_pct = 25 and total = 100 from orders where id = :'o3'::bigint),
  (select format('disc %s hh %s pct %s total %s', discount, hh_discount, hh_pct, total) from orders where id = :'o3'::bigint));
select chk('restaurant commission unchanged during the happy hour', (select commission = 11.8 from orders where id = :'o3'::bigint));
select chk('promo code refused during a happy hour (and not counted as a guess)',
  q(:B, $$select check_promo('GOOD', '50000000-0000-0000-0000-000000000001', '[]')->>'error'$$) = 'promo_offer'
  and (select count(*) from promo_guess where user_id = 'c0000000-0000-0000-0000-000000000002' and bad) = 0);
select deliver(:'o3'::bigint);
select chk('points earned on what was paid (90 TJS -> 900)', (select points_earned from orders where id = :'o3'::bigint) = 900, (select points_earned::text from orders where id = :'o3'::bigint));
delete from happy_hours where title = 'Now';

-- 9) security
select chk('customer cannot write points', q(:Z, $$insert into loyalty_lots(user_id, points, points_left, expires_at, kind) values ('c0000000-0000-0000-0000-000000000001', 99999, 99999, now() + interval '1 day', 'earn') returning id::text$$) like 'ERR:%');
select chk('customer cannot change his points', q(:Z, $$update loyalty_lots set points_left = 99999 returning id::text$$) like 'ERR:%' or q(:Z, $$with u as (update loyalty_lots set points_left = 99999 returning 1) select count(*)::text from u$$) = '0');
select chk('customer sees only his own points history', q(:B, $$select count(*)::text from loyalty_ledger where user_id <> auth.uid()$$) = '0');
select chk('customer cannot call loyalty_spend', q(:Z, $$select loyalty_spend('c0000000-0000-0000-0000-000000000001', 1, null)::text$$) like 'ERR:permission denied%');
select chk('customer cannot call loyalty_balance for someone else', q(:B, $$select loyalty_balance('c0000000-0000-0000-0000-000000000001')::text$$) like 'ERR:permission denied%');
select chk('negative points refused', po(:Z, :K, :PL, -5) = 'ERR:bad_value');

\pset tuples_only off
select n, case when ok then 'PASS' else 'FAIL' end as r, label, left(got, 60) as got from res order by n;
select 'PATCH29 ' || count(*) filter (where ok) || '/' || count(*) from res;
