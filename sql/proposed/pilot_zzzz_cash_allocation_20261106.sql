-- Owner-approved cash accounting correction. PROPOSED / isolated only.
-- No historical balance rewrite, no restaurant-commission offset.
begin;
create table finance_private.cash_delivery_policy (
 store_id uuid primary key references public.stores(id),
 platform_amount numeric(12,2) not null check(platform_amount>=0),
 reference text not null check(length(btrim(reference))>=3)
);
alter table finance_private.cash_delivery_policy enable row level security;
revoke all on finance_private.cash_delivery_policy from public,anon,authenticated;
-- Deliberately no production default: approved allocation must be supplied explicitly.
alter table public.orders add column cash_allocation_version integer,
 add column cash_platform_share numeric(12,2),
 add column cash_driver_delivery_share numeric(12,2),
 add column cash_allocation_reference text;
alter table public.orders add constraint cash_allocation_consistent check (
 (cash_allocation_version is null and cash_platform_share is null and cash_driver_delivery_share is null and cash_allocation_reference is null)
 or (cash_allocation_version=1 and cash_platform_share is not null and cash_driver_delivery_share is not null
 and cash_allocation_reference is not null and cash_platform_share>=0 and cash_driver_delivery_share>=0
 and cash_platform_share+cash_driver_delivery_share=delivery_fee));
create function finance_private.snapshot_cash(p_order bigint) returns void
language plpgsql security definer set search_path=pg_catalog,public as $$
declare o public.orders; p finance_private.cash_delivery_policy;
begin
 select * into o from public.orders where id=p_order for update;
 if o.payment<>'cash' then return; end if;
 if o.cash_allocation_version is not null then return; end if;
 select * into p from finance_private.cash_delivery_policy where store_id=o.store_id for share;
 if not found then raise exception 'cash_allocation_required'; end if;
 if p.platform_amount>o.delivery_fee then raise exception 'cash_allocation_exceeds_fee'; end if;
 perform set_config('talabot.cash_snapshot',o.id::text,true);
 update public.orders set cash_allocation_version=1,cash_platform_share=p.platform_amount,
 cash_driver_delivery_share=o.delivery_fee-p.platform_amount,cash_allocation_reference=p.reference,
 driver_payout=driver_payout-p.platform_amount where id=o.id;
 perform set_config('talabot.cash_snapshot','',true);
end $$;
create function finance_private.guard_cash_allocation() returns trigger
language plpgsql set search_path=pg_catalog,public as $$
begin
 if tg_op='INSERT' then
  if new.cash_allocation_version is not null or new.cash_platform_share is not null or new.cash_driver_delivery_share is not null or new.cash_allocation_reference is not null then raise exception 'cash_allocation_immutable'; end if;
 elsif row(new.cash_allocation_version,new.cash_platform_share,new.cash_driver_delivery_share,new.cash_allocation_reference)
 is distinct from row(old.cash_allocation_version,old.cash_platform_share,old.cash_driver_delivery_share,old.cash_allocation_reference) then
  if old.cash_allocation_version is not null or coalesce(current_setting('talabot.cash_snapshot',true),'')<>old.id::text then raise exception 'cash_allocation_immutable'; end if;
 end if;
 return new;
