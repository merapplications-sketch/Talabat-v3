-- Self-contained test for patch 38 (+ patch 37 underneath) on an EMPTY local PostgreSQL — isolated stand-in data, no real data:
--   psql -q -f sql/test_patch38.sql  -> "PATCH38 n/n"
-- Base: the stand-in database of test_patch34 (patches 28 → 34, i.e. the repository place_order chain = the live one read 17 Oct),
-- completed with the live shapes patch 37 / 38 need; then the live functions from the rollback files; then patch 37 and 38.
-- Electronic payments are SIMULATED data only (an order marked card) — no capture is claimed. Races: tools/patch38_race.py.
\i sql/test_patch38_setup.sql
-- ================= A) store agreements =================
select c38('defaults = today''s behaviour (online, wallet, points allowed; settlement not set)', (select bool_and(accept_online and allow_wallet and allow_points and settle_method is null) from stores));
select c38('finance alone cannot change an agreement', u38(:F, 'select set_store_pay_rules(''50000000-0000-0000-0000-000000000002'', false, true, true, ''platform_settles'')') like 'ERR:not_allowed%');
select c38('the store owner cannot change it by a direct update (guard)', u38(:M, 'update stores set allow_wallet = false where name = ''Kebab''') like 'ERR:not_allowed%');
select c38('staff «stores»: Pizza = cash only, platform settles', u38(:T, 'select set_store_pay_rules(''50000000-0000-0000-0000-000000000002'', false, true, true, ''platform_settles'')') = 'ok');
select c38('staff «stores»: Kebab = online ok, courier pays the store', u38(:T, 'select set_store_pay_rules(''50000000-0000-0000-0000-000000000001'', true, true, true, ''driver_pays'')') = 'ok');
select c38('the change is in the audit log', (select count(*) >= 2 from audit_log where table_name = 'stores' and details ? 'settle_method'));
select c38('bad method → bad_value', u38(:T, 'select set_store_pay_rules(''50000000-0000-0000-0000-000000000001'', true, true, true, ''x'')') like 'ERR:bad_value%');
select c38('cash-only store: card → online_not_allowed', po38('Pizza', 1, 'card') like 'ERR:online_not_allowed%', po38('Pizza', 1, 'card'));
select c38('cash-only store: cash → placed', po38('Pizza', 1, 'cash') ~ '^[0-9]+$');
select c38('… the rules in force are kept on the order', (select pay_rules = '{"accept_online": false, "allow_wallet": true, "allow_points": true, "settle_method": "platform_settles"}'::jsonb from orders order by id desc limit 1));
select c38('cash-only store: the wallet pays everything with «card» chosen → nothing left to pay online → placed', po38('Pizza', 1, 'card', 110) ~ '^[0-9]+$');
select c38('… payment recorded as wallet', (select payment = 'wallet' from orders order by id desc limit 1));
select u38(:T, 'select set_store_pay_rules(''50000000-0000-0000-0000-000000000002'', false, false, false, ''platform_settles'')');
select c38('wallet not allowed by the store → wallet_not_allowed', po38('Pizza', 1, 'cash', 20) like 'ERR:wallet_not_allowed%');
select c38('points not allowed by the store → points_not_allowed', po38('Pizza', 1, 'cash', null, 1000) like 'ERR:points_not_allowed%');
select c38('the earlier orders keep the rules in force when they were placed (history untouched)', (select count(*) = 2 from orders where pay_rules->>'allow_wallet' = 'true' and store_id = :PIZZA));
select u38(:T, 'select set_store_pay_rules(''50000000-0000-0000-0000-000000000002'', false, true, true, ''platform_settles'')');

-- ================= C) start of the new accounting =================
select c38('money records refused before the start is set', u38(:F, 'select * from record_driver_settlement(''d0000000-0000-0000-0000-00000000000d'', ''driver_to_platform'', 1, null, null, ''key-start-001'')') like 'ERR:accounting_not_started%');
select c38('only finance sets the start', u38(:T, 'select set_accounting_start(now())') like 'ERR:not_allowed%');
select c38('finance sets the start (orders from now on)', u38(:F, 'select set_accounting_start(now())') = 'ok');
select c38('… once only', u38(:F, 'select set_accounting_start(now())') like 'ERR:already_set%');

