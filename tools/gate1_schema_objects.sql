-- LOCAL or authorized-target schema-only metadata; no application rows queried.
WITH target_functions(name,signature) AS (
 VALUES ('driver_ping','public.driver_ping(boolean)'),
        ('deliver_order','public.deliver_order(bigint,numeric,text,text)'),
        ('report_driver_cash_short','public.report_driver_cash_short(bigint,numeric,text)')
),
fn AS (
 SELECT t.name,p.oid,p.proowner,p.prosecdef,p.proconfig,p.proacl
 FROM (SELECT name,to_regprocedure(signature)::oid AS oid FROM target_functions) t
 LEFT JOIN pg_catalog.pg_proc p ON p.oid=t.oid
),
target_indexes(name) AS (VALUES ('tickets_one_open_per_order'),('tickets_one_open_payment_per_order'))
SELECT jsonb_build_object(
 'functions',(SELECT jsonb_object_agg(f.name,
  CASE WHEN f.oid IS NULL THEN NULL ELSE jsonb_build_object(
   'definition',pg_catalog.pg_get_functiondef(f.oid),
   'return',pg_catalog.pg_get_function_result(f.oid),
   'owner',pg_catalog.pg_get_userbyid(f.proowner),
   'security_definer',f.prosecdef,
   'config',to_jsonb(f.proconfig),
   'authenticated_execute',has_function_privilege('authenticated',f.oid,'EXECUTE'),
   'anon_execute',has_function_privilege('anon',f.oid,'EXECUTE'),
   'service_role_execute',has_function_privilege('service_role',f.oid,'EXECUTE'),
   'public_execute',coalesce((SELECT bool_or(a.grantee=0 AND a.privilege_type='EXECUTE')
    FROM pg_catalog.aclexplode(coalesce(f.proacl,pg_catalog.acldefault('f',f.proowner))) a),false)
  ) END) FROM fn f),
 'indexes',(SELECT jsonb_object_agg(t.name,CASE WHEN i.oid IS NULL THEN NULL ELSE pg_catalog.pg_get_indexdef(i.oid) END)
  FROM target_indexes t LEFT JOIN pg_catalog.pg_class i
   ON i.relname=t.name AND i.relnamespace='public'::regnamespace AND i.relkind='i')
)::text;
