-- TALABOT Gate 1 / PROPOSED ONLY. Apply exclusively to newly created, verified
-- zero-cost Supabase talabot-test, after original schema_patch17..34.
-- NEVER apply to real Talabat or the historic pilot without separate owner approval.
-- Source baseline: tech/v82-int 09ef07fd29fb5c5a3e323c23c7331e577567ab1e.
-- F02: row lock + pickedup status ensure a single delivery transition and its existing triggers.
-- F04: fail closed on short/over-collection; existing CASH-01/loyalty triggers unchanged.
-- The standalone report_driver_cash_short RPC creates an authorized support report with
-- no delivery status/payment/driver settlement write. Caller receives its ticket ID.
-- IMPORTANT: Exposing a SECURITY DEFINER function requires independent privilege/RLS audit.

CREATE OR REPLACE FUNCTION public.deliver_order(
  p_id bigint, p_cash numeric DEFAULT NULL, p_note text DEFAULT NULL, p_photo text DEFAULT NULL
) RETURNS void
LANGUAGE plpgsql SECURITY DEFINER SET search_path = ''
AS $gate1$
DECLARE
  o public.orders%ROWTYPE;
  iscash boolean;
  v_due numeric;
BEGIN
  SELECT * INTO o FROM public.orders WHERE id = p_id FOR UPDATE;
  IF NOT FOUND THEN RAISE EXCEPTION 'not_found'; END IF;
  IF auth.uid() IS NULL OR o.driver_id IS DISTINCT FROM auth.uid() THEN
    RAISE EXCEPTION 'not_allowed';
  END IF;
  iscash := o.payment ~ '^(cash|Cash|Наличн)';
  IF o.status = 'delivered' THEN
    -- Exact same-session / retried-after-commit acknowledgment, no second UPDATE/trigger.
    IF o.cash_collected IS NOT DISTINCT FROM p_cash
      AND coalesce(o.cash_note,'') = coalesce(left(p_note,200),'')
      AND o.delivery_photo IS NOT DISTINCT FROM p_photo THEN
      RETURN;
    END IF;
    RAISE EXCEPTION 'already_delivered';
  END IF;
  IF o.status <> 'pickedup' THEN RAISE EXCEPTION 'bad_transition'; END IF;
  IF p_photo IS NOT NULL
     AND p_photo !~ ('^' || auth.uid()::text || '/' || p_id::text || '/[A-Za-z0-9_-]{8,64}\.jpg$') THEN
    RAISE EXCEPTION 'bad_value';
  END IF;
  IF coalesce(o.leave_at_door,false) AND p_photo IS NULL THEN
    RAISE EXCEPTION 'photo_required';
  END IF;

  IF iscash THEN
    IF p_cash IS NULL OR p_cash < 0 THEN RAISE EXCEPTION 'cash_required'; END IF;
    v_due := o.total - coalesce(o.wallet_used,0);
    IF v_due IS NULL OR v_due < 0 THEN RAISE EXCEPTION 'bad_value'; END IF;
    -- Q13: reject more than 2 significant decimals, never silently round the receipt.
    IF p_cash <> round(p_cash,2) OR v_due <> round(v_due,2) THEN
      RAISE EXCEPTION 'cash_precision';
    END IF;
    IF p_cash < v_due THEN RAISE EXCEPTION 'cash_short'; END IF;
    -- CASH-01 / Q09–Q13 are independent. No invented excess-to-wallet effect here.
    IF p_cash > v_due THEN RAISE EXCEPTION 'cash_over_policy'; END IF;
  ELSIF p_cash IS NOT NULL THEN
    RAISE EXCEPTION 'bad_value';
  END IF;

  UPDATE public.orders
     SET status='delivered', done_at=now(),
         cash_collected=CASE WHEN iscash THEN p_cash ELSE NULL END,
         cash_note=CASE WHEN iscash THEN left(p_note,200) ELSE NULL END,
         delivery_photo=p_photo,
         arrived_cust_at=coalesce(arrived_cust_at,now())
   WHERE id=p_id AND status='pickedup';
  IF NOT FOUND THEN RAISE EXCEPTION 'bad_transition'; END IF;
END
$gate1$;
REVOKE ALL ON FUNCTION public.deliver_order(bigint,numeric,text,text) FROM PUBLIC, anon;
GRANT EXECUTE ON FUNCTION public.deliver_order(bigint,numeric,text,text) TO authenticated;

-- F04: separate authorized courier report, because a RAISE EXCEPTION in
-- deliver_order rolls back writes in that transaction.
-- Existing support-tickets schema is from schema_patch19; unique open order ticket
-- index serializes with the locked order row and prevents ticket proliferation.
CREATE OR REPLACE FUNCTION public.report_driver_cash_short(
  p_id bigint, p_cash numeric, p_note text DEFAULT NULL
) RETURNS bigint
LANGUAGE plpgsql SECURITY DEFINER SET search_path = ''
AS $gate1_report$
DECLARE
  o public.orders%ROWTYPE;
  v_due numeric;
  v_ticket bigint;
  v_msg text;
BEGIN
  SELECT * INTO o FROM public.orders WHERE id=p_id FOR UPDATE;
  IF NOT FOUND THEN RAISE EXCEPTION 'not_found'; END IF;
  IF auth.uid() IS NULL OR o.driver_id IS DISTINCT FROM auth.uid() OR o.status <> 'pickedup' THEN
    RAISE EXCEPTION 'not_allowed';
  END IF;
  IF o.payment !~ '^(cash|Cash|Наличн)' THEN RAISE EXCEPTION 'bad_value'; END IF;
  v_due := o.total - coalesce(o.wallet_used,0);
  IF v_due IS NULL OR v_due <= 0 OR v_due <> round(v_due,2)
     OR p_cash IS NULL OR p_cash < 0 OR p_cash <> round(p_cash,2)
     OR p_cash >= v_due OR char_length(coalesce(p_note,'')) > 200 THEN
    RAISE EXCEPTION 'bad_value';
  END IF;
  SELECT id INTO v_ticket FROM public.support_tickets
   WHERE order_id=p_id AND status IN ('open','in_progress')
   ORDER BY id DESC LIMIT 1;
  IF v_ticket IS NULL THEN
    INSERT INTO public.support_tickets(customer_id,order_id,reason)
    VALUES(o.customer_id,p_id,'payment') RETURNING id INTO v_ticket;
  END IF;
  v_msg := left(format('Courier cash-shortfall report, courier=%s; due=%s TJS; received=%s TJS; note=%s',
                       auth.uid(),v_due,p_cash,coalesce(p_note,'')),500);
  IF NOT EXISTS (
      SELECT 1 FROM public.ticket_messages
       WHERE ticket_id=v_ticket AND sender_id=auth.uid() AND body=v_msg
  ) THEN
    INSERT INTO public.ticket_messages(ticket_id,from_staff,sender_id,body)
    VALUES(v_ticket,false,auth.uid(),v_msg);
  END IF;
  UPDATE public.support_tickets SET updated_at=now() WHERE id=v_ticket;
  RETURN v_ticket;
END
$gate1_report$;
REVOKE ALL ON FUNCTION public.report_driver_cash_short(bigint,numeric,text) FROM PUBLIC, anon;
GRANT EXECUTE ON FUNCTION public.report_driver_cash_short(bigint,numeric,text) TO authenticated;
