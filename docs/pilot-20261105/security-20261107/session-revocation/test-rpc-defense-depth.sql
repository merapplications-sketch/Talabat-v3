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

update profiles set lat=38.5,lng=68.7,loc_updated=now() where id='90000000-0000-0000-0000-000000000902';
select set_config('test.result','{}',true);
set local role authenticated;
select set_config('request.jwt.claims','{"sub":"90000000-0000-0000-0000-000000000900","role":"authenticated"}',true);
select set_config('test.result',jsonb_build_object('active_position_rows',(select count(*) from order_courier_position(current_setting('test.scope_order')::bigint)),'active_loyalty',loyalty_summary() is not null)::text,true);
reset role;select set_config('request.jwt.claims','{}',true);
update profiles set banned_at=now() where id='90000000-0000-0000-0000-000000000900';
set local role authenticated;select set_config('request.jwt.claims','{"sub":"90000000-0000-0000-0000-000000000900","role":"authenticated"}',true);
select set_config('test.result',(current_setting('test.result')::jsonb||jsonb_build_object('banned_position_rows',(select count(*) from order_courier_position(current_setting('test.scope_order')::bigint)),'banned_loyalty',loyalty_summary() is not null))::text,true);
DO $$ BEGIN
  BEGIN PERFORM apply_as_driver(); PERFORM set_config('test.apply_result','completed',true);
  EXCEPTION WHEN OTHERS THEN PERFORM set_config('test.apply_result',sqlerrm,true); END;
END $$;
reset role;
select current_setting('test.result')::jsonb || jsonb_build_object('banned_apply',current_setting('test.apply_result'),'banned_role_after',(select role from profiles where id='90000000-0000-0000-0000-000000000900')) results;
rollback;
