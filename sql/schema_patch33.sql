-- =============================================================================================
-- PATCH 33 — batch 1-b (owner decisions of 10 Oct, 18:43). Run after patch 32. Safe to run again.
--  * Points: 1000 points = 1 TJS (owner, 10 Oct 19:21) and an optional earn rate per restaurant (admin).
--  * Free delivery above a restaurant's own threshold (stores.free_delivery_min, 0 = off). The waived fee
--    is paid by the restaurant (orders.fee_waived); the courier is paid as before.
--  * Scheduled orders: the customer picks a time 45 min .. 3 days ahead (orders.scheduled_for); the
--    restaurant may start preparing it at most 60 minutes before.
--  * Office / group orders: a host opens a group order for one restaurant and shares the link; colleagues
--    add their dishes (with their name); the host places ONE order and pays ONE bill, ONE delivery.
--    Group tables are reachable only through the functions below (no direct table access).
-- =============================================================================================

-- ---------- free delivery threshold ----------
alter table stores add column if not exists free_delivery_min numeric not null default 0 check (free_delivery_min between 0 and 100000);
alter table orders add column if not exists fee_waived numeric not null default 0 check (fee_waived >= 0);

create or replace function set_my_free_delivery(p_store uuid, p_min numeric) returns void
language plpgsql security definer set search_path = public as $$
begin
  if not exists (select 1 from stores where id = p_store and owner_id = auth.uid()) then raise exception 'not_allowed'; end if;
  if p_min is null or p_min not between 0 and 100000 then raise exception 'bad_value'; end if;
  update stores set free_delivery_min = round(p_min, 2) where id = p_store;
end $$;
revoke all on function set_my_free_delivery(uuid, numeric) from public, anon;
grant execute on function set_my_free_delivery(uuid, numeric) to authenticated;

create or replace function set_store_free_delivery(p_store uuid, p_min numeric) returns void
language plpgsql security definer set search_path = public as $$
begin
  if not (is_admin() or has_perm('stores')) then raise exception 'not_allowed'; end if;
  if p_min is null or p_min not between 0 and 100000 then raise exception 'bad_value'; end if;
  update stores set free_delivery_min = round(p_min, 2) where id = p_store;
  if not found then raise exception 'not_found'; end if;
end $$;
revoke all on function set_store_free_delivery(uuid, numeric) from public, anon;
grant execute on function set_store_free_delivery(uuid, numeric) to authenticated;

-- ---------- scheduled orders ----------
alter table orders add column if not exists scheduled_for timestamptz;

-- ---------- group (office) orders ----------
create table if not exists group_orders (
  id uuid primary key default gen_random_uuid(),
  store_id uuid not null references stores(id) on delete cascade,
  host_id uuid not null references profiles(id) on delete cascade,
  status text not null default 'open' check (status in ('open', 'closed', 'placed', 'cancelled')),
  order_id bigint references orders(id) on delete set null,
  created_at timestamptz not null default now(),
  expires_at timestamptz not null default now() + interval '3 hours',
  closed_at timestamptz
);
create index if not exists group_orders_host_idx on group_orders (host_id, created_at desc);
create table if not exists group_items (
  id bigint generated always as identity primary key,
  group_id uuid not null references group_orders(id) on delete cascade,
  user_id uuid not null references profiles(id) on delete cascade,
  user_name text not null,
  item_id uuid not null references menu_items(id) on delete cascade,
  qty int not null check (qty between 1 and 20),
  options jsonb not null default '[]'::jsonb,
  note text check (note is null or char_length(note) <= 120),
  created_at timestamptz not null default now()
);
create index if not exists group_items_group_idx on group_items (group_id);
alter table group_orders enable row level security;
alter table group_items enable row level security;
revoke all on group_orders, group_items from anon, authenticated;
alter table orders add column if not exists group_id uuid references group_orders(id) on delete set null;

create or replace function group_json(p_id uuid) returns jsonb
language sql stable security definer set search_path = public as $$
  select jsonb_build_object('id', g.id, 'store_id', g.store_id, 'host_id', g.host_id, 'is_host', g.host_id = auth.uid(),
    'host_name', (select name from profiles where id = g.host_id), 'status', g.status, 'expires_at', g.expires_at, 'order_id', g.order_id,
    'items', coalesce((select jsonb_agg(jsonb_build_object('id', i.id, 'user_name', i.user_name, 'mine', i.user_id = auth.uid(),
        'item_id', i.item_id, 'qty', i.qty, 'options', i.options, 'note', i.note) order by i.created_at) from group_items i where i.group_id = g.id), '[]'::jsonb))
  from group_orders g where g.id = p_id
$$;
revoke all on function group_json(uuid) from public, anon, authenticated;

