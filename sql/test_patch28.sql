-- Self-contained test for patch 28 on an EMPTY local PostgreSQL (not Supabase):
--   psql -v ON_ERROR_STOP=0 -f sql/test_patch28.sql   (then: psql -f sql/schema_patch28.sql is included below)
-- It builds a tiny stand-in for the real database (auth.uid(), promo_attempts, and an "old" check_promo that
-- has exactly the reported bug: the failed attempt it records is rolled back by its own error), proves the bug,
-- applies patch 28 twice, and checks the new behaviour. Prints a summary line "PATCH28 n/n".
\set QUIET on
\pset tuples_only on
drop schema if exists auth cascade; drop schema public cascade; create schema public; grant usage on schema public to public;
do $$ begin create role anon; exception when duplicate_object then null; end $$;
do $$ begin create role authenticated; exception when duplicate_object then null; end $$;
grant usage on schema public to anon, authenticated;
create schema auth; grant usage on schema auth to anon, authenticated;
create function auth.uid() returns uuid language sql stable as $$ select nullif(current_setting('request.jwt.claim.sub', true), '')::uuid $$;
grant execute on function auth.uid() to anon, authenticated;

create table promo_attempts (id bigint generated always as identity, user_id uuid, code text, ok boolean, at timestamptz default now());
-- the OLD function, with the bug: it counts failed attempts, but the error it raises undoes the row it just wrote
create function check_promo(p_code text, p_store uuid, p_items jsonb) returns jsonb
language plpgsql security definer set search_path = public as $$
declare c text := upper(trim(p_code));
begin
  if p_store = '00000000-0000-0000-0000-0000000000cc' then raise exception 'closed'; end if;
  if (select count(*) from promo_attempts where user_id = auth.uid() and not ok and at > now() - interval '10 minutes') >= 10 then raise exception 'too_many'; end if;
  if c = 'GOOD' then insert into promo_attempts(user_id, code, ok) values (auth.uid(), c, true); return jsonb_build_object('ok', true, 'discount', 5, 'base', 50); end if;
  if c = 'MINC' then return jsonb_build_object('ok', false, 'error', 'promo_min', 'min', 100, 'have', 40); end if;
  insert into promo_attempts(user_id, code, ok) values (auth.uid(), c, false);
  raise exception 'promo_invalid';
end $$;
grant execute on function check_promo(text, uuid, jsonb) to authenticated;

create table res(n serial, ok boolean, label text, got text);
create function try(uid text, code text, store text default '00000000-0000-0000-0000-0000000000aa') returns text language plpgsql as $f$
declare r text;
begin
  perform set_config('request.jwt.claim.sub', uid, true);
  set local role authenticated;
  begin r := check_promo(code, store::uuid, '[]'::jsonb)::text; exception when others then r := 'ERR:' || sqlerrm; end;
  reset role;
  return r;
end $f$;
create function chk(label text, cond boolean, got text) returns void language sql as $$ insert into res(ok, label, got) values (cond, label, got) $$;

-- 1) the bug: 13 wrong codes, never blocked
do $$ declare i int; r text; seen boolean := false;
begin for i in 1..13 loop r := try('a0000000-0000-0000-0000-000000000001', 'ZZ' || i); if r like '%too_many%' then seen := true; end if; end loop;
  perform chk('BEFORE patch: 13 wrong codes are NOT blocked (bug reproduced)', not seen, r); end $$;
delete from promo_attempts;

-- 2) apply the patch twice (must be safe to re-run)
\i sql/schema_patch28.sql
\i sql/schema_patch28.sql
select chk('patch keeps the old function as check_promo_base', to_regproc('public.check_promo_base') is not null, '');

-- 3) user A guesses
do $$ declare i int; r text; r10 text; first_block int := null;
begin for i in 1..13 loop r := try('a0000000-0000-0000-0000-000000000001', 'ZZ' || i); if i = 10 then r10 := r; end if; if r like '%too_many%' and first_block is null then first_block := i; end if; end loop;
  perform chk('AFTER: wrong codes are blocked at attempt 11', first_block = 11, coalesce(first_block::text, 'never'));
  perform chk('AFTER: the 10th wrong code still gets a normal "invalid" answer', r10 like '%promo_invalid%' and r10 not like 'ERR%', r10); end $$;
