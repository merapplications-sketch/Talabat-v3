\set ON_ERROR_STOP off
set client_min_messages = notice;
-- ---------- seed (as superuser, no RLS) ----------
select set_config('app.bypass','1',false);
insert into auth.users(id,email) values
 ('a0000000-0000-0000-0000-000000000001','admin@t.com'),('a0000000-0000-0000-0000-000000000002','sup@t.com'),
 ('a0000000-0000-0000-0000-000000000003','ord@t.com'),('a0000000-0000-0000-0000-000000000004','fin@t.com'),
 ('a0000000-0000-0000-0000-000000000005','sto@t.com'),('a0000000-0000-0000-0000-000000000006','con@t.com'),
 ('a0000000-0000-0000-0000-000000000007','off@t.com'),('a0000000-0000-0000-0000-000000000008','cust@t.com'),
 ('a0000000-0000-0000-0000-000000000009','cust2@t.com'),('a0000000-0000-0000-0000-00000000000a','merch@t.com'),
 ('a0000000-0000-0000-0000-00000000000b','drv@t.com'),('a0000000-0000-0000-0000-00000000000c','rnd@t.com');
insert into profiles(id,role,name,phone) values
 ('a0000000-0000-0000-0000-000000000001','admin','Admin','+992900000001'),
 ('a0000000-0000-0000-0000-000000000002','customer','Sup','+992900000002'),
 ('a0000000-0000-0000-0000-000000000003','customer','Ord','+992900000003'),
 ('a0000000-0000-0000-0000-000000000004','customer','Fin','+992900000004'),
 ('a0000000-0000-0000-0000-000000000005','customer','Sto','+992900000005'),
 ('a0000000-0000-0000-0000-000000000006','customer','Con','+992900000006'),
 ('a0000000-0000-0000-0000-000000000007','customer','Off','+992900000007'),
 ('a0000000-0000-0000-0000-000000000008','customer','Cust','+992900000008'),
 ('a0000000-0000-0000-0000-000000000009','customer','Cust2','+992900000009'),
 ('a0000000-0000-0000-0000-00000000000a','merchant','Merch','+992900000010'),
 ('a0000000-0000-0000-0000-00000000000b','driver','Drv','+992900000011'),
 ('a0000000-0000-0000-0000-00000000000c','customer','Rnd','+992900000012');
update profiles set driver_status='approved' where id='a0000000-0000-0000-0000-00000000000b';
insert into stores(id,owner_id,name,category,lat,lng) values
 ('b0000000-0000-0000-0000-000000000001','a0000000-0000-0000-0000-00000000000a','Store1','rest',38.57,68.78);
insert into menu_items(id,store_id,name,price) values ('c0000000-0000-0000-0000-000000000001','b0000000-0000-0000-0000-000000000001','Dish',10);
insert into orders(store_id,customer_id,status,total,subtotal,delivery_fee,payment) values
 ('b0000000-0000-0000-0000-000000000001','a0000000-0000-0000-0000-000000000008','pending',50,45,5,'cash'),
 ('b0000000-0000-0000-0000-000000000001','a0000000-0000-0000-0000-000000000009','pending',60,55,5,'cash');
insert into orders(store_id,customer_id,driver_id,status,total,subtotal,delivery_fee,payment,cash_collected)
 values ('b0000000-0000-0000-0000-000000000001','a0000000-0000-0000-0000-000000000008','a0000000-0000-0000-0000-00000000000b','delivered',40,35,5,'cash',40);
