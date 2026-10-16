-- =============================================================================================
-- PATCH 36 — restaurant onboarding requests from the public partner page (v57). NOT APPLIED ANYWHERE.
--
-- Reuses store_requests. A new kind 'lead' = a request sent WITHOUT an account from partner.html,
-- through the Edge Function `partner-lead` (Turnstile checked by the server). The existing kind
-- 'branch' (a restaurant owner asks for another restaurant, request_store / decide_store_request)
-- is unchanged.
--
-- Who can do what
--   lead_submit      : ONLY the Edge Function (service_role). Not anon, not signed-in users, so the
--                      Turnstile check cannot be skipped by calling the database directly.
--   read leads       : admin or staff with the 'stores' permission (existing read policy; a lead has
--                      no user, so nobody else can read it).
--   lead_set_status  : 'stores' permission: new → contacted, new/contacted → rejected (note required).
--   lead_link        : admin only: new/contacted → converted, linked to ONE existing store, once.
--                      Switched OFF by default (setting link_enabled = 0) until the owner assignment
--                      path (assign_owner, not in the project files) is verified.
-- Limits (all in lead_settings, PROPOSED values, not approved for production):
--   counted on ATTEMPTS (lead_attempts), never reset by a success or a duplicate; the answer is the
--   same 'ok' for new / duplicate / phone limit, so it never tells whether a phone is known.
-- Phone in lead_attempts: only a keyed hash made by the Edge Function with a server secret.
-- Safe to run again.
-- =============================================================================================
begin;

-- ---------- 1. store_requests: kind + lead states ----------
alter table store_requests add column if not exists kind text not null default 'branch';
alter table store_requests add column if not exists updated_at timestamptz;
alter table store_requests add column if not exists updated_by uuid references profiles(id);
alter table store_requests alter column user_id drop not null;
alter table store_requests alter column lat drop not null;
alter table store_requests alter column lng drop not null;
alter table store_requests drop constraint if exists store_requests_status_check;
alter table store_requests drop constraint if exists store_requests_kind_shape;
alter table store_requests add constraint store_requests_kind_shape check (
  (kind = 'branch' and user_id is not null and lat is not null and lng is not null and status in ('pending', 'approved', 'rejected'))
  or
  (kind = 'lead' and status in ('new', 'contacted', 'converted', 'rejected') and (store_id is null or status = 'converted'))
  -- (a converted lead keeps its status if the store is later deleted: store_id becomes null by the existing foreign key)
);
-- one OPEN lead per phone (blocks duplicates even when two requests arrive at the same moment)
create unique index if not exists store_req_lead_open_phone on store_requests (phone) where kind = 'lead' and status in ('new', 'contacted');
-- a store is linked to at most one lead
create unique index if not exists store_req_lead_store on store_requests (store_id) where kind = 'lead' and store_id is not null;
create index if not exists store_req_kind_status_idx on store_requests (kind, status, created_at desc);

-- ---------- 2. settings (PROPOSED values) ----------
create table if not exists lead_settings (
  key text primary key check (key in ('per_phone_day', 'per_client_hour', 'per_client_day', 'global_hour',
                                      'attempts_keep_days', 'rejected_keep_days', 'link_enabled')),
  value int not null check (value >= 0)
);
insert into lead_settings(key, value) values
  ('per_phone_day', 3),        -- attempts with the same phone in 24 h
  ('per_client_hour', 5),      -- attempts from the same client key (IP hash, see the Edge Function) in 1 h
  ('per_client_day', 15),      -- same, 24 h
  ('global_hour', 200),        -- emergency brake for the whole site, 1 h (not the main protection)
  ('attempts_keep_days', 30),
  ('rejected_keep_days', 90),
  ('link_enabled', 0)          -- lead → store linking off until assign_owner is verified
on conflict (key) do nothing;
alter table lead_settings enable row level security;
revoke all on table lead_settings from public, anon, authenticated;

create or replace function lead_setting(p_key text) returns int language sql stable security definer set search_path = public as $$
  select coalesce((select value from lead_settings where key = p_key), 0)
$$;
revoke all on function lead_setting(text) from public, anon, authenticated;

-- ---------- 3. attempts (never shown to the app) ----------
create table if not exists lead_attempts (
  id bigint generated always as identity primary key,
  at timestamptz not null default now(),
  phone_key text not null check (phone_key ~ '^[0-9a-f]{64}$'),
  client_key text check (client_key is null or client_key ~ '^[0-9a-f]{64}$'),
  outcome text not null
);
create index if not exists lead_att_phone_idx on lead_attempts (phone_key, at desc);
create index if not exists lead_att_client_idx on lead_attempts (client_key, at desc) where client_key is not null;
create index if not exists lead_att_at_idx on lead_attempts (at desc);
alter table lead_attempts enable row level security;
revoke all on table lead_attempts from public, anon, authenticated;

