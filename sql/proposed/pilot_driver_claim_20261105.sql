-- PROPOSED ONLY; serialize the existing one-active-order rule per driver. No live application.
begin;
CREATE OR REPLACE FUNCTION public.driver_accept(p_id bigint)
 RETURNS boolean
 LANGUAGE plpgsql
 SECURITY DEFINER
 SET search_path TO 'public'
AS $function$
declare v_id bigint; v_name text; v_blocked boolean; v_phone text;
begin
  select name, accept_blocked, phone into v_name, v_blocked, v_phone from profiles
   where id = auth.uid() and role = 'driver' and driver_status = 'approved' for update;
  if not found then raise exception 'not_approved'; end if;
  if v_blocked then raise exception 'blocked'; end if;
  if norm_phone(v_phone) is null then raise exception 'phone_required'; end if;
  if exists (select 1 from orders x where x.driver_id = auth.uid() and x.status in ('preparing', 'ready', 'pickedup')) then
    raise exception 'busy';
  end if;
  if not exists (select 1 from order_offers where order_id = p_id and driver_id = auth.uid() and state = 'pending' and expires_at > now()) then
    raise exception 'no_offer';
  end if;
  update orders set driver_id = auth.uid(), driver_name = v_name
   where id = p_id and driver_id is null and status in ('preparing', 'ready') returning id into v_id;
  if v_id is not null then
    update order_offers set state = case when driver_id = auth.uid() then 'accepted' else 'cancelled' end
     where order_id = p_id and state = 'pending';
    insert into order_driver_phone(order_id, phone) values (p_id, norm_phone(v_phone))
      on conflict (order_id) do update set phone = excluded.phone;
  end if;
  return v_id is not null;
end $function$
;
commit;
