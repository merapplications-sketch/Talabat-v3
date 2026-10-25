-- PROPOSED patch 40 (navigation budget) — NOT applied. Apply only after owner approval. Safe to run again.
-- One durable routing budget for ALL drivers, cities and Edge Function instances, used only by the Edge Function «route»
-- with the service key:
--   navigation_reserve_budget(p_provider, p_credits, p_daily_cap, p_rps, p_request_id)   BEFORE every upstream request
--     -> {"allowed":true} | {"allowed":false,"reason":"quota"|"rate"|"bad_value","retryAfterS":n}
--   navigation_settle_budget(p_provider, p_request_id, p_total_credits)                    AFTER EVERY upstream call
--     -> closes THAT reservation (same request id) with its real total; books any excess truthfully (even above the cap:
--        the next reservations are then refused); keeps the reservation when the total is lower (no refund).
--     -> {"recorded":true[,"repeat":true],"extra":n} | {"recorded":false,"reason":"unknown_request"|"conflict"|"bad_value"}
-- Unsettled guard: a paid reservation not settled within 60 s (crash, RPC failure, lost answer) blocks EVERY further
--   reservation, all instances, with reason «unsettled» until it is settled (owner: see the end of this file).
-- Time: read AFTER the provider row lock is held, so a request that waited for the lock is booked in the hour / second in
--   which it really passes (not the moment it started waiting). Read through navigation_budget_clock() (= clock_timestamp()).
-- Window: rolling — current hour + the 24 previous hour buckets (never shorter than 24 h); the provider does not publish its
--   daily reset moment, so no 24-hour period can exceed the cap.
-- Concurrency: one row per provider locked FOR UPDATE for the whole check-and-book; idempotent by request id.
-- Hard limits inside SQL (caller cannot raise them): cap <= 3000, rps <= 5, credits per call <= 100. Cap 0 = routing stopped.
-- No refund on ambiguous errors. Zero-credit checks (cache) are refused once exhausted and do not count towards the rate.
-- SCOPE OF THE GUARANTEE: only requests that go through this proxy are counted. Any other use of the same Geoapify account
--   (other keys / apps, map tiles, geocoding, dashboard playground) is invisible here; keep a dedicated Geoapify project
--   and key for TALABOT routing only and keep dailyCredits below the account allowance (3 000) to leave room for it.
-- New tables are closed to anon / authenticated: RLS on, no policies, all privileges revoked (incl. TRUNCATE).
-- No change to orders, dispatch, accounts, finance, or existing tables / policies.

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
-- settlement of a paid reservation (added after review of f174ce9); refused / zero-credit rows need none
alter table public.navigation_budget_requests add column if not exists settled       boolean not null default true;
alter table public.navigation_budget_requests add column if not exists final_credits integer;
alter table public.navigation_budget_requests add column if not exists settled_at    timestamptz;
create index if not exists navigation_budget_requests_unsettled_idx
  on public.navigation_budget_requests (provider, created_at) where not settled;
create index if not exists navigation_budget_requests_created_idx on public.navigation_budget_requests (created_at);

alter table public.navigation_budget_state    enable row level security;
alter table public.navigation_budget_hours    enable row level security;
alter table public.navigation_budget_requests enable row level security;
revoke all on table public.navigation_budget_state, public.navigation_budget_hours, public.navigation_budget_requests
  from public, anon, authenticated;
insert into public.navigation_budget_state (provider) values ('geoapify') on conflict do nothing;

create or replace function public.navigation_budget_clock() returns timestamptz
language sql volatile security invoker set search_path = public as $$ select clock_timestamp() $$;

create or replace function public.navigation_reserve_budget(
  p_provider text, p_credits integer, p_daily_cap integer, p_rps integer, p_request_id uuid)
returns jsonb
language plpgsql
security invoker
set search_path = public
as $$
declare
  v_now timestamptz; v_sec timestamptz; v_hour timestamptz;
  v_cap integer; v_rps integer; v_used integer; v_oldest timestamptz;
  v_state public.navigation_budget_state%rowtype;
  v_prev  public.navigation_budget_requests%rowtype;
  v_result jsonb;
