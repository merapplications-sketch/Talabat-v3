-- =============================================================================================
-- PATCH 38 — store payment agreements + separate money records (customer · courier · store · platform). PREPARED LOCALLY,
-- NOT APPLIED ANYWHERE. Needs patch 37 (proof_exists). Rollbacks: sql/rollback_patch38.sql (refuses while money records exist,
-- checked under a table lock) and sql/rollback_patch38_keep_records.sql.
--
-- A) PAYMENT AGREEMENT PER STORE (owner's requirement 17 Oct). stores.accept_online / allow_wallet / allow_points (defaults =
--    today's behaviour: all allowed) and settle_method ('driver_pays' = the courier pays the store's full goods invoice;
--    'platform_settles' = the platform settles the store later; NULL = not set yet). Only admin / staff «stores» change them
--    (guard trigger + audit). place_order enforces them (online_not_allowed / wallet_not_allowed / points_not_allowed) and keeps
--    the rules in force on the order (orders.pay_rules). Historical orders are not touched. No electronic capture is created:
--    there is still no payment provider; an electronic payment is NOT recorded as collected.
-- B) SEPARATE RECORDS (no «all cash the courier took is a debt» model; the v60 model A is withdrawn):
--    customer collection   = orders.cash_collected (courier, at delivery) + wallet ledger (patch 21); kept whatever the status
--    courier → store       = driver_store_payments (amount, reference / photo, who confirmed: the store or finance; disputed)
--    courier pay owed      = orders.driver_payout of delivered orders; paid only by a recorded platform → courier settlement
--    platform ↔ courier    = platform_driver_settlements (both directions, receiver / payer, reference, before / after)
--    store owed / paid     = the restaurant's existing «net payable» formula of delivered orders; paid by the courier (non-disputed)
--                            or by the platform (platform_store_settlements: method, reference, status pending / done / failed)
--    Nothing is netted automatically (courier pay is never deducted from the cash he holds without an approved rule).
--    A status change never deletes a collection or a payment.
-- C) START OF THE NEW ACCOUNTING: accounting_start (set once by finance at activation, after reviewing
--    sql/reconcile_transition_readonly.sql). Orders created from that moment belong to the new records; older ones stay with the
--    old cash_balances / settle_driver_cash (which, once a start is set, only look at older orders). No balance is moved.
-- Every write goes through a function: permission check, lock, idempotency key per form, «before / after» kept. Records are
-- append-only (only the status of a pending item can be decided, once).
-- =============================================================================================
begin;

-- ---------- A) store agreement ----------
alter table stores add column if not exists accept_online boolean not null default true;
alter table stores add column if not exists allow_wallet boolean not null default true;
alter table stores add column if not exists allow_points boolean not null default true;
alter table stores add column if not exists settle_method text check (settle_method is null or settle_method in ('driver_pays', 'platform_settles'));
alter table orders add column if not exists pay_rules jsonb;

create or replace function trg_store_pay_guard() returns trigger language plpgsql security definer set search_path = public as $$
begin
  if (new.accept_online, new.allow_wallet, new.allow_points, new.settle_method) is distinct from (old.accept_online, old.allow_wallet, old.allow_points, old.settle_method)
     and not (is_admin() or has_perm('stores')) then raise exception 'not_allowed'; end if;
  return new;
end $$;
drop trigger if exists trg_store_pay_guard on stores;
create trigger trg_store_pay_guard before update on stores for each row execute function trg_store_pay_guard();
drop trigger if exists trg_audit_store_pay on stores;
create trigger trg_audit_store_pay after update on stores for each row execute function audit_changes('id', 'accept_online', 'allow_wallet', 'allow_points', 'settle_method');

create or replace function set_store_pay_rules(p_store uuid, p_online boolean, p_wallet boolean, p_points boolean, p_method text) returns void
language plpgsql security definer set search_path = public as $$
begin
  if not (is_admin() or has_perm('stores')) then raise exception 'not_allowed'; end if;
  if p_online is null or p_wallet is null or p_points is null or (p_method is not null and p_method not in ('driver_pays', 'platform_settles')) then raise exception 'bad_value'; end if;
  update stores set accept_online = p_online, allow_wallet = p_wallet, allow_points = p_points, settle_method = p_method where id = p_store;
  if not found then raise exception 'not_found'; end if;
end $$;
revoke all on function set_store_pay_rules(uuid, boolean, boolean, boolean, text) from public, anon;
grant execute on function set_store_pay_rules(uuid, boolean, boolean, boolean, text) to authenticated;

