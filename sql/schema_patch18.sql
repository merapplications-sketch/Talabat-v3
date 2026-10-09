-- Patch 18: phones (private, with visibility rules), delivery fee by distance with a fixed quote, rating averages
-- Run once in Supabase SQL Editor BEFORE uploading the files (needs patches 1-17). Safe to re-run.
--
-- NEW / CHANGED ROW LEVEL SECURITY (what each role can reach after this patch)
--   order_customer_phone / order_driver_phone : RLS ON and NO policy at all -> nobody can read or write them directly.
--       They are reachable only through the SECURITY DEFINER functions below, which decide who may see which number:
--         customer : the courier's number, only while the order is active (preparing / ready / pickedup)
--         restaurant : the courier's number, only while the order is active and a courier is assigned (never the customer's)
--         courier : the customer's number, only for his own active order
--         admin : both numbers, always
--   app_settings : every signed-in user may READ the delivery tariffs (customers see the prices anyway); nobody can write
--       directly, only the admin through set_setting() (validated ranges, audited).
--   orders.customer_phone : emptied. The old column stays but is no longer filled (a leak path through the orders row is closed).
--   stores : two new public columns (app_rating, app_rating_count) are added to the column grant of patch 17.

------------------------------------------------------------------------------------------------
-- 1) TAJIKISTAN PHONE NUMBERS: one format (+992 and 9 digits)
------------------------------------------------------------------------------------------------
create or replace function norm_phone(p text) returns text language sql immutable as $$
  select case
    when d ~ '^992[0-9]{9}$' then '+' || d
    when d ~ '^[0-9]{9}$' then '+992' || d
    when d ~ '^0[0-9]{9}$' then '+992' || substr(d, 2)
    else null end
  from (select regexp_replace(coalesce(p, ''), '[^0-9]', '', 'g') as d) x
$$;
revoke execute on function norm_phone(text) from public, anon;
grant execute on function norm_phone(text) to authenticated;

create or replace function set_my_phone(p_phone text) returns void
language plpgsql security definer set search_path = public as $$
declare v_p text := norm_phone(p_phone);
begin
  if auth.uid() is null then raise exception 'auth'; end if;
  if v_p is null then raise exception 'bad_phone'; end if;
  update profiles set phone = v_p where id = auth.uid();
end $$;

-- the phone typed at sign-up (stored in the sign-up metadata) is validated here, never trusted as it is
create or replace function handle_new_user() returns trigger language plpgsql security definer set search_path = public as $$
begin
  insert into profiles(id, name, phone)
  values (new.id, left(btrim(coalesce(new.raw_user_meta_data->>'name', '')), 80),
          coalesce(norm_phone(new.raw_user_meta_data->>'phone'), norm_phone(new.phone)));
  return new;
end $$;

-- a restaurant phone is normalized and validated when it changes (old values never block an unrelated edit)
create or replace function trg_store_phone() returns trigger language plpgsql set search_path = public as $$
declare v_p text;
begin
  if new.phone is null or btrim(new.phone) = '' then new.phone := null; return new; end if;
  if tg_op = 'INSERT' or new.phone is distinct from old.phone then
    v_p := norm_phone(new.phone);
    if v_p is null then raise exception 'bad_phone'; end if;
    new.phone := v_p;
  end if;
  return new;
end $$;
drop trigger if exists trg_store_phone on stores;
create trigger trg_store_phone before insert or update on stores for each row execute function trg_store_phone();

-- bring existing numbers to the same format
do $$ begin
  perform set_config('app.bypass', '1', true);
  update profiles set phone = norm_phone(phone) where phone is not null and norm_phone(phone) is not null and phone <> norm_phone(phone);
  update stores set phone = norm_phone(phone) where phone is not null and norm_phone(phone) is not null and phone <> norm_phone(phone);
end $$;

------------------------------------------------------------------------------------------------
-- 2) PRIVATE CONTACT TABLES (no policy = no direct access) + the functions that apply the visibility rules
------------------------------------------------------------------------------------------------
create table if not exists order_customer_phone (order_id bigint primary key references orders(id) on delete cascade, phone text not null);
create table if not exists order_driver_phone (order_id bigint primary key references orders(id) on delete cascade, phone text not null);
alter table order_customer_phone enable row level security;
alter table order_driver_phone enable row level security;
revoke all on order_customer_phone from anon, authenticated;
revoke all on order_driver_phone from anon, authenticated;

-- stop the old trigger that copied the customer phone into the orders row (that row is readable by the restaurant)
drop trigger if exists trg_fill_order_phone on orders;
drop function if exists fill_order_phone();

