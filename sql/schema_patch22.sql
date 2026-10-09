-- Patch 22: repair + hardening found by the security self-check (run AFTER patch 21; safe to run more than once)
--
-- 1) A customer could erase his own phone number (this lets him dodge the "no change during an active order / once a day" rules).
--    The profile guard, the phone trigger and the audit trigger of patch 20 are installed again, exactly as written there,
--    in case any part of patch 20 was not applied.
-- 2) place_order ignored a NEGATIVE wallet amount and simply created the order. It is now refused (bad_value).
--    (No money could be created: the amount was ignored. But a refusal is the correct behaviour.)

------------------------------------------------------------------------------------------------
-- 1) PROFILE GUARD + PHONE RULES (same as patch 20)
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
drop trigger if exists trg_guard_profile on profiles;
create trigger trg_guard_profile before update on profiles for each row execute function guard_profile();
drop trigger if exists trg_profile_phone on profiles;
create trigger trg_profile_phone before update of phone on profiles for each row execute function trg_profile_phone();
drop trigger if exists trg_audit_profiles on profiles;
create trigger trg_audit_profiles after update on profiles for each row
  execute function audit_changes('id', 'role', 'driver_status', 'cash_limit', 'accept_blocked', 'banned_at', 'banned_reason', 'phone');

------------------------------------------------------------------------------------------------
-- 2) place_order: a negative wallet amount is refused (same signature as patch 21)
------------------------------------------------------------------------------------------------
create or replace function place_order(p_store uuid, p_items jsonb, p_tip numeric default 0, p_payment text default 'cash',
  p_address text default '', p_lat float8 default null, p_lng float8 default null, p_promo text default null, p_key text default null, p_fee numeric default null, p_wallet numeric default null)
returns bigint language plpgsql security definer set search_path = public as $$
declare s stores; pr profiles; it record; v_item menu_items; pl jsonb; v_id bigint; v_sub numeric; v_fee numeric; v_pay numeric; v_disc numeric; v_base numeric; v_gate numeric;
        v_promo numeric := 0; v_tip numeric; v_km float8; v_code text := null; v_dq jsonb; v_cphone text; v_total numeric; v_bal numeric; v_w numeric;
begin
  if p_wallet is not null and p_wallet < 0 then raise exception 'bad_value'; end if;   -- a negative amount would mean ADDING money: refuse it
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
end $$;
revoke all on function place_order(uuid, jsonb, numeric, text, text, double precision, double precision, text, text, numeric, numeric) from public, anon;
grant execute on function place_order(uuid, jsonb, numeric, text, text, double precision, double precision, text, text, numeric, numeric) to authenticated;
