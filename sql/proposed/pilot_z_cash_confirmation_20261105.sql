-- REVIEW CANDIDATE ONLY. Native isolated lab; NOT APPLIED LIVE.
-- Numeric policy values remain NULL/unapproved until explicitly configured.
begin;
create schema if not exists fulfillment_private;
revoke all on schema fulfillment_private from public,anon,authenticated;
create table if not exists fulfillment_private.confirmation_config(
 id boolean primary key default true check(id),enabled boolean not null default true,
 timeout_seconds integer check(timeout_seconds between 30 and 1800),timeout_approved boolean not null default false,
 material_delay_minutes integer check(material_delay_minutes between 1 and 90),delay_approved boolean not null default false,
 updated_by uuid,updated_at timestamptz not null default now(),
 check(not timeout_approved or timeout_seconds is not null),check(not delay_approved or material_delay_minutes is not null));
insert into fulfillment_private.confirmation_config(id)values(true)on conflict do nothing;
create table if not exists fulfillment_private.order_approvals(
 order_id bigint primary key references public.orders(id),customer_id uuid not null,
 state text not null check(state in('awaiting_merchant','awaiting_customer','checkout_accepted','accepted')),
 revision integer not null default 0,snapshot jsonb,accepted_revision integer,accepted_prep_minutes integer,
 first_cash boolean not null default false,creation_xid xid8 not null default pg_current_xact_id(),
 deadline timestamptz,merchant_actor uuid,merchant_at timestamptz,customer_actor uuid,customer_at timestamptz);
create index if not exists order_approvals_customer_idx on fulfillment_private.order_approvals(customer_id);
create table if not exists fulfillment_private.approval_requests(
 request uuid primary key,actor uuid not null,operation text not null,order_id bigint not null,
 payload jsonb not null,result jsonb not null,at timestamptz not null default now());
create table if not exists fulfillment_private.approval_events(
 id bigint generated always as identity primary key,order_id bigint not null,revision integer not null,
 kind text not null,actor uuid,at timestamptz not null default now(),snapshot jsonb,
 unique(order_id,revision,kind));
create table if not exists fulfillment_private.config_events(
 id bigint generated always as identity primary key,actor uuid not null,at timestamptz not null default now(),before_value jsonb,after_value jsonb);
alter table fulfillment_private.order_approvals enable row level security;
alter table fulfillment_private.approval_requests enable row level security;
alter table fulfillment_private.approval_events enable row level security;
alter table fulfillment_private.confirmation_config enable row level security;
alter table fulfillment_private.config_events enable row level security;
revoke all on all tables in schema fulfillment_private from public,anon,authenticated;

create or replace function fulfillment_private.snapshot(p_order bigint)returns jsonb
language sql stable security definer set search_path=public as $$
 select jsonb_build_object('order',o.id,'total',o.total,'subtotal',o.subtotal,'currency','TJS',
  'wallet_used',coalesce(o.wallet_used,0),'cash_due',greatest(0,o.total-coalesce(o.wallet_used,0)),
  'address',o.address,'lat',o.lat,'lng',o.lng,'prep_minutes',o.prep_time,
  'lines',coalesce((select jsonb_agg(jsonb_build_object('item_id',i.item_id,'name',i.name,'price',i.price,'qty',i.qty,'note',i.note,'options',i.options)order by i.id)from order_items i where i.order_id=o.id),'[]'::jsonb))
 from orders o where o.id=p_order $$;

create or replace function fulfillment_private.register_order(p_order bigint)returns void
language plpgsql security definer set search_path=public as $$
declare o orders;need_first boolean;cfg fulfillment_private.confirmation_config;
begin
 select * into o from orders where id=p_order;
 select * into cfg from fulfillment_private.confirmation_config where id;
 if not cfg.enabled then return;end if;
 -- place_order locks this customer's profile before inserting; request races cannot
 -- consume a second first-cash slot. Failed creation rolls back all wallet/points effects.
 need_first:=o.payment ~ '^(cash|Cash|Наличн)' and not exists(
  select 1 from fulfillment_private.order_approvals a where a.customer_id=o.customer_id and a.first_cash and a.customer_at is not null)
  and not exists(select 1 from orders old where old.customer_id=o.customer_id and old.id<>o.id and old.status='delivered'
   and old.payment ~ '^(cash|Cash|Наличн)' and not exists(select 1 from fulfillment_private.order_approvals a where a.order_id=old.id));
 if need_first and exists(select 1 from fulfillment_private.order_approvals a join orders x on x.id=a.order_id
  where a.customer_id=o.customer_id and a.first_cash and a.customer_at is null and x.status in('pending','preparing','ready','pickedup'))then
  raise exception 'first_cash_pending';end if;
 insert into fulfillment_private.order_approvals(order_id,customer_id,state,first_cash,snapshot,accepted_revision)
 values(o.id,o.customer_id,case when need_first then 'awaiting_merchant'else'checkout_accepted'end,need_first,
  fulfillment_private.snapshot(o.id),case when need_first then null else 0 end);
