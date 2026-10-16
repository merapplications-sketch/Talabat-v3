-- Patch 36 against the LIVE structure (read on 17 Oct from sql/verify_patch36_single.sql; definitions copied from that result).
-- Local PostgreSQL only:  psql -q -f sql/test_patch36_prodshape.sql   -> "PATCH36-PROD n/n"
-- Rebuilds: store_requests exactly as live (columns, constraint names, indexes, policy, realtime), banners with its 6 constraints
-- and audit / image triggers, profiles guard + audit, stores audit, audit_changes / guard_profile / assign_owner as live,
-- 2 approved branch requests. Then: apply → lead flow → assign_owner separately → rollback → apply again.
\set QUIET on
\set ON_ERROR_STOP on
\pset tuples_only on
drop publication if exists supabase_realtime;
drop schema if exists auth cascade; drop schema public cascade; create schema public; grant usage on schema public to public;
do $$ begin create role authenticated; exception when duplicate_object then null; end $$;
do $$ begin create role anon; exception when duplicate_object then null; end $$;
do $$ begin create role service_role bypassrls; exception when duplicate_object then null; end $$;
grant usage on schema public to anon, authenticated, service_role;
alter default privileges in schema public grant all on tables to anon, authenticated, service_role;
create schema auth; grant usage on schema auth to authenticated, anon, service_role;
create function auth.uid() returns uuid language sql stable as $$ select nullif(current_setting('request.jwt.claim.sub', true), '')::uuid $$;
grant execute on function auth.uid() to authenticated, anon, service_role;
create table auth.users (id uuid primary key, email text);
-- ---------- live helpers (definitions as read) ----------
create function norm_phone(p text) returns text language sql immutable as $$
  select case when d ~ '^992[0-9]{9}$' then '+' || d when d ~ '^[0-9]{9}$' then '+992' || d when d ~ '^0[0-9]{9}$' then '+992' || substr(d, 2) else null end
  from (select regexp_replace(coalesce(p, ''), '[^0-9]', '', 'g') as d) x $$;
create table profiles (id uuid primary key, role text, name text, phone text, driver_status text, cash_limit numeric default 0,
  accept_blocked boolean default false, banned_at timestamptz, banned_reason text, phone_changed_at timestamptz);
create table staff_members (user_id uuid, perms text[], active boolean);
create function is_admin() returns boolean language sql stable security definer set search_path to 'public'
  as $function$ select exists(select 1 from profiles where id = auth.uid() and role = 'admin') $function$;
create function has_perm(p text) returns boolean language sql stable security definer set search_path to 'public' as $function$
  select auth.uid() is not null and (
    exists(select 1 from profiles where id = auth.uid() and role = 'admin')
    or exists(select 1 from staff_members s where s.user_id = auth.uid() and s.active and p = any(s.perms)))
$function$;
create table audit_log (id bigserial primary key, at timestamptz default now(), user_id uuid, action text, table_name text, row_id text, details jsonb);
create function audit_changes() returns trigger language plpgsql security definer set search_path to 'public' as $function$
declare v_n jsonb; v_o jsonb; v_d jsonb := '{}'::jsonb; v_k text; v_id text;
begin
  if tg_op = 'INSERT' then v_n := to_jsonb(new); v_id := v_n->>coalesce(tg_argv[0], 'id');
    insert into audit_log(user_id, action, table_name, row_id, details) values (auth.uid(), 'INSERT', tg_table_name, v_id, '{}'::jsonb);
    return new;
  elsif tg_op = 'DELETE' then v_o := to_jsonb(old); v_id := v_o->>coalesce(tg_argv[0], 'id');
    insert into audit_log(user_id, action, table_name, row_id, details) values (auth.uid(), 'DELETE', tg_table_name, v_id, '{}'::jsonb);
    return old;
  end if;
  v_n := to_jsonb(new); v_o := to_jsonb(old); v_id := v_n->>coalesce(tg_argv[0], 'id');
  foreach v_k in array tg_argv[1:] loop
    if (v_n->v_k) is distinct from (v_o->v_k) then v_d := v_d || jsonb_build_object(v_k, jsonb_build_object('from', v_o->v_k, 'to', v_n->v_k)); end if;
  end loop;
  if v_d <> '{}'::jsonb then
    insert into audit_log(user_id, action, table_name, row_id, details) values (auth.uid(), 'UPDATE', tg_table_name, v_id, v_d);
  end if;
  return new;