-- place_order: the live definition (read 17 Oct) + the lines marked «patch 38» (agreement checks, rules kept on the order)
CREATE OR REPLACE FUNCTION public.place_order(p_store uuid, p_items jsonb, p_tip numeric DEFAULT 0, p_payment text DEFAULT 'cash'::text, p_address text DEFAULT ''::text, p_lat double precision DEFAULT NULL::double precision, p_lng double precision DEFAULT NULL::double precision, p_promo text DEFAULT NULL::text, p_key text DEFAULT NULL::text, p_fee numeric DEFAULT NULL::numeric, p_wallet numeric DEFAULT NULL::numeric, p_points integer DEFAULT NULL::integer, p_extra jsonb DEFAULT NULL::jsonb)
 RETURNS bigint
 LANGUAGE plpgsql
 SECURITY DEFINER
 SET search_path TO 'public'
AS $function$
declare s stores; pr profiles; it record; v_item menu_items; pl jsonb; v_id bigint; v_sub numeric; v_fee numeric; v_pay numeric; v_disc numeric; v_base numeric; v_gate numeric;
        v_promo numeric := 0; v_tip numeric; v_km float8; v_code text := null; v_dq jsonb; v_cphone text; v_total numeric; v_bal numeric; v_w numeric;
        v_hh int := 0; v_all numeric; v_hdisc numeric := 0; v_rate numeric; v_min numeric; v_lb int; v_pts int := 0; v_pval numeric := 0; v_cap numeric;
        v_step numeric; v_mo numeric; v_subst text; v_door boolean; v_gn text; v_gp text;
        v_at timestamptz; v_waived numeric := 0; v_gid uuid; g group_orders; v_t2 numeric; v_w2 numeric := 0;   -- patch 38
