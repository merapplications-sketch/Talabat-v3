-- Self-contained test for patch 37 on an EMPTY local PostgreSQL (isolated stand-in data, no real data):
--   psql -q -f sql/test_patch37.sql  -> "PATCH37 n/n"
-- Stand-in tables carry the LIVE column shapes read on 17 Oct; the live functions are installed from rollback_patch37.sql first
-- (so the «before» gaps are shown), then patch 37, then rollback and patch again (both must be repeatable).
-- Concurrency (two sessions) is in tools/patch37_race.py.
\set QUIET on
\set ON_ERROR_STOP on
\pset tuples_only on
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
  created_at timestamptz default now());
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

-- ================= BEFORE: the live functions (from the rollback file) =================
\i sql/rollback_patch37.sql
-- #1 cancelled order like 9104: 275 total, 124.38 wallet (spent, then returned automatically), cash not collected
insert into orders(customer_id, status, payment, total, wallet_used) values (:C, 'pending', 'cash', 275, 124.38);
insert into wallet_entries(user_id, amount, kind, order_id) values (:C, -124.38, 'spend', 1);
update orders set status = 'cancelled' where id = 1;
insert into support_tickets(customer_id, order_id) values (:C, 1);
select pg_temp.chk('before: live ticket_refund_room offers the whole total (275) on a cancelled, uncollected order',
  pg_temp.val(:SUP, 'select room::text from ticket_refund_room(1)') = '275', pg_temp.val(:SUP, 'select row(r.*)::text from ticket_refund_room(1) r'));
select pg_temp.chk('before: live allows a 275 refund on it (wallet already returned, cash never collected)',
  pg_temp.as_user(:SUP, 'select ticket_set_status(1, ''resolved'', ''x'', 275)') = 'ok', null);
delete from wallet_entries where ticket_id = 1;   -- not possible through the app (ledger is insert-only); stand-in reset only
-- (the immutable trigger guards UPDATE only, as live)
update support_tickets set status = 'open', refund_amount = null where id = 1;

-- ================= PATCH =================
\i sql/schema_patch37.sql
select pg_temp.chk('patch applies; new objects present', to_regprocedure('receive_driver_cash(uuid,numeric,text,text,text)') is not null
  and to_regclass('public.cash_settlements') is not null and to_regprocedure('order_refund_cap(bigint)') is not null, null);

-- ---------- refunds ----------
select pg_temp.chk('cap #1 (cancelled, wallet returned, cash not collected): proven paid 0 → room 0',
  (select room = 0 and paid_wallet = 0 and paid_cash = 0 and unproven = 150.62 from order_refund_cap(1)), (select row(c.*)::text from order_refund_cap(1) c));
select pg_temp.chk('ticket_refund_room shows the same cap with its breakdown (support)',
  pg_temp.val(:SUP, 'select (room = 0 and order_total = 275 and unproven = 150.62)::text from ticket_refund_room(1)') = 'true', pg_temp.val(:SUP, 'select row(r.*)::text from ticket_refund_room(1) r'));
