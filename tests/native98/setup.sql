
create schema auth;create schema security_private;create schema finance_private;create schema fulfillment_private;create role authenticated;create role anon;
create table profiles(id uuid primary key,name text,phone text,banned_at timestamptz,role text);
create table staff_members(user_id uuid,active boolean,perms text[]);
create table security_private.revoked_sessions(user_id uuid,session_id uuid);create table security_private.mfa_required_users(user_id uuid);
create table stores(id uuid primary key,is_active boolean,is_open boolean,fee_type text,fee_base numeric,discount_pct numeric,free_delivery_min numeric,commission_pct numeric,points_min_order numeric);
create table menu_items(id uuid primary key,store_id uuid,name text,price numeric,available boolean,approved boolean,discount_pct numeric);
create table item_option_groups(id uuid,item_id uuid,name text,max_sel int,required boolean,sort int,created_at timestamptz);create table item_options(id uuid,group_id uuid,name text,price_delta numeric,available boolean,sort int);
create table group_orders(id uuid primary key,host_id uuid,status text,store_id uuid,expires_at timestamptz,order_id bigint,closed_at timestamptz);
create table orders(id bigserial primary key,store_id uuid references stores,customer_id uuid references profiles,customer_name text,payment text,address text,lat float8,lng float8,client_key text,leave_at_door boolean,substitution text,is_gift boolean,scheduled_for timestamptz,group_id uuid,status text default 'pending',created_at timestamptz default now(),subtotal numeric,discount numeric,delivery_fee numeric,fee_waived numeric,tip numeric,delivery_base numeric,delivery_extra numeric,delivery_km numeric,promo_code text,promo_discount numeric,hh_discount numeric,hh_pct int,total numeric,commission_pct numeric,commission numeric,driver_payout numeric,points_used int,points_value numeric,wallet_used numeric);
create table order_items(id bigserial primary key,order_id bigint references orders,item_id uuid,name text,price numeric,qty int check(qty between 1 and 50),note text,options jsonb);
create table wallet_entries(id bigserial primary key,user_id uuid,amount numeric check(amount<>0),kind text,order_id bigint references orders);
create table order_customer_phone(order_id bigint references orders,phone text);create table order_recipient(order_id bigint references orders,name text,phone text);
create table promo_attempts(user_id uuid,ok boolean,code text,at timestamptz);
create table synthetic_effect92(kind text,order_id bigint references orders);
CREATE OR REPLACE FUNCTION auth.jwt()
 RETURNS jsonb
 LANGUAGE sql
 STABLE
AS $function$
  select 
    coalesce(
        nullif(current_setting('request.jwt.claim', true), ''),
        nullif(current_setting('request.jwt.claims', true), '')
    )::jsonb
$function$;
CREATE OR REPLACE FUNCTION auth.uid()
 RETURNS uuid
 LANGUAGE sql
 STABLE
AS $function$
  select 
  coalesce(
    nullif(current_setting('request.jwt.claim.sub', true), ''),
    (nullif(current_setting('request.jwt.claims', true), '')::jsonb ->> 'sub')
  )::uuid
$function$;

CREATE OR REPLACE FUNCTION public.account_enabled()
 RETURNS boolean
 LANGUAGE sql
 STABLE SECURITY DEFINER
 SET search_path TO ''
AS $function$
 SELECT EXISTS(SELECT 1 FROM public.profiles p WHERE p.id=auth.uid() AND p.banned_at IS NULL)
 AND NOT EXISTS(SELECT 1 FROM security_private.revoked_sessions r
 WHERE r.user_id=auth.uid() AND r.session_id::text=auth.jwt()->>'session_id')
 AND (NOT EXISTS(SELECT 1 FROM security_private.mfa_required_users m WHERE m.user_id=auth.uid()) OR coalesce(auth.jwt()->>'aal','')='aal2')
$function$
;
CREATE OR REPLACE FUNCTION public.has_perm(p text)
 RETURNS boolean
 LANGUAGE sql
 STABLE SECURITY DEFINER
 SET search_path TO 'public'
