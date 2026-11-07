begin;
set local lock_timeout='2s';set local statement_timeout='15s';
select set_config('test.finance_config_before',md5(value::text),true) from pilot_private.config where id;
update pilot_private.config set value=jsonb_set(jsonb_set(value,'{customers}',value->'customers'||'"90000000-0000-0000-0000-000000000920"'::jsonb),'{stores}',value->'stores'||'"90000000-0000-0000-0000-000000000923"'::jsonb) where id;
insert into auth.users(id,raw_user_meta_data) values
('90000000-0000-0000-0000-000000000920','{"name":"Synthetic finance customer"}'),
('90000000-0000-0000-0000-000000000921','{"name":"Synthetic finance driver"}'),
('90000000-0000-0000-0000-000000000922','{"name":"Synthetic finance staff"}');
update profiles set role='driver',driver_status='approved' where id='90000000-0000-0000-0000-000000000921';
insert into staff_members(user_id,perms) values('90000000-0000-0000-0000-000000000922',array['finance','support']);
insert into stores(id,name,category) values('90000000-0000-0000-0000-000000000923','Synthetic finance store','rest');
insert into finance_private.cash_delivery_policy(store_id,platform_amount,reference) select '90000000-0000-0000-0000-000000000923',platform_amount,reference from finance_private.cash_delivery_policy order by store_id limit 1;
with o as(insert into orders(store_id,customer_id,driver_id,status,lat,lng,payment,total,delivery_fee,driver_payout,cash_collected,done_at) values('90000000-0000-0000-0000-000000000923','90000000-0000-0000-0000-000000000920','90000000-0000-0000-0000-000000000921','delivered',38.56,68.79,'cash',100,15,15,100,now()) returning id) select set_config('test.finance_order',id::text,true) from o;
select finance_private.snapshot_cash(current_setting('test.finance_order')::bigint);
with t as(insert into support_tickets(customer_id,order_id,reason,status) values('90000000-0000-0000-0000-000000000920',current_setting('test.finance_order')::bigint,'payment','resolved') returning id) select set_config('test.finance_ticket1',id::text,true) from t;
with t as(insert into support_tickets(customer_id,order_id,reason,status) values('90000000-0000-0000-0000-000000000920',current_setting('test.finance_order')::bigint,'payment','resolved') returning id) select set_config('test.finance_ticket2',id::text,true) from t;
set local role authenticated;
select set_config('request.jwt.claims','{"sub":"90000000-0000-0000-0000-000000000922","role":"authenticated"}',true);
do $$declare r jsonb:='{}';a jsonb;b jsonb;e text;t1 bigint:=current_setting('test.finance_ticket1')::bigint;t2 bigint:=current_setting('test.finance_ticket2')::bigint;begin
begin perform ticket_set_status(t1,'resolved','Synthetic abort refund',25);raise exception 'synthetic_interrupt';exception when others then if sqlerrm<>'synthetic_interrupt' then raise;end if;end;
r:=r||jsonb_build_object('refund_after_interrupt',(select coalesce(sum(amount),0) from wallet_entries where ticket_id=t1 and kind='refund'));
perform ticket_set_status(t1,'resolved','Synthetic refund',60);
begin perform ticket_set_status(t1,'resolved','Synthetic refund',60);e:='ACCEPTED';exception when others then e:=sqlerrm;end;r:=r||jsonb_build_object('same_ticket_repeat',e);
begin perform ticket_set_status(t2,'resolved','Synthetic cap',41);e:='ACCEPTED';exception when others then e:=sqlerrm;end;r:=r||jsonb_build_object('cross_ticket_over_cap',e);
perform ticket_set_status(t2,'resolved','Synthetic remaining',40);
r:=r||jsonb_build_object('refund_sum',(select sum(amount) from wallet_entries where order_id=current_setting('test.finance_order')::bigint and kind='refund'),'refund_count',(select count(*) from wallet_entries where order_id=current_setting('test.finance_order')::bigint and kind='refund'));
begin perform finance_execute('90000000-0000-0000-0000-000000000924','settle_cash','90000000-0000-0000-0000-000000000921');raise exception 'synthetic_interrupt';exception when others then if sqlerrm<>'synthetic_interrupt' then raise;end if;end;
r:=r||jsonb_build_object('settled_after_interrupt',(select cash_settled_at from orders where id=current_setting('test.finance_order')::bigint),'status_after_interrupt',finance_command_status('90000000-0000-0000-0000-000000000924'));
a:=finance_execute('90000000-0000-0000-0000-000000000924','settle_cash','90000000-0000-0000-0000-000000000921');
b:=finance_execute('90000000-0000-0000-0000-000000000924','settle_cash','90000000-0000-0000-0000-000000000921');
if a is distinct from b then raise exception 'ASSERT settlement replay changed';end if;
r:=r||jsonb_build_object('settlement_amount',a->'amount','settlement_same_key_equal',a=b,'settlement_order_count',jsonb_array_length(a->'orders'));
begin perform finance_execute('90000000-0000-0000-0000-000000000924','settle_cash','90000000-0000-0000-0000-000000000920');e:='ACCEPTED';exception when others then e:=sqlerrm;end;r:=r||jsonb_build_object('same_key_changed_target',e);
begin perform finance_execute('90000000-0000-0000-0000-000000000925','settle_cash','90000000-0000-0000-0000-000000000921');e:='ACCEPTED';exception when others then e:=sqlerrm;end;r:=r||jsonb_build_object('second_key_same_settlement',e);
perform set_config('test.finance_results',r::text,true);end $$;
reset role;
select current_setting('test.finance_results')::jsonb||jsonb_build_object('command_count',(select count(*) from finance_private.commands where actor='90000000-0000-0000-0000-000000000922'),'receipt_count',(select count(*) from finance_private.settlement_receipts where driver='90000000-0000-0000-0000-000000000921'),'receipt_order_count',(select count(*) from finance_private.settlement_receipt_orders where order_id=current_setting('test.finance_order')::bigint),'refund_sum_privileged',(select sum(amount) from wallet_entries where user_id='90000000-0000-0000-0000-000000000920'),'pilot_before_hash',current_setting('test.finance_config_before')) as results;
rollback;