insert into support_tickets(customer_id,reason,order_id) values ('a0000000-0000-0000-0000-000000000008','other',(select min(id) from orders));
select set_config('app.bypass','',false);
-- ---------- harness ----------
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
-- ---------- admin creates staff ----------
select chk('admin staff_set sup','a0000000-0000-0000-0000-000000000001',$$select staff_set('sup@t.com','{support}')::text$$,'');
select chk('admin staff_set ord','a0000000-0000-0000-0000-000000000001',$$select staff_set('ord@t.com','{orders}')::text$$,'');
select chk('admin staff_set fin','a0000000-0000-0000-0000-000000000001',$$select staff_set('fin@t.com','{finance}')::text$$,'');
select chk('admin staff_set sto','a0000000-0000-0000-0000-000000000001',$$select staff_set('sto@t.com','{stores}')::text$$,'');
select chk('admin staff_set con','a0000000-0000-0000-0000-000000000001',$$select staff_set('con@t.com','{content}')::text$$,'');
select chk('admin staff_set off (inactive)','a0000000-0000-0000-0000-000000000001',$$select staff_set('off@t.com','{support,orders,finance,stores,content}',false)::text$$,'');
select chk('staff_set bad perm','a0000000-0000-0000-0000-000000000001',$$select staff_set('cust@t.com','{superuser}')::text$$,'ERR:bad_value');
select chk('staff_set empty perms active','a0000000-0000-0000-0000-000000000001',$$select staff_set('cust@t.com','{}')::text$$,'ERR:bad_value');
select chk('staff_set admin target','a0000000-0000-0000-0000-000000000001',$$select staff_set('admin@t.com','{support}')::text$$,'ERR:bad_value');
select chk('staff_set unknown email','a0000000-0000-0000-0000-000000000001',$$select staff_set('nobody@t.com','{support}')::text$$,'ERR:user_not_found');
select chk('staff_set bad email','a0000000-0000-0000-0000-000000000001',$$select staff_set('x; drop table orders;--','{support}')::text$$,'ERR:bad_value');
-- ---------- who may manage staff ----------
select chk('support cannot staff_set','a0000000-0000-0000-0000-000000000002',$$select staff_set('cust@t.com','{support}')::text$$,'ERR:not_allowed');
select chk('customer cannot staff_set','a0000000-0000-0000-0000-000000000008',$$select staff_set('cust@t.com','{support}')::text$$,'ERR:not_allowed');
select chk('anon cannot staff_set',null,$$select staff_set('cust@t.com','{support}')::text$$,'ANYERR');
select chk('support cannot staff_remove','a0000000-0000-0000-0000-000000000002',$$select staff_remove('a0000000-0000-0000-0000-000000000004')::text$$,'ERR:not_allowed');
select chk('staff_list admin sees 6','a0000000-0000-0000-0000-000000000001',$$select count(*)::text from staff_list()$$,'6');
select chk('staff_list support sees 0','a0000000-0000-0000-0000-000000000002',$$select count(*)::text from staff_list()$$,'0');
select chk('staff_members: staff sees only own','a0000000-0000-0000-0000-000000000002',$$select count(*)::text from staff_members$$,'1');
select chk('staff_members: customer sees none','a0000000-0000-0000-0000-000000000008',$$select count(*)::text from staff_members$$,'0');
select chk('direct insert staff_members denied','a0000000-0000-0000-0000-000000000008',$$insert into staff_members(user_id,perms) values ('a0000000-0000-0000-0000-000000000008','{orders}')$$,'ANYERR');
select chk('self-escalate perms denied','a0000000-0000-0000-0000-000000000002',$$update staff_members set perms='{orders,support,finance,stores,content}' where user_id='a0000000-0000-0000-0000-000000000002'$$,'ANYERR');
select chk('staff cannot make self admin','a0000000-0000-0000-0000-000000000002',$$update profiles set role='admin' where id='a0000000-0000-0000-0000-000000000002'$$,'ANYERR');
select chk('staff cannot make other admin (0 rows)','a0000000-0000-0000-0000-000000000002',$$with u as (update profiles set role='admin' where id='a0000000-0000-0000-0000-000000000008' returning 1) select count(*)::text from u$$,'0');
-- ---------- my_perms ----------
select chk('my_perms admin','a0000000-0000-0000-0000-000000000001',$$select cardinality(my_perms())::text$$,'5');
select chk('my_perms support','a0000000-0000-0000-0000-000000000002',$$select my_perms()::text$$,'{support}');
select chk('my_perms inactive staff','a0000000-0000-0000-0000-000000000007',$$select coalesce(my_perms()::text,'NULL')$$,'NULL');
select chk('my_perms random customer','a0000000-0000-0000-0000-00000000000c',$$select coalesce(my_perms()::text,'NULL')$$,'NULL');
select chk('my_perms anon',null,$$select coalesce(my_perms()::text,'NULL')$$,'NULL');
-- ---------- orders visibility ----------
select chk('orders: admin sees 3','a0000000-0000-0000-0000-000000000001',$$select count(*)::text from orders$$,'3');
select chk('orders: orders-staff sees 3','a0000000-0000-0000-0000-000000000003',$$select count(*)::text from orders$$,'3');
select chk('orders: support sees 3','a0000000-0000-0000-0000-000000000002',$$select count(*)::text from orders$$,'3');
select chk('orders: finance sees 0','a0000000-0000-0000-0000-000000000004',$$select count(*)::text from orders$$,'0');
select chk('orders: stores-staff sees 0','a0000000-0000-0000-0000-000000000005',$$select count(*)::text from orders$$,'0');
select chk('orders: content sees 0','a0000000-0000-0000-0000-000000000006',$$select count(*)::text from orders$$,'0');
select chk('orders: inactive staff sees 0','a0000000-0000-0000-0000-000000000007',$$select count(*)::text from orders$$,'0');
select chk('orders: random customer 0','a0000000-0000-0000-0000-00000000000c',$$select count(*)::text from orders$$,'0');
select chk('orders: customer sees own 2','a0000000-0000-0000-0000-000000000008',$$select count(*)::text from orders$$,'2');
select chk('orders: merchant sees store 3','a0000000-0000-0000-0000-00000000000a',$$select count(*)::text from orders$$,'3');
select chk('orders: anon 0',null,$$select count(*)::text from orders$$,'0');
-- ---------- order actions ----------
select chk('orders-staff cancels pending','a0000000-0000-0000-0000-000000000003',$$select set_order_status((select min(id) from orders),'cancelled')::text$$,'');
select chk('orders-staff cannot mark delivered','a0000000-0000-0000-0000-000000000003',$$select set_order_status((select max(id) from orders where status='pending'),'delivered')::text$$,'ERR:bad_transition');
select chk('support cannot cancel','a0000000-0000-0000-0000-000000000002',$$select set_order_status((select max(id) from orders where status='pending'),'cancelled')::text$$,'ERR:bad_transition');
select chk('finance cannot cancel','a0000000-0000-0000-0000-000000000004',$$select set_order_status((select max(id) from orders),'cancelled')::text$$,'ANYERR');
select chk('support cannot assign courier','a0000000-0000-0000-0000-000000000002',$$select admin_assign_driver((select max(id) from orders),'a0000000-0000-0000-0000-00000000000b')::text$$,'ERR:not_allowed');
select chk('orders-staff assign courier passes permission','a0000000-0000-0000-0000-000000000003',$$select admin_assign_driver((select max(id) from orders),'a0000000-0000-0000-0000-00000000000b')::text$$,'ERR:bad_transition');
select chk('orders-staff sees phones','a0000000-0000-0000-0000-000000000003',$$select (order_contacts((select max(id) from orders))->>'customer_phone') is null or true from orders limit 1$$,'NOERR');
select chk('content cannot read contacts','a0000000-0000-0000-0000-000000000006',$$select count(*)::text from contacts_for(array[(select max(id) from orders)])$$,'0');
select chk('offers_read orders-staff ok','a0000000-0000-0000-0000-000000000003',$$select count(*)::text from order_offers$$,'0');
-- ---------- support ----------
select chk('tickets: admin 1','a0000000-0000-0000-0000-000000000001',$$select count(*)::text from support_tickets$$,'1');
select chk('tickets: support 1','a0000000-0000-0000-0000-000000000002',$$select count(*)::text from support_tickets$$,'1');
select chk('tickets: orders-staff 0','a0000000-0000-0000-0000-000000000003',$$select count(*)::text from support_tickets$$,'0');
select chk('tickets: finance 0','a0000000-0000-0000-0000-000000000004',$$select count(*)::text from support_tickets$$,'0');
select chk('tickets: owner customer 1','a0000000-0000-0000-0000-000000000008',$$select count(*)::text from support_tickets$$,'1');
select chk('tickets: other customer 0','a0000000-0000-0000-0000-000000000009',$$select count(*)::text from support_tickets$$,'0');
select chk('support replies','a0000000-0000-0000-0000-000000000002',$$select ticket_staff_reply((select min(id) from support_tickets),'hello')::text$$,'');
select chk('orders-staff cannot reply','a0000000-0000-0000-0000-000000000003',$$select ticket_staff_reply((select min(id) from support_tickets),'hello')::text$$,'ERR:not_allowed');
select chk('finance cannot reply','a0000000-0000-0000-0000-000000000004',$$select ticket_staff_reply((select min(id) from support_tickets),'hello')::text$$,'ERR:not_allowed');
select chk('support in_progress','a0000000-0000-0000-0000-000000000002',$$select ticket_set_status((select min(id) from support_tickets),'in_progress')::text$$,'');
select chk('content cannot set status','a0000000-0000-0000-0000-000000000006',$$select ticket_set_status((select min(id) from support_tickets),'resolved')::text$$,'ERR:not_allowed');
select chk('support refund over order total refused','a0000000-0000-0000-0000-000000000002',$$select ticket_set_status((select min(id) from support_tickets),'resolved','x',9999)::text$$,'ERR:refund_too_high');
select chk('support partial refund ok','a0000000-0000-0000-0000-000000000002',$$select ticket_set_status((select min(id) from support_tickets),'resolved','ok',10)::text$$,'');
select chk('wallet got the refund','a0000000-0000-0000-0000-000000000008',$$select wallet_balance()::text$$,'10.00');
select chk('support reads customers 8','a0000000-0000-0000-0000-000000000002',$$select count(*)::text from profiles where role='customer'$$,'9');
select chk('support cannot read drivers','a0000000-0000-0000-0000-000000000002',$$select count(*)::text from profiles where role='driver'$$,'0');
select chk('support cannot read merchants/admin','a0000000-0000-0000-0000-000000000002',$$select count(*)::text from profiles where role in ('merchant','admin')$$,'0');
select chk('orders-staff reads drivers','a0000000-0000-0000-0000-000000000003',$$select count(*)::text from profiles where role='driver'$$,'1');
select chk('orders-staff cannot read customers','a0000000-0000-0000-0000-000000000003',$$select count(*)::text from profiles where role='customer'$$,'1');
select chk('content sees only itself','a0000000-0000-0000-0000-000000000006',$$select count(*)::text from profiles$$,'1');
select chk('support admin_customers','a0000000-0000-0000-0000-000000000002',$$select (count(*)>0)::text from admin_customers()$$,'true');
select chk('finance admin_customers denied=empty','a0000000-0000-0000-0000-000000000004',$$select count(*)::text from admin_customers()$$,'0');
select chk('support bans customer','a0000000-0000-0000-0000-000000000002',$$select set_customer_ban('a0000000-0000-0000-0000-00000000000c',true,'abuse test')::text$$,'');
select chk('finance cannot ban','a0000000-0000-0000-0000-000000000004',$$select set_customer_ban('a0000000-0000-0000-0000-00000000000c',false,'x')::text$$,'ERR:not_allowed');
select chk('support cannot override phone','a0000000-0000-0000-0000-000000000002',$$select admin_set_customer_phone('a0000000-0000-0000-0000-00000000000c','+992900000099','test reason ok')::text$$,'ERR:not_allowed');
select chk('wallet_read: support sees entries','a0000000-0000-0000-0000-000000000002',$$select (count(*)>0)::text from wallet_entries$$,'true');
select chk('wallet_read: orders-staff 0','a0000000-0000-0000-0000-000000000003',$$select count(*)::text from wallet_entries$$,'0');
-- ---------- finance ----------
select chk('cash_balances: admin 1','a0000000-0000-0000-0000-000000000001',$$select count(*)::text from cash_balances()$$,'1');
select chk('cash_balances: finance 1','a0000000-0000-0000-0000-000000000004',$$select count(*)::text from cash_balances()$$,'1');
select chk('cash_balances: orders 0','a0000000-0000-0000-0000-000000000003',$$select count(*)::text from cash_balances()$$,'0');
select chk('cash_balances: support 0','a0000000-0000-0000-0000-000000000002',$$select count(*)::text from cash_balances()$$,'0');
select chk('support cannot settle','a0000000-0000-0000-0000-000000000002',$$select settle_driver_cash('a0000000-0000-0000-0000-00000000000b')::text$$,'ERR:not_allowed');
select chk('wallet_adjust support denied','a0000000-0000-0000-0000-000000000002',$$select wallet_adjust('a0000000-0000-0000-0000-000000000008',5,'manual test')::text$$,'ERR:not_allowed');
select chk('wallet_adjust finance ok','a0000000-0000-0000-0000-000000000004',$$select wallet_adjust('a0000000-0000-0000-0000-000000000008',5,'manual test')::text$$,'');
select chk('wallet_adjust negative below zero refused','a0000000-0000-0000-0000-000000000004',$$select wallet_adjust('a0000000-0000-0000-0000-000000000008',-99999,'manual test')::text$$,'ERR:insufficient_funds');
select chk('finance settles','a0000000-0000-0000-0000-000000000004',$$select settle_driver_cash('a0000000-0000-0000-0000-00000000000b')::text$$,'40');
-- ---------- stores ----------
select chk('stores-staff edits store','a0000000-0000-0000-0000-000000000005',$$with u as (update stores set description='x' where id='b0000000-0000-0000-0000-000000000001' returning 1) select count(*)::text from u$$,'1');
select chk('content cannot edit store','a0000000-0000-0000-0000-000000000006',$$with u as (update stores set description='y' where id='b0000000-0000-0000-0000-000000000001' returning 1) select count(*)::text from u$$,'0');
select chk('stores-staff cannot change commission','a0000000-0000-0000-0000-000000000005',$$with u as (update stores set commission_pct=1 where id='b0000000-0000-0000-0000-000000000001' returning 1) select count(*)::text from u$$,'ANYERR');
select chk('stores-staff cannot change discount','a0000000-0000-0000-0000-000000000005',$$with u as (update stores set discount_pct=90 where id='b0000000-0000-0000-0000-000000000001' returning 1) select count(*)::text from u$$,'ANYERR');
select chk('stores-staff cannot delete store','a0000000-0000-0000-0000-000000000005',$$with d as (delete from stores where id='b0000000-0000-0000-0000-000000000001' returning 1) select count(*)::text from d$$,'0');
select chk('stores-staff cannot take ownership','a0000000-0000-0000-0000-000000000005',$$select assign_owner('b0000000-0000-0000-0000-000000000001','sto@t.com')::text$$,'ERR:not_allowed');
select chk('stores-staff creates store','a0000000-0000-0000-0000-000000000005',$$with i as (insert into stores(name,category) values ('S2','rest') returning 1) select count(*)::text from i$$,'1');
select chk('support cannot create store','a0000000-0000-0000-0000-000000000002',$$insert into stores(name,category) values ('S3','rest')$$,'ANYERR');
select chk('stores-staff edits menu','a0000000-0000-0000-0000-000000000005',$$with u as (update menu_items set price=11 where id='c0000000-0000-0000-0000-000000000001' returning 1) select count(*)::text from u$$,'1');
select chk('support cannot edit menu','a0000000-0000-0000-0000-000000000002',$$with u as (update menu_items set price=12 where id='c0000000-0000-0000-0000-000000000001' returning 1) select count(*)::text from u$$,'0');
select chk('stores-staff sees private','a0000000-0000-0000-0000-000000000005',$$select (count(*)>0)::text from store_private()$$,'true');
select chk('support sees no store_private','a0000000-0000-0000-0000-000000000002',$$select count(*)::text from store_private()$$,'0');
select chk('stores-staff cannot read owner info','a0000000-0000-0000-0000-000000000005',$$select count(*)::text from store_owner_info('b0000000-0000-0000-0000-000000000001')$$,'0');
-- ---------- content ----------
select chk('content adds banner','a0000000-0000-0000-0000-000000000006',$$with i as (insert into banners(title) values ('b') returning 1) select count(*)::text from i$$,'1');
select chk('stores-staff cannot add banner','a0000000-0000-0000-0000-000000000005',$$insert into banners(title) values ('b2')$$,'ANYERR');
select chk('content adds promo','a0000000-0000-0000-0000-000000000006',$$with i as (insert into promo_codes(code,kind,value) values ('PROMOX','percent',10) returning 1) select count(*)::text from i$$,'1');
select chk('support cannot add promo','a0000000-0000-0000-0000-000000000002',$$insert into promo_codes(code,kind,value) values ('PROMOY','percent',10)$$,'ANYERR');
select chk('content sets page','a0000000-0000-0000-0000-000000000006',$$select set_page('about','ru','Hello text')::text$$,'');
select chk('support cannot set page','a0000000-0000-0000-0000-000000000002',$$select set_page('about','ru','Hello text')::text$$,'ERR:not_allowed');
-- ---------- never delegated ----------
select chk('content cannot set_setting','a0000000-0000-0000-0000-000000000006',$$select set_setting('delivery_step_price',3)::text$$,'ERR:not_allowed');
select chk('all-perm inactive staff cannot set_setting','a0000000-0000-0000-0000-000000000007',$$select set_setting('delivery_step_price',3)::text$$,'ERR:not_allowed');
select chk('audit_log: admin reads','a0000000-0000-0000-0000-000000000001',$$select (count(*)>0)::text from audit_log$$,'true');
select chk('audit_log: staff 0','a0000000-0000-0000-0000-000000000002',$$select count(*)::text from audit_log$$,'0');
select chk('audit_log: staff cannot write','a0000000-0000-0000-0000-000000000002',$$insert into audit_log(user_id,action,table_name) values (null,'X','y')$$,'ANYERR');
select chk('client_errors: staff 0','a0000000-0000-0000-0000-000000000002',$$select count(*)::text from client_errors$$,'0');
select chk('addresses admin read: staff 0','a0000000-0000-0000-0000-000000000002',$$select count(*)::text from addresses$$,'0');
select chk('inactive staff cannot reply','a0000000-0000-0000-0000-000000000007',$$select ticket_staff_reply((select min(id) from support_tickets),'hello')::text$$,'ERR:not_allowed');
select chk('inactive staff cannot adjust wallet','a0000000-0000-0000-0000-000000000007',$$select wallet_adjust('a0000000-0000-0000-0000-000000000008',5,'manual test')::text$$,'ERR:not_allowed');
-- disabling staff takes effect at once
select chk('admin disables sup','a0000000-0000-0000-0000-000000000001',$$select staff_set('sup@t.com','{support}',false)::text$$,'');
select chk('disabled sup: tickets 0','a0000000-0000-0000-0000-000000000002',$$select count(*)::text from support_tickets$$,'0');
select chk('admin removes con','a0000000-0000-0000-0000-000000000001',$$select staff_remove('a0000000-0000-0000-0000-000000000006')::text$$,'');
select chk('removed con cannot add banner','a0000000-0000-0000-0000-000000000006',$$insert into banners(title) values ('b3')$$,'ANYERR');
select chk('audit trail has staff events','a0000000-0000-0000-0000-000000000001',$$select (count(*) >= 7)::text from audit_log where action in ('STAFF_SET','STAFF_REMOVE')$$,'true');
select count(*) filter (where ok) as pass, count(*) filter (where not ok) as fail from res;
select n,label,got,want from res where not ok order by n;