-- ================= B) the worked example =================
-- orders after the start; Kebab = courier pays the store; Pizza = platform settles. Plov 50 TJS, delivery 10 TJS (courier pay 10), commission 10 %.
create temp table ex (k text primary key, id bigint);
insert into ex select 'A', po38('Kebab', 2, 'cash')::bigint;                    -- 100 + 10 = 110 cash
insert into ex select 'B', po38('Kebab', 2, 'cash', 30)::bigint;                -- 110: wallet 30 + cash 80 (mixed)
insert into ex select 'C', po38('Pizza', 1, 'cash')::bigint;                    -- 100 + 10 = 110 cash, platform settles
insert into ex select 'E', po38('Kebab', 2, 'card')::bigint;                    -- 110 «card» — SIMULATED, nothing captured
insert into ex select 'D1', po38('Kebab', 2, 'cash')::bigint;                   -- cancelled BEFORE the courier paid the store
insert into ex select 'D2', po38('Kebab', 2, 'cash')::bigint;                   -- cancelled AFTER the courier paid the store
select c38('example orders placed (6)', (select count(*) = 6 and bool_and(id is not null) from ex));
select c38('order A: subtotal 100, total 110, commission 10, courier pay 10', (select subtotal = 100 and total = 110 and commission = 10 and driver_payout = 10 from orders where id = (select id from ex where k = 'A')),
  (select row(subtotal, total, commission, driver_payout)::text from orders where id = (select id from ex where k = 'A')));
update orders set driver_id = :DR, status = 'pickedup' where id in (select id from ex where k in ('A', 'B', 'C', 'E', 'D2'));
update orders set driver_id = :DR, status = 'ready' where id = (select id from ex where k = 'D1');
-- courier → store
select c38('A: the courier records 100 paid to the store (receipt CHK-A)', u38(:DR, format('select * from record_store_payment(%s, 100, ''CHK-A'', null, ''dsp-key-A001'')', (select id from ex where k = 'A'))) = 'ok');
select c38('A: the same form again → the same record (no second payment)', u38(:DR, format('select * from record_store_payment(%s, 100, ''CHK-A'', null, ''dsp-key-A001'')', (select id from ex where k = 'A'))) = 'ok'
  and (select count(*) = 1 from driver_store_payments where order_id = (select id from ex where k = 'A')));
