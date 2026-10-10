-- =============================================================================================
-- PATCH 30 — promo-code guessing limit, robust version (replaces patch 28's guard; safe to run
-- whether patch 28 / 29 were run or not, and safe to run again).
--
-- Why: the security check still reported "13 wrong codes were not blocked". Patch 28 counted a
-- wrong code only when the old check answered exactly "promo_invalid". If the old check says it
-- another way (another error word, or an error that is not about promos at all), nothing was
-- counted. Now it is the other way round: EVERY answer that is not a success counts as a wrong
-- guess, except the few answers that prove the code is real (below its minimum, already used,
-- limit reached, not for discounted dishes) or that have nothing to do with the code
-- (restaurant closed, dish unavailable ...). Errors are answered, never thrown, so the counted
-- attempt is never rolled back. Limits: 10 wrong codes or 60 checks per 10 minutes.
-- =============================================================================================

create table if not exists promo_guess (
  id bigint generated always as identity primary key,
  user_id uuid not null,
  at timestamptz not null default now(),
  bad boolean not null
);
create index if not exists promo_guess_user_at_idx on promo_guess (user_id, at desc);
alter table promo_guess enable row level security;
revoke all on table promo_guess from public, anon, authenticated;

-- keep the ORIGINAL check under another name, only the first time (patch 28 may already have done it)
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
  for r in select p.oid::regprocedure as sig from pg_proc p join pg_namespace n on n.oid = p.pronamespace
            where n.nspname = 'public' and p.proname = 'check_promo_base' loop
    execute format('revoke all on function %s from public, anon, authenticated', r.sig);
  end loop;
end $$;

create or replace function check_promo(p_code text, p_store uuid, p_items jsonb) returns jsonb
language plpgsql security definer set search_path = public as $$
declare
  v_uid uuid := auth.uid();
  v_bad int; v_all int; v_hh int := 0;
  v_res jsonb; v_err text; v_key text; v_ok boolean;
begin
  if v_uid is null then raise exception 'auth'; end if;
  perform pg_advisory_xact_lock(hashtext('promo_guess:' || v_uid::text));

  select count(*) filter (where bad), count(*) into v_bad, v_all
    from promo_guess where user_id = v_uid and at > now() - interval '10 minutes';
  if v_bad >= 10 or v_all >= 60 then raise exception 'too_many'; end if;

  -- during a happy hour (patch 29) every dish already has a discount: promo codes never apply then
  if to_regproc('public.happy_hour_pct') is not null then
    execute 'select happy_hour_pct($1)' into v_hh using p_store;
    if coalesce(v_hh, 0) > 0 then return jsonb_build_object('ok', false, 'error', 'promo_offer'); end if;
  end if;

  begin
    v_res := to_jsonb(check_promo_base(p_code, p_store, p_items));
  exception when others then
    v_err := sqlerrm;
  end;
  if v_err is not null then
    if v_err ~* 'too_many' then raise exception 'too_many'; end if;
    v_key := coalesce(substring(v_err from '([a-z]+_[a-z_]+)'), substring(v_err from '([a-z_]+)'), 'promo_invalid');
    v_res := jsonb_build_object('ok', false, 'error', v_key);       -- answered, not thrown: the attempt below is kept
  end if;

  v_ok := coalesce((v_res->>'ok')::boolean, false);
  v_key := lower(coalesce(v_res->>'error', ''));
  insert into promo_guess(user_id, bad)
  values (v_uid, not v_ok and v_key !~ '^(promo_min|promo_used|promo_limit|promo_offer|promo_expired|closed|store_unavailable|unavailable|bad_options|empty|account_blocked|phone_required|auth)$');
  delete from promo_guess where user_id = v_uid and at < now() - interval '1 day';
  return v_res;
end $$;
revoke all on function check_promo(text, uuid, jsonb) from public, anon;
grant execute on function check_promo(text, uuid, jsonb) to authenticated;

-- for the security page: is this guard installed? (true/false only, no data)
create or replace function promo_guard_version() returns int language sql stable as $$ select 30 $$;
grant execute on function promo_guard_version() to authenticated;
