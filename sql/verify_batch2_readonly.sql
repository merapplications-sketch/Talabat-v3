-- =============================================================================================
-- ONE read-only SELECT (one result, CSV) for preparing batch 2 (points / clarity of the amounts). NOT RUN ANYWHERE.
-- Why: the live definitions of place_order and the loyalty functions may differ from sql/ in the repository.
-- Returns only definitions and settings (no customer data). Columns: section | item | detail
-- =============================================================================================
with f as (
  select p.oid, p.proname, p.oid::regprocedure::text as sig
    from pg_proc p join pg_namespace n on n.oid = p.pronamespace
   where n.nspname = 'public' and p.prokind = 'f'
     and (p.proname in ('place_order', 'set_order_status', 'deliver_order', 'check_promo', 'check_promo_base', 'loyalty_summary', 'happy_hour_pct')
          or p.proname ~* '(point|loyal|cashback|voucher|wallet|commission|settle|refund)')
)
select '1 function' as section, f.sig as item, pg_get_functiondef(f.oid) as detail from f
union all
select '2 trigger', t.tgrelid::regclass::text || '.' || t.tgname, 'enabled=' || t.tgenabled::text || ' | ' || pg_get_triggerdef(t.oid)
  from pg_trigger t
 where not t.tgisinternal and t.tgrelid in (select c.oid from pg_class c join pg_namespace n on n.oid = c.relnamespace
                                             where n.nspname = 'public' and c.relname in ('orders', 'order_items', 'wallet_entries', 'ratings'))
union all
select '3 setting', s.key, s.value::text from app_settings s
union all
select '4 column', c.table_name || '.' || c.column_name, c.data_type || coalesce(' default ' || c.column_default, '')
  from information_schema.columns c
 where c.table_schema = 'public' and c.table_name in ('orders', 'stores', 'loyalty_ledger', 'loyalty_lots', 'happy_hours')
   and (c.table_name <> 'orders' or c.column_name ~* '(point|cash|discount|commission|subtotal|total|fee|tip|wallet|hh_|promo)')
   and (c.table_name <> 'stores' or c.column_name ~* '(point|cashback|discount|commission|fee|earn)')
order by 1, 2;
