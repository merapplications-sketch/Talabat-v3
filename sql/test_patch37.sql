-- Self-contained test for patch 37 on an EMPTY local PostgreSQL (isolated stand-in data, no real data):
--   psql -q -f sql/test_patch37.sql  -> "PATCH37 n/n"
-- Stand-in tables carry the LIVE column shapes read on 17 Oct; the live functions are installed from rollback_patch37.sql first
-- (so the «before» gaps are shown), then patch 37, then rollback and patch again (both must be repeatable).
-- Concurrency (two sessions) is in tools/patch37_race.py. Courier / store money: patch 38 (test_patch38.sql).
\set QUIET on
\set ON_ERROR_STOP on
\pset tuples_only on
\i sql/test_patch37_setup.sql
-- #1 cancelled order like 9104: 275 total, 124.38 wallet (spent, then returned automatically), cash not collected
insert into orders(customer_id, status, payment, total, wallet_used) values (:C, 'pending', 'cash', 275, 124.38);
insert into wallet_entries(user_id, amount, kind, order_id) values (:C, -124.38, 'spend', 1);
update orders set status = 'cancelled' where id = 1;
insert into support_tickets(customer_id, order_id) values (:C, 1);
select pg_temp.chk('before: live ticket_refund_room offers the whole total (275) on a cancelled, uncollected order',
  pg_temp.val(:SUP, 'select room::text from ticket_refund_room(1)') = '275', pg_temp.val(:SUP, 'select row(r.*)::text from ticket_refund_room(1) r'));
select pg_temp.chk('before: live allows a 275 refund on it (wallet already returned, cash never collected)',
  pg_temp.as_user(:SUP, 'select ticket_set_status(1, ''resolved'', ''x'', 275)') = 'ok', null);
delete from wallet_entries where ticket_id = 1;   -- not possible through the app (ledger is insert-only); stand-in reset only
-- (the immutable trigger guards UPDATE only, as live)
update support_tickets set status = 'open', refund_amount = null where id = 1;

-- ================= PATCH =================
\i sql/schema_patch37.sql
select pg_temp.chk('patch applies; new objects present', to_regprocedure('order_refund_cap(bigint)') is not null and to_regprocedure('proof_exists(text,uuid)') is not null, null);
\i sql/rollback_patch37.sql
select pg_temp.chk('rollback: live functions back, every patch-37 object removed',
  to_regprocedure('order_refund_cap(bigint)') is null and to_regprocedure('proof_exists(text,uuid)') is null and pg_temp.val(:SUP, 'select room::text from ticket_refund_room(1)') = '275', null);
\i sql/schema_patch37.sql

-- ---------- refunds ----------
select pg_temp.chk('cap #1 (cancelled, wallet returned, cash not collected): proven paid 0 → room 0',
  (select room = 0 and paid_wallet = 0 and paid_cash = 0 and unproven = 150.62 from order_refund_cap(1)), (select row(c.*)::text from order_refund_cap(1) c));
select pg_temp.chk('ticket_refund_room shows the same cap with its breakdown (support)',
  pg_temp.val(:SUP, 'select (room = 0 and order_total = 275 and unproven = 150.62)::text from ticket_refund_room(1)') = 'true', pg_temp.val(:SUP, 'select row(r.*)::text from ticket_refund_room(1) r'));
