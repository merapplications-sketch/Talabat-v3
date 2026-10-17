-- =============================================================================================
-- PATCH 37 — delivery proof, support refunds. PREPARED LOCALLY, NOT APPLIED ANYWHERE.
-- Base: the live definitions read on 17 Oct (verify_batch3_readonly). Rollback: sql/rollback_patch37.sql.
-- Unchanged on purpose: delivery conditions and permissions, one refund per ticket, status transitions, the automatic
-- wallet return, points policy, cancellation responsibility. Courier / store money is in patch 38 (the v60 «model A» is withdrawn).
--
-- 1) PROOF (UAT005): deliver_order also requires that the photo really exists NOW in the private bucket «proofs», at the
--    allowed path <courier>/<order>/<file>.jpg, uploaded by this courier, a finished upload whose recorded type IS image/jpeg
--    (a missing type is refused, not assumed) and size 1 B–1 MB, not archived / deleted. No permission is widened.
-- 2) REFUNDS: one rule for ticket_refund_room and ticket_set_status (order_refund_cap):
--      proven paid = wallet money spent on the order and not given back (spend + automatic return, from the wallet ledger)
--                  + cash the courier RECORDED (delivered orders only, never more than the cash part of the order)
--      card / Apple Pay without a capture record, uncollected cash and points are NOT counted as paid
--      room = proven paid − support refunds already made on the order
--    ticket_set_status locks the ticket and the ORDER row before the check: two tickets of one order, and a cancel (whose
--    wallet return trigger updates the same order row) cannot pass the cap at the same moment. One refund per ticket stays.
--    NOT included (proposals, sql/option_*.sql): «refund only after the order ends», «a delivered order stays delivered».
--    Exceptional compensation is NOT created here (wallet_adjust stays as it is).
-- 3) Support refunds per order are read by the app with the existing RLS (wallet_read: own rows); an index on order_id.
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
       and s.metadata->>'mimetype' = 'image/jpeg')                    -- a missing type is refused (not assumed)
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
  select round(pw, 2), round(pc, 2), round(greatest(0, total - wu - pc), 2), round(rf, 2), round(greatest(0, pw + pc - rf), 2) from p
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

-- ---------- 3) support refunds per order on the receipt ----------
create index if not exists wallet_order_idx on wallet_entries (order_id) where order_id is not null;

commit;
