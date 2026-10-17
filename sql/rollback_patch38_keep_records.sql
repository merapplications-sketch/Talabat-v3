-- =============================================================================================
-- PARTIAL ROLLBACK of patch 38 when money records EXIST: only place_order goes back to the live definition (the store
-- agreements stop being enforced at checkout). Every money record, position, settlement function, the start marker and the
-- old-cash split stay, so nothing already handed over or paid looks unpaid again. Not run anywhere.
-- =============================================================================================
begin;
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
        v_at timestamptz; v_waived numeric := 0; v_gid uuid; g group_orders;
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
  if coalesce(p_wallet, 0) > 0 then
    select total into v_total from orders where id = v_id;
    perform 1 from profiles where id = auth.uid() for update;           -- two orders at the same moment cannot spend the same money
    v_bal := wallet_balance();
    v_w := round(least(p_wallet, v_bal, v_total), 2);
    if v_w <= 0 or abs(v_w - round(p_wallet, 2)) > 0.009 then raise exception 'wallet_changed'; end if;   -- the customer saw another amount: ask again
    insert into wallet_entries(user_id, amount, kind, order_id) values (auth.uid(), -v_w, 'spend', v_id);
    update orders set wallet_used = v_w, payment = case when v_w >= v_total then 'wallet' else payment end where id = v_id;
  end if;
  if v_gid is not null then update group_orders set status = 'placed', order_id = v_id, closed_at = coalesce(closed_at, now()) where id = v_gid; end if;
  return v_id;
end $function$;
commit;
