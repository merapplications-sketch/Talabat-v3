-- READ-ONLY (24 Oct 2026, batch C): full policy texts and function bodies the first query did not settle.
-- Changes nothing. Run once in Supabase -> SQL Editor, export CSV. No personal data (structure only).
-- Purpose: reuse an existing read path for the courier position if there is one, before proposing new SQL.
select 'policy' as kind, tablename||'.'||policyname as name,
       cmd||' · roles='||array_to_string(roles,',')||' · using='||coalesce(qual,'∅')||' · check='||coalesce(with_check,'∅') as detail
from pg_policies where schemaname='public' and tablename in ('profiles','order_chat','order_recipient','orders')
union all
select 'rls', relname, 'rls='||relrowsecurity||' forced='||relforcerowsecurity
from pg_class where relnamespace='public'::regnamespace and relname in ('profiles','orders','order_recipient','order_chat')
union all
select 'grant', table_name||'.'||privilege_type, grantee
from information_schema.role_table_grants
where table_schema='public' and table_name='profiles' and grantee in ('anon','authenticated')
union all
select 'function_body', p.proname, pg_get_functiondef(p.oid)
from pg_proc p where p.pronamespace='public'::regnamespace
  and (p.proname in ('driver_location','can_see_order','order_courier_position')
       or p.prosrc ilike '%loc_updated%' or p.prosrc ilike '%profiles.lat%' or p.prosrc ilike '%p.lat%')
union all
select 'enum', t.typname, string_agg(e.enumlabel, ',' order by e.enumsortorder)
from pg_type t join pg_enum e on e.enumtypid=t.oid where t.typname='order_status' group by t.typname
order by 1,2;
