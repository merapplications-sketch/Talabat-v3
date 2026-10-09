-- Patch 21: WALLET (refund credit only) - refunds go to the customer's wallet and are spent at checkout
-- Run once in Supabase SQL Editor AFTER patch 20, then upload the files. Safe to re-run.
--
-- ROW LEVEL SECURITY
--   wallet_entries : a customer reads only HIS entries, the admin reads all. NOBODY writes directly (no write policy, and updates are blocked by a trigger):
--       money enters only through ticket_set_status (a refund approved by the admin), wallet_adjust (admin, with a reason) and
--       is spent only inside place_order; it comes back only through the cancel/reject trigger.
--   wallet_balance(p_user) : a customer gets his own balance; only the admin may ask for another user's.
--   The balance can never go below zero (checked under a row lock); one refund per ticket; one spend and one return per order.

------------------------------------------------------------------------------------------------
-- 1) LEDGER
------------------------------------------------------------------------------------------------
create table if not exists wallet_entries (
  id bigint generated always as identity primary key,
  user_id uuid not null references profiles(id) on delete cascade,
  amount numeric(12, 2) not null check (amount <> 0),
  kind text not null check (kind in ('refund', 'spend', 'return', 'adjust')),
  order_id bigint references orders(id) on delete set null,
  ticket_id bigint references support_tickets(id) on delete set null,
  note text check (note is null or char_length(note) <= 200),
  created_by uuid,
  created_at timestamptz not null default now()
);
create index if not exists wallet_user_idx on wallet_entries (user_id, created_at desc);
create unique index if not exists wallet_one_refund_per_ticket on wallet_entries (ticket_id) where kind = 'refund';
create unique index if not exists wallet_one_spend_per_order on wallet_entries (order_id) where kind = 'spend';
create unique index if not exists wallet_one_return_per_order on wallet_entries (order_id) where kind = 'return';
alter table wallet_entries enable row level security;
drop policy if exists wallet_read on wallet_entries;
create policy wallet_read on wallet_entries for select using (user_id = auth.uid() or is_admin());
revoke insert, update, delete on wallet_entries from anon, authenticated;
do $$ begin
  begin alter publication supabase_realtime add table wallet_entries; exception when duplicate_object then null; end;
end $$;

-- an entry is never edited (a mistake is corrected with a new entry)
create or replace function trg_wallet_immutable() returns trigger language plpgsql as $$
begin
  raise exception 'ledger_immutable';
end $$;
drop trigger if exists trg_wallet_no_update on wallet_entries;
create trigger trg_wallet_no_update before update on wallet_entries for each row execute function trg_wallet_immutable();

create or replace function wallet_balance(p_user uuid default null) returns numeric
language sql stable security definer set search_path = public as $$
  select coalesce(sum(w.amount), 0)::numeric
    from wallet_entries w
   where w.user_id = coalesce(p_user, auth.uid())
     and (coalesce(p_user, auth.uid()) = auth.uid() or is_admin())
$$;
revoke all on function wallet_balance(uuid) from public, anon;
grant execute on function wallet_balance(uuid) to authenticated;

-- admin correction (credit or debit) with a mandatory reason; a debit can never push the balance below zero
create or replace function wallet_adjust(p_user uuid, p_amount numeric, p_note text) returns void
language plpgsql security definer set search_path = public as $$
declare v_a numeric := round(coalesce(p_amount, 0), 2); v_note text := btrim(coalesce(p_note, ''));
begin
  if not is_admin() then raise exception 'not_allowed'; end if;
  if v_a = 0 or abs(v_a) > 100000 or char_length(v_note) < 3 or char_length(v_note) > 200 then raise exception 'bad_value'; end if;
  perform 1 from profiles where id = p_user and role = 'customer' for update;
  if not found then raise exception 'not_found'; end if;
  if v_a < 0 and wallet_balance(p_user) + v_a < 0 then raise exception 'insufficient_funds'; end if;
  insert into wallet_entries(user_id, amount, kind, note, created_by) values (p_user, v_a, 'adjust', v_note, auth.uid());
end $$;
revoke all on function wallet_adjust(uuid, numeric, text) from public, anon;
grant execute on function wallet_adjust(uuid, numeric, text) to authenticated;

------------------------------------------------------------------------------------------------
-- 2) ORDERS: how much of the order was paid from the wallet
------------------------------------------------------------------------------------------------
alter table orders add column if not exists wallet_used numeric not null default 0 check (wallet_used >= 0);
alter table orders add column if not exists wallet_returned_at timestamptz;

-- cancelled by the customer or rejected by the restaurant: the wallet part comes back, once
create or replace function trg_wallet_return() returns trigger language plpgsql security definer set search_path = public as $$
begin
  if new.status in ('rejected', 'cancelled') and old.status not in ('rejected', 'cancelled')
     and coalesce(new.wallet_used, 0) > 0 and new.wallet_returned_at is null then
    insert into wallet_entries(user_id, amount, kind, order_id) values (new.customer_id, new.wallet_used, 'return', new.id)
    on conflict (order_id) where kind = 'return' do nothing;
    new.wallet_returned_at := now();
  end if;
  return new;