end $$;

create or replace function fulfillment_private.unblocked(p_order bigint)returns boolean
language sql stable security definer set search_path=public as $$
 select not exists(select 1 from fulfillment_private.order_approvals where order_id=p_order and state in('awaiting_merchant','awaiting_customer')) $$;

create or replace function fulfillment_private.guard_order()returns trigger
language plpgsql security definer set search_path=public as $$
declare a fulfillment_private.order_approvals;internal_write boolean;ox text;
begin
 select * into a from fulfillment_private.order_approvals where order_id=old.id;
 internal_write:=coalesce(current_setting('talabot.approval_write',true),'')=old.id::text or coalesce(current_setting('talabot.order_building',true),'')=old.id::text;
 select xmin::text into ox from orders where id=old.id;
 if not internal_write and (a.order_id is not null or ox<>pg_current_xact_id()::text)then
  if row(new.total,new.subtotal,new.wallet_used,new.points_used,new.points_value,new.address,new.lat,new.lng)
   is distinct from row(old.total,old.subtotal,old.wallet_used,old.points_used,old.points_value,old.address,old.lat,old.lng)then
   raise exception 'order_change_requires_confirmation';end if;
  if new.prep_time is distinct from old.prep_time and old.prep_time is not null
   and coalesce(a.state,'legacy')<>'awaiting_merchant' then raise exception 'order_change_requires_confirmation';end if;
 end if;
 if a.state in('awaiting_merchant','awaiting_customer') and
  ((new.status is distinct from old.status and new.status in('preparing','ready','pickedup','delivered'))
   or(new.driver_id is distinct from old.driver_id and new.driver_id is not null))then raise exception 'customer_confirmation_required';end if;
 return new;
end $$;
create or replace function fulfillment_private.guard_lines()returns trigger
language plpgsql security definer set search_path=public as $$
declare oid bigint;ox text;begin
 oid:=case when tg_op='DELETE'then old.order_id else new.order_id end;
 if coalesce(current_setting('talabot.approval_write',true),'')=oid::text or coalesce(current_setting('talabot.order_building',true),'')=oid::text then
  if tg_op='DELETE'then return old;else return new;end if;end if;
 select xmin::text into ox from orders where id=oid;
 if exists(select 1 from fulfillment_private.order_approvals where order_id=oid)or ox<>pg_current_xact_id()::text then
  raise exception 'order_change_requires_confirmation';end if;
 if tg_op='DELETE'then return old;else return new;end if;
end $$;
create or replace function fulfillment_private.guard_offer()returns trigger
language plpgsql security definer set search_path=public as $$begin
 if new.state='pending'and not fulfillment_private.unblocked(new.order_id)then raise exception 'customer_confirmation_required';end if;return new;end $$;
drop trigger if exists approval_order_guard on orders;
create trigger approval_order_guard before update on orders for each row execute function fulfillment_private.guard_order();
drop trigger if exists approval_lines_guard on order_items;
create trigger approval_lines_guard before insert or update or delete on order_items for each row execute function fulfillment_private.guard_lines();
drop trigger if exists approval_offer_guard on order_offers;
create trigger approval_offer_guard before insert or update on order_offers for each row execute function fulfillment_private.guard_offer();

create or replace function public.order_confirmation_settings()returns jsonb
language plpgsql stable security definer set search_path=public as $$begin
 if auth.uid()is null then raise exception'auth';end if;
 return(select to_jsonb(c)-'id'-'updated_by'||jsonb_build_object('version',1,'proposed_timeout_seconds',120,'proposed_material_delay_minutes',10)
 from fulfillment_private.confirmation_config c where id);end $$;
create or replace function public.configure_order_confirmation(p_timeout_seconds integer,p_material_delay_minutes integer,
 p_timeout_approved boolean default false,p_delay_approved boolean default false,p_enabled boolean default true)returns jsonb
language plpgsql security definer set search_path=public as $$
declare before_json jsonb;after_json jsonb;begin
 if not is_admin()then raise exception'not_allowed';end if;
 select to_jsonb(c)into before_json from fulfillment_private.confirmation_config c where id for update;
 update fulfillment_private.confirmation_config set timeout_seconds=p_timeout_seconds,material_delay_minutes=p_material_delay_minutes,
 timeout_approved=p_timeout_approved,delay_approved=p_delay_approved,enabled=p_enabled,updated_by=auth.uid(),updated_at=now()where id;
 select to_jsonb(c)into after_json from fulfillment_private.confirmation_config c where id;
 insert into fulfillment_private.config_events(actor,before_value,after_value)values(auth.uid(),before_json,after_json);
 return public.order_confirmation_settings();end $$;

