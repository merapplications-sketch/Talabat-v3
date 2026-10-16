-- Self-contained test for patch 36 (partner page requests) on an EMPTY local PostgreSQL:
--   psql -q -f sql/test_patch36.sql   -> "PATCH36 n/n"
-- Mimics Supabase: anon / authenticated get table rights by default (RLS protects rows), service_role bypasses RLS.
-- The tables of patches 18/19/26 that patch 36 touches are rebuilt here as the project files define them.
\set QUIET on
\set ON_ERROR_STOP on
\pset tuples_only on
drop schema if exists auth cascade; drop schema public cascade; create schema public; grant usage on schema public to public;
do $$ begin create role authenticated; exception when duplicate_object then null; end $$;
do $$ begin create role anon; exception when duplicate_object then null; end $$;
do $$ begin create role service_role bypassrls; exception when duplicate_object then null; end $$;
grant usage on schema public to anon, authenticated, service_role;
alter default privileges in schema public grant all on tables to anon, authenticated, service_role;
alter default privileges in schema public grant all on sequences to anon, authenticated, service_role;
create schema auth; grant usage on schema auth to authenticated, anon, service_role;
create function auth.uid() returns uuid language sql stable as $$ select nullif(current_setting('request.jwt.claim.sub', true), '')::uuid $$;
grant execute on function auth.uid() to authenticated, anon, service_role;
-- patch 18 / 26 helpers
create function norm_phone(p text) returns text language sql immutable as $$
  select case when d ~ '^992[0-9]{9}$' then '+' || d when d ~ '^[0-9]{9}$' then '+992' || d when d ~ '^0[0-9]{9}$' then '+992' || substr(d, 2) else null end
  from (select regexp_replace(coalesce(p, ''), '[^0-9]', '', 'g') as d) x $$;
create table profiles (id uuid primary key, role text, name text);
create table staff_members (user_id uuid, perms text[], active boolean);
create function is_admin() returns boolean language sql stable security definer set search_path = public as $$
  select exists(select 1 from profiles where id = auth.uid() and role = 'admin') $$;
create function has_perm(p text) returns boolean language sql stable security definer set search_path = public as $$
  select auth.uid() is not null and (is_admin() or exists(select 1 from staff_members s where s.user_id = auth.uid() and s.active and p = any(s.perms))) $$;
create table stores (id uuid primary key default gen_random_uuid(), name text, category text, phone text, address text, lat float8, lng float8,
  owner_id uuid, commission_pct numeric, fee_type text, fee_base numeric, is_active boolean, is_open boolean);
create table banners (id serial primary key, title text, link_type text, link_value text,
  constraint banners_link_type_ck check (link_type is null or link_type in ('none', 'store', 'category')));
insert into banners(title, link_type, link_value) values ('a', 'store', 'x'), ('b', 'category', 'rest'), ('c', null, null), ('d', 'none', null);
-- patch 19 (store_requests + branch request functions) as in the project files
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
alter table store_requests enable row level security;
create policy store_req_read on store_requests for select to public using (user_id = auth.uid() or has_perm('stores'));
create function request_store(p_name text, p_category text, p_phone text, p_address text, p_lat float8, p_lng float8, p_note text default null) returns uuid
language plpgsql security definer set search_path = public as $$
declare v_id uuid; v_ph text := norm_phone(p_phone); v_name text := btrim(coalesce(p_name, ''));
begin
  if auth.uid() is null then raise exception 'auth'; end if;
  if not exists (select 1 from profiles where id = auth.uid() and role = 'merchant') then raise exception 'not_allowed'; end if;
  if v_ph is null then raise exception 'bad_phone'; end if;
  insert into store_requests(user_id, name, category, phone, address, lat, lng, note)
  values (auth.uid(), v_name, p_category, v_ph, nullif(btrim(coalesce(p_address, '')), ''), p_lat, p_lng, nullif(btrim(coalesce(p_note, '')), '')) returning id into v_id;
  return v_id;