begin
  if p_wallet is not null and p_wallet < 0 then raise exception 'bad_value'; end if;
  if p_points is not null and (p_points < 0 or p_points > 100000000) then raise exception 'bad_value'; end if;
  -- order options (v50): leave at the door, what to do if a dish is missing, a gift for someone else
  v_door := coalesce((p_extra->>'door')::boolean, false);
  v_subst := coalesce(p_extra->>'subst', 'call');
  if v_subst not in ('call', 'replace', 'remove') then raise exception 'bad_value'; end if;
  -- scheduled delivery time (v51): from 45 minutes (with a little slack for the screen) to 3 days ahead
  if nullif(p_extra->>'at', '') is not null then
    begin v_at := (p_extra->>'at')::timestamptz; exception when others then raise exception 'bad_time'; end;
    if v_at < now() + interval '40 minutes' or v_at > now() + interval '3 days' then raise exception 'bad_time'; end if;
  end if;
  -- office / group order (v51): only its host can place it, once
  if nullif(p_extra->>'group', '') is not null then
    begin v_gid := (p_extra->>'group')::uuid; exception when others then raise exception 'bad_group'; end;
    select * into g from group_orders where id = v_gid for update;
    if not found or g.host_id <> auth.uid() or g.status not in ('open', 'closed') or g.store_id <> p_store then raise exception 'bad_group'; end if;
  end if;
  if p_extra ? 'gift' and jsonb_typeof(p_extra->'gift') = 'object' then
    v_gn := btrim(coalesce(p_extra->'gift'->>'name', '')); v_gp := norm_phone(p_extra->'gift'->>'phone');
    if char_length(v_gn) not between 2 and 60 or v_gp is null then raise exception 'bad_gift'; end if;
  end if;   -- a negative amount would mean ADDING money: refuse it
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
  v_hh := happy_hour_pct(p_store);                                -- admin-scheduled happy hour (paid by the platform)
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
  v_tip := case when p_tip in (0,3,5,10) then p_tip else 0 end;

  begin
    insert into orders(store_id, customer_id, customer_name, payment, address, lat, lng, client_key, leave_at_door, substitution, is_gift, scheduled_for, group_id)
    values (p_store, auth.uid(), pr.name, left(p_payment,40), left(p_address,200), p_lat, p_lng, p_key, v_door, v_subst, v_gn is not null, v_at, v_gid)
    returning id into v_id;
  exception when unique_violation then
    -- two taps raced: the other attempt won, return its order
    select o.id into v_id from orders o where o.customer_id = auth.uid() and o.client_key = p_key;
    return v_id;
  end;
  insert into order_customer_phone(order_id, phone) values (v_id, v_cphone);
  if v_gn is not null then insert into order_recipient(order_id, name, phone) values (v_id, v_gn, v_gp); end if;

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

  -- each line gets the better of the store discount and its own item discount (they do not stack; paid by the restaurant).
  -- A happy hour can only make it better. Owner decision (v48): the RESTAURANT pays it too, like its own offers: it is part of
  -- orders.discount (so revenue and commission are on what the customer pays); orders.hh_discount says how much of it came from the happy hour.
  select sum(oi.price * oi.qty),
         coalesce(sum(round(oi.price * oi.qty * greatest(s.discount_pct, coalesce(m.discount_pct, 0)) / 100, 2)), 0),
         coalesce(sum(round(oi.price * oi.qty * greatest(s.discount_pct, coalesce(m.discount_pct, 0), v_hh) / 100, 2)), 0),
         coalesce(sum(oi.price * oi.qty) filter (where greatest(s.discount_pct, coalesce(m.discount_pct, 0), v_hh) = 0), 0)
    into v_sub, v_disc, v_all, v_base
    from order_items oi left join menu_items m on m.id = oi.item_id
   where oi.order_id = v_id;
  v_hdisc := v_all - v_disc;
  -- free delivery above the restaurant's own threshold (v51): the restaurant pays the waived fee (orders.fee_waived)
  if coalesce(s.free_delivery_min, 0) > 0 and v_sub - v_disc - v_hdisc >= s.free_delivery_min and v_fee > 0 then
    v_waived := v_fee; v_fee := 0;
  end if;
  if p_fee is not null and abs(p_fee - v_fee) > 0.009 then raise exception 'fee_changed'; end if;   -- the price shown to the customer must be the price charged

  if p_promo is not null and length(trim(p_promo)) > 0 then
    if v_base <= 0 then raise exception 'promo_offer'; end if;     -- promo codes never apply to lines that already have an offer
    if not exists (select 1 from promo_attempts where user_id = auth.uid() and ok and code = upper(trim(p_promo))
                    and at > now() - interval '2 hours') then
      raise exception 'promo_invalid';                             -- must be validated (rate-limited) in check_promo first
    end if;
    v_gate := v_sub - v_disc - v_hdisc;                                       -- the minimum order is checked on what the customer pays for items
    v_promo := promo_eval(p_promo, v_base, auth.uid(), true, v_gate);
    if v_promo > 0 then v_code := upper(trim(p_promo)); end if;
  end if;

  update orders set subtotal = v_sub, discount = v_disc + v_hdisc, delivery_fee = v_fee, fee_waived = v_waived, tip = v_tip,
    delivery_base = (v_dq->>'base')::numeric, delivery_extra = (v_dq->>'extra')::numeric, delivery_km = (v_dq->>'km')::numeric,
    promo_code = v_code, promo_discount = v_promo, hh_discount = v_hdisc, hh_pct = v_hh,
    total = greatest(5, v_sub - v_disc - v_hdisc - v_promo + v_fee + v_tip),
    commission_pct = s.commission_pct, commission = round((v_sub - v_disc - v_hdisc) * s.commission_pct / 100, 2),
    driver_payout = v_pay + v_tip
  where id = v_id;

  -- POINTS: the customer may pay part of the items with loyalty points (all he can use, decided here, never by the app)
  if coalesce(p_points, 0) > 0 and not s.allow_points then raise exception 'points_not_allowed'; end if;   -- patch 38: the store's agreement
  if coalesce(p_points, 0) > 0 then
    v_rate := loyalty_setting('loyalty_points_per_tjs'); v_min := loyalty_setting('loyalty_min_redeem');
    v_step := greatest(1, loyalty_setting('loyalty_voucher_points'));
    v_mo := coalesce(s.points_min_order, loyalty_setting('loyalty_min_order'));
    perform 1 from profiles where id = auth.uid() for update;          -- two orders at the same moment cannot spend the same points
    v_lb := loyalty_balance(auth.uid());
    if v_lb < v_min then raise exception 'points_min'; end if;
    v_cap := v_sub - v_disc - v_hdisc - v_promo;                       -- points never pay for delivery or the tip
    if v_cap < v_mo then raise exception 'points_min_order'; end if;  -- the order (dishes) must reach the minimum to use points
    v_pts := (floor(least(v_lb, floor(greatest(v_cap, 0) * v_rate)) / v_step) * v_step)::int;   -- whole vouchers only (1000, 2000 ...)
    if v_pts <= 0 or v_pts <> p_points then raise exception 'points_changed'; end if;   -- the customer saw another amount: ask again
    v_pval := round(v_pts / v_rate, 2);
    perform loyalty_spend(auth.uid(), v_pts, v_id);
    update orders set points_used = v_pts, points_value = v_pval,
      total = greatest(5, v_sub - v_disc - v_hdisc - v_promo - v_pval + v_fee + v_tip) where id = v_id;
  end if;

  -- WALLET: the customer may pay all or part of the order from his refund balance (the server decides the amount, never the app)
  if coalesce(p_wallet, 0) > 0 and not s.allow_wallet then raise exception 'wallet_not_allowed'; end if;   -- patch 38: the store's agreement
  if coalesce(p_wallet, 0) > 0 then
    select total into v_total from orders where id = v_id;
    perform 1 from profiles where id = auth.uid() for update;           -- two orders at the same moment cannot spend the same money
    v_bal := wallet_balance();
    v_w := round(least(p_wallet, v_bal, v_total), 2);
    if v_w <= 0 or abs(v_w - round(p_wallet, 2)) > 0.009 then raise exception 'wallet_changed'; end if;   -- the customer saw another amount: ask again
    insert into wallet_entries(user_id, amount, kind, order_id) values (auth.uid(), -v_w, 'spend', v_id);
    update orders set wallet_used = v_w, payment = case when v_w >= v_total then 'wallet' else payment end where id = v_id;
  end if;
  -- patch 38: a cash-only store takes no electronic payment for what is left after the wallet; the rules in force are kept on the order
  select total, coalesce(wallet_used, 0) into v_t2, v_w2 from orders where id = v_id;
  if v_t2 - v_w2 > 0 and p_payment !~ '^(cash|Cash|Наличн)' and not s.accept_online then raise exception 'online_not_allowed'; end if;
  update orders set pay_rules = jsonb_build_object('accept_online', s.accept_online, 'allow_wallet', s.allow_wallet, 'allow_points', s.allow_points,
                                                   'settle_method', s.settle_method) where id = v_id;
  if v_gid is not null then update group_orders set status = 'placed', order_id = v_id, closed_at = coalesce(closed_at, now()) where id = v_gid; end if;
  return v_id;
