-- READ-ONLY (24 Oct 2026): settles the TRUNCATE note. Changes nothing. Run once, export CSV.
-- 1) every public table where anon / authenticated hold TRUNCATE, TRIGGER or REFERENCES;
-- 2) whether those roles can log in (a direct SQL session) or bypass RLS;
-- 3) functions anon / authenticated may execute whose body runs TRUNCATE or dynamic SQL (the only API path to use it).
select 'grant' as kind, table_name as name, grantee||' · '||string_agg(privilege_type, ',' order by privilege_type) as detail
from information_schema.role_table_grants
where table_schema='public' and grantee in ('anon','authenticated') and privilege_type in ('TRUNCATE','TRIGGER','REFERENCES')
group by table_name, grantee
union all
select 'role', rolname, 'login='||rolcanlogin||' bypassrls='||rolbypassrls||' super='||rolsuper
from pg_roles where rolname in ('anon','authenticated','service_role','authenticator')
union all
select 'function_path', p.proname,
       'definer='||p.prosecdef||' · anon='||has_function_privilege('anon', p.oid, 'execute')||' · authenticated='||has_function_privilege('authenticated', p.oid, 'execute')
from pg_proc p
where p.pronamespace='public'::regnamespace
  and (p.prosrc ~* '\mtruncate\M' or p.prosrc ~* '\mexecute\M\s+(format|''|\$|[a-z_]+\s*\|\|)')
  and (has_function_privilege('anon', p.oid, 'execute') or has_function_privilege('authenticated', p.oid, 'execute'))
union all
select 'default_privileges', coalesce(nspname,'*'), array_to_string(defaclacl, ' ')
from pg_default_acl d left join pg_namespace n on n.oid=d.defaclnamespace
where d.defaclobjtype='r' and (nspname='public' or nspname is null)
order by 1,2;