create or replace function public.order_approval_states(p_order_ids bigint[])returns jsonb
language plpgsql stable security definer set search_path=public as $$begin
 if auth.uid()is null then raise exception'auth';end if;
 if cardinality(p_order_ids)>300 then raise exception'bad_value';end if;
 return coalesce((select jsonb_agg(jsonb_build_object('order_id',a.order_id,'state',a.state,'revision',a.revision,
 'snapshot',a.snapshot,'first_cash',a.first_cash,'deadline',a.deadline,'expired',a.deadline is not null and now()>a.deadline,
 'accepted_revision',a.accepted_revision,'merchant_at',a.merchant_at,'customer_at',a.customer_at))
 from fulfillment_private.order_approvals a where a.order_id=any(p_order_ids)and can_see_order(a.order_id)),'[]'::jsonb);end $$;

create or replace function fulfillment_private.quote_lines(p_order bigint,p_items jsonb)returns jsonb
language plpgsql stable security definer set search_path=public as $$
declare o orders;i record;m menu_items;pl jsonb;lines jsonb:='[]';sub numeric:=0;total_value numeric;
begin
 select * into o from orders where id=p_order;
 if o.driver_id is not null or o.status not in('pending','preparing','ready')then raise exception'change_requires_support';end if;
 -- A price proposal never invents refunds, reprices redeemed points, or changes a courier's agreed pay.
 if coalesce(o.wallet_used,0)>0 or coalesce(o.points_used,0)>0 or coalesce(o.discount,0)>0 or coalesce(o.promo_discount,0)>0
  or coalesce(o.fee_waived,0)>0 or exists(select 1 from stores where id=o.store_id and(coalesce(discount_pct,0)>0 or coalesce(free_delivery_min,0)>0))
  or happy_hour_pct(o.store_id)>0 then raise exception'change_requires_support';end if;
 if jsonb_typeof(p_items)<>'array'or jsonb_array_length(p_items)not between 1 and 60 then raise exception'bad_value';end if;
 for i in select (x->>'item_id')::uuid item_id,(x->>'qty')::int qty,coalesce(x->'options','[]'::jsonb)opts,left(coalesce(x->>'note',''),120)note from jsonb_array_elements(p_items)x loop
  if i.qty not between 1 and 50 then raise exception'bad_value';end if;
  select * into m from menu_items where id=i.item_id and store_id=o.store_id and available and approved;
  if not found then raise exception'unavailable';end if;
  if coalesce(m.discount_pct,0)>0 then raise exception'change_requires_support';end if;
  pl:=price_line(i.item_id,i.opts);sub:=sub+(pl->>'unit')::numeric*i.qty;
  lines:=lines||jsonb_build_array(jsonb_build_object('item_id',m.id,'name',m.name,'price',(pl->>'unit')::numeric,'qty',i.qty,'note',i.note,'options',pl->'snap'));
 end loop;
 total_value:=greatest(5,sub+coalesce(o.delivery_fee,0)+coalesce(o.tip,0));
 return jsonb_build_object('lines',lines,'subtotal',sub,'total',total_value,'cash_due',total_value,'apply_items',true);
end $$;
create or replace function public.order_change_quote(p_order bigint,p_items jsonb)returns jsonb
language plpgsql stable security definer set search_path=public as $$begin
 if not exists(select 1 from orders where id=p_order and(owns_store(store_id)or has_perm('orders')))then raise exception'not_allowed';end if;
 return fulfillment_private.quote_lines(p_order,p_items);end $$;

create or replace function public.merchant_review_order(p_order bigint,p_minutes integer,p_request uuid,p_items jsonb default null,p_note text default null)returns jsonb
language plpgsql security definer set search_path=public as $$
declare o orders;a fulfillment_private.order_approvals;cfg fulfillment_private.confirmation_config;r fulfillment_private.approval_requests;
 payload jsonb;snap jsonb;old_snap jsonb;quoted jsonb;needs_accept boolean;price_change boolean;time_change boolean;result_json jsonb;prev_write text;
