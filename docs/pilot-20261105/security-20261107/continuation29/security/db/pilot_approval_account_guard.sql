CREATE OR REPLACE FUNCTION public.customer_confirm_order(p_order bigint, p_revision integer, p_request uuid)
 RETURNS jsonb
 LANGUAGE plpgsql
 SECURITY DEFINER
 SET search_path TO 'public'
AS $function$
declare o orders;a fulfillment_private.order_approvals;r fulfillment_private.approval_requests;payload jsonb;result_json jsonb;line jsonb;prev_write text;
begin
 if not public.account_enabled() then raise exception 'not_allowed'; end if;
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
end $function$;

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
end $function$;
