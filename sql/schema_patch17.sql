-- Patch 17: SECURITY HARDENING + SCALABILITY
--   * hides every restaurant's commission / discount cap / owner from other users (column-level security)
--   * database indexes for every hot query (before: none besides the primary keys)
--   * image storage (Supabase Storage) so images are no longer downloaded inside every data refresh
--   * audit log of sensitive changes, client error log, rate limits (chat, favorites, orders per hour)
--   * safe retry for orders (idempotency key)
--   * address form with separate fields (house, entrance, floor, apartment, note)
-- Run once in Supabase SQL Editor BEFORE uploading the files (needs patches 1-16). Safe to re-run.
-- A rollback for the stores column lock is at the very bottom (commented).

------------------------------------------------------------------------------------------------
-- 1) COLUMN-LEVEL SECURITY ON stores: commission_pct, max_discount_pct and owner_id are admin/owner-only
--    The app reads the public columns directly and the private ones through store_private().
------------------------------------------------------------------------------------------------
revoke select on stores from authenticated;
grant select (id, name, category, description, logo_url, cover_url, address, lat, lng,
              fee_type, fee_base, fee_per_km, fee_free_km, discount_pct, is_open, is_active, is_featured,
              created_at, phone, free_first_delivery, google_place_id, rating, rating_count, rating_updated_at)
  on stores to authenticated;

create or replace function store_private() returns table(id uuid, owner_id uuid, commission_pct numeric, max_discount_pct numeric)
language sql stable security definer set search_path = public as $$
  select s.id, s.owner_id, s.commission_pct, s.max_discount_pct
    from stores s where is_admin() or s.owner_id = auth.uid()
$$;
revoke all on function store_private() from public, anon;
grant execute on function store_private() to authenticated;

------------------------------------------------------------------------------------------------
-- 2) INDEXES for the hot queries (foreign keys are NOT indexed automatically in PostgreSQL)
------------------------------------------------------------------------------------------------
create index if not exists orders_customer_idx on orders (customer_id, created_at desc);
create index if not exists orders_driver_idx on orders (driver_id, created_at desc);
create index if not exists orders_store_idx on orders (store_id, created_at desc);
create index if not exists orders_created_idx on orders (created_at desc);
create index if not exists orders_open_idx on orders (created_at) where driver_id is null and status in ('preparing', 'ready');
create index if not exists orders_active_idx on orders (status) where status in ('pending', 'preparing', 'ready', 'pickedup');
create index if not exists order_items_order_idx on order_items (order_id);
create index if not exists order_chat_order_idx on order_chat (order_id, created_at);
create index if not exists menu_items_store_idx on menu_items (store_id, available);
create index if not exists favorites_user_idx on favorites (user_id);
create index if not exists banners_sort_idx on banners (sort, created_at);
create index if not exists profiles_role_idx on profiles (role, driver_status);
create index if not exists profiles_online_idx on profiles (online, last_seen) where role = 'driver';
create index if not exists stores_owner_idx on stores (owner_id);
create index if not exists promo_attempts_code_idx on promo_attempts (code) where ok;
create index if not exists orders_promo_idx on orders (promo_code) where promo_code is not null;

------------------------------------------------------------------------------------------------
-- 3) INPUT LIMITS on text columns (NOT VALID = new writes only; old rows untouched)
------------------------------------------------------------------------------------------------
do $$ begin
  if not exists (select 1 from pg_constraint where conname = 'stores_text_len') then
    alter table stores add constraint stores_text_len check (
      char_length(name) <= 80 and (description is null or char_length(description) <= 500)
      and (address is null or char_length(address) <= 200) and (phone is null or char_length(phone) <= 20)) not valid;
  end if;
  if not exists (select 1 from pg_constraint where conname = 'banners_text_len') then
    alter table banners add constraint banners_text_len check (char_length(title) <= 80 and (link_value is null or char_length(link_value) <= 80)) not valid;
  end if;
  if not exists (select 1 from pg_constraint where conname = 'menu_items_name_len') then
    alter table menu_items add constraint menu_items_name_len check (char_length(name) <= 80) not valid;
  end if;
end $$;

-- images: only our own storage or an inline data: image may be written (no tracking pixels from other hosts)
create or replace function check_image_url(u text) returns boolean language sql immutable as $$
  select u is null or u = '' or u like 'data:image/%'
         or u like 'https://dzydscryrnahnneydnry.supabase.co/storage/v1/object/public/media/%'