end $$;
drop trigger if exists trg_orders_wallet_return on orders;
create trigger trg_orders_wallet_return before update of status on orders for each row execute function trg_wallet_return();

------------------------------------------------------------------------------------------------
-- 3) COURIER CASH: the cash to collect is the total minus what the wallet paid
------------------------------------------------------------------------------------------------
create or replace function deliver_order(p_id bigint, p_cash numeric default null, p_note text default null) returns void
language plpgsql security definer set search_path = public as $$
declare o orders; iscash boolean;
begin
  select * into o from orders where id = p_id for update;
  if not found then raise exception 'not_found'; end if;
  if o.driver_id is distinct from auth.uid() or o.status <> 'pickedup' then raise exception 'bad_transition'; end if;
  iscash := o.payment ~ '^(cash|Cash|Наличн)';
  if iscash then
    if p_cash is null or p_cash < 0 then raise exception 'cash_required'; end if;
    if p_cash <> (o.total - coalesce(o.wallet_used, 0)) and coalesce(trim(p_note), '') = '' then raise exception 'note_required'; end if;
  end if;
  update orders set status = 'delivered', done_at = now(),
    cash_collected = case when iscash then p_cash end,
    cash_note = case when iscash then left(p_note, 200) end
  where id = p_id;
end $$;
revoke all on function deliver_order(bigint, numeric, text) from public, anon;
grant execute on function deliver_order(bigint, numeric, text) to authenticated;

------------------------------------------------------------------------------------------------
-- 4) REFUNDS: closing a ticket with an amount credits the wallet (all in one step, one refund per ticket)
------------------------------------------------------------------------------------------------
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
    if v_t.order_id is not null then
      select total into v_max from orders where id = v_t.order_id;
      select coalesce(sum(amount), 0) into v_prev from wallet_entries where order_id = v_t.order_id and kind = 'refund';
      if v_ref + v_prev > coalesce(v_max, 0) then raise exception 'bad_value'; end if;   -- never more than the order was worth, over all its tickets
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
-- 5) place_order: one more optional argument p_wallet = the amount the customer chose to pay from the wallet
------------------------------------------------------------------------------------------------
drop function if exists place_order(uuid, jsonb, numeric, text, text, double precision, double precision, text, text, numeric);
create or replace function place_order(p_store uuid, p_items jsonb, p_tip numeric default 0, p_payment text default 'cash',
  p_address text default '', p_lat float8 default null, p_lng float8 default null, p_promo text default null, p_key text default null, p_fee numeric default null, p_wallet numeric default null)
returns bigint language plpgsql security definer set search_path = public as $$
declare s stores; pr profiles; it record; v_item menu_items; pl jsonb; v_id bigint; v_sub numeric; v_fee numeric; v_pay numeric; v_disc numeric; v_base numeric; v_gate numeric;
        v_promo numeric := 0; v_tip numeric; v_km float8; v_code text := null; v_dq jsonb; v_cphone text; v_total numeric; v_bal numeric; v_w numeric;
