CREATE OR REPLACE FUNCTION public.apply_as_driver()
 RETURNS void
 LANGUAGE plpgsql
 SECURITY DEFINER
 SET search_path TO 'public'
AS $function$
begin
  if not public.account_enabled() then raise exception 'account_blocked'; end if;
  perform set_config('app.bypass', '1', true);
  update profiles set role = 'driver', driver_status = 'pending' where id = auth.uid() and role = 'customer';
end $function$;

CREATE OR REPLACE FUNCTION public.loyalty_summary()
 RETURNS jsonb
 LANGUAGE sql
 STABLE SECURITY DEFINER
 SET search_path TO 'public'
AS $function$
  select jsonb_build_object(
    'balance', loyalty_balance(auth.uid()),
    'next_exp_at', (select min(expires_at) from loyalty_lots where user_id = auth.uid() and points_left > 0 and expires_at > now()),
    'next_exp_pts', (select coalesce(sum(points_left), 0) from loyalty_lots where user_id = auth.uid() and points_left > 0 and expires_at > now()
                       and expires_at < (select min(expires_at) from loyalty_lots where user_id = auth.uid() and points_left > 0 and expires_at > now()) + interval '1 day'),
    'earn_per_tjs', loyalty_setting('loyalty_earn_per_tjs'), 'points_per_tjs', loyalty_setting('loyalty_points_per_tjs'),
    'min_redeem', loyalty_setting('loyalty_min_redeem'), 'expiry_days', loyalty_setting('loyalty_expiry_days'), 'cashback_pct', loyalty_setting('cashback_pct'),
    'voucher_points', loyalty_setting('loyalty_voucher_points'), 'min_order', loyalty_setting('loyalty_min_order'), 'rate_reward', loyalty_setting('loyalty_rate_reward'))
  where public.account_enabled()
$function$;

CREATE OR REPLACE FUNCTION public.order_courier_position(p_order bigint)
 RETURNS TABLE(lat double precision, lng double precision, acc double precision, updated_at timestamp with time zone)
 LANGUAGE sql
 STABLE SECURITY DEFINER
 SET search_path TO 'public'
AS $function$
  select p.lat, p.lng, p.loc_acc, p.loc_updated
  from public.orders o
  join public.profiles p on p.id = o.driver_id
  where public.account_enabled() and o.id = p_order
    and o.customer_id = auth.uid()
    and o.status = 'pickedup'
    and p.lat is not null and p.lng is not null;
$function$
;
