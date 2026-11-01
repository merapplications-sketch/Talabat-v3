-- PROPOSAL A. NOT APPLIED TO SUPABASE. Reviewed deployment required.
-- No has_perm change, no historical backfill, no frozen v60/v61/patch38 activation.
begin;
create schema if not exists finance_private;
revoke all on schema finance_private from public, anon, authenticated;
create table if not exists finance_private.commands (
 request uuid primary key, actor uuid not null, operation text not null,
 target uuid not null, amount_input numeric, note_input text, result jsonb not null,
 created_at timestamptz not null default now()
);
alter table finance_private.commands enable row level security;
revoke all on finance_private.commands from public, anon, authenticated;
create or replace function finance_private.accountant() returns boolean
language sql stable security definer set search_path=pg_catalog,public as $$
 select auth.uid() is not null and exists(select 1 from public.staff_members s
 where s.user_id=auth.uid() and s.active and 'finance'=any(s.perms))
$$;
create or replace function public.finance_access() returns jsonb
language sql stable security definer set search_path=pg_catalog,public as $$
 select jsonb_build_object('execute',finance_private.accountant(),'version',2,'capabilities',jsonb_build_array('commands','settlement_events'))
$$;
create or replace function public.finance_execute(p_request uuid,p_operation text,p_target uuid,p_amount numeric default null,p_note text default null)
returns jsonb language plpgsql security definer set search_path=pg_catalog,public as $$
declare old finance_private.commands; total numeric; ids bigint[]; entry_id bigint; v_note text:=btrim(coalesce(p_note,'')); v_a numeric:=round(coalesce(p_amount,0),2); reply jsonb;
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
 return reply;
end $$;
create or replace function public.finance_command_status(p_request uuid) returns jsonb
language sql stable security definer set search_path=pg_catalog,public as $$
 select result from finance_private.commands where request=p_request and actor=auth.uid() and finance_private.accountant()
$$;
-- Retire keyless financial mutation endpoints. Older clients fail safely, not silently mutate.
create or replace function public.settle_driver_cash(p_driver uuid) returns numeric
language plpgsql security definer set search_path=pg_catalog,public as $$
begin if not finance_private.accountant() then raise exception 'not_allowed'; end if; raise exception 'request_id_required'; end $$;
create or replace function public.wallet_adjust(p_user uuid,p_amount numeric,p_note text) returns void
language plpgsql security definer set search_path=pg_catalog,public as $$
begin if not finance_private.accountant() then raise exception 'not_allowed'; end if; raise exception 'request_id_required'; end $$;
-- No direct table path for clients. Operational SECURITY DEFINER deliver_order remains unchanged.
revoke insert, update, delete on public.wallet_entries from public, anon, authenticated;
revoke update on public.orders from public, anon, authenticated;
-- Table REVOKE alone leaves explicit column grants effective, including grants to PUBLIC.
do $acl$
declare col record;
begin
 for col in select attname from pg_attribute where attrelid='public.orders'::regclass and attnum>0 and not attisdropped loop
  execute format('revoke update (%I) on public.orders from public, anon, authenticated',col.attname);
 end loop;
 for col in select attname from pg_attribute where attrelid='public.wallet_entries'::regclass and attnum>0 and not attisdropped loop
  execute format('revoke insert (%I), update (%I) on public.wallet_entries from public, anon, authenticated',col.attname,col.attname);
 end loop;
end $acl$;

create or replace function finance_private.reader() returns boolean
language sql stable security definer set search_path=pg_catalog,public as $$ select public.is_admin() or finance_private.accountant() $$;
create or replace function public.finance_drivers() returns table(id uuid,name text,phone text,driver_status text,cash_limit numeric,accept_blocked boolean,last_seen timestamptz)
language sql stable security definer set search_path=pg_catalog,public as $$
 select p.id,p.name,p.phone,p.driver_status::text,p.cash_limit,p.accept_blocked,p.last_seen from public.profiles p where p.role='driver' and finance_private.reader()