select pg_temp.chk('refund on #1 refused: refund_too_high', pg_temp.as_user(:SUP, 'select ticket_set_status(1, ''resolved'', ''x'', 10)') like '%refund_too_high%', null);
select pg_temp.chk('ticket_refund_room for a non-support user → nothing', pg_temp.val(:C, 'select count(*)::text from ticket_refund_room(1)') = '0', null);
-- #2 delivered cash order: 200 total, 50 from wallet, 150 cash recorded
insert into orders(customer_id, driver_id, status, payment, total, wallet_used, cash_collected) values (:C, :D, 'delivered', 'cash', 200, 50, 150);
insert into wallet_entries(user_id, amount, kind, order_id) values (:C, -50, 'spend', 2);
insert into support_tickets(customer_id, order_id) values (:C, 2);
select pg_temp.chk('cap #2 (delivered, wallet 50 + recorded cash 150) = 200', (select room = 200 and paid_wallet = 50 and paid_cash = 150 from order_refund_cap(2)), (select row(c.*)::text from order_refund_cap(2) c));
select pg_temp.chk('refund 120 on ticket A of #2 → ok', pg_temp.as_user(:SUP, 'select ticket_set_status(2, ''resolved'', ''part'', 120)') = 'ok', null);
select pg_temp.chk('same ticket again → already_refunded (one refund per ticket kept)', pg_temp.as_user(:SUP, 'select ticket_set_status(2, ''resolved'', ''again'', 10)') like '%already_refunded%', null);
insert into support_tickets(customer_id, order_id) values (:C, 2);
select pg_temp.chk('ticket B of #2: 90 > room 80 → refund_too_high', pg_temp.as_user(:SUP, 'select ticket_set_status(3, ''resolved'', ''x'', 90)') like '%refund_too_high%', null);
select pg_temp.chk('ticket B of #2: 80 = room → ok', pg_temp.as_user(:SUP, 'select ticket_set_status(3, ''resolved'', ''x'', 80)') = 'ok', null);
select pg_temp.chk('… room on #2 is now 0 (refunds 120 + 80 = proven paid 200)', (select room = 0 and refunded = 200 from order_refund_cap(2)), null);
-- #3 delivered cash order where the courier recorded MORE than the cash part (220 for 200): only the cash part counts
insert into orders(customer_id, driver_id, status, payment, total, cash_collected) values (:C, :D, 'delivered', 'cash', 200, 220);
select pg_temp.chk('cap #3: recorded cash above the cash part counts as the cash part only (200)', (select room = 200 from order_refund_cap(3)), null);
-- #4 delivered card order: no capture record → unproven, room 0
insert into orders(customer_id, driver_id, status, payment, total) values (:C, :D, 'delivered', 'card', 120);
select pg_temp.chk('cap #4 (card, no capture data): room 0, unproven 120', (select room = 0 and unproven = 120 from order_refund_cap(4)), null);
-- #5 delivered cash order, cash NOT recorded: not counted
insert into orders(customer_id, driver_id, status, payment, total) values (:C, :D, 'delivered', 'cash', 80);
select pg_temp.chk('cap #5 (cash not recorded): room 0', (select room = 0 and unproven = 80 from order_refund_cap(5)), null);
-- #6 delivered order paid fully from the wallet (never returned): wallet counts
insert into orders(customer_id, driver_id, status, payment, total, wallet_used) values (:C, :D, 'delivered', 'wallet', 60, 60);
insert into wallet_entries(user_id, amount, kind, order_id) values (:C, -60, 'spend', 6);
select pg_temp.chk('cap #6 (wallet 60 spent, not returned): room 60', (select room = 60 from order_refund_cap(6)), null);
select pg_temp.chk('non-refund decisions still work (rejected with a note)', pg_temp.as_user(:SUP, 'select ticket_set_status(1, ''rejected'', ''no payment'')') = 'ok', null);
select pg_temp.chk('refund without support permission → not_allowed', pg_temp.as_user(:C, 'select ticket_set_status(1, ''resolved'', ''x'', 1)') like '%not_allowed%', null);

-- ---------- proof photo ----------
insert into orders(customer_id, driver_id, status, payment, total, leave_at_door) values (:C, :D, 'pickedup', 'card', 50, true);   -- #7
select pg_temp.chk('photo path well formed but no file → photo_missing',
  pg_temp.as_user(:D, 'select deliver_order(7, null, null, ''d0000000-0000-0000-0000-00000000000d/7/abcdefgh12.jpg'')') like '%photo_missing%', null);
insert into storage.objects(bucket_id, name, owner, owner_id, metadata) values ('proofs', 'd0000000-0000-0000-0000-00000000000d/7/abcdefgh12.jpg', null, 'd0000000-0000-0000-0000-0000000000d2', '{"size":1000,"mimetype":"image/jpeg"}');
select pg_temp.chk('file uploaded by ANOTHER user at that path → photo_missing',
  pg_temp.as_user(:D, 'select deliver_order(7, null, null, ''d0000000-0000-0000-0000-00000000000d/7/abcdefgh12.jpg'')') like '%photo_missing%', null);
insert into storage.objects(bucket_id, name, owner_id, metadata) values ('proofs', 'd0000000-0000-0000-0000-00000000000d/7/zzzzzzzz12.jpg', 'd0000000-0000-0000-0000-00000000000d', null);
select pg_temp.chk('unfinished upload (no size) → photo_missing',
  pg_temp.as_user(:D, 'select deliver_order(7, null, null, ''d0000000-0000-0000-0000-00000000000d/7/zzzzzzzz12.jpg'')') like '%photo_missing%', null);
insert into storage.objects(bucket_id, name, owner_id, metadata, archived_at) values ('proofs', 'd0000000-0000-0000-0000-00000000000d/7/oldoldol12.jpg', 'd0000000-0000-0000-0000-00000000000d', '{"size":900,"mimetype":"image/jpeg"}', now());
select pg_temp.chk('archived (not current) file → photo_missing',
  pg_temp.as_user(:D, 'select deliver_order(7, null, null, ''d0000000-0000-0000-0000-00000000000d/7/oldoldol12.jpg'')') like '%photo_missing%', null);
