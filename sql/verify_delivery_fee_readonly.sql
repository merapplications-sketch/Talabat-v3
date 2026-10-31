-- READ-ONLY delivery-fee audit (31 Oct): how the fee of orders 9115 and 9116 was produced. Nothing is changed.
-- Run as the default role (postgres) in Supabase → SQL Editor. ONE statement. Send the result (CSV).
-- What it shows: the stored fee parts of both orders, the store's fee settings, the platform delivery settings, the
-- straight-line distance recomputed now with the database's own dist_km() and with the haversine formula, and the
-- definition of dist_km() itself (to prove whether it is a straight line or a road distance).
with o as (
  select o.id, o.store_id, o.lat, o.lng, o.created_at, to_jsonb(o) j from public.orders o where o.id in (9115, 9116)
), s as (
  select distinct s.id, to_jsonb(s) j, s.lat, s.lng from public.stores s join o on o.store_id = s.id
)
select 'order ' || o.id as part, key as item, value
  from o, jsonb_each_text(o.j)
 where key in ('status', 'subtotal', 'discount', 'promo_discount', 'points_value', 'delivery_base', 'delivery_extra',
               'delivery_km', 'delivery_fee', 'fee_waived', 'tip', 'total', 'wallet_used', 'payment', 'driver_payout',
               'lat', 'lng', 'created_at')
union all
select 'store', key, coalesce(value, '(null)')
  from s, jsonb_each_text(s.j)
 where key in ('name', 'lat', 'lng', 'fee_type', 'fee_base', 'fee_per_km', 'fee_free_km', 'free_first_delivery', 'free_delivery_min')
union all
select 'setting', key, value::text from public.app_settings where key like 'delivery_%'
union all
select 'distance ' || o.id, 'dist_km(store, customer) now', round(public.dist_km(s.lat, s.lng, o.lat, o.lng)::numeric, 3)::text
  from o join s on s.id = o.store_id where s.lat is not null and o.lat is not null
union all
select 'distance ' || o.id, 'haversine km (reference)', round((6371 * 2 * asin(sqrt(
         power(sin(radians(o.lat - s.lat) / 2), 2) + cos(radians(s.lat)) * cos(radians(o.lat)) * power(sin(radians(o.lng - s.lng) / 2), 2))))::numeric, 3)::text
  from o join s on s.id = o.store_id where s.lat is not null and o.lat is not null
union all
select 'function', p.oid::regprocedure::text, pg_get_functiondef(p.oid)
  from pg_proc p join pg_namespace n on n.oid = p.pronamespace
 where n.nspname = 'public' and p.proname in ('dist_km', 'delivery_calc');
