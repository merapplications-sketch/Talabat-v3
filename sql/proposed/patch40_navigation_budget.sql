-- PROPOSED patch 40 (navigation budget) — NOT applied. Apply only after owner approval. Safe to run again.
-- One durable, project-wide routing budget shared by ALL drivers, cities and Edge Function instances.
-- Called only by the Edge Function «route» with the service-role key, BEFORE every upstream routing request:
--   navigation_reserve_budget(p_provider, p_credits, p_daily_cap, p_rps, p_request_id)
--   -> {"allowed":true} | {"allowed":false,"reason":"quota"|"rate"|"bad_value","retryAfterS":n}
-- Window: rolling 24 hours, counted as the current hour + the 24 previous hour buckets (never shorter than 24 h). The provider does not publish its daily reset time, so a rolling window
--   guarantees that no 24-hour period ever exceeds the cap, whatever the provider's reset moment.
-- Concurrency: one row per provider is locked (FOR UPDATE) for the whole check-and-reserve, so simultaneous requests
--   from any number of instances are serialized; the cap can never be passed by a race.
-- Idempotent by request id: a repeated id returns the first decision and never reserves twice.
-- Hard limits inside SQL as well (the caller cannot raise them): daily cap <= 3000, rps <= 5, credits per request <= 100.
-- No refund on ambiguous upstream errors (the function never gives credits back). Zero-credit calls (cache hits) are still
--   refused once the window is exhausted, and do not count against the per-second rate.
-- No change to orders, dispatch, accounts, finance, or existing tables / policies. New tables are closed to anon /
--   authenticated (RLS on, no policies, privileges revoked — also TRUNCATE, which RLS does not cover).

create table if not exists public.navigation_budget_state (
  provider   text primary key check (provider in ('geoapify')),
  sec        timestamptz not null default to_timestamp(0),
  sec_count  integer     not null default 0
);
create table if not exists public.navigation_budget_hours (
  provider   text        not null references public.navigation_budget_state(provider),
  hour       timestamptz not null,
  credits    integer     not null default 0 check (credits >= 0),
  primary key (provider, hour)
);
create table if not exists public.navigation_budget_requests (
  request_id    uuid primary key,
  provider      text        not null,
  credits       integer     not null,
  allowed       boolean     not null,
  reason        text,
  retry_after_s integer,
  created_at    timestamptz not null default now()
);
create index if not exists navigation_budget_requests_created_idx on public.navigation_budget_requests (created_at);

alter table public.navigation_budget_state    enable row level security;
alter table public.navigation_budget_hours    enable row level security;
alter table public.navigation_budget_requests enable row level security;
revoke all on table public.navigation_budget_state, public.navigation_budget_hours, public.navigation_budget_requests
  from public, anon, authenticated;

insert into public.navigation_budget_state (provider) values ('geoapify') on conflict do nothing;

create or replace function public.navigation_reserve_budget(
  p_provider text, p_credits integer, p_daily_cap integer, p_rps integer, p_request_id uuid)
returns jsonb
language plpgsql
security invoker
set search_path = public
as $$
declare
  v_now     timestamptz := clock_timestamp();
  v_sec     timestamptz := date_trunc('second', v_now);
  v_hour    timestamptz := date_trunc('hour', v_now);
  v_cap     integer;
  v_rps     integer;
  v_used    integer;
  v_oldest  timestamptz;
  v_state   public.navigation_budget_state%rowtype;
  v_prev    public.navigation_budget_requests%rowtype;
  v_result  jsonb;
begin
  if p_provider is null or p_request_id is null or p_credits is null or p_credits < 0 or p_credits > 100
     or p_daily_cap is null or p_daily_cap < 0 or p_rps is null or p_rps < 1 then
    return jsonb_build_object('allowed', false, 'reason', 'bad_value', 'retryAfterS', 300);
  end if;
  v_cap := least(p_daily_cap, 3000);
  v_rps := least(p_rps, 5);

  -- serialize every reservation of this provider (all instances, all cities)
  select * into v_state from public.navigation_budget_state where provider = p_provider for update;
  if not found then
    return jsonb_build_object('allowed', false, 'reason', 'bad_value', 'retryAfterS', 300);
  end if;

  -- idempotency: same request id -> same answer, nothing reserved twice
  select * into v_prev from public.navigation_budget_requests where request_id = p_request_id;
  if found then
    return case when v_prev.allowed then jsonb_build_object('allowed', true)
                else jsonb_build_object('allowed', false, 'reason', v_prev.reason, 'retryAfterS', v_prev.retry_after_s) end;
  end if;

  select coalesce(sum(credits), 0), min(hour) into v_used, v_oldest
    from public.navigation_budget_hours
   where provider = p_provider and hour > v_hour - interval '25 hours' and credits > 0;

  if v_used >= v_cap or v_used + p_credits > v_cap then
    v_result := jsonb_build_object('allowed', false, 'reason', 'quota',
      'retryAfterS', greatest(60, least(86400, ceil(extract(epoch from (coalesce(v_oldest, v_hour) + interval '25 hours' - v_now)))::int)));
  elsif p_credits > 0 and v_state.sec = v_sec and v_state.sec_count >= v_rps then
    v_result := jsonb_build_object('allowed', false, 'reason', 'rate', 'retryAfterS', 1);
  else
    if p_credits > 0 then
      update public.navigation_budget_state
         set sec = v_sec, sec_count = case when sec = v_sec then sec_count + 1 else 1 end
       where provider = p_provider;
      insert into public.navigation_budget_hours (provider, hour, credits) values (p_provider, v_hour, p_credits)
        on conflict (provider, hour) do update set credits = public.navigation_budget_hours.credits + excluded.credits;
    end if;
    v_result := jsonb_build_object('allowed', true);
  end if;

  insert into public.navigation_budget_requests (request_id, provider, credits, allowed, reason, retry_after_s)
  values (p_request_id, p_provider, p_credits, (v_result->>'allowed')::boolean, v_result->>'reason', (v_result->>'retryAfterS')::int);

  -- housekeeping, bounded: old request ids and hour buckets outside any window
  delete from public.navigation_budget_requests where created_at < v_now - interval '3 days';
  delete from public.navigation_budget_hours where provider = p_provider and hour < v_hour - interval '3 days';
  return v_result;
end $$;

revoke all on function public.navigation_reserve_budget(text, integer, integer, integer, uuid) from public, anon, authenticated;
grant execute on function public.navigation_reserve_budget(text, integer, integer, integer, uuid) to service_role;
grant select, insert, update, delete on table public.navigation_budget_state, public.navigation_budget_hours,
  public.navigation_budget_requests to service_role;

-- Read-only usage view for the owner (SQL Editor): credits reserved in the last 24 h.
--   select coalesce(sum(credits),0) from public.navigation_budget_hours where hour > date_trunc('hour', now()) - interval '25 hours';
-- Rollback: drop function public.navigation_reserve_budget(text,integer,integer,integer,uuid);
--           drop table public.navigation_budget_requests, public.navigation_budget_hours, public.navigation_budget_state;