select pg_temp.chk('refund on #1 refused: refund_too_high', pg_temp.as_user(:SUP, 'select ticket_set_status(1, ''resolved'', ''x'', 10)') like '%refund_too_high%', null);
select pg_temp.chk('ticket_refund_room for a non-support user → nothing', pg_temp.val(:C, 'select count(*)::text from ticket_refund_room(1)') = '0', null);
-- #2 delivered cash order: 200 total, 50 from wallet, 150 cash recorded
insert into orders(customer_id, driver_id, status, payment, total, wallet_used, cash_collected) values (:C, :D, 'delivered', 'cash', 200, 50, 150);
insert into wallet_entries(user_id, amount, kind, order_id) values (:C, -50, 'spend', 2);
insert into support_tickets(customer_id, order_id) values (:C, 2);
select pg_temp.chk('cap #2 (delivered, wallet 50 + recorded cash 150) = 200', (select room = 200 and paid_wallet = 50 and paid_cash = 150 from order_refund_cap(2)), (select row(c.*)::text from order_refund_cap(2) c));
select pg_temp.chk('refund 120 on ticket A of #2 → ok', pg_temp.as_user(:SUP, 'select ticket_set_status(2, ''resolved'', ''part'', 120)') = 'ok', null);
select pg_temp.chk('same ticket again → already_refunded (one refund per ticket kept)', pg_temp.as_user(:SUP, 'select ticket_set_status(2, ''resolved'', ''again'', 10)') like '%already_refunded%', null);
insert into support_tickets(customer_id, order_id) values (:C, 2);
select pg_temp.chk('ticket B of #2: 90 > room 80 → refund_too_high', pg_temp.as_user(:SUP, 'select ticket_set_status(3, ''resolved'', ''x'', 90)') like '%refund_too_high%', null);
select pg_temp.chk('ticket B of #2: 80 = room → ok', pg_temp.as_user(:SUP, 'select ticket_set_status(3, ''resolved'', ''x'', 80)') = 'ok', null);
select pg_temp.chk('… room on #2 is now 0 (refunds 120 + 80 = proven paid 200)', (select room = 0 and refunded = 200 from order_refund_cap(2)), null);
-- #3 delivered cash order where the courier recorded MORE than the cash part (220 for 200): only the cash part counts
insert into orders(customer_id, driver_id, status, payment, total, cash_collected) values (:C, :D, 'delivered', 'cash', 200, 220);
select pg_temp.chk('cap #3: recorded cash above the cash part counts as the cash part only (200)', (select room = 200 from order_refund_cap(3)), null);
-- #4 delivered card order: no capture record → unproven, room 0
insert into orders(customer_id, driver_id, status, payment, total) values (:C, :D, 'delivered', 'card', 120);
select pg_temp.chk('cap #4 (card, no capture data): room 0, unproven 120', (select room = 0 and unproven = 120 from order_refund_cap(4)), null);
-- #5 delivered cash order, cash NOT recorded: not counted
insert into orders(customer_id, driver_id, status, payment, total) values (:C, :D, 'delivered', 'cash', 80);
select pg_temp.chk('cap #5 (cash not recorded): room 0', (select room = 0 and unproven = 80 from order_refund_cap(5)), null);
-- #6 delivered order paid fully from the wallet (never returned): wallet counts
insert into orders(customer_id, driver_id, status, payment, total, wallet_used) values (:C, :D, 'delivered', 'wallet', 60, 60);
insert into wallet_entries(user_id, amount, kind, order_id) values (:C, -60, 'spend', 6);
select pg_temp.chk('cap #6 (wallet 60 spent, not returned): room 60', (select room = 60 from order_refund_cap(6)), null);
select pg_temp.chk('non-refund decisions still work (rejected with a note)', pg_temp.as_user(:SUP, 'select ticket_set_status(1, ''rejected'', ''no payment'')') = 'ok', null);
select pg_temp.chk('refund without support permission → not_allowed', pg_temp.as_user(:C, 'select ticket_set_status(1, ''resolved'', ''x'', 1)') like '%not_allowed%', null);

-- ---------- proof photo ----------
insert into orders(customer_id, driver_id, status, payment, total, leave_at_door) values (:C, :D, 'pickedup', 'card', 50, true);   -- #7
select pg_temp.chk('photo path well formed but no file → photo_missing',
  pg_temp.as_user(:D, 'select deliver_order(7, null, null, ''d0000000-0000-0000-0000-00000000000d/7/abcdefgh12.jpg'')') like '%photo_missing%', null);
insert into storage.objects(bucket_id, name, owner, owner_id, metadata) values ('proofs', 'd0000000-0000-0000-0000-00000000000d/7/abcdefgh12.jpg', null, 'd0000000-0000-0000-0000-0000000000d2', '{"size":1000,"mimetype":"image/jpeg"}');
select pg_temp.chk('file uploaded by ANOTHER user at that path → photo_missing',
  pg_temp.as_user(:D, 'select deliver_order(7, null, null, ''d0000000-0000-0000-0000-00000000000d/7/abcdefgh12.jpg'')') like '%photo_missing%', null);
insert into storage.objects(bucket_id, name, owner_id, metadata) values ('proofs', 'd0000000-0000-0000-0000-00000000000d/7/zzzzzzzz12.jpg', 'd0000000-0000-0000-0000-00000000000d', null);
select pg_temp.chk('unfinished upload (no size) → photo_missing',
  pg_temp.as_user(:D, 'select deliver_order(7, null, null, ''d0000000-0000-0000-0000-00000000000d/7/zzzzzzzz12.jpg'')') like '%photo_missing%', null);
insert into storage.objects(bucket_id, name, owner_id, metadata, archived_at) values ('proofs', 'd0000000-0000-0000-0000-00000000000d/7/oldoldol12.jpg', 'd0000000-0000-0000-0000-00000000000d', '{"size":900,"mimetype":"image/jpeg"}', now());
select pg_temp.chk('archived (not current) file → photo_missing',
  pg_temp.as_user(:D, 'select deliver_order(7, null, null, ''d0000000-0000-0000-0000-00000000000d/7/oldoldol12.jpg'')') like '%photo_missing%', null);
