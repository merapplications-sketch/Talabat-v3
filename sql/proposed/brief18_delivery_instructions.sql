-- TALABOT BRIEF-18 U-02 — PROPOSED ONLY, NOT APPLIED. REQUIRES SECURITY REVIEW.
-- Nonfinancial courier-instruction storage; no modifications to place_order,
-- CASH-01, tips, settlement, wallet, refunds, or any existing money RPC.
BEGIN;
CREATE TABLE IF NOT EXISTS public.order_delivery_instructions (
 order_id bigint PRIMARY KEY REFERENCES public.orders(id) ON DELETE CASCADE,
 customer_id uuid NOT NULL,
 instruction_keys text[] NOT NULL DEFAULT ARRAY[]::text[],
 updated_at timestamptz NOT NULL DEFAULT now(),
 CONSTRAINT order_delivery_instructions_limit CHECK (cardinality(instruction_keys) <= 6)
);
ALTER TABLE public.order_delivery_instructions ENABLE ROW LEVEL SECURITY;
REVOKE ALL ON TABLE public.order_delivery_instructions FROM PUBLIC, anon, authenticated;
CREATE OR REPLACE FUNCTION public.delivery_instructions_ready()
RETURNS boolean LANGUAGE sql STABLE SECURITY INVOKER SET search_path=pg_catalog,public
AS $$ SELECT auth.uid() IS NOT NULL $$;
REVOKE ALL ON FUNCTION public.delivery_instructions_ready() FROM PUBLIC, anon;
GRANT EXECUTE ON FUNCTION public.delivery_instructions_ready() TO authenticated;
CREATE OR REPLACE FUNCTION public.set_order_delivery_instructions(p_order bigint,p_keys text[])
RETURNS boolean LANGUAGE plpgsql SECURITY DEFINER SET search_path=pg_catalog,public AS $$
DECLARE v_customer uuid;
BEGIN
 IF auth.uid() IS NULL OR p_order IS NULL OR p_order<=0 OR p_keys IS NULL
    OR cardinality(p_keys)>6 THEN RAISE EXCEPTION 'bad_value' USING ERRCODE='22023'; END IF;
 IF EXISTS(SELECT 1 FROM unnest(p_keys) x(k) WHERE k IS NULL OR
    k NOT IN ('door','call','no_ring','knock','reception','meet'))
    OR (SELECT count(DISTINCT k) FROM unnest(p_keys) x(k))<>cardinality(p_keys)
 THEN RAISE EXCEPTION 'bad_value' USING ERRCODE='22023'; END IF;
 SELECT customer_id INTO v_customer FROM public.orders
 WHERE id=p_order AND status IN ('pending','preparing','ready','pickedup') FOR SHARE;
 IF v_customer IS NULL OR v_customer<>auth.uid()
 THEN RAISE EXCEPTION 'forbidden' USING ERRCODE='42501'; END IF;
 INSERT INTO public.order_delivery_instructions(order_id,customer_id,instruction_keys,updated_at)
 VALUES(p_order,v_customer,p_keys,now())
 ON CONFLICT(order_id) DO UPDATE SET instruction_keys=excluded.instruction_keys,updated_at=now();
 RETURN true;
END $$;
REVOKE ALL ON FUNCTION public.set_order_delivery_instructions(bigint,text[]) FROM PUBLIC,anon;
GRANT EXECUTE ON FUNCTION public.set_order_delivery_instructions(bigint,text[]) TO authenticated;
CREATE OR REPLACE FUNCTION public.get_order_delivery_instructions(p_order bigint)
RETURNS text[] LANGUAGE plpgsql STABLE SECURITY DEFINER SET search_path=pg_catalog,public AS $$
DECLARE v_customer uuid;v_driver uuid;v_result text[];
BEGIN
 IF auth.uid() IS NULL OR p_order IS NULL OR p_order<=0
 THEN RAISE EXCEPTION 'forbidden' USING ERRCODE='42501'; END IF;
 SELECT customer_id,driver_id INTO v_customer,v_driver FROM public.orders WHERE id=p_order;
 IF NOT FOUND OR (v_customer IS DISTINCT FROM auth.uid()
                 AND v_driver IS DISTINCT FROM auth.uid())
 THEN RAISE EXCEPTION 'forbidden' USING ERRCODE='42501'; END IF;
 SELECT instruction_keys INTO v_result FROM public.order_delivery_instructions WHERE order_id=p_order;
 RETURN coalesce(v_result,ARRAY[]::text[]);
END $$;
REVOKE ALL ON FUNCTION public.get_order_delivery_instructions(bigint) FROM PUBLIC,anon;
GRANT EXECUTE ON FUNCTION public.get_order_delivery_instructions(bigint) TO authenticated;
COMMIT;
-- Required review tests: customer isolation, unassigned driver denial, anon denial,
-- duplicate/invalid input, no changes to monetary functions, and safe rollback.
