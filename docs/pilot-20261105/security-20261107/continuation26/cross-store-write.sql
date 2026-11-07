begin;
set local lock_timeout='2s';set local statement_timeout='15s';
insert into auth.users(id,raw_user_meta_data) values('90000000-0000-0000-0000-000000002601','{"name":"Synthetic merchant A"}'),('90000000-0000-0000-0000-000000002602','{"name":"Synthetic merchant B"}');
insert into stores(id,name,category,owner_id)values('90000000-0000-0000-0000-000000002611','Synthetic store A','rest','90000000-0000-0000-0000-000000002601'),('90000000-0000-0000-0000-000000002612','Synthetic store B','rest','90000000-0000-0000-0000-000000002602');
insert into menu_items(id,store_id,name,price)values('90000000-0000-0000-0000-000000002621','90000000-0000-0000-0000-000000002611','Synthetic item A',10),('90000000-0000-0000-0000-000000002622','90000000-0000-0000-0000-000000002612','Synthetic item B',20);
set local role authenticated;
select set_config('request.jwt.claims','{"sub":"90000000-0000-0000-0000-000000002601","role":"authenticated"}',true);
do $$declare n int;r jsonb:='{}';e text;begin
update menu_items set price=11 where id='90000000-0000-0000-0000-000000002621';get diagnostics n=row_count;if n<>1 then raise exception 'ASSERT own write failed';end if;r:=r||jsonb_build_object('own_update_rows',n);
update menu_items set price=99 where id='90000000-0000-0000-0000-000000002622';get diagnostics n=row_count;if n<>0 then raise exception 'ASSERT cross-store write';end if;r:=r||jsonb_build_object('foreign_update_rows',n);
delete from menu_items where id='90000000-0000-0000-0000-000000002622';get diagnostics n=row_count;if n<>0 then raise exception 'ASSERT foreign delete';end if;r:=r||jsonb_build_object('foreign_delete_rows',n);
begin update menu_items set store_id='90000000-0000-0000-0000-000000002612' where id='90000000-0000-0000-0000-000000002621';raise exception 'ASSERT reassignment accepted';exception when insufficient_privilege or raise_exception then if sqlerrm like 'ASSERT%' then raise;end if;e:=sqlerrm;end;r:=r||jsonb_build_object('reassignment_rejected',e);
begin insert into menu_items(id,store_id,name,price)values('90000000-0000-0000-0000-000000002623','90000000-0000-0000-0000-000000002612','Synthetic cross insertion',10);raise exception 'ASSERT foreign insertion accepted';exception when insufficient_privilege or raise_exception then if sqlerrm like 'ASSERT%' then raise;end if;e:=sqlerrm;end;r:=r||jsonb_build_object('foreign_insert_rejected',e);
perform set_config('test.c26_result',r::text,true);end $$;
reset role;
select current_setting('test.c26_result')::jsonb||jsonb_build_object('own_price',(select price from menu_items where id='90000000-0000-0000-0000-000000002621'),'foreign_price',(select price from menu_items where id='90000000-0000-0000-0000-000000002622')) as result;
rollback;