-- move the existing numbers into the private tables and empty the old column
do $$ begin
  perform set_config('app.bypass', '1', true);
  insert into order_customer_phone(order_id, phone)
    select id, customer_phone from orders where coalesce(btrim(customer_phone), '') <> '' on conflict do nothing;
  insert into order_driver_phone(order_id, phone)
    select o.id, p.phone from orders o join profiles p on p.id = o.driver_id where coalesce(btrim(p.phone), '') <> '' on conflict do nothing;
  update orders set customer_phone = null where customer_phone is not null;
end $$;

create or replace function order_contacts(p_order bigint) returns jsonb
language plpgsql stable security definer set search_path = public as $$
declare v_o orders; v_cp text; v_dp text; v_active boolean;
begin
  if auth.uid() is null then raise exception 'auth'; end if;
  select * into v_o from orders where id = p_order;
  if not found then return '{}'::jsonb; end if;
  v_active := v_o.status in ('preparing', 'ready', 'pickedup');
  select phone into v_cp from order_customer_phone where order_id = p_order;
  select phone into v_dp from order_driver_phone where order_id = p_order;
  if is_admin() then return jsonb_build_object('customer_phone', v_cp, 'driver_phone', v_dp); end if;
  return jsonb_build_object(
    'customer_phone', case when v_active and v_o.driver_id = auth.uid() then v_cp end,
    'driver_phone', case when v_active and v_o.driver_id is not null and (v_o.customer_id = auth.uid() or owns_store(v_o.store_id)) then v_dp end);
end $$;
revoke all on function order_contacts(bigint) from public, anon;
grant execute on function order_contacts(bigint) to authenticated;

create or replace function active_contacts() returns table(order_id bigint, customer_phone text, driver_phone text)
language sql stable security definer set search_path = public as $$
  select o.id,
         case when o.driver_id = auth.uid() then cp.phone end,
         case when o.driver_id is not null and (o.customer_id = auth.uid() or owns_store(o.store_id)) then dp.phone end
    from orders o
    left join order_customer_phone cp on cp.order_id = o.id
    left join order_driver_phone dp on dp.order_id = o.id
   where o.status in ('preparing', 'ready', 'pickedup')
     and (o.driver_id = auth.uid() or o.customer_id = auth.uid() or owns_store(o.store_id))
$$;
revoke all on function active_contacts() from public, anon;
grant execute on function active_contacts() to authenticated;

create or replace function contacts_for(p_ids bigint[]) returns table(order_id bigint, customer_phone text, driver_phone text)
language sql stable security definer set search_path = public as $$
  select t.i, cp.phone, dp.phone
    from unnest(case when cardinality(p_ids) > 200 then p_ids[1:200] else p_ids end) as t(i)
    left join order_customer_phone cp on cp.order_id = t.i
    left join order_driver_phone dp on dp.order_id = t.i
   where is_admin()
$$;
revoke all on function contacts_for(bigint[]) from public, anon;
grant execute on function contacts_for(bigint[]) to authenticated;

-- the courier's number is copied to the order when he accepts (or when the admin assigns him); no number = cannot accept
create or replace function driver_accept(p_id bigint) returns boolean
language plpgsql security definer set search_path = public as $$
declare v_id bigint; v_name text; v_blocked boolean; v_phone text;
begin
  select name, accept_blocked, phone into v_name, v_blocked, v_phone from profiles
   where id = auth.uid() and role = 'driver' and driver_status = 'approved';
  if not found then raise exception 'not_approved'; end if;
  if v_blocked then raise exception 'blocked'; end if;
  if norm_phone(v_phone) is null then raise exception 'phone_required'; end if;
  if exists (select 1 from orders x where x.driver_id = auth.uid() and x.status in ('preparing', 'ready', 'pickedup')) then
    raise exception 'busy';
  end if;
  if not exists (select 1 from order_offers where order_id = p_id and driver_id = auth.uid() and state = 'pending' and expires_at > now()) then
    raise exception 'no_offer';
  end if;
  update orders set driver_id = auth.uid(), driver_name = v_name
   where id = p_id and driver_id is null and status in ('preparing', 'ready') returning id into v_id;
  if v_id is not null then
    update order_offers set state = case when driver_id = auth.uid() then 'accepted' else 'cancelled' end
     where order_id = p_id and state = 'pending';
    insert into order_driver_phone(order_id, phone) values (p_id, norm_phone(v_phone))
      on conflict (order_id) do update set phone = excluded.phone;
  end if;
  return v_id is not null;
end $$;
revoke all on function driver_accept(bigint) from public, anon;
grant execute on function driver_accept(bigint) to authenticated;

