-- TALABOT BRIEF-18 U-02 proposed rollback ONLY; not applied.
BEGIN;
DROP FUNCTION IF EXISTS public.get_order_delivery_instructions(bigint);
DROP FUNCTION IF EXISTS public.set_order_delivery_instructions(bigint,text[]);
DROP FUNCTION IF EXISTS public.delivery_instructions_ready();
DROP TABLE IF EXISTS public.order_delivery_instructions;
COMMIT;
