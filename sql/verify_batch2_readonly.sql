-- =============================================================================================
-- ONE read-only SELECT (one result, CSV) for preparing batch 2 (UAT008/009/011/012/013/014/015). NOT RUN ANYWHERE.
-- Why: the live definitions of place_order, reject_order, set_order_status and the loyalty / wallet functions may differ
-- from sql/ in the repository. Returns only definitions, constraints, settings and column types — no customer data,
-- no keys, secrets or service settings (app_settings: 8 named loyalty / cashback keys only). Columns: section | item | detail
-- =============================================================================================
with
trg as (  -- triggers on the money / points tables
  select t.oid, t.tgname, t.tgrelid::regclass::text as tbl, t.tgenabled, t.tgfoid
    from pg_trigger t
   where not t.tgisinternal
     and t.tgrelid in (select c.oid from pg_class c join pg_namespace n on n.oid = c.relnamespace
                        where n.nspname = 'public' and c.relname in ('orders', 'order_items', 'wallet_entries', 'loyalty_lots', 'loyalty_ledger', 'ratings'))
),
f as (    -- functions: order life-cycle, points, wallet, commission / settlement, + every trigger function above
  select p.oid, p.oid::regprocedure::text as sig
    from pg_proc p join pg_namespace n on n.oid = p.pronamespace
   where n.nspname = 'public' and p.prokind = 'f'
     and (p.proname in ('place_order', 'set_order_status', 'reject_order', 'deliver_order', 'loyalty_summary', 'loyalty_setting',
                        'happy_hour_pct', 'wallet_balance')
          or p.proname ~* '(point|loyal|cashback|voucher|wallet|commission|settle|refund)'
          or p.oid in (select tgfoid from trg))
)
select '1 function' as section, f.sig as item, pg_get_functiondef(f.oid) as detail from f
union all
select '2 trigger', trg.tbl || '.' || trg.tgname, 'enabled=' || trg.tgenabled::text || ' | ' || pg_get_triggerdef(trg.oid) from trg
union all
select '3 constraint', c.conrelid::regclass::text || '.' || c.conname, pg_get_constraintdef(c.oid)
  from pg_constraint c
 where c.contype in ('c', 'u') and c.conrelid in (select oid from pg_class where relname in ('loyalty_lots', 'loyalty_ledger', 'wallet_entries')
                                                    and relnamespace = 'public'::regnamespace)
union all
select '4 setting', s.key, s.value::text from app_settings s           -- only the loyalty / cashback keys used by these items
 where s.key in ('loyalty_points_per_tjs', 'loyalty_earn_per_tjs', 'loyalty_expiry_days', 'loyalty_min_redeem', 'loyalty_min_order',
                 'loyalty_voucher_points', 'loyalty_rate_reward', 'cashback_pct')
union all
select '6 realtime', pt.pubname, pt.tablename from pg_publication_tables pt   -- which of these tables send live events
 where pt.schemaname = 'public' and pt.tablename in ('orders', 'wallet_entries', 'loyalty_ledger', 'loyalty_lots', 'ratings')
union all
select '5 column', c.table_name || '.' || c.column_name, c.data_type || coalesce(' default ' || c.column_default, '')
  from information_schema.columns c
 where c.table_schema = 'public' and c.table_name in ('orders', 'stores', 'loyalty_ledger', 'loyalty_lots', 'wallet_entries')
   and (c.table_name <> 'orders' or c.column_name ~* '(status|cancel|reject|point|cash|discount|commission|subtotal|total|fee|tip|wallet|hh_|promo|returned|loyalty)')
   and (c.table_name <> 'stores' or c.column_name ~* '(point|cashback|discount|commission|fee|earn)')
order by 1, 2;