begin
 if auth.uid()is null or p_request is null or p_minutes is null or p_minutes not between 5 and 90 then raise exception'bad_value';end if;
 payload:=jsonb_build_object('minutes',p_minutes,'items',p_items,'note',left(coalesce(p_note,''),200));
 perform pg_advisory_xact_lock(hashtextextended('approval:'||p_request::text,0));
 select * into r from fulfillment_private.approval_requests where request=p_request;
 if found then
  if r.actor<>auth.uid()or r.operation<>'merchant_review'or r.order_id<>p_order or r.payload<>payload then raise exception'request_conflict';end if;return r.result;end if;
 select * into o from orders where id=p_order for update;
 if not found or not(owns_store(o.store_id)or has_perm('orders'))then raise exception'not_allowed';end if;
 if o.status not in('pending','preparing','ready','pickedup')then raise exception'bad_transition';end if;
 if o.scheduled_for is not null and now()<o.scheduled_for-interval'60 minutes'then raise exception'too_early';end if;
 insert into fulfillment_private.order_approvals(order_id,customer_id,state,snapshot,accepted_revision,accepted_prep_minutes)
 values(o.id,o.customer_id,'checkout_accepted',fulfillment_private.snapshot(o.id),0,o.prep_time)on conflict do nothing;
 select * into a from fulfillment_private.order_approvals where order_id=p_order for update;
 select * into cfg from fulfillment_private.confirmation_config where id;
 old_snap:=fulfillment_private.snapshot(p_order);snap:=old_snap||jsonb_build_object('prep_minutes',p_minutes,'previous_total',o.total,'previous_prep_minutes',o.prep_time);
 if p_items is not null then quoted:=fulfillment_private.quote_lines(p_order,p_items);snap:=snap||quoted;end if;
 price_change:=p_items is not null and(snap->'lines'is distinct from old_snap->'lines'or snap->'total'is distinct from old_snap->'total');
 time_change:=a.accepted_prep_minutes is not null and p_minutes>a.accepted_prep_minutes and
  (not cfg.delay_approved or cfg.material_delay_minutes is null or p_minutes-a.accepted_prep_minutes>=cfg.material_delay_minutes);
 needs_accept:=a.state in('awaiting_merchant','awaiting_customer')or price_change or time_change;
 snap:=snap||jsonb_build_object('reason',case when a.state='awaiting_merchant'then'first_cash'when price_change then'items_or_price'when time_change and not cfg.delay_approved then'delay_policy_unapproved'when time_change then'material_delay'else'nonmaterial_time'end,
 'apply_items',price_change,'base_total',o.total,'base_subtotal',o.subtotal);
 update fulfillment_private.order_approvals set revision=revision+1,snapshot=snap,
 state=case when needs_accept then'awaiting_customer'else state end,
 deadline=case when needs_accept and cfg.timeout_approved then now()+make_interval(secs=>cfg.timeout_seconds)else null end,
 merchant_actor=auth.uid(),merchant_at=now(),accepted_prep_minutes=case when not needs_accept and accepted_prep_minutes is null then p_minutes else accepted_prep_minutes end
 where order_id=p_order returning *into a;
 if needs_accept then
  update order_offers set state='cancelled'where order_id=p_order and state='pending';
 else
  prev_write:=current_setting('talabot.approval_write',true);perform set_config('talabot.approval_write',p_order::text,true);
  update orders set prep_time=p_minutes where id=p_order;
  perform set_config('talabot.approval_write',coalesce(prev_write,''),true);
 end if;
 insert into fulfillment_private.approval_events(order_id,revision,kind,actor,snapshot)values(p_order,a.revision,'merchant_review',auth.uid(),snap);
 result_json:=jsonb_build_object('request',p_request,'order_id',p_order,'revision',a.revision,'state',a.state,'needs_customer',needs_accept);
 insert into fulfillment_private.approval_requests values(p_request,auth.uid(),'merchant_review',p_order,payload,result_json,now());return result_json;
end $$;

