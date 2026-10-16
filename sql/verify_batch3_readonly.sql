-- =============================================================================================
-- ONE read-only SELECT (one result, CSV) for preparing the batch «delivery proof, support refunds, cash settlement». NOT RUN ANYWHERE.
-- Why: dispatch_next, driver_accept, ticket_set_status and the storage policies of the proof photos are not in the repository
-- (or may differ from it). Returns only definitions, policies, indexes, column types, privileges and the proofs bucket settings —
-- no customer / courier data, no keys, no secrets. Columns: section | item | detail
-- =============================================================================================
with
f as (    -- order hand-over, courier offers, support refunds, cash, proof photos, wallet
  select p.oid, p.oid::regprocedure::text as sig, pg_get_userbyid(p.proowner) as owner
    from pg_proc p join pg_namespace n on n.oid = p.pronamespace
   where n.nspname = 'public' and p.prokind = 'f'
     and (p.proname in ('deliver_order', 'driver_accept', 'dispatch_next', 'ticket_set_status', 'ticket_refund_room', 'cash_balances',
                        'settle_driver_cash', 'wallet_balance', 'wallet_adjust', 'has_perm', 'is_admin')
          or p.proname ~* '(dispatch|offer|ticket|cash|settle|refund|proof|photo|courier)')
),
tb as (   -- tables the batch touches
  select c.oid, n.nspname || '.' || c.relname as t
    from pg_class c join pg_namespace n on n.oid = c.relnamespace
   where c.relkind in ('r', 'p')
     and ((n.nspname = 'public' and c.relname in ('orders', 'wallet_entries', 'support_tickets', 'profiles', 'order_offers', 'audit_log'))
       or (n.nspname = 'storage' and c.relname in ('objects', 'buckets')))
)
select '1 function' as section, f.sig as item, 'owner=' || f.owner || E'\n' || pg_get_functiondef(f.oid) as detail from f
union all
select '2 trigger', tb.t || '.' || g.tgname, 'enabled=' || g.tgenabled::text || ' | ' || pg_get_triggerdef(g.oid)
  from pg_trigger g join tb on tb.oid = g.tgrelid where not g.tgisinternal and tb.t like 'public.%'
union all
select '3 policy', pl.schemaname || '.' || pl.tablename || '.' || pl.policyname,
       pl.cmd || ' to ' || array_to_string(pl.roles, ',') || ' | using: ' || coalesce(pl.qual, '—') || ' | check: ' || coalesce(pl.with_check, '—')
  from pg_policies pl
 where (pl.schemaname = 'public' and pl.tablename in ('wallet_entries', 'support_tickets', 'orders', 'audit_log'))
    or (pl.schemaname = 'storage' and pl.tablename = 'objects')
union all
select '4 rls', tb.t, 'rls=' || c.relrowsecurity::text || ' force=' || c.relforcerowsecurity::text from tb join pg_class c on c.oid = tb.oid
union all
select '5 index', tb.t || '.' || i.relname, pg_get_indexdef(i.oid)
  from tb join pg_index x on x.indrelid = tb.oid join pg_class i on i.oid = x.indexrelid
 where tb.t in ('public.wallet_entries', 'public.support_tickets', 'public.orders', 'storage.objects')
union all
select '6 constraint', tb.t || '.' || k.conname, pg_get_constraintdef(k.oid)
  from tb join pg_constraint k on k.conrelid = tb.oid
 where k.contype in ('c', 'u', 'f') and tb.t in ('public.wallet_entries', 'public.support_tickets', 'storage.buckets')
union all
select '7 column', ic.table_schema || '.' || ic.table_name || '.' || ic.column_name, ic.data_type || coalesce(' default ' || ic.column_default, '')
  from information_schema.columns ic
 where (ic.table_schema = 'public' and (ic.table_name in ('support_tickets', 'audit_log', 'order_offers')
         or (ic.table_name = 'profiles' and ic.column_name ~* '(cash|limit|block|driver|role|online)')
         or (ic.table_name = 'orders' and ic.column_name ~* '(cash|photo|proof|driver|wallet|returned|total|payment|status|done_at|picked|arrived)')))
    or (ic.table_schema = 'storage' and ic.table_name in ('objects', 'buckets'))
union all
select '8 bucket', b.id, 'public=' || b.public::text || ' size_limit=' || coalesce(b.file_size_limit::text, '—')
       || ' mime=' || coalesce(array_to_string(b.allowed_mime_types, ','), '—')
  from storage.buckets b where b.id = 'proofs'
union all
-- can the owner of deliver_order read the stored photo list (needed for a server-side existence check)?
select '9 privilege', f.sig || ' owner ' || f.owner,
       'storage.objects select=' || has_table_privilege(f.owner, 'storage.objects', 'SELECT')::text
       || ' | storage usage=' || has_schema_privilege(f.owner, 'storage', 'USAGE')::text
  from f where f.sig like 'deliver_order(%'
order by 1, 2;
