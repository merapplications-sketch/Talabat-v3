-- =============================================================================================
-- PATCH 29 — LOYALTY POINTS, CASHBACK and HAPPY HOUR (owner decisions of 10 Oct 2026)
-- Run once in the Supabase SQL Editor AFTER patch 28 (safe to run again).
--
--  * Points: earned when an order is DELIVERED, 10 points per 1 TJS the customer paid for the dishes
--    (not delivery, not the tip). They expire after N days (default 90). They can be used at checkout
--    as a discount once the customer has at least the minimum (default 1000 points); value:
--    1000 points = 1 TJS by default. All numbers are set by the admin (Loyalty tab).
--  * Cashback: a % (default 0 = off) of what the customer paid for the dishes goes to his WALLET when
--    the order is delivered (wallet kind 'cashback').
--  * Happy hour: the admin schedules windows (days of the week + time, Dushanbe time, all restaurants
--    or one) with a discount %. Each dish gets the best of store / dish / happy-hour discount (never
--    stacked). The EXTRA part given by the happy hour is paid by the platform (orders.hh_discount), so
--    the restaurant's revenue and commission are unchanged.
--  * Cancelled / rejected order: the points used come back (once). Points and cashback are given once.
--  * Nobody writes these tables directly: only place_order, the order triggers and the admin RPCs.
-- =============================================================================================

-- ---------- settings (admin edits them with set_setting) ----------
alter table app_settings drop constraint if exists app_settings_key_check;
alter table app_settings add constraint app_settings_key_check check (key in (
  'delivery_free_km', 'delivery_step_km', 'delivery_step_price', 'delivery_max_km', 'delivery_road_factor',
  'loyalty_earn_per_tjs', 'loyalty_points_per_tjs', 'loyalty_min_redeem', 'loyalty_expiry_days', 'cashback_pct'));
insert into app_settings(key, value) values
  ('loyalty_earn_per_tjs', 10), ('loyalty_points_per_tjs', 1000), ('loyalty_min_redeem', 1000), ('loyalty_expiry_days', 90), ('cashback_pct', 0)
on conflict (key) do nothing;

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
     or (p_key = 'cashback_pct' and p_value not between 0 and 50) then
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
    case p_key when 'loyalty_earn_per_tjs' then 10 when 'loyalty_points_per_tjs' then 1000 when 'loyalty_min_redeem' then 1000
               when 'loyalty_expiry_days' then 90 else 0 end)
$$;
revoke all on function loyalty_setting(text) from public, anon, authenticated;

-- ---------- happy hour ----------
create table if not exists happy_hours (
  id bigint generated always as identity primary key,
  title text not null check (char_length(btrim(title)) between 1 and 60),
  store_id uuid references stores(id) on delete cascade,          -- null = all restaurants
  days smallint[] not null default '{1,2,3,4,5,6,7}' check (array_length(days, 1) between 1 and 7 and days <@ '{1,2,3,4,5,6,7}'::smallint[]),
  start_time time not null,
  end_time time not null check (end_time <> start_time),           -- end < start = goes past midnight
  discount_pct int not null check (discount_pct between 1 and 90),
  active boolean not null default true,
  created_at timestamptz not null default now(),
  created_by uuid
);
create index if not exists happy_hours_active_idx on happy_hours (active, store_id);
alter table happy_hours enable row level security;
drop policy if exists hh_read on happy_hours;
create policy hh_read on happy_hours for select using (auth.uid() is not null);        -- everyone signed in sees the schedule (prices)
drop policy if exists hh_write on happy_hours;
create policy hh_write on happy_hours for all using (is_admin()) with check (is_admin());
revoke all on happy_hours from anon;
grant select, insert, update, delete on happy_hours to authenticated;            -- the policy above lets only the admin write
do $$ begin
  begin alter publication supabase_realtime add table happy_hours; exception when duplicate_object or undefined_object then null; end;
end $$;

