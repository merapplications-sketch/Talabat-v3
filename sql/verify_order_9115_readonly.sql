-- READ-ONLY (31 Oct): stored components of order 9115 and its restaurant's address, to reconcile what the iPhone screens
-- showed (items 295, commission 14.75, cashback 5.9, «Вам» 274.35, wallet 153.52, cash to the courier 161.48, driver 20).
-- Run as the default role (postgres) in Supabase → SQL Editor; ONE statement, nothing is changed. Send the result (CSV).
-- Columns are read through to_jsonb, so a column missing in this database simply does not appear (no error).
select 'order' as part, key as item, value
  from public.orders o, jsonb_each_text(to_jsonb(o))
 where o.id = 9115 and key in ('status', 'store_id', 'subtotal', 'discount', 'promo_discount', 'promo_code', 'points_used',
       'points_value', 'delivery_base', 'delivery_extra', 'delivery_km', 'delivery_fee', 'fee_waived', 'tip', 'total',
       'wallet_used', 'payment', 'commission', 'cashback', 'points_earned', 'driver_payout', 'cash_collected',
       'created_at', 'done_at')
union all
select 'items', i.name || ' ×' || i.qty, (i.price * i.qty)::text
  from public.order_items i where i.order_id = 9115
union all
select 'wallet', e.kind, e.amount::text || ' · ' || e.created_at::text
  from public.wallet_entries e where e.order_id = 9115
union all
select 'store', key, coalesce(value, '(null)')
  from public.orders o join public.stores s on s.id = o.store_id, jsonb_each_text(to_jsonb(s))
 where o.id = 9115 and key in ('name', 'address', 'lat', 'lng', 'cashback_pct', 'earn_per_tjs', 'fee_type', 'fee_base', 'fee_per_km');