-- ---------- 4. submit (Edge Function only) ----------
-- answers: 'ok' (created, duplicate or phone limit: the same answer), 'busy' (client / site limit),
--          'bad_value'. Never raises after counting, so the attempt row is always kept.
create or replace function lead_submit(p_name text, p_category text, p_phone text, p_phone_key text, p_client_key text default null)
returns text language plpgsql security definer set search_path = public as $$
declare
  v_name text := regexp_replace(btrim(coalesce(p_name, '')), '\s+', ' ', 'g');
  v_ph text := norm_phone(p_phone);
  v_ck text := nullif(btrim(coalesce(p_client_key, '')), '');
  n_phone int; n_ch int; n_cd int; n_all int; v_out text;
begin
  if coalesce(p_phone_key, '') !~ '^[0-9a-f]{64}$' or (v_ck is not null and v_ck !~ '^[0-9a-f]{64}$') then return 'bad_value'; end if;
  -- the same client / phone is handled one at a time (fixed order: client, then phone)
  if v_ck is not null then perform pg_advisory_xact_lock(hashtext('lead-client:' || v_ck)); end if;
  perform pg_advisory_xact_lock(hashtext('lead-phone:' || p_phone_key));
  select count(*) into n_phone from lead_attempts where phone_key = p_phone_key and at > now() - interval '24 hours';
  if v_ck is not null then
    select count(*) filter (where at > now() - interval '1 hour'), count(*) into n_ch, n_cd
      from lead_attempts where client_key = v_ck and at > now() - interval '24 hours';
  end if;
  select count(*) into n_all from lead_attempts where at > now() - interval '1 hour';

  if char_length(v_name) < 2 or char_length(v_name) > 80 or v_ph is null
     or coalesce(p_category, '') not in ('rest','grocery','pharmacy','beauty','flowers','gifts','shops','sweets') then
    v_out := 'bad_value';
  elsif n_all >= lead_setting('global_hour') then
    v_out := 'busy_global';
  elsif v_ck is not null and (n_ch >= lead_setting('per_client_hour') or n_cd >= lead_setting('per_client_day')) then
    v_out := 'busy_client';
  elsif n_phone >= lead_setting('per_phone_day') then
    v_out := 'limit_phone';
  else
    insert into store_requests(kind, status, name, category, phone)
    values ('lead', 'new', v_name, p_category, v_ph)
    on conflict (phone) where kind = 'lead' and status in ('new', 'contacted') do nothing;
    v_out := case when found then 'created' else 'duplicate' end;
  end if;

  insert into lead_attempts(phone_key, client_key, outcome) values (p_phone_key, v_ck, v_out);
  return case v_out when 'created' then 'ok' when 'duplicate' then 'ok' when 'limit_phone' then 'ok'
                    when 'bad_value' then 'bad_value' else 'busy' end;
end $$;
revoke all on function lead_submit(text, text, text, text, text) from public, anon, authenticated;
do $$ begin grant execute on function lead_submit(text, text, text, text, text) to service_role; exception when undefined_object then null; end $$;

-- ---------- 5. staff: follow-up status ----------
create or replace function lead_set_status(p_id uuid, p_status text, p_note text default null) returns void
language plpgsql security definer set search_path = public as $$
declare v_r store_requests; v_note text := nullif(left(btrim(coalesce(p_note, '')), 300), '');
begin
  if not has_perm('stores') then raise exception 'not_allowed'; end if;
  select * into v_r from store_requests where id = p_id and kind = 'lead' for update;
  if not found then raise exception 'not_found'; end if;
  if p_status = 'contacted' and v_r.status = 'new' then
    update store_requests set status = 'contacted', admin_note = coalesce(v_note, admin_note), updated_at = now(), updated_by = auth.uid() where id = p_id;
  elsif p_status = 'rejected' and v_r.status in ('new', 'contacted') then
    if v_note is null or char_length(v_note) < 3 then raise exception 'note_required'; end if;
    update store_requests set status = 'rejected', admin_note = v_note, updated_at = now(), updated_by = auth.uid(),
           decided_at = now(), decided_by = auth.uid() where id = p_id;
  else
    raise exception 'bad_transition';
  end if;
end $$;
revoke all on function lead_set_status(uuid, text, text) from public, anon;
grant execute on function lead_set_status(uuid, text, text) to authenticated;

-- ---------- 6. admin: link to ONE existing store (off until assign_owner is verified) ----------
create or replace function lead_link(p_id uuid, p_store uuid) returns void
language plpgsql security definer set search_path = public as $$
declare v_r store_requests;
begin
  if not is_admin() then raise exception 'not_allowed'; end if;
  if lead_setting('link_enabled') <> 1 then raise exception 'link_disabled'; end if;
  select * into v_r from store_requests where id = p_id and kind = 'lead' for update;
  if not found then raise exception 'not_found'; end if;
  if v_r.status not in ('new', 'contacted') or v_r.store_id is not null then raise exception 'bad_transition'; end if;
  if not exists (select 1 from stores where id = p_store) then raise exception 'not_found'; end if;
  if exists (select 1 from store_requests where kind = 'lead' and store_id = p_store) then raise exception 'already_linked'; end if;
  update store_requests set status = 'converted', store_id = p_store, updated_at = now(), updated_by = auth.uid(),
         decided_at = now(), decided_by = auth.uid() where id = p_id;
