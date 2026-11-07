-- Re-run only after relevant permission/function changes. No persistent writes.
begin read only;
set local role anon;
do $$ declare n text;e text;r jsonb:='{}';begin
 foreach n in array array['best_dishes(null,1)','brand_route(null,0,0)','cash_balances()','contacts_for(array[-34001]::bigint[])','ticket_refund_room(-34001)','dispatch_tick()'] loop
  e:=null;begin execute 'select * from public.'||n;exception when insufficient_privilege then e:=sqlstate;end;
  if e is distinct from '42501' then raise exception 'Unexpected anonymous access: %',n;end if;
  r:=r||jsonb_build_object(n,e);
 end loop;perform set_config('test.anon_ops',r::text,true);
end $$;
reset role;select current_setting('test.anon_ops')::jsonb as denied;
rollback;

begin read only;
set local role authenticated;
select set_config('request.jwt.claims','{"sub":"85fea11e-738c-4221-ac29-51d4ff50d594","role":"authenticated","aal":"aal2"}',true);
select account_enabled() as synthetic_enabled,has_perm('finance') as finance_permission,has_perm('orders') as orders_permission,has_perm('support') as support_permission,
 (select count(*) from cash_balances()) as cash_rows,
 (select count(*) from contacts_for(array[-34001]::bigint[])) as contact_rows,
 (select count(*) from ticket_refund_room(-34001)) as refund_rows,
 (select count(*)<=1 from best_dishes(null,1)) as catalogue_call_allowed_bounded;
rollback;