create or replace function public.customer_confirm_order(p_order bigint,p_revision integer,p_request uuid)returns jsonb
language plpgsql security definer set search_path=public as $$
declare o orders;a fulfillment_private.order_approvals;r fulfillment_private.approval_requests;payload jsonb;result_json jsonb;line jsonb;prev_write text;
begin
 if auth.uid()is null or p_request is null then raise exception'bad_value';end if;
 payload:=jsonb_build_object('revision',p_revision);
 perform pg_advisory_xact_lock(hashtextextended('approval:'||p_request::text,0));
 select *into r from fulfillment_private.approval_requests where request=p_request;
 if found then
  if r.actor<>auth.uid()or r.operation<>'customer_confirm'or r.order_id<>p_order or r.payload<>payload then raise exception'request_conflict';end if;return r.result;end if;
 select *into o from orders where id=p_order for update;
 if not found or o.customer_id<>auth.uid()then raise exception'not_allowed';end if;
 select *into a from fulfillment_private.order_approvals where order_id=p_order for update;
 if not found or a.revision is distinct from p_revision then raise exception'approval_changed';end if;
 if o.status not in('pending','preparing','ready','pickedup')then raise exception'bad_transition';end if;
 if a.state<>'awaiting_customer'then raise exception'approval_changed';end if;
 if a.deadline is not null and now()>a.deadline then raise exception'confirmation_expired';end if;
 if o.total is distinct from(a.snapshot->>'base_total')::numeric then raise exception'approval_changed';end if;
 if o.scheduled_for is not null and now()<o.scheduled_for-interval'60 minutes'then raise exception'too_early';end if;
 prev_write:=current_setting('talabot.approval_write',true);perform set_config('talabot.approval_write',p_order::text,true);
 if coalesce((a.snapshot->>'apply_items')::boolean,false)then
  if o.driver_id is not null or coalesce(o.wallet_used,0)>0 or coalesce(o.points_used,0)>0 then raise exception'change_requires_support';end if;
  delete from order_items where order_id=p_order;
  for line in select value from jsonb_array_elements(a.snapshot->'lines')loop
   insert into order_items(order_id,item_id,name,price,qty,note,options)values(p_order,(line->>'item_id')::uuid,line->>'name',(line->>'price')::numeric,(line->>'qty')::int,line->>'note',line->'options');
  end loop;
  update orders set subtotal=(a.snapshot->>'subtotal')::numeric,total=(a.snapshot->>'total')::numeric,
   commission=round((a.snapshot->>'subtotal')::numeric*coalesce(o.commission_pct,0)/100,2)where id=p_order;
 end if;
 update fulfillment_private.order_approvals set state='accepted',accepted_revision=revision,accepted_prep_minutes=(snapshot->>'prep_minutes')::int,
 customer_actor=auth.uid(),customer_at=now()where order_id=p_order;
 update orders set prep_time=(a.snapshot->>'prep_minutes')::int,status=case when status='pending'then'preparing'::order_status else status end where id=p_order;
 perform set_config('talabot.approval_write',coalesce(prev_write,''),true);
 insert into fulfillment_private.approval_events(order_id,revision,kind,actor,snapshot)values(p_order,a.revision,'customer_confirm',auth.uid(),a.snapshot);
 result_json:=jsonb_build_object('request',p_request,'order_id',p_order,'revision',a.revision,'state','accepted');
 insert into fulfillment_private.approval_requests values(p_request,auth.uid(),'customer_confirm',p_order,payload,result_json,now());return result_json;
end $$;

revoke all on all functions in schema fulfillment_private from public,anon,authenticated;
revoke all on function public.order_confirmation_settings()from public,anon;
revoke all on function public.configure_order_confirmation(integer,integer,boolean,boolean,boolean)from public,anon;
revoke all on function public.order_approval_states(bigint[])from public,anon;
revoke all on function public.order_change_quote(bigint,jsonb)from public,anon;
revoke all on function public.merchant_review_order(bigint,integer,uuid,jsonb,text)from public,anon;
revoke all on function public.customer_confirm_order(bigint,integer,uuid)from public,anon;
grant execute on function public.order_confirmation_settings(),public.configure_order_confirmation(integer,integer,boolean,boolean,boolean),
 public.order_approval_states(bigint[]),public.order_change_quote(bigint,jsonb),public.merchant_review_order(bigint,integer,uuid,jsonb,text),public.customer_confirm_order(bigint,integer,uuid)to authenticated;

-- Preserve the exact priced checkout body; only customer lock and registration are added.
CREATE OR REPLACE FUNCTION public.place_order(p_store uuid, p_items jsonb, p_tip numeric DEFAULT 0, p_payment text DEFAULT 'cash'::text, p_address text DEFAULT ''::text, p_lat double precision DEFAULT NULL::double precision, p_lng double precision DEFAULT NULL::double precision, p_promo text DEFAULT NULL::text, p_key text DEFAULT NULL::text, p_fee numeric DEFAULT NULL::numeric, p_wallet numeric DEFAULT NULL::numeric, p_points integer DEFAULT NULL::integer, p_extra jsonb DEFAULT NULL::jsonb)
 RETURNS bigint
 LANGUAGE plpgsql
 SECURITY DEFINER
 SET search_path TO 'public'
