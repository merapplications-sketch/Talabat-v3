-- =============================================================================================
-- PATCH 34 — batch 2: courier steps, photo proof, restaurant cancel reasons (owner, 10 Oct 19:58).
-- Run after patch 33. Safe to run again.
--  * The courier marks "at the restaurant" and "at the customer" (orders.arrived_store_at / arrived_cust_at).
--    Pick-up is still only possible after the restaurant pressed "ready" (set_order_status, unchanged).
--  * "Leave at the door": the courier must add a photo to finish the delivery (orders.delivery_photo). Photos
--    are in a PRIVATE bucket "proofs": only that courier, the customer of the order and staff can open them.
--  * The restaurant cancels with a ready-made reason (out of stock, too busy, closing, other + note), also
--    while preparing. The customer sees the reason and an apology; points / wallet come back as before.
-- =============================================================================================

alter table orders add column if not exists arrived_store_at timestamptz;
alter table orders add column if not exists arrived_cust_at timestamptz;
alter table orders add column if not exists delivery_photo text check (delivery_photo is null or char_length(delivery_photo) <= 300);
alter table orders add column if not exists cancel_reason text check (cancel_reason is null or cancel_reason in ('out_of_stock', 'too_busy', 'closing', 'other'));
alter table orders add column if not exists cancel_note text check (cancel_note is null or char_length(cancel_note) <= 200);
alter table orders add column if not exists cancelled_by text check (cancelled_by is null or cancelled_by in ('store', 'customer', 'staff'));

-- ---------- the courier: "I am at the restaurant" / "I am at the customer" ----------
create or replace function driver_arrived(p_id bigint, p_where text) returns void
language plpgsql security definer set search_path = public as $$
declare o orders;
begin
  select * into o from orders where id = p_id for update;
  if not found then raise exception 'not_found'; end if;
  if o.driver_id is distinct from auth.uid() then raise exception 'not_allowed'; end if;
  if p_where = 'store' then
    if o.status not in ('preparing', 'ready') then raise exception 'bad_transition'; end if;
    update orders set arrived_store_at = coalesce(arrived_store_at, now()) where id = p_id;
  elsif p_where = 'customer' then
    if o.status <> 'pickedup' then raise exception 'bad_transition'; end if;
    update orders set arrived_cust_at = coalesce(arrived_cust_at, now()) where id = p_id;
  else
    raise exception 'bad_value';
  end if;
  -- also in the order timeline when the existing events table accepts it (its kinds are not known here)
  begin
    insert into order_events(order_id, kind) values (p_id, case p_where when 'store' then 'at_store' else 'at_customer' end);
  exception when others then null;
  end;
end $$;
revoke all on function driver_arrived(bigint, text) from public, anon;
grant execute on function driver_arrived(bigint, text) to authenticated;

-- ---------- delivery: the same rules as patch 21 + the photo for "leave at the door" ----------
drop function if exists deliver_order(bigint, numeric, text);
create or replace function deliver_order(p_id bigint, p_cash numeric default null, p_note text default null, p_photo text default null) returns void
language plpgsql security definer set search_path = public as $$
declare o orders; iscash boolean;
begin
  select * into o from orders where id = p_id for update;
  if not found then raise exception 'not_found'; end if;
  if o.driver_id is distinct from auth.uid() or o.status <> 'pickedup' then raise exception 'bad_transition'; end if;
  -- the photo must be in this courier's folder for this order: <courier id>/<order id>/<file>.jpg
  if p_photo is not null and p_photo !~ ('^' || auth.uid()::text || '/' || p_id::text || '/[A-Za-z0-9_-]{8,64}\.jpg$') then raise exception 'bad_value'; end if;
  if coalesce(o.leave_at_door, false) and p_photo is null then raise exception 'photo_required'; end if;
  iscash := o.payment ~ '^(cash|Cash|Наличн)';
  if iscash then
    if p_cash is null or p_cash < 0 then raise exception 'cash_required'; end if;
    if p_cash <> (o.total - coalesce(o.wallet_used, 0)) and coalesce(trim(p_note), '') = '' then raise exception 'note_required'; end if;
  end if;
  update orders set status = 'delivered', done_at = now(),
    cash_collected = case when iscash then p_cash end,
    cash_note = case when iscash then left(p_note, 200) end,
    delivery_photo = p_photo,
    arrived_cust_at = coalesce(arrived_cust_at, now())
  where id = p_id;
end $$;
revoke all on function deliver_order(bigint, numeric, text, text) from public, anon;
grant execute on function deliver_order(bigint, numeric, text, text) to authenticated;

-- ---------- the restaurant cancels with a reason (new orders and orders being prepared) ----------
create or replace function reject_order(p_id bigint, p_reason text, p_note text default null) returns void
language plpgsql security definer set search_path = public as $$
declare o orders;
begin
  if p_reason is null or p_reason not in ('out_of_stock', 'too_busy', 'closing', 'other') then raise exception 'bad_value'; end if;
  if p_reason = 'other' and char_length(btrim(coalesce(p_note, ''))) < 3 then raise exception 'note_required'; end if;
  select * into o from orders where id = p_id for update;
  if not found then raise exception 'not_found'; end if;
  if not owns_store(o.store_id) then raise exception 'not_allowed'; end if;
  if o.status not in ('pending', 'preparing') then raise exception 'bad_transition'; end if;
  update orders set status = 'rejected', done_at = now(), cancel_reason = p_reason,
    cancel_note = nullif(left(btrim(coalesce(p_note, '')), 200), ''), cancelled_by = 'store'
  where id = p_id;
end $$;
revoke all on function reject_order(bigint, text, text) from public, anon;
grant execute on function reject_order(bigint, text, text) to authenticated;

-- ---------- private photo bucket ----------
do $$
begin
  if to_regclass('storage.buckets') is null then raise notice 'storage schema not found: skipping the proofs bucket'; return; end if;
  insert into storage.buckets (id, name, public, file_size_limit, allowed_mime_types)
  values ('proofs', 'proofs', false, 1048576, array['image/jpeg'])
  on conflict (id) do update set public = false, file_size_limit = 1048576, allowed_mime_types = array['image/jpeg'];
  execute 'drop policy if exists proofs_insert on storage.objects';
  execute 'drop policy if exists proofs_read on storage.objects';
  -- upload: only the courier of that order, into <his id>/<order id>/, while he is delivering it
  execute $p$create policy proofs_insert on storage.objects for insert to authenticated
    with check (bucket_id = 'proofs' and (storage.foldername(name))[1] = auth.uid()::text
      and exists (select 1 from public.orders o where o.id::text = (storage.foldername(name))[2] and o.driver_id = auth.uid() and o.status = 'pickedup'))$p$;
  -- open: that courier, the customer of the order, admin / staff with the orders permission
  execute $p$create policy proofs_read on storage.objects for select to authenticated
    using (bucket_id = 'proofs' and ((storage.foldername(name))[1] = auth.uid()::text or public.is_admin() or public.has_perm('orders')
      or exists (select 1 from public.orders o where o.id::text = (storage.foldername(name))[2] and o.customer_id = auth.uid())))$p$;
end $$;

create or replace function courier_steps_version() returns int language sql immutable as $$ select 34 $$;
grant execute on function courier_steps_version() to authenticated;