insert into storage.objects(bucket_id, name, owner_id, metadata) values ('proofs', 'd0000000-0000-0000-0000-00000000000d/7/notypeno12.jpg', 'd0000000-0000-0000-0000-00000000000d', '{"size":900}');
select pg_temp.chk('finished upload WITHOUT a recorded type → photo_missing (JPEG not assumed)',
  pg_temp.as_user(:D, 'select deliver_order(7, null, null, ''d0000000-0000-0000-0000-00000000000d/7/notypeno12.jpg'')') like '%photo_missing%', null);
insert into storage.objects(bucket_id, name, owner_id, metadata) values ('proofs', 'd0000000-0000-0000-0000-00000000000d/7/pngpngpn12.jpg', 'd0000000-0000-0000-0000-00000000000d', '{"size":900,"mimetype":"image/png"}');
select pg_temp.chk('recorded type other than image/jpeg → photo_missing',
  pg_temp.as_user(:D, 'select deliver_order(7, null, null, ''d0000000-0000-0000-0000-00000000000d/7/pngpngpn12.jpg'')') like '%photo_missing%', null);
insert into storage.objects(bucket_id, name, owner_id, metadata) values ('media', 'd0000000-0000-0000-0000-00000000000d/7/medmedme12.jpg', 'd0000000-0000-0000-0000-00000000000d', '{"size":900,"mimetype":"image/jpeg"}');
select pg_temp.chk('same path in another bucket → photo_missing',
  pg_temp.as_user(:D, 'select deliver_order(7, null, null, ''d0000000-0000-0000-0000-00000000000d/7/medmedme12.jpg'')') like '%photo_missing%', null);
select pg_temp.chk('path of another order → bad_value (format rule unchanged)',
  pg_temp.as_user(:D, 'select deliver_order(7, null, null, ''d0000000-0000-0000-0000-00000000000d/8/abcdefgh12.jpg'')') like '%bad_value%', null);
select pg_temp.chk('leave at the door without photo → photo_required (unchanged)', pg_temp.as_user(:D, 'select deliver_order(7)') like '%photo_required%', null);
insert into storage.objects(bucket_id, name, owner_id, metadata) values ('proofs', 'd0000000-0000-0000-0000-00000000000d/7/goodgood12.jpg', 'd0000000-0000-0000-0000-00000000000d', '{"size":5000,"mimetype":"image/jpeg"}');
select pg_temp.chk('another courier cannot deliver (unchanged) even with a real file',
  pg_temp.as_user(:D2, 'select deliver_order(7, null, null, ''d0000000-0000-0000-0000-00000000000d/7/goodgood12.jpg'')') like '%bad_transition%', null);
select pg_temp.chk('real current file by this courier → delivered',
  pg_temp.as_user(:D, 'select deliver_order(7, null, null, ''d0000000-0000-0000-0000-00000000000d/7/goodgood12.jpg'')') = 'ok', null);
select pg_temp.chk('… the order keeps that photo', (select status = 'delivered' and delivery_photo like '%goodgood12.jpg' from orders where id = 7), null);
insert into orders(customer_id, driver_id, status, payment, total) values (:C, :D, 'pickedup', 'cash', 40);   -- #8 no photo needed
select pg_temp.chk('no photo needed and none given → delivered (unchanged)', pg_temp.as_user(:D, 'select deliver_order(8, 40)') = 'ok', null);
select pg_temp.chk('proof_exists is not callable by app users', pg_temp.as_user(:D, 'set local role authenticated; select proof_exists(''x'', auth.uid())') like '%permission denied%', null);

-- #9 refund while the order is in progress, then a cancel (patch 37 alone: the proposal «refund only after the end» is NOT in it)
insert into orders(customer_id, status, payment, total, wallet_used) values (:C, 'preparing', 'cash', 90, 30);
insert into wallet_entries(user_id, amount, kind, order_id) values (:C, -30, 'spend', currval('orders_id_seq'));
insert into support_tickets(customer_id, order_id) select :C, currval('orders_id_seq');
select pg_temp.chk('#9 patch 37 alone: refund 30 on an order in progress → accepted (room = wallet 30)', pg_temp.as_user(:SUP, format('select ticket_set_status(%s, ''resolved'', ''x'', 30)', currval('support_tickets_id_seq'))) = 'ok', null);
update orders set status = 'cancelled' where id = currval('orders_id_seq');
select pg_temp.chk('#9 GAP without the proposal: the later cancel returns the wallet 30 again → 60 back for 30 paid',
  (select sum(amount) = 60 from wallet_entries where order_id = currval('orders_id_seq') and kind in ('return', 'refund')), null);
