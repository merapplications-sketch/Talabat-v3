-- Test-only synthetic users, no credentials, orders or money; rollback required.
begin; set local lock_timeout='2s'; set local statement_timeout='15s';
insert into auth.users(id,raw_user_meta_data) values
('90000000-0000-0000-0000-000000003501','{"name":"Synthetic support reader"}'),
('90000000-0000-0000-0000-000000003502','{"name":"ASVS35 O''Reilly search fixture"}');
insert into staff_members(user_id,perms) values('90000000-0000-0000-0000-000000003501',array['support']);
set local role authenticated;
select set_config('request.jwt.claims','{"sub":"90000000-0000-0000-0000-000000003501","role":"authenticated"}',true);
do $$declare normal_count int;quote_count int;payload_count int;begin
 select count(*) into normal_count from admin_customers('ASVS35',30,0);
 select count(*) into quote_count from admin_customers('ASVS35 O''Reilly',30,0);
 select count(*) into payload_count from admin_customers('zzASVS35'' OR ''1''=''1',30,0);
 if normal_count<>1 or quote_count<>1 or payload_count<>0 then raise exception 'ASSERT search parameter or fixture failure';end if;
 perform set_config('test.support_search',jsonb_build_object('normal',normal_count,'apostrophe',quote_count,'sql_looking_literal',payload_count)::text,true);
end $$;
reset role;select set_config('request.jwt.claims','{}',true);
update staff_members set perms=array[]::text[] where user_id='90000000-0000-0000-0000-000000003501';
set local role authenticated;
select set_config('request.jwt.claims','{"sub":"90000000-0000-0000-0000-000000003501","role":"authenticated"}',true);
do $$declare n int;begin select count(*) into n from admin_customers('ASVS35',30,0);if n<>0 then raise exception 'ASSERT permission removal';end if;perform set_config('test.support_removed',n::text,true);end $$;
reset role;select set_config('request.jwt.claims','{}',true);
update staff_members set perms=array['support'] where user_id='90000000-0000-0000-0000-000000003501';
update profiles set banned_at=now() where id='90000000-0000-0000-0000-000000003501';
set local role authenticated;
select set_config('request.jwt.claims','{"sub":"90000000-0000-0000-0000-000000003501","role":"authenticated"}',true);
do $$declare n int;begin select count(*) into n from admin_customers('ASVS35',30,0);if n<>0 or account_enabled() then raise exception 'ASSERT banned support';end if;perform set_config('test.support_banned',n::text,true);end $$;
reset role;select set_config('request.jwt.claims','{}',true);
select jsonb_build_object('active_search',current_setting('test.support_search')::jsonb,'permission_removed_rows',current_setting('test.support_removed')::int,'banned_rows',current_setting('test.support_banned')::int) as result;
rollback;
