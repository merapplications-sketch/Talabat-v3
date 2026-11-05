-- Isolated candidate. Apply after order consent and pilot admission.
begin;
create schema return_private;
revoke all on schema return_private from public, anon, authenticated;

create table return_private.agreements (
  id uuid primary key,
  store_id uuid not null references public.stores(id),
  active boolean not null,
  evidence text not null,
  recorded_by uuid not null,
  recorded_at timestamptz not null default clock_timestamp()
);
create index return_agreements_store_time on return_private.agreements(store_id, recorded_at desc);
create table return_private.cases (
  order_id bigint primary key references public.orders(id),
  store_id uuid not null references public.stores(id),
  agreement_id uuid not null references return_private.agreements(id),
  driver_id uuid not null,
  customer_id uuid not null,
  paid numeric(12,2) not null check (paid > 0),
  payment_ref text not null,
  currency text not null default 'TJS' check (currency = 'TJS'),
  departed_at timestamptz not null default clock_timestamp(),
  cancelled_at timestamptz,
  received_at timestamptz,
  received_by uuid,
  receipt_ref text,
  refused_at timestamptz,
  refused_by uuid,
  refusal_ref text,
  unique (store_id, payment_ref),
  unique (store_id, receipt_ref)
);
create table return_private.refunds (
  order_id bigint not null references return_private.cases(order_id),
  store_id uuid not null references public.stores(id),
  source_ref text not null,
  amount numeric(12,2) not null check (amount > 0),
  method text not null check (method in ('cash', 'transfer')),
  reported_by uuid not null,
  reported_at timestamptz not null default clock_timestamp(),
  state text not null default 'pending' check (state in ('pending', 'confirmed', 'disputed')),
  checked_by uuid,
  checked_at timestamptz,
  primary key (store_id, source_ref)
);
create index return_refunds_order on return_private.refunds(order_id);
create unique index return_one_pending_refund on return_private.refunds(order_id) where state = 'pending';
create table return_private.delivery_due (
  order_id bigint primary key references return_private.cases(order_id),
  driver_id uuid not null,
  amount numeric(12,2) not null check (amount >= 0),
  currency text not null check (currency = 'TJS'),
  created_at timestamptz not null default clock_timestamp()
);
create table return_private.commands (
  actor uuid not null,
  request uuid not null,
  order_id bigint not null references return_private.cases(order_id),
  action text not null,
  payload jsonb not null,
  result jsonb not null,
  recorded_at timestamptz not null default clock_timestamp(),
  primary key (actor, request)
);
create index return_commands_order on return_private.commands(order_id);
alter table return_private.agreements enable row level security;
alter table return_private.cases enable row level security;
alter table return_private.refunds enable row level security;
alter table return_private.delivery_due enable row level security;
alter table return_private.commands enable row level security;
revoke all on all tables in schema return_private from public, anon, authenticated;

create function public.record_return_agreement(p_store uuid, p_request uuid, p_active boolean, p_evidence text)
returns uuid language plpgsql security definer set search_path = '' as $$
declare
  v_actor uuid := auth.uid();
  existing return_private.agreements;
  evidence text := nullif(btrim(p_evidence), '');
begin
  if v_actor is null or not public.is_admin() then raise exception 'not_allowed'; end if;
  if p_request is null or p_active is null or evidence is null or length(evidence) > 200 then
    raise exception 'bad_value';
  end if;
  perform 1 from public.stores where id = p_store for update;
  if not found then raise exception 'not_found'; end if;
  insert into return_private.agreements(id, store_id, active, evidence, recorded_by)
  values (p_request, p_store, p_active, evidence, v_actor) on conflict (id) do nothing;
  select * into existing from return_private.agreements where id = p_request;
  if (existing.store_id, existing.active, existing.evidence, existing.recorded_by)
     is distinct from (p_store, p_active, evidence, v_actor) then
    raise exception 'request_conflict';
  end if;
  return existing.id;
end $$;

