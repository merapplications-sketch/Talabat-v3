CREATE OR REPLACE FUNCTION public.driver_accept(p_id bigint)
 RETURNS boolean
 LANGUAGE plpgsql
 SECURITY DEFINER
 SET search_path TO 'public'
AS $function$
declare v_id bigint; v_name text; v_blocked boolean; v_phone text;
begin
  if not public.account_enabled() then raise exception 'account_blocked'; end if;
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
CREATE OR REPLACE FUNCTION public.driver_decline(p_id bigint)
 RETURNS void
 LANGUAGE plpgsql
 SECURITY DEFINER
 SET search_path TO 'public'
AS $function$
begin
  if not public.account_enabled() then raise exception 'account_blocked'; end if;
  if auth.uid() is null then raise exception 'auth'; end if;
  update order_offers set state = 'declined' where order_id = p_id and driver_id = auth.uid() and state = 'pending';
  if found then perform dispatch_next(p_id); end if;
end $function$
;
CREATE OR REPLACE FUNCTION public.group_add(p_id uuid, p_item uuid, p_qty integer, p_options jsonb DEFAULT '[]'::jsonb, p_note text DEFAULT NULL::text)
 RETURNS jsonb
 LANGUAGE plpgsql
 SECURITY DEFINER
 SET search_path TO 'public'
AS $function$
declare g group_orders; v_name text;
begin
  if not public.account_enabled() then raise exception 'account_blocked'; end if;
  if auth.uid() is null then raise exception 'auth'; end if;
  select * into g from group_orders where id = p_id for update;
  if not found or g.status <> 'open' or g.expires_at < now() then raise exception 'group_closed'; end if;
  if p_qty is null or p_qty not between 1 and 20 then raise exception 'bad_value'; end if;
  if not exists (select 1 from menu_items where id = p_item and store_id = g.store_id and available and approved) then raise exception 'unavailable'; end if;
  perform price_line(p_item, coalesce(p_options, '[]'::jsonb));          -- the same option rules as a normal order
  if (select count(*) from group_items where group_id = p_id) >= 60 or (select count(*) from group_items where group_id = p_id and user_id = auth.uid()) >= 20 then
    raise exception 'too_many';
  end if;
  select coalesce(nullif(btrim(name), ''), 'Гость') into v_name from profiles where id = auth.uid();
  insert into group_items(group_id, user_id, user_name, item_id, qty, options, note)
  values (p_id, auth.uid(), left(v_name, 40), p_item, p_qty, coalesce(p_options, '[]'::jsonb), nullif(left(btrim(coalesce(p_note, '')), 120), ''));
  return group_json(p_id);
end $function$
;
CREATE OR REPLACE FUNCTION public.group_get(p_id uuid)
 RETURNS jsonb
 LANGUAGE plpgsql
 SECURITY DEFINER
 SET search_path TO 'public'
AS $function$
begin
  if not public.account_enabled() then raise exception 'account_blocked'; end if;
  if auth.uid() is null then raise exception 'auth'; end if;
  update group_orders set status = 'cancelled' where id = p_id and status = 'open' and expires_at < now();
  return group_json(p_id);
end $function$
;
CREATE OR REPLACE FUNCTION public.group_remove(p_line bigint)
 RETURNS jsonb
 LANGUAGE plpgsql
 SECURITY DEFINER
 SET search_path TO 'public'
AS $function$
declare v_g uuid;
begin
  if not public.account_enabled() then raise exception 'account_blocked'; end if;
  select i.group_id into v_g from group_items i join group_orders g on g.id = i.group_id
   where i.id = p_line and g.status = 'open' and (i.user_id = auth.uid() or g.host_id = auth.uid());
  if v_g is null then raise exception 'not_allowed'; end if;
  delete from group_items where id = p_line;
  return group_json(v_g);
end $function$
;
CREATE OR REPLACE FUNCTION public.group_set(p_id uuid, p_status text)
 RETURNS jsonb
 LANGUAGE plpgsql
 SECURITY DEFINER
 SET search_path TO 'public'