$$;
create or replace function trg_check_images() returns trigger language plpgsql set search_path = public as $$
declare v_n jsonb := to_jsonb(new); v_o jsonb := case when tg_op = 'UPDATE' then to_jsonb(old) else '{}'::jsonb end; v_k text;
begin
  foreach v_k in array array['image_url', 'cover_url', 'logo_url'] loop
    if v_n ? v_k and (v_n->>v_k) is distinct from (v_o->>v_k) and not check_image_url(v_n->>v_k) then
      raise exception 'bad_value';
    end if;
  end loop;
  return new;
end $$;
drop trigger if exists trg_images_menu on menu_items;
create trigger trg_images_menu before insert or update on menu_items for each row execute function trg_check_images();
drop trigger if exists trg_images_stores on stores;
create trigger trg_images_stores before insert or update on stores for each row execute function trg_check_images();
drop trigger if exists trg_images_banners on banners;
create trigger trg_images_banners before insert or update on banners for each row execute function trg_check_images();

------------------------------------------------------------------------------------------------
-- 4) IMAGE STORAGE: public-read bucket "media"; only restaurant owners and the admin may upload, into their own folder
------------------------------------------------------------------------------------------------
insert into storage.buckets (id, name, public, file_size_limit, allowed_mime_types)
values ('media', 'media', true, 1048576, array['image/jpeg', 'image/png', 'image/webp'])
on conflict (id) do update set public = true, file_size_limit = 1048576, allowed_mime_types = array['image/jpeg', 'image/png', 'image/webp'];

drop policy if exists media_read on storage.objects;
drop policy if exists media_insert on storage.objects;
drop policy if exists media_update on storage.objects;
drop policy if exists media_delete on storage.objects;
create policy media_read on storage.objects for select using (bucket_id = 'media');
create policy media_insert on storage.objects for insert to authenticated
  with check (bucket_id = 'media' and (storage.foldername(name))[1] = auth.uid()::text
              and exists (select 1 from public.profiles p where p.id = auth.uid() and p.role in ('merchant', 'admin')));
create policy media_update on storage.objects for update to authenticated
  using (bucket_id = 'media' and (storage.foldername(name))[1] = auth.uid()::text);
create policy media_delete on storage.objects for delete to authenticated
  using (bucket_id = 'media' and ((storage.foldername(name))[1] = auth.uid()::text or exists (select 1 from public.profiles p where p.id = auth.uid() and p.role = 'admin')));

------------------------------------------------------------------------------------------------
-- 5) AUDIT LOG (admin-readable, nobody can write except the triggers)
------------------------------------------------------------------------------------------------
create table if not exists audit_log (
  id bigint generated always as identity primary key,
  at timestamptz not null default now(),
  user_id uuid,
  action text not null,
  table_name text not null,
  row_id text,
  details jsonb not null default '{}'::jsonb
);
create index if not exists audit_log_at_idx on audit_log (at desc);
alter table audit_log enable row level security;
drop policy if exists audit_read on audit_log;
create policy audit_read on audit_log for select using (is_admin());

create or replace function audit_changes() returns trigger language plpgsql security definer set search_path = public as $$
declare v_n jsonb; v_o jsonb; v_d jsonb := '{}'::jsonb; v_k text; v_id text;
begin
  if tg_op = 'INSERT' then v_n := to_jsonb(new); v_id := v_n->>coalesce(tg_argv[0], 'id');
    insert into audit_log(user_id, action, table_name, row_id, details) values (auth.uid(), 'INSERT', tg_table_name, v_id, '{}'::jsonb);
    return new;
  elsif tg_op = 'DELETE' then v_o := to_jsonb(old); v_id := v_o->>coalesce(tg_argv[0], 'id');
    insert into audit_log(user_id, action, table_name, row_id, details) values (auth.uid(), 'DELETE', tg_table_name, v_id, '{}'::jsonb);
    return old;
  end if;
  v_n := to_jsonb(new); v_o := to_jsonb(old); v_id := v_n->>coalesce(tg_argv[0], 'id');
  foreach v_k in array tg_argv[1:] loop
    if (v_n->v_k) is distinct from (v_o->v_k) then v_d := v_d || jsonb_build_object(v_k, jsonb_build_object('from', v_o->v_k, 'to', v_n->v_k)); end if;
  end loop;
  if v_d <> '{}'::jsonb then
    insert into audit_log(user_id, action, table_name, row_id, details) values (auth.uid(), 'UPDATE', tg_table_name, v_id, v_d);
  end if;
  return new;
