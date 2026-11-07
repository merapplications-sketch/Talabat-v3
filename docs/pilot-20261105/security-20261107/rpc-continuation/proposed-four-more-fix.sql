CREATE OR REPLACE FUNCTION public.order_contacts(p_order bigint)
 RETURNS jsonb
 LANGUAGE plpgsql
 STABLE SECURITY DEFINER
 SET search_path TO 'public'
AS $function$
declare v_o orders; v_cp text; v_dp text; v_active boolean;
begin
  if not public.account_enabled() then raise exception 'account_blocked'; end if;
  if auth.uid() is null then raise exception 'auth'; end if;
  select * into v_o from orders where id = p_order;
  if not found then return '{}'::jsonb; end if;
  v_active := v_o.status in ('preparing', 'ready', 'pickedup');
  select phone into v_cp from order_customer_phone where order_id = p_order;
  select phone into v_dp from order_driver_phone where order_id = p_order;
  if (has_perm('orders') or has_perm('support')) then return jsonb_build_object('customer_phone', v_cp, 'driver_phone', v_dp); end if;
  return jsonb_build_object(
    'customer_phone', case when v_active and v_o.driver_id = auth.uid() then v_cp end,
    'driver_phone', case when v_active and v_o.driver_id is not null and (v_o.customer_id = auth.uid() or owns_store(v_o.store_id)) then v_dp end);
end $function$
;
CREATE OR REPLACE FUNCTION public.set_default_address(p_id uuid)
 RETURNS void
 LANGUAGE plpgsql
 SECURITY DEFINER
 SET search_path TO 'public'
AS $function$
begin
  if not public.account_enabled() then raise exception 'account_blocked'; end if;
  if auth.uid() is null then raise exception 'auth'; end if;
  if not exists (select 1 from addresses where id = p_id and user_id = auth.uid()) then raise exception 'not_allowed'; end if;
  update addresses set is_default = false where user_id = auth.uid() and is_default and id <> p_id;
  update addresses set is_default = true where id = p_id and user_id = auth.uid();
end $function$
;
CREATE OR REPLACE FUNCTION public.set_order_status(p_id bigint, p_to order_status)
 RETURNS void
 LANGUAGE plpgsql
 SECURITY DEFINER
 SET search_path TO 'public'
AS $function$
declare o orders; ok boolean := false;
begin
  if not public.account_enabled() then raise exception 'account_blocked'; end if;
  select * into o from orders where id = p_id for update;
  if not found then raise exception 'not_found'; end if;
  if is_admin() then ok := true;
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
end $function$
;
CREATE OR REPLACE FUNCTION public.store_private()
 RETURNS TABLE(id uuid, owner_id uuid, commission_pct numeric, max_discount_pct numeric)
 LANGUAGE sql
 STABLE SECURITY DEFINER
 SET search_path TO 'public'
AS $function$
  select s.id, s.owner_id, s.commission_pct, s.max_discount_pct
    from stores s where public.account_enabled() and (has_perm('stores') or s.owner_id = auth.uid())
$function$
;