-- ============================================================
-- schema_patch27.sql : restaurant brands with several branches
-- * brands: one owner, many branches. A branch is a normal store row (own menu, hours, address, open/closed),
--   so ordering, delivery fee, cash and ratings keep working exactly as before.
-- * branch_create(): the brand owner adds a branch; the menu (with options) is COPIED from the brand's first branch,
--   the commercial terms (commission, delivery, discount) are inherited and cannot be changed by the owner.
--   The new branch starts CLOSED until the owner opens it. Max 25 branches per brand, max 5 new branches per day.
-- * brand_sync_menu(): copies prices/availability/new dishes from one branch to another (owner only).
-- * brand_route(): for the customer app: nearest OPEN branch first, then the ones that have every dish in the cart.
-- * brand_stats(): per-branch orders / revenue for the owner.
-- * brand_create / brand_attach / brand_detach: admin only.
-- Safe to run twice. Requires patch 26 (has_perm) to exist only for nothing here - it does not depend on it.
-- ============================================================
begin;

create table if not exists brands (
  id         uuid primary key default gen_random_uuid(),
  name       text not null check (char_length(btrim(name)) between 2 and 60),
  owner_id   uuid not null references profiles(id),
  created_at timestamptz not null default now()
);
alter table brands enable row level security;
drop policy if exists brands_read on brands;
create policy brands_read on brands for select to public using (auth.uid() is not null);
revoke insert, update, delete on brands from anon, authenticated;   -- changes only through the functions below

alter table stores add column if not exists brand_id    uuid references brands(id) on delete set null;
alter table stores add column if not exists branch_name text;
do $$ begin
  if not exists (select 1 from pg_constraint where conname = 'stores_branch_name_len') then
    alter table stores add constraint stores_branch_name_len check (branch_name is null or char_length(btrim(branch_name)) between 1 and 40);
  end if;
end $$;
create index if not exists stores_brand_idx on stores(brand_id) where brand_id is not null;

-- ---------------- admin: brands ----------------
create or replace function brand_create(p_name text, p_owner_email text) returns uuid
language plpgsql security definer set search_path = public as $$
declare u uuid; v_id uuid; v_name text := btrim(coalesce(p_name, ''));
begin
  if not is_admin() then raise exception 'not_allowed'; end if;
  if char_length(v_name) < 2 or char_length(v_name) > 60 then raise exception 'bad_value'; end if;
  select id into u from auth.users where lower(email) = lower(btrim(coalesce(p_owner_email, '')));
  if u is null or not exists(select 1 from profiles where id = u) then raise exception 'user_not_found'; end if;
  insert into brands(name, owner_id) values (v_name, u) returning id into v_id;
  insert into audit_log(user_id, action, table_name, row_id, details) values (auth.uid(), 'BRAND_CREATE', 'brands', v_id::text, jsonb_build_object('name', v_name, 'owner', u));
  return v_id;
end $$;

create or replace function brand_attach(p_store uuid, p_brand uuid, p_branch text default null) returns void
language plpgsql security definer set search_path = public as $$
declare b brands; s stores; v_br text := nullif(btrim(coalesce(p_branch, '')), '');
begin
  if not is_admin() then raise exception 'not_allowed'; end if;
  select * into b from brands where id = p_brand;  if not found then raise exception 'not_found'; end if;
  select * into s from stores where id = p_store;  if not found then raise exception 'not_found'; end if;
  if s.owner_id is distinct from b.owner_id then raise exception 'owner_mismatch'; end if;
  if v_br is not null and char_length(v_br) > 40 then raise exception 'bad_value'; end if;
  update stores set brand_id = p_brand, branch_name = v_br where id = p_store;
  insert into audit_log(user_id, action, table_name, row_id, details) values (auth.uid(), 'BRAND_ATTACH', 'stores', p_store::text, jsonb_build_object('brand', p_brand, 'branch', v_br));
end $$;

create or replace function brand_detach(p_store uuid) returns void
language plpgsql security definer set search_path = public as $$
begin
  if not is_admin() then raise exception 'not_allowed'; end if;
  update stores set brand_id = null, branch_name = null where id = p_store and brand_id is not null;
  if not found then raise exception 'not_found'; end if;
  insert into audit_log(user_id, action, table_name, row_id, details) values (auth.uid(), 'BRAND_DETACH', 'stores', p_store::text, '{}'::jsonb);
