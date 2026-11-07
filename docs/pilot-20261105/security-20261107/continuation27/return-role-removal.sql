begin;
set local lock_timeout='2s'; set local statement_timeout='15s';
-- Entire synthetic fixture and all delivery effects roll back. Never use orders 1/2/3.
select set_config('test.c27_return_config_before',md5(value::text),true) from pilot_private.config where id;
update pilot_private.config set value=jsonb_set(jsonb_set(value,'{customers}',value->'customers'||'"90000000-0000-0000-0000-000000002741"'::jsonb),'{stores}',value->'stores'||'"90000000-0000-0000-0000-000000002743"'::jsonb) where id;
insert into auth.users(id,raw_user_meta_data) values
('90000000-0000-0000-0000-000000002741','{"name":"Synthetic return guard customer"}'),
('90000000-0000-0000-0000-000000002742','{"name":"Synthetic return guard driver"}');
update profiles set role='driver',driver_status='approved' where id='90000000-0000-0000-0000-000000002742';
insert into stores(id,name,category) values('90000000-0000-0000-0000-000000002743','Synthetic return guard store','rest');
insert into orders(id,store_id,customer_id,driver_id,status,lat,lng,payment,total,delivery_fee,driver_payout,subtotal) overriding system value values(-27041,'90000000-0000-0000-0000-000000002743','90000000-0000-0000-0000-000000002741','90000000-0000-0000-0000-000000002742','pickedup',38.56,68.79,'cash',40,15,15,0);
update stores set owner_id='90000000-0000-0000-0000-000000002741' where id='90000000-0000-0000-0000-000000002743';
insert into return_private.agreements(id,store_id,active,evidence,recorded_by)values('90000000-0000-0000-0000-000000002746','90000000-0000-0000-0000-000000002743',true,'Synthetic rollback agreement','90000000-0000-0000-0000-000000002741');
insert into return_private.cases(order_id,store_id,agreement_id,driver_id,customer_id,paid,payment_ref)values(-27041,'90000000-0000-0000-0000-000000002743','90000000-0000-0000-0000-000000002746','90000000-0000-0000-0000-000000002742','90000000-0000-0000-0000-000000002741',25,'SYNTHETIC-ROLLBACK');
insert into return_private.commands(actor,request,order_id,action,payload,result)values('90000000-0000-0000-0000-000000002741','90000000-0000-0000-0000-000000002745',-27041,'receive','{"ref":"SYNTHETIC","amount":null,"method":null}','{"synthetic_marker":"cached_return"}');
set local role authenticated;
select set_config('request.jwt.claims','{"sub":"90000000-0000-0000-0000-000000002741","role":"authenticated"}',true);
select set_config('test.c27_return_active',public.order_return_action(-27041,'90000000-0000-0000-0000-000000002745','receive','SYNTHETIC')::text,true);
reset role;
select set_config('request.jwt.claims','{}',true);
update stores set owner_id=null where id='90000000-0000-0000-0000-000000002743';
set local role authenticated;
select set_config('request.jwt.claims','{"sub":"90000000-0000-0000-0000-000000002741","role":"authenticated"}',true);
do $$declare r jsonb;begin
begin r:=public.order_return_action(-27041,'90000000-0000-0000-0000-000000002745','receive','SYNTHETIC');r:=jsonb_build_object('accepted',true,'result',r);exception when raise_exception then r:=jsonb_build_object('accepted',false,'error',sqlerrm);end;
perform set_config('test.c30_return_removed',r::text,true);end $$;
reset role;
select jsonb_build_object('active',current_setting('test.c27_return_active')::jsonb,'role_removed',current_setting('test.c30_return_removed')::jsonb,'account_banned',(select banned_at is not null from profiles where id='90000000-0000-0000-0000-000000002741')) as result;
rollback;
