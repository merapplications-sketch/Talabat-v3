-- Isolated fixture overlay from REVIEW102 target catalog; not a live migration.
-- Match captured ID mechanisms and FKs where both referenced tables exist in fixture.
alter table orders alter column id drop default;
alter table orders alter column id add generated always as identity;
select setval(pg_get_serial_sequence('orders','id'),greatest(coalesce((select max(id) from orders),0),1),(select count(*)>0 from orders));
alter table wallet_entries alter column id drop default;
alter table wallet_entries alter column id add generated always as identity;
select setval(pg_get_serial_sequence('wallet_entries','id'),greatest(coalesce((select max(id) from wallet_entries),0),1),(select count(*)>0 from wallet_entries));
alter table order_items alter column id drop default;
alter table order_items alter column id type uuid using gen_random_uuid();
alter table order_items alter column id set default gen_random_uuid();
alter table group_orders add constraint group_orders_host_id_fkey foreign key(host_id) references profiles(id) on delete cascade;
alter table group_orders add constraint group_orders_order_id_fkey foreign key(order_id) references orders(id) on delete set null;
alter table group_orders add constraint group_orders_store_id_fkey foreign key(store_id) references stores(id) on delete cascade;
alter table orders add constraint orders_group_id_fkey foreign key(group_id) references group_orders(id) on delete set null;
alter table order_items drop constraint order_items_order_id_fkey;
alter table order_items add constraint order_items_order_id_fkey foreign key(order_id) references orders(id) on delete cascade;
alter table wallet_entries drop constraint wallet_entries_order_id_fkey;
alter table wallet_entries add constraint wallet_entries_order_id_fkey foreign key(order_id) references orders(id) on delete set null;
alter table wallet_entries add constraint wallet_entries_user_id_fkey foreign key(user_id) references profiles(id) on delete cascade;
