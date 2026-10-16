-- =============================================================================================
-- OPTION (NOT part of patch 37, NOT applied, needs the owner's decision): an order that was DELIVERED can no longer be turned
-- into cancelled / rejected through set_order_status (today the admin can). Why: on such a change the automatic wallet return
-- pays the wallet part again on top of any support refund, and the recorded courier cash drops out of what he owes.
-- The only change against the live definition (read 17 Oct) is the admin line. Rollback: sql/rollback_option_no_cancel_after_delivery.sql
-- =============================================================================================
begin;
CREATE OR REPLACE FUNCTION public.set_order_status(p_id bigint, p_to order_status)
 RETURNS void
 LANGUAGE plpgsql
 SECURITY DEFINER
 SET search_path TO 'public'
AS $function$
declare o orders; ok boolean := false;
begin
  select * into o from orders where id = p_id for update;
  if not found then raise exception 'not_found'; end if;
  if is_admin() then ok := not (o.status = 'delivered' and p_to in ('cancelled', 'rejected'));   -- option: a delivered order stays delivered
  elsif has_perm('orders') and p_to in ('cancelled','rejected') then ok := o.status in ('pending','preparing','ready','pickedup');
  elsif o.customer_id = auth.uid() then ok := (o.status = 'pending' and p_to = 'cancelled');
  elsif owns_store(o.store_id) then
    ok := (o.status = 'pending' and p_to in ('preparing','rejected')) or (o.status = 'preparing' and p_to = 'ready');
    -- a scheduled order is prepared at most 60 minutes before its time (v51)
    if ok and p_to = 'preparing' and o.scheduled_for is not null and now() < o.scheduled_for - interval '60 minutes' then raise exception 'too_early'; end if;
  elsif o.driver_id = auth.uid() then
    ok := (o.status = 'ready' and p_to = 'pickedup');
  end if;
  if not ok then raise exception 'bad_transition'; end if;
  update orders set status = p_to,
    done_at = case when p_to in ('delivered','rejected','cancelled') then now() else null end where id = p_id;
end $function$;
commit;
