-- Gate1 schema-only read: exact function definitions, return signatures, security and grants + index DDL.
-- No SELECT against application/auth/storage table rows.
WITH target_functions(name,signature) AS (
 VALUES ('driver_ping','public.driver_ping(boolean)'),
        ('deliver_order','public.deliver_order(bigint,numeric,text,text)'),
        ('report_driver_cash_short','public.report_driver_cash_short(bigint,numeric,text)')
),
function_objects AS (
 SELECT wanted.name, p.oid, p.prosecdef, p.proowner, p.proconfig, p.proacl
 FROM (SELECT name, to_regprocedure(signature)::oid AS oid FROM target_functions) wanted
 LEFT JOIN pg_proc p ON p.oid=wanted.oid
),
target_indexes(name) AS (VALUES ('tickets_one_open_per_order'),('tickets_one_open_payment_per_order'))
SELECT jsonb_build_object(
  'functions',(SELECT jsonb_object_agg(f.name,
   CASE WHEN f.oid IS NULL THEN NULL ELSE jsonb_build_object(
     'definition',pg_get_functiondef(f.oid),
     'return',pg_get_function_result(f.oid),
     'owner',pg_get_userbyid(f.proowner),
     'security_definer',f.prosecdef,
     'config',to_jsonb(f.proconfig),
     'authenticated_execute',has_function_privilege('authenticated',f.oid,'EXECUTE'),
     'anon_execute',has_function_privilege('anon',f.oid,'EXECUTE'),
     'service_role_execute',has_function_privilege('service_role',f.oid,'EXECUTE'),
     'public_execute',coalesce((SELECT bool_or(a.grantee=0 AND a.privilege_type='EXECUTE')
       FROM aclexplode(coalesce(f.proacl,acldefault('f',f.proowner))) a),false)
   ) END
  ) FROM function_objects f),
  'indexes',(SELECT jsonb_object_agg(t.name,CASE WHEN idx.oid IS NULL THEN NULL ELSE pg_get_indexdef(idx.oid) END)
    FROM target_indexes t
    LEFT JOIN pg_class idx ON idx.relname=t.name
       AND idx.relnamespace='public'::regnamespace
       AND idx.relkind='i')
)::text;
