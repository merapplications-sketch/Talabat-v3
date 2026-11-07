begin;
set local lock_timeout='2s';set local statement_timeout='15s';
insert into auth.users(id,raw_user_meta_data)values('90000000-0000-0000-0000-000000002631','{"name":"Synthetic support A"}'),('90000000-0000-0000-0000-000000002632','{"name":"Synthetic support B"}');
insert into support_tickets(id,customer_id,reason,status)overriding system value values(-26031,'90000000-0000-0000-0000-000000002631','payment','open'),(-26032,'90000000-0000-0000-0000-000000002632','payment','open');
insert into ticket_messages(ticket_id,from_staff,sender_id,body)select -26031,false,'90000000-0000-0000-0000-000000002631','Synthetic quota seed' from generate_series(1,19);
set local role authenticated;
select set_config('request.jwt.claims','{"sub":"90000000-0000-0000-0000-000000002631","role":"authenticated"}',true);
select ticket_reply(-26031,'Synthetic twentieth allowed');
do $$begin
begin perform ticket_reply(-26031,'Synthetic twenty-first rejected');raise exception 'ASSERT quota bypass';exception when raise_exception then if sqlerrm<>'too_many' then raise;end if;end;
end $$;
reset role;
select count(*) as message_count, count(*) filter(where body='Synthetic twenty-first rejected') as rejected_message_rows from ticket_messages where ticket_id=-26031;
rollback;