end $$;

-- ---------------- owner: add a branch ----------------
create or replace function branch_create(p_brand uuid, p_branch text, p_address text, p_lat double precision, p_lng double precision, p_phone text)
returns uuid language plpgsql security definer set search_path = public as $$
declare b brands; t stores; v_id uuid := gen_random_uuid(); v_br text := btrim(coalesce(p_branch, '')); v_name text; v_ph text := norm_phone(p_phone); v_addr text := nullif(btrim(coalesce(p_address, '')), '');
begin
  select * into b from brands where id = p_brand;
  if not found then raise exception 'not_found'; end if;
  if not (b.owner_id = auth.uid() or is_admin()) then raise exception 'not_allowed'; end if;
  if char_length(v_br) < 1 or char_length(v_br) > 40 then raise exception 'bad_value'; end if;
  if v_addr is not null and char_length(v_addr) > 200 then raise exception 'bad_value'; end if;
  if p_lat is null or p_lng is null or p_lat not between -90 and 90 or p_lng not between -180 and 180 then raise exception 'bad_value'; end if;
  if v_ph is null then raise exception 'bad_phone'; end if;
  v_name := b.name || ' · ' || v_br;
  if char_length(v_name) > 80 then raise exception 'bad_value'; end if;
  if exists(select 1 from stores where lower(name) = lower(v_name)) then raise exception 'name_taken'; end if;
  if (select count(*) from stores where brand_id = p_brand) >= 25 then raise exception 'too_many'; end if;
  if (select count(*) from stores where brand_id = p_brand and created_at > now() - interval '1 day') >= 5 then raise exception 'too_many'; end if;
  select * into t from stores where brand_id = p_brand order by created_at limit 1;
  if not found then raise exception 'no_template'; end if;   -- attach at least one existing store first

  insert into stores(id, owner_id, name, category, description, logo_url, cover_url, address, lat, lng, commission_pct, fee_type, fee_base, fee_per_km, fee_free_km,
                     discount_pct, max_discount_pct, free_first_delivery, is_open, is_active, is_featured, phone, brand_id, branch_name)
  values (v_id, b.owner_id, v_name, t.category, t.description, t.logo_url, t.cover_url, v_addr, p_lat, p_lng, t.commission_pct, t.fee_type, t.fee_base, t.fee_per_km, t.fee_free_km,
          t.discount_pct, t.max_discount_pct, t.free_first_delivery, false, true, false, v_ph, p_brand, v_br);

  perform copy_menu(t.id, v_id, false);
  insert into audit_log(user_id, action, table_name, row_id, details) values (auth.uid(), 'BRANCH_CREATE', 'stores', v_id::text, jsonb_build_object('brand', p_brand, 'name', v_name, 'from', t.id));
  return v_id;
end $$;

-- internal helper: copy dishes (+ option groups + options) from one store to another. p_update=true also refreshes matching dishes.
create or replace function copy_menu(p_from uuid, p_to uuid, p_update boolean) returns jsonb
language plpgsql security definer set search_path = public as $$
declare v_add int := 0; v_upd int := 0;
begin
  if p_update then
    update menu_items d set price = s.price, discount_pct = s.discount_pct, available = s.available, section = s.section, popular = s.popular,
           image_url = coalesce(s.image_url, d.image_url)
      from menu_items s
     where s.store_id = p_from and d.store_id = p_to and lower(btrim(d.name)) = lower(btrim(s.name))
       and (d.price, d.discount_pct, d.available, d.section, d.popular) is distinct from (s.price, s.discount_pct, s.available, s.section, s.popular);
    get diagnostics v_upd = row_count;
  end if;
  with m as (
    select i.id as old_id, gen_random_uuid() as new_id from menu_items i
     where i.store_id = p_from and i.approved
       and not exists(select 1 from menu_items x where x.store_id = p_to and lower(btrim(x.name)) = lower(btrim(i.name)))),
  ins as (
    insert into menu_items(id, store_id, name, price, image_url, popular, available, section, discount_pct)
    select m.new_id, p_to, i.name, i.price, i.image_url, i.popular, i.available, i.section, i.discount_pct
      from menu_items i join m on m.old_id = i.id returning 1),
  g as (select og.id as old_g, gen_random_uuid() as new_g, m.new_id as item, og.name, og.required, og.max_sel, og.sort
          from item_option_groups og join m on m.old_id = og.item_id),
  insg as (insert into item_option_groups(id, item_id, name, required, max_sel, sort) select new_g, item, name, required, max_sel, sort from g returning 1),
  inso as (insert into item_options(group_id, name, price_delta, available, sort)
           select g.new_g, o.name, o.price_delta, o.available, o.sort from item_options o join g on g.old_g = o.group_id returning 1)
  select (select count(*) from ins) into v_add;
  return jsonb_build_object('added', v_add, 'updated', v_upd);
