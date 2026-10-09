-- Patch 24: precise refund errors + refunds only for tickets with an order, phone change once every 30 days, admin can change a customer's phone
-- Run once in Supabase SQL Editor AFTER patch 23. Safe to re-run.
--
-- ROW LEVEL SECURITY / PERMISSIONS
--   ticket_refund_room() and admin_set_customer_phone() : admin only (they return nothing / refuse for everybody else).

------------------------------------------------------------------------------------------------
-- 1) REFUNDS
------------------------------------------------------------------------------------------------
-- how much can still be refunded on the order of a ticket (so the admin screen can show the maximum)
create or replace function ticket_refund_room(p_ticket bigint) returns table(order_total numeric, refunded numeric, room numeric)
language sql stable security definer set search_path = public as $$
  select o.total,
         coalesce(w.sum_refunded, 0),
         greatest(0, o.total - coalesce(w.sum_refunded, 0))
    from support_tickets t
    join orders o on o.id = t.order_id
    left join lateral (select sum(x.amount) as sum_refunded from wallet_entries x where x.order_id = o.id and x.kind = 'refund') w on true
   where t.id = p_ticket and is_admin()
$$;
revoke all on function ticket_refund_room(bigint) from public, anon;
grant execute on function ticket_refund_room(bigint) to authenticated;

-- same function as patch 21, with two precise errors instead of "bad_value":
--   refund_needs_order : a refund on a ticket that has no order
--   refund_too_high    : more than the order was worth (counting what was already refunded on it)
create or replace function ticket_set_status(p_ticket bigint, p_status text, p_note text default null, p_refund numeric default null) returns void
language plpgsql security definer set search_path = public as $$
declare v_t support_tickets; v_max numeric; v_cred numeric; v_prev numeric; v_ref numeric := case when p_refund is null then null else round(p_refund, 2) end;
begin
  if not is_admin() then raise exception 'not_allowed'; end if;
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
end $$;
revoke all on function ticket_set_status(bigint, text, text, numeric) from public, anon;
grant execute on function ticket_set_status(bigint, text, text, numeric) to authenticated;

------------------------------------------------------------------------------------------------
-- 2) CUSTOMER PHONE: once every 30 days (was 24 hours); same rules as patch 23 otherwise
------------------------------------------------------------------------------------------------
create or replace function trg_profile_phone() returns trigger language plpgsql set search_path = public as $$
declare v_p text;
  -- NULL-safe on purpose: current_setting(..., true) is NULL when the setting was never set, and (false OR NULL OR false) is NULL,
  -- which made "not v_free" NULL and silently switched every rule below OFF.
  v_free boolean := (auth.uid() is null) or (coalesce(current_setting('app.bypass', true), '') = '1') or coalesce(is_admin(), false);
begin
  if new.phone is distinct from old.phone then
    if new.phone is null or btrim(new.phone) = '' then
      if old.phone is not null and not v_free then raise exception 'bad_phone'; end if;   -- cannot erase the number to dodge the rules
      new.phone := null; return new;
    end if;
    v_p := norm_phone(new.phone);
    if v_p is null then raise exception 'bad_phone'; end if;
    new.phone := v_p;
    if v_p is distinct from old.phone and old.phone is not null and not v_free and new.role = 'customer' then
      if exists (select 1 from orders where customer_id = new.id and status in ('pending', 'preparing', 'ready', 'pickedup')) then
        raise exception 'phone_locked';
      end if;
      if old.phone_changed_at is not null and old.phone_changed_at > now() - interval '30 days' then
        raise exception 'phone_cooldown';
      end if;
      new.phone_changed_at := now();
    end if;
  end if;
  return new;
end $$;
drop trigger if exists trg_profile_phone on profiles;
create trigger trg_profile_phone before update of phone on profiles for each row execute function trg_profile_phone();

-- the administrator changes a customer's phone (lost SIM, etc.): always possible, with a mandatory reason that goes to the audit log
create or replace function admin_set_customer_phone(p_user uuid, p_phone text, p_reason text) returns void
language plpgsql security definer set search_path = public as $$
declare v_p text := norm_phone(p_phone); v_why text := btrim(coalesce(p_reason, ''));
begin
  if not is_admin() then raise exception 'not_allowed'; end if;
  if v_p is null then raise exception 'bad_phone'; end if;
  if char_length(v_why) < 3 or char_length(v_why) > 200 then raise exception 'note_required'; end if;
  perform 1 from profiles where id = p_user and role = 'customer' for update;
  if not found then raise exception 'not_found'; end if;
  update profiles set phone = v_p where id = p_user;      -- the trigger lets the admin through and logs the change (from / to)
  insert into audit_log(user_id, action, table_name, row_id, details)
  values (auth.uid(), 'ADMIN_SET_PHONE', 'profiles', p_user::text, jsonb_build_object('reason', v_why));
end $$;
revoke all on function admin_set_customer_phone(uuid, text, text) from public, anon;
grant execute on function admin_set_customer_phone(uuid, text, text) to authenticated;
