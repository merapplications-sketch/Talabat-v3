-- TALABOT BRIEF-19 / SEC-18: PROPOSED, NOT DEPLOYED.
-- Nonfinancial delivery instructions only. LOCAL validation required before any owner decision.
BEGIN;
DO $brief19_preflight$
DECLARE
  v_table oid := to_regclass('public.order_delivery_instructions');
BEGIN
  IF v_table IS NULL THEN
    CREATE TABLE public.order_delivery_instructions (
      order_id bigint PRIMARY KEY REFERENCES public.orders(id) ON DELETE CASCADE,
      customer_id uuid NOT NULL,
      instruction_keys text[] NOT NULL DEFAULT ARRAY[]::text[],
      updated_at timestamptz NOT NULL DEFAULT now(),
      CONSTRAINT order_delivery_instructions_limit CHECK (cardinality(instruction_keys) <= 6)
    );
  ELSE
    -- Never accept CREATE IF NOT EXISTS on an incompatible pre-existing table.
    IF (SELECT jsonb_agg(jsonb_build_array(a.attname,pg_catalog.format_type(a.atttypid,a.atttypmod),a.attnotnull)
                         ORDER BY a.attnum)
          FROM pg_catalog.pg_attribute a
         WHERE a.attrelid=v_table AND a.attnum>0 AND NOT a.attisdropped)
         IS DISTINCT FROM
         '[["order_id","bigint",true],["customer_id","uuid",true],["instruction_keys","text[]",true],["updated_at","timestamp with time zone",true]]'::jsonb
       OR NOT EXISTS (
         SELECT 1 FROM pg_catalog.pg_constraint c
         WHERE c.conrelid=v_table AND c.contype='p'
           AND c.conkey=ARRAY[(SELECT attnum FROM pg_catalog.pg_attribute
                               WHERE attrelid=v_table AND attname='order_id')]::smallint[]
       )
       OR NOT EXISTS (
         SELECT 1 FROM pg_catalog.pg_constraint c
         WHERE c.conrelid=v_table AND c.contype='f'
           AND c.confrelid='public.orders'::regclass AND c.confdeltype='c'
           AND c.conkey=ARRAY[(SELECT attnum FROM pg_catalog.pg_attribute
                               WHERE attrelid=v_table AND attname='order_id')]::smallint[]
       )
       OR NOT EXISTS (
         SELECT 1 FROM pg_catalog.pg_constraint c
          WHERE c.conrelid=v_table AND c.contype='c'
            AND c.conname='order_delivery_instructions_limit'
            AND pg_catalog.pg_get_constraintdef(c.oid) LIKE '%cardinality(instruction_keys)%<= 6%'
       )
       OR (SELECT pg_catalog.pg_get_expr(d.adbin,d.adrelid)
             FROM pg_catalog.pg_attrdef d JOIN pg_catalog.pg_attribute a
               ON a.attrelid=d.adrelid AND a.attnum=d.adnum
            WHERE d.adrelid=v_table AND a.attname='instruction_keys') IS DISTINCT FROM 'ARRAY[]::text[]'
       OR (SELECT pg_catalog.pg_get_expr(d.adbin,d.adrelid)
             FROM pg_catalog.pg_attrdef d JOIN pg_catalog.pg_attribute a
               ON a.attrelid=d.adrelid AND a.attnum=d.adnum
            WHERE d.adrelid=v_table AND a.attname='updated_at') IS DISTINCT FROM 'now()'
    THEN
      RAISE EXCEPTION 'BRIEF19_PREFLIGHT_INCOMPATIBLE: existing order_delivery_instructions differs; no migration applied'
        USING ERRCODE='55000';
    END IF;
  END IF;
END
$brief19_preflight$;

-- All reads/writes via explicit, permission-checked RPCs. No direct table access.
ALTER TABLE public.order_delivery_instructions ENABLE ROW LEVEL SECURITY;
REVOKE ALL ON TABLE public.order_delivery_instructions FROM PUBLIC, anon, authenticated;

