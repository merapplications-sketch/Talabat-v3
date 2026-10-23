-- v81 · READ-ONLY check of the catalog path (stores, dishes, sizes / extras, photos, banners) and of the admin accounts.
-- Changes nothing: only SELECT on catalog views. Run once in Supabase → SQL Editor and send back the result table.
-- No personal data: accounts are counted, emails are not shown.
with
cols as (
  select 'column' as kind, table_name||'.'||column_name as name,
         coalesce(column_default,'∅')||' · null='||is_nullable||' · '||data_type as detail
  from information_schema.columns
  where table_schema='public' and table_name in ('stores','menu_items','item_option_groups','item_options','banners')
    and column_name in ('is_active','is_open','available','approved','sort','max_sel','required','price_delta','image_url','cover_url',
                        'logo_url','placement','starts_at','ends_at','link_type','link_value','owner_id','section','discount_pct','fee_per_km')
),
pol as (
  select 'policy', tablename||' · '||policyname, cmd||' · roles='||array_to_string(roles,',')||' · using='||coalesce(left(qual,160),'∅')||' · check='||coalesce(left(with_check,160),'∅')
  from pg_policies where schemaname='public' and tablename in ('stores','menu_items','item_option_groups','item_options','banners')
),
rls as (
  select 'rls', relname, case when relrowsecurity then 'on' else 'OFF' end
  from pg_class where relnamespace='public'::regnamespace and relname in ('stores','menu_items','item_option_groups','item_options','banners')
),
bkt as (
  select 'bucket', id, 'public='||public||' · size_limit='||coalesce(file_size_limit::text,'∅')||' · types='||coalesce(array_to_string(allowed_mime_types,','),'∅')
  from storage.buckets
),
spol as (
  select 'storage_policy', policyname, cmd||' · roles='||array_to_string(roles,',')||' · using='||coalesce(left(qual,160),'∅')||' · check='||coalesce(left(with_check,160),'∅')
  from pg_policies where schemaname='storage' and tablename='objects'
),
trg as (
  select 'trigger', event_object_table||' · '||trigger_name, action_timing||' '||event_manipulation
  from information_schema.triggers where event_object_schema='public'
    and event_object_table in ('stores','menu_items','item_option_groups','item_options','banners')
),
fn as (
  select 'function', p.proname, 'security_definer='||p.prosecdef
  from pg_proc p where p.pronamespace='public'::regnamespace and p.proname in ('assign_owner','is_admin','my_perms','update_my_store','set_store_open','owner_info')
),
acc as (
  select 'accounts', 'role='||coalesce(role,'∅'), count(*)::text from public.profiles group by role
),
cnt as (
  select 'rows','stores', count(*)::text||' · active '||count(*) filter (where is_active)::text from public.stores
  union all select 'rows','menu_items', count(*)::text||' · approved '||count(*) filter (where approved)::text||' · with photo '||count(*) filter (where image_url is not null and image_url<>'')::text||' · inline photo '||count(*) filter (where image_url like 'data:%')::text from public.menu_items
  union all select 'rows','item_option_groups', count(*)::text from public.item_option_groups
  union all select 'rows','item_options', count(*)::text from public.item_options
  union all select 'rows','banners', count(*)::text||' · active '||count(*) filter (where is_active)::text||' · inline photo '||count(*) filter (where image_url like 'data:%')::text from public.banners
)
select * from cols union all select * from pol union all select * from rls union all select * from bkt union all select * from spol
union all select * from trg union all select * from fn union all select * from acc union all select * from cnt
order by 1,2;
