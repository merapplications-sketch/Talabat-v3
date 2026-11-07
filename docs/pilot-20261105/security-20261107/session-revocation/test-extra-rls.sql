begin;
set local lock_timeout='2s';set local statement_timeout='15s';
update pilot_private.config set value=jsonb_set(jsonb_set(value,'{customers}',value->'customers'||'"90000000-0000-0000-0000-000000000900"'::jsonb),'{stores}',value->'stores'||'"90000000-0000-0000-0000-000000000901"'::jsonb) where id;
insert into auth.users(id,raw_user_meta_data) values
('90000000-0000-0000-0000-000000000900','{"name":"Synthetic A"}'),
('90000000-0000-0000-0000-000000000902','{"name":"Synthetic B"}');
update profiles set role='driver',driver_status='approved',online=true where id='90000000-0000-0000-0000-000000000902';
insert into stores(id,name,category,owner_id) values
('90000000-0000-0000-0000-000000000901','Synthetic A','rest','90000000-0000-0000-0000-000000000900'),
('90000000-0000-0000-0000-000000000904','Synthetic B','rest','90000000-0000-0000-0000-000000000902');
insert into menu_items(id,store_id,name,price) values
('90000000-0000-0000-0000-000000000905','90000000-0000-0000-0000-000000000901','A',10),
('90000000-0000-0000-0000-000000000906','90000000-0000-0000-0000-000000000904','B',10);
with o as(insert into orders(store_id,customer_id,driver_id,status,lat,lng) values ('90000000-0000-0000-0000-000000000901','90000000-0000-0000-0000-000000000900','90000000-0000-0000-0000-000000000902','pickedup',38.56,68.79) returning id) select set_config('test.scope_order',id::text,true) from o;

insert into order_offers(order_id,driver_id,expires_at) values(current_setting('test.scope_order')::bigint,'90000000-0000-0000-0000-000000000902',now()+interval '1 minute');
insert into ratings(order_id,customer_id,store_id,store_stars) values(current_setting('test.scope_order')::bigint,'90000000-0000-0000-0000-000000000900','90000000-0000-0000-0000-000000000901',5);
insert into staff_members(user_id,perms) values('90000000-0000-0000-0000-000000000900','{}');
insert into store_requests(user_id,name,category,phone,lat,lng) values('90000000-0000-0000-0000-000000000900','synthetic','rest','+992000000000',0,0);
select set_config('test.result','{}',true);
set local role authenticated;select set_config('request.jwt.claims','{"sub":"90000000-0000-0000-0000-000000000900","role":"authenticated"}',true);
select set_config('test.result',(current_setting('test.result')::jsonb||jsonb_build_object('active',jsonb_build_object('ratings',(select count(*) from ratings where customer_id=auth.uid()),'staff',(select count(*) from staff_members where user_id=auth.uid()),'store_requests',(select count(*) from store_requests where user_id=auth.uid()))))::text,true);
select set_config('request.jwt.claims','{"sub":"90000000-0000-0000-0000-000000000902","role":"authenticated"}',true);
select set_config('test.result',(current_setting('test.result')::jsonb||jsonb_build_object('active_offers',(select count(*) from order_offers where driver_id=auth.uid())))::text,true);
reset role;select set_config('request.jwt.claims','{}',true);update profiles set banned_at=now() where id in ('90000000-0000-0000-0000-000000000900','90000000-0000-0000-0000-000000000902');
set local role authenticated;select set_config('request.jwt.claims','{"sub":"90000000-0000-0000-0000-000000000900","role":"authenticated"}',true);
select set_config('test.result',(current_setting('test.result')::jsonb||jsonb_build_object('banned',jsonb_build_object('ratings',(select count(*) from ratings where customer_id=auth.uid()),'staff',(select count(*) from staff_members where user_id=auth.uid()),'store_requests',(select count(*) from store_requests where user_id=auth.uid()))))::text,true);
select set_config('request.jwt.claims','{"sub":"90000000-0000-0000-0000-000000000902","role":"authenticated"}',true);
select set_config('test.result',(current_setting('test.result')::jsonb||jsonb_build_object('banned_offers',(select count(*) from order_offers where driver_id=auth.uid())))::text,true);
reset role;select current_setting('test.result')::jsonb results;rollback;