create or replace function group_create(p_store uuid) returns jsonb
language plpgsql security definer set search_path = public as $$
declare v_id uuid;
begin
  if auth.uid() is null then raise exception 'auth'; end if;
  if not exists (select 1 from stores where id = p_store and is_active) then raise exception 'store_unavailable'; end if;
  if (select count(*) from group_orders where host_id = auth.uid() and created_at > now() - interval '1 day') >= 10 then raise exception 'too_many'; end if;
  update group_orders set status = 'cancelled' where host_id = auth.uid() and status in ('open', 'closed');   -- one open group per host
  insert into group_orders(store_id, host_id) values (p_store, auth.uid()) returning id into v_id;
  return group_json(v_id);
end $$;

-- anyone signed in who has the link (an unguessable id) can see the group and join it
create or replace function group_get(p_id uuid) returns jsonb
language plpgsql security definer set search_path = public as $$
begin
  if auth.uid() is null then raise exception 'auth'; end if;
  update group_orders set status = 'cancelled' where id = p_id and status = 'open' and expires_at < now();
  return group_json(p_id);
end $$;

create or replace function group_add(p_id uuid, p_item uuid, p_qty int, p_options jsonb default '[]'::jsonb, p_note text default null) returns jsonb
language plpgsql security definer set search_path = public as $$
declare g group_orders; v_name text;
begin
  if auth.uid() is null then raise exception 'auth'; end if;
  select * into g from group_orders where id = p_id for update;
  if not found or g.status <> 'open' or g.expires_at < now() then raise exception 'group_closed'; end if;
  if p_qty is null or p_qty not between 1 and 20 then raise exception 'bad_value'; end if;
  if not exists (select 1 from menu_items where id = p_item and store_id = g.store_id and available and approved) then raise exception 'unavailable'; end if;
  perform price_line(p_item, coalesce(p_options, '[]'::jsonb));          -- the same option rules as a normal order
  if (select count(*) from group_items where group_id = p_id) >= 60 or (select count(*) from group_items where group_id = p_id and user_id = auth.uid()) >= 20 then
    raise exception 'too_many';
  end if;
  select coalesce(nullif(btrim(name), ''), 'Гость') into v_name from profiles where id = auth.uid();
  insert into group_items(group_id, user_id, user_name, item_id, qty, options, note)
  values (p_id, auth.uid(), left(v_name, 40), p_item, p_qty, coalesce(p_options, '[]'::jsonb), nullif(left(btrim(coalesce(p_note, '')), 120), ''));
  return group_json(p_id);
end $$;

create or replace function group_remove(p_line bigint) returns jsonb
language plpgsql security definer set search_path = public as $$
declare v_g uuid;
begin
  select i.group_id into v_g from group_items i join group_orders g on g.id = i.group_id
   where i.id = p_line and g.status = 'open' and (i.user_id = auth.uid() or g.host_id = auth.uid());
  if v_g is null then raise exception 'not_allowed'; end if;
  delete from group_items where id = p_line;
  return group_json(v_g);
end $$;

-- the host stops new additions (to check out), can re-open, or cancel
create or replace function group_set(p_id uuid, p_status text) returns jsonb
language plpgsql security definer set search_path = public as $$
begin
  if p_status not in ('open', 'closed', 'cancelled') then raise exception 'bad_value'; end if;
  update group_orders set status = p_status, closed_at = case when p_status = 'closed' then now() else closed_at end,
         expires_at = case when p_status = 'open' then greatest(expires_at, now() + interval '1 hour') else expires_at end
   where id = p_id and host_id = auth.uid() and status in ('open', 'closed');
  if not found then raise exception 'not_allowed'; end if;
  return group_json(p_id);
end $$;
revoke all on function group_create(uuid), group_get(uuid), group_add(uuid, uuid, int, jsonb, text), group_remove(bigint), group_set(uuid, text) from public, anon;
grant execute on function group_create(uuid), group_get(uuid), group_add(uuid, uuid, int, jsonb, text), group_remove(bigint), group_set(uuid, text) to authenticated;

-- ---------- order status: a scheduled order is prepared at most 60 minutes before its time ----------
CREATE OR REPLACE FUNCTION public.set_order_status(p_id bigint, p_to order_status)
 RETURNS void
 LANGUAGE plpgsql
 SECURITY DEFINER
 SET search_path TO 'public'
AS $function$
declare o orders; ok boolean := false;
begin
  select * into o from orders where id = p_id for update;
  if not found then raise exception 'not_found'; end if;
  if is_admin() then ok := true;
  elsif has_perm('orders') and p_to in ('cancelled','rejected') then ok := o.status in ('pending','preparing','ready','pickedup');
  elsif o.customer_id = auth.uid() then ok := (o.status = 'pending' and p_to = 'cancelled');
  elsif owns_store(o.store_id) then
    ok := (o.status = 'pending' and p_to in ('preparing','rejected')) or (o.status = 'preparing' and p_to = 'ready');
    -- a scheduled order is prepared at most 60 minutes before its time (v51)
    if ok and p_to = 'preparing' and o.scheduled_for is not null and now() < o.scheduled_for - interval '60 minutes' then raise exception 'too_early'; end if;
  elsif o.driver_id = auth.uid() then
    ok := (o.status = 'ready' and p_to = 'pickedup');
  end if;
  if not ok then raise exception 'bad_transition'; end if;
  update orders set status = p_to,
    done_at = case when p_to in ('delivered','rejected','cancelled') then now() else null end where id = p_id;
