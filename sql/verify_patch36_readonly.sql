-- =============================================================================================
-- READ-ONLY checks before patch 36 / before switching on lead linking (v57). NOT RUN ANYWHERE.
-- Run in the Supabase SQL editor; it changes nothing (read-only transaction, rolled back).
-- Send the results back; no customer names or phones are selected (counts only).
-- =============================================================================================
begin transaction read only;

-- A. assign_owner (needed only for LINKING a request to a store; receiving requests does not depend on it)
-- A1. full definition: who may call it, what it changes (owner of the store, role of the account, previous owner, audit)
select p.oid::regprocedure as signature, p.prosecdef as security_definer, pg_get_userbyid(p.proowner) as owner,
       p.proconfig as settings, pg_get_functiondef(p.oid) as definition
  from pg_proc p join pg_namespace n on n.oid = p.pronamespace
 where n.nspname = 'public' and p.proname = 'assign_owner';
-- A2. who can execute it
select p.oid::regprocedure as signature,
       has_function_privilege('anon', p.oid, 'execute') as anon_can,
       has_function_privilege('authenticated', p.oid, 'execute') as signed_in_can
  from pg_proc p join pg_namespace n on n.oid = p.pronamespace where n.nspname = 'public' and p.proname = 'assign_owner';
-- A3. other functions / triggers that change profiles.role (an owner assignment may rely on one)
select p.oid::regprocedure as function_name from pg_proc p join pg_namespace n on n.oid = p.pronamespace
 where n.nspname = 'public' and p.prosrc ~* 'update\s+(public\.)?profiles\s+set[^;]*\mrole\M';
select tgname, tgrelid::regclass as on_table, pg_get_triggerdef(oid) from pg_trigger
 where not tgisinternal and tgrelid in ('public.stores'::regclass, 'public.profiles'::regclass);

-- B. banners.link_type check (patch 36 changes it only if it has the simple known form)
select conname, pg_get_constraintdef(oid) from pg_constraint where conrelid = 'public.banners'::regclass and contype = 'c';
select coalesce(link_type, '(empty)') as link_type, count(*) from banners group by 1 order by 1;

-- C. store_requests as patch 36 expects it (patch 19 + 26)
select column_name, data_type, is_nullable, column_default from information_schema.columns
 where table_schema = 'public' and table_name = 'store_requests' order by ordinal_position;
select conname, pg_get_constraintdef(oid) from pg_constraint where conrelid = 'public.store_requests'::regclass order by 1;
select polname, polcmd, pg_get_expr(polqual, polrelid) as using_expr from pg_policy where polrelid = 'public.store_requests'::regclass;
select status, count(*) from store_requests group by 1 order by 1;

-- D. names patch 36 creates must not exist yet; helpers it uses must exist
select name, to_regclass('public.' || name) is not null as table_exists from unnest(array['lead_settings', 'lead_attempts']) name;
select name, exists (select 1 from pg_proc p join pg_namespace n on n.oid = p.pronamespace where n.nspname = 'public' and p.proname = name) as function_exists
  from unnest(array['lead_submit', 'lead_set_status', 'lead_link', 'lead_cleanup', 'lead_setting', 'norm_phone', 'is_admin', 'has_perm']) name;
select rolname, rolbypassrls from pg_roles where rolname in ('service_role', 'authenticated', 'anon');

-- E. scheduling for lead_cleanup (optional)
select name, installed_version, default_version from pg_available_extensions where name = 'pg_cron';

rollback;
