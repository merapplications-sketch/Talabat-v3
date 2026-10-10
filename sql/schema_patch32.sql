-- =============================================================================================
-- PATCH 32 — batch 1 (owner decisions of 10 Oct 2026, evening). Run after patch 31. Safe to run again.
--  * Points: 1000 points = 10 TJS, used ONLY in whole vouchers (1000, 2000 ...), only when the dishes reach
--    the restaurant's minimum (default 30 TJS, the admin can set it per restaurant). Earning rounded UP.
--  * +10 points for rating an order (once per order).
--  * Cashback: each restaurant sets its own % (and pays it); without it the app-wide % (default 0 = off).
--  * Order options: leave at the door, what to do if a dish is missing, a gift (recipient name + phone,
--    readable only by the customer, the courier of the order and the admin/staff).
--  * Best-selling dishes (last 30 days) and the restaurants' real preparation speed ("Express" <= 15 min).
-- =============================================================================================

-- ---------- settings ----------
alter table app_settings drop constraint if exists app_settings_key_check;
alter table app_settings add constraint app_settings_key_check check (key in (
  'delivery_free_km', 'delivery_step_km', 'delivery_step_price', 'delivery_max_km', 'delivery_road_factor',
  'loyalty_earn_per_tjs', 'loyalty_points_per_tjs', 'loyalty_min_redeem', 'loyalty_expiry_days', 'cashback_pct',
  'loyalty_voucher_points', 'loyalty_min_order', 'loyalty_rate_reward'));
insert into app_settings(key, value) values ('loyalty_voucher_points', 1000), ('loyalty_min_order', 30), ('loyalty_rate_reward', 10)
on conflict (key) do nothing;
-- owner decision: 1000 points = 10 TJS (only if the old default 1000 points = 1 TJS was never changed)
update app_settings set value = 100 where key = 'loyalty_points_per_tjs' and value = 1000;

create or replace function set_setting(p_key text, p_value numeric) returns void
language plpgsql security definer set search_path = public as $$
begin
  if not is_admin() then raise exception 'not_allowed'; end if;
  if p_value is null
     or (p_key = 'delivery_free_km' and p_value not between 0 and 50)
     or (p_key = 'delivery_step_km' and p_value not between 0.1 and 5)
     or (p_key = 'delivery_step_price' and p_value not between 0 and 1000)
     or (p_key = 'delivery_max_km' and p_value not between 1 and 100)
     or (p_key = 'delivery_road_factor' and p_value not between 1 and 3)
     or (p_key = 'loyalty_earn_per_tjs' and (p_value not between 0 and 1000 or p_value <> trunc(p_value)))
     or (p_key = 'loyalty_points_per_tjs' and (p_value not between 1 and 100000 or p_value <> trunc(p_value)))
     or (p_key = 'loyalty_min_redeem' and (p_value not between 0 and 1000000 or p_value <> trunc(p_value)))
     or (p_key = 'loyalty_expiry_days' and (p_value not between 1 and 3650 or p_value <> trunc(p_value)))
     or (p_key = 'cashback_pct' and p_value not between 0 and 50)
     or (p_key = 'loyalty_voucher_points' and (p_value not between 1 and 1000000 or p_value <> trunc(p_value)))
     or (p_key = 'loyalty_min_order' and p_value not between 0 and 10000)
     or (p_key = 'loyalty_rate_reward' and (p_value not between 0 and 10000 or p_value <> trunc(p_value))) then
    raise exception 'bad_value';
  end if;
  update app_settings set value = p_value, updated_at = now(), updated_by = auth.uid() where key = p_key;
  if not found then raise exception 'bad_value'; end if;
end $$;
revoke all on function set_setting(text, numeric) from public, anon;
grant execute on function set_setting(text, numeric) to authenticated;

create or replace function loyalty_setting(p_key text) returns numeric
language sql stable security definer set search_path = public as $$
  select coalesce((select value from app_settings where key = p_key),
    case p_key when 'loyalty_earn_per_tjs' then 10 when 'loyalty_points_per_tjs' then 100 when 'loyalty_min_redeem' then 1000
               when 'loyalty_expiry_days' then 90 when 'loyalty_voucher_points' then 1000 when 'loyalty_min_order' then 30
               when 'loyalty_rate_reward' then 10 else 0 end)