end $$;
create trigger cash_allocation_guard before insert or update on public.orders for each row execute function finance_private.guard_cash_allocation();
revoke all on function finance_private.snapshot_cash(bigint),finance_private.guard_cash_allocation() from public,anon,authenticated;
-- Extend the final pricing point of the exact reviewed place_order, before approval registration.
do $$ declare f record; src text; needle text := '  perform set_config(''talabot.order_building'',coalesce(v_build_prev,''''),true);'; begin
 for f in select oid from pg_proc where pronamespace='public'::regnamespace and proname='place_order' loop
  src:=pg_get_functiondef(f.oid);
  if position(needle in src)=0 then raise exception 'unexpected_place_order_source'; end if;
  execute replace(src,needle,'  perform finance_private.snapshot_cash(v_id);'||chr(10)||needle);
 end loop;
end $$;
create or replace function public.cash_balances() returns table(driver_id uuid,balance numeric)
language plpgsql stable security definer set search_path=pg_catalog,public as $$
begin
 if exists(select 1 from public.orders o where o.payment='cash' and o.status='delivered'
 and o.cash_collected is not null and o.cash_settled_at is null and o.cash_allocation_version is null
 and (public.has_perm('finance') or o.driver_id=auth.uid())) then raise exception 'legacy_cash_reconciliation_required'; end if;
 return query select o.driver_id,coalesce(sum(o.cash_platform_share),0)::numeric from public.orders o
 where o.payment='cash' and o.status='delivered' and o.cash_collected is not null and o.cash_settled_at is null
 and o.driver_id is not null and (public.has_perm('finance') or o.driver_id=auth.uid()) group by o.driver_id;
end $$;
create or replace function public.finance_execute(p_request uuid,p_operation text,p_target uuid,p_amount numeric default null,p_note text default null)
returns jsonb language plpgsql security definer set search_path=pg_catalog,public as $$
declare old finance_private.commands; total numeric; ids bigint[]; entry_id bigint; v_note text:=btrim(coalesce(p_note,'')); v_a numeric:=round(coalesce(p_amount,0),2); reply jsonb; receipt_id bigint;
begin
 if not finance_private.accountant() then raise exception 'not_allowed'; end if;
 if p_request is null or p_target is null or p_operation is null or p_operation not in ('settle_cash','wallet_adjust') then raise exception 'bad_value'; end if;
 -- Same key serializes across connections; ownership and payload are verified, never silently reused.
 perform pg_advisory_xact_lock(hashtextextended('finance-request:'||p_request::text,0));
 select * into old from finance_private.commands where request=p_request;
 if found then
  if old.actor<>auth.uid() or old.operation<>p_operation or old.target<>p_target or old.amount_input is distinct from p_amount or old.note_input is distinct from p_note then raise exception 'request_conflict'; end if;
  return old.result;
 end if;
 if p_operation='settle_cash' then
  if p_amount is not null or p_note is not null then raise exception 'bad_value'; end if;
  if not exists(select 1 from public.profiles where id=p_target and role='driver') then raise exception 'not_found'; end if;
  perform pg_advisory_xact_lock(hashtextextended('finance-driver:'||p_target::text,0));
  if exists(select 1 from public.orders where driver_id=p_target and payment='cash' and status='delivered' and cash_collected is not null and cash_settled_at is null and cash_allocation_version is null) then raise exception 'legacy_cash_reconciliation_required'; end if;
  -- One statement chooses/locks the exact set, updates it, and computes ONLY from RETURNING.
  with eligible as materialized (
   select id from public.orders where driver_id=p_target and status='delivered'
    and payment='cash' and cash_allocation_version=1 and cash_platform_share>0 and cash_collected is not null and cash_settled_at is null order by id for update
  ), moved as (
   update public.orders o set cash_settled_at=now() from eligible e where o.id=e.id
    returning o.id,o.cash_platform_share
  ) select coalesce(sum(cash_platform_share),0),coalesce(array_agg(id order by id),'{}'::bigint[]) into total,ids from moved;
  if cardinality(ids)=0 then raise exception 'nothing_to_settle'; end if;
 else
  if v_a=0 or abs(v_a)>100000 or length(v_note)<3 or length(v_note)>200 then raise exception 'bad_value'; end if;
  perform 1 from public.profiles where id=p_target and role='customer' for update;
  if not found then raise exception 'not_found'; end if;
  if v_a<0 and public.wallet_balance(p_target)+v_a<0 then raise exception 'insufficient_funds'; end if;
  insert into public.wallet_entries(user_id,amount,kind,note,created_by) values(p_target,v_a,'adjust',v_note,auth.uid()) returning id into entry_id;
  total:=v_a;ids:='{}'::bigint[];
 end if;
 reply:=jsonb_build_object('request',p_request,'operation',p_operation,'target',p_target,'amount',total,'orders',ids,'wallet_entry',entry_id,'actor',auth.uid(),'at',now());
 insert into finance_private.commands(request,actor,operation,target,amount_input,note_input,result) values(p_request,auth.uid(),p_operation,p_target,p_amount,p_note,reply);
 if p_operation='settle_cash' then
  insert into finance_private.settlement_receipts(request,driver,driver_name,actor,actor_name,amount,currency,at)
  values(p_request,p_target,coalesce((select name from profiles where id=p_target),p_target::text),auth.uid(),
   coalesce((select name from profiles where id=auth.uid()),auth.uid()::text),total,'TJS',now()) returning id into receipt_id;
  insert into finance_private.settlement_receipt_orders(order_id,receipt_id,amount)
   select id,receipt_id,cash_platform_share from public.orders where id=any(ids);
  reply:=reply||jsonb_build_object('receipt',finance_private.receipt_json(receipt_id));
  update finance_private.commands set result=reply where request=p_request;
 end if;
 return reply;
end $$;

create or replace function public.finance_driver_orders() returns setof jsonb
language sql stable security definer set search_path=pg_catalog,public as $$
 select jsonb_build_object('cash_allocation_version',o.cash_allocation_version,'cash_platform_share',o.cash_platform_share,'cash_driver_delivery_share',o.cash_driver_delivery_share,'cash_allocation_reference',o.cash_allocation_reference,'id',o.id,'store_id',o.store_id,'driver_id',o.driver_id,'status',o.status,'subtotal',o.subtotal,'discount',o.discount,'delivery_fee',o.delivery_fee,'tip',o.tip,'total',o.total,'commission',o.commission,'driver_payout',o.driver_payout,'payment',o.payment,'cash_collected',o.cash_collected,'cash_settled_at',o.cash_settled_at,'done_at',o.done_at,'created_at',o.created_at)
 from public.orders o where o.driver_id is not null and finance_private.reader() order by o.created_at desc limit 300
$$;
create or replace function public.finance_access() returns jsonb
language sql stable security definer set search_path=pg_catalog,public as $$
 select jsonb_build_object('execute',finance_private.accountant(),'version',4,
 'capabilities',jsonb_build_array('commands','settlement_events','settlement_receipts','cash_delivery_share_v1'))
$$;
-- Receipt lines retain the immutable platform amount recorded at settlement.
create or replace function finance_private.receipt_json(p_id bigint) returns jsonb
language sql stable security definer set search_path=pg_catalog,public as $$
 select jsonb_build_object('number','TS-'||lpad(r.id::text,greatest(12,length(r.id::text)),'0'),'request',r.request,
 'driver',r.driver,'driver_name',r.driver_name,'actor',r.actor,'actor_name',r.actor_name,
 'amount',r.amount,'currency',r.currency,'at',r.at,
 'basis',case when not exists(select 1 from finance_private.settlement_receipt_orders x join public.orders z on z.id=x.order_id where x.receipt_id=r.id and z.cash_allocation_version is distinct from 1) then 'platform_delivery_share_v1' else 'legacy' end,
 'orders',(select jsonb_agg(jsonb_build_object('id',o.order_id::text,'amount',o.amount) order by o.order_id) from finance_private.settlement_receipt_orders o where o.receipt_id=r.id))
 from finance_private.settlement_receipts r where r.id=p_id
$$;
commit;
