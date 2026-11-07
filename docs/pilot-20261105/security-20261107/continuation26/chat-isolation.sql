begin;
set local lock_timeout='2s'; set local statement_timeout='15s';
-- Entire synthetic fixture and all delivery effects roll back. Never use orders 1/2/3.
select set_config('test.c26_chat_config_before',md5(value::text),true) from pilot_private.config where id;
update pilot_private.config set value=jsonb_set(jsonb_set(value,'{customers}',value->'customers'||'"90000000-0000-0000-0000-000000002641"'::jsonb),'{stores}',value->'stores'||'"90000000-0000-0000-0000-000000002643"'::jsonb) where id;
insert into auth.users(id,raw_user_meta_data) values
('90000000-0000-0000-0000-000000002641','{"name":"Synthetic chat isolation customer"}'),
('90000000-0000-0000-0000-000000002642','{"name":"Synthetic chat isolation driver"}');
update profiles set role='driver',driver_status='approved' where id='90000000-0000-0000-0000-000000002642';
insert into stores(id,name,category) values('90000000-0000-0000-0000-000000002643','Synthetic chat isolation store','rest');
insert into orders(id,store_id,customer_id,driver_id,status,lat,lng,payment,total,delivery_fee,driver_payout,subtotal) overriding system value values(-26041,'90000000-0000-0000-0000-000000002643','90000000-0000-0000-0000-000000002641','90000000-0000-0000-0000-000000002642','pickedup',38.56,68.79,'cash',40,15,15,0);
insert into auth.users(id,raw_user_meta_data)values('90000000-0000-0000-0000-000000002644','{"name":"Synthetic outsider"}');
set local role authenticated;
select set_config('request.jwt.claims','{"sub":"90000000-0000-0000-0000-000000002641","role":"authenticated"}',true);
insert into order_chat(order_id,sender_id,body)values(-26041,'90000000-0000-0000-0000-000000002641','Synthetic allowed message');
do $$declare e text;begin
begin insert into order_chat(order_id,sender_id,body)values(-26041,'90000000-0000-0000-0000-000000002642','Synthetic sender forgery');raise exception 'ASSERT sender forgery accepted';exception when insufficient_privilege then e:=sqlerrm;end;
perform set_config('test.c26_chat_forgery',e,true);end $$;
select set_config('request.jwt.claims','{"sub":"90000000-0000-0000-0000-000000002644","role":"authenticated"}',true);
do $$declare e text;begin
begin insert into order_chat(order_id,sender_id,body)values(-26041,'90000000-0000-0000-0000-000000002644','Synthetic outsider message');raise exception 'ASSERT outsider accepted';exception when insufficient_privilege then e:=sqlerrm;end;
perform set_config('test.c26_chat_outsider',e,true);end $$;
reset role;
select jsonb_build_object('allowed_rows',(select count(*)from order_chat where order_id=-26041 and sender_id='90000000-0000-0000-0000-000000002641'),'total_rows',(select count(*)from order_chat where order_id=-26041),'forged_sender',current_setting('test.c26_chat_forgery'),'outsider',current_setting('test.c26_chat_outsider')) as result;
rollback;
