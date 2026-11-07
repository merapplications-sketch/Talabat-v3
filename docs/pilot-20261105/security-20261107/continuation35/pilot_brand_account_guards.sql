-- C35-BRAND: test project only; preserve signatures, ACLs, search_path and business rules.
set lock_timeout='2s';
do $guard$ begin if pg_get_functiondef('public.branch_create(uuid,text,text,double precision,double precision,text)'::regprocedure) is distinct from $baseline$CREATE OR REPLACE FUNCTION public.branch_create(p_brand uuid, p_branch text, p_address text, p_lat double precision, p_lng double precision, p_phone text)
 RETURNS uuid
 LANGUAGE plpgsql
 SECURITY DEFINER
 SET search_path TO 'public'
AS $function$
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
end $function$
$baseline$ then raise exception 'Concurrent definition change: branch_create(uuid,text,text,double precision,double precision,text)'; end if; end $guard$;
CREATE OR REPLACE FUNCTION public.branch_create(p_brand uuid, p_branch text, p_address text, p_lat double precision, p_lng double precision, p_phone text)
 RETURNS uuid
 LANGUAGE plpgsql
 SECURITY DEFINER
 SET search_path TO 'public'
AS $function$
declare b brands; t stores; v_id uuid := gen_random_uuid(); v_br text := btrim(coalesce(p_branch, '')); v_name text; v_ph text := norm_phone(p_phone); v_addr text := nullif(btrim(coalesce(p_address, '')), '');
begin
  if not public.account_enabled() then raise exception 'account_blocked'; end if;
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
end $function$
;
do $guard$ begin if pg_get_functiondef('public.brand_stats(uuid,integer)'::regprocedure) is distinct from $baseline$CREATE OR REPLACE FUNCTION public.brand_stats(p_brand uuid, p_days integer DEFAULT 30)
 RETURNS TABLE(store_id uuid, name text, branch_name text, orders bigint, delivered bigint, cancelled bigint, revenue numeric)
 LANGUAGE sql
 STABLE SECURITY DEFINER
 SET search_path TO 'public'
AS $function$
  select s.id, s.name, s.branch_name,
         count(o.id), count(o.id) filter (where o.status = 'delivered'), count(o.id) filter (where o.status in ('cancelled', 'rejected')),
         coalesce(sum(o.total) filter (where o.status = 'delivered'), 0)::numeric
    from stores s
    join brands b on b.id = s.brand_id
    left join orders o on o.store_id = s.id and o.created_at > now() - make_interval(days => least(greatest(coalesce(p_days, 30), 1), 365))
   where s.brand_id = p_brand and (b.owner_id = auth.uid() or is_admin())
   group by s.id, s.name, s.branch_name order by s.name
$function$
$baseline$ then raise exception 'Concurrent definition change: brand_stats(uuid,integer)'; end if; end $guard$;
CREATE OR REPLACE FUNCTION public.brand_stats(p_brand uuid, p_days integer DEFAULT 30)
 RETURNS TABLE(store_id uuid, name text, branch_name text, orders bigint, delivered bigint, cancelled bigint, revenue numeric)
 LANGUAGE sql
 STABLE SECURITY DEFINER
 SET search_path TO 'public'
AS $function$
  select s.id, s.name, s.branch_name,
         count(o.id), count(o.id) filter (where o.status = 'delivered'), count(o.id) filter (where o.status in ('cancelled', 'rejected')),
         coalesce(sum(o.total) filter (where o.status = 'delivered'), 0)::numeric
    from stores s
    join brands b on b.id = s.brand_id
    left join orders o on o.store_id = s.id and o.created_at > now() - make_interval(days => least(greatest(coalesce(p_days, 30), 1), 365))
   where public.account_enabled() and s.brand_id = p_brand and (b.owner_id = auth.uid() or is_admin())
   group by s.id, s.name, s.branch_name order by s.name
$function$
;
do $guard$ begin if pg_get_functiondef('public.brand_sync_menu(uuid,uuid)'::regprocedure) is distinct from $baseline$CREATE OR REPLACE FUNCTION public.brand_sync_menu(p_from uuid, p_to uuid)
 RETURNS jsonb
 LANGUAGE plpgsql
 SECURITY DEFINER
 SET search_path TO 'public'
AS $function$
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
end $function$
$baseline$ then raise exception 'Concurrent definition change: brand_sync_menu(uuid,uuid)'; end if; end $guard$;
CREATE OR REPLACE FUNCTION public.brand_sync_menu(p_from uuid, p_to uuid)
 RETURNS jsonb
 LANGUAGE plpgsql
 SECURITY DEFINER
 SET search_path TO 'public'
AS $function$
declare a stores; b stores; br brands; r jsonb;
begin
  if not public.account_enabled() then raise exception 'account_blocked'; end if;
  select * into a from stores where id = p_from;  select * into b from stores where id = p_to;
  if a.id is null or b.id is null or p_from = p_to then raise exception 'not_found'; end if;
  if a.brand_id is null or a.brand_id is distinct from b.brand_id then raise exception 'bad_value'; end if;
  select * into br from brands where id = a.brand_id;
  if not (br.owner_id = auth.uid() or is_admin()) then raise exception 'not_allowed'; end if;
  r := copy_menu(p_from, p_to, true);
  insert into audit_log(user_id, action, table_name, row_id, details) values (auth.uid(), 'BRANCH_SYNC', 'stores', p_to::text, r || jsonb_build_object('from', p_from));
  return r;
end $function$
;