end $$;
revoke all on function audit_changes() from public, anon, authenticated;

drop trigger if exists trg_audit_stores on stores;
create trigger trg_audit_stores after insert or update or delete on stores for each row
  execute function audit_changes('id', 'name', 'owner_id', 'commission_pct', 'max_discount_pct', 'discount_pct', 'is_active', 'is_open', 'fee_type', 'fee_base', 'fee_per_km', 'free_first_delivery');
drop trigger if exists trg_audit_profiles on profiles;
create trigger trg_audit_profiles after update on profiles for each row
  execute function audit_changes('id', 'role', 'driver_status', 'cash_limit', 'accept_blocked');
drop trigger if exists trg_audit_promo on promo_codes;
create trigger trg_audit_promo after insert or update or delete on promo_codes for each row
  execute function audit_changes('id', 'code', 'kind', 'value', 'min_order', 'max_uses', 'is_active', 'starts_at', 'ends_at');
drop trigger if exists trg_audit_banners on banners;
create trigger trg_audit_banners after insert or update or delete on banners for each row
  execute function audit_changes('id', 'title', 'is_active', 'placement', 'starts_at', 'ends_at', 'link_type', 'link_value');
drop trigger if exists trg_audit_items on menu_items;
create trigger trg_audit_items after update on menu_items for each row
  execute function audit_changes('id', 'price', 'approved', 'available', 'discount_pct');
drop trigger if exists trg_audit_orders on orders;
create trigger trg_audit_orders after update on orders for each row
  execute function audit_changes('id', 'driver_id', 'cash_settled_at');
drop trigger if exists trg_audit_ratings on ratings;
create trigger trg_audit_ratings after update on ratings for each row
  execute function audit_changes('order_id', 'handled_at', 'handled_note');

------------------------------------------------------------------------------------------------
-- 6) CLIENT ERROR LOG (so a crash on a customer's phone is visible to the admin)
------------------------------------------------------------------------------------------------
create table if not exists client_errors (
  id bigint generated always as identity primary key,
  at timestamptz not null default now(),
  user_id uuid,
  app text,
  message text,
  context text,
  ua text
);
create index if not exists client_errors_at_idx on client_errors (at desc);
alter table client_errors enable row level security;
drop policy if exists client_errors_read on client_errors;
create policy client_errors_read on client_errors for select using (is_admin());

create or replace function report_client_error(p_app text, p_message text, p_context text default null, p_ua text default null) returns void
language plpgsql security definer set search_path = public as $$
begin
  if auth.uid() is null then return; end if;
  if (select count(*) from client_errors where user_id = auth.uid() and at > now() - interval '1 hour') >= 10 then return; end if;
  delete from client_errors where at < now() - interval '30 days';
  insert into client_errors(user_id, app, message, context, ua)
  values (auth.uid(), left(coalesce(p_app, ''), 20), left(coalesce(p_message, ''), 300), left(coalesce(p_context, ''), 300), left(coalesce(p_ua, ''), 160));
end $$;
revoke all on function report_client_error(text, text, text, text) from public, anon;
grant execute on function report_client_error(text, text, text, text) to authenticated;

------------------------------------------------------------------------------------------------
-- 7) RATE LIMITS
------------------------------------------------------------------------------------------------
create or replace function trg_chat_limit() returns trigger language plpgsql security definer set search_path = public as $$
begin
  if (select count(*) from order_chat where sender_id = new.sender_id and created_at > now() - interval '1 minute') >= 20 then
    raise exception 'too_many';
  end if;
  return new;
end $$;
drop trigger if exists trg_chat_limit on order_chat;
create trigger trg_chat_limit before insert on order_chat for each row execute function trg_chat_limit();

create or replace function trg_fav_limit() returns trigger language plpgsql security definer set search_path = public as $$
begin
  if (select count(*) from favorites where user_id = new.user_id) >= 200 then raise exception 'bad_value'; end if;
  return new;