end $function$;

-- ---------- C) start of the new accounting ----------
create table if not exists accounting_start (id boolean primary key default true check (id), start_at timestamptz not null, set_by uuid, set_at timestamptz not null default now());
alter table accounting_start enable row level security;
drop policy if exists accounting_start_read on accounting_start;
create policy accounting_start_read on accounting_start for select using (auth.uid() is not null);
revoke all on accounting_start from anon; revoke insert, update, delete, truncate on accounting_start from authenticated; grant select on accounting_start to authenticated;
create or replace function acc_start() returns timestamptz language sql stable security definer set search_path = public as $$ select start_at from accounting_start where id $$;
create or replace function set_accounting_start(p_at timestamptz) returns void language plpgsql security definer set search_path = public as $$
begin
  if not has_perm('finance') then raise exception 'not_allowed'; end if;
  if p_at is null then raise exception 'bad_value'; end if;
  insert into accounting_start(id, start_at, set_by) values (true, p_at, auth.uid()) on conflict (id) do nothing;   -- once
  if not found then raise exception 'already_set'; end if;
end $$;
revoke all on function set_accounting_start(timestamptz) from public, anon; grant execute on function set_accounting_start(timestamptz) to authenticated;
-- an order belongs to the new records when it was created from the start on
create or replace function acc_order(p_created timestamptz) returns boolean language sql stable security definer set search_path = public as $$
  select acc_start() is not null and p_created >= acc_start() $$;

-- ---------- B) records ----------
create table if not exists driver_store_payments (
  id bigint generated always as identity primary key,
  order_id bigint not null references orders(id), store_id uuid not null, driver_id uuid not null references profiles(id),
  amount numeric(12,2) not null check (amount > 0 and amount <= 1000000),
  reference text check (reference is null or char_length(reference) between 1 and 80),
  proof_path text check (proof_path is null or char_length(proof_path) <= 300),
  status text not null default 'claimed' check (status in ('claimed', 'confirmed', 'disputed')),
  recorded_at timestamptz not null default now(),
  decided_by uuid, decided_by_name text, decided_at timestamptz, decision_note text check (decision_note is null or char_length(decision_note) <= 200),
  client_key text not null check (client_key ~ '^[A-Za-z0-9_-]{8,64}$'),
  check (reference is not null or proof_path is not null)
);
create unique index if not exists dsp_key_uq on driver_store_payments (driver_id, client_key);
create unique index if not exists dsp_one_active_per_order on driver_store_payments (order_id) where status <> 'disputed';
create index if not exists dsp_store_idx on driver_store_payments (store_id, id desc);
create index if not exists dsp_driver_idx on driver_store_payments (driver_id, id desc);