end $function$;
create function guard_profile() returns trigger language plpgsql security definer set search_path to 'public' as $function$
begin
  if auth.uid() is null or current_setting('app.bypass', true) = '1' or is_admin() then return new; end if;
  if new.role <> old.role or new.driver_status is distinct from old.driver_status
     or new.cash_limit <> old.cash_limit or new.accept_blocked <> old.accept_blocked
     or new.banned_at is distinct from old.banned_at or new.banned_reason is distinct from old.banned_reason
     or new.phone_changed_at is distinct from old.phone_changed_at then
    raise exception 'not_allowed';
  end if;
  return new;
end $function$;
create trigger trg_guard_profile before update on profiles for each row execute function guard_profile();
create trigger trg_audit_profiles after update on profiles for each row execute function audit_changes('id', 'role', 'driver_status', 'cash_limit', 'accept_blocked', 'banned_at', 'banned_reason', 'phone');
create table stores (id uuid primary key default gen_random_uuid(), name text, category text, phone text, address text, lat float8, lng float8,
  owner_id uuid, commission_pct numeric, max_discount_pct numeric default 30, discount_pct numeric default 0, is_active boolean, is_open boolean,
  fee_type text, fee_base numeric, fee_per_km numeric, free_first_delivery boolean);
create trigger trg_audit_stores after insert or delete or update on stores for each row execute function audit_changes('id', 'name', 'owner_id', 'commission_pct', 'max_discount_pct', 'discount_pct', 'is_active', 'is_open', 'fee_type', 'fee_base', 'fee_per_km', 'free_first_delivery');
create function assign_owner(p_store uuid, p_email text) returns void language plpgsql security definer set search_path to 'public' as $function$
declare u uuid;
begin
  if not is_admin() then raise exception 'not_allowed'; end if;
  select id into u from auth.users where lower(email) = lower(p_email);
  if u is null then raise exception 'user_not_found'; end if;
  perform set_config('app.bypass', '1', true);
  update profiles set role = 'merchant' where id = u and role = 'customer';
  update stores set owner_id = u where id = p_store;
end $function$;
revoke all on function assign_owner(uuid, text) from public, anon; grant execute on function assign_owner(uuid, text) to authenticated, service_role;
-- banners: the 6 live constraints + 2 triggers (image check stubbed)
create table banners (id uuid primary key default gen_random_uuid(), title text, image_url text, placement text default 'top', link_type text, link_value text,
  sort int, is_active boolean default true, starts_at timestamptz, ends_at timestamptz);
create function trg_check_images() returns trigger language plpgsql as $$ begin return new; end $$;
create trigger trg_audit_banners after insert or delete or update on banners for each row execute function audit_changes('id', 'title', 'is_active', 'placement', 'starts_at', 'ends_at', 'link_type', 'link_value');
create trigger trg_images_banners before insert or update on banners for each row execute function trg_check_images();
insert into banners(title, link_type, link_value, placement) values ('n1','none',null,'top'),('n2','none',null,'top'),('n3','none',null,'bottom'),
  ('s1','store','x','top'),('s2','store','y','top'),('s3','store','z','bottom'),('c1','category','rest','top'),('c2','category','sweets','top'),('c3','category','gifts','bottom');
alter table banners add constraint banners_dates_chk check ((starts_at is null) or (ends_at is null) or (ends_at > starts_at));
alter table banners add constraint banners_image_len check ((image_url is null) or (char_length(image_url) <= 900000)) not valid;
alter table banners add constraint banners_link_type_check check (link_type = any (array['none'::text, 'store'::text, 'category'::text]));
alter table banners add constraint banners_placement_chk check (placement = any (array['top'::text, 'bottom'::text]));
alter table banners add constraint banners_text_len check ((char_length(title) <= 80) and ((link_value is null) or (char_length(link_value) <= 80))) not valid;
-- store_requests exactly as live (patch 19 + 26)
create table store_requests (
  id uuid primary key default gen_random_uuid(),
  user_id uuid not null references profiles(id) on delete cascade,
  name text not null check (char_length(btrim(name)) between 2 and 80),
  category text not null check (category in ('rest','grocery','pharmacy','beauty','flowers','gifts','shops','sweets')),
  phone text not null check (phone ~ '^\+992[0-9]{9}$'),
  address text check (address is null or char_length(address) <= 200),
  lat float8 not null check (lat between -90 and 90),
  lng float8 not null check (lng between -180 and 180),
  note text check (note is null or char_length(note) <= 500),
  status text not null default 'pending' check (status in ('pending', 'approved', 'rejected')),
  admin_note text check (admin_note is null or char_length(admin_note) <= 300),
  store_id uuid references stores(id) on delete set null,
  created_at timestamptz not null default now(),
  decided_at timestamptz,
  decided_by uuid references profiles(id));
