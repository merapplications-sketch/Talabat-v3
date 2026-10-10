-- Self-contained test for patch 34 (courier steps, photo proof, restaurant cancel reasons) on an EMPTY local
-- PostgreSQL:  psql -q -f sql/test_patch34.sql  -> "PATCH34 n/n". Same stand-in database as test 33, patches 28 -> 34.
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

-- stand-in of Supabase storage (only what the policies use)
drop schema if exists storage cascade; create schema storage; grant usage on schema storage to authenticated;
create table storage.buckets (id text primary key, name text, public boolean, file_size_limit bigint, allowed_mime_types text[]);
create table storage.objects (id bigint generated always as identity primary key, bucket_id text, name text);
alter table storage.objects enable row level security;
grant select, insert on storage.objects to authenticated;
create function storage.foldername(name text) returns text[] language sql immutable as $$ select (string_to_array(name, '/'))[1:array_length(string_to_array(name, '/'), 1) - 1] $$;
grant execute on function storage.foldername(text) to authenticated;
-- the deliver_order of patch 21 (patch 34 must replace it)
alter table orders add column cash_collected numeric, add column cash_note text;
create function deliver_order(p_id bigint, p_cash numeric default null, p_note text default null) returns void language sql as $$ select $$;
insert into profiles values ('d0000000-0000-0000-0000-00000000000d', 'driver', 'Rustam', '+992900000009', null),
  ('d0000000-0000-0000-0000-00000000000e', 'driver', 'Other', '+992900000010', null);
\i sql/schema_patch28.sql
\i sql/schema_patch29.sql
\i sql/schema_patch30.sql
\i sql/schema_patch31.sql
\i sql/schema_patch32.sql
\i sql/schema_patch33.sql
\i sql/schema_patch34.sql
\i sql/schema_patch34.sql
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
\set D '''d0000000-0000-0000-0000-00000000000d'''
\set D2 '''d0000000-0000-0000-0000-00000000000e'''
create function as_do(uid text, sql text) returns text language plpgsql as $f$
declare r text;
begin perform set_config('request.jwt.claim.sub', uid, true); set local role authenticated;
  begin execute sql; r := 'ok'; exception when others then r := 'ERR:' || sqlerrm; end; reset role; return r; end $f$;
-- an order of Zarina, taken by courier D, being prepared
select po2(:Z, :PL, 10) as o1 \gset
update orders set driver_id = :D::uuid, status = 'preparing' where id = :'o1'::bigint;
select chk('another courier cannot mark arrival', as_do(:D2, format('select driver_arrived(%s, ''store'')', :'o1')) like 'ERR:not_allowed%');
select as_do(:D, format('select driver_arrived(%s, ''store'')', :'o1')) as r2 \gset
select chk('courier: at the restaurant', :'r2' = 'ok' and (select arrived_store_at is not null from orders where id = :'o1'::bigint));
select arrived_store_at as t1 from orders where id = :'o1'::bigint \gset
select pg_sleep(0.02);
select as_do(:D, format('select driver_arrived(%s, ''store'')', :'o1'));
select chk('pressing again keeps the first time', (select arrived_store_at = :'t1'::timestamptz from orders where id = :'o1'::bigint));
select chk('at the customer is refused before pick-up', as_do(:D, format('select driver_arrived(%s, ''customer'')', :'o1')) like 'ERR:bad_transition%');
select chk('pick-up refused until the restaurant presses ready', as_do(:D, format('select set_order_status(%s, ''pickedup'')', :'o1')) like 'ERR:bad_transition%');
update orders set status = 'ready' where id = :'o1'::bigint;
select chk('pick-up after ready', as_do(:D, format('select set_order_status(%s, ''pickedup'')', :'o1')) = 'ok');
select as_do(:D, format('select driver_arrived(%s, ''customer'')', :'o1')) as r7 \gset
select chk('courier: at the customer', :'r7' = 'ok' and (select arrived_cust_at is not null from orders where id = :'o1'::bigint));
select chk('unknown place refused', as_do(:D, format('select driver_arrived(%s, ''moon'')', :'o1')) like 'ERR:bad_value%');
-- photo proof
update orders set leave_at_door = true where id = :'o1'::bigint;
select total as tot1 from orders where id = :'o1'::bigint \gset
select chk('leave at the door: no photo = refused', as_do(:D, format('select deliver_order(%s, %s, null)', :'o1', :'tot1')) like 'ERR:photo_required%');
select chk('photo of another folder refused', as_do(:D, format('select deliver_order(%s, %s, null, %L)', :'o1', :'tot1', 'd0000000-0000-0000-0000-00000000000e/' || :'o1' || '/abcdefgh12.jpg')) like 'ERR:bad_value%');
select chk('photo upload: the courier into his folder for this order', as_do(:D, format($$insert into storage.objects(bucket_id, name) values ('proofs', 'd0000000-0000-0000-0000-00000000000d/%s/abcdefgh12.jpg')$$, :'o1')) = 'ok');
select chk('photo upload into another order is refused', as_do(:D, $$insert into storage.objects(bucket_id, name) values ('proofs', 'd0000000-0000-0000-0000-00000000000d/999/abcdefgh13.jpg')$$) like 'ERR:%row-level%');
select chk('another courier cannot upload for this order', as_do(:D2, format($$insert into storage.objects(bucket_id, name) values ('proofs', 'd0000000-0000-0000-0000-00000000000e/%s/abcdefgh14.jpg')$$, :'o1')) like 'ERR:%row-level%');
select as_do(:D, format('select deliver_order(%s, %s, null, %L)', :'o1', :'tot1', 'd0000000-0000-0000-0000-00000000000d/' || :'o1' || '/abcdefgh12.jpg')) as r14 \gset
select chk('delivered with the photo', :'r14' = 'ok'
  and (select status = 'delivered' and delivery_photo like '%abcdefgh12.jpg' from orders where id = :'o1'::bigint));
