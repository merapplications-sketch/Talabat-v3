begin;
set local lock_timeout='2s';set local statement_timeout='15s';
insert into auth.users(id,raw_user_meta_data)values('90000000-0000-0000-0000-000000002731','{"name":"Synthetic encoding"}');
insert into support_tickets(id,customer_id,reason,status)overriding system value values(-27031,'90000000-0000-0000-0000-000000002731','payment','open');
set local role authenticated;
select set_config('request.jwt.claims','{"sub":"90000000-0000-0000-0000-000000002731","role":"authenticated"}',true);
do $$declare v_body text;n int;begin
foreach v_body in array ARRAY['literal quote '' OR ''1''=''1','%2527 %27 &amp; &quot;','عربي русский apostrophe ''','{"quoted":"value","nested":"%252F"}'] loop
perform ticket_reply(-27031,v_body);
select count(*) into n from ticket_messages m where m.ticket_id=-27031 and m.body=v_body;
if n<>1 then raise exception 'ASSERT literal storage mismatch';end if;
end loop;
end $$;
reset role;
select count(*)=4 as exact_four_rows, bool_and(not from_staff) as no_staff_escalation from ticket_messages where ticket_id=-27031;
rollback;
