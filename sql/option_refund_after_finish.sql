-- =============================================================================================
-- OPTION (proposal, NOT approved, NOT part of patch 37): a support refund only after the order ended («order_not_finished»).
-- Needs patch 37. The only change against patch 37's ticket_set_status is the marked line.
-- Rollback (back to patch 37's version): sql/rollback_option_refund_after_finish.sql. Not run anywhere.
-- =============================================================================================
begin;
create or replace function ticket_set_status(p_ticket bigint, p_status text, p_note text default null, p_refund numeric default null) returns void
language plpgsql security definer set search_path = public as $$
declare v_t support_tickets; v_room numeric; v_cred numeric; v_ref numeric := case when p_refund is null then null else round(p_refund, 2) end;
begin
  if not has_perm('support') then raise exception 'not_allowed'; end if;
  if p_status not in ('open', 'in_progress', 'resolved', 'rejected') then raise exception 'bad_value'; end if;
  if p_status = 'rejected' and char_length(btrim(coalesce(p_note, ''))) < 3 then raise exception 'note_required'; end if;   -- the customer must be told why
  select * into v_t from support_tickets where id = p_ticket for update;          -- patch 37: one decision at a time per ticket
  if not found then raise exception 'not_found'; end if;
  select amount into v_cred from wallet_entries where ticket_id = p_ticket and kind = 'refund';
  if v_ref is not null then
    if p_status <> 'resolved' or v_ref < 0 then raise exception 'bad_value'; end if;
    if v_ref > 0 and v_cred is not null then raise exception 'already_refunded'; end if;   -- one refund per ticket
    if v_ref > 0 and v_t.order_id is null then raise exception 'refund_needs_order'; end if;  -- a refund needs an order to be measured against
    if v_ref > 0 then
      -- patch 37: lock the order (a cancel and its automatic wallet return update this row too), then measure against PROVEN payment
      perform 1 from orders where id = v_t.order_id for update;
      -- option: a refund only after the order ended (a refund + the automatic return of a later cancel would pay the wallet part twice)
      if (select status from orders where id = v_t.order_id) not in ('delivered', 'rejected', 'cancelled') then raise exception 'order_not_finished'; end if;
      select c.room into v_room from order_refund_cap(v_t.order_id) c;
      if v_ref > coalesce(v_room, 0) then raise exception 'refund_too_high'; end if;
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
end $$;
commit;
