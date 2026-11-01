-- REVIEW ONLY / NOT EXECUTED LIVE HERE. SELECT-only inventory, no rows or credentials.
-- Run statements separately if the editor shows only its final result.
select table_name,column_name,data_type,udt_name from information_schema.columns
where table_schema='public' and table_name in ('orders','profiles','staff_members','wallet_entries','audit_log') order by table_name,ordinal_position;
select n.nspname,p.proname,pg_get_function_identity_arguments(p.oid) arguments,p.prosecdef,p.proacl,pg_get_functiondef(p.oid) definition
from pg_proc p join pg_namespace n on n.oid=p.pronamespace
where n.nspname='public' and p.prokind='f' and (p.prosecdef or p.proname in ('wallet_balance','cash_balances','has_perm')) order by p.proname,arguments;
select table_name,grantee,privilege_type from information_schema.table_privileges where table_schema='public' and table_name in ('orders','wallet_entries','staff_members','profiles','audit_log') order by table_name,grantee;
select table_name,column_name,grantee,privilege_type from information_schema.column_privileges where table_schema='public' and table_name in ('orders','wallet_entries') order by table_name,column_name;
select * from pg_policies where schemaname='public' and tablename in ('orders','wallet_entries','staff_members','profiles','audit_log');
select c.relname,t.tgname,pg_get_triggerdef(t.oid) definition from pg_trigger t join pg_class c on c.oid=t.tgrelid join pg_namespace n on n.oid=c.relnamespace where n.nspname='public' and not t.tgisinternal and c.relname in ('orders','wallet_entries','staff_members');
-- Effective grants include PUBLIC and inherited roles; information_schema alone is insufficient.
select r.rolname,c.oid::regclass relation,
 has_table_privilege(r.oid,c.oid,'INSERT') can_insert,
 has_table_privilege(r.oid,c.oid,'UPDATE') can_update,
 has_table_privilege(r.oid,c.oid,'DELETE') can_delete
from pg_roles r cross join pg_class c join pg_namespace n on n.oid=c.relnamespace
where r.rolname in ('anon','authenticated') and n.nspname='public'
 and c.relname in ('orders','wallet_entries','staff_members','audit_log');
select r.rolname,c.oid::regclass relation,a.attname,
 has_column_privilege(r.oid,c.oid,a.attnum,'INSERT') can_insert,
 has_column_privilege(r.oid,c.oid,a.attnum,'UPDATE') can_update
from pg_roles r cross join pg_class c join pg_namespace n on n.oid=c.relnamespace
join pg_attribute a on a.attrelid=c.oid and a.attnum>0 and not a.attisdropped
where r.rolname in ('anon','authenticated') and n.nspname='public'
 and c.relname in ('orders','wallet_entries');
select n.nspname,p.oid::regprocedure signature,r.rolname,
 has_function_privilege(r.oid,p.oid,'EXECUTE') effective_execute,
 pg_get_functiondef(p.oid) definition
from pg_proc p join pg_namespace n on n.oid=p.pronamespace cross join pg_roles r
where p.prokind='f' and n.nspname in ('public','finance_private')
 and r.rolname in ('anon','authenticated') and
 (p.prosecdef or p.proname ~ 'finance|settle|wallet|payout|ticket_set_status|deliver_order');
select current_setting('server_version') server_version;