begin
  if p_provider is null or p_request_id is null or p_credits is null or p_credits < 0 or p_credits > 100
     or p_daily_cap is null or p_daily_cap < 0 or p_rps is null or p_rps < 1 then
    return jsonb_build_object('allowed', false, 'reason', 'bad_value', 'retryAfterS', 300);
  end if;
  v_cap := least(p_daily_cap, 3000);
  v_rps := least(p_rps, 5);

  select * into v_state from public.navigation_budget_state where provider = p_provider for update;
  if not found then
    return jsonb_build_object('allowed', false, 'reason', 'bad_value', 'retryAfterS', 300);
  end if;
  -- time is taken only now, with the lock held
  v_now := public.navigation_budget_clock(); v_sec := date_trunc('second', v_now); v_hour := date_trunc('hour', v_now);

  select * into v_prev from public.navigation_budget_requests where request_id = p_request_id;
  if found then
    return case when v_prev.allowed then jsonb_build_object('allowed', true)
                else jsonb_build_object('allowed', false, 'reason', v_prev.reason, 'retryAfterS', v_prev.retry_after_s) end;
  end if;

  select coalesce(sum(credits), 0), min(hour) into v_used, v_oldest
    from public.navigation_budget_hours
   where provider = p_provider and hour > v_hour - interval '25 hours' and credits > 0;

  if exists (select 1 from public.navigation_budget_requests
              where provider = p_provider and allowed and not settled and created_at < v_now - interval '60 seconds') then
    -- an earlier upstream call has an unconfirmed cost: no new use (cache included) until it is settled
    v_result := jsonb_build_object('allowed', false, 'reason', 'unsettled', 'retryAfterS', 300);
  elsif v_used >= v_cap or v_used + p_credits > v_cap then
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

  insert into public.navigation_budget_requests (request_id, provider, credits, allowed, reason, retry_after_s, created_at, settled)
  values (p_request_id, p_provider, p_credits, (v_result->>'allowed')::boolean, v_result->>'reason',
          (v_result->>'retryAfterS')::int, v_now, not ((v_result->>'allowed')::boolean and p_credits > 0));
  -- bounded housekeeping: SETTLED request ids older than 3 days only (unsettled rows and hour buckets are kept)
  delete from public.navigation_budget_requests where created_at < v_now - interval '3 days' and settled;
  return v_result;
end $$;

drop function if exists public.navigation_settle_budget(text, integer, uuid);   -- first proposal (f174ce9), never applied live
create or replace function public.navigation_settle_budget(p_provider text, p_request_id uuid, p_total_credits integer)
returns jsonb
language plpgsql
security invoker
set search_path = public
as $$
declare v_now timestamptz; v_hour timestamptz; v_req public.navigation_budget_requests%rowtype; v_final integer; v_extra integer;
begin
  if p_provider is null or p_request_id is null or p_total_credits is null or p_total_credits < 1 or p_total_credits > 100 then
    return jsonb_build_object('recorded', false, 'reason', 'bad_value');
  end if;
  perform 1 from public.navigation_budget_state where provider = p_provider for update;
  if not found then return jsonb_build_object('recorded', false, 'reason', 'bad_value'); end if;
  v_now := public.navigation_budget_clock(); v_hour := date_trunc('hour', v_now);
  select * into v_req from public.navigation_budget_requests where request_id = p_request_id for update;
  -- only a paid, allowed reservation of this provider can be settled (binds the settlement to that route call)
  if not found or v_req.provider <> p_provider or not v_req.allowed or v_req.credits < 1 then
    return jsonb_build_object('recorded', false, 'reason', 'unknown_request');
  end if;
  v_final := greatest(p_total_credits, v_req.credits);          -- never below the reservation (no refund)
  if v_req.settled then
    return case when v_req.final_credits = v_final then jsonb_build_object('recorded', true, 'repeat', true, 'extra', 0)
                else jsonb_build_object('recorded', false, 'reason', 'conflict') end;
  end if;
  v_extra := v_final - v_req.credits;
  if v_extra > 0 then
    insert into public.navigation_budget_hours (provider, hour, credits) values (p_provider, v_hour, v_extra)
      on conflict (provider, hour) do update set credits = public.navigation_budget_hours.credits + excluded.credits;
  end if;
  update public.navigation_budget_requests set settled = true, final_credits = v_final, settled_at = v_now
   where request_id = p_request_id;
  return jsonb_build_object('recorded', true, 'extra', v_extra);
end $$;

revoke all on function public.navigation_budget_clock() from public, anon, authenticated;
revoke all on function public.navigation_reserve_budget(text, integer, integer, integer, uuid) from public, anon, authenticated;
revoke all on function public.navigation_settle_budget(text, uuid, integer) from public, anon, authenticated;
grant execute on function public.navigation_budget_clock() to service_role;
grant execute on function public.navigation_reserve_budget(text, integer, integer, integer, uuid) to service_role;
grant execute on function public.navigation_settle_budget(text, uuid, integer) to service_role;
grant select, insert, update, delete on table public.navigation_budget_state, public.navigation_budget_hours,
  public.navigation_budget_requests to service_role;

-- Usage (owner, SQL Editor, read-only): credits booked in the current window
--   select coalesce(sum(credits),0) from public.navigation_budget_hours where hour > date_trunc('hour', now()) - interval '25 hours';
-- Unsettled guard, owner recovery (SQL Editor): list  select request_id, created_at from public.navigation_budget_requests
--   where not settled;  then close each one with the credits shown for that day in the Geoapify dashboard, or at least 1:
--   select public.navigation_settle_budget('geoapify', '<request_id>', <credits>);
-- Default rollback = DISABLE, keep the record: sql/proposed/patch40_disable.sql (no table dropped, no booking reset).