create table if not exists platform_driver_settlements (
  id bigint generated always as identity primary key,
  driver_id uuid not null references profiles(id),
  direction text not null check (direction in ('driver_to_platform', 'platform_to_driver')),
  amount numeric(12,2) not null check (amount > 0 and amount <= 1000000),
  before_amount numeric(12,2) not null, after_amount numeric(12,2) not null,
  reference text check (reference is null or char_length(reference) between 1 and 80),
  note text check (note is null or char_length(note) <= 200),
  recorded_by uuid not null, recorded_by_name text, recorded_at timestamptz not null default now(),
  client_key text not null check (client_key ~ '^[A-Za-z0-9_-]{8,64}$'),
  check (amount <= before_amount and after_amount = before_amount - amount)
);
create unique index if not exists pds_key_uq on platform_driver_settlements (recorded_by, client_key);
create index if not exists pds_driver_idx on platform_driver_settlements (driver_id, id desc);

create table if not exists platform_store_settlements (
  id bigint generated always as identity primary key,
  store_id uuid not null,
  amount numeric(12,2) not null check (amount > 0 and amount <= 10000000),
  method text not null check (method in ('cash', 'bank', 'online')),
  status text not null default 'pending' check (status in ('pending', 'done', 'failed')),
  before_amount numeric(12,2) not null, after_amount numeric(12,2) not null,
  reference text check (reference is null or char_length(reference) between 1 and 80),
  note text check (note is null or char_length(note) <= 200),
  recorded_by uuid not null, recorded_by_name text, recorded_at timestamptz not null default now(),
  status_by uuid, status_by_name text, status_at timestamptz,
  client_key text not null check (client_key ~ '^[A-Za-z0-9_-]{8,64}$'),
  check (amount <= before_amount and after_amount = before_amount - amount),
  check (status <> 'done' or reference is not null)                       -- a done settlement always has its reference
);
create unique index if not exists pss_key_uq on platform_store_settlements (recorded_by, client_key);
create index if not exists pss_store_idx on platform_store_settlements (store_id, id desc);

-- append-only: only a pending status may be decided, once; nothing else changes; nothing is deleted
create or replace function trg_money_record_guard() returns trigger language plpgsql as $$
begin
  if tg_op = 'DELETE' then raise exception 'ledger_immutable'; end if;
  if tg_table_name = 'driver_store_payments' then
    if old.status <> 'claimed' or new.status not in ('confirmed', 'disputed')
       or (to_jsonb(new) - array['status', 'decided_by', 'decided_by_name', 'decided_at', 'decision_note']) <> (to_jsonb(old) - array['status', 'decided_by', 'decided_by_name', 'decided_at', 'decision_note'])
    then raise exception 'ledger_immutable'; end if;
  elsif tg_table_name = 'platform_store_settlements' then
    if old.status <> 'pending' or new.status not in ('done', 'failed')
       or (to_jsonb(new) - array['status', 'status_by', 'status_by_name', 'status_at', 'reference']) <> (to_jsonb(old) - array['status', 'status_by', 'status_by_name', 'status_at', 'reference'])
       or (old.reference is not null and new.reference is distinct from old.reference)
    then raise exception 'ledger_immutable'; end if;
  else raise exception 'ledger_immutable';
  end if;
  return new;
end $$;
do $$ declare t text; begin
  foreach t in array array['driver_store_payments', 'platform_driver_settlements', 'platform_store_settlements'] loop
    execute format('drop trigger if exists trg_guard on %I', t);
    execute format('create trigger trg_guard before update or delete on %I for each row execute function trg_money_record_guard()', t);
    execute format('alter table %I enable row level security', t);
    execute format('revoke all on %I from anon', t);
    execute format('revoke insert, update, delete, truncate on %I from authenticated', t);
    execute format('grant select on %I to authenticated', t);
  end loop;
end $$;
drop policy if exists dsp_read on driver_store_payments;
create policy dsp_read on driver_store_payments for select using (driver_id = auth.uid() or owns_store(store_id) or has_perm('finance'));
drop policy if exists pds_read on platform_driver_settlements;
create policy pds_read on platform_driver_settlements for select using (driver_id = auth.uid() or has_perm('finance'));
drop policy if exists pss_read on platform_store_settlements;
create policy pss_read on platform_store_settlements for select using (owns_store(store_id) or has_perm('finance'));

-- ---------- positions (read) ----------
create or replace function driver_position(p_driver uuid)
returns table(collected numeric, paid_to_stores_confirmed numeric, paid_to_stores_claimed numeric, handed_to_platform numeric,
              cash_held numeric, earned numeric, earnings_paid numeric, earnings_due numeric)
