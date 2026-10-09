\set ON_ERROR_STOP off
select set_config('app.bypass','1',false);
insert into auth.users(id,email) values
 ('a0000000-0000-0000-0000-000000000001','admin@t.com'),('a0000000-0000-0000-0000-000000000002','owner@t.com'),
 ('a0000000-0000-0000-0000-000000000003','other@t.com'),('a0000000-0000-0000-0000-000000000004','cust@t.com'),
 ('a0000000-0000-0000-0000-000000000005','staff@t.com');
insert into profiles(id,role,name,phone) values
 ('a0000000-0000-0000-0000-000000000001','admin','Admin','+992900000001'),
 ('a0000000-0000-0000-0000-000000000002','merchant','Owner','+992900000002'),
 ('a0000000-0000-0000-0000-000000000003','merchant','Other','+992900000003'),
 ('a0000000-0000-0000-0000-000000000004','customer','Cust','+992900000004'),
 ('a0000000-0000-0000-0000-000000000005','customer','Staff','+992900000005');
insert into stores(id,owner_id,name,category,lat,lng,commission_pct,fee_base,phone,description) values
 ('b0000000-0000-0000-0000-000000000001','a0000000-0000-0000-0000-000000000002','Kebab','rest',38.5700,68.7800,12,8,'+992900100001','Best kebab'),
 ('b0000000-0000-0000-0000-000000000002','a0000000-0000-0000-0000-000000000003','Pizza','rest',38.5800,68.7900,10,10,'+992900100002','Pizza');
insert into menu_items(id,store_id,name,price,section) values
 ('c0000000-0000-0000-0000-000000000001','b0000000-0000-0000-0000-000000000001','Shashlik',30,'Grill'),
 ('c0000000-0000-0000-0000-000000000002','b0000000-0000-0000-0000-000000000001','Lagman',25,'Soups'),
 ('c0000000-0000-0000-0000-000000000003','b0000000-0000-0000-0000-000000000002','Margherita',40,'Pizza');
insert into item_option_groups(id,item_id,name,required,max_sel,sort) values ('d0000000-0000-0000-0000-000000000001','c0000000-0000-0000-0000-000000000001','Size',true,1,0);
insert into item_options(group_id,name,price_delta) values ('d0000000-0000-0000-0000-000000000001','Large',5),('d0000000-0000-0000-0000-000000000001','Small',0);
update stores set created_at = now() - interval '30 days';
select set_config('app.bypass','',false);
create table if not exists res(n serial, ok boolean, label text, got text, want text);
create or replace function chk(label text, uid text, q text, want text) returns void language plpgsql as $f$
declare r text;
begin
  execute 'set local role ' || case when uid is null then 'anon' else 'authenticated' end;
  perform set_config('request.jwt.claim.sub', coalesce(uid,''), true);
  begin execute q into r; r := coalesce(r,'');
  exception when others then r := 'ERR:' || sqlerrm; end;
  reset role;
  insert into res(ok,label,got,want) values (r = want or (want = 'ANYERR' and r like 'ERR:%') or (want = 'NOERR' and r not like 'ERR:%'), label, r, want);
