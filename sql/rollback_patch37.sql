-- =============================================================================================
-- ROLLBACK of patch 37: restores the five functions EXACTLY as read live on 17 Oct (verify_batch3_readonly) and removes the new
-- helpers. The receipts table cash_settlements is KEPT (records of money received must not be lost); it is no longer used.
-- NOTE: after a rollback, amounts already received through patch 37 are not reflected by the old cash_balances (which only
-- knows orders marked settled): finance must mark those orders by hand or re-apply patch 37. Not run anywhere.
-- =============================================================================================
begin;
drop function if exists receive_driver_cash(uuid, numeric, text, text, text);
drop function if exists driver_cash_due(uuid);
drop function if exists ticket_refund_room(bigint);
-- live definition, read 17 Oct (owner postgres)
CREATE OR REPLACE FUNCTION public.deliver_order(p_id bigint, p_cash numeric DEFAULT NULL::numeric, p_note text DEFAULT NULL::text, p_photo text DEFAULT NULL::text)
 RETURNS void
 LANGUAGE plpgsql
 SECURITY DEFINER
 SET search_path TO 'public'
AS $function$
declare o orders; iscash boolean;
begin
  select * into o from orders where id = p_id for update;
  if not found then raise exception 'not_found'; end if;
  if o.driver_id is distinct from auth.uid() or o.status <> 'pickedup' then raise exception 'bad_transition'; end if;
  -- the photo must be in this courier's folder for this order: <courier id>/<order id>/<file>.jpg
  if p_photo is not null and p_photo !~ ('^' || auth.uid()::text || '/' || p_id::text || '/[A-Za-z0-9_-]{8,64}\.jpg$') then raise exception 'bad_value'; end if;
  if coalesce(o.leave_at_door, false) and p_photo is null then raise exception 'photo_required'; end if;
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
end $function$;

-- live definition, read 17 Oct (owner postgres)
CREATE OR REPLACE FUNCTION public.ticket_set_status(p_ticket bigint, p_status text, p_note text DEFAULT NULL::text, p_refund numeric DEFAULT NULL::numeric)
 RETURNS void
 LANGUAGE plpgsql
 SECURITY DEFINER
 SET search_path TO 'public'
AS $function$
declare v_t support_tickets; v_max numeric; v_cred numeric; v_prev numeric; v_ref numeric := case when p_refund is null then null else round(p_refund, 2) end;
begin
  if not has_perm('support') then raise exception 'not_allowed'; end if;
  if p_status not in ('open', 'in_progress', 'resolved', 'rejected') then raise exception 'bad_value'; end if;
  if p_status = 'rejected' and char_length(btrim(coalesce(p_note, ''))) < 3 then raise exception 'note_required'; end if;   -- the customer must be told why
  select * into v_t from support_tickets where id = p_ticket;
  if not found then raise exception 'not_found'; end if;
  select amount into v_cred from wallet_entries where ticket_id = p_ticket and kind = 'refund';
  if v_ref is not null then
    if p_status <> 'resolved' or v_ref < 0 then raise exception 'bad_value'; end if;
    if v_ref > 0 and v_cred is not null then raise exception 'already_refunded'; end if;   -- one refund per ticket
    if v_ref > 0 and v_t.order_id is null then raise exception 'refund_needs_order'; end if;  -- a refund needs an order to be measured against
    if v_t.order_id is not null then
      select total into v_max from orders where id = v_t.order_id;
      select coalesce(sum(amount), 0) into v_prev from wallet_entries where order_id = v_t.order_id and kind = 'refund';
      if v_ref + v_prev > coalesce(v_max, 0) then raise exception 'refund_too_high'; end if;   -- never more than the order was worth, over all its tickets
    end if;
  end if;
  update support_tickets set status = p_status,
         admin_note = nullif(left(btrim(coalesce(p_note, '')), 300), ''),
         refund_amount = coalesce(v_cred, case when p_status = 'resolved' and v_ref > 0 then v_ref end),
         updated_at = now(), last_staff_at = now(), handled_by = auth.uid(),
         closed_at = case when p_status in ('resolved', 'rejected') then now() else null end
   where id = p_ticket;
  -- the approved refund goes to the customer's wallet in the same moment (atomic with closing the ticket)
  if v_ref > 0 and v_cred is null then
    insert into wallet_entries(user_id, amount, kind, ticket_id, order_id, note, created_by)
    values (v_t.customer_id, v_ref, 'refund', p_ticket, v_t.order_id, left(coalesce(p_note, ''), 200), auth.uid());
  end if;
end $function$;

-- live definition, read 17 Oct (owner postgres)
CREATE OR REPLACE FUNCTION public.ticket_refund_room(p_ticket bigint)
 RETURNS TABLE(order_total numeric, refunded numeric, room numeric)
 LANGUAGE sql
 STABLE SECURITY DEFINER
 SET search_path TO 'public'
AS $function$
  select o.total,
         coalesce(w.sum_refunded, 0),
         greatest(0, o.total - coalesce(w.sum_refunded, 0))
    from support_tickets t
    join orders o on o.id = t.order_id
    left join lateral (select sum(x.amount) as sum_refunded from wallet_entries x where x.order_id = o.id and x.kind = 'refund') w on true
   where t.id = p_ticket and has_perm('support')
$function$;

-- live definition, read 17 Oct (owner postgres)
CREATE OR REPLACE FUNCTION public.cash_balances()
 RETURNS TABLE(driver_id uuid, balance numeric)
 LANGUAGE sql
 STABLE SECURITY DEFINER
 SET search_path TO 'public'
AS $function$
  select o.driver_id, coalesce(sum(o.cash_collected), 0)::numeric
    from orders o
   where o.status = 'delivered' and o.cash_collected is not null and o.cash_settled_at is null
     and o.driver_id is not null and (has_perm('finance') or o.driver_id = auth.uid())
   group by o.driver_id
$function$;

-- live definition, read 17 Oct (owner postgres)
CREATE OR REPLACE FUNCTION public.settle_driver_cash(p_driver uuid)
 RETURNS numeric
 LANGUAGE plpgsql
 SECURITY DEFINER
 SET search_path TO 'public'
AS $function$
declare tot numeric;
begin
  if not has_perm('finance') then raise exception 'not_allowed'; end if;
  select coalesce(sum(cash_collected), 0) into tot from orders
   where driver_id = p_driver and status = 'delivered' and cash_collected is not null and cash_settled_at is null;
  update orders set cash_settled_at = now()
   where driver_id = p_driver and status = 'delivered' and cash_collected is not null and cash_settled_at is null;
  return tot;
end $function$;
revoke all on function ticket_refund_room(bigint) from public, anon;
grant execute on function ticket_refund_room(bigint) to authenticated;
drop function if exists order_refund_cap(bigint);
drop function if exists proof_exists(text, uuid);
drop index if exists wallet_order_idx;
commit;
