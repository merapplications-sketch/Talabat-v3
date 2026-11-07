CREATE OR REPLACE FUNCTION public.deliver_order(p_id bigint, p_cash numeric DEFAULT NULL::numeric, p_note text DEFAULT NULL::text, p_photo text DEFAULT NULL::text)
 RETURNS void
 LANGUAGE plpgsql
 SECURITY DEFINER
 SET search_path TO 'public'
AS $function$
declare o orders; iscash boolean;
begin
  if not public.account_enabled() then raise exception 'account_blocked'; end if;
  select * into o from orders where id = p_id for update;
  if not found then raise exception 'not_found'; end if;
  if o.driver_id is distinct from auth.uid() or o.status <> 'pickedup' then raise exception 'bad_transition'; end if;
  -- the photo must be in this courier's folder for this order: <courier id>/<order id>/<file>.jpg
  if p_photo is not null and p_photo !~ ('^' || auth.uid()::text || '/' || p_id::text || '/[A-Za-z0-9_-]{8,64}\.jpg$') then raise exception 'bad_value'; end if;
  if coalesce(o.leave_at_door, false) and p_photo is null then raise exception 'photo_required'; end if;
  -- A well-shaped path is not evidence of a stored proof. Preserve optional
  -- photos: resolve Storage only inside this branch; never block photo-less cash.
  if p_photo is not null then
    if to_regclass('storage.objects') is null then raise exception 'photo_service_unavailable'; end if;
    perform 1 from storage.objects where bucket_id = 'proofs' and name = p_photo for key share;
    if not found then raise exception 'photo_not_found'; end if;
  end if;
  iscash := o.payment ~ '^(cash|Cash|Наличн)';
  if iscash then
    if p_cash is null or p_cash < 0 or p_cash in ('NaN'::numeric, 'Infinity'::numeric, '-Infinity'::numeric) then raise exception 'cash_required'; end if;
    if p_cash <> (o.total - coalesce(o.wallet_used, 0)) and coalesce(trim(p_note), '') = '' then raise exception 'note_required'; end if;
  end if;
  update orders set status = 'delivered', done_at = now(),
    cash_collected = case when iscash then p_cash end,
    cash_note = case when iscash then left(p_note, 200) end,
    delivery_photo = p_photo,
    arrived_cust_at = coalesce(arrived_cust_at, now())
  where id = p_id;
end $function$