language sql stable security definer set search_path = public as $$
  with o as (select * from orders where driver_id = p_driver and acc_order(created_at)),
  c as (select coalesce(sum(cash_collected), 0) as col,                                     -- kept whatever the status now is
               coalesce(sum(driver_payout) filter (where status = 'delivered'), 0) as ear from o),
  p as (select coalesce(sum(amount) filter (where status = 'confirmed'), 0) as conf, coalesce(sum(amount) filter (where status = 'claimed'), 0) as clm
          from driver_store_payments d where d.driver_id = p_driver and d.order_id in (select id from o)),
  s as (select coalesce(sum(amount) filter (where direction = 'driver_to_platform'), 0) as hand,
               coalesce(sum(amount) filter (where direction = 'platform_to_driver'), 0) as paid from platform_driver_settlements where driver_id = p_driver)
  select round(c.col, 2), round(p.conf, 2), round(p.clm, 2), round(s.hand, 2), round(c.col - p.conf - p.clm - s.hand, 2),
         round(c.ear, 2), round(s.paid, 2), round(c.ear - s.paid, 2)
    from c, p, s where has_perm('finance') or p_driver = auth.uid()
$$;
create or replace function store_position(p_store uuid)
returns table(gross numeric, commission numeric, store_funded numeric, net_due numeric, paid_by_drivers numeric, paid_by_platform numeric,
              balance numeric, paid_on_undelivered numeric, claimed_unconfirmed numeric)
language sql stable security definer set search_path = public as $$
  with o as (select * from orders where store_id = p_store and acc_order(created_at)),
  d as (select coalesce(sum(subtotal - discount), 0) as gross, coalesce(sum(commission), 0) as com,
               coalesce(sum(coalesce(points_value, 0) + coalesce(cashback, 0) + coalesce(fee_waived, 0)), 0) as sf
          from o where status = 'delivered'),                                   -- the restaurant's existing «net payable» formula
  p as (select coalesce(sum(x.amount), 0) as drv, coalesce(sum(x.amount) filter (where o.status <> 'delivered'), 0) as undel,
               coalesce(sum(x.amount) filter (where x.status = 'claimed'), 0) as clm
          from driver_store_payments x join o on o.id = x.order_id where x.status <> 'disputed'),
  q as (select coalesce(sum(amount), 0) as plat from platform_store_settlements where store_id = p_store and status in ('pending', 'done'))
  select round(d.gross, 2), round(d.com, 2), round(d.sf, 2), round(d.gross - d.com - d.sf, 2), round(p.drv, 2), round(q.plat, 2),
         round(d.gross - d.com - d.sf - p.drv - q.plat, 2), round(p.undel, 2), round(p.clm, 2)
    from d, p, q where has_perm('finance') or owns_store(p_store)
$$;
revoke all on function driver_position(uuid) from public, anon; grant execute on function driver_position(uuid) to authenticated;
revoke all on function store_position(uuid) from public, anon; grant execute on function store_position(uuid) to authenticated;

-- ---------- writes ----------
-- courier → store: the courier records what he paid the store for THIS order (driver_pays stores, new accounting only)
create or replace function record_store_payment(p_order bigint, p_amount numeric, p_reference text, p_proof text, p_key text)
returns table(id bigint, status text, amount numeric)
language plpgsql security definer set search_path = public as $$
#variable_conflict use_column
declare o orders; v_a numeric := round(p_amount, 2); v_ref text := nullif(btrim(coalesce(p_reference, '')), ''); r driver_store_payments;
begin
  if p_key is null or p_key !~ '^[A-Za-z0-9_-]{8,64}$' then raise exception 'bad_value'; end if;
  select * into r from driver_store_payments where driver_id = auth.uid() and client_key = p_key;
  if found then return query select r.id, r.status, r.amount; return; end if;            -- the same form again → the first record
  select * into o from orders where orders.id = p_order for update;
  if not found then raise exception 'not_found'; end if;
  if o.driver_id is distinct from auth.uid() then raise exception 'not_allowed'; end if;
  if not acc_order(o.created_at) then raise exception 'accounting_not_started'; end if;
  if coalesce(o.pay_rules->>'settle_method', '') <> 'driver_pays' then raise exception 'not_driver_pays'; end if;
  if o.status not in ('ready', 'pickedup', 'delivered') then raise exception 'bad_transition'; end if;
  if v_a is null or v_a <= 0 or v_a > 1000000 or char_length(coalesce(v_ref, '')) > 80 then raise exception 'bad_value'; end if;
  if v_ref is null and p_proof is null then raise exception 'proof_required'; end if;
  if p_proof is not null and (p_proof !~ ('^' || auth.uid()::text || '/' || p_order::text || '/[A-Za-z0-9_-]{8,64}\.jpg$') or not proof_exists(p_proof, auth.uid())) then raise exception 'photo_missing'; end if;
  if exists (select 1 from driver_store_payments d where d.order_id = p_order and d.status <> 'disputed') then raise exception 'already_recorded'; end if;
  insert into driver_store_payments(order_id, store_id, driver_id, amount, reference, proof_path, client_key)
  values (p_order, o.store_id, auth.uid(), v_a, v_ref, p_proof, p_key) returning * into r;
  return query select r.id, r.status, r.amount;