select c38('A: another form for the same order → already_recorded', u38(:DR, format('select * from record_store_payment(%s, 100, ''CHK-A2'', null, ''dsp-key-A002'')', (select id from ex where k = 'A'))) like 'ERR:already_recorded%');
select c38('C (platform settles): the courier cannot record a store payment → not_driver_pays', u38(:DR, format('select * from record_store_payment(%s, 100, ''X'', null, ''dsp-key-C001'')', (select id from ex where k = 'C'))) like 'ERR:not_driver_pays%');
select c38('another courier cannot record it → not_allowed', u38('d0000000-0000-0000-0000-00000000000e', format('select * from record_store_payment(%s, 100, ''X'', null, ''dsp-key-X001'')', (select id from ex where k = 'B'))) like 'ERR:not_allowed%');
select c38('no reference and no photo → proof_required', u38(:DR, format('select * from record_store_payment(%s, 100, null, null, ''dsp-key-B000'')', (select id from ex where k = 'B'))) like 'ERR:proof_required%');
select c38('a photo that is not stored → photo_missing', u38(:DR, format('select * from record_store_payment(%s, 100, null, %L, ''dsp-key-B00x'')', (select id from ex where k = 'B'), 'd0000000-0000-0000-0000-00000000000d/' || (select id from ex where k = 'B') || '/abcdefgh12.jpg')) like 'ERR:photo_missing%');
insert into storage.objects(bucket_id, name, owner_id, metadata) select 'proofs', 'd0000000-0000-0000-0000-00000000000d/' || id || '/chkphoto12.jpg', 'd0000000-0000-0000-0000-00000000000d', '{"size":4000,"mimetype":"image/jpeg"}' from ex where k = 'B';
select c38('B: the courier records 100 paid, with the photo of the receipt', u38(:DR, format('select * from record_store_payment(%s, 100, null, %L, ''dsp-key-B001'')', (select id from ex where k = 'B'), 'd0000000-0000-0000-0000-00000000000d/' || (select id from ex where k = 'B') || '/chkphoto12.jpg')) = 'ok');
select c38('E: the courier records 100 paid', u38(:DR, format('select * from record_store_payment(%s, 100, ''CHK-E'', null, ''dsp-key-E001'')', (select id from ex where k = 'E'))) = 'ok');
select c38('D2: the courier records 100 paid', u38(:DR, format('select * from record_store_payment(%s, 100, ''CHK-D2'', null, ''dsp-key-D201'')', (select id from ex where k = 'D2'))) = 'ok');
-- store decides
select c38('a stranger cannot confirm → not_allowed', u38(:T, format('select decide_store_payment(%s, true)', (select id from driver_store_payments where client_key = 'dsp-key-A001'))) like 'ERR:not_allowed%');
select c38('A: the store owner confirms', u38(:M, format('select decide_store_payment(%s, true)', (select id from driver_store_payments where client_key = 'dsp-key-A001'))) = 'ok');
select c38('… who confirmed is kept', (select status = 'confirmed' and decided_by_name = 'Owner Muso' and decided_at is not null from driver_store_payments where client_key = 'dsp-key-A001'));
select c38('A: deciding again → already_decided', u38(:M, format('select decide_store_payment(%s, false)', (select id from driver_store_payments where client_key = 'dsp-key-A001'))) like 'ERR:already_decided%');
select c38('B: finance confirms', u38(:F, format('select decide_store_payment(%s, true)', (select id from driver_store_payments where client_key = 'dsp-key-B001'))) = 'ok');
select c38('E: the store DISPUTES (amount not received)', u38(:M, format('select decide_store_payment(%s, false, ''not received'')', (select id from driver_store_payments where client_key = 'dsp-key-E001'))) = 'ok');
select c38('E: after a dispute the courier may record the payment again', u38(:DR, format('select * from record_store_payment(%s, 100, ''CHK-E2'', null, ''dsp-key-E002'')', (select id from ex where k = 'E'))) = 'ok');
select c38('records cannot be edited or deleted', u38(:F, format('update driver_store_payments set amount = 1 where client_key = ''dsp-key-A001''')) like 'ERR:ledger_immutable%'
  and u38(:F, 'delete from driver_store_payments') like 'ERR:ledger_immutable%');
-- cancels
update orders set status = 'cancelled' where id in (select id from ex where k in ('D1', 'D2'));
select c38('D1 cancelled before any payment: the courier cannot record one → bad_transition', u38(:DR, format('select * from record_store_payment(%s, 100, ''X'', null, ''dsp-key-D101'')', (select id from ex where k = 'D1'))) like 'ERR:bad_transition%');
select c38('D2 cancelled after the payment: the payment is KEPT', (select count(*) = 1 from driver_store_payments where order_id = (select id from ex where k = 'D2') and status = 'claimed'));
-- deliveries (patch 37 deliver_order: no photo needed here)
select c38('A delivered, 110 cash collected', u38(:DR, format('select deliver_order(%s, 110)', (select id from ex where k = 'A'))) = 'ok');
select c38('B delivered, 80 cash collected (30 came from the wallet)', u38(:DR, format('select deliver_order(%s, 80)', (select id from ex where k = 'B'))) = 'ok');
select c38('C delivered, 110 cash collected', u38(:DR, format('select deliver_order(%s, 110)', (select id from ex where k = 'C'))) = 'ok');
select c38('E delivered, «card»: nothing collected by the courier', u38(:DR, format('select deliver_order(%s)', (select id from ex where k = 'E'))) = 'ok'
  and (select cash_collected is null from orders where id = (select id from ex where k = 'E')));

