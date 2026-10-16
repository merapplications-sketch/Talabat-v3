-- =============================================================================================
-- PATCH 37 — delivery proof, support refunds, courier cash receipts. PREPARED LOCALLY, NOT APPLIED ANYWHERE.
-- Base: the live definitions read on 17 Oct (verify_batch3_readonly). Rollback: sql/rollback_patch37.sql.
-- Unchanged on purpose: delivery conditions and permissions, one refund per ticket, the courier cash limit (it still only
-- concerns new orders: accept_blocked / eligible_couriers are not touched), points policy, cancellation responsibility.
--
-- 1) PROOF (UAT005): deliver_order also requires that the photo really exists NOW in the private bucket «proofs», at the
--    allowed path <courier>/<order>/<file>.jpg, uploaded by this courier, a finished upload (size known), not archived / deleted.
-- 2) REFUNDS: one rule for ticket_refund_room and ticket_set_status (order_refund_cap):
--      proven paid = wallet money spent on the order and not given back (spend + automatic return, from the wallet ledger)
--                  + cash the courier RECORDED (delivered orders only, never more than the cash part of the order)
--      card / Apple Pay without a capture record, uncollected cash and points are NOT counted as paid
--      room = proven paid − support refunds already made on the order; 0 while the order is still in progress
--      (refund only after it ends: otherwise a refund + the automatic return on a later cancel would pay the wallet part twice)
--    ticket_set_status locks the ticket and the ORDER row before the check: two tickets of one order, and a cancel (whose
--    wallet return trigger updates the same order row) can no longer pass the cap at the same moment. One refund per
--    ticket stays (unique index + check). Exceptional compensation is NOT created here (wallet_adjust stays as it is).
-- 3) CASH: a permanent receipt record (cash_settlements) and receive_driver_cash(): any positive amount up to what the
--    courier owes, under a lock on the courier, idempotent per client key. MODEL UNDER REVIEW — «running balance»:
--      owed = recorded cash of delivered orders not marked by the old full settlement − receipts recorded here.
--    No per-order allocation is made (see BATCH3-PLAN.md for the alternatives). settle_driver_cash(p_driver) keeps its
--    signature (old admin screens) and now records ONE receipt of the full amount owed instead of marking orders.
-- 4) Support refunds per order are read by the app with the existing RLS (wallet_read: own rows); an index on order_id.
-- =============================================================================================
begin;

-- ---------- 1) proof photo ----------
create or replace function proof_exists(p_path text, p_driver uuid) returns boolean
language sql stable security definer set search_path = public, storage as $$
  select exists (
    select 1 from storage.objects s
     where s.bucket_id = 'proofs' and s.name = p_path
       and (s.owner = p_driver or s.owner_id = p_driver::text)
       and s.archived_at is null and not coalesce(s.is_delete_marker, false)
       and coalesce((s.metadata->>'size')::bigint, 0) between 1 and 1048576
       and coalesce(s.metadata->>'mimetype', 'image/jpeg') = 'image/jpeg')
$$;
revoke all on function proof_exists(text, uuid) from public, anon, authenticated;

create or replace function deliver_order(p_id bigint, p_cash numeric default null, p_note text default null, p_photo text default null) returns void
language plpgsql security definer set search_path = public as $$
declare o orders; iscash boolean;
begin
  select * into o from orders where id = p_id for update;
  if not found then raise exception 'not_found'; end if;
  if o.driver_id is distinct from auth.uid() or o.status <> 'pickedup' then raise exception 'bad_transition'; end if;
  -- the photo must be in this courier's folder for this order: <courier id>/<order id>/<file>.jpg
  if p_photo is not null and p_photo !~ ('^' || auth.uid()::text || '/' || p_id::text || '/[A-Za-z0-9_-]{8,64}\.jpg$') then raise exception 'bad_value'; end if;
  -- … and it must really be there now, uploaded by this courier (patch 37)
  if p_photo is not null and not proof_exists(p_photo, auth.uid()) then raise exception 'photo_missing'; end if;
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
end $$;