end $$;
-- the store (owner) or finance confirms or disputes a courier's payment; who decided is kept
create or replace function decide_store_payment(p_id bigint, p_ok boolean, p_note text default null) returns void
language plpgsql security definer set search_path = public as $$
declare r driver_store_payments;
begin
  select * into r from driver_store_payments where id = p_id for update;
  if not found then raise exception 'not_found'; end if;
  if not (owns_store(r.store_id) or has_perm('finance')) then raise exception 'not_allowed'; end if;
  if p_ok is null then raise exception 'bad_value'; end if;
  if r.status <> 'claimed' then raise exception 'already_decided'; end if;
  update driver_store_payments set status = case when p_ok then 'confirmed' else 'disputed' end, decided_by = auth.uid(),
         decided_by_name = (select name from profiles where profiles.id = auth.uid()), decided_at = now(),
         decision_note = nullif(left(btrim(coalesce(p_note, '')), 200), '') where id = p_id;
end $$;
-- platform ↔ courier: cash handed to the platform (≤ cash he holds) or courier pay paid out (≤ pay owed); never netted
create or replace function record_driver_settlement(p_driver uuid, p_direction text, p_amount numeric, p_reference text, p_note text, p_key text)
returns table(id bigint, amount numeric, before_amount numeric, after_amount numeric, recorded_at timestamptz)
language plpgsql security definer set search_path = public as $$
#variable_conflict use_column
declare v_a numeric := round(p_amount, 2); v_b numeric; v_ref text := nullif(btrim(coalesce(p_reference, '')), ''); r platform_driver_settlements; x record;
begin
  if not has_perm('finance') then raise exception 'not_allowed'; end if;
  if p_key is null or p_key !~ '^[A-Za-z0-9_-]{8,64}$' or p_direction not in ('driver_to_platform', 'platform_to_driver') then raise exception 'bad_value'; end if;
  if v_a is null or v_a <= 0 or v_a > 1000000 or char_length(coalesce(v_ref, '')) > 80 or char_length(coalesce(p_note, '')) > 200 then raise exception 'bad_value'; end if;
  perform 1 from profiles where profiles.id = p_driver and role = 'driver' for update;      -- one settlement at a time per courier
  if not found then raise exception 'not_found'; end if;
  select * into r from platform_driver_settlements where recorded_by = auth.uid() and client_key = p_key;
  if found then
    if r.driver_id <> p_driver or r.direction <> p_direction or r.amount <> v_a then raise exception 'bad_value'; end if;
    return query select r.id, r.amount, r.before_amount, r.after_amount, r.recorded_at; return;
  end if;
  if acc_start() is null then raise exception 'accounting_not_started'; end if;
  select * into x from driver_position(p_driver);
  v_b := case when p_direction = 'driver_to_platform' then x.cash_held else x.earnings_due end;
  if coalesce(v_b, 0) <= 0 then raise exception 'nothing_due'; end if;
  if v_a > v_b then raise exception 'amount_too_high'; end if;
  insert into platform_driver_settlements(driver_id, direction, amount, before_amount, after_amount, reference, note, recorded_by, recorded_by_name, client_key)
  values (p_driver, p_direction, v_a, v_b, v_b - v_a, v_ref, nullif(left(btrim(coalesce(p_note, '')), 200), ''), auth.uid(),
          (select name from profiles where profiles.id = auth.uid()), p_key) returning * into r;
  return query select r.id, r.amount, r.before_amount, r.after_amount, r.recorded_at;