create or replace function admin_assign_driver(p_order bigint, p_driver uuid) returns void
language plpgsql security definer set search_path = public as $$
declare v_name text; v_phone text;
begin
  if not is_admin() then raise exception 'not_allowed'; end if;
  select name, phone into v_name, v_phone from profiles where id = p_driver and role = 'driver' and driver_status = 'approved';
  if not found then raise exception 'not_approved'; end if;
  if norm_phone(v_phone) is null then raise exception 'phone_required'; end if;
  update orders set driver_id = p_driver, driver_name = v_name
   where id = p_order and driver_id is null and status in ('preparing', 'ready');
  if not found then raise exception 'bad_transition'; end if;
  update order_offers set state = case when driver_id = p_driver then 'accepted' else 'cancelled' end
   where order_id = p_order and state = 'pending';
  insert into order_driver_phone(order_id, phone) values (p_order, norm_phone(v_phone))
    on conflict (order_id) do update set phone = excluded.phone;
end $$;
revoke all on function admin_assign_driver(bigint, uuid) from public, anon;
grant execute on function admin_assign_driver(bigint, uuid) to authenticated;

------------------------------------------------------------------------------------------------
-- 3) DELIVERY TARIFFS (one set for all restaurants, edited by the admin)
--    first 3 km are covered by the restaurant's base fee, then every started 0.5 km costs the step price.
--    The distance is the straight line x 1.3 (an estimate of the road); more than 15 km is refused.
------------------------------------------------------------------------------------------------
create table if not exists app_settings (
  key text primary key check (key in ('delivery_free_km', 'delivery_step_km', 'delivery_step_price', 'delivery_max_km', 'delivery_road_factor')),
  value numeric not null,
  updated_at timestamptz not null default now(),
  updated_by uuid
);
insert into app_settings(key, value) values
  ('delivery_free_km', 3), ('delivery_step_km', 0.5), ('delivery_step_price', 2), ('delivery_max_km', 15), ('delivery_road_factor', 1.3)
on conflict (key) do nothing;
alter table app_settings enable row level security;
drop policy if exists settings_read on app_settings;
create policy settings_read on app_settings for select using (auth.uid() is not null);   -- no write policy: only set_setting()

create or replace function set_setting(p_key text, p_value numeric) returns void
language plpgsql security definer set search_path = public as $$
begin
  if not is_admin() then raise exception 'not_allowed'; end if;
  if p_value is null
     or (p_key = 'delivery_free_km' and p_value not between 0 and 50)
     or (p_key = 'delivery_step_km' and p_value not between 0.1 and 5)
     or (p_key = 'delivery_step_price' and p_value not between 0 and 1000)
     or (p_key = 'delivery_max_km' and p_value not between 1 and 100)
     or (p_key = 'delivery_road_factor' and p_value not between 1 and 3) then
    raise exception 'bad_value';
  end if;
  update app_settings set value = p_value, updated_at = now(), updated_by = auth.uid() where key = p_key;
  if not found then raise exception 'bad_value'; end if;
end $$;
revoke all on function set_setting(text, numeric) from public, anon;
grant execute on function set_setting(text, numeric) to authenticated;

drop trigger if exists trg_audit_settings on app_settings;
create trigger trg_audit_settings after update on app_settings for each row execute function audit_changes('key', 'value');

alter table orders add column if not exists delivery_base numeric;
alter table orders add column if not exists delivery_extra numeric not null default 0;
alter table orders add column if not exists delivery_km numeric;

-- ONE calculation used by both the preview (delivery_quote) and the order (place_order): they cannot disagree
create or replace function delivery_calc(p_store uuid, p_lat float8, p_lng float8, p_uid uuid) returns jsonb
language plpgsql stable security definer set search_path = public as $$
declare v_s stores; v_free numeric; v_step numeric; v_price numeric; v_max numeric; v_fac numeric;
        v_straight float8; v_road numeric; v_steps int := 0; v_extra numeric := 0; v_base numeric; v_full numeric; v_fee numeric; v_first boolean := false;