-- best happy-hour % for a restaurant at a moment (Dushanbe local time); 0 when none
create or replace function happy_hour_pct(p_store uuid, p_at timestamptz default now()) returns int
language sql stable security definer set search_path = public as $$
  with l as (select (p_at at time zone 'Asia/Dushanbe') as t)
  select coalesce(max(h.discount_pct), 0)::int
    from happy_hours h, l
   where h.active and (h.store_id is null or h.store_id = p_store)
     and (
       (h.start_time < h.end_time and extract(isodow from l.t)::smallint = any(h.days) and l.t::time >= h.start_time and l.t::time < h.end_time)
       or (h.start_time > h.end_time and (
            (extract(isodow from l.t)::smallint = any(h.days) and l.t::time >= h.start_time)
         or (extract(isodow from (l.t - interval '1 day'))::smallint = any(h.days) and l.t::time < h.end_time)))
     )
$$;
grant execute on function happy_hour_pct(uuid, timestamptz) to authenticated;

-- ---------- points ----------
create table if not exists loyalty_lots (                           -- one row per earning; spending takes from the oldest first
  id bigint generated always as identity primary key,
  user_id uuid not null references profiles(id) on delete cascade,
  points int not null check (points > 0),
  points_left int not null check (points_left >= 0),
  expires_at timestamptz not null,
  order_id bigint references orders(id) on delete set null,
  kind text not null check (kind in ('earn', 'return')),
  created_at timestamptz not null default now()
);
create index if not exists loyalty_lots_user_idx on loyalty_lots (user_id, expires_at) where points_left > 0;
create unique index if not exists loyalty_one_earn_per_order on loyalty_lots (order_id) where kind = 'earn';
create unique index if not exists loyalty_one_return_per_order on loyalty_lots (order_id) where kind = 'return';

create table if not exists loyalty_ledger (                         -- history shown to the customer
  id bigint generated always as identity primary key,
  user_id uuid not null references profiles(id) on delete cascade,
  points int not null check (points <> 0),
  kind text not null check (kind in ('earn', 'spend', 'return')),
  order_id bigint references orders(id) on delete set null,
  created_at timestamptz not null default now()
);
create index if not exists loyalty_ledger_user_idx on loyalty_ledger (user_id, created_at desc);
alter table loyalty_lots enable row level security;
alter table loyalty_ledger enable row level security;
drop policy if exists loyalty_lots_read on loyalty_lots;
create policy loyalty_lots_read on loyalty_lots for select using (user_id = auth.uid() or is_admin());
drop policy if exists loyalty_ledger_read on loyalty_ledger;
create policy loyalty_ledger_read on loyalty_ledger for select using (user_id = auth.uid() or is_admin());
revoke insert, update, delete on loyalty_lots, loyalty_ledger from anon, authenticated;

create or replace function loyalty_balance(p_user uuid) returns int
language sql stable security definer set search_path = public as $$
  select coalesce(sum(points_left), 0)::int from loyalty_lots where user_id = p_user and points_left > 0 and expires_at > now()
$$;
revoke all on function loyalty_balance(uuid) from public, anon, authenticated;

-- the customer's points: balance, what expires first, and the rules (for the app)
create or replace function loyalty_summary() returns jsonb
language sql stable security definer set search_path = public as $$
  select jsonb_build_object(
    'balance', loyalty_balance(auth.uid()),
    'next_exp_at', (select min(expires_at) from loyalty_lots where user_id = auth.uid() and points_left > 0 and expires_at > now()),
    'next_exp_pts', (select coalesce(sum(points_left), 0) from loyalty_lots where user_id = auth.uid() and points_left > 0 and expires_at > now()
                       and expires_at < (select min(expires_at) from loyalty_lots where user_id = auth.uid() and points_left > 0 and expires_at > now()) + interval '1 day'),
    'earn_per_tjs', loyalty_setting('loyalty_earn_per_tjs'), 'points_per_tjs', loyalty_setting('loyalty_points_per_tjs'),
    'min_redeem', loyalty_setting('loyalty_min_redeem'), 'expiry_days', loyalty_setting('loyalty_expiry_days'), 'cashback_pct', loyalty_setting('cashback_pct'))
  where auth.uid() is not null
$$;
revoke all on function loyalty_summary() from public, anon;
grant execute on function loyalty_summary() to authenticated;

