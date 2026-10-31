-- Live definitions read 31 Oct 2026 (owner, read-only query). Reference only — not to be run.
CREATE OR REPLACE FUNCTION public.delivery_calc(p_store uuid, p_lat double precision, p_lng double precision, p_uid uuid)
 RETURNS jsonb
 LANGUAGE plpgsql
 STABLE SECURITY DEFINER
 SET search_path TO 'public'
AS $function$
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
end $function$;

CREATE OR REPLACE FUNCTION public.dist_km(a1 double precision, o1 double precision, a2 double precision, o2 double precision)
 RETURNS double precision
 LANGUAGE sql
 IMMUTABLE
AS $function$ select 2*6371*asin(sqrt(power(sin(radians(a2-a1)/2),2) + cos(radians(a1))*cos(radians(a2))*power(sin(radians(o2-o1)/2),2))) $function$;