end $$;
create function decide_store_request(p_id uuid, p_approve boolean, p_note text default null) returns uuid
language plpgsql security definer set search_path = public as $$
declare v_r store_requests; v_store uuid; v_note text := nullif(left(btrim(coalesce(p_note, '')), 300), '');
begin
  if not is_admin() then raise exception 'not_allowed'; end if;
  select * into v_r from store_requests where id = p_id and status = 'pending' for update;
  if not found then raise exception 'bad_transition'; end if;
  if coalesce(p_approve, false) then
    insert into stores(name, category, phone, address, lat, lng, owner_id, commission_pct, fee_type, fee_base, is_active, is_open)
    values (v_r.name, v_r.category, v_r.phone, v_r.address, v_r.lat, v_r.lng, v_r.user_id, 10, 'fixed', 10, false, false) returning id into v_store;
  elsif v_note is null then raise exception 'note_required'; end if;
  update store_requests set status = case when coalesce(p_approve, false) then 'approved' else 'rejected' end,
         admin_note = v_note, store_id = v_store, decided_at = now(), decided_by = auth.uid() where id = p_id;
  return v_store;
end $$;
revoke all on function request_store(text, text, text, text, float8, float8, text), decide_store_request(uuid, boolean, text) from public, anon;
grant execute on function request_store(text, text, text, text, float8, float8, text), decide_store_request(uuid, boolean, text) to authenticated;
-- people: admin, stores staff, support staff, merchant, customer
insert into profiles(id, role) values ('a0000000-0000-0000-0000-00000000000a','admin'),('50000000-0000-0000-0000-000000000005','customer'),
  ('50000000-0000-0000-0000-000000000002','customer'),('e0000000-0000-0000-0000-00000000000e','merchant'),('c0000000-0000-0000-0000-000000000001','customer');
insert into staff_members values ('50000000-0000-0000-0000-000000000005','{stores}',true),('50000000-0000-0000-0000-000000000002','{support}',true);
insert into stores(id, name) values ('b0000000-0000-0000-0000-000000000001','Store 1'),('b0000000-0000-0000-0000-000000000002','Store 2');
-- an existing branch request from before the patch
insert into store_requests(id, user_id, name, category, phone, lat, lng) values
  ('d0000000-0000-0000-0000-000000000001','e0000000-0000-0000-0000-00000000000e','Old branch','rest','+992900000001',38.5,68.7);

\i sql/schema_patch36.sql
\i sql/schema_patch36.sql

create table res(n serial, ok boolean, label text, got text);
create function chk(l text, c boolean, g text default '') returns void language sql as $$ insert into res(ok, label, got) values (coalesce(c, false), l, g) $$;
-- run one statement as a role / user, answer = first column as text or 'ERR:<message>'
create function q(rl text, uid text, sqlt text) returns text language plpgsql as $f$
declare r text;
begin perform set_config('request.jwt.claim.sub', coalesce(uid, ''), true); execute 'set local role ' || rl;
  begin execute sqlt into r; exception when others then r := 'ERR:' || sqlerrm; end;
  reset role; perform set_config('request.jwt.claim.sub', '', true); return coalesce(r, ''); end $f$;
create function k(t text) returns text language sql immutable as $$ select md5(t) || md5(t || '#') $$;   -- stands for the HMAC made by the Edge Function
create function sub(nm text, ph text, cl text default null, cat text default 'rest') returns text language sql as $$
  select q('service_role', null, format('select lead_submit(%L, %L, %L, %L, %L)', nm, cat, ph, k(norm_phone(ph)), case when cl is null then null else k('ip:' || cl) end)) $$;
create function setv(key text, v int) returns void language sql as $$ update lead_settings set value = v where lead_settings.key = setv.key $$;
\set A '''a0000000-0000-0000-0000-00000000000a'''
\set STO '''50000000-0000-0000-0000-000000000005'''
\set SUP '''50000000-0000-0000-0000-000000000002'''
\set M '''e0000000-0000-0000-0000-00000000000e'''
\set C '''c0000000-0000-0000-0000-000000000001'''

