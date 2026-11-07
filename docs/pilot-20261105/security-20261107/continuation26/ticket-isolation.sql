begin;
set local lock_timeout='2s';set local statement_timeout='15s';
insert into auth.users(id,raw_user_meta_data)values('90000000-0000-0000-0000-000000002631','{"name":"Synthetic support A"}'),('90000000-0000-0000-0000-000000002632','{"name":"Synthetic support B"}');
insert into support_tickets(id,customer_id,reason,status)overriding system value values(-26031,'90000000-0000-0000-0000-000000002631','payment','open'),(-26032,'90000000-0000-0000-0000-000000002632','payment','open');
set local role authenticated;
select set_config('request.jwt.claims','{"sub":"90000000-0000-0000-0000-000000002631","role":"authenticated"}',true);
do $$declare e text;r jsonb:='{}';begin
perform ticket_reply(-26031,'Synthetic authorized reply');
r:=jsonb_build_object('own_reply_rows',(select count(*) from ticket_messages where ticket_id=-26031));
begin perform ticket_reply(-26032,'Synthetic foreign reply');raise exception 'ASSERT foreign ticket reply accepted';exception when raise_exception then if sqlerrm<>'not_allowed' then raise;end if;e:=sqlerrm;end;r:=r||jsonb_build_object('foreign_reply',e);
begin insert into ticket_messages(ticket_id,from_staff,sender_id,body)values(-26031,true,'90000000-0000-0000-0000-000000002631','Synthetic staff forgery');raise exception 'ASSERT staff forgery accepted';exception when insufficient_privilege then e:=sqlerrm;end;r:=r||jsonb_build_object('forged_staff_message',e);
perform set_config('test.c26_tickets',r::text,true);end $$;
reset role;
select current_setting('test.c26_tickets')::jsonb||jsonb_build_object('own_rows_privileged',(select count(*) from ticket_messages where ticket_id=-26031),'foreign_rows_privileged',(select count(*) from ticket_messages where ticket_id=-26032),'forged_staff_rows',(select count(*) from ticket_messages where ticket_id in(-26031,-26032)and from_staff)) as result;
rollback;