$$;
create or replace function public.finance_driver_orders() returns setof jsonb
language sql stable security definer set search_path=pg_catalog,public as $$
 select jsonb_build_object('id',o.id,'store_id',o.store_id,'driver_id',o.driver_id,'status',o.status,'subtotal',o.subtotal,'discount',o.discount,'delivery_fee',o.delivery_fee,'tip',o.tip,'total',o.total,'commission',o.commission,'driver_payout',o.driver_payout,'payment',o.payment,'cash_collected',o.cash_collected,'cash_settled_at',o.cash_settled_at,'done_at',o.done_at,'created_at',o.created_at)
 from public.orders o where o.driver_id is not null and finance_private.reader() order by o.created_at desc limit 300
$$;
create or replace function public.finance_customers(p_q text default null,p_limit integer default 30,p_offset integer default 0)
returns table(id uuid,name text) language sql stable security definer set search_path=pg_catalog,public as $$
 select p.id,p.name from public.profiles p where p.role='customer' and finance_private.reader()
 and (p_q is null or p.name ilike '%'||left(p_q,60)||'%' or p.id::text=left(p_q,60)) order by p.id limit least(greatest(p_limit,1),30) offset greatest(p_offset,0)
$$;
create or replace function public.finance_audit(p_limit integer default 100) returns setof public.audit_log
language sql stable security definer set search_path=pg_catalog,public as $$
 select a.* from public.audit_log a where finance_private.reader() and
 (a.table_name='wallet_entries' or (a.table_name='orders' and a.details ? 'cash_settled_at')) order by a.at desc limit least(greatest(p_limit,1),200)
$$;
create or replace function public.finance_actor_names(p_ids uuid[]) returns table(id uuid,name text)
language sql stable security definer set search_path=pg_catalog,public as $$
 select p.id,p.name from public.profiles p where p.id=any(p_ids[1:200]) and
 (public.is_admin() or ((finance_private.accountant() or public.has_perm('support')) and
  (exists(select 1 from public.wallet_entries w where w.created_by=p.id)
   or exists(select 1 from public.audit_log a where a.user_id=p.id and a.table_name='orders' and a.details ? 'cash_settled_at'))))
$$;
-- Match the recorded settlement timestamp, not the latest global audit window.
-- Invalid historical metadata cannot abort every visible row or manufacture an actor.
create or replace function finance_private.settlement_time(p_value text) returns timestamptz
language plpgsql stable strict set search_path=pg_catalog as $$
begin return p_value::timestamptz;
exception when invalid_datetime_format or datetime_field_overflow then return null;
end $$;
create or replace function public.finance_settlement_events(p_order_ids text[])
returns table(id bigint,user_id uuid,at timestamptz,table_name text,row_id text,details jsonb)
language sql stable security definer set search_path=pg_catalog,public as $$
 select a.id,a.user_id,a.at,'orders'::text,a.row_id,
 jsonb_build_object('cash_settled_at',a.details->'cash_settled_at')
 from public.orders o cross join lateral (
  select l.id,l.user_id,l.at,l.row_id,l.details from public.audit_log l
  where l.table_name='orders' and l.row_id=o.id::text
   and finance_private.settlement_time(l.details->'cash_settled_at'->>'to')=o.cash_settled_at
  order by l.at desc,l.id desc limit 1
 ) a
 where finance_private.reader() and o.id::text=any(p_order_ids[1:30]) and o.cash_settled_at is not null
$$;
-- Functions are not PUBLIC APIs by default: explicit authenticated grants, auth checks inside.
revoke all on all functions in schema finance_private from public,anon,authenticated;
revoke all on function public.finance_settlement_events(text[]),public.finance_access(),public.finance_execute(uuid,text,uuid,numeric,text),public.finance_command_status(uuid),public.finance_drivers(),public.finance_driver_orders(),public.finance_customers(text,integer,integer),public.finance_audit(integer),public.finance_actor_names(uuid[]),public.settle_driver_cash(uuid),public.wallet_adjust(uuid,numeric,text) from public,anon;
grant execute on function public.finance_settlement_events(text[]),public.finance_access(),public.finance_execute(uuid,text,uuid,numeric,text),public.finance_command_status(uuid),public.finance_drivers(),public.finance_driver_orders(),public.finance_customers(text,integer,integer),public.finance_audit(integer),public.finance_actor_names(uuid[]),public.settle_driver_cash(uuid),public.wallet_adjust(uuid,numeric,text) to authenticated;
commit;