\i sql/option_refund_after_finish.sql
insert into orders(customer_id, status, payment, total, wallet_used) values (:C, 'preparing', 'cash', 90, 30);
insert into wallet_entries(user_id, amount, kind, order_id) values (:C, -30, 'spend', currval('orders_id_seq'));
insert into support_tickets(customer_id, order_id) select :C, currval('orders_id_seq');
select pg_temp.chk('PROPOSAL «refund after the end»: refund on an order in progress → order_not_finished', pg_temp.as_user(:SUP, format('select ticket_set_status(%s, ''resolved'', ''x'', 10)', currval('support_tickets_id_seq'))) like '%order_not_finished%', null);
update orders set status = 'cancelled' where id = currval('orders_id_seq');
select pg_temp.chk('PROPOSAL: … the cancel returns 30 once; room afterwards 0', (select sum(amount) = 30 from wallet_entries where order_id = currval('orders_id_seq') and kind in ('return', 'refund'))
  and (select room = 0 from order_refund_cap(currval('orders_id_seq'))), null);
\i sql/rollback_option_refund_after_finish.sql
select pg_temp.chk('proposal rolled back: patch-37 behaviour again', pg_temp.as_user(:SUP, 'select 1') = 'ok' and position('order_not_finished' in pg_get_functiondef('ticket_set_status(bigint,text,text,numeric)'::regprocedure)) = 0, null);
-- ---------- sequences: refund + cancel in both orders (totals given back to the customer) ----------
-- helper: everything given back to the customer for an order (automatic returns + support refunds)
create or replace function pg_temp.back(o bigint) returns numeric language sql as $$ select coalesce(sum(amount), 0) from wallet_entries where order_id = o and kind in ('return', 'refund') $$;
create or replace function pg_temp.mk(st text, wal numeric, cash numeric) returns bigint language plpgsql as $$
declare v bigint;
begin
  insert into orders(customer_id, driver_id, status, payment, total, wallet_used, cash_collected)
  values ('c0000000-0000-0000-0000-00000000000c', 'd0000000-0000-0000-0000-0000000000d2', st::order_status, 'cash', 200, wal, cash) returning id into v;
  if wal > 0 then insert into wallet_entries(user_id, amount, kind, order_id) values ('c0000000-0000-0000-0000-00000000000c', -wal, 'spend', v); end if;
  insert into support_tickets(customer_id, order_id, status) values ('c0000000-0000-0000-0000-00000000000c', v, 'in_progress');
  return v;
