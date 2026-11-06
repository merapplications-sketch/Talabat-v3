-- Apply only to the approved isolated pilot. No historical balance mutations.
-- Both reads use the caller's RLS, auth.uid(), and one statement snapshot.
create or replace function public.points_snapshot() returns jsonb
language sql stable security invoker set search_path = public, pg_temp as $$
  select jsonb_build_object('balance', (public.loyalty_summary()->>'balance')::int,
    'rows', coalesce((select jsonb_agg(to_jsonb(e) order by e.id desc) from
      (select id,points,kind,order_id,created_at from public.loyalty_ledger
       where user_id=auth.uid() order by id desc limit 60) e),'[]'::jsonb),
    'consistent',true) where auth.uid() is not null
$$;
revoke all on function public.points_snapshot() from public,anon;
grant execute on function public.points_snapshot() to authenticated;

create or replace function public.order_wallet_entries(p_order bigint) returns jsonb
language plpgsql stable security invoker set search_path = public, pg_temp as $$
begin
  if auth.uid() is null or not exists(select 1 from public.orders where id=p_order and customer_id=auth.uid()) then
    raise exception 'not_allowed';
  end if;
  return (with selected as (
    select id,amount,kind,order_id,ticket_id,created_at,created_by,note from public.wallet_entries
    where user_id=auth.uid() and order_id=p_order order by id desc limit 1001
  ), shown as (select * from selected order by id desc limit 1000)
  select jsonb_build_object('entries',coalesce((select jsonb_agg(to_jsonb(s) order by s.id desc) from shown s),'[]'::jsonb),
    'partial',(select count(*)>1000 from selected)));
end $$;
revoke all on function public.order_wallet_entries(bigint) from public,anon;
grant execute on function public.order_wallet_entries(bigint) to authenticated;

-- Catalog images only. Delivery proofs remain private in their existing bucket.
insert into storage.buckets(id,name,public,file_size_limit,allowed_mime_types)
values ('media','media',true,1048576,array['image/jpeg','image/png','image/webp'])
on conflict(id) do nothing;
create policy pilot_media_insert on storage.objects for insert to authenticated
with check(bucket_id='media' and (storage.foldername(name))[1]=auth.uid()::text
  and (public.is_admin() or public.has_perm('stores') or public.has_perm('content')
    or exists(select 1 from public.stores where owner_id=auth.uid())));
-- No update/delete grants: client uploads new UUID paths with upsert=false.
create policy pilot_media_read on storage.objects for select to authenticated
using(bucket_id='media' and ((storage.foldername(name))[1]=auth.uid()::text or public.is_admin()));