-- ---------- who may submit ----------
select chk('anon cannot call lead_submit (Turnstile path cannot be skipped)', q('anon', null, $$select lead_submit('X','rest','900000111', md5('a')||md5('b'))$$) like 'ERR:permission denied%');
select chk('a signed-in customer cannot call lead_submit', q('authenticated', :C, $$select lead_submit('X','rest','900000111', md5('a')||md5('b'))$$) like 'ERR:permission denied%');
select chk('anon cannot insert into store_requests directly', q('anon', null, $$insert into store_requests(kind,status,name,category,phone) values ('lead','new','Spam','rest','+992900000999') returning 'inserted'$$) like 'ERR:%');
select chk('anon cannot read or write the attempts / settings', q('anon', null, $$select count(*)::text from lead_attempts$$) like 'ERR:permission denied%'
   and q('authenticated', :A, $$select count(*)::text from lead_settings$$) like 'ERR:permission denied%');
-- ---------- submit, duplicate, generic answer ----------
select chk('new request → ok', sub('Чайхана Роҳат', '+992 90 123 45 67', '1.1.1.1') = 'ok');
select chk('stored as a lead: new, normalized phone, no account, no location',
  (select string_agg(kind||'/'||status||'/'||phone||'/'||coalesce(user_id::text,'-')||'/'||coalesce(lat::text,'-'), ',') from store_requests where kind = 'lead') = 'lead/new/+992901234567/-/-');
select sub('Чайхана', '901234567', '1.1.1.2') as r \gset
select chk('same phone again (other format) → same answer ok, no second row', :'r' = 'ok' and (select count(*) from store_requests where kind = 'lead') = 1);
select chk('every call is counted, the duplicate too', (select count(*) from lead_attempts) = 2
   and (select string_agg(outcome, ',' order by id) from lead_attempts) = 'created,duplicate');
select chk('the phone itself is never stored in the attempts', not exists (select 1 from lead_attempts where phone_key like '%901234567%' or client_key like '%1.1.1%'));
select q('service_role', null, format('select lead_submit(%L, %L, %L, %L, %L)', 'Kafe', 'rest', '12345', k('12345'), k('ip:1.1.1.3'))) as r \gset
select chk('bad phone → bad_value (counted, nothing created)', :'r' = 'bad_value' and (select count(*) from lead_attempts) = 3
   and (select count(*) from store_requests where kind = 'lead') = 1, :'r');
select chk('bad category / too short name → bad_value', sub('K', '901111111', '1.1.1.4') = 'bad_value' and sub('Kafe', '901111111', '1.1.1.4', 'cars') = 'bad_value');
select chk('bad key format refused', q('service_role', null, $$select lead_submit('Kafe','rest','901111111','abc')$$) = 'bad_value');
-- ---------- phone limit: same answer, not reset by success ----------
select setv('per_phone_day', 3);
select sub('Чайхана', '+992901234567', '2.2.2.1') as r1 \gset
select sub('Чайхана', '+992901234567', '2.2.2.1') as r2 \gset
select chk('3rd attempt = duplicate, 4th = phone limit reached; both answer ok', :'r1' = 'ok' and :'r2' = 'ok'
   and (select string_agg(outcome, ',' order by id) from (select * from lead_attempts where phone_key = k('+992901234567') order by id desc limit 2) x) = 'duplicate,limit_phone');
update store_requests set status = 'rejected', decided_at = now(), admin_note = 'test' where kind = 'lead';
select sub('Чайхана', '+992901234567', '2.2.2.2') as r \gset
select chk('after the request is closed the phone limit still applies (success does not reset it)', :'r' = 'ok'
   and (select count(*) from store_requests where kind = 'lead') = 1 and (select outcome from lead_attempts order by id desc limit 1) = 'limit_phone');
delete from lead_attempts where phone_key = k('+992901234567');
select sub('Чайхана 2', '+992901234567', '2.2.2.3') as r \gset
select chk('when the window has passed, a closed phone may send a new request', :'r' = 'ok' and (select count(*) from store_requests where kind = 'lead') = 2);
-- ---------- client limit (main repeat protection besides Turnstile) ----------
truncate lead_attempts; select setv('per_client_hour', 2);
select sub('A1', '900000201', '9.9.9.9') || sub('A2', '900000202', '9.9.9.9') || sub('A3', '900000203', '9.9.9.9') as r \gset
select chk('client limit: different phones from one client, 3rd → busy', :'r' = 'okokbusy' and not exists (select 1 from store_requests where name = 'A3')
   and exists (select 1 from store_requests where name = 'A2'), :'r');
