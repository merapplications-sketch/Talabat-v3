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
set local role authenticated;
select set_config('request.jwt.claims','{"sub":"90000000-0000-0000-0000-000000000900","role":"authenticated"}',true);
do $$declare r jsonb:='{}';e text;n int;o bigint:=current_setting('test.scope_order')::bigint;begin
update menu_items set name='Cross store' where id='90000000-0000-0000-0000-000000000906';get diagnostics n=row_count;r:=r||jsonb_build_object('cross_store_update_rows',n);
begin perform set_store_open('90000000-0000-0000-0000-000000000904',false);e:='ACCEPTED';exception when others then e:=sqlerrm;end;r:=r||jsonb_build_object('cross_store_rpc',e);
update profiles set lat=0 where id='90000000-0000-0000-0000-000000000902';get diagnostics n=row_count;r:=r||jsonb_build_object('cross_driver_profile_update_rows',n);
begin perform driver_arrived(o,'customer');e:='ACCEPTED';exception when others then e:=sqlerrm;end;r:=r||jsonb_build_object('cross_driver_arrived',e);
begin perform deliver_order(o,0);e:='ACCEPTED';exception when others then e:=sqlerrm;end;r:=r||jsonb_build_object('cross_driver_deliver',e);
begin insert into storage.objects(bucket_id,name) values('proofs','90000000-0000-0000-0000-000000000900/'||o||'/synthetic900.jpg');e:='ACCEPTED';exception when others then e:=sqlerrm;end;r:=r||jsonb_build_object('customer_proof_insert',e);
perform set_config('test.scope_result',r::text,true);end $$;
select set_config('request.jwt.claims','{"sub":"90000000-0000-0000-0000-000000000902","role":"authenticated"}',true);
do $$declare r jsonb:=current_setting('test.scope_result')::jsonb;e text;n int;o bigint:=current_setting('test.scope_order')::bigint;begin
begin insert into storage.objects(bucket_id,name) values('proofs','90000000-0000-0000-0000-000000000900/'||o||'/wrongowner900.jpg');e:='ACCEPTED';exception when others then e:=sqlerrm;end;r:=r||jsonb_build_object('driver_other_folder_insert',e);
insert into storage.objects(bucket_id,name) values('proofs','90000000-0000-0000-0000-000000000902/'||o||'/synthetic900.jpg');
r:=r||jsonb_build_object('assigned_driver_proof_insert','ACCEPTED');
update storage.objects set metadata='{"tamper":true}' where bucket_id='proofs' and name='90000000-0000-0000-0000-000000000902/'||o||'/synthetic900.jpg';get diagnostics n=row_count;r:=r||jsonb_build_object('proof_update_rows',n);
begin delete from storage.objects where bucket_id='proofs' and name='90000000-0000-0000-0000-000000000902/'||o||'/synthetic900.jpg';get diagnostics n=row_count;r:=r||jsonb_build_object('proof_delete_rows',n); exception when others then r:=r||jsonb_build_object('proof_delete_error',sqlerrm);end;
perform set_config('test.scope_result',r::text,true);end $$;
reset role;
select set_config('request.jwt.claims','{}',true);
update profiles set banned_at=now() where id='90000000-0000-0000-0000-000000000900';
set local role authenticated;
select set_config('request.jwt.claims','{"sub":"90000000-0000-0000-0000-000000000900","role":"authenticated"}',true);
do $$declare r jsonb:=current_setting('test.scope_result')::jsonb;e text;n int;begin
r:=r||jsonb_build_object('banned_own_profile_count',(select count(*) from profiles where id='90000000-0000-0000-0000-000000000900'),'banned_other_profile_count',(select count(*) from profiles where id='90000000-0000-0000-0000-000000000902'),'banned_customer_proof_read',(select count(*) from storage.objects where bucket_id='proofs' and name='90000000-0000-0000-0000-000000000902/'||current_setting('test.scope_order')||'/synthetic900.jpg'),'banned_has_perm',has_perm('stores'));
begin update profiles set name='Banned own edit' where id='90000000-0000-0000-0000-000000000900';get diagnostics n=row_count;r:=r||jsonb_build_object('banned_own_profile_update_rows',n);exception when others then r:=r||jsonb_build_object('banned_own_profile_update_error',sqlerrm);end;
begin perform set_store_open('90000000-0000-0000-0000-000000000901',false);e:='ACCEPTED';exception when others then e:=sqlerrm;end;r:=r||jsonb_build_object('banned_owned_store_write',e);
perform set_config('test.scope_result',r::text,true);end $$;
reset role;
select current_setting('test.scope_result')::jsonb as results;
rollback;
