-- Isolated test project only. Synthetic records; rollback required; no orders or money.
begin;
set local lock_timeout='2s';set local statement_timeout='15s';
insert into auth.users(id,raw_user_meta_data) values
('90000000-0000-0000-0000-000000003511','{"name":"ASVS35 owner"}'),
('90000000-0000-0000-0000-000000003512','{"name":"ASVS35 admin"}'),
('90000000-0000-0000-0000-000000003513','{"name":"ASVS35 outsider"}');
update profiles set role='admin' where id='90000000-0000-0000-0000-000000003512';
insert into staff_members(user_id,perms) values('90000000-0000-0000-0000-000000003513',array['support']);
insert into stores(id,name,category,owner_id) values('90000000-0000-0000-0000-000000003514','ASVS35 private reader store','rest','90000000-0000-0000-0000-000000003511');
set local role authenticated;
select set_config('request.jwt.claims','{"sub":"90000000-0000-0000-0000-000000003511","role":"authenticated","aal":"aal2"}',true);
do $$begin
 if (select count(*) from store_private() where id='90000000-0000-0000-0000-000000003514')<>1 then raise exception 'ASSERT owner positive';end if;
 if (select count(*) from store_owner_info('90000000-0000-0000-0000-000000003514'))<>0 then raise exception 'ASSERT owner not admin';end if;
end $$;
select set_config('request.jwt.claims','{"sub":"90000000-0000-0000-0000-000000003513","role":"authenticated","aal":"aal2"}',true);
do $$begin
 if (select count(*) from store_private() where id='90000000-0000-0000-0000-000000003514')<>0 then raise exception 'ASSERT cross owner';end if;
 if (select count(*) from store_owner_info('90000000-0000-0000-0000-000000003514'))<>0 then raise exception 'ASSERT support not admin owner';end if;
 if (select count(*) from staff_list() where user_id='90000000-0000-0000-0000-000000003513')<>0 then raise exception 'ASSERT support not admin staff';end if;
end $$;
select set_config('request.jwt.claims','{"sub":"90000000-0000-0000-0000-000000003512","role":"authenticated","aal":"aal2"}',true);
do $$begin
 if (select count(*) from store_private() where id='90000000-0000-0000-0000-000000003514')<>1 then raise exception 'ASSERT admin private';end if;
 if (select count(*) from store_owner_info('90000000-0000-0000-0000-000000003514'))<>1 then raise exception 'ASSERT admin owner';end if;
 if (select count(*) from staff_list() where user_id='90000000-0000-0000-0000-000000003513')<>1 then raise exception 'ASSERT admin staff';end if;
end $$;
reset role;select set_config('request.jwt.claims','{}',true);
update profiles set banned_at=now() where id in ('90000000-0000-0000-0000-000000003511','90000000-0000-0000-0000-000000003512');
set local role authenticated;
select set_config('request.jwt.claims','{"sub":"90000000-0000-0000-0000-000000003511","role":"authenticated","aal":"aal2"}',true);
do $$begin
 if account_enabled() or (select count(*) from store_private() where id='90000000-0000-0000-0000-000000003514')<>0 then raise exception 'ASSERT banned owner';end if;
end $$;
select set_config('request.jwt.claims','{"sub":"90000000-0000-0000-0000-000000003512","role":"authenticated","aal":"aal2"}',true);
do $$begin
 if account_enabled() then raise exception 'ASSERT ban fixture';end if;
 if (select count(*) from store_private() where id='90000000-0000-0000-0000-000000003514')<>0 then raise exception 'ASSERT banned admin private';end if;
 if (select count(*) from store_owner_info('90000000-0000-0000-0000-000000003514'))<>0 then raise exception 'ASSERT banned admin owner';end if;
 if (select count(*) from staff_list() where user_id='90000000-0000-0000-0000-000000003513')<>0 then raise exception 'ASSERT banned admin staff';end if;
end $$;
reset role;select set_config('request.jwt.claims','{}',true);
select jsonb_build_object('result','PASS','assertions',12,'positive_owner',true,'positive_admin',true,'cross_owner_denied',true,'support_not_admin',true,'banned_owner_denied',true,'banned_admin_denied',true,'scope','live SQL roles; not HTTP JWT lifecycle') result;
rollback;