-- ---------- positions (expected numbers written out) ----------
-- courier: collected A110 + B80 + C110 = 300; paid to stores confirmed A100 + B100 = 200, claimed (unconfirmed) E100 + D2 100 = 200;
-- cash held = 300 − 200 − 200 = −100 (the platform owes him 100 advanced for the «card» order and the cancelled one);
-- earned (delivered A, B, C, E) 4 × 10 = 40; paid 0 → due 40
create temp table dp as select * from driver_position(:DR) limit 0;
select c38('courier position before settlements', v38(:F, 'select row(p.*)::text from driver_position(''d0000000-0000-0000-0000-00000000000d'') p') = '(300.00,200.00,200.00,0.00,-100.00,40.00,0.00,40.00)',
  v38(:F, 'select row(p.*)::text from driver_position(''d0000000-0000-0000-0000-00000000000d'') p'));
-- store Kebab (driver pays): delivered A, B, E → gross 300, commission 30, store-funded 0, net due 270;
-- paid by couriers (non-disputed) A100 + B100 + E100 (2nd) + D2 100 = 400 → balance 270 − 400 = −130; paid on undelivered (D2) 100; claimed 200
select c38('Kebab position', v38(:F, format('select row(p.*)::text from store_position(%L) p', '50000000-0000-0000-0000-000000000001')) = '(300.00,30.00,0.00,270.00,400.00,0.00,-130.00,100.00,200.00)',
  v38(:F, format('select row(p.*)::text from store_position(%L) p', '50000000-0000-0000-0000-000000000001')));
-- store Pizza (platform settles): delivered C → gross 100, commission 10, net due 90, nothing paid → balance 90
select c38('Pizza position', v38(:F, format('select row(p.*)::text from store_position(%L) p', '50000000-0000-0000-0000-000000000002')) = '(100.00,10.00,0.00,90.00,0.00,0.00,90.00,0.00,0.00)',
  v38(:F, format('select row(p.*)::text from store_position(%L) p', '50000000-0000-0000-0000-000000000002')));
select c38('the store owner sees his own position, not another store''s', v38(:M, format('select count(*)::text from store_position(%L)', '50000000-0000-0000-0000-000000000001')) = '1'
  and v38(:M, format('select count(*)::text from store_position(%L)', '50000000-0000-0000-0000-000000000002')) = '0');
select c38('the courier sees his own position only', v38(:DR, 'select count(*)::text from driver_position(''d0000000-0000-0000-0000-00000000000d'')') = '1'
  and v38('d0000000-0000-0000-0000-00000000000e', 'select count(*)::text from driver_position(''d0000000-0000-0000-0000-00000000000d'')') = '0');