AS $function$
begin
  if not public.account_enabled() then raise exception 'account_blocked'; end if;
  if p_status not in ('open', 'closed', 'cancelled') then raise exception 'bad_value'; end if;
  update group_orders set status = p_status, closed_at = case when p_status = 'closed' then now() else closed_at end,
         expires_at = case when p_status = 'open' then greatest(expires_at, now() + interval '1 hour') else expires_at end
   where id = p_id and host_id = auth.uid() and status in ('open', 'closed');
  if not found then raise exception 'not_allowed'; end if;
  return group_json(p_id);
end $function$
;
CREATE OR REPLACE FUNCTION public.my_offers()
 RETURNS TABLE(order_id bigint, mode text, rank integer, dist_km numeric, secs_left integer)
 LANGUAGE sql
 STABLE SECURITY DEFINER
 SET search_path TO 'public'
AS $function$
  select f.order_id, f.mode, f.rank, f.dist_km, greatest(0, extract(epoch from (f.expires_at - now()))::int)
    from order_offers f join orders o on o.id = f.order_id
   where public.account_enabled() and f.driver_id = auth.uid() and f.state = 'pending' and f.expires_at > now()
     and o.driver_id is null and o.status in ('preparing', 'ready')
   order by f.offered_at
$function$
;
CREATE OR REPLACE FUNCTION public.my_rating()
 RETURNS jsonb
 LANGUAGE sql
 STABLE SECURITY DEFINER
 SET search_path TO 'public'
AS $function$
  select jsonb_build_object('avg', round(avg(driver_stars)::numeric, 1), 'count', count(driver_stars))
    from ratings where public.account_enabled() and driver_id = auth.uid()
$function$
;
CREATE OR REPLACE FUNCTION public.request_store(p_name text, p_category text, p_phone text, p_address text, p_lat double precision, p_lng double precision, p_note text DEFAULT NULL::text)
 RETURNS uuid
 LANGUAGE plpgsql
 SECURITY DEFINER
 SET search_path TO 'public'
AS $function$
declare v_id uuid; v_ph text := norm_phone(p_phone); v_name text := btrim(coalesce(p_name, ''));
begin
  if not public.account_enabled() then raise exception 'account_blocked'; end if;
  if auth.uid() is null then raise exception 'auth'; end if;
  if not exists (select 1 from profiles where id = auth.uid() and role = 'merchant') then raise exception 'not_allowed'; end if;
  if char_length(v_name) < 2 or char_length(v_name) > 80 or p_category not in ('rest','grocery','pharmacy','beauty','flowers','gifts','shops','sweets') then raise exception 'bad_value'; end if;
  if v_ph is null then raise exception 'bad_phone'; end if;
  if p_lat is null or p_lng is null or p_lat not between -90 and 90 or p_lng not between -180 and 180 then raise exception 'bad_value'; end if;
  if char_length(coalesce(p_address, '')) > 200 or char_length(coalesce(p_note, '')) > 500 then raise exception 'bad_value'; end if;
  if (select count(*) from store_requests where user_id = auth.uid() and status = 'pending') >= 3
     or (select count(*) from store_requests where user_id = auth.uid() and created_at > now() - interval '1 day') >= 5 then
    raise exception 'too_many';
  end if;
  insert into store_requests(user_id, name, category, phone, address, lat, lng, note)
  values (auth.uid(), v_name, p_category, v_ph, nullif(btrim(coalesce(p_address, '')), ''), p_lat, p_lng, nullif(btrim(coalesce(p_note, '')), ''))
  returning id into v_id;
  return v_id;
end $function$
;
CREATE OR REPLACE FUNCTION public.set_my_free_delivery(p_store uuid, p_min numeric)
 RETURNS void
 LANGUAGE plpgsql
 SECURITY DEFINER
 SET search_path TO 'public'
AS $function$
begin
  if not public.account_enabled() then raise exception 'account_blocked'; end if;
  if not exists (select 1 from stores where id = p_store and owner_id = auth.uid()) then raise exception 'not_allowed'; end if;
  if p_min is null or p_min not between 0 and 100000 then raise exception 'bad_value'; end if;
  update stores set free_delivery_min = round(p_min, 2) where id = p_store;
end $function$
;