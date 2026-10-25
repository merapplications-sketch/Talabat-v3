-- DEFAULT ROLLBACK of patch 40 — NOT applied. Stops all routing reservations; KEEPS every table and booking.
-- Effect: the Edge Function «route» can no longer reserve (RPC refused) -> it answers «tracking» with reason
-- «budget_unavailable»: no route, no ETA, no upstream call. Orders, chat, delivery and external navigation links unaffected.
-- First step of a rollback (no SQL needed): set NAVIGATION_CONFIG "internal": false in the function secrets.
-- This file is the database-side stop. Re-enable later with the two GRANT lines at the end of patch40_navigation_budget.sql.
revoke execute on function public.navigation_reserve_budget(text, integer, integer, integer, uuid) from service_role;
revoke execute on function public.navigation_settle_budget(text, uuid, integer) from service_role;
-- Check: select has_function_privilege('service_role','public.navigation_reserve_budget(text,integer,integer,integer,uuid)','execute'); -> false
-- Tables navigation_budget_* stay as they are (usage record kept).
