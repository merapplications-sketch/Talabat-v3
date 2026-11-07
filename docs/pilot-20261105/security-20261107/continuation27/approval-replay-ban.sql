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
insert into fulfillment_private.approval_requests(request,actor,operation,order_id,payload,result)values
('90000000-0000-0000-0000-000000002751','90000000-0000-0000-0000-000000002741','customer_confirm',-27041,'{"revision":1}','{"synthetic_marker":"customer_cached"}'),
('90000000-0000-0000-0000-000000002752','90000000-0000-0000-0000-000000002741','merchant_review',-27041,'{"minutes":15,"items":null,"note":""}','{"synthetic_marker":"merchant_cached"}');
set local role authenticated;
select set_config('request.jwt.claims','{"sub":"90000000-0000-0000-0000-000000002741","role":"authenticated"}',true);
do $$declare a jsonb;b jsonb;begin
begin a:=customer_confirm_order(-27041,1,'90000000-0000-0000-0000-000000002751');a:=jsonb_build_object('accepted',true,'value',a);exception when raise_exception then a:=jsonb_build_object('accepted',false,'error',sqlerrm);end;
begin b:=merchant_review_order(-27041,15,'90000000-0000-0000-0000-000000002752',null,null);b:=jsonb_build_object('accepted',true,'value',b);exception when raise_exception then b:=jsonb_build_object('accepted',false,'error',sqlerrm);end;
perform set_config('test.c28_active',jsonb_build_object('customer',a,'merchant',b)::text,true);end $$;
reset role; select set_config('request.jwt.claims','{}',true); update profiles set banned_at=now() where id='90000000-0000-0000-0000-000000002741';
set local role authenticated;
select set_config('request.jwt.claims','{"sub":"90000000-0000-0000-0000-000000002741","role":"authenticated"}',true);
do $$declare a jsonb;b jsonb;begin
begin a:=customer_confirm_order(-27041,1,'90000000-0000-0000-0000-000000002751');a:=jsonb_build_object('accepted',true,'value',a);exception when raise_exception then a:=jsonb_build_object('accepted',false,'error',sqlerrm);end;
begin b:=merchant_review_order(-27041,15,'90000000-0000-0000-0000-000000002752',null,null);b:=jsonb_build_object('accepted',true,'value',b);exception when raise_exception then b:=jsonb_build_object('accepted',false,'error',sqlerrm);end;
perform set_config('test.c28_banned',jsonb_build_object('customer',a,'merchant',b)::text,true);end $$;
reset role; select jsonb_build_object('active',current_setting('test.c28_active')::jsonb,'banned',current_setting('test.c28_banned')::jsonb)as result; rollback;
