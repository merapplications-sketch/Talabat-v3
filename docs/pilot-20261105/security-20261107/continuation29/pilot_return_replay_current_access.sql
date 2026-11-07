CREATE OR REPLACE FUNCTION public.order_return_action(p_order bigint, p_request uuid, p_action text, p_ref text DEFAULT NULL::text, p_amount numeric DEFAULT NULL::numeric, p_method text DEFAULT NULL::text)
 RETURNS jsonb
 LANGUAGE plpgsql
 SECURITY DEFINER
 SET search_path TO ''
AS $function$
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
  if v_actor is null or not public.account_enabled() then raise exception 'not_allowed'; end if;
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
  if prior.request is not null then
    if (prior.order_id, prior.action, prior.payload) is distinct from (p_order, p_action, payload) then
      raise exception 'request_conflict';
    end if;
    return prior.result;
  end if;
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
end $function$

