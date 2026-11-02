-- PROPOSAL R1: receipt only, AFTER exact reviewed A. Never applied live.
-- No old-row backfill, partial collection, offsetting, payouts or permission expansion.
begin;
create table finance_private.settlement_receipts (
 id bigint generated always as identity primary key,
 request uuid not null unique references finance_private.commands(request),
 driver uuid not null references public.profiles(id), driver_name text not null,
 actor uuid not null references public.profiles(id), actor_name text not null,
 amount numeric not null check(amount>=0), currency text not null check(currency='TJS'),
 at timestamptz not null
);
create table finance_private.settlement_receipt_orders (
 order_id bigint primary key references public.orders(id),
 receipt_id bigint not null references finance_private.settlement_receipts(id),
 amount numeric not null
);
alter table finance_private.settlement_receipts enable row level security;
alter table finance_private.settlement_receipt_orders enable row level security;
revoke all on finance_private.settlement_receipts,finance_private.settlement_receipt_orders from public,anon,authenticated;
revoke all on sequence finance_private.settlement_receipts_id_seq from public,anon,authenticated;
create function finance_private.receipt_immutable() returns trigger language plpgsql set search_path=pg_catalog as $$
begin raise exception 'receipt_immutable'; end $$;
create trigger receipt_immutable before update or delete on finance_private.settlement_receipts for each row execute function finance_private.receipt_immutable();
create trigger receipt_orders_immutable before update or delete on finance_private.settlement_receipt_orders for each row execute function finance_private.receipt_immutable();
create function finance_private.receipt_json(p_id bigint) returns jsonb
language sql stable security definer set search_path=pg_catalog,public as $$
 select jsonb_build_object('number','TS-'||lpad(r.id::text,greatest(12,length(r.id::text)),'0'),'request',r.request,
 'driver',r.driver,'driver_name',r.driver_name,'actor',r.actor,'actor_name',r.actor_name,
 'amount',r.amount,'currency',r.currency,'at',r.at,'orders',
 (select jsonb_agg(jsonb_build_object('id',o.order_id::text,'amount',o.amount) order by o.order_id)
 from finance_private.settlement_receipt_orders o where o.receipt_id=r.id))
 from finance_private.settlement_receipts r where r.id=p_id
$$;
create or replace function public.finance_access() returns jsonb
language sql stable security definer set search_path=pg_catalog,public as $$
 select jsonb_build_object('execute',finance_private.accountant(),'version',3,
 'capabilities',jsonb_build_array('commands','settlement_events','settlement_receipts'))
$$;
create function public.finance_settlement_receipts(p_order_ids text[])
returns table(order_id text,cash_settled_at timestamptz,receipt jsonb)
language sql stable security definer set search_path=pg_catalog,public as $$
 select o.order_id::text,r.at,finance_private.receipt_json(r.id)
 from finance_private.settlement_receipt_orders o join finance_private.settlement_receipts r on r.id=o.receipt_id
 join public.orders ord on ord.id=o.order_id and ord.cash_settled_at=r.at
 where o.order_id::text=any(p_order_ids[1:30])
 and (finance_private.reader() or (auth.uid() is not null and r.driver=auth.uid()))
$$;
revoke all on function finance_private.receipt_immutable(),finance_private.receipt_json(bigint) from public,anon,authenticated;
revoke all on function public.finance_settlement_receipts(text[]) from public,anon;
grant execute on function public.finance_settlement_receipts(text[]) to authenticated;
-- finance_execute is appended by the source-preserving builder below.
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
  -- One statement chooses/locks the exact set, updates it, and computes ONLY from RETURNING.
  with eligible as materialized (
   select id from public.orders where driver_id=p_target and status='delivered'
    and cash_collected is not null and cash_settled_at is null order by id for update
  ), moved as (
   update public.orders o set cash_settled_at=now() from eligible e where o.id=e.id
    returning o.id,o.cash_collected
  ) select coalesce(sum(cash_collected),0),coalesce(array_agg(id order by id),'{}'::bigint[]) into total,ids from moved;
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
   select id,receipt_id,cash_collected from public.orders where id=any(ids);
  reply:=reply||jsonb_build_object('receipt',finance_private.receipt_json(receipt_id));
  update finance_private.commands set result=reply where request=p_request;
 end if;
 return reply;
end $$;

commit;