end $f$;
\set A '''a0000000-0000-0000-0000-000000000001'''
\set O '''a0000000-0000-0000-0000-000000000002'''
\set X '''a0000000-0000-0000-0000-000000000003'''
\set C '''a0000000-0000-0000-0000-000000000004'''
\set S '''a0000000-0000-0000-0000-000000000005'''
-- staff with stores perm (patch 26) must NOT manage brands
select chk('admin staff_set stores perm', :A, $$select staff_set('staff@t.com','{stores}')::text$$, '');
-- brands: admin only
select chk('customer cannot brand_create', :C, $$select brand_create('Kebab House','owner@t.com')::text$$, 'ERR:not_allowed');
select chk('owner cannot brand_create', :O, $$select brand_create('Kebab House','owner@t.com')::text$$, 'ERR:not_allowed');
select chk('stores-staff cannot brand_create', :S, $$select brand_create('Kebab House','owner@t.com')::text$$, 'ERR:not_allowed');
select chk('anon cannot brand_create', null, $$select brand_create('Kebab House','owner@t.com')::text$$, 'ANYERR');
select chk('brand_create bad name', :A, $$select brand_create('x','owner@t.com')::text$$, 'ERR:bad_value');
select chk('brand_create unknown owner', :A, $$select brand_create('Kebab House','nobody@t.com')::text$$, 'ERR:user_not_found');
select chk('admin brand_create', :A, $$select (brand_create('Kebab House','owner@t.com') is not null)::text$$, 'true');
create temp table bid as select id from brands limit 1;
select set_config('t.brand',(select id::text from bid),false);
select chk('brand_attach owner mismatch', :A, format($$select brand_attach('b0000000-0000-0000-0000-000000000002','%s','Pizza')::text$$, current_setting('t.brand')), 'ERR:owner_mismatch');
select chk('owner cannot attach (admin only)', :O, format($$select brand_attach('b0000000-0000-0000-0000-000000000001','%s','Main')::text$$, current_setting('t.brand')), 'ERR:not_allowed');
select chk('admin attaches main store', :A, format($$select brand_attach('b0000000-0000-0000-0000-000000000001','%s','Main')::text$$, current_setting('t.brand')), '');
-- branch creation permissions
select chk('other merchant cannot branch_create', :X, format($$select branch_create('%s','Evil','addr',38.6,68.8,'+992900555555')::text$$, current_setting('t.brand')), 'ERR:not_allowed');
select chk('customer cannot branch_create', :C, format($$select branch_create('%s','Evil','addr',38.6,68.8,'+992900555555')::text$$, current_setting('t.brand')), 'ERR:not_allowed');
select chk('stores-staff cannot branch_create', :S, format($$select branch_create('%s','Evil','addr',38.6,68.8,'+992900555555')::text$$, current_setting('t.brand')), 'ERR:not_allowed');
select chk('anon cannot branch_create', null, format($$select branch_create('%s','Evil','addr',38.6,68.8,'+992900555555')::text$$, current_setting('t.brand')), 'ANYERR');
-- validation
select chk('bad latitude', :O, format($$select branch_create('%s','Bad','a',95,68.8,'+992900555555')::text$$, current_setting('t.brand')), 'ERR:bad_value');
select chk('null coordinates', :O, format($$select branch_create('%s','Bad','a',null,null,'+992900555555')::text$$, current_setting('t.brand')), 'ERR:bad_value');
select chk('missing phone', :O, format($$select branch_create('%s','Bad','a',38.6,68.8,'abc')::text$$, current_setting('t.brand')), 'ERR:bad_phone');
select chk('empty branch name', :O, format($$select branch_create('%s','   ','a',38.6,68.8,'+992900555555')::text$$, current_setting('t.brand')), 'ERR:bad_value');
select chk('branch name too long', :O, format($$select branch_create('%s',repeat('x',41),'a',38.6,68.8,'+992900555555')::text$$, current_setting('t.brand')), 'ERR:bad_value');
select chk('sql-ish branch name stored as plain text', :O, format($$select (branch_create('%s','Rudaki''; drop table orders;--','a',38.60,68.80,'+992900555551') is not null)::text$$, current_setting('t.brand')), 'true');
select chk('orders table still exists', :A, $$select count(*)::text from orders$$, '0');
select chk('owner creates branch (Rudaki)', :O, format($$select (branch_create('%s','Rudaki','Rudaki 10',38.5900,68.7700,'+992900555552') is not null)::text$$, current_setting('t.brand')), 'true');
select chk('duplicate branch name refused', :O, format($$select branch_create('%s','Rudaki','x',38.6,68.8,'+992900555553')::text$$, current_setting('t.brand')), 'ERR:name_taken');
-- the copy
select chk('branch inherits terms, starts closed', :A, $$select (commission_pct=12 and fee_base=8 and is_open=false and is_active and owner_id='a0000000-0000-0000-0000-000000000002' and category='rest' and description='Best kebab')::text from stores where name='Kebab House · Rudaki'$$, 'true');
select chk('branch menu copied (2 dishes)', :A, $$select count(*)::text from menu_items where store_id=(select id from stores where name='Kebab House · Rudaki')$$, '2');
select chk('options copied (1 group, 2 options)', :A, $$select (select count(*) from item_option_groups g join menu_items m on m.id=g.item_id where m.store_id=(select id from stores where name='Kebab House · Rudaki'))::text||'/'||(select count(*) from item_options o join item_option_groups g on g.id=o.group_id join menu_items m on m.id=g.item_id where m.store_id=(select id from stores where name='Kebab House · Rudaki'))::text$$, '1/2');
select chk('original menu untouched', :A, $$select count(*)::text from menu_items where store_id='b0000000-0000-0000-0000-000000000001'$$, '2');
select chk('copied ids are new', :A, $$select count(*)::text from menu_items where id in ('c0000000-0000-0000-0000-000000000001','c0000000-0000-0000-0000-000000000002') and store_id<>'b0000000-0000-0000-0000-000000000001'$$, '0');
select chk('owner cannot raise commission of branch', :O, $$with u as (update stores set commission_pct=0 where name='Kebab House · Rudaki' returning 1) select count(*)::text from u$$, '0');
select chk('owner cannot set brand_id directly', :O, $$with u as (update stores set brand_id=null where name='Kebab House · Rudaki' returning 1) select count(*)::text from u$$, '0');
select chk('direct insert into brands denied', :O, $$insert into brands(name,owner_id) values ('Evil','a0000000-0000-0000-0000-000000000002')$$, 'ANYERR');
select chk('direct update of brands denied', :O, $$update brands set owner_id='a0000000-0000-0000-0000-000000000003'$$, 'ANYERR');
-- daily limit: 2 branches exist so far (Rudaki, the sql-ish one) -> 3 more allowed, the 4th extra is refused
select chk('branch #3', :O, format($$select (branch_create('%s','B3','a',38.61,68.81,'+992900555561') is not null)::text$$, current_setting('t.brand')), 'true');
select chk('branch #4', :O, format($$select (branch_create('%s','B4','a',38.62,68.82,'+992900555562') is not null)::text$$, current_setting('t.brand')), 'true');
select chk('branch #5', :O, format($$select (branch_create('%s','B5','a',38.63,68.83,'+992900555563') is not null)::text$$, current_setting('t.brand')), 'true');
select chk('main store counts: 6th in a day refused', :O, format($$select branch_create('%s','B6','a',38.64,68.84,'+992900555564')::text$$, current_setting('t.brand')), 'ERR:too_many');
-- sync
select set_config('app.bypass','1',false);
update menu_items set price=35 where id='c0000000-0000-0000-0000-000000000001';
insert into menu_items(store_id,name,price) values ('b0000000-0000-0000-0000-000000000001','Plov',28);
select set_config('app.bypass','',false);
select set_config('t.rud',(select id::text from stores where name='Kebab House · Rudaki'),false);
select chk('other merchant cannot sync', :X, format($$select brand_sync_menu('b0000000-0000-0000-0000-000000000001','%s')::text$$, current_setting('t.rud')), 'ERR:not_allowed');
select chk('customer cannot sync', :C, format($$select brand_sync_menu('b0000000-0000-0000-0000-000000000001','%s')::text$$, current_setting('t.rud')), 'ERR:not_allowed');
select chk('cannot sync across brands', :O, $$select brand_sync_menu('b0000000-0000-0000-0000-000000000001','b0000000-0000-0000-0000-000000000002')::text$$, 'ERR:bad_value');
select chk('owner syncs: 1 updated, 1 added', :O, format($$select brand_sync_menu('b0000000-0000-0000-0000-000000000001','%s')::text$$, current_setting('t.rud')), '{"added": 1, "updated": 1}');
select chk('price synced', :A, format($$select price::text from menu_items where store_id='%s' and name='Shashlik'$$, current_setting('t.rud')), '35');
select chk('new dish synced', :A, format($$select count(*)::text from menu_items where store_id='%s' and name='Plov'$$, current_setting('t.rud')), '1');
select chk('second sync is a no-op', :O, format($$select brand_sync_menu('b0000000-0000-0000-0000-000000000001','%s')::text$$, current_setting('t.rud')), '{"added": 0, "updated": 0}');
-- routing (customer at 38.5905,68.7705 ~ next to Rudaki)
select chk('route: all branches closed except main -> main first', :C, format($$select (select name from brand_route('%s',38.5905,68.7705,'{}') limit 1)$$, current_setting('t.brand')), 'Kebab');
select chk('owner opens Rudaki', :O, format($$select set_store_open('%s',true)::text$$, current_setting('t.rud')), '');
select chk('route: nearest open = Rudaki', :C, format($$select (select name from brand_route('%s',38.5905,68.7705,'{}') limit 1)$$, current_setting('t.brand')), 'Kebab House · Rudaki');
select chk('route: customer far away near main -> main', :C, format($$select (select name from brand_route('%s',38.5700,68.7800,'{}') limit 1)$$, current_setting('t.brand')), 'Kebab');
select chk('route: nearest closed is skipped', :C, format($$select (select name from brand_route('%s',38.5905,68.7705,'{}') where is_open limit 1)$$, current_setting('t.brand')), 'Kebab House · Rudaki');
select set_config('app.bypass','1',false);
update menu_items set available=false where store_id=current_setting('t.rud')::uuid and name='Lagman';
select set_config('app.bypass','',false);
select chk('route: cart with Lagman -> branch missing it goes second', :C, format($$select (select name from brand_route('%s',38.5905,68.7705,'{Lagman,Shashlik}') limit 1)$$, current_setting('t.brand')), 'Kebab');
select chk('route: reports what is missing', :C, format($$select missing::text from brand_route('%s',38.5905,68.7705,'{Lagman,Shashlik}') where name='Kebab House · Rudaki'$$, current_setting('t.brand')), '{lagman}');
select chk('route: anon sees nothing', null, format($$select count(*)::text from brand_route('%s',38.59,68.77,'{}')$$, current_setting('t.brand')), 'ANYERR');
select chk('route: huge name list is capped', :C, format($$select count(*)::text from brand_route('%s',38.59,68.77,(select array_agg('x'||g) from generate_series(1,500) g))$$, current_setting('t.brand')), '6');
-- stats
select chk('stats: owner sees 5 branches + main = 6', :O, format($$select count(*)::text from brand_stats('%s',30)$$, current_setting('t.brand')), '6');
select chk('stats: other merchant sees none', :X, format($$select count(*)::text from brand_stats('%s',30)$$, current_setting('t.brand')), '0');
select chk('stats: customer sees none', :C, format($$select count(*)::text from brand_stats('%s',30)$$, current_setting('t.brand')), '0');
select chk('stats: admin sees all', :A, format($$select count(*)::text from brand_stats('%s',30)$$, current_setting('t.brand')), '6');
select chk('stats: days is clamped (no error)', :O, format($$select count(*)::text from brand_stats('%s',-5)$$, current_setting('t.brand')), '6');
-- visibility
select chk('customers can read brands', :C, $$select count(*)::text from brands$$, '1');
select chk('anon cannot read brands', null, $$select count(*)::text from brands$$, '0');
select chk('customers see active branches', :C, $$select count(*)::text from stores where brand_id is not null$$, '6');
-- detach
select chk('owner cannot detach', :O, format($$select brand_detach('%s')::text$$, current_setting('t.rud')), 'ERR:not_allowed');
select chk('admin detaches', :A, format($$select brand_detach('%s')::text$$, current_setting('t.rud')), '');
select chk('detached store no longer routed', :C, format($$select count(*)::text from brand_route('%s',38.59,68.77,'{}')$$, current_setting('t.brand')), '5');
select chk('audit trail has brand events', :A, $$select (count(*) >= 8)::text from audit_log where action like 'BRAND%' or action like 'BRANCH%'$$, 'true');
-- existing order flow guards still intact for a branch: an outsider cannot edit the branch menu
select chk('other merchant cannot edit branch menu', :X, $$with u as (update menu_items set price=1 where store_id=(select id from stores where name='Kebab House · B3') returning 1) select count(*)::text from u$$, '0');
select chk('owner can edit branch menu', :O, $$with u as (update menu_items set price=31 where store_id=(select id from stores where name='Kebab House · B3') and name='Shashlik' returning 1) select count(*)::text from u$$, '1');
select count(*) filter (where ok) as pass, count(*) filter (where not ok) as fail from res;
select n,label,got,want from res where not ok order by n;