AS $function$ SELECT public.account_enabled() AND EXISTS(SELECT 1 FROM public.profiles u WHERE u.id=auth.uid() AND u.banned_at IS NULL AND (u.role='admin' OR EXISTS(SELECT 1 FROM public.staff_members s WHERE s.user_id=u.id AND s.active AND p=ANY(s.perms)))) $function$
;
CREATE OR REPLACE FUNCTION public.norm_phone(p text)
 RETURNS text
 LANGUAGE sql
 IMMUTABLE
AS $function$
  select case
    when d ~ '^992[0-9]{9}$' then '+' || d
    when d ~ '^[0-9]{9}$' then '+992' || d
    when d ~ '^0[0-9]{9}$' then '+992' || substr(d, 2)
    else null end
  from (select regexp_replace(coalesce(p, ''), '[^0-9]', '', 'g') as d) x
$function$
;
CREATE OR REPLACE FUNCTION public.price_line(p_item uuid, p_opts jsonb)
 RETURNS jsonb
 LANGUAGE plpgsql
 STABLE SECURITY DEFINER
 SET search_path TO 'public'
AS $function$
declare v_item menu_items; ids uuid[]; g record; o record; n int; total numeric := 0; snap jsonb := '[]'::jsonb;
begin
  select * into v_item from menu_items where id = p_item;
  if not found then raise exception 'unavailable'; end if;
  begin
    ids := array(select distinct t.x::uuid from jsonb_array_elements_text(coalesce(p_opts, '[]'::jsonb)) as t(x));
  exception when others then raise exception 'bad_options';
  end;
  if cardinality(ids) > 40 then raise exception 'bad_options'; end if;
  if exists (select 1 from unnest(ids) u(id)
              where not exists (select 1 from item_options op join item_option_groups gr on gr.id = op.group_id
                                 where op.id = u.id and gr.item_id = p_item and op.available)) then
    raise exception 'bad_options';
  end if;
  for g in select * from item_option_groups where item_id = p_item loop
    select count(*) into n from item_options op where op.group_id = g.id and op.id = any(ids);
    if n > g.max_sel or (g.required and n < 1) then raise exception 'bad_options'; end if;
  end loop;
  for o in select op.id, op.name, op.price_delta, gr.name as gname
             from item_options op join item_option_groups gr on gr.id = op.group_id
            where gr.item_id = p_item and op.id = any(ids) order by gr.sort, gr.created_at, op.sort, op.name loop
    total := total + o.price_delta;
    snap := snap || jsonb_build_array(jsonb_build_object('id', o.id, 'g', o.gname, 'n', o.name, 'p', o.price_delta));
  end loop;
  return jsonb_build_object('unit', v_item.price + total, 'snap', snap);
end $function$
;
CREATE OR REPLACE FUNCTION public.wallet_balance(p_user uuid DEFAULT NULL::uuid)
 RETURNS numeric
 LANGUAGE sql
 STABLE SECURITY DEFINER
 SET search_path TO 'public'
AS $function$
  select coalesce(sum(w.amount), 0)::numeric
    from wallet_entries w
   where public.account_enabled() and w.user_id = coalesce(p_user, auth.uid())
     and (coalesce(p_user, auth.uid()) = auth.uid() or (has_perm('support') or has_perm('finance')))
$function$
;
CREATE UNIQUE INDEX orders_client_key_uq ON public.orders USING btree (customer_id, client_key) WHERE (client_key IS NOT NULL);
CREATE UNIQUE INDEX wallet_one_spend_per_order ON public.wallet_entries USING btree (order_id) WHERE (kind = 'spend'::text);
-- Explicit dependency doubles, not provider function coverage. No hosted guards changed.
create function happy_hour_pct(uuid) returns int language sql as $$select 0$$;
create function delivery_calc(uuid,float8,float8,uuid) returns jsonb language sql as $$select '{"fee":2,"fee_full":2,"base":2,"extra":0,"km":1}'::jsonb$$;
alter table orders add column prep_time integer;
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
 insert into fulfillment_private.order_approvals(order_id,customer_id,state,first_cash,snapshot,accepted_revision,accepted_prep_minutes)
 values(o.id,o.customer_id,case when need_first then 'awaiting_merchant'else'checkout_accepted'end,need_first,
  fulfillment_private.snapshot(o.id),case when need_first then null else 0 end,case when need_first then null else o.prep_time end);