end $$;
-- platform → store: a settlement (≤ what the store is still owed, counting pending ones), method + reference + status
create or replace function record_store_settlement(p_store uuid, p_amount numeric, p_method text, p_reference text, p_note text, p_status text, p_key text)
returns table(id bigint, amount numeric, before_amount numeric, after_amount numeric, status text)
language plpgsql security definer set search_path = public as $$
#variable_conflict use_column
declare v_a numeric := round(p_amount, 2); v_b numeric; v_ref text := nullif(btrim(coalesce(p_reference, '')), ''); r platform_store_settlements;
begin
  if not has_perm('finance') then raise exception 'not_allowed'; end if;
  if p_key is null or p_key !~ '^[A-Za-z0-9_-]{8,64}$' or p_method not in ('cash', 'bank', 'online') or p_status not in ('pending', 'done') then raise exception 'bad_value'; end if;
  if v_a is null or v_a <= 0 or char_length(coalesce(v_ref, '')) > 80 or char_length(coalesce(p_note, '')) > 200 then raise exception 'bad_value'; end if;
  if p_status = 'done' and v_ref is null then raise exception 'reference_required'; end if;
  perform 1 from stores where stores.id = p_store for update;                              -- one settlement at a time per store
  if not found then raise exception 'not_found'; end if;
  select * into r from platform_store_settlements where recorded_by = auth.uid() and client_key = p_key;
  if found then
    if r.store_id <> p_store or r.amount <> v_a then raise exception 'bad_value'; end if;
    return query select r.id, r.amount, r.before_amount, r.after_amount, r.status; return;
  end if;
  if acc_start() is null then raise exception 'accounting_not_started'; end if;
  select balance into v_b from store_position(p_store);
  if coalesce(v_b, 0) <= 0 then raise exception 'nothing_due'; end if;
  if v_a > v_b then raise exception 'amount_too_high'; end if;
  insert into platform_store_settlements(store_id, amount, method, status, before_amount, after_amount, reference, note, recorded_by, recorded_by_name, client_key,
                                         status_by, status_by_name, status_at)
  values (p_store, v_a, p_method, p_status, v_b, v_b - v_a, v_ref, nullif(left(btrim(coalesce(p_note, '')), 200), ''), auth.uid(),
          (select name from profiles where profiles.id = auth.uid()), p_key,
          case when p_status = 'done' then auth.uid() end, case when p_status = 'done' then (select name from profiles where profiles.id = auth.uid()) end,
          case when p_status = 'done' then now() end) returning * into r;
  return query select r.id, r.amount, r.before_amount, r.after_amount, r.status;
end $$;
create or replace function set_store_settlement_status(p_id bigint, p_status text, p_reference text default null) returns void
language plpgsql security definer set search_path = public as $$
declare r platform_store_settlements; v_ref text := nullif(btrim(coalesce(p_reference, '')), '');
begin
  if not has_perm('finance') then raise exception 'not_allowed'; end if;
  if p_status not in ('done', 'failed') then raise exception 'bad_value'; end if;
  select * into r from platform_store_settlements where id = p_id for update;
  if not found then raise exception 'not_found'; end if;
  if r.status <> 'pending' then raise exception 'already_decided'; end if;
  if p_status = 'done' and coalesce(r.reference, v_ref) is null then raise exception 'reference_required'; end if;
  update platform_store_settlements set status = p_status, reference = coalesce(r.reference, v_ref), status_by = auth.uid(),
         status_by_name = (select name from profiles where profiles.id = auth.uid()), status_at = now() where id = p_id;
end $$;
do $$ declare f text; begin
  foreach f in array array['record_store_payment(bigint,numeric,text,text,text)', 'decide_store_payment(bigint,boolean,text)',
    'record_driver_settlement(uuid,text,numeric,text,text,text)', 'record_store_settlement(uuid,numeric,text,text,text,text,text)',
    'set_store_settlement_status(bigint,text,text)'] loop
    execute 'revoke all on function ' || f || ' from public, anon'; execute 'grant execute on function ' || f || ' to authenticated';
  end loop;
end $$;
revoke all on function acc_order(timestamptz) from public, anon, authenticated;

-- ---------- the old cash functions only look at orders from BEFORE the start (no double counting, nothing moved) ----------
create or replace function cash_balances() returns table(driver_id uuid, balance numeric)
language sql stable security definer set search_path = public as $$
  select o.driver_id, coalesce(sum(o.cash_collected), 0)::numeric
    from orders o
   where o.status = 'delivered' and o.cash_collected is not null and o.cash_settled_at is null
     and o.driver_id is not null and (has_perm('finance') or o.driver_id = auth.uid())
     and (acc_start() is null or o.created_at < acc_start())                    -- patch 38
   group by o.driver_id
$$;
create or replace function settle_driver_cash(p_driver uuid) returns numeric
language plpgsql security definer set search_path = public as $$
declare tot numeric;
begin
  if not has_perm('finance') then raise exception 'not_allowed'; end if;
  perform 1 from profiles where id = p_driver for update;                       -- patch 38: one at a time per courier
  select coalesce(sum(cash_collected), 0) into tot from orders
   where driver_id = p_driver and status = 'delivered' and cash_collected is not null and cash_settled_at is null
     and (acc_start() is null or created_at < acc_start());
  update orders set cash_settled_at = now()
   where driver_id = p_driver and status = 'delivered' and cash_collected is not null and cash_settled_at is null
     and (acc_start() is null or created_at < acc_start());
  return tot;
end $$;

commit;
