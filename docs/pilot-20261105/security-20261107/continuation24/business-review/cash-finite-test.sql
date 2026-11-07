begin;
set local lock_timeout='2s'; set local statement_timeout='15s';
-- Entire synthetic fixture and all delivery effects roll back. Never use orders 1/2/3.
select set_config('test.c24_config_before',md5(value::text),true) from pilot_private.config where id;
update pilot_private.config set value=jsonb_set(jsonb_set(value,'{customers}',value->'customers'||'"90000000-0000-0000-0000-000000002401"'::jsonb),'{stores}',value->'stores'||'"90000000-0000-0000-0000-000000002403"'::jsonb) where id;
insert into auth.users(id,raw_user_meta_data) values
('90000000-0000-0000-0000-000000002401','{"name":"Synthetic finite cash customer"}'),
('90000000-0000-0000-0000-000000002402','{"name":"Synthetic finite cash driver"}');
update profiles set role='driver',driver_status='approved' where id='90000000-0000-0000-0000-000000002402';
insert into stores(id,name,category) values('90000000-0000-0000-0000-000000002403','Synthetic finite cash store','rest');
insert into orders(id,store_id,customer_id,driver_id,status,lat,lng,payment,total,delivery_fee,driver_payout,subtotal) overriding system value values(-24001,'90000000-0000-0000-0000-000000002403','90000000-0000-0000-0000-000000002401','90000000-0000-0000-0000-000000002402','pickedup',38.56,68.79,'cash',40,15,15,0);
set local role authenticated;
select set_config('request.jwt.claims','{"sub":"90000000-0000-0000-0000-000000002402","role":"authenticated"}',true);
do $$declare v text;r jsonb:='[]';outcome text;observed text;begin
foreach v in array array['NaN','Infinity','-Infinity','-1','0','40'] loop
 observed:=null;
 begin
  perform deliver_order(-24001,v::numeric,'Synthetic validation note',null);
  select cash_collected::text into observed from orders where id=-24001;
  raise exception using errcode='P2401',message='synthetic_rollback';
 exception when sqlstate 'P2401' then outcome:='accepted_then_rolled_back';
 when others then outcome:=sqlerrm;
 end;
 r:=r||jsonb_build_array(jsonb_build_object('input',v,'outcome',outcome,'stored_cash',observed));
end loop;
perform set_config('test.c24_results',r::text,true);
end $$;
reset role;
select current_setting('test.c24_results')::jsonb as results;
rollback;