exception when unique_violation then raise exception 'already_linked';
end $$;
revoke all on function lead_link(uuid, uuid) from public, anon;
grant execute on function lead_link(uuid, uuid) to authenticated;

-- ---------- 6b. audit of website-request decisions (live DB has audit_changes + audit_log; store_requests had no audit trigger) ----------
-- Only rows of kind 'lead' (the WHEN clause): branch requests keep exactly their current behaviour. Logged: who (auth.uid()),
-- status, linked store and the staff note. Inserts by the Edge Function and retention deletes are not logged (the attempts table
-- and the retention rule cover them). Skipped with a NOTICE if audit_changes() does not exist.
do $$
begin
  if to_regproc('public.audit_changes') is null then raise notice 'patch36: audit_changes() not found, lead audit trigger not created'; return; end if;
  execute 'drop trigger if exists trg_audit_store_leads on store_requests';
  execute 'create trigger trg_audit_store_leads after update on store_requests for each row when (old.kind = ''lead'')
           execute function audit_changes(''id'', ''status'', ''store_id'', ''admin_note'')';
end $$;

-- ---------- 7. retention (run by a schedule, e.g. pg_cron, once a day — not set up by this patch) ----------
create or replace function lead_cleanup() returns int language plpgsql security definer set search_path = public as $$
declare a int; b int;
begin
  delete from lead_attempts where at < now() - make_interval(days => lead_setting('attempts_keep_days'));
  get diagnostics a = row_count;
  delete from store_requests where kind = 'lead' and status = 'rejected' and decided_at < now() - make_interval(days => lead_setting('rejected_keep_days'));
  get diagnostics b = row_count;
  return a + b;
end $$;
revoke all on function lead_cleanup() from public, anon, authenticated;
do $$ begin grant execute on function lead_cleanup() to service_role; exception when undefined_object then null; end $$;

-- ---------- 8. banners: link to the partner page ----------
-- The live check on banners.link_type is NOT in the project files. It is changed ONLY when it is exactly one check of the simple
-- form «link_type IS NULL OR link_type IN (…)» or «link_type IN (…)»: the same constraint (same name, same conditions, same
-- values) is re-created with 'partner' added to its list. Any other structure (several checks, other columns or conditions)
-- → banners are NOT touched, a WARNING says so, and the rest of the patch still applies. Then send the result of:
--   select conname, pg_get_constraintdef(oid) from pg_constraint where conrelid = 'banners'::regclass;
do $$
declare n int; v_name text; v_def text; v_new text;
  re1 text := '^CHECK \(\(\(link_type IS NULL\) OR \(link_type = ANY \(ARRAY\[''[a-z_]+''::text(, ''[a-z_]+''::text)*\]\)\)\)\)$';
  re2 text := '^CHECK \(\(link_type = ANY \(ARRAY\[''[a-z_]+''::text(, ''[a-z_]+''::text)*\]\)\)\)$';
begin
  if to_regclass('public.banners') is null then raise warning 'patch36: table banners not found, banners not changed'; return; end if;
  select count(*) into n from pg_constraint where conrelid = 'public.banners'::regclass and contype = 'c' and pg_get_constraintdef(oid) ~* 'link_type';
  if n = 0 then raise notice 'patch36: banners.link_type has no check, the partner link needs no change'; return; end if;
  if n > 1 then
    raise warning 'patch36: banners NOT changed: % checks mention link_type. Send: select conname, pg_get_constraintdef(oid) from pg_constraint where conrelid = ''banners''::regclass;', n;
    return;
  end if;
  select conname, pg_get_constraintdef(oid) into v_name, v_def from pg_constraint
   where conrelid = 'public.banners'::regclass and contype = 'c' and pg_get_constraintdef(oid) ~* 'link_type';
  if v_def ~ '''partner''::text' then return; end if;
  if v_def !~ re1 and v_def !~ re2 then
    raise warning 'patch36: banners NOT changed: the link_type check has a structure this patch does not know: %. Send: select conname, pg_get_constraintdef(oid) from pg_constraint where conrelid = ''banners''::regclass;', v_def;
    return;
  end if;
  v_new := regexp_replace(v_def, '\]\)', ', ''partner''::text])');   -- these two forms hold exactly one list
  execute format('alter table banners drop constraint %I', v_name);
  execute format('alter table banners add constraint %I %s', v_name, substr(v_new, 1));
end $$;

commit;
