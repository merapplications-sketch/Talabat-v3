-- TALABOT BRIEF-19 / SEC-18: DESTRUCTIVE OWNER-ONLY SQL (NOT A MIGRATION).
-- NOT for CI, Supabase migrations, routine rollback, or deployment automation.
-- Explicit owner approval and an independently reviewed backup are required.
-- Use only in a separate manual session after recording the owner's decision.
BEGIN;
DO $owner_gate$
BEGIN
 IF current_setting('talabot.brief18_owner_approved_drop', true)
       IS DISTINCT FROM 'OWNER-APPROVED-PURGE-BRIEF18-20261118' THEN
   RAISE EXCEPTION 'OWNER_AUTHORIZATION_REQUIRED: data-preserving rollback is the default'
     USING ERRCODE='42501';
 END IF;
END $owner_gate$;
DROP TABLE public.order_delivery_instructions RESTRICT;
COMMIT;