select chk('blocked user: even a valid code is refused for now', try('a0000000-0000-0000-0000-000000000001', 'GOOD') like '%too_many%', try('a0000000-0000-0000-0000-000000000001', 'GOOD'));

-- 4) another user is not affected; a valid code still works and is recorded for place_order
select chk('other user: valid code works', try('b0000000-0000-0000-0000-000000000002', 'good') like '%"ok": true%', try('b0000000-0000-0000-0000-000000000002', 'good'));
select chk('valid code recorded in promo_attempts (place_order needs it)', exists(select 1 from promo_attempts where user_id = 'b0000000-0000-0000-0000-000000000002' and ok and code = 'GOOD'), '');

-- 5) a REAL code below its minimum, re-checked many times as the cart changes, never locks the customer out
do $$ declare i int; r text; seen boolean := false;
begin for i in 1..15 loop r := try('c0000000-0000-0000-0000-000000000003', 'MINC'); if r like '%too_many%' then seen := true; end if; end loop;
  perform chk('minimum-order answers are not counted as guesses (15x)', not seen and r like '%promo_min%', r); end $$;
-- ... but hammering the check with any code is capped (60 per 10 min)
do $$ declare i int; r text; first_block int := null;
begin for i in 1..70 loop r := try('d0000000-0000-0000-0000-000000000004', 'GOOD'); if r like '%too_many%' and first_block is null then first_block := i; end if; end loop;
  perform chk('any code: capped at 60 checks per 10 minutes', first_block = 61, coalesce(first_block::text, 'never')); end $$;

-- 6) errors that are not about the code are unchanged and not counted
select chk('closed store error passes through unchanged', try('e0000000-0000-0000-0000-000000000005', 'X1', '00000000-0000-0000-0000-0000000000cc') = 'ERR:closed', try('e0000000-0000-0000-0000-000000000005', 'X1', '00000000-0000-0000-0000-0000000000cc'));
select chk('... and not counted', (select count(*) from promo_guess where user_id = 'e0000000-0000-0000-0000-000000000005') = 0, '');

-- 7) no bypass, no reading the counter, no anonymous use
do $$ declare r text;
begin perform set_config('request.jwt.claim.sub', 'a0000000-0000-0000-0000-000000000001', true); set local role authenticated;
  begin r := check_promo_base('ZZ', '00000000-0000-0000-0000-0000000000aa'::uuid, '[]'::jsonb)::text; exception when others then r := 'ERR:' || sqlerrm; end;
  reset role; perform chk('customer cannot call check_promo_base directly', r like 'ERR:permission denied%', r); end $$;
do $$ declare r text;
begin set local role authenticated;
  begin perform count(*) from promo_guess; r := 'readable'; exception when others then r := 'ERR:' || sqlerrm; end;
  reset role; perform chk('customer cannot read promo_guess', r like 'ERR:permission denied%', r); end $$;
do $$ declare r text;
begin set local role anon;
  begin r := check_promo('ZZ', '00000000-0000-0000-0000-0000000000aa'::uuid, '[]'::jsonb)::text; exception when others then r := 'ERR:' || sqlerrm; end;
  reset role; perform chk('anonymous cannot call check_promo', r like 'ERR:permission denied%', r); end $$;

-- 8) the block ends after 10 minutes
update promo_guess set at = at - interval '11 minutes' where user_id = 'a0000000-0000-0000-0000-000000000001';
select chk('after 10 minutes the user can try again', try('a0000000-0000-0000-0000-000000000001', 'GOOD') like '%"ok": true%', try('a0000000-0000-0000-0000-000000000001', 'GOOD'));

\pset tuples_only off
select n, case when ok then 'PASS' else 'FAIL' end as r, label, left(got, 70) as got from res order by n;
select 'PATCH28 ' || count(*) filter (where ok) || '/' || count(*) from res;
