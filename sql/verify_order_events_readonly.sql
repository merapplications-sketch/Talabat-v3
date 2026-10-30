-- READ-ONLY check (27 Oct, work item C-2): can a CUSTOMER read the order_events of his own orders, and only those?
-- No table, policy, grant or row is changed. Two separate runs in Supabase → SQL Editor (the editor shows the result of
-- the last statement only, so each part is ONE statement). Send both result tables (Export → CSV, or a screenshot).

-- ============ PART 1 — run as the default role (postgres). Table settings, policies, grants, event kinds (counts only).
select 'rls' as item, relrowsecurity::text as value, relforcerowsecurity::text as detail
  from pg_class where oid = 'public.order_events'::regclass
union all
select 'policy', policyname || ' · ' || cmd || ' · ' || array_to_string(roles, ','), coalesce(qual, '') || ' | ' || coalesce(with_check, '')
  from pg_policies where schemaname = 'public' and tablename = 'order_events'
union all
select 'grant', grantee, string_agg(privilege_type, ',' order by privilege_type)
  from information_schema.role_table_grants
 where table_schema = 'public' and table_name = 'order_events' and grantee in ('anon', 'authenticated')
 group by grantee
union all
select 'kind', kind, count(*)::text from public.order_events group by kind;

-- ============ PART 2 — run AS A TEST CUSTOMER: in the SQL Editor role selector choose «authenticated», then impersonate
-- the existing test customer account (no new account). Row «me» must show that customer's id and role = customer;
-- if «me» is empty the editor is not impersonating and the result does not count.
-- Expected: own_orders > 0 and events_visible > 0 for orders that changed status; foreign_events_visible = 0.
select 'me' as item, coalesce(auth.uid()::text, 'NOT IMPERSONATING') as value,
       coalesce((select role::text from public.profiles where id = auth.uid()), '') as detail
union all
select 'own_order ' || o.id::text, o.status::text,
       'events_visible=' || (select count(*) from public.order_events e where e.order_id = o.id)::text
       || ' kinds=' || coalesce((select string_agg(distinct e.kind, ',') from public.order_events e where e.order_id = o.id), '')
  from (select id, status from public.orders where customer_id = auth.uid() order by created_at desc limit 5) o
union all
select 'foreign_events_visible', (select count(*) from public.order_events e
        where not exists (select 1 from public.orders o where o.id = e.order_id and o.customer_id = auth.uid()))::text, '';