create index store_req_user_idx on store_requests (user_id, created_at desc);
create index store_req_status_idx on store_requests (status, created_at);
alter table store_requests enable row level security;
create policy store_req_read on store_requests for select to public using ((user_id = auth.uid()) or has_perm('stores'::text));
create publication supabase_realtime for table store_requests;
-- people, stores, the 2 approved branch requests
insert into profiles(id, role) values ('a0000000-0000-0000-0000-00000000000a','admin'),('50000000-0000-0000-0000-000000000005','customer'),
  ('e0000000-0000-0000-0000-00000000000e','merchant'),('c0000000-0000-0000-0000-000000000001','customer');
insert into auth.users values ('c0000000-0000-0000-0000-000000000001','owner@example.com');
insert into staff_members values ('50000000-0000-0000-0000-000000000005','{stores}',true);
insert into stores(id, name, owner_id) values ('b0000000-0000-0000-0000-000000000001','Branch A','e0000000-0000-0000-0000-00000000000e'),
  ('b0000000-0000-0000-0000-000000000002','Branch B','e0000000-0000-0000-0000-00000000000e'),('b0000000-0000-0000-0000-000000000003','New store',null);
insert into store_requests(id, user_id, name, category, phone, lat, lng, status, store_id, decided_at, decided_by) values
  ('d0000000-0000-0000-0000-000000000001','e0000000-0000-0000-0000-00000000000e','Branch A','rest','+992900000001',38.5,68.7,'approved','b0000000-0000-0000-0000-000000000001',now()-interval '9 days','a0000000-0000-0000-0000-00000000000a'),
  ('d0000000-0000-0000-0000-000000000002','e0000000-0000-0000-0000-00000000000e','Branch B','sweets','+992900000002',38.6,68.8,'approved','b0000000-0000-0000-0000-000000000002',now()-interval '3 days','a0000000-0000-0000-0000-00000000000a');
truncate audit_log;

-- ---------- helpers ----------
create table res(n serial, ok boolean, label text, got text);
create function chk(l text, c boolean, g text default '') returns void language sql as $$ insert into res(ok, label, got) values (coalesce(c, false), l, g) $$;
create function q(rl text, uid text, sqlt text) returns text language plpgsql as $f$
declare r text;
begin perform set_config('request.jwt.claim.sub', coalesce(uid, ''), true); execute 'set local role ' || rl;
  begin execute sqlt into r; exception when others then r := 'ERR:' || sqlerrm; end;
  reset role; perform set_config('request.jwt.claim.sub', '', true); return coalesce(r, ''); end $f$;
-- the two branch requests: the original 15 columns only
create function branch_rows() returns text language sql as $$
  select string_agg(concat_ws('|', id, user_id, name, category, phone, address, lat, lng, note, status, admin_note, store_id, created_at, decided_at, decided_by), E'\n' order by id)
    from store_requests where id::text like 'd0000000%' $$;
