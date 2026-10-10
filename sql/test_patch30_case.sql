-- one scenario of test_patch30.sql (variable :scen)
drop schema if exists auth cascade; drop schema public cascade; create schema public; grant usage on schema public to public;
do $$ begin create role anon; exception when duplicate_object then null; end $$;
do $$ begin create role authenticated; exception when duplicate_object then null; end $$;
grant usage on schema public to anon, authenticated; grant usage on schema r30 to authenticated; grant all on all tables in schema r30 to authenticated; grant all on all sequences in schema r30 to authenticated;
create schema auth; grant usage on schema auth to anon, authenticated;
create function auth.uid() returns uuid language sql stable as $$ select nullif(current_setting('request.jwt.claim.sub', true), '')::uuid $$;
grant execute on function auth.uid() to anon, authenticated;
create table promo_attempts (id bigint generated always as identity, user_id uuid, code text, ok boolean, at timestamptz default now());
create table scen(v text); insert into scen values (:'scen');
create function check_promo(p_code text, p_store uuid, p_items jsonb) returns jsonb
language plpgsql security definer set search_path = public as $$
declare c text := upper(trim(p_code)); v text := (select v from scen);
begin
  if p_store = '00000000-0000-0000-0000-0000000000cc' then raise exception 'closed'; end if;
  if c = 'GOOD' then insert into promo_attempts(user_id, code, ok) values (auth.uid(), c, true); return '{"ok":true,"discount":5,"base":50}'::jsonb; end if;
  if c = 'MINC' then return '{"ok":false,"error":"promo_min","min":100,"have":40}'::jsonb; end if;
  insert into promo_attempts(user_id, code, ok) values (auth.uid(), c, false);
  if v = 'B' then return '{"ok":false,"error":"invalid"}'::jsonb; end if;
  if v = 'C' then raise exception 'not_found'; end if;
  raise exception 'promo_invalid';
end $$;
grant execute on function check_promo(text, uuid, jsonb) to authenticated;
create function try(uid text, code text, store text default '00000000-0000-0000-0000-0000000000aa') returns text language plpgsql as $f$
declare r text;
begin perform set_config('request.jwt.claim.sub', uid, true); set local role authenticated;
  begin r := check_promo(code, store::uuid, '[]'::jsonb)::text; exception when others then r := 'ERR:' || sqlerrm; end; reset role; return r; end $f$;
create function chk(label text, cond boolean, got text default '') returns void language sql as $$ insert into r30.res(ok, scen, label, got) values (coalesce(cond, false), (select v from scen), label, got) $$;
select (:'scen' = 'A28') as with28 \gset
\if :with28
\i sql/schema_patch28.sql
\endif
\i sql/schema_patch30.sql
\i sql/schema_patch30.sql
do $$ declare i int; r text; first_block int := null; r10 text;
begin for i in 1..13 loop r := try('a0000000-0000-0000-0000-000000000001', 'ZZ' || i); if i = 10 then r10 := r; end if; if r like '%too_many%' and first_block is null then first_block := i; end if; end loop;
  perform chk('wrong codes blocked at the 11th', first_block = 11, coalesce(first_block::text, 'never') || ' / 10th: ' || r10); end $$;
select try('b0000000-0000-0000-0000-000000000002', 'good') as good \gset
select chk('other user: real code works and is recorded for place_order', :'good' like '%"ok": true%' and exists(select 1 from promo_attempts where user_id = 'b0000000-0000-0000-0000-000000000002' and ok), :'good');
do $$ declare i int; r text; seen boolean := false;
begin for i in 1..15 loop r := try('c0000000-0000-0000-0000-000000000003', 'MINC'); if r like '%too_many%' then seen := true; end if; end loop;
  perform chk('real code below its minimum: never blocked (15x)', not seen and r like '%promo_min%', r); end $$;
do $$ declare i int; r text; seen boolean := false;
begin for i in 1..12 loop r := try('d0000000-0000-0000-0000-000000000004', 'X' || i, '00000000-0000-0000-0000-0000000000cc'); if r like '%too_many%' then seen := true; end if; end loop;
  perform chk('restaurant closed: answered "closed", not counted as guesses', not seen and r like '%closed%', r); end $$;
do $$ declare r text;
begin perform set_config('request.jwt.claim.sub', 'a0000000-0000-0000-0000-000000000001', true); set local role authenticated;
  begin r := check_promo_base('ZZ', '00000000-0000-0000-0000-0000000000aa'::uuid, '[]'::jsonb)::text; exception when others then r := 'ERR:' || sqlerrm; end;
  reset role; perform chk('no bypass: check_promo_base closed', r like 'ERR:permission denied%', r); end $$;