begin
  if p_lat is null or p_lng is null or p_lat not between -90 and 90 or p_lng not between -180 and 180 then raise exception 'bad_value'; end if;
  select * into v_s from stores where id = p_store and is_active;
  if not found then raise exception 'store_unavailable'; end if;
  select coalesce((select value from app_settings where key = 'delivery_free_km'), 3) into v_free;
  select coalesce((select value from app_settings where key = 'delivery_step_km'), 0.5) into v_step;
  select coalesce((select value from app_settings where key = 'delivery_step_price'), 2) into v_price;
  select coalesce((select value from app_settings where key = 'delivery_max_km'), 15) into v_max;
  select coalesce((select value from app_settings where key = 'delivery_road_factor'), 1.3) into v_fac;
  v_base := case v_s.fee_type when 'free' then 0 else v_s.fee_base end;
  if v_s.lat is not null and v_s.lng is not null then
    v_straight := dist_km(v_s.lat, v_s.lng, p_lat, p_lng);
    v_road := round((v_straight * v_fac)::numeric, 2);
    if v_road > v_max then raise exception 'too_far'; end if;
    if v_s.fee_type = 'distance' then
      v_steps := ceil(round(greatest(0, v_road - v_free) / v_step, 6));
      v_extra := v_steps * v_price;
    end if;
  end if;
  v_full := v_base + v_extra;
  v_fee := v_full;
  if v_s.free_first_delivery and v_s.fee_type <> 'free' and p_uid is not null
     and not exists (select 1 from orders where customer_id = p_uid and store_id = p_store and status not in ('rejected', 'cancelled')) then
    v_first := true; v_fee := 0;
  end if;
  return jsonb_build_object('fee', v_fee, 'fee_full', v_full, 'base', v_base, 'extra', v_extra, 'steps', v_steps,
    'km', v_road, 'km_straight', round(v_straight::numeric, 2), 'free_km', v_free, 'step_km', v_step, 'step_price', v_price,
    'max_km', v_max, 'first_free', v_first, 'fee_type', v_s.fee_type);
end $$;
revoke all on function delivery_calc(uuid, float8, float8, uuid) from public, anon, authenticated;

create or replace function delivery_quote(p_store uuid, p_lat float8, p_lng float8) returns jsonb
language plpgsql stable security definer set search_path = public as $$
begin
  if auth.uid() is null then raise exception 'auth'; end if;
  return delivery_calc(p_store, p_lat, p_lng, auth.uid());
end $$;
revoke all on function delivery_quote(uuid, float8, float8) from public, anon;
grant execute on function delivery_quote(uuid, float8, float8) to authenticated;

-- place_order gets one more optional argument (p_fee = the delivery fee the customer saw): if it differs, the order is refused
drop function if exists place_order(uuid, jsonb, numeric, text, text, double precision, double precision, text, text);
create or replace function place_order(p_store uuid, p_items jsonb, p_tip numeric default 0, p_payment text default 'cash',
  p_address text default '', p_lat float8 default null, p_lng float8 default null, p_promo text default null, p_key text default null, p_fee numeric default null)
returns bigint language plpgsql security definer set search_path = public as $$
declare s stores; pr profiles; it record; v_item menu_items; pl jsonb; v_id bigint; v_sub numeric; v_fee numeric; v_pay numeric; v_disc numeric; v_base numeric; v_gate numeric;
        v_promo numeric := 0; v_tip numeric; v_km float8; v_code text := null; v_dq jsonb; v_cphone text;
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
  return v_id;
end $$;
revoke all on function place_order(uuid, jsonb, numeric, text, text, double precision, double precision, text, text, numeric) from public, anon;
grant execute on function place_order(uuid, jsonb, numeric, text, text, double precision, double precision, text, text, numeric) to authenticated;

------------------------------------------------------------------------------------------------
-- 4) RATING AVERAGES from customers (shown on the restaurant, and to the courier for himself)
------------------------------------------------------------------------------------------------
alter table stores add column if not exists app_rating numeric(2,1);
alter table stores add column if not exists app_rating_count int not null default 0;
grant select (app_rating, app_rating_count) on stores to authenticated;

create or replace function trg_rating_aggregate() returns trigger
language plpgsql security definer set search_path = public as $$
begin
  perform set_config('app.bypass', '1', true);
  update stores set
    app_rating = (select round(avg(r.store_stars)::numeric, 1) from ratings r where r.store_id = new.store_id and r.store_stars is not null),
    app_rating_count = (select count(r.store_stars) from ratings r where r.store_id = new.store_id)
  where id = new.store_id;
  return new;
end $$;
drop trigger if exists trg_rating_aggregate on ratings;
create trigger trg_rating_aggregate after insert on ratings for each row execute function trg_rating_aggregate();

do $$ begin
  perform set_config('app.bypass', '1', true);
  update stores s set
    app_rating = (select round(avg(r.store_stars)::numeric, 1) from ratings r where r.store_id = s.id and r.store_stars is not null),
    app_rating_count = (select count(r.store_stars) from ratings r where r.store_id = s.id);
end $$;

create or replace function my_rating() returns jsonb
language sql stable security definer set search_path = public as $$
  select jsonb_build_object('avg', round(avg(driver_stars)::numeric, 1), 'count', count(driver_stars))
    from ratings where driver_id = auth.uid()
$$;
revoke all on function my_rating() from public, anon;
grant execute on function my_rating() to authenticated;