select chk('the customer of the order can open the photo', q(:Z, $$select count(*)::text from storage.objects where bucket_id = 'proofs'$$) = '1');
select chk('another customer cannot', q(:B, $$select count(*)::text from storage.objects where bucket_id = 'proofs'$$) = '0');
select chk('the courier can', q(:D, $$select count(*)::text from storage.objects where bucket_id = 'proofs'$$) = '1');
select chk('photos are private (bucket not public)', (select not public from storage.buckets where id = 'proofs'));
-- a normal order: old call without a photo still works
select po2(:Z, :PL, 10) as o2 \gset
update orders set driver_id = :D::uuid, status = 'pickedup' where id = :'o2'::bigint;
select total as tot2 from orders where id = :'o2'::bigint \gset
select chk('normal delivery needs no photo (old 3-value call)', as_do(:D, format('select deliver_order(p_id => %s, p_cash => %s, p_note => null)', :'o2', :'tot2')) = 'ok');
-- the restaurant cancels with a reason (owner of Kebab is Bahrom)
select po2(:Z, :PL, 10) as o3 \gset
select chk('a customer cannot use the restaurant cancel', as_do(:Z, format('select reject_order(%s, ''too_busy'')', :'o3')) like 'ERR:not_allowed%');
select chk('unknown reason refused', as_do(:B, format('select reject_order(%s, ''lazy'')', :'o3')) like 'ERR:bad_value%');
select chk('"other" needs a note', as_do(:B, format('select reject_order(%s, ''other'', '' '')', :'o3')) like 'ERR:note_required%');
select as_do(:B, format('select reject_order(%s, ''out_of_stock'', ''нет плова'')', :'o3')) as r23 \gset
select chk('out of stock: rejected with the reason', :'r23' = 'ok'
  and (select status = 'rejected' and cancel_reason = 'out_of_stock' and cancel_note = 'нет плова' and cancelled_by = 'store' and done_at is not null from orders where id = :'o3'::bigint));
select po2(:Z, :PL, 10) as o4 \gset
update orders set status = 'preparing' where id = :'o4'::bigint;
select chk('also while preparing', as_do(:B, format('select reject_order(%s, ''too_busy'')', :'o4')) = 'ok');
select po2(:Z, :PL, 10) as o5 \gset
update orders set status = 'ready' where id = :'o5'::bigint;
select chk('not once it is ready (the courier may be on the way)', as_do(:B, format('select reject_order(%s, ''closing'')', :'o5')) like 'ERR:bad_transition%');
select chk('anonymous cannot call the new functions', not has_function_privilege('anon', 'reject_order(bigint, text, text)', 'execute') and not has_function_privilege('anon', 'driver_arrived(bigint, text)', 'execute'));
select chk('only one deliver_order left (no ambiguity)', (select count(*) from pg_proc where proname = 'deliver_order') = 1);

\pset tuples_only off
select n, case when ok then 'PASS' else 'FAIL' end as r, label, left(got, 60) as got from res order by n;
select 'PATCH34 ' || count(*) filter (where ok) || '/' || count(*) from res;
