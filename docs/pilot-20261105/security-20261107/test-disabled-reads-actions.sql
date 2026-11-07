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
insert into wallet_entries(user_id,amount,kind,note) values('90000000-0000-0000-0000-000000000900',7,'adjust','synthetic rollback');
select set_config('test.result','{}',true);
set local role authenticated;
select set_config('request.jwt.claims','{"sub":"90000000-0000-0000-0000-000000000900","role":"authenticated"}',true);
do $$declare r jsonb;e text;begin
r:=jsonb_build_object('profiles',(select count(*) from profiles where id=auth.uid()),'orders',(select count(*) from orders where id=current_setting('test.scope_order')::bigint),'contacts',(select count(*) from active_contacts() where order_id=current_setting('test.scope_order')::bigint),'wallet_rows',(select count(*) from wallet_entries where user_id=auth.uid()),'wallet_balance',wallet_balance());
begin perform group_create('90000000-0000-0000-0000-000000000901');e:='ACCEPTED';exception when others then e:=sqlerrm;end;r:=r||jsonb_build_object('group_create',e);
begin perform order_return_status(current_setting('test.scope_order')::bigint);e:='ACCEPTED';exception when others then e:=sqlerrm;end;r:=r||jsonb_build_object('return_status',e);
perform set_config('test.result',(current_setting('test.result')::jsonb||jsonb_build_object('active',r))::text,true);end $$;
select set_config('request.jwt.claims','{"sub":"90000000-0000-0000-0000-000000000902","role":"authenticated"}',true);
do $$declare e text;begin
begin perform driver_arrived(current_setting('test.scope_order')::bigint,'customer');e:='ACCEPTED';exception when others then e:=sqlerrm;end;
perform set_config('test.result',(current_setting('test.result')::jsonb||jsonb_build_object('active_driver_arrived',e))::text,true);begin perform deliver_order(current_setting('test.scope_order')::bigint,0);raise exception using errcode='PZ001';exception when sqlstate 'PZ001' then e:='ACCEPTED';when others then e:=sqlerrm;end;perform set_config('test.result',(current_setting('test.result')::jsonb||jsonb_build_object('active_deliver',e))::text,true);end $$;
reset role;select set_config('request.jwt.claims','{}',true);update profiles set banned_at=now() where id in ('90000000-0000-0000-0000-000000000900','90000000-0000-0000-0000-000000000902');
set local role authenticated;
select set_config('request.jwt.claims','{"sub":"90000000-0000-0000-0000-000000000900","role":"authenticated"}',true);
do $$declare r jsonb;e text;begin
r:=jsonb_build_object('profiles',(select count(*) from profiles where id=auth.uid()),'orders',(select count(*) from orders where id=current_setting('test.scope_order')::bigint),'contacts',(select count(*) from active_contacts() where order_id=current_setting('test.scope_order')::bigint),'wallet_rows',(select count(*) from wallet_entries where user_id=auth.uid()),'wallet_balance',wallet_balance());
begin perform group_create('90000000-0000-0000-0000-000000000901');e:='ACCEPTED';exception when others then e:=sqlerrm;end;r:=r||jsonb_build_object('group_create',e);
begin perform order_return_status(current_setting('test.scope_order')::bigint);e:='ACCEPTED';exception when others then e:=sqlerrm;end;r:=r||jsonb_build_object('return_status',e);
perform set_config('test.result',(current_setting('test.result')::jsonb||jsonb_build_object('disabled',r))::text,true);end $$;
select set_config('request.jwt.claims','{"sub":"90000000-0000-0000-0000-000000000902","role":"authenticated"}',true);
do $$declare e text;begin
begin perform driver_arrived(current_setting('test.scope_order')::bigint,'customer');e:='ACCEPTED';exception when others then e:=sqlerrm;end;
perform set_config('test.result',(current_setting('test.result')::jsonb||jsonb_build_object('disabled_driver_arrived',e))::text,true);begin perform deliver_order(current_setting('test.scope_order')::bigint,0);raise exception using errcode='PZ001';exception when sqlstate 'PZ001' then e:='ACCEPTED';when others then e:=sqlerrm;end;perform set_config('test.result',(current_setting('test.result')::jsonb||jsonb_build_object('disabled_deliver',e))::text,true);end $$;
reset role;select current_setting('test.result')::jsonb as results;rollback;