insert into storage.objects(bucket_id, name, owner_id, metadata) values ('media', 'd0000000-0000-0000-0000-00000000000d/7/medmedme12.jpg', 'd0000000-0000-0000-0000-00000000000d', '{"size":900,"mimetype":"image/jpeg"}');
select pg_temp.chk('same path in another bucket → photo_missing',
  pg_temp.as_user(:D, 'select deliver_order(7, null, null, ''d0000000-0000-0000-0000-00000000000d/7/medmedme12.jpg'')') like '%photo_missing%', null);
select pg_temp.chk('path of another order → bad_value (format rule unchanged)',
  pg_temp.as_user(:D, 'select deliver_order(7, null, null, ''d0000000-0000-0000-0000-00000000000d/8/abcdefgh12.jpg'')') like '%bad_value%', null);
select pg_temp.chk('leave at the door without photo → photo_required (unchanged)', pg_temp.as_user(:D, 'select deliver_order(7)') like '%photo_required%', null);
insert into storage.objects(bucket_id, name, owner_id, metadata) values ('proofs', 'd0000000-0000-0000-0000-00000000000d/7/goodgood12.jpg', 'd0000000-0000-0000-0000-00000000000d', '{"size":5000,"mimetype":"image/jpeg"}');
select pg_temp.chk('another courier cannot deliver (unchanged) even with a real file',
  pg_temp.as_user(:D2, 'select deliver_order(7, null, null, ''d0000000-0000-0000-0000-00000000000d/7/goodgood12.jpg'')') like '%bad_transition%', null);
select pg_temp.chk('real current file by this courier → delivered',
  pg_temp.as_user(:D, 'select deliver_order(7, null, null, ''d0000000-0000-0000-0000-00000000000d/7/goodgood12.jpg'')') = 'ok', null);
select pg_temp.chk('… the order keeps that photo', (select status = 'delivered' and delivery_photo like '%goodgood12.jpg' from orders where id = 7), null);
insert into orders(customer_id, driver_id, status, payment, total) values (:C, :D, 'pickedup', 'cash', 40);   -- #8 no photo needed
select pg_temp.chk('no photo needed and none given → delivered (unchanged)', pg_temp.as_user(:D, 'select deliver_order(8, 40)') = 'ok', null);
select pg_temp.chk('proof_exists is not callable by app users', pg_temp.as_user(:D, 'set local role authenticated; select proof_exists(''x'', auth.uid())') like '%permission denied%', null);

-- ---------- cash ----------
-- courier D: delivered cash recorded: #2 150, #3 220, #8 40 = 410
select pg_temp.chk('owed by D = 410 (recorded cash)', driver_cash_due(:D) = 410, driver_cash_due(:D)::text);
select pg_temp.chk('receive 25.5 (any positive amount, far below the 1000 limit) → ok',
  pg_temp.val(:F, 'select (amount = 25.5 and due_before = 410 and remaining_after = 384.5)::text from receive_driver_cash(''d0000000-0000-0000-0000-00000000000d'', 25.5, ''REC-1'', ''smena'', ''key-aaaa-0001'')') = 'true', null);
select pg_temp.chk('record keeps amount, receiver, time, reference, remaining',
  (select amount = 25.5 and received_by = :F and received_at is not null and reference = 'REC-1' and remaining_after = 384.5 from cash_settlements where client_key = 'key-aaaa-0001'), null);
select pg_temp.chk('the same form sent twice (same key) → the first receipt, no second record',
  pg_temp.as_user(:F, 'select * from receive_driver_cash(''d0000000-0000-0000-0000-00000000000d'', 25.5, ''REC-1'', ''smena'', ''key-aaaa-0001'')') = 'ok'
  and (select count(*) = 1 from cash_settlements), null);
select pg_temp.chk('the same key with another amount → bad_value', pg_temp.as_user(:F, 'select * from receive_driver_cash(''d0000000-0000-0000-0000-00000000000d'', 30, null, null, ''key-aaaa-0001'')') like '%bad_value%', null);
select pg_temp.chk('more than owed → amount_too_high', pg_temp.as_user(:F, 'select * from receive_driver_cash(''d0000000-0000-0000-0000-00000000000d'', 384.51)') like '%amount_too_high%', null);
select pg_temp.chk('zero / negative → bad_value', pg_temp.as_user(:F, 'select * from receive_driver_cash(''d0000000-0000-0000-0000-00000000000d'', 0)') like '%bad_value%'
  and pg_temp.as_user(:F, 'select * from receive_driver_cash(''d0000000-0000-0000-0000-00000000000d'', -5)') like '%bad_value%', null);