end $function$
;

-- ---------- place_order: free delivery threshold, scheduled time, group order ----------
drop function if exists place_order(uuid, jsonb, numeric, text, text, double precision, double precision, text, text, numeric, numeric, integer);
create or replace function place_order(p_store uuid, p_items jsonb, p_tip numeric default 0, p_payment text default 'cash',
  p_address text default '', p_lat float8 default null, p_lng float8 default null, p_promo text default null, p_key text default null, p_fee numeric default null, p_wallet numeric default null, p_points integer default null, p_extra jsonb default null)
returns bigint language plpgsql security definer set search_path = public as $$
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
end $$;
revoke all on function place_order(uuid, jsonb, numeric, text, text, double precision, double precision, text, text, numeric, numeric, integer, jsonb) from public, anon;
grant execute on function place_order(uuid, jsonb, numeric, text, text, double precision, double precision, text, text, numeric, numeric, integer, jsonb) to authenticated;

-- ---------- the app must be able to READ the restaurant rules ----------
-- Patch 17 made stores readable column by column (commission stays private). Columns added later are NOT readable
-- until granted: brand_id/branch_name (patch 27), points_min_order/cashback_pct (patch 32), free_delivery_min (this patch).
-- Only the columns that exist are granted, so this also works when patch 27 was not run yet.
do $$
declare c text;
begin
  foreach c in array array['brand_id', 'branch_name', 'points_min_order', 'cashback_pct', 'free_delivery_min'] loop
    if exists (select 1 from information_schema.columns where table_schema = 'public' and table_name = 'stores' and column_name = c) then
      execute format('grant select (%I) on stores to authenticated', c);
    end if;
  end loop;
end $$;

-- ---------- owner decision 10 Oct 19:21: earn 10 points per 1 TJS, 1000 points = 1 TJS off (= 1%) ----------
-- Only the untouched v50 default (100) is changed; a value the admin chose himself stays.
update app_settings set value = 1000 where key = 'loyalty_points_per_tjs' and value = 100;
create or replace function loyalty_setting(p_key text) returns numeric
language sql stable security definer set search_path = public as $$
  select coalesce((select value from app_settings where key = p_key),
    case p_key when 'loyalty_earn_per_tjs' then 10 when 'loyalty_points_per_tjs' then 1000 when 'loyalty_min_redeem' then 1000
               when 'loyalty_expiry_days' then 90 when 'loyalty_voucher_points' then 1000 when 'loyalty_min_order' then 30
               when 'loyalty_rate_reward' then 10 else 0 end)
$$;
revoke all on function loyalty_setting(text) from public, anon, authenticated;

-- per restaurant (admin): how many points per 1 TJS this restaurant gives (empty = the general rule). The value of a
-- point when paying stays ONE for the whole app, so a balance means the same everywhere.
alter table stores add column if not exists earn_per_tjs numeric check (earn_per_tjs is null or (earn_per_tjs between 0 and 1000 and earn_per_tjs = trunc(earn_per_tjs)));
create or replace function set_store_earn(p_store uuid, p_earn numeric) returns void
language plpgsql security definer set search_path = public as $$
begin
  if not (is_admin() or has_perm('stores')) then raise exception 'not_allowed'; end if;
  if p_earn is not null and (p_earn not between 0 and 1000 or p_earn <> trunc(p_earn)) then raise exception 'bad_value'; end if;
  update stores set earn_per_tjs = p_earn where id = p_store;
  if not found then raise exception 'not_found'; end if;
end $$;
revoke all on function set_store_earn(uuid, numeric) from public, anon;
grant execute on function set_store_earn(uuid, numeric) to authenticated;
grant select (earn_per_tjs) on stores to authenticated;

-- earning trigger: the restaurant's own rate when the admin set one (same rules as patch 32 otherwise)
create or replace function trg_loyalty() returns trigger language plpgsql security definer set search_path = public as $$
declare v_paid numeric; v_pts int; v_cb numeric;
begin
  if new.status = 'delivered' and old.status <> 'delivered' and new.loyalty_done_at is null then
    v_paid := greatest(0, coalesce(new.subtotal, 0) - coalesce(new.discount, 0) - coalesce(new.promo_discount, 0) - coalesce(new.points_value, 0));
    v_pts := ceil(v_paid * coalesce((select earn_per_tjs from stores where id = new.store_id), loyalty_setting('loyalty_earn_per_tjs')) - 0.000001)::int;   -- fractions in favour of the customer
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
