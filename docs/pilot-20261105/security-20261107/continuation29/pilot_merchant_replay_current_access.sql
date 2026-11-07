CREATE OR REPLACE FUNCTION public.merchant_review_order(p_order bigint, p_minutes integer, p_request uuid, p_items jsonb DEFAULT NULL::jsonb, p_note text DEFAULT NULL::text)
 RETURNS jsonb
 LANGUAGE plpgsql
 SECURITY DEFINER
 SET search_path TO 'public'
AS $function$
declare o orders;a fulfillment_private.order_approvals;cfg fulfillment_private.confirmation_config;r fulfillment_private.approval_requests;
 payload jsonb;snap jsonb;old_snap jsonb;quoted jsonb;needs_accept boolean;price_change boolean;time_change boolean;result_json jsonb;prev_write text;
begin
 if not public.account_enabled() then raise exception 'not_allowed'; end if;
 if auth.uid()is null or p_request is null or p_minutes is null or p_minutes not between 5 and 90 then raise exception'bad_value';end if;
 payload:=jsonb_build_object('minutes',p_minutes,'items',p_items,'note',left(coalesce(p_note,''),200));
 perform pg_advisory_xact_lock(hashtextextended('approval:'||p_request::text,0));
 select * into r from fulfillment_private.approval_requests where request=p_request;
 if found then
  if r.actor<>auth.uid()or r.operation<>'merchant_review'or r.order_id<>p_order or r.payload<>payload then raise exception'request_conflict';end if;
  if not exists(select 1 from public.orders current_order where current_order.id=p_order and (public.owns_store(current_order.store_id) or public.has_perm('orders'))) then raise exception 'not_allowed'; end if;
  return r.result;end if;
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
 merchant_actor=auth.uid(),merchant_at=now(),accepted_prep_minutes=case when not needs_accept and(accepted_prep_minutes is null or p_minutes<accepted_prep_minutes)then p_minutes else accepted_prep_minutes end
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
end $function$