-- the live catalog shape of store_requests + banners (what the rollback must restore)
create function shape() returns text language sql as $$
  select concat_ws(E'\n',
   (select string_agg(a.attname || ' ' || format_type(a.atttypid, a.atttypmod) || case when a.attnotnull then ' NN' else '' end || coalesce(' d=' || pg_get_expr(d.adbin, d.adrelid), ''), ',' order by a.attnum)
      from pg_attribute a left join pg_attrdef d on d.adrelid = a.attrelid and d.adnum = a.attnum where a.attrelid = 'store_requests'::regclass and a.attnum > 0 and not a.attisdropped),
   (select string_agg(conname || '=' || pg_get_constraintdef(oid), ',' order by conname) from pg_constraint where conrelid = 'store_requests'::regclass),
   (select string_agg(pg_get_indexdef(indexrelid), ',' order by indexrelid::regclass::text) from pg_index where indrelid = 'store_requests'::regclass),
   (select string_agg(polname || ' ' || polcmd::text || ' ' || pg_get_expr(polqual, polrelid), ',') from pg_policy where polrelid = 'store_requests'::regclass),
   (select string_agg(tgname, ',' order by tgname) from pg_trigger where tgrelid = 'store_requests'::regclass and not tgisinternal),
   (select string_agg(tablename, ',') from pg_publication_tables where pubname = 'supabase_realtime'),
   (select string_agg(conname || '=' || pg_get_constraintdef(oid) || case when convalidated then '' else ' NV' end, ',' order by conname) from pg_constraint where conrelid = 'banners'::regclass),
   (select string_agg(tgname, ',' order by tgname) from pg_trigger where tgrelid = 'banners'::regclass and not tgisinternal)) $$;
select branch_rows() as b0 \gset
select shape() as s0 \gset
\set A '''a0000000-0000-0000-0000-00000000000a'''
\set STO '''50000000-0000-0000-0000-000000000005'''
\set M '''e0000000-0000-0000-0000-00000000000e'''
\set C '''c0000000-0000-0000-0000-000000000001'''

-- ---------- 1. apply ----------
\i sql/schema_patch36.sql
select chk('apply: the 2 approved branch requests unchanged (all original columns)', branch_rows() = :'b0', branch_rows());
select chk('apply: branch requests got kind = branch', (select string_agg(kind, ',') from store_requests) = 'branch,branch');
select chk('apply: read policy unchanged', (select polname || ' ' || pg_get_expr(polqual, polrelid) from pg_policy where polrelid = 'store_requests'::regclass) = 'store_req_read ((user_id = auth.uid()) OR has_perm(''stores''::text))');
select chk('apply: still in realtime', exists (select 1 from pg_publication_tables where pubname = 'supabase_realtime' and tablename = 'store_requests'));
select chk('apply: old indexes kept', (select count(*) from pg_indexes where tablename = 'store_requests' and indexname in ('store_req_user_idx', 'store_req_status_idx')) = 2);
select chk('apply: banners_link_type_check same name, live values kept + partner',
  (select pg_get_constraintdef(oid) from pg_constraint where conname = 'banners_link_type_check') = 'CHECK ((link_type = ANY (ARRAY[''none''::text, ''store''::text, ''category''::text, ''partner''::text])))',
  (select pg_get_constraintdef(oid) from pg_constraint where conname = 'banners_link_type_check'));
select chk('apply: the other 5 banner constraints untouched (incl. the 2 NOT VALID)', (select count(*) from pg_constraint where conrelid = 'banners'::regclass) = 6
  and (select count(*) from pg_constraint where conrelid = 'banners'::regclass and not convalidated) = 2);
select chk('apply: lead audit trigger only for kind lead', (select pg_get_triggerdef(oid) from pg_trigger where tgname = 'trg_audit_store_leads') like '%WHEN ((old.kind = ''lead''::text))%');
select chk('apply: branch requests still readable by their owner, not by a customer',
  q('authenticated', :M, 'select count(*)::text from store_requests') = '2' and q('authenticated', :C, 'select count(*)::text from store_requests') = '0');
select chk('apply: a partner banner can be saved', q('service_role', null, $$insert into banners(title, link_type) values ('partner','partner') returning link_type$$) = 'partner');
-- ---------- 2. lead flow: link changes only the request; audited ----------
create function k(t text) returns text language sql immutable as $$ select md5(t) || md5(t || '#') $$;
select q('service_role', null, format('select lead_submit(%L,%L,%L,%L,%L)', 'Чайхана', 'rest', '901234567', k('+992901234567'), k('ip:1'))) as r \gset
select chk('lead submitted', :'r' = 'ok' and (select count(*) from store_requests where kind = 'lead') = 1);
select chk('submitting writes no store_requests audit row (Edge Function path)', (select count(*) from audit_log where table_name = 'store_requests') = 0, (select string_agg(table_name || ':' || action, ',') from audit_log));
truncate audit_log;
select id as lid from store_requests where kind = 'lead' \gset
select q('authenticated', :STO, format('select lead_set_status(%L, ''contacted'', ''called'')', :'lid')) as r \gset
select chk('stores staff: contacted', :'r' = '' and (select status from store_requests where id = :'lid') = 'contacted', :'r');
select chk('… audited: who, status new→contacted, note', (select count(*) from audit_log where table_name = 'store_requests' and row_id = :'lid' and user_id = :STO::uuid
  and details->'status'->>'from' = 'new' and details->'status'->>'to' = 'contacted' and details ? 'admin_note') = 1,
  (select string_agg(details::text, ' ') from audit_log));
