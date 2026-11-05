-- PROPOSED safety fix. NOT APPLIED LIVE. No rate/policy changes; serialize existing cap and one-refund rules.
begin;
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
  select * into v_t from support_tickets where id = p_ticket for update;
  if not found then raise exception 'not_found'; end if;
  -- All refund tickets for an order share this row lock before reading its cap.
  -- Different tickets cannot both approve against the same old refund sum.
  if v_ref > 0 and v_t.order_id is not null then
    perform 1 from orders where id = v_t.order_id for update;
  end if;
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
end $function$
;

commit;