-- take points from the oldest lots that have not expired (called only inside place_order, under the profile lock)
create or replace function loyalty_spend(p_user uuid, p_points int, p_order bigint) returns void
language plpgsql security definer set search_path = public as $$
declare l record; v_left int := p_points; v_take int;
begin
  for l in select id, points_left from loyalty_lots where user_id = p_user and points_left > 0 and expires_at > now()
            order by expires_at, id for update loop
    exit when v_left <= 0;
    v_take := least(l.points_left, v_left);
    update loyalty_lots set points_left = points_left - v_take where id = l.id;
    v_left := v_left - v_take;
  end loop;
  if v_left > 0 then raise exception 'points_changed'; end if;
  insert into loyalty_ledger(user_id, points, kind, order_id) values (p_user, -p_points, 'spend', p_order);
end $$;
revoke all on function loyalty_spend(uuid, int, bigint) from public, anon, authenticated;

-- ---------- orders ----------
alter table orders add column if not exists hh_discount numeric not null default 0 check (hh_discount >= 0);
alter table orders add column if not exists hh_pct int not null default 0;
alter table orders add column if not exists points_used int not null default 0 check (points_used >= 0);
alter table orders add column if not exists points_value numeric not null default 0 check (points_value >= 0);
alter table orders add column if not exists points_earned int not null default 0;
alter table orders add column if not exists cashback numeric not null default 0;
alter table orders add column if not exists loyalty_done_at timestamptz;
alter table orders add column if not exists points_returned_at timestamptz;

-- ---------- wallet: cashback entries ----------
alter table wallet_entries drop constraint if exists wallet_entries_kind_check;
alter table wallet_entries add constraint wallet_entries_kind_check check (kind in ('refund', 'spend', 'return', 'adjust', 'cashback'));
create unique index if not exists wallet_one_cashback_per_order on wallet_entries (order_id) where kind = 'cashback';

-- delivered: points + cashback (once). cancelled / rejected: the points used come back (once).
create or replace function trg_loyalty() returns trigger language plpgsql security definer set search_path = public as $$
declare v_paid numeric; v_pts int; v_cb numeric;
begin
  if new.status = 'delivered' and old.status <> 'delivered' and new.loyalty_done_at is null then
    v_paid := greatest(0, coalesce(new.subtotal, 0) - coalesce(new.discount, 0) - coalesce(new.hh_discount, 0) - coalesce(new.promo_discount, 0) - coalesce(new.points_value, 0));
    v_pts := floor(v_paid * loyalty_setting('loyalty_earn_per_tjs'))::int;
    if v_pts > 0 then
      insert into loyalty_lots(user_id, points, points_left, expires_at, order_id, kind)
      values (new.customer_id, v_pts, v_pts, now() + make_interval(days => loyalty_setting('loyalty_expiry_days')::int), new.id, 'earn')
      on conflict (order_id) where kind = 'earn' do nothing;
      insert into loyalty_ledger(user_id, points, kind, order_id) values (new.customer_id, v_pts, 'earn', new.id);
    end if;
    v_cb := round(v_paid * loyalty_setting('cashback_pct') / 100, 2);
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

-- ---------- place_order: happy hour + points (same rules as patch 22 otherwise) ----------
drop function if exists place_order(uuid, jsonb, numeric, text, text, double precision, double precision, text, text, numeric, numeric);
create or replace function place_order(p_store uuid, p_items jsonb, p_tip numeric default 0, p_payment text default 'cash',
  p_address text default '', p_lat float8 default null, p_lng float8 default null, p_promo text default null, p_key text default null, p_fee numeric default null, p_wallet numeric default null, p_points integer default null)
returns bigint language plpgsql security definer set search_path = public as $$
declare s stores; pr profiles; it record; v_item menu_items; pl jsonb; v_id bigint; v_sub numeric; v_fee numeric; v_pay numeric; v_disc numeric; v_base numeric; v_gate numeric;
        v_promo numeric := 0; v_tip numeric; v_km float8; v_code text := null; v_dq jsonb; v_cphone text; v_total numeric; v_bal numeric; v_w numeric;
        v_hh int := 0; v_all numeric; v_hdisc numeric := 0; v_rate numeric; v_min numeric; v_lb int; v_pts int := 0; v_pval numeric := 0; v_cap numeric;
