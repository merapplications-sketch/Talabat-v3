-- Patch 20: owner info for the admin, support reasons by order stage (message optional), customer phone change rules
-- Run once in Supabase SQL Editor AFTER patch 19, then upload the files. Safe to re-run.
--
-- ROW LEVEL SECURITY / PERMISSIONS
--   store_owner_info() : admin only (it returns the owner's name and email; the email lives in auth.users, which the browser cannot read).
--   profiles.phone_changed_at : written only by the trigger (the guard blocks any self-edit of it).
--   Customer phone change : refused while the customer has an active order, and at most once every 24 hours; a customer cannot erase
--       the number first to dodge the rule. Admin and server functions are not limited. Every change is written to the audit log.

------------------------------------------------------------------------------------------------
-- 1) WHO OWNS THIS RESTAURANT (shown on the admin store screen)
------------------------------------------------------------------------------------------------
create or replace function store_owner_info(p_store uuid) returns table(owner_id uuid, name text, email text)
language sql stable security definer set search_path = public as $$
  select p.id, p.name, u.email::text
    from stores s join profiles p on p.id = s.owner_id join auth.users u on u.id = p.id
   where s.id = p_store and is_admin()
$$;
revoke all on function store_owner_info(uuid) from public, anon;
grant execute on function store_owner_info(uuid) to authenticated;

------------------------------------------------------------------------------------------------
-- 2) SUPPORT: reasons depend on the stage of the order; the message is optional (required only for "other")
------------------------------------------------------------------------------------------------
create or replace function ticket_reason_ok(p_status text, p_reason text, p_has_order boolean) returns boolean
language sql immutable as $$
  select case
    when not p_has_order then p_reason in ('courier', 'restaurant', 'payment', 'other')
    when p_status in ('pending', 'preparing', 'ready', 'pickedup') then p_reason in ('late', 'courier', 'restaurant', 'payment', 'other')
    when p_status = 'delivered' then p_reason in ('not_delivered', 'wrong_order', 'missing_items', 'quality', 'late', 'courier', 'restaurant', 'payment', 'other')
    else p_reason in ('restaurant', 'payment', 'other')
  end
$$;
revoke execute on function ticket_reason_ok(text, text, boolean) from public, anon;
grant execute on function ticket_reason_ok(text, text, boolean) to authenticated;

create or replace function create_ticket(p_order bigint, p_reason text, p_message text) returns bigint
language plpgsql security definer set search_path = public as $$
declare v_o orders; v_id bigint; v_msg text := btrim(coalesce(p_message, ''));
begin
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
end $$;
revoke all on function create_ticket(bigint, text, text) from public, anon;
grant execute on function create_ticket(bigint, text, text) to authenticated;

-- rejecting a ticket now REQUIRES a comment (the customer sees why)
create or replace function ticket_set_status(p_ticket bigint, p_status text, p_note text default null, p_refund numeric default null) returns void
language plpgsql security definer set search_path = public as $$
declare v_t support_tickets; v_max numeric;
begin
  if not is_admin() then raise exception 'not_allowed'; end if;
  if p_status not in ('open', 'in_progress', 'resolved', 'rejected') then raise exception 'bad_value'; end if;
  if p_status = 'rejected' and char_length(btrim(coalesce(p_note, ''))) < 3 then raise exception 'note_required'; end if;   -- the customer must be told why
  select * into v_t from support_tickets where id = p_ticket;
  if not found then raise exception 'not_found'; end if;
  if p_refund is not null then
    if p_status <> 'resolved' or p_refund < 0 then raise exception 'bad_value'; end if;
    if v_t.order_id is not null then
      select total into v_max from orders where id = v_t.order_id;
      if p_refund > coalesce(v_max, 0) then raise exception 'bad_value'; end if;   -- never more than the order was worth
    end if;
  end if;
  update support_tickets set status = p_status,
         admin_note = nullif(left(btrim(coalesce(p_note, '')), 300), ''),
         refund_amount = case when p_status = 'resolved' then p_refund else null end,
         updated_at = now(), last_staff_at = now(), handled_by = auth.uid(),
         closed_at = case when p_status in ('resolved', 'rejected') then now() else null end
   where id = p_ticket;
end $$;
revoke all on function ticket_set_status(bigint, text, text, numeric) from public, anon;
grant execute on function ticket_set_status(bigint, text, text, numeric) to authenticated;

------------------------------------------------------------------------------------------------
-- 3) CUSTOMER PHONE: no change during an active order, once every 24 hours, always audited
------------------------------------------------------------------------------------------------
alter table profiles add column if not exists phone_changed_at timestamptz;

create or replace function guard_profile() returns trigger
language plpgsql security definer set search_path = public as $$
begin
  if auth.uid() is null or current_setting('app.bypass', true) = '1' or is_admin() then return new; end if;
  if new.role <> old.role or new.driver_status is distinct from old.driver_status
     or new.cash_limit <> old.cash_limit or new.accept_blocked <> old.accept_blocked
     or new.banned_at is distinct from old.banned_at or new.banned_reason is distinct from old.banned_reason
     or new.phone_changed_at is distinct from old.phone_changed_at then
    raise exception 'not_allowed';
  end if;
  return new;
end $$;

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
      if old.phone_changed_at is not null and old.phone_changed_at > now() - interval '24 hours' then
        raise exception 'phone_cooldown';
      end if;
      new.phone_changed_at := now();
    end if;
  end if;
  return new;
end $$;
drop trigger if exists trg_profile_phone on profiles;
create trigger trg_profile_phone before update of phone on profiles for each row execute function trg_profile_phone();

drop trigger if exists trg_audit_profiles on profiles;
create trigger trg_audit_profiles after update on profiles for each row
  execute function audit_changes('id', 'role', 'driver_status', 'cash_limit', 'accept_blocked', 'banned_at', 'banned_reason', 'phone');