create function return_private.view_case(p_order bigint, p_customer boolean) returns jsonb
language sql stable set search_path = '' as $$
  select jsonb_build_object(
    'departed_at', c.departed_at, 'cancelled_at', c.cancelled_at, 'received_at', c.received_at
  ) || case when p_customer then '{}'::jsonb else jsonb_build_object(
    'paid', c.paid, 'currency', c.currency, 'refused_at', c.refused_at,
    'confirmed_refund', totals.refunded,
    'open_claim', case when c.cancelled_at is not null then c.paid - totals.refunded end,
    'delivery_due', d.amount,
    'pending', totals.pending
  ) end
  from return_private.cases c
  left join return_private.delivery_due d using (order_id)
  cross join lateral (
    select coalesce(sum(r.amount) filter (where r.state = 'confirmed'), 0) refunded,
           (jsonb_agg(jsonb_build_object('ref', r.source_ref, 'amount', r.amount, 'method', r.method))
             filter (where r.state = 'pending'))->0 pending
    from return_private.refunds r where r.order_id = c.order_id
  ) totals
  where c.order_id = p_order;
$$;

create function public.order_return_status(p_order bigint) returns jsonb
language plpgsql stable security definer set search_path = '' as $$
declare
  v_actor uuid := auth.uid();
  o public.orders;
  result jsonb;
begin
  select * into o from public.orders where id = p_order;
  if v_actor is null or not found or not (
    v_actor = o.customer_id or v_actor is not distinct from o.driver_id
    or public.owns_store(o.store_id) or public.has_perm('orders')
  ) then raise exception 'not_allowed'; end if;
  result := coalesce(return_private.view_case(p_order, v_actor = o.customer_id), '{}'::jsonb);
  return result || jsonb_build_object('order_status', o.status,
    'can_document_departure', v_actor is not distinct from o.driver_id and o.status = 'pickedup'
      and o.payment = 'cash' and exists (
        select 1 from (
          select active from return_private.agreements
          where store_id = o.store_id and recorded_at < o.created_at
          order by recorded_at desc, id desc limit 1
        ) a where a.active
      ));
end $$;

create function public.order_return_action(
  p_order bigint, p_request uuid, p_action text,
  p_ref text default null, p_amount numeric default null, p_method text default null
) returns jsonb language plpgsql security definer set search_path = '' as $$
declare
  v_actor uuid := auth.uid();
  o public.orders;
  c return_private.cases;
  agreement return_private.agreements;
  prior return_private.commands;
  refund return_private.refunds;
  ref text := nullif(upper(btrim(p_ref)), '');
  payload jsonb := jsonb_build_object('ref', ref, 'amount', p_amount, 'method', p_method);
  result jsonb;
  remaining numeric;
  merchant boolean;
  driver boolean;
