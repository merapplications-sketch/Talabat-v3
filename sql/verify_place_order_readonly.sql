-- READ-ONLY (31 Oct): every live definition of public.place_order (all overloads) and the lines where the free-delivery
-- threshold is applied. Nothing is changed. Run as the default role in Supabase → SQL Editor; ONE statement; send the CSV.
-- One «definition» row per overload (signature + total lines), then each line that mentions free_delivery_min or fee_waived.
select p.oid::regprocedure::text as signature, 0 as line_no,
       'definition ' || row_number() over (order by p.oid) || ' of ' || count(*) over () || ' · ' ||
       array_length(string_to_array(pg_get_functiondef(p.oid), E'\n'), 1) || ' lines' as line
  from pg_proc p join pg_namespace n on n.oid = p.pronamespace
 where n.nspname = 'public' and p.proname = 'place_order'
union all
select p.oid::regprocedure::text, l.n::int, btrim(l.line)
  from pg_proc p join pg_namespace n on n.oid = p.pronamespace,
       regexp_split_to_table(pg_get_functiondef(p.oid), E'\n') with ordinality as l(line, n)
 where n.nspname = 'public' and p.proname = 'place_order'
   and (l.line ilike '%free_delivery_min%' or l.line ilike '%fee_waived%' or l.line ilike '%v_waived%')
order by 1, 2;