select pg_temp.chk('without finance permission → not_allowed', pg_temp.as_user(:SUP, 'select * from receive_driver_cash(''d0000000-0000-0000-0000-00000000000d'', 5)') like '%not_allowed%', null);
select pg_temp.chk('a customer id → not_found', pg_temp.as_user(:F, 'select * from receive_driver_cash(''c0000000-0000-0000-0000-00000000000c'', 5)') like '%not_found%', null);
select pg_temp.chk('cash_balances (finance) = 384.5 for D', pg_temp.val(:F, 'select balance::text from cash_balances() where driver_id = ''d0000000-0000-0000-0000-00000000000d''') = '384.50', pg_temp.val(:F, 'select string_agg(row(c.*)::text, '';'') from cash_balances() c'));
select pg_temp.chk('the courier sees only his own balance', pg_temp.val(:D2, 'select count(*)::text from cash_balances()') = '0', null);
select pg_temp.chk('old «receive all» (settle_driver_cash) records ONE receipt of the rest: 384.5',
  pg_temp.val(:F, 'select settle_driver_cash(''d0000000-0000-0000-0000-00000000000d'')::text') in ('384.50', '384.5'), null);
select pg_temp.chk('… D now owes 0, two receipts in total', driver_cash_due(:D) = 0 and (select count(*) = 2 from cash_settlements), null);
select pg_temp.chk('nothing owed → nothing_due', pg_temp.as_user(:F, 'select * from receive_driver_cash(''d0000000-0000-0000-0000-00000000000d'', 1)') like '%nothing_due%', null);
select pg_temp.chk('receipts cannot be changed or deleted', pg_temp.as_user(:A, 'update cash_settlements set amount = 1') like '%ledger_immutable%'
  and pg_temp.as_user(:A, 'delete from cash_settlements') like '%ledger_immutable%', null);
select pg_temp.chk('orders are no longer marked by settlement (no allocation chosen)', (select count(*) = 0 from orders where cash_settled_at is not null), null);
select pg_temp.chk('the cash limit / blocking columns are untouched', (select bool_and(not accept_blocked and cash_limit = 1000) from profiles where role = 'driver'), null);
select pg_temp.chk('app users cannot insert receipts directly', pg_temp.as_user(:F, 'set local role authenticated; insert into cash_settlements(driver_id, amount, due_before, remaining_after, received_by) values (''d0000000-0000-0000-0000-00000000000d'', 1, 1, 0, auth.uid())') like '%permission denied%', null);

-- #9 an order still in progress with wallet money: no refund until it ends
insert into orders(customer_id, status, payment, total, wallet_used) values (:C, 'preparing', 'cash', 90, 30);
insert into wallet_entries(user_id, amount, kind, order_id) values (:C, -30, 'spend', currval('orders_id_seq'));
insert into support_tickets(customer_id, order_id) select :C, currval('orders_id_seq');
select pg_temp.chk('order in progress: room 0, refund → order_not_finished', (select room = 0 from order_refund_cap(currval('orders_id_seq')))
  and pg_temp.as_user(:SUP, format('select ticket_set_status(%s, ''resolved'', ''x'', 10)', currval('support_tickets_id_seq'))) like '%order_not_finished%', null);
update orders set status = 'cancelled' where id = currval('orders_id_seq');
select pg_temp.chk('… after the cancel its wallet part came back automatically → room still 0', (select room = 0 and paid_wallet = 0 from order_refund_cap(currval('orders_id_seq'))), null);
-- ---------- rollback, then patch again ----------
\i sql/rollback_patch37.sql
select pg_temp.chk('rollback restores the live functions (old room on #1 = 275 again) and keeps the receipts',
  pg_temp.val(:SUP, 'select room::text from ticket_refund_room(1)') = '275'
  and to_regprocedure('receive_driver_cash(uuid,numeric,text,text,text)') is null and (select count(*) = 2 from cash_settlements), null);
\i sql/schema_patch37.sql
\i sql/schema_patch37.sql
select pg_temp.chk('patch is repeatable (applied twice after the rollback); D owes 0, receipts kept', driver_cash_due(:D) = 0 and (select count(*) = 2 from cash_settlements), null);

\pset tuples_only off
select n, case when ok then 'PASS' else 'FAIL' end as r, label, left(coalesce(got, ''), 90) as got from res order by n;
select 'PATCH37 ' || count(*) filter (where ok) || '/' || count(*) from res;