$$;
revoke all on function loyalty_setting(text) from public, anon, authenticated;

-- ---------- per restaurant: minimum order for points (admin), cashback % (the restaurant) ----------
alter table stores add column if not exists points_min_order numeric check (points_min_order is null or points_min_order between 0 and 10000);
alter table stores add column if not exists cashback_pct numeric check (cashback_pct is null or cashback_pct between 0 and 50);

create or replace function set_store_loyalty(p_store uuid, p_min_order numeric, p_cashback numeric) returns void
language plpgsql security definer set search_path = public as $$
begin
  if not (is_admin() or has_perm('stores')) then raise exception 'not_allowed'; end if;
  if (p_min_order is not null and p_min_order not between 0 and 10000) or (p_cashback is not null and p_cashback not between 0 and 50) then raise exception 'bad_value'; end if;
  update stores set points_min_order = p_min_order, cashback_pct = p_cashback where id = p_store;
  if not found then raise exception 'not_found'; end if;
end $$;
revoke all on function set_store_loyalty(uuid, numeric, numeric) from public, anon;
grant execute on function set_store_loyalty(uuid, numeric, numeric) to authenticated;

create or replace function set_my_cashback(p_store uuid, p_pct numeric) returns void
language plpgsql security definer set search_path = public as $$
begin
  if not exists (select 1 from stores where id = p_store and owner_id = auth.uid()) then raise exception 'not_allowed'; end if;
  if p_pct is null or p_pct not between 0 and 50 then raise exception 'bad_value'; end if;
  update stores set cashback_pct = round(p_pct, 1) where id = p_store;
end $$;
revoke all on function set_my_cashback(uuid, numeric) from public, anon;
grant execute on function set_my_cashback(uuid, numeric) to authenticated;

-- ---------- the customer's points summary (+ the new rules) ----------
create or replace function loyalty_summary() returns jsonb
language sql stable security definer set search_path = public as $$
  select jsonb_build_object(
    'balance', loyalty_balance(auth.uid()),
    'next_exp_at', (select min(expires_at) from loyalty_lots where user_id = auth.uid() and points_left > 0 and expires_at > now()),
    'next_exp_pts', (select coalesce(sum(points_left), 0) from loyalty_lots where user_id = auth.uid() and points_left > 0 and expires_at > now()
                       and expires_at < (select min(expires_at) from loyalty_lots where user_id = auth.uid() and points_left > 0 and expires_at > now()) + interval '1 day'),
    'earn_per_tjs', loyalty_setting('loyalty_earn_per_tjs'), 'points_per_tjs', loyalty_setting('loyalty_points_per_tjs'),
    'min_redeem', loyalty_setting('loyalty_min_redeem'), 'expiry_days', loyalty_setting('loyalty_expiry_days'), 'cashback_pct', loyalty_setting('cashback_pct'),
    'voucher_points', loyalty_setting('loyalty_voucher_points'), 'min_order', loyalty_setting('loyalty_min_order'), 'rate_reward', loyalty_setting('loyalty_rate_reward'))
  where auth.uid() is not null
$$;
revoke all on function loyalty_summary() from public, anon;
grant execute on function loyalty_summary() to authenticated;

-- ---------- +10 points for rating an order (once per order) ----------
alter table loyalty_lots drop constraint if exists loyalty_lots_kind_check;
alter table loyalty_lots add constraint loyalty_lots_kind_check check (kind in ('earn', 'return', 'reward'));
alter table loyalty_ledger drop constraint if exists loyalty_ledger_kind_check;
alter table loyalty_ledger add constraint loyalty_ledger_kind_check check (kind in ('earn', 'spend', 'return', 'reward'));
create unique index if not exists loyalty_one_reward_per_order on loyalty_lots (order_id) where kind = 'reward';

create or replace function trg_rating_reward() returns trigger language plpgsql security definer set search_path = public as $$
declare v_pts int := loyalty_setting('loyalty_rate_reward')::int; v_id bigint;
begin
  if v_pts > 0 and new.customer_id is not null and new.order_id is not null then
    insert into loyalty_lots(user_id, points, points_left, expires_at, order_id, kind)
    values (new.customer_id, v_pts, v_pts, now() + make_interval(days => loyalty_setting('loyalty_expiry_days')::int), new.order_id, 'reward')
    on conflict (order_id) where kind = 'reward' do nothing returning id into v_id;
    if v_id is not null then insert into loyalty_ledger(user_id, points, kind, order_id) values (new.customer_id, v_pts, 'reward', new.order_id); end if;
  end if;
  return new;