AS $function$
declare v_build_prev text; s stores; pr profiles; it record; v_item menu_items; pl jsonb; v_id bigint; v_sub numeric; v_fee numeric; v_pay numeric; v_disc numeric; v_base numeric; v_gate numeric;
        v_promo numeric := 0; v_tip numeric; v_km float8; v_code text := null; v_dq jsonb; v_cphone text; v_total numeric; v_bal numeric; v_w numeric;
        v_hh int := 0; v_all numeric; v_hdisc numeric := 0; v_rate numeric; v_min numeric; v_lb int; v_pts int := 0; v_pval numeric := 0; v_cap numeric;
        v_step numeric; v_mo numeric; v_subst text; v_door boolean; v_gn text; v_gp text;
        v_at timestamptz; v_waived numeric := 0; v_gid uuid; g group_orders;
begin
  if p_wallet is not null and p_wallet < 0 then raise exception 'bad_value'; end if;
  if p_points is not null and (p_points < 0 or p_points > 100000000) then raise exception 'bad_value'; end if;
  -- order options (v50): leave at the door, what to do if a dish is missing, a gift for someone else
  v_door := coalesce((p_extra->>'door')::boolean, false);
  v_subst := coalesce(p_extra->>'subst', 'call');
  if v_subst not in ('call', 'replace', 'remove') then raise exception 'bad_value'; end if;
  -- scheduled delivery time (v51): from 45 minutes (with a little slack for the screen) to 3 days ahead
  if nullif(p_extra->>'at', '') is not null then
    begin v_at := (p_extra->>'at')::timestamptz; exception when others then raise exception 'bad_time'; end;
    if v_at < now() + interval '40 minutes' or v_at > now() + interval '3 days' then raise exception 'bad_time'; end if;
  end if;
  -- office / group order (v51): only its host can place it, once
  if nullif(p_extra->>'group', '') is not null then
    begin v_gid := (p_extra->>'group')::uuid; exception when others then raise exception 'bad_group'; end;
    select * into g from group_orders where id = v_gid for update;
    if not found or g.host_id <> auth.uid() or g.status not in ('open', 'closed') or g.store_id <> p_store then raise exception 'bad_group'; end if;
  end if;
  if p_extra ? 'gift' and jsonb_typeof(p_extra->'gift') = 'object' then
    v_gn := btrim(coalesce(p_extra->'gift'->>'name', '')); v_gp := norm_phone(p_extra->'gift'->>'phone');
    if char_length(v_gn) not between 2 and 60 or v_gp is null then raise exception 'bad_gift'; end if;
  end if;   -- a negative amount would mean ADDING money: refuse it
  if auth.uid() is null then raise exception 'auth'; end if;
  -- idempotency: a retry of the SAME attempt (bad network, double tap) returns the order that already exists
  if p_key is not null then
    if p_key !~ '^[A-Za-z0-9_-]{8,64}$' then raise exception 'bad_value'; end if;
    select o.id into v_id from orders o where o.customer_id = auth.uid() and o.client_key = p_key;
    if found then return v_id; end if;
  end if;
  -- No external processor is configured. Only cash may be asserted by a caller;
  -- existing wallet debit logic below alone may mark a fully funded order wallet.
  -- Preserve existing-key recovery above; never rewrite historical payments.
  if p_payment is distinct from 'cash' then raise exception 'payment_not_configured'; end if;
  -- abuse guard: at most 20 orders per hour per customer
  if (select count(*) from orders where customer_id = auth.uid() and created_at > now() - interval '1 hour') >= 20 then
    raise exception 'too_many_orders';
  end if;
  -- spam / abuse guard: at most 5 unfinished orders per customer
  if (select count(*) from orders where customer_id = auth.uid() and status in ('pending', 'preparing', 'ready', 'pickedup')) >= 5 then
    raise exception 'too_many_orders';
  end if;
  if (p_lat is not null and (p_lat < -90 or p_lat > 90)) or (p_lng is not null and (p_lng < -180 or p_lng > 180)) then
    raise exception 'bad_value';
  end if;
  -- a delivery address (text + map point) is mandatory
  if p_lat is null or p_lng is null or char_length(btrim(coalesce(p_address, ''))) < 3 then
    raise exception 'address_required';
  end if;
  select * into s from stores where id = p_store and is_active;
  if not found then raise exception 'store_unavailable'; end if;
  if not s.is_open then raise exception 'closed'; end if;
  v_hh := happy_hour_pct(p_store);                                -- admin-scheduled happy hour (paid by the platform)
  if jsonb_typeof(p_items) <> 'array' or jsonb_array_length(p_items) = 0 then raise exception 'empty'; end if;
  if jsonb_array_length(p_items) > 60 then raise exception 'bad_value'; end if;
  select * into pr from profiles where id = auth.uid() for update;

  -- the customer phone is required (stored privately, see order_customer_phone) and the fee is calculated here, never by the app
  if pr.banned_at is not null then raise exception 'account_blocked'; end if;   -- a suspended account cannot order
  v_cphone := norm_phone(pr.phone);
  if v_cphone is null then raise exception 'phone_required'; end if;
  v_dq := delivery_calc(p_store, p_lat, p_lng, auth.uid());
  v_fee := (v_dq->>'fee')::numeric;
  v_pay := case s.fee_type when 'free' then s.fee_base else (v_dq->>'fee_full')::numeric end;   -- courier is always paid; the platform covers free delivery
  v_tip := case when p_tip in (0,3,5,10) then p_tip else 0 end;

  begin
    insert into orders(store_id, customer_id, customer_name, payment, address, lat, lng, client_key, leave_at_door, substitution, is_gift, scheduled_for, group_id)
    values (p_store, auth.uid(), pr.name, left(p_payment,40), left(p_address,200), p_lat, p_lng, p_key, v_door, v_subst, v_gn is not null, v_at, v_gid)
    returning id into v_id;
  exception when unique_violation then
    -- two taps raced: the other attempt won, return its order
    select o.id into v_id from orders o where o.customer_id = auth.uid() and o.client_key = p_key;
    return v_id;
  end;
  v_build_prev:=current_setting('talabot.order_building',true);
  perform set_config('talabot.order_building',v_id::text,true);
  insert into order_customer_phone(order_id, phone) values (v_id, v_cphone);
  if v_gn is not null then insert into order_recipient(order_id, name, phone) values (v_id, v_gn, v_gp); end if;

  -- every line is priced by the DATABASE: base price + the chosen options (validated against the item's own option groups)
  for it in select (x->>'item_id')::uuid as item_id,
                   least(50, greatest(1, (x->>'qty')::int)) as qty,
                   left(coalesce(x->>'note', ''), 120) as note,
                   case when jsonb_typeof(x->'options') = 'array' then x->'options' else '[]'::jsonb end as opts
              from jsonb_array_elements(p_items) x loop
    select * into v_item from menu_items where id = it.item_id and store_id = p_store and available and approved;
    if not found then raise exception 'unavailable'; end if;
    pl := price_line(it.item_id, it.opts);
    insert into order_items(order_id, item_id, name, price, qty, note, options)
    values (v_id, v_item.id, v_item.name, (pl->>'unit')::numeric, it.qty, it.note, pl->'snap');
  end loop;

  -- each line gets the better of the store discount and its own item discount (they do not stack; paid by the restaurant).
  -- A happy hour can only make it better. Owner decision (v48): the RESTAURANT pays it too, like its own offers: it is part of
  -- orders.discount (so revenue and commission are on what the customer pays); orders.hh_discount says how much of it came from the happy hour.
  select sum(oi.price * oi.qty),
         coalesce(sum(round(oi.price * oi.qty * greatest(s.discount_pct, coalesce(m.discount_pct, 0)) / 100, 2)), 0),
         coalesce(sum(round(oi.price * oi.qty * greatest(s.discount_pct, coalesce(m.discount_pct, 0), v_hh) / 100, 2)), 0),
         coalesce(sum(oi.price * oi.qty) filter (where greatest(s.discount_pct, coalesce(m.discount_pct, 0), v_hh) = 0), 0)
    into v_sub, v_disc, v_all, v_base
    from order_items oi left join menu_items m on m.id = oi.item_id
   where oi.order_id = v_id;
  v_hdisc := v_all - v_disc;
  -- free delivery above the restaurant's own threshold (v51): the restaurant pays the waived fee (orders.fee_waived)
  if coalesce(s.free_delivery_min, 0) > 0 and v_sub - v_disc - v_hdisc >= s.free_delivery_min and v_fee > 0 then
    v_waived := v_fee; v_fee := 0;
  end if;
  if p_fee is not null and abs(p_fee - v_fee) > 0.009 then raise exception 'fee_changed'; end if;   -- the price shown to the customer must be the price charged

  if p_promo is not null and length(trim(p_promo)) > 0 then
    if v_base <= 0 then raise exception 'promo_offer'; end if;     -- promo codes never apply to lines that already have an offer
    if not exists (select 1 from promo_attempts where user_id = auth.uid() and ok and code = upper(trim(p_promo))
                    and at > now() - interval '2 hours') then
      raise exception 'promo_invalid';                             -- must be validated (rate-limited) in check_promo first
    end if;
    v_gate := v_sub - v_disc - v_hdisc;                                       -- the minimum order is checked on what the customer pays for items
    v_promo := promo_eval(p_promo, v_base, auth.uid(), true, v_gate);
    if v_promo > 0 then v_code := upper(trim(p_promo)); end if;
  end if;

  update orders set subtotal = v_sub, discount = v_disc + v_hdisc, delivery_fee = v_fee, fee_waived = v_waived, tip = v_tip,
    delivery_base = (v_dq->>'base')::numeric, delivery_extra = (v_dq->>'extra')::numeric, delivery_km = (v_dq->>'km')::numeric,
    promo_code = v_code, promo_discount = v_promo, hh_discount = v_hdisc, hh_pct = v_hh,
    total = greatest(5, v_sub - v_disc - v_hdisc - v_promo + v_fee + v_tip),
    commission_pct = s.commission_pct, commission = round((v_sub - v_disc - v_hdisc) * s.commission_pct / 100, 2),
    driver_payout = v_pay + v_tip
  where id = v_id;

  -- POINTS: the customer may pay part of the items with loyalty points (all he can use, decided here, never by the app)
  if coalesce(p_points, 0) > 0 then
    v_rate := loyalty_setting('loyalty_points_per_tjs'); v_min := loyalty_setting('loyalty_min_redeem');
    v_step := greatest(1, loyalty_setting('loyalty_voucher_points'));
    v_mo := coalesce(s.points_min_order, loyalty_setting('loyalty_min_order'));
    perform 1 from profiles where id = auth.uid() for update;          -- two orders at the same moment cannot spend the same points
    v_lb := loyalty_balance(auth.uid());
    if v_lb < v_min then raise exception 'points_min'; end if;
    v_cap := v_sub - v_disc - v_hdisc - v_promo;                       -- points never pay for delivery or the tip
    if v_cap < v_mo then raise exception 'points_min_order'; end if;  -- the order (dishes) must reach the minimum to use points
    v_pts := (floor(least(v_lb, floor(greatest(v_cap, 0) * v_rate)) / v_step) * v_step)::int;   -- whole vouchers only (1000, 2000 ...)
    if v_pts <= 0 or v_pts <> p_points then raise exception 'points_changed'; end if;   -- the customer saw another amount: ask again
    v_pval := round(v_pts / v_rate, 2);
    perform loyalty_spend(auth.uid(), v_pts, v_id);
    update orders set points_used = v_pts, points_value = v_pval,
      total = greatest(5, v_sub - v_disc - v_hdisc - v_promo - v_pval + v_fee + v_tip) where id = v_id;
  end if;

  -- WALLET: the customer may pay all or part of the order from his refund balance (the server decides the amount, never the app)
  if coalesce(p_wallet, 0) > 0 then
    select total into v_total from orders where id = v_id;
    perform 1 from profiles where id = auth.uid() for update;           -- two orders at the same moment cannot spend the same money
    v_bal := wallet_balance();
    v_w := round(least(p_wallet, v_bal, v_total), 2);
    if v_w <= 0 or abs(v_w - round(p_wallet, 2)) > 0.009 then raise exception 'wallet_changed'; end if;   -- the customer saw another amount: ask again
    insert into wallet_entries(user_id, amount, kind, order_id) values (auth.uid(), -v_w, 'spend', v_id);
    update orders set wallet_used = v_w, payment = case when v_w >= v_total then 'wallet' else payment end where id = v_id;
  end if;
  if v_gid is not null then update group_orders set status = 'placed', order_id = v_id, closed_at = coalesce(closed_at, now()) where id = v_gid; end if;
  perform set_config('talabot.order_building',coalesce(v_build_prev,''),true);
  perform fulfillment_private.register_order(v_id);
  return v_id;
end $function$
;


CREATE OR REPLACE FUNCTION public.eligible_couriers(p_order bigint, p_reoffer boolean DEFAULT false)
 RETURNS TABLE(id uuid, dist double precision, fresh boolean)
 LANGUAGE sql
 STABLE SECURITY DEFINER
 SET search_path TO 'public'
AS $function$
  select p.id,
         case when st.lat is not null and p.lat is not null and p.loc_updated > now() - interval '3 minutes'
              then dist_km(st.lat, st.lng, p.lat, p.lng) end,
         coalesce(p.loc_updated > now() - interval '3 minutes', false)
    from orders o
    join stores st on st.id = o.store_id
    join profiles p on p.role = 'driver' and p.driver_status = 'approved' and not p.accept_blocked and p.online
                   and p.last_seen > now() - interval '2 minutes'
   where o.id = p_order and fulfillment_private.unblocked(p_order)
     and not exists (select 1 from orders b where b.driver_id = p.id and b.status in ('preparing', 'ready', 'pickedup'))
     and not exists (select 1 from order_offers f
                      where f.order_id = p_order and f.driver_id = p.id
                        and not (p_reoffer and f.state = 'expired'))
$function$
;

commit;
