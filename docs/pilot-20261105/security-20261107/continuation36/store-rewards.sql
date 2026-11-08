-- Test project only. No protected rows, orders or money. Always ROLLBACK.
begin;set local statement_timeout='15s';set local lock_timeout='2s';
insert into auth.users(id,raw_user_meta_data) values ('90000000-0000-0000-0000-000000003601','{"name":"ASVS36 synthetic store staff"}');
insert into staff_members(user_id,perms) values('90000000-0000-0000-0000-000000003601',array['stores']);
insert into stores(id,name,category,owner_id) values('90000000-0000-0000-0000-000000003602','ASVS36 synthetic rewards store','rest','90000000-0000-0000-0000-000000003601');
set local role authenticated;
select set_config('request.jwt.claims','{"sub":"90000000-0000-0000-0000-000000003601","role":"authenticated"}',true);
select set_store_earn('90000000-0000-0000-0000-000000003602',7);
select set_store_loyalty('90000000-0000-0000-0000-000000003602',100,5);
do $$declare v numeric;e text;begin
 foreach v in array array['NaN'::numeric,'Infinity'::numeric,'-Infinity'::numeric,-1::numeric,1001::numeric,1.5::numeric] loop
 e:=null;begin perform set_store_earn('90000000-0000-0000-0000-000000003602',v);exception when others then e:=sqlerrm;end;
 if e is distinct from 'bad_value' then raise exception 'ASSERT invalid earn %: %',v,e;end if;
 end loop;
 foreach v in array array['NaN'::numeric,'Infinity'::numeric,'-Infinity'::numeric,-1::numeric,51::numeric] loop
 e:=null;begin perform set_store_loyalty('90000000-0000-0000-0000-000000003602',100,v);exception when others then e:=sqlerrm;end;
 if e is distinct from 'bad_value' then raise exception 'ASSERT invalid cashback %: %',v,e;end if;
 end loop;
end $$;
reset role;select set_config('request.jwt.claims','{}',true);
do $$begin if not exists(select 1 from stores where id='90000000-0000-0000-0000-000000003602' and earn_per_tjs=7 and points_min_order=100 and cashback_pct=5) then raise exception 'ASSERT positive values/invalid value isolation';end if;end $$;
update staff_members set perms='{}' where user_id='90000000-0000-0000-0000-000000003601';
set local role authenticated;select set_config('request.jwt.claims','{"sub":"90000000-0000-0000-0000-000000003601","role":"authenticated"}',true);
do $$declare e text;begin
 begin perform set_store_earn('90000000-0000-0000-0000-000000003602',8);exception when others then e:=sqlerrm;end;if e is distinct from 'not_allowed' then raise exception 'ASSERT removed earn';end if;
 e:=null;begin perform set_store_loyalty('90000000-0000-0000-0000-000000003602',200,6);exception when others then e:=sqlerrm;end;if e is distinct from 'not_allowed' then raise exception 'ASSERT removed loyalty';end if;
end $$;
reset role;select set_config('request.jwt.claims','{}',true);
update staff_members set perms=array['stores'] where user_id='90000000-0000-0000-0000-000000003601';
update profiles set banned_at=now() where id='90000000-0000-0000-0000-000000003601';
set local role authenticated;select set_config('request.jwt.claims','{"sub":"90000000-0000-0000-0000-000000003601","role":"authenticated"}',true);
do $$declare e text;begin
 if account_enabled() then raise exception 'ASSERT ban fixture';end if;
 begin perform set_store_earn('90000000-0000-0000-0000-000000003602',8);exception when others then e:=sqlerrm;end;if e is distinct from 'not_allowed' then raise exception 'ASSERT banned earn';end if;
 e:=null;begin perform set_store_loyalty('90000000-0000-0000-0000-000000003602',200,6);exception when others then e:=sqlerrm;end;if e is distinct from 'not_allowed' then raise exception 'ASSERT banned loyalty';end if;
end $$;
reset role;select set_config('request.jwt.claims','{}',true);
do $$begin if not exists(select 1 from stores where id='90000000-0000-0000-0000-000000003602' and earn_per_tjs=7 and points_min_order=100 and cashback_pct=5) then raise exception 'ASSERT denied calls changed values';end if;end $$;
select jsonb_build_object('active_staff_write','PASS','invalid_earn_values_rejected',6,'invalid_cashback_values_rejected',5,'permission_removal_denial','PASS','banned_staff_denial','PASS','allowed_values_unchanged_after_denials',true,'scope','SQL role; no orders, wallet entries or HTTP JWT proof') result;
rollback;
