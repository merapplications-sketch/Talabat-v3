-- =============================================================================================
-- PATCH 28 — promo-code guessing is really rate-limited
-- Run once in the Supabase SQL Editor (safe to run again).
--
-- Problem (security-check: "13 wrong codes were not blocked"): a wrong code is answered with an
-- error, and an error rolls back everything the check wrote — including the "failed attempt" row
-- the limit counts. So the counter never grew and guessing was unlimited.
--
-- Fix: the existing check_promo is kept untouched as check_promo_base (all its rules: pricing,
-- minimum order, per-user use, offers ...). A new check_promo in front of it:
--   * counts attempts in its own table promo_guess, OUTSIDE the part that can fail,
--   * blocks with 'too_many' after 10 wrong codes in 10 minutes (or 60 checks of any kind),
--   * a valid code below its minimum / already used is NOT a wrong guess (the cart re-checks
--     the code when it changes; that must never lock a real customer out),
--   * nobody can call check_promo_base directly any more (no bypass).
-- =============================================================================================

create table if not exists promo_guess (
  id bigint generated always as identity primary key,
  user_id uuid not null,
  at timestamptz not null default now(),
  bad boolean not null
);
create index if not exists promo_guess_user_at_idx on promo_guess (user_id, at desc);
alter table promo_guess enable row level security;            -- no policy: invisible through the API
revoke all on table promo_guess from public, anon, authenticated;

-- keep the original function under a new name (only the first time this patch runs)
do $$
declare r record;
begin
  if to_regproc('public.check_promo_base') is null then
    for r in select p.oid::regprocedure as sig from pg_proc p join pg_namespace n on n.oid = p.pronamespace
              where n.nspname = 'public' and p.proname = 'check_promo' loop
      execute format('alter function %s rename to check_promo_base', r.sig);
    end loop;
  end if;
  if to_regproc('public.check_promo_base') is null then
    raise exception 'check_promo was not found: run the earlier patches first';
  end if;
  -- no direct calls: only the guarded check_promo below may use it
  for r in select p.oid::regprocedure as sig from pg_proc p join pg_namespace n on n.oid = p.pronamespace
            where n.nspname = 'public' and p.proname = 'check_promo_base' loop
    execute format('revoke all on function %s from public, anon, authenticated', r.sig);
  end loop;
end $$;

create or replace function check_promo(p_code text, p_store uuid, p_items jsonb) returns jsonb
language plpgsql security definer set search_path = public as $$
declare
  v_uid uuid := auth.uid();
  v_bad int; v_all int;
  v_res jsonb; v_err text; v_key text;
begin
  if v_uid is null then raise exception 'auth'; end if;
  perform pg_advisory_xact_lock(hashtext('promo_guess:' || v_uid::text));   -- parallel taps are counted one by one

  select count(*) filter (where bad), count(*) into v_bad, v_all
    from promo_guess where user_id = v_uid and at > now() - interval '10 minutes';
  if v_bad >= 10 or v_all >= 60 then raise exception 'too_many'; end if;

  begin
    v_res := to_jsonb(check_promo_base(p_code, p_store, p_items));
  exception when others then
    v_err := sqlerrm;
  end;

  if v_err is not null then
    if v_err ~* 'too_many' then raise exception 'too_many'; end if;
    v_key := substring(v_err from '(promo_[a-z_]+)');
    if v_key is null then raise exception '%', v_err; end if;            -- not about the code (closed, unavailable ...): unchanged
    v_res := jsonb_build_object('ok', false, 'error', v_key);            -- answered, so the attempt below is kept
  end if;

  v_key := coalesce(v_res->>'error', '');
  insert into promo_guess(user_id, bad)
  values (v_uid, coalesce((v_res->>'ok')::boolean, false) = false and (v_key = '' or v_key ~* 'promo_invalid'));
  delete from promo_guess where user_id = v_uid and at < now() - interval '1 day';
  return v_res;
end $$;
revoke all on function check_promo(text, uuid, jsonb) from public, anon;
grant execute on function check_promo(text, uuid, jsonb) to authenticated;
