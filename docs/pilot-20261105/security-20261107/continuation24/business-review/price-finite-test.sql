begin;
set local lock_timeout='2s';set local statement_timeout='15s';
insert into auth.users(id,raw_user_meta_data) values('90000000-0000-0000-0000-000000002410','{"name":"Synthetic price-validation staff"}');
insert into staff_members(user_id,perms) values('90000000-0000-0000-0000-000000002410',array['stores']);
insert into stores(id,name,category,owner_id) values('90000000-0000-0000-0000-000000002411','Synthetic price-validation store','rest','90000000-0000-0000-0000-000000002410');
insert into menu_items(id,store_id,name,price) values('90000000-0000-0000-0000-000000002412','90000000-0000-0000-0000-000000002411','Synthetic item',10);
set local role authenticated;
select set_config('request.jwt.claims','{"sub":"90000000-0000-0000-0000-000000002410","role":"authenticated"}',true);
do $$declare col text;v text;r jsonb:='[]';outcome text;observed text;begin
foreach col in array array['menu_price','fee_base','fee_per_km'] loop
 foreach v in array array['NaN','Infinity','-Infinity','-1','0','10.25'] loop
  observed:=null;
  begin
   if col='menu_price' then update menu_items set price=v::numeric where id='90000000-0000-0000-0000-000000002412' returning price::text into observed;
   elsif col='fee_base' then update stores set fee_base=v::numeric where id='90000000-0000-0000-0000-000000002411' returning fee_base::text into observed;
   else update stores set fee_per_km=v::numeric where id='90000000-0000-0000-0000-000000002411' returning fee_per_km::text into observed;end if;
   raise exception using errcode='P2410',message='synthetic_rollback';
  exception when sqlstate 'P2410' then outcome:='accepted_then_rolled_back';when others then outcome:=sqlerrm;end;
  r:=r||jsonb_build_array(jsonb_build_object('field',col,'input',v,'outcome',outcome,'stored',observed));
 end loop;
end loop;
perform set_config('test.c24_price_results',r::text,true);
end $$;
reset role;
select current_setting('test.c24_price_results')::jsonb as results;
rollback;