create temp table st0 as select md5(string_agg(row_to_json(s)::text, '' order by id)) h from stores s;
create temp table pr0 as select md5(string_agg(row_to_json(p)::text, '' order by id)) h from profiles p;
update lead_settings set value = 1 where key = 'link_enabled';
truncate audit_log;
select q('authenticated', :A, format('select lead_link(%L, %L)', :'lid', 'b0000000-0000-0000-0000-000000000003')) as r \gset
select chk('admin links the lead to an existing store', :'r' = '' and (select status || '/' || store_id from store_requests where id = :'lid') = 'converted/b0000000-0000-0000-0000-000000000003', :'r');
select chk('… stores unchanged (no owner set by linking)', (select md5(string_agg(row_to_json(s)::text, '' order by id)) from stores s) = (select h from st0));
select chk('… profiles unchanged (no role change by linking)', (select md5(string_agg(row_to_json(p)::text, '' order by id)) from profiles p) = (select h from pr0));
select chk('… audited: one store_requests row (status contacted→converted, store_id), nothing on stores / profiles',
  (select count(*) from audit_log) = 1 and (select count(*) from audit_log where table_name = 'store_requests' and user_id = :A::uuid
   and details->'status'->>'to' = 'converted' and details->'store_id'->>'to' = 'b0000000-0000-0000-0000-000000000003') = 1,
  (select string_agg(table_name || ' ' || details::text, ' | ') from audit_log));
select chk('… branch requests still unchanged', branch_rows() = :'b0');
update lead_settings set value = 0 where key = 'link_enabled';
-- ---------- 3. owner assignment is a separate operation (live function, not changed) ----------
create temp table sr0 as select md5(string_agg(row_to_json(r)::text, '' order by id)) h from store_requests r;
truncate audit_log;
select q('authenticated', :A, $$select assign_owner('b0000000-0000-0000-0000-000000000003', 'OWNER@example.com')$$) as r \gset
select chk('assign_owner (separately): store owner set, customer became merchant', :'r' = ''
  and (select owner_id::text from stores where id = 'b0000000-0000-0000-0000-000000000003') = 'c0000000-0000-0000-0000-000000000001'
  and (select role from profiles where id = :C::uuid) = 'merchant', :'r');
select chk('… store_requests untouched by assign_owner', (select md5(string_agg(row_to_json(r)::text, '' order by id)) from store_requests r) = (select h from sr0));
select chk('… its own audit (live triggers): stores.owner_id + profiles.role, none on store_requests',
  (select string_agg(table_name, ',' order by table_name) from audit_log) = 'profiles,stores', (select string_agg(table_name || ' ' || details::text, ' | ') from audit_log));
select chk('a customer cannot call assign_owner (is_admin inside)', q('authenticated', :C, $$select assign_owner('b0000000-0000-0000-0000-000000000001', 'owner@example.com')$$) like 'ERR:not_allowed%');
-- ---------- 4. rollback: back to the live shape ----------
delete from banners where link_type = 'partner';
set patch36.drop_leads = 'yes';
\i sql/rollback_patch36.sql
reset patch36.drop_leads;
select chk('rollback: store_requests + banners catalog identical to the live shape (columns, constraints, indexes, policy, triggers, realtime)', shape() = :'s0', shape());
select chk('rollback: the 2 approved branch requests identical', branch_rows() = :'b0');
select chk('rollback: lead objects gone', (select count(*) from pg_proc where proname like 'lead\_%') = 0 and to_regclass('lead_attempts') is null);
-- ---------- 5. apply again ----------
\i sql/schema_patch36.sql
select chk('apply again after rollback works, branch rows unchanged', to_regproc('lead_submit') is not null and branch_rows() = :'b0');
\pset tuples_only off
select n, case when ok then 'PASS' else 'FAIL' end r, label, left(got, 60) got from res order by n;
select 'PATCH36-PROD ' || count(*) filter (where ok) || '/' || count(*) from res;