-- ---------- settlements ----------
-- the courier holds −100: nothing to hand over
select c38('courier holds −100 → handing cash to the platform: nothing_due', u38(:F, 'select * from record_driver_settlement(''d0000000-0000-0000-0000-00000000000d'', ''driver_to_platform'', 10, ''R1'', null, ''pds-key-0001'')') like 'ERR:nothing_due%');
-- the store confirms D2 / E2 later? E2 confirmed now, D2 disputed by the store (it refunds the courier) → courier holds 0
select u38(:M, format('select decide_store_payment(%s, true)', (select id from driver_store_payments where client_key = 'dsp-key-E002')));
select u38(:M, format('select decide_store_payment(%s, false, ''refunded to courier'')', (select id from driver_store_payments where client_key = 'dsp-key-D201')));
select c38('after E confirmed and D2 disputed: held = 300 − 300 = 0', v38(:F, 'select cash_held::text from driver_position(''d0000000-0000-0000-0000-00000000000d'')') = '0.00');
-- courier pay: partial 15, then the rest 25; more → amount_too_high
select c38('platform pays the courier 15 of his 40 (partial)', v38(:F, 'select row(before_amount, after_amount)::text from record_driver_settlement(''d0000000-0000-0000-0000-00000000000d'', ''platform_to_driver'', 15, ''PAY-1'', null, ''pds-key-0002'')') = '(40.00,25.00)');
select c38('… the receiver / payer and the reference are kept', (select recorded_by_name = 'Finance Farhod' and reference = 'PAY-1' and direction = 'platform_to_driver' from platform_driver_settlements where client_key = 'pds-key-0002'));
select c38('paying 26 when 25 is due → amount_too_high', u38(:F, 'select * from record_driver_settlement(''d0000000-0000-0000-0000-00000000000d'', ''platform_to_driver'', 26, ''PAY-2'', null, ''pds-key-0003'')') like 'ERR:amount_too_high%');
select c38('the same form again (unknown answer, retried) → the first record, no second payment', u38(:F, 'select * from record_driver_settlement(''d0000000-0000-0000-0000-00000000000d'', ''platform_to_driver'', 15, ''PAY-1'', null, ''pds-key-0002'')') = 'ok'
  and (select count(*) = 1 from platform_driver_settlements));
select c38('the same key with another amount → bad_value', u38(:F, 'select * from record_driver_settlement(''d0000000-0000-0000-0000-00000000000d'', ''platform_to_driver'', 16, ''PAY-1'', null, ''pds-key-0002'')') like 'ERR:bad_value%');
select c38('courier pay is NOT netted against cash: held stays 0, pay due 25', v38(:F, 'select row(cash_held, earnings_due)::text from driver_position(''d0000000-0000-0000-0000-00000000000d'')') = '(0.00,25.00)');
-- a new cash order where the courier keeps the money: then hands part of it over
insert into ex select 'G', po38('Pizza', 1, 'cash')::bigint;
update orders set driver_id = :DR, status = 'pickedup' where id = (select id from ex where k = 'G');
select u38(:DR, format('select deliver_order(%s, 110)', (select id from ex where k = 'G')));
select c38('G (platform settles) delivered: courier holds 110', v38(:F, 'select cash_held::text from driver_position(''d0000000-0000-0000-0000-00000000000d'')') = '110.00');
select c38('courier hands 60 of 110 (partial), receiver kept, 50 left', v38(:F, 'select row(before_amount, after_amount)::text from record_driver_settlement(''d0000000-0000-0000-0000-00000000000d'', ''driver_to_platform'', 60, ''KASSA-7'', ''smena'', ''pds-key-0004'')') = '(110.00,50.00)');
-- the admin cancels G after delivery: the collection and the handover stay
update orders set status = 'cancelled' where id = (select id from ex where k = 'G');
select c38('a status change after delivery does not erase the cash collected or handed over (held still 50)', v38(:F, 'select cash_held::text from driver_position(''d0000000-0000-0000-0000-00000000000d'')') = '50.00');
-- platform → store (Pizza, net due 90; G was cancelled so not due)
select c38('platform → Pizza: 50 by bank, pending (reference later)', v38(:F, 'select row(before_amount, after_amount, status)::text from record_store_settlement(''50000000-0000-0000-0000-000000000002'', 50, ''bank'', null, null, ''pending'', ''pss-key-0001'')') = '(90.00,40.00,pending)');
select c38('done without a reference → reference_required', u38(:F, format('select set_store_settlement_status(%s, ''done'')', (select id from platform_store_settlements where client_key = 'pss-key-0001'))) like 'ERR:reference_required%');
select c38('done with the bank reference', u38(:F, format('select set_store_settlement_status(%s, ''done'', ''BANK-55'')', (select id from platform_store_settlements where client_key = 'pss-key-0001'))) = 'ok');
select c38('a pending one counts: 41 more → amount_too_high (40 left)', u38(:F, 'select * from record_store_settlement(''50000000-0000-0000-0000-000000000002'', 41, ''online'', ''ON-1'', null, ''done'', ''pss-key-0002'')') like 'ERR:amount_too_high%');
select c38('online 40 done with reference → balance 0', u38(:F, 'select * from record_store_settlement(''50000000-0000-0000-0000-000000000002'', 40, ''online'', ''ON-1'', null, ''done'', ''pss-key-0003'')') = 'ok'
  and v38(:F, format('select balance::text from store_position(%L)', '50000000-0000-0000-0000-000000000002')) = '0.00');