end $$;
drop trigger if exists trg_ratings_reward on ratings;
create trigger trg_ratings_reward after insert on ratings for each row execute function trg_rating_reward();

-- ---------- order options ----------
alter table orders add column if not exists leave_at_door boolean not null default false;
alter table orders add column if not exists substitution text not null default 'call' check (substitution in ('call', 'replace', 'remove'));
alter table orders add column if not exists is_gift boolean not null default false;
create table if not exists order_recipient (
  order_id bigint primary key references orders(id) on delete cascade,
  name text not null check (char_length(name) between 2 and 60),
  phone text not null check (char_length(phone) <= 20)
);
alter table order_recipient enable row level security;
drop policy if exists recipient_read on order_recipient;
create policy recipient_read on order_recipient for select using (
  is_admin() or has_perm('orders') or has_perm('support')
  or exists (select 1 from orders o where o.id = order_recipient.order_id and (o.customer_id = auth.uid() or o.driver_id = auth.uid())));
revoke insert, update, delete on order_recipient from anon, authenticated;

-- ---------- best-selling dishes and real preparation speed (for badges) ----------
create or replace function best_dishes(p_store uuid default null, p_limit int default 20) returns table(item_id uuid, store_id uuid, cnt bigint)
language sql stable security definer set search_path = public as $$
  select oi.item_id, o.store_id, sum(oi.qty)::bigint as cnt
    from order_items oi join orders o on o.id = oi.order_id
    join menu_items m on m.id = oi.item_id and m.available and m.approved
    join stores s on s.id = o.store_id and s.is_active
   where o.status = 'delivered' and o.created_at > now() - interval '30 days' and (p_store is null or o.store_id = p_store)
   group by oi.item_id, o.store_id
  having sum(oi.qty) >= 3
   order by cnt desc
   limit least(greatest(coalesce(p_limit, 20), 1), 50)
$$;
revoke all on function best_dishes(uuid, int) from public, anon;
grant execute on function best_dishes(uuid, int) to authenticated;

create or replace function store_speed() returns table(store_id uuid, avg_min numeric, n int)
language sql stable security definer set search_path = public as $$
  select o.store_id, round(avg(extract(epoch from r.at - p.at) / 60)::numeric, 1), count(*)::int
    from orders o
    join lateral (select min(at) as at from order_events e where e.order_id = o.id and e.kind = 'preparing') p on p.at is not null
    join lateral (select min(at) as at from order_events e where e.order_id = o.id and e.kind = 'ready') r on r.at is not null
   where o.created_at > now() - interval '30 days' and r.at > p.at
   group by o.store_id
$$;
revoke all on function store_speed() from public, anon;
grant execute on function store_speed() to authenticated;