select chk('busy attempts are counted too (hammering keeps the window full)', (select count(*) from lead_attempts where client_key = k('ip:9.9.9.9')) = 3);
select chk('another client is not affected', sub('A4', '900000204', '8.8.8.8') = 'ok');
-- ---------- site brake ----------
select setv('global_hour', 4);
select chk('site emergency brake → busy for everyone', sub('A5', '900000205', '7.7.7.7') = 'busy');
select setv('global_hour', 200); select setv('per_client_hour', 5);
-- ---------- reading ----------
select chk('anon reads no lead', q('anon', null, $$select count(*)::text from store_requests where kind='lead'$$) = '0');
select chk('a customer reads no lead', q('authenticated', :C, $$select count(*)::text from store_requests where kind='lead'$$) = '0');
select chk('support staff reads no lead', q('authenticated', :SUP, $$select count(*)::text from store_requests where kind='lead'$$) = '0');
select chk('stores staff and admin read the leads', q('authenticated', :STO, $$select (count(*)>0)::text from store_requests where kind='lead'$$) = 'true'
   and q('authenticated', :A, $$select (count(*)>0)::text from store_requests where kind='lead'$$) = 'true');
-- ---------- staff status ----------
create temp table L as select id from store_requests where kind = 'lead' and name = 'A1';
grant select on L to authenticated;
select q('authenticated', :STO, format('select lead_set_status(%L, ''contacted'')', (select id from L))) as r \gset
select chk('stores staff: new → contacted', :'r' = '' and (select status from store_requests where id = (select id from L)) = 'contacted', :'r');
select chk('contacted → contacted again refused', q('authenticated', :STO, format('select lead_set_status(%L, ''contacted'')', (select id from L))) like 'ERR:bad_transition%');
select chk('reject needs a note', q('authenticated', :STO, format('select lead_set_status(%L, ''rejected'', '''')', (select id from L))) like 'ERR:note_required%');
select chk('support staff / customer cannot change a lead', q('authenticated', :SUP, format('select lead_set_status(%L, ''rejected'', ''nope'')', (select id from L))) like 'ERR:not_allowed%'
   and q('authenticated', :C, format('select lead_set_status(%L, ''rejected'', ''nope'')', (select id from L))) like 'ERR:not_allowed%');
select chk('staff cannot set converted by the status function', q('authenticated', :STO, format('select lead_set_status(%L, ''converted'')', (select id from L))) like 'ERR:bad_transition%');
select q('authenticated', :STO, format('update store_requests set status=''converted'' where id=%L returning 1', (select id from L))) as r \gset
select chk('nobody updates leads directly (no update policy)', (select status from store_requests where id = (select id from L)) = 'contacted', :'r');
-- ---------- admin link (off by default) ----------
select chk('link is OFF by default (assign_owner not verified)', q('authenticated', :A, format('select lead_link(%L, %L)', (select id from L), 'b0000000-0000-0000-0000-000000000001')) like 'ERR:link_disabled%');
select setv('link_enabled', 1);
select chk('stores staff cannot link', q('authenticated', :STO, format('select lead_link(%L, %L)', (select id from L), 'b0000000-0000-0000-0000-000000000001')) like 'ERR:not_allowed%');
select q('authenticated', :A, format('select lead_link(%L, %L)', (select id from L), 'b0000000-0000-0000-0000-000000000001')) as r \gset
select chk('admin links the lead to a store → converted', :'r' = ''
   and (select status || '/' || store_id from store_requests where id = (select id from L)) = 'converted/b0000000-0000-0000-0000-000000000001', :'r');
select chk('linking the same lead again refused', q('authenticated', :A, format('select lead_link(%L, %L)', (select id from L), 'b0000000-0000-0000-0000-000000000002')) like 'ERR:bad_transition%');
select chk('another lead to the same store refused', q('authenticated', :A, format('select lead_link(%L, %L)', (select id from store_requests where name = 'A2'), 'b0000000-0000-0000-0000-000000000001')) like 'ERR:already_linked%');
select chk('unknown store refused', q('authenticated', :A, format('select lead_link(%L, %L)', (select id from store_requests where name = 'A2'), gen_random_uuid())) like 'ERR:not_found%');
select chk('a converted lead cannot be rejected', q('authenticated', :STO, format('select lead_set_status(%L, ''rejected'', ''late'')', (select id from L))) like 'ERR:bad_transition%');
select sub('A1 again', '900000201', '6.6.6.6') as r \gset
select chk('a converted (closed) lead frees the phone for a new request', :'r' = 'ok' and (select count(*) from store_requests where kind = 'lead' and phone = '+992900000201') = 2);
delete from stores where id = 'b0000000-0000-0000-0000-000000000001';
select chk('deleting a linked store keeps the converted lead (store_id cleared)',
   (select status || '/' || coalesce(store_id::text, '-') from store_requests where id = (select id from L)) = 'converted/-');
select setv('link_enabled', 0);
-- ---------- branch requests unchanged ----------
select chk('merchant still sends a branch request', q('authenticated', :M, $$select (request_store('New branch','rest','+992900000077','',38.5,68.7) is not null)::text$$) = 'true');
select chk('branch request: kind branch, pending', (select kind || '/' || status from store_requests where name = 'New branch') = 'branch/pending');
select chk('a customer still cannot send a branch request', q('authenticated', :C, $$select request_store('X','rest','+992900000078','',38.5,68.7)::text$$) like 'ERR:not_allowed%');
select chk('admin approves a branch request (store created)', q('authenticated', :A, format('select (decide_store_request(%L, true) is not null)::text', (select id from store_requests where name = 'New branch'))) = 'true');
select chk('decide_store_request cannot touch a lead', q('authenticated', :A, format('select decide_store_request(%L, true)::text', (select id from store_requests where name = 'A2'))) like 'ERR:bad_transition%');
select chk('merchant reads only his own branch requests, no lead', q('authenticated', :M, $$select string_agg(distinct kind, ',') from store_requests$$) = 'branch');
select chk('a branch row cannot be stored without location / owner', q('service_role', null, $$insert into store_requests(kind,status,name,category,phone) values ('branch','pending','Bad','rest','+992900000079') returning 'x'$$) like 'ERR:%store_requests_kind_shape%');
select chk('a lead cannot get a branch status', q('service_role', null, $$insert into store_requests(kind,status,name,category,phone) values ('lead','pending','Bad','rest','+992900000080') returning 'x'$$) like 'ERR:%store_requests_kind_shape%');
-- ---------- banners ----------
select q('service_role', null, $$insert into banners(title, link_type) values ('p','partner') returning link_type$$) as r \gset
select chk('banners: partner link allowed, old link types still valid', :'r' = 'partner' and (select count(*) from banners) = 5, :'r');
select chk('banners: unknown link type still refused', q('service_role', null, $$insert into banners(title, link_type) values ('p','url') returning link_type$$) like 'ERR:%');
-- ---------- retention ----------
update lead_attempts set at = now() - interval '40 days' where id = (select min(id) from lead_attempts);
update store_requests set decided_at = now() - interval '100 days' where kind = 'lead' and status = 'rejected';
select q('service_role', null, 'select lead_cleanup()::text') as r \gset
select chk('cleanup removes old attempts and old rejected leads only', :'r'::int >= 2
   and not exists (select 1 from store_requests where kind = 'lead' and status = 'rejected')
   and exists (select 1 from store_requests where kind = 'lead' and status = 'converted'), :'r');
select chk('cleanup is not callable by users', q('authenticated', :A, 'select lead_cleanup()::text') like 'ERR:permission denied%');
\pset tuples_only off
select n, case when ok then 'PASS' else 'FAIL' end r, label, left(got, 50) got from res order by n;
select 'PATCH36 ' || count(*) filter (where ok) || '/' || count(*) from res;