begin
  if auth.uid() is null then raise exception 'auth'; end if;
  -- idempotency: a retry of the SAME attempt (bad network, double tap) returns the order that already exists
  if p_key is not null then
    if p_key !~ '^[A-Za-z0-9_-]{8,64}$' then raise exception 'bad_value'; end if;
    select o.id into v_id from orders o where o.customer_id = auth.uid() and o.client_key = p_key;
    if found then return v_id; end if;
  end if;
  -- abuse guard: at most 20 orders per hour per customer
  if (select count(*) from orders where customer_id = auth.uid() and created_at > now() - interval '1 hour') >= 20 then
    raise exception 'too_many_orders';
  end if;
  -- spam / abuse guard: at most 5 unfinished orders per customer
  if (select count(*) from orders where customer_id = auth.uid() and status in ('pending', 'preparing', 'ready', 'pickedup')) >= 5 then
    raise exception 'too_many_orders';
  end if;
  if (p_lat is not null and (p_lat < -90 or p_lat > 90)) or (p_lng is not null and (p_lng < -180 or p_lng > 180)) then
    raise exception 'bad_value';
  end if;
  -- a delivery address (text + map point) is mandatory
  if p_lat is null or p_lng is null or char_length(btrim(coalesce(p_address, ''))) < 3 then
    raise exception 'address_required';
  end if;
  select * into s from stores where id = p_store and is_active;
  if not found then raise exception 'store_unavailable'; end if;
  if not s.is_open then raise exception 'closed'; end if;
  if jsonb_typeof(p_items) <> 'array' or jsonb_array_length(p_items) = 0 then raise exception 'empty'; end if;
  if jsonb_array_length(p_items) > 60 then raise exception 'bad_value'; end if;
  select * into pr from profiles where id = auth.uid();

  -- the customer phone is required (stored privately, see order_customer_phone) and the fee is calculated here, never by the app
  if pr.banned_at is not null then raise exception 'account_blocked'; end if;   -- a suspended account cannot order
  v_cphone := norm_phone(pr.phone);
  if v_cphone is null then raise exception 'phone_required'; end if;
  v_dq := delivery_calc(p_store, p_lat, p_lng, auth.uid());
  v_fee := (v_dq->>'fee')::numeric;
  v_pay := case s.fee_type when 'free' then s.fee_base else (v_dq->>'fee_full')::numeric end;   -- courier is always paid; the platform covers free delivery
  if p_fee is not null and abs(p_fee - v_fee) > 0.009 then raise exception 'fee_changed'; end if;   -- the price shown to the customer must be the price charged
  v_tip := case when p_tip in (0,3,5,10) then p_tip else 0 end;

  begin
    insert into orders(store_id, customer_id, customer_name, payment, address, lat, lng, client_key)
    values (p_store, auth.uid(), pr.name, left(p_payment,40), left(p_address,200), p_lat, p_lng, p_key)
    returning id into v_id;
  exception when unique_violation then
    -- two taps raced: the other attempt won, return its order
    select o.id into v_id from orders o where o.customer_id = auth.uid() and o.client_key = p_key;
    return v_id;
  end;
  insert into order_customer_phone(order_id, phone) values (v_id, v_cphone);

  -- every line is priced by the DATABASE: base price + the chosen options (validated against the item's own option groups)
  for it in select (x->>'item_id')::uuid as item_id,
                   least(50, greatest(1, (x->>'qty')::int)) as qty,
                   left(coalesce(x->>'note', ''), 120) as note,
                   case when jsonb_typeof(x->'options') = 'array' then x->'options' else '[]'::jsonb end as opts
              from jsonb_array_elements(p_items) x loop
    select * into v_item from menu_items where id = it.item_id and store_id = p_store and available and approved;
    if not found then raise exception 'unavailable'; end if;
    pl := price_line(it.item_id, it.opts);
    insert into order_items(order_id, item_id, name, price, qty, note, options)
    values (v_id, v_item.id, v_item.name, (pl->>'unit')::numeric, it.qty, it.note, pl->'snap');
  end loop;

  -- each line gets the better of the store discount and its own item discount (they do not stack)
  select sum(oi.price * oi.qty),
         coalesce(sum(round(oi.price * oi.qty * greatest(s.discount_pct, coalesce(m.discount_pct, 0)) / 100, 2)), 0),
         coalesce(sum(oi.price * oi.qty) filter (where greatest(s.discount_pct, coalesce(m.discount_pct, 0)) = 0), 0)
    into v_sub, v_disc, v_base
    from order_items oi left join menu_items m on m.id = oi.item_id
   where oi.order_id = v_id;

  if p_promo is not null and length(trim(p_promo)) > 0 then
    if v_base <= 0 then raise exception 'promo_offer'; end if;     -- promo codes never apply to lines that already have an offer
    if not exists (select 1 from promo_attempts where user_id = auth.uid() and ok and code = upper(trim(p_promo))
                    and at > now() - interval '2 hours') then
      raise exception 'promo_invalid';                             -- must be validated (rate-limited) in check_promo first
    end if;
    v_gate := v_sub - v_disc;                                       -- the minimum order is checked on what the customer pays for items
    v_promo := promo_eval(p_promo, v_base, auth.uid(), true, v_gate);
    if v_promo > 0 then v_code := upper(trim(p_promo)); end if;
  end if;

  update orders set subtotal = v_sub, discount = v_disc, delivery_fee = v_fee, tip = v_tip,
    delivery_base = (v_dq->>'base')::numeric, delivery_extra = (v_dq->>'extra')::numeric, delivery_km = (v_dq->>'km')::numeric,
    promo_code = v_code, promo_discount = v_promo,
    total = greatest(5, v_sub - v_disc - v_promo + v_fee + v_tip),
    commission_pct = s.commission_pct, commission = round((v_sub - v_disc) * s.commission_pct / 100, 2),
    driver_payout = v_pay + v_tip
  where id = v_id;

  -- WALLET: the customer may pay all or part of the order from his refund balance (the server decides the amount, never the app)
  if coalesce(p_wallet, 0) > 0 then
    select total into v_total from orders where id = v_id;
    perform 1 from profiles where id = auth.uid() for update;           -- two orders at the same moment cannot spend the same money
    v_bal := wallet_balance();
    v_w := round(least(p_wallet, v_bal, v_total), 2);
    if v_w <= 0 or abs(v_w - round(p_wallet, 2)) > 0.009 then raise exception 'wallet_changed'; end if;   -- the customer saw another amount: ask again
    insert into wallet_entries(user_id, amount, kind, order_id) values (auth.uid(), -v_w, 'spend', v_id);
    update orders set wallet_used = v_w, payment = case when v_w >= v_total then 'wallet' else payment end where id = v_id;
  end if;
  return v_id;
end $$;revoke all on function place_order(uuid, jsonb, numeric, text, text, double precision, double precision, text, text, numeric, numeric) from public, anon;
grant execute on function place_order(uuid, jsonb, numeric, text, text, double precision, double precision, text, text, numeric, numeric) to authenticated;
