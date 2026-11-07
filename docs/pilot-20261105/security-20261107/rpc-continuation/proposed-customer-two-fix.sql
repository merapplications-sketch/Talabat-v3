CREATE OR REPLACE FUNCTION public.rate_order(p_order bigint, p_store integer, p_driver integer, p_comment text DEFAULT NULL::text)
 RETURNS void
 LANGUAGE plpgsql
 SECURITY DEFINER
 SET search_path TO 'public'
AS $function$
declare o orders;
begin
  if not public.account_enabled() then raise exception 'account_blocked'; end if;
  if auth.uid() is null then raise exception 'auth'; end if;
  select * into o from orders where id = p_order and customer_id = auth.uid() and status = 'delivered';
  if not found then raise exception 'not_allowed'; end if;
  if (p_store is not null and p_store not between 1 and 5) or (p_driver is not null and p_driver not between 1 and 5)
     or (p_store is null and p_driver is null) then raise exception 'bad_value'; end if;
  if o.driver_id is null then p_driver := null; end if;
  insert into ratings(order_id, customer_id, store_id, driver_id, store_stars, driver_stars, comment)
  values (p_order, auth.uid(), o.store_id, o.driver_id, p_store, p_driver, nullif(left(btrim(coalesce(p_comment, '')), 300), ''));
exception when unique_violation then
  raise exception 'already_rated';
end $function$
;
CREATE OR REPLACE FUNCTION public.ticket_seen(p_ticket bigint)
 RETURNS void
 LANGUAGE plpgsql
 SECURITY DEFINER
 SET search_path TO 'public'
AS $function$
begin
  if not public.account_enabled() then raise exception 'account_blocked'; end if;
  if auth.uid() is null then raise exception 'auth'; end if;
  update support_tickets set customer_seen_at = now() where id = p_ticket and customer_id = auth.uid();
end $function$
;