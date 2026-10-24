-- PROPOSED patch 39 (batch C) — NOT applied. Apply only after owner approval AND only if verify_tracking_readonly.sql
-- shows no existing read path that already gives the customer this (then reuse it instead).
-- The customer of an order reads the LAST position of that order's courier, ONLY while the order is out for delivery
-- (status 'pickedup'); nothing before pickup, nothing after delivered / cancelled, no history, no other courier data.
-- Position source = what driver_location() already writes (profiles.lat/lng/loc_acc/loc_updated). No table change,
-- no realtime change (the app polls), no change to dispatch, accounts or finance. Safe to run again.
create or replace function public.order_courier_position(p_order bigint)
returns table (lat double precision, lng double precision, acc double precision, updated_at timestamptz)
language sql stable security definer
set search_path = public
as $$
  select p.lat, p.lng, p.loc_acc, p.loc_updated
  from public.orders o
  join public.profiles p on p.id = o.driver_id
  where o.id = p_order
    and o.customer_id = auth.uid()
    and o.status = 'pickedup'
    and p.lat is not null and p.lng is not null;
$$;
revoke all on function public.order_courier_position(bigint) from public, anon;
grant execute on function public.order_courier_position(bigint) to authenticated;

-- Test after applying (as the customer of a picked-up order): select * from order_courier_position(<order id>);
-- expected 1 row; for any other order / status / user: 0 rows. Rollback: drop function public.order_courier_position(bigint);