-- ---------- 2) refunds: one cap ----------
create or replace function order_refund_cap(p_order bigint)
returns table(paid_wallet numeric, paid_cash numeric, unproven numeric, refunded numeric, room numeric)
language sql stable security definer set search_path = public as $$
  with o as (select * from orders where id = p_order),
  w as (select coalesce(sum(amount) filter (where kind in ('spend', 'return')), 0) as net_wallet,
               coalesce(sum(amount) filter (where kind = 'refund'), 0) as refunded
          from wallet_entries where order_id = p_order),
  p as (select greatest(0, -w.net_wallet) as pw,
               case when o.status = 'delivered' and o.cash_collected is not null
                    then greatest(0, least(o.cash_collected, o.total - coalesce(o.wallet_used, 0))) else 0 end as pc,
               w.refunded as rf, o.total as total, coalesce(o.wallet_used, 0) as wu
          from o, w)
  select round(pw, 2), round(pc, 2), round(greatest(0, total - wu - pc), 2), round(rf, 2),
         -- an order still in progress has no room yet: its wallet part may still come back automatically on a cancel
         case when (select status from o) in ('delivered', 'rejected', 'cancelled') then round(greatest(0, pw + pc - rf), 2) else 0 end from p
$$;
revoke all on function order_refund_cap(bigint) from public, anon, authenticated;

drop function if exists ticket_refund_room(bigint);
create function ticket_refund_room(p_ticket bigint)
returns table(order_total numeric, refunded numeric, room numeric, paid_wallet numeric, paid_cash numeric, unproven numeric)
language sql stable security definer set search_path = public as $$
  select o.total, c.refunded, c.room, c.paid_wallet, c.paid_cash, c.unproven
    from support_tickets t
    join orders o on o.id = t.order_id
    cross join lateral order_refund_cap(o.id) c
   where t.id = p_ticket and has_perm('support')
$$;
revoke all on function ticket_refund_room(bigint) from public, anon;
grant execute on function ticket_refund_room(bigint) to authenticated;

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

-- ---------- 3) courier cash receipts ----------
create table if not exists cash_settlements (
  id bigint generated always as identity primary key,
  driver_id uuid not null references profiles(id),
  amount numeric(12,2) not null check (amount > 0),
  due_before numeric(12,2) not null,
  remaining_after numeric(12,2) not null,
  received_by uuid not null references profiles(id),
  received_at timestamptz not null default now(),
  reference text check (reference is null or char_length(reference) between 1 and 80),
  note text check (note is null or char_length(note) <= 200),
  client_key text check (client_key is null or client_key ~ '^[A-Za-z0-9_-]{8,64}$'),
  check (amount <= due_before and remaining_after = due_before - amount)
);
create index if not exists cash_settlements_driver_idx on cash_settlements (driver_id, received_at desc);
create unique index if not exists cash_settlements_key_uq on cash_settlements (received_by, client_key) where client_key is not null;
alter table cash_settlements enable row level security;
drop policy if exists cash_settlements_read on cash_settlements;
create policy cash_settlements_read on cash_settlements for select using (driver_id = auth.uid() or has_perm('finance'));
revoke all on cash_settlements from anon;
revoke insert, update, delete, truncate on cash_settlements from authenticated;
grant select on cash_settlements to authenticated;
drop trigger if exists trg_cash_settlements_immutable on cash_settlements;
create trigger trg_cash_settlements_immutable before update or delete on cash_settlements
  for each row execute function trg_wallet_immutable();                          -- the same «ledger_immutable» guard as the wallet

