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
insert into return_private.agreements(id,store_id,active,evidence,recorded_by)values('90000000-0000-0000-0000-000000002746','90000000-0000-0000-0000-000000002743',true,'Synthetic rollback agreement','90000000-0000-0000-0000-000000002741');
insert into return_private.cases(order_id,store_id,agreement_id,driver_id,customer_id,paid,payment_ref)values(-27041,'90000000-0000-0000-0000-000000002743','90000000-0000-0000-0000-000000002746','90000000-0000-0000-0000-000000002742','90000000-0000-0000-0000-000000002741',25,'SYNTHETIC-ROLLBACK');
insert into auth.users(id,raw_user_meta_data)values('90000000-0000-0000-0000-000000002749','{"name":"Synthetic return staff"}');
insert into staff_members(user_id,perms)values('90000000-0000-0000-0000-000000002749',array['orders']);
insert into return_private.commands(actor,request,order_id,action,payload,result)values('90000000-0000-0000-0000-000000002749','90000000-0000-0000-0000-000000002745',-27041,'refuse_refund','{"ref":"SYNTHETIC","amount":null,"method":null}','{"synthetic_marker":"staff_cached"}');
set local role authenticated;
select set_config('request.jwt.claims','{"sub":"90000000-0000-0000-0000-000000002749","role":"authenticated"}',true);
do $$declare a jsonb;b jsonb;begin
begin perform order_return_status(-27041);a:='{"accepted":true}';exception when raise_exception then a:=jsonb_build_object('accepted',false,'error',sqlerrm);end;
begin b:=order_return_action(-27041,'90000000-0000-0000-0000-000000002745','refuse_refund','SYNTHETIC');b:=jsonb_build_object('accepted',true,'value',b);exception when raise_exception then b:=jsonb_build_object('accepted',false,'error',sqlerrm);end;
if (a->>'accepted')::boolean<>true or (b->>'accepted')::boolean<>true then raise exception 'ASSERT staff active';end if;
perform set_config('test.c30_staff_active',jsonb_build_object('status',a,'replay',b)::text,true);end $$;
reset role;select set_config('request.jwt.claims','{}',true);
update staff_members set active=false where user_id='90000000-0000-0000-0000-000000002749';
set local role authenticated;
select set_config('request.jwt.claims','{"sub":"90000000-0000-0000-0000-000000002749","role":"authenticated"}',true);
do $$declare a jsonb;b jsonb;begin
begin perform order_return_status(-27041);a:='{"accepted":true}';exception when raise_exception then a:=jsonb_build_object('accepted',false,'error',sqlerrm);end;
begin b:=order_return_action(-27041,'90000000-0000-0000-0000-000000002745','refuse_refund','SYNTHETIC');b:=jsonb_build_object('accepted',true,'value',b);exception when raise_exception then b:=jsonb_build_object('accepted',false,'error',sqlerrm);end;
if (a->>'accepted')::boolean<>false or (b->>'accepted')::boolean<>false then raise exception 'ASSERT staff inactive';end if;
perform set_config('test.c30_staff_inactive',jsonb_build_object('status',a,'replay',b)::text,true);end $$;
reset role;select set_config('request.jwt.claims','{}',true);
update staff_members set active=true,perms=array[]::text[] where user_id='90000000-0000-0000-0000-000000002749';
set local role authenticated;
select set_config('request.jwt.claims','{"sub":"90000000-0000-0000-0000-000000002749","role":"authenticated"}',true);
do $$declare a jsonb;b jsonb;begin
begin perform order_return_status(-27041);a:='{"accepted":true}';exception when raise_exception then a:=jsonb_build_object('accepted',false,'error',sqlerrm);end;
begin b:=order_return_action(-27041,'90000000-0000-0000-0000-000000002745','refuse_refund','SYNTHETIC');b:=jsonb_build_object('accepted',true,'value',b);exception when raise_exception then b:=jsonb_build_object('accepted',false,'error',sqlerrm);end;
if (a->>'accepted')::boolean<>false or (b->>'accepted')::boolean<>false then raise exception 'ASSERT staff permission_removed';end if;
perform set_config('test.c30_staff_permission_removed',jsonb_build_object('status',a,'replay',b)::text,true);end $$;
reset role;select jsonb_build_object('active',current_setting('test.c30_staff_active')::jsonb,'inactive',current_setting('test.c30_staff_inactive')::jsonb,'permission_removed',current_setting('test.c30_staff_permission_removed')::jsonb)as result;rollback;