end $$;


create function synthetic_fail_approval94() returns trigger language plpgsql as $$begin if current_setting('test92.fail_end',true)='yes' then raise exception 'synthetic_final_failure';end if;return new;end$$;
create trigger synthetic_end_failure before insert on fulfillment_private.order_approvals for each row execute function synthetic_fail_approval94();
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
  if auth.uid() is not null and public.account_enabled() is not true then raise exception 'account_blocked'; end if;
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
    if not found or g.host_id <> auth.uid() or g.status not in ('open', 'closed') or g.store_id <> p_store or g.expires_at <= now() then raise exception 'bad_group'; end if;
  end if;
  if p_extra ? 'gift' and jsonb_typeof(p_extra->'gift') = 'object' then
    v_gn := btrim(coalesce(p_extra->'gift'->>'name', '')); v_gp := norm_phone(p_extra->'gift'->>'phone');
    if char_length(v_gn) not between 2 and 60 or v_gp is null then raise exception 'bad_gift'; end if;
  end if;   -- a negative amount would mean ADDING money: refuse it
  if auth.uid() is null then raise exception 'auth'; end if;
  -- idempotency: a retry of the SAME attempt (bad network, double tap) returns the order that already exists
  if p_key is not null then
    if p_key !~ '^[A-Za-z0-9_-]{8,64}$' then raise exception 'bad_value'; end if;
    -- Serialize one caller/request key before lookup and admission checks.
    perform pg_catalog.pg_advisory_xact_lock(pg_catalog.hashtextextended(auth.uid()::text || ':' || p_key, 0));
    select o.id into v_id from orders o where o.customer_id = auth.uid() and o.client_key = p_key;
    if found then return v_id; end if;
  end if;
  -- No external processor is configured. Only cash may be asserted by a caller;
  -- existing wallet debit logic below alone may mark a fully funded order wallet.
  -- Preserve existing-key recovery above; never rewrite historical payments.
  if p_payment is distinct from 'cash' then raise exception 'payment_not_configured'; end if;
  -- S98: serialize admission for all keys of this account, not just identical keys.
  select * into pr from profiles where id = auth.uid() for update;
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
    if found then return v_id; end if;
    -- An unrelated unique constraint failure is not an idempotent replay.
    raise;
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
  perform finance_private.snapshot_cash(v_id);
  perform set_config('talabot.order_building',coalesce(v_build_prev,''),true);
  perform fulfillment_private.register_order(v_id);
  return v_id;
end $function$
;
;
insert into profiles values('10000000-0000-4000-8000-000000000092','Buyer92','+992900000092',null,'customer'),('20000000-0000-4000-8000-000000000092','Other92','+992900000093',null,'customer');
insert into stores values('30000000-0000-4000-8000-000000000092',true,true,'fixed',2,0,0,10,null);
insert into finance_private.cash_delivery_policy values('30000000-0000-4000-8000-000000000092',0.50,'synthetic allocation only');
insert into menu_items values('40000000-0000-4000-8000-000000000092','30000000-0000-4000-8000-000000000092','Synthetic dish',20,true,true,0);
insert into wallet_entries(user_id,amount,kind)values('10000000-0000-4000-8000-000000000092',100,'adjust'),('20000000-0000-4000-8000-000000000092',100,'adjust');
grant usage on schema public,auth to authenticated;grant execute on function place_order(uuid,jsonb,numeric,text,text,float8,float8,text,text,numeric,numeric,int,jsonb) to authenticated;
