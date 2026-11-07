CREATE FUNCTION public.pilot_bounded_finance_probe(p_phase text) RETURNS jsonb
LANGUAGE plpgsql SECURITY DEFINER SET search_path='' AS $$
DECLARE started timestamptz:=clock_timestamp(); acquired timestamptz; r jsonb; req uuid; amt numeric;
BEGIN
 IF auth.uid() IS DISTINCT FROM '85fea11e-738c-4221-ac29-51d4ff50d594'::uuid OR NOT public.account_enabled() THEN RAISE EXCEPTION 'not_allowed'; END IF;
 IF p_phase='run' THEN req:='5d2dbe6a-8fb0-427f-96ef-99e310f5a4cb';amt:=1;
 ELSIF p_phase='compensate' THEN req:='01d215ab-2f1e-4c40-8db3-ffe5595dc69e';amt:=-1;
 ELSE RAISE EXCEPTION 'bad_value'; END IF;
 PERFORM pg_advisory_xact_lock(hashtextextended('finance-request:'||req::text,0));
 acquired:=clock_timestamp();
 IF p_phase='compensate' AND NOT EXISTS(SELECT 1 FROM finance_private.commands WHERE request='5d2dbe6a-8fb0-427f-96ef-99e310f5a4cb') THEN RAISE EXCEPTION 'not_started'; END IF;
 IF EXISTS(SELECT 1 FROM public.staff_members WHERE user_id=auth.uid()) THEN RAISE EXCEPTION 'fixture_changed'; END IF;
 IF p_phase='run' THEN PERFORM pg_sleep(2); END IF;
 -- Test-only authorization exists inside this transaction and is removed before commit.
 -- Other requests cannot observe this grant. No caller-controlled target or amount.
 INSERT INTO public.staff_members(user_id,perms) VALUES(auth.uid(),ARRAY['finance']);
 r:=public.finance_execute(req,'wallet_adjust','00000000-0000-4000-8000-000000000901',amt,'ASVS bounded HTTP concurrency');
 DELETE FROM public.staff_members WHERE user_id=auth.uid();
 RETURN jsonb_build_object('pid',pg_backend_pid(),'started',started,'acquired',acquired,'finished',clock_timestamp(),'entry',r->'wallet_entry','amount',r->'amount');
END $$;
REVOKE ALL ON FUNCTION public.pilot_bounded_finance_probe(text) FROM PUBLIC,anon;
GRANT EXECUTE ON FUNCTION public.pilot_bounded_finance_probe(text) TO authenticated;