end $$;
revoke all on function copy_menu(uuid, uuid, boolean) from public, anon, authenticated;   -- internal only

create or replace function brand_sync_menu(p_from uuid, p_to uuid) returns jsonb
language plpgsql security definer set search_path = public as $$
declare a stores; b stores; br brands; r jsonb;
begin
  select * into a from stores where id = p_from;  select * into b from stores where id = p_to;
  if a.id is null or b.id is null or p_from = p_to then raise exception 'not_found'; end if;
  if a.brand_id is null or a.brand_id is distinct from b.brand_id then raise exception 'bad_value'; end if;
  select * into br from brands where id = a.brand_id;
  if not (br.owner_id = auth.uid() or is_admin()) then raise exception 'not_allowed'; end if;
  r := copy_menu(p_from, p_to, true);
  insert into audit_log(user_id, action, table_name, row_id, details) values (auth.uid(), 'BRANCH_SYNC', 'stores', p_to::text, r || jsonb_build_object('from', p_from));
  return r;
end $$;

-- ---------------- customer app: which branch should serve me ----------------
create or replace function brand_route(p_brand uuid, p_lat double precision, p_lng double precision, p_names text[] default '{}')
returns table(store_id uuid, name text, branch_name text, dist_km numeric, is_open boolean, missing text[])
language sql stable security definer set search_path = public as $$
  with want as (select distinct lower(btrim(x)) as n from unnest(coalesce(p_names, '{}')) x where btrim(x) <> '' limit 60),
  b as (
    select s.id, s.name, s.branch_name, s.is_open,
           case when p_lat is null or p_lng is null or s.lat is null or s.lng is null then null else round(dist_km(p_lat, p_lng, s.lat, s.lng)::numeric, 2) end as d,
           array(select w.n from want w where not exists(select 1 from menu_items i where i.store_id = s.id and i.available and i.approved and lower(btrim(i.name)) = w.n)) as miss
      from stores s where s.brand_id = p_brand and s.is_active and auth.uid() is not null)
  select id, name, branch_name, d, is_open, miss from b
   order by (is_open and cardinality(miss) = 0) desc, is_open desc, cardinality(miss), d nulls last, name
$$;

-- ---------------- owner analytics ----------------
create or replace function brand_stats(p_brand uuid, p_days integer default 30)
returns table(store_id uuid, name text, branch_name text, orders bigint, delivered bigint, cancelled bigint, revenue numeric)
language sql stable security definer set search_path = public as $$
  select s.id, s.name, s.branch_name,
         count(o.id), count(o.id) filter (where o.status = 'delivered'), count(o.id) filter (where o.status in ('cancelled', 'rejected')),
         coalesce(sum(o.total) filter (where o.status = 'delivered'), 0)::numeric
    from stores s
    join brands b on b.id = s.brand_id
    left join orders o on o.store_id = s.id and o.created_at > now() - make_interval(days => least(greatest(coalesce(p_days, 30), 1), 365))
   where s.brand_id = p_brand and (b.owner_id = auth.uid() or is_admin())
   group by s.id, s.name, s.branch_name order by s.name
$$;

revoke all on function brand_create(text, text), brand_attach(uuid, uuid, text), brand_detach(uuid), branch_create(uuid, text, text, double precision, double precision, text),
  brand_sync_menu(uuid, uuid), brand_route(uuid, double precision, double precision, text[]), brand_stats(uuid, integer) from public, anon;
grant execute on function brand_create(text, text), brand_attach(uuid, uuid, text), brand_detach(uuid), branch_create(uuid, text, text, double precision, double precision, text),
  brand_sync_menu(uuid, uuid), brand_route(uuid, double precision, double precision, text[]), brand_stats(uuid, integer) to authenticated;

commit;
