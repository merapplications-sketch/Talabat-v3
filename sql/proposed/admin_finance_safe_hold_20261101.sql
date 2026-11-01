-- REVIEW-ONLY SAFE HOLD. NOT APPLIED LIVE. No reversal/deletion of financial history.
-- For an authorised coordinated rollback only; operational delivery remains independent.
begin;
revoke execute on function public.finance_execute(uuid,text,uuid,numeric,text) from public,anon,authenticated;
create or replace function public.finance_access() returns jsonb
language sql stable security definer set search_path=pg_catalog,public as $$
 select jsonb_build_object('execute',false,'version',2,'capabilities',jsonb_build_array('commands','settlement_events'),'paused',true)
$$;
revoke all on function public.finance_access() from public,anon;
grant execute on function public.finance_access() to authenticated;
commit;
-- Keep finance_private.commands, all timestamps, wallet entries, read/status endpoints and
-- the legacy keyless refusal functions intact. Never restore the old unsafe settlement function.