-- what a courier owes: recorded cash of delivered orders not marked by the old full settlement − receipts recorded here
create or replace function driver_cash_due(p_driver uuid) returns numeric
language sql stable security definer set search_path = public as $$
  select round(coalesce((select sum(o.cash_collected) from orders o
                          where o.driver_id = p_driver and o.status = 'delivered' and o.cash_collected is not null and o.cash_settled_at is null), 0)
             - coalesce((select sum(s.amount) from cash_settlements s where s.driver_id = p_driver), 0), 2)
$$;
revoke all on function driver_cash_due(uuid) from public, anon, authenticated;

create or replace function receive_driver_cash(p_driver uuid, p_amount numeric, p_reference text default null, p_note text default null, p_key text default null)
returns table(id bigint, amount numeric, due_before numeric, remaining_after numeric, received_at timestamptz)
language plpgsql security definer set search_path = public as $$
declare v_a numeric := round(p_amount, 2); v_due numeric; v_ref text := nullif(btrim(coalesce(p_reference, '')), ''); v_s cash_settlements;
begin
  if not has_perm('finance') then raise exception 'not_allowed'; end if;
  if p_key is not null and p_key !~ '^[A-Za-z0-9_-]{8,64}$' then raise exception 'bad_value'; end if;
  if v_a is null or v_a <= 0 or v_a > 1000000 or char_length(coalesce(v_ref, '')) > 80 or char_length(coalesce(p_note, '')) > 200 then raise exception 'bad_value'; end if;
  perform 1 from profiles where profiles.id = p_driver and role = 'driver' for update;   -- one receipt at a time per courier
  if not found then raise exception 'not_found'; end if;
  if p_key is not null then                                                      -- the same form sent twice → the first receipt
    select * into v_s from cash_settlements s where s.received_by = auth.uid() and s.client_key = p_key;
    if found then
      if v_s.driver_id <> p_driver or v_s.amount <> v_a then raise exception 'bad_value'; end if;
      return query select v_s.id, v_s.amount, v_s.due_before, v_s.remaining_after, v_s.received_at; return;
    end if;
  end if;
  v_due := driver_cash_due(p_driver);
  if v_due <= 0 then raise exception 'nothing_due'; end if;
  if v_a > v_due then raise exception 'amount_too_high'; end if;
  insert into cash_settlements(driver_id, amount, due_before, remaining_after, received_by, reference, note, client_key)
  values (p_driver, v_a, v_due, v_due - v_a, auth.uid(), v_ref, nullif(left(btrim(coalesce(p_note, '')), 200), ''), p_key)
  returning * into v_s;
  return query select v_s.id, v_s.amount, v_s.due_before, v_s.remaining_after, v_s.received_at;
end $$;
revoke all on function receive_driver_cash(uuid, numeric, text, text, text) from public, anon;
grant execute on function receive_driver_cash(uuid, numeric, text, text, text) to authenticated;

-- old screens: «receive all» now records one receipt of the full amount owed (no order marking)
create or replace function settle_driver_cash(p_driver uuid) returns numeric
language plpgsql security definer set search_path = public as $$
declare v numeric;
begin
  if not has_perm('finance') then raise exception 'not_allowed'; end if;
  perform 1 from profiles where id = p_driver and role = 'driver' for update;
  if not found then raise exception 'not_found'; end if;
  v := driver_cash_due(p_driver);
  if v <= 0 then return 0; end if;
  perform * from receive_driver_cash(p_driver, v, null, null, null);
  return v;
end $$;

create or replace function cash_balances() returns table(driver_id uuid, balance numeric)
language sql stable security definer set search_path = public as $$
  select d.driver_id, driver_cash_due(d.driver_id)
    from (select distinct o.driver_id from orders o
           where o.status = 'delivered' and o.cash_collected is not null and o.cash_settled_at is null and o.driver_id is not null) d
   where has_perm('finance') or d.driver_id = auth.uid()
$$;

-- ---------- 4) support refunds per order on the receipt ----------
create index if not exists wallet_order_idx on wallet_entries (order_id) where order_id is not null;

commit;
