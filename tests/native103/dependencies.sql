-- Captured function bodies; minimal tables and settings below are explicit synthetic dependencies.
create table promo_codes(code text primary key,is_active boolean,starts_at timestamptz,ends_at timestamptz,min_order numeric,max_uses int,kind text,value numeric);
create table loyalty_lots(id bigserial primary key,user_id uuid,points_left int,expires_at timestamptz);
create table loyalty_ledger(user_id uuid,points int,kind text,order_id bigint references orders(id));
-- Test settings only: NOT asserted to be current hosted settings/function implementation.
create function loyalty_setting(text) returns numeric language sql as $$select case $1 when 'loyalty_points_per_tjs' then 10 when 'loyalty_min_redeem' then 10 when 'loyalty_voucher_points' then 10 when 'loyalty_min_order' then 0 else 0 end::numeric$$;
CREATE OR REPLACE FUNCTION public.promo_eval(p_code text, p_base numeric, p_uid uuid, p_lock boolean DEFAULT false, p_gate numeric DEFAULT NULL::numeric)
 RETURNS numeric
 LANGUAGE plpgsql
 SECURITY DEFINER
 SET search_path TO 'public'
AS $function$
declare c promo_codes; k text := upper(trim(coalesce(p_code, ''))); d numeric; n int;
begin
  if k !~ '^[A-Z0-9_-]{3,20}$' then raise exception 'promo_invalid'; end if;
  if p_lock then perform pg_advisory_xact_lock(hashtext('promo:' || k)); end if;
  select * into c from promo_codes
   where upper(code) = k and is_active
     and (starts_at is null or starts_at <= now()) and (ends_at is null or ends_at > now());
  if not found then raise exception 'promo_invalid'; end if;
  if coalesce(p_gate, p_base) < c.min_order then raise exception 'promo_min'; end if;
  if exists (select 1 from orders where customer_id = p_uid and promo_code = k and status not in ('rejected', 'cancelled')) then
    raise exception 'promo_used';
  end if;
  if c.max_uses is not null then
    select count(*) into n from orders where promo_code = k and status not in ('rejected', 'cancelled');
    if n >= c.max_uses then raise exception 'promo_limit'; end if;
  end if;
  d := case c.kind when 'percent' then round(p_base * c.value / 100, 2) else least(c.value, p_base) end;
  return greatest(0, least(d, p_base));
end $function$
;
CREATE OR REPLACE FUNCTION public.loyalty_balance(p_user uuid)
 RETURNS integer
 LANGUAGE sql
 STABLE SECURITY DEFINER
 SET search_path TO 'public'
AS $function$
  select coalesce(sum(points_left), 0)::int from loyalty_lots where user_id = p_user and points_left > 0 and expires_at > now()
$function$
;
CREATE OR REPLACE FUNCTION public.loyalty_spend(p_user uuid, p_points integer, p_order bigint)
 RETURNS void
 LANGUAGE plpgsql
 SECURITY DEFINER
 SET search_path TO 'public'
AS $function$
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
end $function$
;
