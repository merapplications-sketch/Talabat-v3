begin;
set local lock_timeout='2s';set local statement_timeout='15s';
update pilot_private.config set value=jsonb_set(jsonb_set(value,'{customers}',value->'customers'||'"90000000-0000-0000-0000-000000000900"'::jsonb),'{stores}',value->'stores'||'"90000000-0000-0000-0000-000000000901"'::jsonb) where id;
insert into auth.users(id,raw_user_meta_data) values
('90000000-0000-0000-0000-000000000900','{"name":"Synthetic A"}'),
('90000000-0000-0000-0000-000000000902','{"name":"Synthetic B"}');
update profiles set role='driver',driver_status='approved',online=true where id='90000000-0000-0000-0000-000000000902';
insert into stores(id,name,category,owner_id) values
('90000000-0000-0000-0000-000000000901','Synthetic A','rest','90000000-0000-0000-0000-000000000900'),
('90000000-0000-0000-0000-000000000904','Synthetic B','rest','90000000-0000-0000-0000-000000000902');
insert into menu_items(id,store_id,name,price) values
('90000000-0000-0000-0000-000000000905','90000000-0000-0000-0000-000000000901','A',10),
('90000000-0000-0000-0000-000000000906','90000000-0000-0000-0000-000000000904','B',10);
with o as(insert into orders(store_id,customer_id,driver_id,status,lat,lng) values ('90000000-0000-0000-0000-000000000901','90000000-0000-0000-0000-000000000900','90000000-0000-0000-0000-000000000902','pickedup',38.56,68.79) returning id) select set_config('test.scope_order',id::text,true) from o;
insert into wallet_entries(user_id,amount,kind,note) values('90000000-0000-0000-0000-000000000900',7,'adjust','synthetic rollback');

insert into addresses(user_id,street,lat,lng) values('90000000-0000-0000-0000-000000000900','Synthetic address',0,0);
insert into favorites(user_id,store_id) values('90000000-0000-0000-0000-000000000900','90000000-0000-0000-0000-000000000901');
insert into loyalty_lots(user_id,points,points_left,expires_at,kind) values('90000000-0000-0000-0000-000000000900',10,10,now()+interval '1 day','reward');
insert into loyalty_ledger(user_id,points,kind) values('90000000-0000-0000-0000-000000000900',10,'reward');
with t as(insert into support_tickets(customer_id,reason) values('90000000-0000-0000-0000-000000000900','other') returning id) select set_config('test.ticket',id::text,true) from t;
insert into ticket_messages(ticket_id,sender_id,body) values(current_setting('test.ticket')::bigint,'90000000-0000-0000-0000-000000000900','synthetic private message');
select set_config('test.result','{}',true);
set local role authenticated;select set_config('request.jwt.claims','{"sub":"90000000-0000-0000-0000-000000000900","role":"authenticated"}',true);
do $$declare r jsonb;e text;n int;begin
r:=jsonb_build_object('addresses',(select count(*) from addresses where user_id=auth.uid()),'favorites',(select count(*) from favorites where user_id=auth.uid()),'lots',(select count(*) from loyalty_lots where user_id=auth.uid()),'ledger',(select count(*) from loyalty_ledger where user_id=auth.uid()),'tickets',(select count(*) from support_tickets where id=current_setting('test.ticket')::bigint),'messages',(select count(*) from ticket_messages where ticket_id=current_setting('test.ticket')::bigint));
update addresses set details='active' where user_id=auth.uid();get diagnostics n=row_count;r:=r||jsonb_build_object('address_write',n);
begin perform ticket_reply(current_setting('test.ticket')::bigint,'synthetic reply');e:='ACCEPTED';exception when others then e:=sqlerrm;end;r:=r||jsonb_build_object('ticket_reply',e);
begin perform create_ticket(null,'other','synthetic new ticket');e:='ACCEPTED';exception when others then e:=sqlerrm;end;r:=r||jsonb_build_object('ticket_create',e);
perform set_config('test.result',(current_setting('test.result')::jsonb||jsonb_build_object('active',r))::text,true);end $$;reset role;select set_config('request.jwt.claims','{}',true);update profiles set banned_at=now() where id='90000000-0000-0000-0000-000000000900';set local role authenticated;select set_config('request.jwt.claims','{"sub":"90000000-0000-0000-0000-000000000900","role":"authenticated"}',true);
do $$declare r jsonb;e text;n int;begin
r:=jsonb_build_object('addresses',(select count(*) from addresses where user_id=auth.uid()),'favorites',(select count(*) from favorites where user_id=auth.uid()),'lots',(select count(*) from loyalty_lots where user_id=auth.uid()),'ledger',(select count(*) from loyalty_ledger where user_id=auth.uid()),'tickets',(select count(*) from support_tickets where id=current_setting('test.ticket')::bigint),'messages',(select count(*) from ticket_messages where ticket_id=current_setting('test.ticket')::bigint));
update addresses set details='disabled' where user_id=auth.uid();get diagnostics n=row_count;r:=r||jsonb_build_object('address_write',n);
begin perform ticket_reply(current_setting('test.ticket')::bigint,'synthetic reply');e:='ACCEPTED';exception when others then e:=sqlerrm;end;r:=r||jsonb_build_object('ticket_reply',e);
begin perform create_ticket(null,'other','synthetic new ticket');e:='ACCEPTED';exception when others then e:=sqlerrm;end;r:=r||jsonb_build_object('ticket_create',e);
perform set_config('test.result',(current_setting('test.result')::jsonb||jsonb_build_object('disabled',r))::text,true);end $$;reset role;select current_setting('test.result')::jsonb as results;rollback;