select c38('Pizza paid → nothing_due (no double payment)', u38(:F, 'select * from record_store_settlement(''50000000-0000-0000-0000-000000000002'', 1, ''cash'', ''C'', null, ''done'', ''pss-key-0004'')') like 'ERR:nothing_due%');
select c38('Kebab (balance −130, the store owes the platform) → the platform pays nothing: nothing_due', u38(:F, 'select * from record_store_settlement(''50000000-0000-0000-0000-000000000001'', 1, ''cash'', ''C'', null, ''done'', ''pss-key-0005'')') like 'ERR:nothing_due%');
select c38('the old cash_balances counts only orders from before the start, none of the new ones', v38(:F, 'select coalesce(sum(balance), 0)::text from cash_balances()')::numeric = (select coalesce(sum(cash_collected), 0) from orders where status = 'delivered' and cash_collected is not null and cash_settled_at is null and created_at < acc_start()), v38(:F, 'select coalesce(sum(balance), 0)::text from cash_balances()'));
select c38('a courier / merchant cannot record platform settlements', u38(:DR, 'select * from record_driver_settlement(''d0000000-0000-0000-0000-00000000000d'', ''platform_to_driver'', 1, null, null, ''pds-key-0009'')') like 'ERR:not_allowed%'
  and u38(:M, 'select * from record_store_settlement(''50000000-0000-0000-0000-000000000001'', 1, ''cash'', ''x'', null, ''done'', ''pss-key-0009'')') like 'ERR:not_allowed%');
select c38('app users cannot write the record tables directly', u38(:F, 'set local role authenticated; insert into platform_driver_settlements(driver_id, direction, amount, before_amount, after_amount, recorded_by, client_key) values (''d0000000-0000-0000-0000-00000000000d'', ''platform_to_driver'', 1, 1, 0, auth.uid(), ''pds-key-xxxx'')') like 'ERR:permission denied%');

-- ================= rollbacks =================
\set ON_ERROR_STOP off
\i sql/rollback_patch38.sql
\set ON_ERROR_STOP on
select c38('full rollback with records → refused, nothing changed', to_regprocedure('record_driver_settlement(uuid,text,numeric,text,text,text)') is not null
  and (select count(*) from platform_driver_settlements) = 2 and v38(:F, 'select cash_held::text from driver_position(''d0000000-0000-0000-0000-00000000000d'')') = '50.00');
\i sql/rollback_patch38_keep_records.sql
select c38('partial rollback: checkout no longer enforces the agreement (live place_order)', po38('Pizza', 1, 'card') ~ '^[0-9]+$');
select c38('… records, positions and the old-cash split kept (held 50, old cash_balances still excludes new orders)', v38(:F, 'select cash_held::text from driver_position(''d0000000-0000-0000-0000-00000000000d'')') = '50.00'
  and v38(:F, 'select coalesce(sum(balance), 0)::text from cash_balances()')::numeric = (select coalesce(sum(cash_collected), 0) from orders where status = 'delivered' and cash_collected is not null and cash_settled_at is null and created_at < acc_start()));
\i sql/schema_patch38.sql
\i sql/schema_patch38.sql
select c38('patch 38 re-applied twice: enforcement back, records intact', po38('Pizza', 1, 'card') like 'ERR:online_not_allowed%' and (select count(*) = 2 from platform_driver_settlements));

\pset tuples_only off
select n, case when ok then 'PASS' else 'FAIL' end as r, label, left(got, 80) as got from r38 order by n;
select 'PATCH38 ' || count(*) filter (where ok) || '/' || count(*) from r38;
