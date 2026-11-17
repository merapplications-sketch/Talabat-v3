-- BRIEF-19 SEC-18 rollback: NON-DESTRUCTIVE. Proposed only; no live execution.
-- Existing delivery instructions rows are deliberately retained for restoration/review.
BEGIN;
DROP FUNCTION IF EXISTS public.get_order_delivery_instructions(bigint);
DROP FUNCTION IF EXISTS public.set_order_delivery_instructions(bigint,text[]);
DROP FUNCTION IF EXISTS public.delivery_instructions_ready();
-- NEVER DROP public.order_delivery_instructions during rollback.
COMMIT;
