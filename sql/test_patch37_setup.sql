-- Stand-in schema for patch 37 tests on an EMPTY local PostgreSQL (live column shapes read on 17 Oct, isolated people, the live
-- functions installed from the rollback files). Used by sql/test_patch37.sql and tools/patch37_race.py. Not for any real database.
\set ON_ERROR_STOP on
drop schema if exists auth cascade; drop schema if exists storage cascade; drop schema public cascade; create schema public;
do $$ begin create role anon; exception when duplicate_object then null; end $$;
do $$ begin create role authenticated; exception when duplicate_object then null; end $$;
grant usage on schema public to anon, authenticated;
create schema auth; grant usage on schema auth to anon, authenticated;
create function auth.uid() returns uuid language sql stable as $$ select nullif(current_setting('request.jwt.claim.sub', true), '')::uuid $$;
create type order_status as enum ('pending', 'preparing', 'ready', 'pickedup', 'delivered', 'rejected', 'cancelled');
create type user_role as enum ('customer', 'merchant', 'driver', 'admin');
create table profiles (id uuid primary key, role user_role default 'customer', name text, phone text, driver_status text, accept_blocked boolean default false,
  cash_limit numeric default 1000, online boolean default false);
create table staff_members (user_id uuid, active boolean, perms text[]);
create or replace function has_perm(p text) returns boolean language sql stable security definer set search_path = public as $$
  select auth.uid() is not null and (exists(select 1 from profiles where id = auth.uid() and role = 'admin')
    or exists(select 1 from staff_members s where s.user_id = auth.uid() and s.active and p = any(s.perms))) $$;
create or replace function is_admin() returns boolean language sql stable security definer set search_path = public as $$
  select exists(select 1 from profiles where id = auth.uid() and role = 'admin') $$;
create table orders (id bigint generated always as identity primary key, customer_id uuid, driver_id uuid, status order_status default 'pending',
  payment text, total numeric default 0, wallet_used numeric default 0, wallet_returned_at timestamptz, cash_collected numeric, cash_note text,
  cash_settled_at timestamptz, delivery_photo text, leave_at_door boolean default false, done_at timestamptz, arrived_cust_at timestamptz,
  created_at timestamptz default now(), store_id uuid, scheduled_for timestamptz);
create or replace function owns_store(p uuid) returns boolean language sql stable as $$ select false $$;
create table support_tickets (id bigint generated always as identity primary key, customer_id uuid, order_id bigint references orders(id) on delete set null,
  reason text default 'other', status text default 'open', admin_note text, refund_amount numeric check (refund_amount is null or (refund_amount >= 0 and refund_amount <= 100000)),
  handled_by uuid, closed_at timestamptz, created_at timestamptz default now(), updated_at timestamptz default now(), last_staff_at timestamptz,
  last_customer_at timestamptz default now(), customer_seen_at timestamptz);
create unique index tickets_one_open_per_order on support_tickets (order_id) where order_id is not null and status in ('open', 'in_progress');
create table wallet_entries (id bigint generated always as identity primary key, user_id uuid not null, amount numeric(12,2) not null check (amount <> 0),
  kind text not null check (kind in ('refund', 'spend', 'return', 'adjust', 'cashback')), order_id bigint references orders(id) on delete set null,
  ticket_id bigint references support_tickets(id) on delete set null, note text, created_by uuid, created_at timestamptz not null default now());
create unique index wallet_one_refund_per_ticket on wallet_entries (ticket_id) where kind = 'refund';
create unique index wallet_one_return_per_order on wallet_entries (order_id) where kind = 'return';
create unique index wallet_one_spend_per_order on wallet_entries (order_id) where kind = 'spend';
create function trg_wallet_immutable() returns trigger language plpgsql as $$ begin raise exception 'ledger_immutable'; end $$;
create trigger trg_wallet_no_update before update on wallet_entries for each row execute function trg_wallet_immutable();
-- live automatic wallet return on cancel / reject
create function trg_wallet_return() returns trigger language plpgsql security definer set search_path = public as $$
begin
  if new.status in ('rejected', 'cancelled') and old.status not in ('rejected', 'cancelled')
     and coalesce(new.wallet_used, 0) > 0 and new.wallet_returned_at is null then
    insert into wallet_entries(user_id, amount, kind, order_id) values (new.customer_id, new.wallet_used, 'return', new.id)
    on conflict (order_id) where kind = 'return' do nothing;
    new.wallet_returned_at := now();
  end if;
  return new;
end $$;
create trigger trg_orders_wallet_return before update of status on orders for each row execute function trg_wallet_return();
-- storage stand-in with the live columns that matter
create schema storage;
create table storage.buckets (id text primary key, public boolean, file_size_limit bigint, allowed_mime_types text[]);
create table storage.objects (id uuid primary key default gen_random_uuid(), bucket_id text, name text, owner uuid, owner_id text, metadata jsonb,
  archived_at timestamptz, is_delete_marker boolean default false, created_at timestamptz default now());
insert into storage.buckets values ('proofs', false, 1048576, array['image/jpeg']);

create temp table res (n serial, label text, ok boolean, got text);
create or replace function pg_temp.chk(l text, ok boolean, got text default null) returns void language sql as $$ insert into res(label, ok, got) values (l, coalesce(ok, false), got) $$;
-- run a query as a user and return its single text value (or the error message)
create or replace function pg_temp.val(u uuid, q text) returns text language plpgsql as $$
declare r text;
begin perform set_config('request.jwt.claim.sub', coalesce(u::text, ''), true); execute q into r; return r;
exception when others then return 'ERR ' || sqlerrm; end $$;
-- run a statement as a user, return the error code / message or 'ok'
create or replace function pg_temp.as_user(u uuid, q text) returns text language plpgsql as $$
begin perform set_config('request.jwt.claim.sub', coalesce(u::text, ''), true); execute q; return 'ok';
exception when others then return sqlerrm; end $$;

-- people
insert into profiles(id, role, name) values
 ('a0000000-0000-0000-0000-00000000000a', 'admin', 'A'), ('c0000000-0000-0000-0000-00000000000c', 'customer', 'C'),
 ('d0000000-0000-0000-0000-00000000000d', 'driver', 'D'), ('d0000000-0000-0000-0000-0000000000d2', 'driver', 'D2'),
 ('f0000000-0000-0000-0000-00000000000f', 'customer', 'F'), ('50000000-0000-0000-0000-000000000005', 'customer', 'S');
insert into staff_members values ('f0000000-0000-0000-0000-00000000000f', true, array['finance']), ('50000000-0000-0000-0000-000000000005', true, array['support']);
\set A '''a0000000-0000-0000-0000-00000000000a'''
\set C '''c0000000-0000-0000-0000-00000000000c'''
\set D '''d0000000-0000-0000-0000-00000000000d'''
\set D2 '''d0000000-0000-0000-0000-0000000000d2'''
\set F '''f0000000-0000-0000-0000-00000000000f'''
\set SUP '''50000000-0000-0000-0000-000000000005'''

-- ================= BEFORE: the live functions (from the rollback files) =================
\i sql/rollback_patch37.sql
\i sql/rollback_option_no_cancel_after_delivery.sql
