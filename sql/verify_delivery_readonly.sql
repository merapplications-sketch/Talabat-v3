-- READ-ONLY check for the delivery / tracking plan (24 Oct 2026). Changes nothing: SELECT on catalog views only.
-- Run once in Supabase -> SQL Editor and export the result as CSV. No personal data, only structure.
-- Answers: where the courier position is stored and who may read it; order / address coordinate columns; gift
-- recipient table and policies; chat table and policies; prep-time / status functions; delivery-code columns (if any).
with
cols as (
  select 'column' as kind, table_name||'.'||column_name as name, data_type||' · null='||is_nullable as detail
  from information_schema.columns
  where table_schema='public' and (
        table_name in ('orders','addresses','order_recipient','order_chat','profiles')
     or table_name ilike '%locat%' or table_name ilike '%track%')
    and (table_name<>'orders' or column_name ~ '(lat|lng|address|recipient|gift|prep|ready|code|pin|eta|driver|landmark|note|entrance|floor|apart)')
    and (table_name<>'profiles' or column_name ~ '(lat|lng|loc|seen|online)')
),
fn as (
  select 'function', p.proname, 'security_definer='||p.prosecdef||' · args='||pg_get_function_identity_arguments(p.oid)
  from pg_proc p where p.pronamespace='public'::regnamespace
   and p.proname ~ '(driver_location|location|track|set_prep|prep|order_status|set_status|ready|deliver|recipient|gift|chat|code|eta)'
),
pol as (
  select 'policy', tablename||'.'||policyname, cmd||' · '||coalesce(left(qual,160),'')
  from pg_policies where schemaname='public'
   and (tablename in ('orders','addresses','order_recipient','order_chat') or tablename ilike '%locat%' or tablename ilike '%track%')
),
rt as (
  select 'realtime', tablename, 'in supabase_realtime publication' from pg_publication_tables where pubname='supabase_realtime'
),
ext as (
  select 'extension', extname, extversion from pg_extension where extname in ('pg_cron','pg_net','http','postgis')
)
select * from cols union all select * from fn union all select * from pol union all select * from rt union all select * from ext
order by 1,2;
