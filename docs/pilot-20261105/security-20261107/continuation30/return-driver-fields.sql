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
insert into auth.users(id,raw_user_meta_data)values('90000000-0000-0000-0000-000000002749','{"name":"Synthetic return outsider"}');
insert into return_private.commands(actor,request,order_id,action,payload,result)values('90000000-0000-0000-0000-000000002742','90000000-0000-0000-0000-000000002745',-27041,'confirm_refund','{"ref":"SYNTHETIC","amount":25,"method":null}','{"synthetic_marker":"driver_cached"}');
set local role authenticated;
select set_config('request.jwt.claims','{"sub":"90000000-0000-0000-0000-000000002741","role":"authenticated"}',true);
do $$declare r jsonb;begin r:=order_return_status(-27041);if r ?| array['paid','currency','confirmed_refund','open_claim','delivery_due','pending'] then raise exception 'ASSERT customer finance disclosure';end if;perform set_config('test.c30_customer_keys',(select jsonb_agg(k order by k)::text from jsonb_object_keys(r)k),true);end $$;
select set_config('request.jwt.claims','{"sub":"90000000-0000-0000-0000-000000002742","role":"authenticated"}',true);
do $$declare r jsonb;begin r:=order_return_status(-27041);if not r ?& array['paid','currency','confirmed_refund','open_claim','delivery_due','pending'] then raise exception 'ASSERT driver allowed fields absent';end if;perform set_config('test.c30_driver_keys',(select jsonb_agg(k order by k)::text from jsonb_object_keys(r)k),true);perform set_config('test.c30_driver_active',order_return_action(-27041,'90000000-0000-0000-0000-000000002745','confirm_refund','SYNTHETIC',25)::text,true);end $$;
select set_config('request.jwt.claims','{"sub":"90000000-0000-0000-0000-000000002749","role":"authenticated"}',true);
do $$begin begin perform order_return_status(-27041);raise exception 'ASSERT outsider allowed';exception when raise_exception then if sqlerrm<>'not_allowed' then raise;end if;perform set_config('test.c30_outsider',sqlerrm,true);end;end $$;
reset role;select set_config('request.jwt.claims','{}',true);
do $$begin begin update orders set driver_id=null where id=-27041;raise exception 'ASSERT return order assignment mutable';exception when raise_exception then if sqlerrm<>'return_order_protected' then raise;end if;perform set_config('test.c30_assignment_guard',sqlerrm,true);end;end $$;
reset role;
select jsonb_build_object('customer_keys',current_setting('test.c30_customer_keys')::jsonb,'driver_keys',current_setting('test.c30_driver_keys')::jsonb,'driver_active',current_setting('test.c30_driver_active')::jsonb,'outsider',current_setting('test.c30_outsider'),'assignment_change',current_setting('test.c30_assignment_guard')) as result;
rollback;
