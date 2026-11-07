CREATE OR REPLACE FUNCTION public.active_contacts()
 RETURNS TABLE(order_id bigint, customer_phone text, driver_phone text)
 LANGUAGE sql
 STABLE SECURITY DEFINER
 SET search_path TO 'public'
AS $function$
  select o.id,
         case when o.driver_id = auth.uid() then cp.phone end,
         case when o.driver_id is not null and (o.customer_id = auth.uid() or owns_store(o.store_id)) then dp.phone end
    from orders o
    left join order_customer_phone cp on cp.order_id = o.id
    left join order_driver_phone dp on dp.order_id = o.id
   where public.account_enabled() and o.status in ('preparing', 'ready', 'pickedup')
     and (o.driver_id = auth.uid() or o.customer_id = auth.uid() or owns_store(o.store_id))
$function$
;
CREATE OR REPLACE FUNCTION public.can_see_order(o bigint)
 RETURNS boolean
 LANGUAGE sql
 STABLE SECURITY DEFINER
 SET search_path TO 'public'
AS $function$ select public.account_enabled() and exists(select 1 from orders r where r.id = o and (
     r.customer_id = auth.uid() or r.driver_id = auth.uid() or owns_store(r.store_id) or (has_perm('orders') or has_perm('support'))
     or (r.driver_id is null and r.status in ('preparing', 'ready') and exists(
          select 1 from order_offers f where f.order_id = r.id and f.driver_id = auth.uid()
             and f.state = 'pending' and f.expires_at > now())))) $function$
;
CREATE OR REPLACE FUNCTION public.driver_arrived(p_id bigint, p_where text)
 RETURNS void
 LANGUAGE plpgsql
 SECURITY DEFINER
 SET search_path TO 'public'
AS $function$
declare o orders;
begin
  if not public.account_enabled() then raise exception 'account_blocked'; end if;
  select * into o from orders where id = p_id for update;
  if not found then raise exception 'not_found'; end if;
  if o.driver_id is distinct from auth.uid() then raise exception 'not_allowed'; end if;
  if p_where = 'store' then
    if o.status not in ('preparing', 'ready') then raise exception 'bad_transition'; end if;
    update orders set arrived_store_at = coalesce(arrived_store_at, now()) where id = p_id;
  elsif p_where = 'customer' then
    if o.status <> 'pickedup' then raise exception 'bad_transition'; end if;
    update orders set arrived_cust_at = coalesce(arrived_cust_at, now()) where id = p_id;
  else
    raise exception 'bad_value';
  end if;
  -- also in the order timeline when the existing events table accepts it (its kinds are not known here)
  begin
    insert into order_events(order_id, kind) values (p_id, case p_where when 'store' then 'at_store' else 'at_customer' end);
  exception when others then null;
  end;
end $function$
;
CREATE OR REPLACE FUNCTION public.group_create(p_store uuid)
 RETURNS jsonb
 LANGUAGE plpgsql
 SECURITY DEFINER
 SET search_path TO 'public'
AS $function$
declare v_id uuid;
begin
  if not public.account_enabled() then raise exception 'account_blocked'; end if;
  if auth.uid() is null then raise exception 'auth'; end if;
  if not exists (select 1 from stores where id = p_store and is_active) then raise exception 'store_unavailable'; end if;
  if (select count(*) from group_orders where host_id = auth.uid() and created_at > now() - interval '1 day') >= 10 then raise exception 'too_many'; end if;
  update group_orders set status = 'cancelled' where host_id = auth.uid() and status in ('open', 'closed');   -- one open group per host
  insert into group_orders(store_id, host_id) values (p_store, auth.uid()) returning id into v_id;
  return group_json(v_id);
end $function$
;
CREATE OR REPLACE FUNCTION public.wallet_balance(p_user uuid DEFAULT NULL::uuid)
 RETURNS numeric
 LANGUAGE sql
 STABLE SECURITY DEFINER
 SET search_path TO 'public'
AS $function$
  select coalesce(sum(w.amount), 0)::numeric
    from wallet_entries w
   where public.account_enabled() and w.user_id = coalesce(p_user, auth.uid())
     and (coalesce(p_user, auth.uid()) = auth.uid() or (has_perm('support') or has_perm('finance')))