begin
  if v_actor is null then raise exception 'not_allowed'; end if;
  if p_request is null or p_action is null or length(ref) > 200
     or (p_amount is not null and (p_amount <= 0 or p_amount > 9999999999.99 or scale(p_amount) > 2)) then
    raise exception 'bad_value';
  end if;
  if (p_action in ('depart', 'report_refund', 'confirm_refund', 'dispute_refund') and p_amount is null)
     or (p_action not in ('depart', 'report_refund', 'confirm_refund', 'dispute_refund') and p_amount is not null)
     or (p_action = 'report_refund' and (p_method is null or p_method not in ('cash', 'transfer')))
     or (p_action <> 'report_refund' and p_method is not null)
     or (p_action = 'cancel' and ref is not null)
     or (p_action <> 'cancel' and ref is null) then
    raise exception 'bad_value';
  end if;
  -- Lock request first, then the shared order. Different keys still serialize per order.
  perform pg_advisory_xact_lock(hashtextextended(v_actor::text || ':' || p_request::text, 771606));
  select * into prior from return_private.commands where request = p_request and commands.actor = v_actor;
  if found then
    if (prior.order_id, prior.action, prior.payload) is distinct from (p_order, p_action, payload) then
      raise exception 'request_conflict';
    end if;
    return prior.result;
  end if;
  select * into o from public.orders where id = p_order for update;
  if not found then raise exception 'not_allowed'; end if;
  merchant := public.owns_store(o.store_id);
  driver := v_actor is not distinct from o.driver_id;
  case p_action
    when 'depart', 'confirm_refund', 'dispute_refund' then
      if not driver then raise exception 'not_allowed'; end if;
    when 'cancel' then
      if v_actor <> o.customer_id then raise exception 'not_allowed'; end if;
    when 'receive', 'report_refund' then
      if not merchant then raise exception 'not_allowed'; end if;
    when 'refuse_refund' then
      if not (merchant or public.has_perm('orders')) then raise exception 'not_allowed'; end if;
    else raise exception 'bad_value';
  end case;
  select * into c from return_private.cases where order_id = p_order;

  if p_action = 'depart' then
    if c.order_id is not null or o.status <> 'pickedup' or o.payment is distinct from 'cash' then
      raise exception 'return_bad_state';
    end if;
    select * into agreement from return_private.agreements
    where store_id = o.store_id and recorded_at < o.created_at
    order by recorded_at desc, id desc limit 1;
    if not found or not agreement.active then raise exception 'return_no_agreement'; end if;
    insert into return_private.cases(order_id, store_id, agreement_id, driver_id, customer_id, paid, payment_ref)
    values (p_order, o.store_id, agreement.id, o.driver_id, o.customer_id, p_amount, ref);
  elsif p_action = 'cancel' then
    if c.order_id is null or c.cancelled_at is not null or o.status <> 'pickedup' then
      raise exception 'return_bad_state';
    end if;
    update return_private.cases set cancelled_at = clock_timestamp() where order_id = p_order;
    insert into return_private.delivery_due(order_id, driver_id, amount, currency)
    values (p_order, c.driver_id, round(o.driver_payout - o.tip, 2), c.currency);
    update public.orders set status = 'cancelled', done_at = clock_timestamp(), cancelled_by = 'customer'
    where id = p_order;
  else
    if c.cancelled_at is null or o.status <> 'cancelled' then raise exception 'return_bad_state'; end if;
    if p_action = 'receive' then
      if c.received_at is not null then raise exception 'return_bad_state'; end if;
      update return_private.cases set received_at = clock_timestamp(), received_by = v_actor, receipt_ref = ref
      where order_id = p_order;
    else
      if c.received_at is null then raise exception 'return_waiting_receipt'; end if;
      select c.paid - coalesce(sum(amount), 0) into remaining
      from return_private.refunds where order_id = p_order and state = 'confirmed';
      if remaining <= 0 then raise exception 'return_bad_state'; end if;
      case p_action
        when 'refuse_refund' then
          if c.refused_at is not null or exists (
            select 1 from return_private.refunds where order_id = p_order and state = 'pending'
          ) then raise exception 'return_bad_state'; end if;
          update return_private.cases set refused_at = clock_timestamp(), refused_by = v_actor, refusal_ref = ref
          where order_id = p_order;
        when 'report_refund' then
          if p_amount > remaining then raise exception 'return_exceeds_claim'; end if;
          insert into return_private.refunds(order_id, store_id, source_ref, amount, method, reported_by)
          values (p_order, o.store_id, ref, p_amount, p_method, v_actor);
        else
          select * into refund from return_private.refunds
          where order_id = p_order and store_id = o.store_id and source_ref = ref;
          if not found or refund.state <> 'pending' or refund.amount <> p_amount then
            raise exception 'return_bad_state';
          end if;
          if refund.amount > remaining then raise exception 'return_exceeds_claim'; end if;
          update return_private.refunds set state = case when p_action = 'confirm_refund' then 'confirmed' else 'disputed' end,
            checked_by = v_actor, checked_at = clock_timestamp()
          where store_id = o.store_id and source_ref = ref;
      end case;
    end if;
  end if;

  result := return_private.view_case(p_order, p_action = 'cancel');
  insert into return_private.commands(actor, request, order_id, action, payload, result)
  values (v_actor, p_request, p_order, p_action, payload, result);
  return result;
end $$;

create function return_private.guard_case_order() returns trigger
language plpgsql set search_path = '' security definer as $$
declare c return_private.cases;
begin
  select * into c from return_private.cases where order_id = old.id;
  if found and (
    (new.store_id, new.driver_id, new.customer_id) is distinct from (old.store_id, old.driver_id, old.customer_id)
    or (c.cancelled_at is not null and new.status <> 'cancelled')
  ) then raise exception 'return_order_protected'; end if;
  return new;
end $$;
create trigger return_order_guard before update of status, store_id, driver_id, customer_id on public.orders
for each row execute function return_private.guard_case_order();

revoke all on all functions in schema return_private from public, anon, authenticated;
revoke all on function public.record_return_agreement(uuid,uuid,boolean,text),
  public.order_return_status(bigint), public.order_return_action(bigint,uuid,text,text,numeric,text)
  from public, anon, authenticated;
grant execute on function public.record_return_agreement(uuid,uuid,boolean,text),
  public.order_return_status(bigint), public.order_return_action(bigint,uuid,text,text,numeric,text)
  to authenticated;
commit;
