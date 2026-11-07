-- Dedicated disposable fixtures; no wallet entries, settlements or receipts.
-- Never remove ROLLBACK or relax pilot hours/capacity/financial constraints.
begin; set local lock_timeout='2s'; set local statement_timeout='15s';
insert into auth.users(id,raw_user_meta_data) values
 ('90000000-0000-0000-0000-000000003401','{"name":"Synthetic balance owner"}'),
 ('90000000-0000-0000-0000-000000003402','{"name":"Synthetic balance driver"}');
update profiles set role='driver' where id='90000000-0000-0000-0000-000000003402';
insert into stores(id,name,category,owner_id)values('90000000-0000-0000-0000-000000003403','Synthetic balance store','rest','90000000-0000-0000-0000-000000003401');
update pilot_private.config set value=jsonb_set(jsonb_set(value,'{customers}',value->'customers'||'"90000000-0000-0000-0000-000000003401"'::jsonb),'{stores}',value->'stores'||'"90000000-0000-0000-0000-000000003403"'::jsonb) where id;
insert into orders(id,store_id,customer_id,driver_id,status,payment,lat,lng,subtotal,delivery_fee,total,cash_collected,cash_allocation_version,cash_platform_share,cash_driver_delivery_share,cash_allocation_reference)
overriding system value values(-34001,'90000000-0000-0000-0000-000000003403','90000000-0000-0000-0000-000000003401','90000000-0000-0000-0000-000000003402','delivered','cash',38.56,68.79,25,15,40,40,1,5,10,'SYNTHETIC-ROLLBACK-ONLY-34');
set local role authenticated;
select set_config('request.jwt.claims','{"sub":"90000000-0000-0000-0000-000000003402","role":"authenticated"}',true);
do $$ declare r jsonb;begin
 select jsonb_agg(to_jsonb(b)) into r from cash_balances() b;
 if r is distinct from '[{"driver_id":"90000000-0000-0000-0000-000000003402","balance":5}]'::jsonb then raise exception 'active positive fixture invalid';end if;
 perform set_config('test.active_balance',r::text,true);
end $$;
reset role; select set_config('request.jwt.claims','{}',true);
update profiles set banned_at=now() where id='90000000-0000-0000-0000-000000003402';
set local role authenticated;
select set_config('request.jwt.claims','{"sub":"90000000-0000-0000-0000-000000003402","role":"authenticated"}',true);
do $$ declare r jsonb;e text;enabled boolean;begin
 enabled:=account_enabled(); if enabled then raise exception 'fixture ban not effective';end if;
 begin select jsonb_agg(to_jsonb(b)) into r from cash_balances() b;exception when others then e:=sqlstate;end;
 perform set_config('test.banned_balance',jsonb_build_object('enabled',enabled,'rows',r,'sqlstate',e)::text,true);
end $$;
reset role;select jsonb_build_object('active',current_setting('test.active_balance')::jsonb,'banned',current_setting('test.banned_balance')::jsonb) as result;
rollback;