begin
  if p_wallet is not null and p_wallet < 0 then raise exception 'bad_value'; end if;
  if p_points is not null and (p_points < 0 or p_points > 100000000) then raise exception 'bad_value'; end if;   -- a negative amount would mean ADDING money: refuse it
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

  -- each line gets the better of the store discount and its own item discount (they do not stack; paid by the restaurant).
  -- A happy hour can only make it better; the EXTRA part is paid by the platform (hh_discount), so the restaurant is not charged for it.
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

  update orders set subtotal = v_sub, discount = v_disc, delivery_fee = v_fee, tip = v_tip,
    delivery_base = (v_dq->>'base')::numeric, delivery_extra = (v_dq->>'extra')::numeric, delivery_km = (v_dq->>'km')::numeric,
    promo_code = v_code, promo_discount = v_promo, hh_discount = v_hdisc, hh_pct = v_hh,
    total = greatest(5, v_sub - v_disc - v_hdisc - v_promo + v_fee + v_tip),
    commission_pct = s.commission_pct, commission = round((v_sub - v_disc) * s.commission_pct / 100, 2),
    driver_payout = v_pay + v_tip
  where id = v_id;

  -- POINTS: the customer may pay part of the items with loyalty points (all he can use, decided here, never by the app)
  if coalesce(p_points, 0) > 0 then
    v_rate := loyalty_setting('loyalty_points_per_tjs'); v_min := loyalty_setting('loyalty_min_redeem');
    perform 1 from profiles where id = auth.uid() for update;          -- two orders at the same moment cannot spend the same points
    v_lb := loyalty_balance(auth.uid());
    if v_lb < v_min then raise exception 'points_min'; end if;
    v_cap := v_sub - v_disc - v_hdisc - v_promo;                       -- points never pay for delivery or the tip
    v_pts := least(v_lb, floor(greatest(v_cap, 0) * v_rate))::int;
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
revoke all on function place_order(uuid, jsonb, numeric, text, text, double precision, double precision, text, text, numeric, numeric, integer) from public, anon;
grant execute on function place_order(uuid, jsonb, numeric, text, text, double precision, double precision, text, text, numeric, numeric, integer) to authenticated;

-- ---------- promo check: no promo code during a happy hour (every dish already has a discount) ----------
create or replace function check_promo(p_code text, p_store uuid, p_items jsonb) returns jsonb
language plpgsql security definer set search_path = public as $$
declare
  v_uid uuid := auth.uid();
  v_bad int; v_all int;
  v_res jsonb; v_err text; v_key text;
begin
  if v_uid is null then raise exception 'auth'; end if;
  perform pg_advisory_xact_lock(hashtext('promo_guess:' || v_uid::text));   -- parallel taps are counted one by one

  select count(*) filter (where bad), count(*) into v_bad, v_all
    from promo_guess where user_id = v_uid and at > now() - interval '10 minutes';
  if v_bad >= 10 or v_all >= 60 then raise exception 'too_many'; end if;

  -- during a happy hour every dish already has a discount, and promo codes never apply to discounted dishes
  if happy_hour_pct(p_store) > 0 then return jsonb_build_object('ok', false, 'error', 'promo_offer'); end if;

  begin
    v_res := to_jsonb(check_promo_base(p_code, p_store, p_items));
  exception when others then
    v_err := sqlerrm;
  end;

  if v_err is not null then
    if v_err ~* 'too_many' then raise exception 'too_many'; end if;
    v_key := substring(v_err from '(promo_[a-z_]+)');
    if v_key is null then raise exception '%', v_err; end if;            -- not about the code (closed, unavailable ...): unchanged
    v_res := jsonb_build_object('ok', false, 'error', v_key);            -- answered, so the attempt below is kept
  end if;

  v_key := coalesce(v_res->>'error', '');
  insert into promo_guess(user_id, bad)
  values (v_uid, coalesce((v_res->>'ok')::boolean, false) = false and (v_key = '' or v_key ~* 'promo_invalid'));
  delete from promo_guess where user_id = v_uid and at < now() - interval '1 day';
  return v_res;
end $$;
revoke all on function check_promo(text, uuid, jsonb) from public, anon;
grant execute on function check_promo(text, uuid, jsonb) to authenticated;
