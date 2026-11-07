CREATE OR REPLACE FUNCTION public.set_my_cashback(p_store uuid, p_pct numeric)
 RETURNS void
 LANGUAGE plpgsql
 SECURITY DEFINER
 SET search_path TO 'public'
AS $function$
begin
  if not public.account_enabled() then raise exception 'account_blocked'; end if;
  if not exists (select 1 from stores where id = p_store and owner_id = auth.uid()) then raise exception 'not_allowed'; end if;
  if p_pct is null or p_pct not between 0 and 50 then raise exception 'bad_value'; end if;
  update stores set cashback_pct = round(p_pct, 1) where id = p_store;
end $function$
;
CREATE OR REPLACE FUNCTION public.set_my_discount(p_store text, p_pct numeric)
 RETURNS void
 LANGUAGE plpgsql
 SECURITY DEFINER
 SET search_path TO 'public'
AS $function$
declare mx numeric;
begin
  if not public.account_enabled() then raise exception 'account_blocked'; end if;
  if auth.uid() is null then raise exception 'auth'; end if;
  select max_discount_pct into mx from stores
   where id::text = p_store and owner_id = auth.uid() for update;
  if not found then raise exception 'not_allowed'; end if;
  if p_pct is null or p_pct < 0 or p_pct > 100 then raise exception 'bad_value'; end if;
  if p_pct > mx then raise exception 'discount_over_max'; end if;
  perform set_config('app.bypass', '1', true);
  update stores set discount_pct = p_pct where id::text = p_store and owner_id = auth.uid();
  perform set_config('app.bypass', '', true);
end $function$
;