$function$
;
CREATE OR REPLACE FUNCTION public.order_return_status(p_order bigint)
 RETURNS jsonb
 LANGUAGE plpgsql
 STABLE SECURITY DEFINER
 SET search_path TO ''
AS $function$
declare
  v_actor uuid := auth.uid();
  o public.orders;
  result jsonb;
begin
  if not public.account_enabled() then raise exception 'account_blocked'; end if;
  select * into o from public.orders where id = p_order;
  if v_actor is null or not found or not (
    v_actor = o.customer_id or v_actor is not distinct from o.driver_id
    or public.owns_store(o.store_id) or public.has_perm('orders')
  ) then raise exception 'not_allowed'; end if;
  result := coalesce(return_private.view_case(p_order, v_actor = o.customer_id), '{}'::jsonb);
  return result || jsonb_build_object('order_status', o.status,
    'can_document_departure', v_actor is not distinct from o.driver_id and o.status = 'pickedup'
      and o.payment = 'cash' and exists (
        select 1 from (
          select active from return_private.agreements
          where store_id = o.store_id and recorded_at < o.created_at
          order by recorded_at desc, id desc limit 1
        ) a where a.active
      ));
end $function$
;
CREATE POLICY pilot_active_account ON public.profiles AS RESTRICTIVE FOR ALL TO authenticated USING (public.account_enabled()) WITH CHECK (public.account_enabled());
CREATE POLICY pilot_active_account ON public.wallet_entries AS RESTRICTIVE FOR ALL TO authenticated USING (public.account_enabled()) WITH CHECK (public.account_enabled());

CREATE OR REPLACE FUNCTION public.create_ticket(p_order bigint, p_reason text, p_message text)
 RETURNS bigint
 LANGUAGE plpgsql
 SECURITY DEFINER
 SET search_path TO 'public'
AS $function$
declare v_o orders; v_id bigint; v_msg text := btrim(coalesce(p_message, ''));
begin
  if not public.account_enabled() then raise exception 'account_blocked'; end if;
  if auth.uid() is null then raise exception 'auth'; end if;
  if p_reason is null or p_reason not in ('not_delivered', 'wrong_order', 'missing_items', 'quality', 'late', 'courier', 'restaurant', 'payment', 'other') then
    raise exception 'bad_value';
  end if;
  -- the message is optional when a reason is chosen; only "other" needs a real description
  if char_length(v_msg) < (case when p_reason = 'other' then 5 else 1 end) or char_length(v_msg) > 500 then raise exception 'bad_value'; end if;
  if (select count(*) from support_tickets where customer_id = auth.uid() and status in ('open', 'in_progress')) >= 5
     or (select count(*) from support_tickets where customer_id = auth.uid() and created_at > now() - interval '1 day') >= 10 then
    raise exception 'too_many';
  end if;
  if p_order is not null then
    select * into v_o from orders where id = p_order and customer_id = auth.uid();
    if not found then raise exception 'not_allowed'; end if;
    if v_o.status in ('delivered', 'rejected', 'cancelled') and coalesce(v_o.done_at, v_o.created_at) < now() - interval '48 hours' then
      raise exception 'ticket_expired';                    -- reports are accepted for 48 hours after the order ends
    end if;
    if not ticket_reason_ok(v_o.status::text, p_reason, true) then raise exception 'bad_value'; end if;   -- reasons must fit the stage of the order
  elsif not ticket_reason_ok('', p_reason, false) then
    raise exception 'bad_value';
  end if;
  begin
    insert into support_tickets(customer_id, order_id, reason) values (auth.uid(), p_order, p_reason) returning id into v_id;
  exception when unique_violation then
    raise exception 'ticket_exists';                       -- one open ticket per order
  end;
  insert into ticket_messages(ticket_id, from_staff, sender_id, body) values (v_id, false, auth.uid(), v_msg);
  return v_id;
end $function$
;
CREATE OR REPLACE FUNCTION public.ticket_reply(p_ticket bigint, p_body text)
 RETURNS void
 LANGUAGE plpgsql
 SECURITY DEFINER
 SET search_path TO 'public'
