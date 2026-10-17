-- Stand-in for patch 38 tests on an EMPTY local PostgreSQL (isolated data; NOT for any real database). Builds on test_patch34
-- (patches 28 → 34 = the repository / live place_order chain), completes the live shapes, installs the live functions from the
-- rollback files, then patches 37 and 38. Used by sql/test_patch38.sql and tools/patch38_race.py.
\i sql/test_patch34.sql
\set QUIET on
\set ON_ERROR_STOP on
\pset tuples_only on
-- ---------- completing the stand-in ----------
alter table storage.objects add column if not exists owner uuid, add column if not exists owner_id text, add column if not exists metadata jsonb,
  add column if not exists archived_at timestamptz, add column if not exists is_delete_marker boolean default false;
create table if not exists staff_members (user_id uuid, active boolean, perms text[]);
create or replace function has_perm(p text) returns boolean language sql stable security definer set search_path = public as $$
  select auth.uid() is not null and (exists(select 1 from profiles where id = auth.uid() and role = 'admin')
    or exists(select 1 from staff_members s where s.user_id = auth.uid() and s.active and p = any(s.perms))) $$;
create table if not exists support_tickets (id bigint generated always as identity primary key, customer_id uuid, order_id bigint, reason text default 'other',
  status text default 'open', admin_note text, refund_amount numeric, handled_by uuid, closed_at timestamptz, created_at timestamptz default now(),
  updated_at timestamptz default now(), last_staff_at timestamptz, last_customer_at timestamptz default now(), customer_seen_at timestamptz);
create table if not exists audit_log (id bigint generated always as identity, user_id uuid, action text, table_name text, row_id text, details jsonb default '{}'::jsonb, at timestamptz default now());
create or replace function audit_changes() returns trigger language plpgsql security definer set search_path = public as $$
declare v_n jsonb; v_o jsonb; v_d jsonb := '{}'::jsonb; v_k text; v_id text;
begin
  if tg_op = 'INSERT' then v_n := to_jsonb(new); v_id := v_n->>coalesce(tg_argv[0], 'id');
    insert into audit_log(user_id, action, table_name, row_id, details) values (auth.uid(), 'INSERT', tg_table_name, v_id, '{}'::jsonb); return new;
  elsif tg_op = 'DELETE' then v_o := to_jsonb(old); v_id := v_o->>coalesce(tg_argv[0], 'id');
    insert into audit_log(user_id, action, table_name, row_id, details) values (auth.uid(), 'DELETE', tg_table_name, v_id, '{}'::jsonb); return old;
  end if;
  v_n := to_jsonb(new); v_o := to_jsonb(old); v_id := v_n->>coalesce(tg_argv[0], 'id');
  foreach v_k in array tg_argv[1:] loop
    if (v_n->v_k) is distinct from (v_o->v_k) then v_d := v_d || jsonb_build_object(v_k, jsonb_build_object('from', v_o->v_k, 'to', v_n->v_k)); end if;
  end loop;
  if v_d <> '{}'::jsonb then insert into audit_log(user_id, action, table_name, row_id, details) values (auth.uid(), 'UPDATE', tg_table_name, v_id, v_d); end if;
  return new;
end $$;
alter table orders add column if not exists cash_settled_at timestamptz;
-- people: finance F, stores staff T, merchant M (owner of Kebab), courier D (exists), D2 (exists)
insert into profiles(id, role, name, phone) values ('f0000000-0000-0000-0000-00000000000f', 'customer', 'Finance Farhod', '+992900000020'),
  ('70000000-0000-0000-0000-000000000007', 'customer', 'Stores Tahmina', '+992900000021'), ('e0000000-0000-0000-0000-00000000000e', 'merchant', 'Owner Muso', '+992900000022');
insert into staff_members values ('f0000000-0000-0000-0000-00000000000f', true, array['finance']), ('70000000-0000-0000-0000-000000000007', true, array['stores']);
update stores set owner_id = 'e0000000-0000-0000-0000-00000000000e' where name = 'Kebab';
-- v61: the owner's worked example (17 Oct) — delivery 20 (the courier's pay 20); test_patch34 above ran with its own 10
create or replace function delivery_calc(p_store uuid, p_lat float8, p_lng float8, p_user uuid) returns jsonb language sql as $$ select '{"fee":20,"fee_full":20,"base":20,"extra":0,"km":2}'::jsonb $$;
-- live functions first (from the rollback files), then the patches
\i sql/rollback_patch37.sql
-- v61: the live automatic wallet return on cancel / reject (trigger read 17 Oct; its function comes from the rollback file above)
drop trigger if exists trg_orders_wallet_return on orders;
create trigger trg_orders_wallet_return before update of status on orders for each row execute function trg_wallet_return();
\i sql/rollback_patch38.sql
\i sql/schema_patch37.sql
\i sql/schema_patch38.sql

-- ---------- helpers ----------
create table r38 (n serial, ok boolean, label text, got text);
create function c38(label text, cond boolean, got text default '') returns void language sql as $$ insert into r38(ok, label, got) values (coalesce(cond, false), label, coalesce(got, '')) $$;
-- run as a user (security definer functions see auth.uid()); returns 'ok' or 'ERR:<message>'
create function u38(uid text, q text) returns text language plpgsql as $f$
begin perform set_config('request.jwt.claim.sub', uid, true); execute q; perform set_config('request.jwt.claim.sub', '', true); return 'ok';
exception when others then perform set_config('request.jwt.claim.sub', '', true); return 'ERR:' || sqlerrm; end $f$;
create function v38(uid text, q text) returns text language plpgsql as $f$
declare r text; begin perform set_config('request.jwt.claim.sub', uid, true); execute q into r; perform set_config('request.jwt.claim.sub', '', true); return r;
exception when others then perform set_config('request.jwt.claim.sub', '', true); return 'ERR:' || sqlerrm; end $f$;
-- place an order as the customer: store name, plov count, payment, wallet, points
-- each call uses a fresh stand-in customer (the live abuse guards allow 5 open orders per customer), with 500 in the wallet
create sequence cseq38;
create function po38(store text, n int, pay text, wallet numeric default null, points int default null) returns text language plpgsql as $f$
declare r text; s uuid := (select id from stores where name = store); it uuid := (select id from menu_items where store_id = s order by price desc limit 1);
        cu uuid := ('c1000000-0000-0000-0000-' || lpad(nextval('cseq38')::text, 12, '0'))::uuid;
begin
  insert into profiles(id, role, name, phone) values (cu, 'customer', 'Test customer', '+99290' || lpad(currval('cseq38')::text, 7, '0'));
  insert into wallet_entries(user_id, amount, kind) values (cu, 500, 'adjust');
  perform set_config('request.jwt.claim.sub', cu::text, true);
  begin r := place_order(s, jsonb_build_array(jsonb_build_object('item_id', it, 'qty', n)), 0, pay, 'Rudaki 1', 38.5, 68.7, null, null, 20, wallet, points, null)::text;
  exception when others then r := 'ERR:' || sqlerrm; end;
  perform set_config('request.jwt.claim.sub', '', true); return r;
end $f$;
\set F '''f0000000-0000-0000-0000-00000000000f'''
\set T '''70000000-0000-0000-0000-000000000007'''
\set M '''e0000000-0000-0000-0000-00000000000e'''
\set DR '''d0000000-0000-0000-0000-00000000000d'''
\set CU '''c0000000-0000-0000-0000-000000000001'''
\set KEBAB '''50000000-0000-0000-0000-000000000001'''
\set PIZZA '''50000000-0000-0000-0000-000000000002'''