-- ---------- earning / cashback trigger (rounded up; the restaurant's own cashback %) ----------
create or replace function trg_loyalty() returns trigger language plpgsql security definer set search_path = public as $$
declare v_paid numeric; v_pts int; v_cb numeric;
begin
  if new.status = 'delivered' and old.status <> 'delivered' and new.loyalty_done_at is null then
    v_paid := greatest(0, coalesce(new.subtotal, 0) - coalesce(new.discount, 0) - coalesce(new.promo_discount, 0) - coalesce(new.points_value, 0));
    v_pts := ceil(v_paid * loyalty_setting('loyalty_earn_per_tjs') - 0.000001)::int;            -- fractions in favour of the customer
    if v_pts > 0 then
      insert into loyalty_lots(user_id, points, points_left, expires_at, order_id, kind)
      values (new.customer_id, v_pts, v_pts, now() + make_interval(days => loyalty_setting('loyalty_expiry_days')::int), new.id, 'earn')
      on conflict (order_id) where kind = 'earn' do nothing;
      insert into loyalty_ledger(user_id, points, kind, order_id) values (new.customer_id, v_pts, 'earn', new.id);
    end if;
    v_cb := round(v_paid * coalesce((select cashback_pct from stores where id = new.store_id), loyalty_setting('cashback_pct')) / 100, 2);   -- the restaurant's own % (it pays it)
    if v_cb > 0 then
      insert into wallet_entries(user_id, amount, kind, order_id, note) values (new.customer_id, v_cb, 'cashback', new.id, null)
      on conflict (order_id) where kind = 'cashback' do nothing;
    end if;
    new.points_earned := greatest(v_pts, 0); new.cashback := greatest(v_cb, 0); new.loyalty_done_at := now();
  end if;
  if new.status in ('rejected', 'cancelled') and old.status not in ('rejected', 'cancelled')
     and coalesce(new.points_used, 0) > 0 and new.points_returned_at is null then
    insert into loyalty_lots(user_id, points, points_left, expires_at, order_id, kind)
    values (new.customer_id, new.points_used, new.points_used, now() + make_interval(days => loyalty_setting('loyalty_expiry_days')::int), new.id, 'return')
    on conflict (order_id) where kind = 'return' do nothing;
    insert into loyalty_ledger(user_id, points, kind, order_id) values (new.customer_id, new.points_used, 'return', new.id);
    new.points_returned_at := now();
  end if;
  return new;
end $$;
drop trigger if exists trg_orders_loyalty on orders;
create trigger trg_orders_loyalty before update of status on orders for each row execute function trg_loyalty();


-- ---------- place_order: whole vouchers, minimum order, order options ----------
drop function if exists place_order(uuid, jsonb, numeric, text, text, double precision, double precision, text, text, numeric, numeric, integer);
create or replace function place_order(p_store uuid, p_items jsonb, p_tip numeric default 0, p_payment text default 'cash',
  p_address text default '', p_lat float8 default null, p_lng float8 default null, p_promo text default null, p_key text default null, p_fee numeric default null, p_wallet numeric default null, p_points integer default null, p_extra jsonb default null)
returns bigint language plpgsql security definer set search_path = public as $$
declare s stores; pr profiles; it record; v_item menu_items; pl jsonb; v_id bigint; v_sub numeric; v_fee numeric; v_pay numeric; v_disc numeric; v_base numeric; v_gate numeric;
        v_promo numeric := 0; v_tip numeric; v_km float8; v_code text := null; v_dq jsonb; v_cphone text; v_total numeric; v_bal numeric; v_w numeric;
        v_hh int := 0; v_all numeric; v_hdisc numeric := 0; v_rate numeric; v_min numeric; v_lb int; v_pts int := 0; v_pval numeric := 0; v_cap numeric;
        v_step numeric; v_mo numeric; v_subst text; v_door boolean; v_gn text; v_gp text;
begin
  if p_wallet is not null and p_wallet < 0 then raise exception 'bad_value'; end if;
  if p_points is not null and (p_points < 0 or p_points > 100000000) then raise exception 'bad_value'; end if;
  -- order options (v50): leave at the door, what to do if a dish is missing, a gift for someone else
  v_door := coalesce((p_extra->>'door')::boolean, false);
  v_subst := coalesce(p_extra->>'subst', 'call');
  if v_subst not in ('call', 'replace', 'remove') then raise exception 'bad_value'; end if;
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
  if p_fee is not null and abs(p_fee - v_fee) > 0.009 then raise exception 'fee_changed'; end if;   -- the price shown to the customer must be the price charged
  v_tip := case when p_tip in (0,3,5,10) then p_tip else 0 end;

  begin
    insert into orders(store_id, customer_id, customer_name, payment, address, lat, lng, client_key, leave_at_door, substitution, is_gift)
    values (p_store, auth.uid(), pr.name, left(p_payment,40), left(p_address,200), p_lat, p_lng, p_key, v_door, v_subst, v_gn is not null)
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

  update orders set subtotal = v_sub, discount = v_disc + v_hdisc, delivery_fee = v_fee, tip = v_tip,
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
  return v_id;
end $$;
revoke all on function place_order(uuid, jsonb, numeric, text, text, double precision, double precision, text, text, numeric, numeric, integer, jsonb) from public, anon;
grant execute on function place_order(uuid, jsonb, numeric, text, text, double precision, double precision, text, text, numeric, numeric, integer, jsonb) to authenticated;