end $$;
create temp table sq (k text primary key, o bigint, t bigint);
-- SA: delivered (wallet 50 + recorded cash 150 = paid 200) → support refund 200 → the admin turns it into «cancelled»
insert into sq select 'A', pg_temp.mk('delivered', 50, 150), currval('support_tickets_id_seq');
select pg_temp.chk('SA step 1: support refund 200 (= proven paid) → ok', pg_temp.as_user(:SUP, format('select ticket_set_status(%s, ''resolved'', ''r'', 200)', (select t from sq where k = 'A'))) = 'ok', null);
select pg_temp.chk('SA step 2: the admin can still cancel a delivered order (live set_order_status, unchanged)', pg_temp.as_user(:A, format('select set_order_status(%s, ''cancelled'')', (select o from sq where k = 'A'))) = 'ok', null);
select pg_temp.chk('SA GAP (needs a decision): given back 250 for 200 paid — the automatic return adds the wallet 50 again', pg_temp.back((select o from sq where k = 'A')) = 250, pg_temp.back((select o from sq where k = 'A'))::text);
select pg_temp.chk('SA: the collected 150 stays recorded on the order (patch 38 counts it whatever the status)', (select cash_collected = 150 from orders where id = (select o from sq where k = 'A')), null);
-- SB: cancelled BEFORE delivery (wallet 40, cash never collected) → then a support refund
insert into sq select 'B', pg_temp.mk('pickedup', 40, null), currval('support_tickets_id_seq');
select pg_temp.chk('SB step 1: cancelled before delivery → wallet 40 back automatically', pg_temp.as_user(:A, format('select set_order_status(%s, ''cancelled'')', (select o from sq where k = 'B'))) = 'ok', null);
select pg_temp.chk('SB step 2: refund after the cancel → refund_too_high (room 0)', pg_temp.as_user(:SUP, format('select ticket_set_status(%s, ''resolved'', ''r'', 10)', (select t from sq where k = 'B'))) like '%refund_too_high%', null);
select pg_temp.chk('SB total: 40 back for 40 paid', pg_temp.back((select o from sq where k = 'B')) = 40, null);
-- SC: delivered (wallet 50 + cash 150) → the admin cancels FIRST → then a support refund
insert into sq select 'C', pg_temp.mk('delivered', 50, 150), currval('support_tickets_id_seq');
select pg_temp.chk('SC step 1: admin cancels a delivered order → wallet 50 back automatically', pg_temp.as_user(:A, format('select set_order_status(%s, ''cancelled'')', (select o from sq where k = 'C'))) = 'ok', null);
select pg_temp.chk('SC step 2: refund of the cash part → refund_too_high (recorded cash of a non-delivered order is not counted)', pg_temp.as_user(:SUP, format('select ticket_set_status(%s, ''resolved'', ''r'', 150)', (select t from sq where k = 'C'))) like '%refund_too_high%', null);
select pg_temp.chk('SC GAP (needs a decision): 50 back for 200 paid; the 150 collected in cash is not refundable after the status change', pg_temp.back((select o from sq where k = 'C')) = 50, null);
-- the minimal option for review: a delivered order cannot be turned into cancelled / rejected
\i sql/option_no_cancel_after_delivery.sql
insert into sq select 'A2', pg_temp.mk('delivered', 50, 150), currval('support_tickets_id_seq');
select pg_temp.chk('OPTION SA: refund 200 → ok', pg_temp.as_user(:SUP, format('select ticket_set_status(%s, ''resolved'', ''r'', 200)', (select t from sq where k = 'A2'))) = 'ok', null);
select pg_temp.chk('OPTION SA: the admin cancel of the delivered order → bad_transition', pg_temp.as_user(:A, format('select set_order_status(%s, ''cancelled'')', (select o from sq where k = 'A2'))) like '%bad_transition%', null);
select pg_temp.chk('OPTION SA total: 200 back for 200 paid', pg_temp.back((select o from sq where k = 'A2')) = 200, null);
select pg_temp.chk('OPTION: delivered → ready (then cancelled) is refused too', pg_temp.as_user(:A, format('select set_order_status(%s, ''ready'')', (select o from sq where k = 'A2'))) like '%bad_transition%', null);
update orders set done_at = '2026-10-17 09:00+05' where id = (select o from sq where k = 'A2');
select pg_temp.chk('OPTION: delivered → delivered again is accepted and changes nothing', pg_temp.as_user(:A, format('select set_order_status(%s, ''delivered'')', (select o from sq where k = 'A2'))) = 'ok', null);
select pg_temp.chk('OPTION: … done_at kept', (select done_at = '2026-10-17 09:00+05' from orders where id = (select o from sq where k = 'A2')), null);
insert into sq select 'B2', pg_temp.mk('pickedup', 40, null), currval('support_tickets_id_seq');
select pg_temp.chk('OPTION: cancelling BEFORE delivery still works (40 back)', pg_temp.as_user(:A, format('select set_order_status(%s, ''cancelled'')', (select o from sq where k = 'B2'))) = 'ok' and true, null);
select pg_temp.chk('OPTION: … and gives back 40', pg_temp.back((select o from sq where k = 'B2')) = 40, null);
select pg_temp.chk('OPTION: the admin can still reject a NOT delivered order', pg_temp.as_user(:A, format('select set_order_status(%s, ''rejected'')', pg_temp.mk('preparing', 0, null))) = 'ok', null);
\i sql/rollback_option_no_cancel_after_delivery.sql
select pg_temp.chk('option rollback: the admin can cancel a delivered order again (live)', pg_temp.as_user(:A, format('select set_order_status(%s, ''cancelled'')', pg_temp.mk('delivered', 0, 10))) = 'ok', null);

-- ---------- rollback, then patch again ----------
\i sql/rollback_patch37.sql
select pg_temp.chk('rollback restores the live functions (room on #1 = 275 again)', pg_temp.val(:SUP, 'select room::text from ticket_refund_room(1)') = '275' and to_regprocedure('proof_exists(text,uuid)') is null, null);
\i sql/schema_patch37.sql
\i sql/schema_patch37.sql
select pg_temp.chk('patch is repeatable (applied twice after the rollback)', pg_temp.val(:SUP, 'select room::text from ticket_refund_room(1)') = '0.00', null);

\pset tuples_only off
select n, case when ok then 'PASS' else 'FAIL' end as r, label, left(coalesce(got, ''), 90) as got from res order by n;
select 'PATCH37 ' || count(*) filter (where ok) || '/' || count(*) from res;