end $$;
drop trigger if exists trg_fav_limit on favorites;
create trigger trg_fav_limit before insert on favorites for each row execute function trg_fav_limit();

------------------------------------------------------------------------------------------------
-- 8) ORDERS: safe retry (idempotency key) + hourly cap
------------------------------------------------------------------------------------------------
alter table orders add column if not exists client_key text;
create unique index if not exists orders_client_key_uq on orders (customer_id, client_key) where client_key is not null;

drop function if exists place_order(uuid, jsonb, numeric, text, text, double precision, double precision, text);
create or replace function place_order(p_store uuid, p_items jsonb, p_tip numeric default 0, p_payment text default 'cash',
  p_address text default '', p_lat float8 default null, p_lng float8 default null, p_promo text default null, p_key text default null)
returns bigint language plpgsql security definer set search_path = public as $$
declare s stores; pr profiles; it record; v_item menu_items; pl jsonb; v_id bigint; v_sub numeric; v_fee numeric; v_pay numeric; v_disc numeric; v_base numeric; v_gate numeric;
        v_promo numeric := 0; v_tip numeric; v_km float8; v_code text := null;
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

  v_fee := case s.fee_type when 'free' then 0 else s.fee_base end;
  if s.fee_type = 'distance' and p_lat is not null and s.lat is not null then
    v_km := dist_km(s.lat, s.lng, p_lat, p_lng);
    v_fee := s.fee_base + greatest(0, ceil(v_km - s.fee_free_km)) * s.fee_per_km;
  end if;
  v_pay := case s.fee_type when 'free' then s.fee_base else v_fee end;   -- courier is always paid; the platform covers free delivery
  if s.free_first_delivery and s.fee_type <> 'free'
     and not exists (select 1 from orders where customer_id = auth.uid() and store_id = p_store and status not in ('rejected', 'cancelled')) then
    v_fee := 0;
  end if;
  v_tip := case when p_tip in (0,3,5,10) then p_tip else 0 end;

  begin
    insert into orders(store_id, customer_id, customer_name, customer_phone, payment, address, lat, lng, client_key)
    values (p_store, auth.uid(), pr.name, pr.phone, left(p_payment,40), left(p_address,200), p_lat, p_lng, p_key)
    returning id into v_id;
  exception when unique_violation then
    -- two taps raced: the other attempt won, return its order
    select o.id into v_id from orders o where o.customer_id = auth.uid() and o.client_key = p_key;
    return v_id;
  end;

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
    promo_code = v_code, promo_discount = v_promo,
    total = greatest(5, v_sub - v_disc - v_promo + v_fee + v_tip),
    commission_pct = s.commission_pct, commission = round((v_sub - v_disc) * s.commission_pct / 100, 2),
    driver_payout = v_pay + v_tip
  where id = v_id;
  return v_id;
end $$;
revoke all on function place_order(uuid, jsonb, numeric, text, text, double precision, double precision, text, text) from public, anon;
grant execute on function place_order(uuid, jsonb, numeric, text, text, double precision, double precision, text, text) to authenticated;

------------------------------------------------------------------------------------------------
-- 9) ADDRESSES: separate fields
------------------------------------------------------------------------------------------------
alter table addresses add column if not exists house text;
alter table addresses add column if not exists entrance text;
alter table addresses add column if not exists floor text;
alter table addresses add column if not exists apartment text;
alter table addresses add column if not exists note text;
do $$ begin
  if not exists (select 1 from pg_constraint where conname = 'addresses_parts_chk') then
    alter table addresses add constraint addresses_parts_chk check (
      (house is null or char_length(btrim(house)) between 1 and 20) and (entrance is null or char_length(entrance) <= 10)
      and (floor is null or char_length(floor) <= 10) and (apartment is null or char_length(apartment) <= 10)
      and (note is null or char_length(note) <= 120)) not valid;
  end if;
end $$;

------------------------------------------------------------------------------------------------
-- 10) RE-APPLY GRANTS for the functions created in this patch
------------------------------------------------------------------------------------------------
revoke execute on function check_image_url(text) from public, anon;
grant execute on function check_image_url(text) to authenticated;

------------------------------------------------------------------------------------------------
-- ROLLBACK of the stores column lock (only if the apps unexpectedly stop loading stores):
--   grant select on stores to authenticated;
------------------------------------------------------------------------------------------------