CREATE OR REPLACE FUNCTION public.delivery_instructions_ready()
RETURNS boolean LANGUAGE sql STABLE SECURITY INVOKER SET search_path=''
AS $$ SELECT auth.uid() IS NOT NULL $$;
REVOKE ALL ON FUNCTION public.delivery_instructions_ready() FROM PUBLIC, anon;
GRANT EXECUTE ON FUNCTION public.delivery_instructions_ready() TO authenticated;

CREATE OR REPLACE FUNCTION public.set_order_delivery_instructions(p_order bigint,p_keys text[])
RETURNS boolean LANGUAGE plpgsql SECURITY DEFINER SET search_path='' AS $$
DECLARE v_customer uuid;
BEGIN
  IF auth.uid() IS NULL OR p_order IS NULL OR p_order<=0 OR p_keys IS NULL
     OR cardinality(p_keys)>6 THEN
    RAISE EXCEPTION 'bad_value' USING ERRCODE='22023';
  END IF;
  IF EXISTS (SELECT 1 FROM unnest(p_keys) x(k)
             WHERE k IS NULL OR k NOT IN ('door','call','no_ring','knock','reception','meet'))
     OR (SELECT count(DISTINCT k) FROM unnest(p_keys) x(k))<>cardinality(p_keys) THEN
    RAISE EXCEPTION 'bad_value' USING ERRCODE='22023';
  END IF;
  -- SHARE lock prevents a pickup/status transition racing the final upsert.
  SELECT customer_id INTO v_customer
    FROM public.orders
   WHERE id=p_order AND status IN ('pending','preparing','ready')
   FOR SHARE;
  IF v_customer IS NULL OR v_customer<>auth.uid() THEN
    RAISE EXCEPTION 'forbidden' USING ERRCODE='42501';
  END IF;
  INSERT INTO public.order_delivery_instructions(order_id,customer_id,instruction_keys,updated_at)
    VALUES(p_order,v_customer,p_keys,now())
  ON CONFLICT(order_id) DO UPDATE
    SET instruction_keys=EXCLUDED.instruction_keys, updated_at=now()
    WHERE public.order_delivery_instructions.instruction_keys
          IS DISTINCT FROM EXCLUDED.instruction_keys;
  RETURN true;
END $$;
REVOKE ALL ON FUNCTION public.set_order_delivery_instructions(bigint,text[]) FROM PUBLIC,anon;
GRANT EXECUTE ON FUNCTION public.set_order_delivery_instructions(bigint,text[]) TO authenticated;

CREATE OR REPLACE FUNCTION public.get_order_delivery_instructions(p_order bigint)
RETURNS text[] LANGUAGE plpgsql STABLE SECURITY DEFINER SET search_path='' AS $$
DECLARE v_customer uuid; v_driver uuid; v_result text[]; v_uid uuid := auth.uid();
BEGIN
  IF v_uid IS NULL OR p_order IS NULL OR p_order<=0 THEN
    RAISE EXCEPTION 'forbidden' USING ERRCODE='42501';
  END IF;
  SELECT customer_id,driver_id INTO v_customer,v_driver
    FROM public.orders WHERE id=p_order;
  IF NOT FOUND OR (
    v_customer IS DISTINCT FROM v_uid AND NOT (
      v_driver IS NOT DISTINCT FROM v_uid AND EXISTS (
        SELECT 1 FROM public.profiles p WHERE p.id=v_uid
          AND p.role='driver' AND p.driver_status='approved'
      )
    )
  ) THEN
    RAISE EXCEPTION 'forbidden' USING ERRCODE='42501';
  END IF;
  SELECT instruction_keys INTO v_result
    FROM public.order_delivery_instructions WHERE order_id=p_order;
  RETURN coalesce(v_result,ARRAY[]::text[]);
END $$;
REVOKE ALL ON FUNCTION public.get_order_delivery_instructions(bigint) FROM PUBLIC,anon;
GRANT EXECUTE ON FUNCTION public.get_order_delivery_instructions(bigint) TO authenticated;
COMMIT;
