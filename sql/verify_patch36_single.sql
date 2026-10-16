-- =============================================================================================
-- ONE read-only SELECT (one result, exportable as CSV) before patch 36 / before any lead linking (v57).
-- NOT RUN ANYWHERE. It is a single SELECT: it reads the catalog and counts rows; it changes nothing.
-- No personal data: no names, e-mails, phones or ids of people; only object definitions and counts.
-- Columns: section | item | detail
-- =============================================================================================
with
f as (  -- plain functions in public (aggregates excluded: they have no function definition)
  select p.oid, p.proname, p.oid::regprocedure::text as sig, p.prosrc
    from pg_proc p join pg_namespace n on n.oid = p.pronamespace
   where n.nspname = 'public' and p.prokind = 'f'
),
trg as (  -- user triggers on stores / profiles / store_requests / banners
  select t.tgname, t.tgrelid::regclass::text as tbl, t.tgenabled, t.tgfoid, pg_get_triggerdef(t.oid) as def
    from pg_trigger t
   where not t.tgisinternal
     and t.tgrelid in (select c.oid from pg_class c join pg_namespace n on n.oid = c.relnamespace
                        where n.nspname = 'public' and c.relname in ('stores', 'profiles', 'store_requests', 'banners'))
),
rel as (  -- functions related to role changes, the app.bypass guard, auditing, or called by the triggers above
  select distinct f.oid, f.sig from f
   where f.oid in (select tgfoid from trg)
      or f.prosrc ~* 'app\.bypass'
      or f.prosrc ~* 'update\s+(public\.)?profiles\s+set[^;]*\mrole\M'
      or f.proname in ('audit_changes', 'is_admin', 'has_perm')
)
-- 1. who may execute assign_owner
select '1 assign_owner execute' as section, f.sig as item,
       'anon=' || has_function_privilege('anon', f.oid, 'execute')
       || ' authenticated=' || has_function_privilege('authenticated', f.oid, 'execute')
       || coalesce(' service_role=' || (select has_function_privilege('service_role', f.oid, 'execute') where exists (select 1 from pg_roles where rolname = 'service_role')), '')
       || ' public_acl=' || coalesce((select array_to_string(proacl, ' ') from pg_proc where oid = f.oid), '(default: PUBLIC can execute)') as detail
  from f where f.proname = 'assign_owner'
union all
-- 2a. triggers on stores / profiles / store_requests / banners
select '2a triggers', trg.tbl || '.' || trg.tgname, 'enabled=' || trg.tgenabled::text || ' | ' || trg.def from trg
union all
-- 2b. definitions of the related functions (trigger functions, app.bypass users, role changes, audit, permission helpers)
select '2b functions', rel.sig, pg_get_functiondef(rel.oid) from rel
union all
-- 3. every constraint on banners + link types in use (counts only)
select '3 banners constraint', c.conname, c.contype::text || ' | ' || pg_get_constraintdef(c.oid)
  from pg_constraint c where c.conrelid = to_regclass('public.banners')
union all
select '3 banners link_type in use', coalesce(b.link_type, '(empty)'), count(*)::text from banners b group by b.link_type
union all
-- 4a. store_requests columns
select '4a store_requests column', a.attname,
       format_type(a.atttypid, a.atttypmod) || case when a.attnotnull then ' NOT NULL' else ' null' end
       || coalesce(' default ' || pg_get_expr(d.adbin, d.adrelid), '')
  from pg_attribute a left join pg_attrdef d on d.adrelid = a.attrelid and d.adnum = a.attnum
 where a.attrelid = to_regclass('public.store_requests') and a.attnum > 0 and not a.attisdropped
union all
-- 4b. store_requests constraints, indexes, policies, row counts per status (no row content)
select '4b store_requests constraint', c.conname, c.contype::text || ' | ' || pg_get_constraintdef(c.oid)
  from pg_constraint c where c.conrelid = to_regclass('public.store_requests')
union all
select '4b store_requests index', i.indexrelid::regclass::text, pg_get_indexdef(i.indexrelid)
  from pg_index i where i.indrelid = to_regclass('public.store_requests')
union all
select '4b store_requests policy', p.polname, p.polcmd::text || ' | ' || coalesce(pg_get_expr(p.polqual, p.polrelid), '') || coalesce(' | check ' || pg_get_expr(p.polwithcheck, p.polrelid), '')
  from pg_policy p where p.polrelid = to_regclass('public.store_requests')
union all
select '4b store_requests rows', 'status=' || r.status, count(*)::text from store_requests r group by r.status
union all
select '4b store_requests realtime', 'in supabase_realtime',
       (exists (select 1 from pg_publication_tables where pubname = 'supabase_realtime' and schemaname = 'public' and tablename = 'store_requests'))::text
union all
-- 4c. names patch 36 creates (must not exist yet) and helpers it needs (must exist)
select '4c patch36 name (must be absent)', x.name,
       case when to_regclass('public.' || x.name) is not null then 'EXISTS as relation'
            when exists (select 1 from f where f.proname = x.name) then 'EXISTS as function'
            when exists (select 1 from pg_constraint where conname = x.name) then 'EXISTS as constraint'
            else 'absent' end
  from unnest(array['lead_settings', 'lead_attempts', 'lead_submit', 'lead_set_status', 'lead_link', 'lead_cleanup', 'lead_setting',
                    'store_requests_kind_shape', 'store_req_lead_open_phone', 'store_req_lead_store', 'store_req_kind_status_idx']) x(name)
union all
select '4c patch36 helper (must exist)', x.name,
       coalesce((select string_agg(f.sig, ', ') from f where f.proname = x.name), 'MISSING')
  from unnest(array['norm_phone', 'is_admin', 'has_perm']) x(name)
union all
select '4c patch36 role', x.name,
       coalesce((select 'exists bypassrls=' || rolbypassrls from pg_roles where rolname = x.name), 'MISSING')
  from unnest(array['service_role', 'authenticated', 'anon']) x(name)
union all
select '4c patch36 type', 'stores.id', coalesce((select format_type(atttypid, atttypmod) from pg_attribute where attrelid = to_regclass('public.stores') and attname = 'id'), 'MISSING')
order by 1, 2;
