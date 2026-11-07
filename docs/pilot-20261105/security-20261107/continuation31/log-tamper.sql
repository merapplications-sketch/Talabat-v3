begin;set local lock_timeout='2s';set local statement_timeout='15s';
insert into auth.users(id,raw_user_meta_data)values('90000000-0000-0000-0000-000000003161','{"name":"Synthetic audit customer"}'),('90000000-0000-0000-0000-000000003162','{"name":"Synthetic audit admin"}');
update profiles set role='admin' where id='90000000-0000-0000-0000-000000003162';
insert into audit_log(id,user_id,action,table_name,row_id,details)overriding system value values(-31061,'90000000-0000-0000-0000-000000003161','SYNTHETIC','synthetic','-31061','{"marker":"original"}');
insert into client_errors(id,user_id,app,message)overriding system value values(-31061,'90000000-0000-0000-0000-000000003161','customer','synthetic-original');
set local role authenticated;select set_config('request.jwt.claims','{"sub":"90000000-0000-0000-0000-000000003161","role":"authenticated"}',true);
do $$declare n int;u int;d int;e text;begin
select count(*) into n from audit_log where id=-31061;
update audit_log set action='tampered' where id=-31061;get diagnostics u=row_count;
delete from audit_log where id=-31061;get diagnostics d=row_count;
begin insert into audit_log(id,action,table_name)overriding system value values(-31062,'FORGED','synthetic');exception when insufficient_privilege then e:=sqlstate;end;
if n<>0 or u<>0 or d<>0 or e is distinct from '42501' then raise exception 'ASSERT customer audit_log';end if;
perform set_config('test.log_customer_audit_log',jsonb_build_object('read',n,'updated',u,'deleted',d,'insert_sqlstate',e)::text,true);end $$;
do $$declare n int;u int;d int;e text;begin
select count(*) into n from client_errors where id=-31061;
update client_errors set message='tampered' where id=-31061;get diagnostics u=row_count;
delete from client_errors where id=-31061;get diagnostics d=row_count;
begin insert into client_errors(id,message)overriding system value values(-31062,'FORGED');exception when insufficient_privilege then e:=sqlstate;end;
if n<>0 or u<>0 or d<>0 or e is distinct from '42501' then raise exception 'ASSERT customer client_errors';end if;
perform set_config('test.log_customer_client_errors',jsonb_build_object('read',n,'updated',u,'deleted',d,'insert_sqlstate',e)::text,true);end $$;
reset role;select set_config('request.jwt.claims','{}',true);
set local role authenticated;select set_config('request.jwt.claims','{"sub":"90000000-0000-0000-0000-000000003162","role":"authenticated"}',true);
do $$declare n int;u int;d int;e text;begin
select count(*) into n from audit_log where id=-31061;
update audit_log set action='tampered' where id=-31061;get diagnostics u=row_count;
delete from audit_log where id=-31061;get diagnostics d=row_count;
begin insert into audit_log(id,action,table_name)overriding system value values(-31062,'FORGED','synthetic');exception when insufficient_privilege then e:=sqlstate;end;
if n<>1 or u<>0 or d<>0 or e is distinct from '42501' then raise exception 'ASSERT admin audit_log';end if;
perform set_config('test.log_admin_audit_log',jsonb_build_object('read',n,'updated',u,'deleted',d,'insert_sqlstate',e)::text,true);end $$;
do $$declare n int;u int;d int;e text;begin
select count(*) into n from client_errors where id=-31061;
update client_errors set message='tampered' where id=-31061;get diagnostics u=row_count;
delete from client_errors where id=-31061;get diagnostics d=row_count;
begin insert into client_errors(id,message)overriding system value values(-31062,'FORGED');exception when insufficient_privilege then e:=sqlstate;end;
if n<>1 or u<>0 or d<>0 or e is distinct from '42501' then raise exception 'ASSERT admin client_errors';end if;
perform set_config('test.log_admin_client_errors',jsonb_build_object('read',n,'updated',u,'deleted',d,'insert_sqlstate',e)::text,true);end $$;
reset role;select set_config('request.jwt.claims','{}',true);
select jsonb_build_object('customer_audit_log',current_setting('test.log_customer_audit_log')::jsonb,'customer_client_errors',current_setting('test.log_customer_client_errors')::jsonb,'admin_audit_log',current_setting('test.log_admin_audit_log')::jsonb,'admin_client_errors',current_setting('test.log_admin_client_errors')::jsonb) as result;rollback;