AS $function$
declare v_t support_tickets; v_body text := btrim(coalesce(p_body, ''));
begin
  if not public.account_enabled() then raise exception 'account_blocked'; end if;
  if auth.uid() is null then raise exception 'auth'; end if;
  if char_length(v_body) < 1 or char_length(v_body) > 500 then raise exception 'bad_value'; end if;
  select * into v_t from support_tickets where id = p_ticket and customer_id = auth.uid();
  if not found then raise exception 'not_allowed'; end if;
  if v_t.status in ('resolved', 'rejected') then raise exception 'ticket_closed'; end if;
  if (select count(*) from ticket_messages where ticket_id = p_ticket and sender_id = auth.uid() and created_at > now() - interval '1 hour') >= 20 then
    raise exception 'too_many';
  end if;
  insert into ticket_messages(ticket_id, from_staff, sender_id, body) values (p_ticket, false, auth.uid(), v_body);
  update support_tickets set updated_at = now(), last_customer_at = now(), customer_seen_at = now() where id = p_ticket;
end $function$
;
CREATE POLICY pilot_active_account ON public.addresses AS RESTRICTIVE FOR ALL TO authenticated USING (public.account_enabled()) WITH CHECK (public.account_enabled());
CREATE POLICY pilot_active_account ON public.favorites AS RESTRICTIVE FOR ALL TO authenticated USING (public.account_enabled()) WITH CHECK (public.account_enabled());
CREATE POLICY pilot_active_account ON public.loyalty_lots AS RESTRICTIVE FOR ALL TO authenticated USING (public.account_enabled()) WITH CHECK (public.account_enabled());
CREATE POLICY pilot_active_account ON public.loyalty_ledger AS RESTRICTIVE FOR ALL TO authenticated USING (public.account_enabled()) WITH CHECK (public.account_enabled());
CREATE POLICY pilot_active_account ON public.support_tickets AS RESTRICTIVE FOR ALL TO authenticated USING (public.account_enabled()) WITH CHECK (public.account_enabled());
CREATE POLICY pilot_active_account ON public.ticket_messages AS RESTRICTIVE FOR ALL TO authenticated USING (public.account_enabled()) WITH CHECK (public.account_enabled());
CREATE OR REPLACE FUNCTION public.deliver_order(p_id bigint, p_cash numeric DEFAULT NULL::numeric, p_note text DEFAULT NULL::text, p_photo text DEFAULT NULL::text)
 RETURNS void
 LANGUAGE plpgsql
 SECURITY DEFINER
 SET search_path TO 'public'
AS $function$
declare o orders; iscash boolean;
begin
  if not public.account_enabled() then raise exception 'account_blocked'; end if;
  select * into o from orders where id = p_id for update;
  if not found then raise exception 'not_found'; end if;
  if o.driver_id is distinct from auth.uid() or o.status <> 'pickedup' then raise exception 'bad_transition'; end if;
  -- the photo must be in this courier's folder for this order: <courier id>/<order id>/<file>.jpg
  if p_photo is not null and p_photo !~ ('^' || auth.uid()::text || '/' || p_id::text || '/[A-Za-z0-9_-]{8,64}\.jpg$') then raise exception 'bad_value'; end if;
  if coalesce(o.leave_at_door, false) and p_photo is null then raise exception 'photo_required'; end if;
  -- A well-shaped path is not evidence of a stored proof. Preserve optional
  -- photos: resolve Storage only inside this branch; never block photo-less cash.
  if p_photo is not null then
    if to_regclass('storage.objects') is null then raise exception 'photo_service_unavailable'; end if;
    perform 1 from storage.objects where bucket_id = 'proofs' and name = p_photo for key share;
    if not found then raise exception 'photo_not_found'; end if;
  end if;
  iscash := o.payment ~ '^(cash|Cash|Наличн)';
  if iscash then
    if p_cash is null or p_cash < 0 then raise exception 'cash_required'; end if;
    if p_cash <> (o.total - coalesce(o.wallet_used, 0)) and coalesce(trim(p_note), '') = '' then raise exception 'note_required'; end if;
  end if;
  update orders set status = 'delivered', done_at = now(),
    cash_collected = case when iscash then p_cash end,
    cash_note = case when iscash then left(p_note, 200) end,
    delivery_photo = p_photo,
    arrived_cust_at = coalesce(arrived_cust_at, now())
  where id = p_id;
end $function$
;