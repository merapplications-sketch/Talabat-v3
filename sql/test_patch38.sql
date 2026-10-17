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
-- courier: collected A110 + B80 + C110 = 300. Store payments: confirmed A100 + B100 = 200; PENDING E2 100 + D2 100 = 200 (a reserve,
-- not «paid»); DISPUTED E1 100 (neither paid nor unpaid). Net on the confirmed basis = 300 − 200 = 100 → held 100, reserve 200,
-- may be taken now 0, advance 0. Pay earned (delivered A, B, C, E) 4 × 10 = 40, paid 0 → owed 40.
select c38('courier position: confirmed / pending / disputed apart; reserve; no advance yet',
  v38(:F, 'select row(p.*)::text from driver_position(''d0000000-0000-0000-0000-00000000000d'') p') = '(300.00,200.00,200.00,100.00,0.00,0.00,100.00,100.00,200.00,0.00,0.00,40.00,0.00,40.00)',
  v38(:F, 'select row(p.*)::text from driver_position(''d0000000-0000-0000-0000-00000000000d'') p'));
-- Kebab (courier pays): delivered A, B, E → gross 300, commission 30, owed 270 (all courier-paid orders);
-- courier payments confirmed 200, pending 200, disputed 100, non-disputed on an undelivered order (D2) 100; confirmed balance 270 − 200 = 70;
-- platform-settled part 0 → the platform may pay 0
select c38('Kebab position: courier part (confirmed / pending / disputed apart) and platform part (0)',
  v38(:F, format('select row(p.*)::text from store_position(%L) p', '50000000-0000-0000-0000-000000000001')) = '(300.00,30.00,0.00,270.00,270.00,200.00,200.00,100.00,100.00,70.00,0.00,0.00,0.00,0.00,0.00)',
  v38(:F, format('select row(p.*)::text from store_position(%L) p', '50000000-0000-0000-0000-000000000001')));
-- Pizza (platform settles): delivered C → owed 90, all of it platform-settled, nothing paid → the platform may pay 90
select c38('Pizza position: platform part 90 available',
  v38(:F, format('select row(p.*)::text from store_position(%L) p', '50000000-0000-0000-0000-000000000002')) = '(100.00,10.00,0.00,90.00,0.00,0.00,0.00,0.00,0.00,0.00,90.00,0.00,0.00,90.00,0.00)',
  v38(:F, format('select row(p.*)::text from store_position(%L) p', '50000000-0000-0000-0000-000000000002')));
select c38('the store owner sees his own position, not another store''s', v38(:M, format('select count(*)::text from store_position(%L)', '50000000-0000-0000-0000-000000000001')) = '1'
  and v38(:M, format('select count(*)::text from store_position(%L)', '50000000-0000-0000-0000-000000000002')) = '0');
select c38('the courier sees his own position only', v38(:DR, 'select count(*)::text from driver_position(''d0000000-0000-0000-0000-00000000000d'')') = '1'
  and v38('d0000000-0000-0000-0000-00000000000e', 'select count(*)::text from driver_position(''d0000000-0000-0000-0000-00000000000d'')') = '0');

-- ---------- settlements ----------
select c38('held 100 but 200 pending (reserve) → taking cash from him now: nothing_due (the reserve is kept back)', u38(:F, 'select * from record_driver_settlement(''d0000000-0000-0000-0000-00000000000d'', ''driver_to_platform'', 10, ''R1'', null, ''pds-key-0001'')') like 'ERR:nothing_due%');
-- the store confirms E2 and disputes D2 (its statement only — no responsibility is decided)
select u38(:M, format('select decide_store_payment(%s, true)', (select id from driver_store_payments where client_key = 'dsp-key-E002')));
select u38(:M, format('select decide_store_payment(%s, false, ''not received'')', (select id from driver_store_payments where client_key = 'dsp-key-D201')));
select c38('after E2 confirmed and D2 disputed: confirmed 300, pending 0, disputed 200 (kept apart), net 0',
  v38(:F, 'select row(store_paid_confirmed, store_paid_pending, store_paid_disputed, net_cash, can_hand_over, advance_due)::text from driver_position(''d0000000-0000-0000-0000-00000000000d'')') = '(300.00,0.00,200.00,0.00,0.00,0.00)',
  v38(:F, 'select row(store_paid_confirmed, store_paid_pending, store_paid_disputed, net_cash, can_hand_over, advance_due)::text from driver_position(''d0000000-0000-0000-0000-00000000000d'')'));
select c38('a dispute is not treated as «the courier did not pay»: it is not added back to the cash he holds', v38(:F, 'select cash_held::text from driver_position(''d0000000-0000-0000-0000-00000000000d'')') = '0.00');
-- courier pay: partial 15; the rest 25; more → amount_too_high
select c38('platform pays the courier 15 of his 40 (partial)', v38(:F, 'select row(before_amount, after_amount)::text from record_driver_settlement(''d0000000-0000-0000-0000-00000000000d'', ''platform_to_driver'', 15, ''PAY-1'', null, ''pds-key-0002'')') = '(40.00,25.00)');
select c38('… the receiver / payer and the reference are kept', (select recorded_by_name = 'Finance Farhod' and reference = 'PAY-1' and direction = 'platform_to_driver' from platform_driver_settlements where client_key = 'pds-key-0002'));
select c38('paying 26 when 25 is due → amount_too_high', u38(:F, 'select * from record_driver_settlement(''d0000000-0000-0000-0000-00000000000d'', ''platform_to_driver'', 26, ''PAY-2'', null, ''pds-key-0003'')') like 'ERR:amount_too_high%');
select c38('KEY: the same form again with the same data → the first record (no second payment)', v38(:F, 'select id::text from record_driver_settlement(''d0000000-0000-0000-0000-00000000000d'', ''platform_to_driver'', 15, ''PAY-1'', null, ''pds-key-0002'')') = (select id::text from platform_driver_settlements where client_key = 'pds-key-0002')
  and (select count(*) = 1 from platform_driver_settlements));
select c38('KEY: the same key with another amount → key_reused', u38(:F, 'select * from record_driver_settlement(''d0000000-0000-0000-0000-00000000000d'', ''platform_to_driver'', 16, ''PAY-1'', null, ''pds-key-0002'')') like 'ERR:key_reused%');
select c38('KEY: the same key with another direction → key_reused', u38(:F, 'select * from record_driver_settlement(''d0000000-0000-0000-0000-00000000000d'', ''advance_repayment'', 15, ''PAY-1'', null, ''pds-key-0002'')') like 'ERR:key_reused%');
select c38('KEY: the same key with another reference → key_reused', u38(:F, 'select * from record_driver_settlement(''d0000000-0000-0000-0000-00000000000d'', ''platform_to_driver'', 15, ''PAY-X'', null, ''pds-key-0002'')') like 'ERR:key_reused%');
select c38('KEY: a courier payment key replayed for another order → key_reused', u38(:DR, format('select * from record_store_payment(%s, 100, ''CHK-A'', null, ''dsp-key-A001'')', (select id from ex where k = 'B'))) like 'ERR:key_reused%');
select c38('KEY: … with another amount → key_reused', u38(:DR, format('select * from record_store_payment(%s, 99, ''CHK-A'', null, ''dsp-key-A001'')', (select id from ex where k = 'A'))) like 'ERR:key_reused%');
select c38('courier pay is NOT netted against cash: held 0, pay owed 25', v38(:F, 'select row(cash_held, earnings_due)::text from driver_position(''d0000000-0000-0000-0000-00000000000d'')') = '(0.00,25.00)');
-- a new cash order where the courier keeps the money: then hands part of it over
insert into ex select 'G', po38('Pizza', 1, 'cash')::bigint;
update orders set driver_id = :DR, status = 'pickedup' where id = (select id from ex where k = 'G');
select u38(:DR, format('select deliver_order(%s, 110)', (select id from ex where k = 'G')));
select c38('G (platform settles) delivered: courier holds 110', v38(:F, 'select cash_held::text from driver_position(''d0000000-0000-0000-0000-00000000000d'')') = '110.00');
select c38('courier hands 60 of 110 (partial), receiver kept, 50 left', v38(:F, 'select row(before_amount, after_amount)::text from record_driver_settlement(''d0000000-0000-0000-0000-00000000000d'', ''driver_to_platform'', 60, ''KASSA-7'', ''smena'', ''pds-key-0004'')') = '(110.00,50.00)');
update orders set status = 'cancelled' where id = (select id from ex where k = 'G');
select c38('a status change after delivery does not erase the cash collected or handed over (held still 50)', v38(:F, 'select cash_held::text from driver_position(''d0000000-0000-0000-0000-00000000000d'')') = '50.00');
-- ADVANCE: a «card» order (nothing collected) where he pays the store 100, confirmed → net 50 − 100 = −50 → advance 50
insert into ex select 'H', po38('Kebab', 2, 'card')::bigint;
update orders set driver_id = :DR, status = 'pickedup' where id = (select id from ex where k = 'H');
select u38(:DR, format('select * from record_store_payment(%s, 100, ''CHK-H'', null, ''dsp-key-H001'')', (select id from ex where k = 'H')));
select u38(:M, format('select decide_store_payment(%s, true)', (select id from driver_store_payments where client_key = 'dsp-key-H001')));
select u38(:DR, format('select deliver_order(%s)', (select id from ex where k = 'H')));
select c38('ADVANCE apart: held 0, advance owed to him 50, his pay owed 35 (25 + 10 for H) — two separate balances',
  v38(:F, 'select row(cash_held, advance_due, earnings_due)::text from driver_position(''d0000000-0000-0000-0000-00000000000d'')') = '(0.00,50.00,35.00)',
  v38(:F, 'select row(cash_held, advance_due, earnings_due)::text from driver_position(''d0000000-0000-0000-0000-00000000000d'')'));
select c38('ADVANCE: paying his pay does not repay the advance (pay 35 → advance still 50)', u38(:F, 'select * from record_driver_settlement(''d0000000-0000-0000-0000-00000000000d'', ''platform_to_driver'', 35, ''PAY-3'', null, ''pds-key-0005'')') = 'ok'
  and v38(:F, 'select row(advance_due, earnings_due)::text from driver_position(''d0000000-0000-0000-0000-00000000000d'')') = '(50.00,0.00)');
select c38('ADVANCE (prepared path, for review): repaying 60 of a 50 advance → amount_too_high', u38(:F, 'select * from record_driver_settlement(''d0000000-0000-0000-0000-00000000000d'', ''advance_repayment'', 60, ''ADV-1'', null, ''pds-key-0006'')') like 'ERR:amount_too_high%');
select c38('ADVANCE: repaying 50 through its own direction → advance 0, cash and pay untouched', v38(:F, 'select row(before_amount, after_amount)::text from record_driver_settlement(''d0000000-0000-0000-0000-00000000000d'', ''advance_repayment'', 50, ''ADV-1'', null, ''pds-key-0007'')') = '(50.00,0.00)'
  and v38(:F, 'select row(cash_held, advance_due, earnings_due)::text from driver_position(''d0000000-0000-0000-0000-00000000000d'')') = '(0.00,0.00,0.00)');
-- platform → store (Pizza: platform-settled 90; G was cancelled so not owed)
select c38('platform → Pizza: 50 by bank, pending (reference later)', v38(:F, 'select row(before_amount, after_amount, status)::text from record_store_settlement(''50000000-0000-0000-0000-000000000002'', 50, ''bank'', null, null, ''pending'', ''pss-key-0001'')') = '(90.00,40.00,pending)');
select c38('KEY: the same settlement key with another method → key_reused', u38(:F, 'select * from record_store_settlement(''50000000-0000-0000-0000-000000000002'', 50, ''cash'', null, null, ''pending'', ''pss-key-0001'')') like 'ERR:key_reused%');
select c38('KEY: … with another status → key_reused', u38(:F, 'select * from record_store_settlement(''50000000-0000-0000-0000-000000000002'', 50, ''bank'', ''B'', null, ''done'', ''pss-key-0001'')') like 'ERR:key_reused%');
select c38('done without a reference → reference_required', u38(:F, format('select set_store_settlement_status(%s, ''done'')', (select id from platform_store_settlements where client_key = 'pss-key-0001'))) like 'ERR:reference_required%');
select c38('done with the bank reference', u38(:F, format('select set_store_settlement_status(%s, ''done'', ''BANK-55'')', (select id from platform_store_settlements where client_key = 'pss-key-0001'))) = 'ok');
select c38('KEY: the original request replayed after it was marked done → the same record (no second payment)', u38(:F, 'select * from record_store_settlement(''50000000-0000-0000-0000-000000000002'', 50, ''bank'', null, null, ''pending'', ''pss-key-0001'')') = 'ok'
  and (select count(*) = 1 from platform_store_settlements where store_id = :PIZZA));
select c38('a pending one counts: 41 more → amount_too_high (40 left)', u38(:F, 'select * from record_store_settlement(''50000000-0000-0000-0000-000000000002'', 41, ''online'', ''ON-1'', null, ''done'', ''pss-key-0002'')') like 'ERR:amount_too_high%');
select c38('online 40 done with reference', u38(:F, 'select * from record_store_settlement(''50000000-0000-0000-0000-000000000002'', 40, ''online'', ''ON-1'', null, ''done'', ''pss-key-0003'')') = 'ok');
select c38('… nothing left for the platform to pay Pizza', v38(:F, format('select pp_available::text from store_position(%L)', '50000000-0000-0000-0000-000000000002')) = '0.00');
select c38('Pizza paid → nothing_due (no double payment)', u38(:F, 'select * from record_store_settlement(''50000000-0000-0000-0000-000000000002'', 1, ''cash'', ''C'', null, ''done'', ''pss-key-0004'')') like 'ERR:nothing_due%');
select c38('Kebab: courier-paid goods are never paid again by the platform → nothing_due', u38(:F, 'select * from record_store_settlement(''50000000-0000-0000-0000-000000000001'', 1, ''cash'', ''C'', null, ''done'', ''pss-key-0005'')') like 'ERR:nothing_due%');
-- both paths in sequence on ONE store: Kebab switches to «platform settles»; old orders keep «courier pays» (snapshot)
select u38(:T, 'select set_store_pay_rules(''50000000-0000-0000-0000-000000000001'', true, true, true, ''platform_settles'')');
insert into ex select 'K', po38('Kebab', 2, 'cash')::bigint;
update orders set driver_id = :DR, status = 'pickedup' where id = (select id from ex where k = 'K');
select c38('BOTH PATHS: a platform-settled order cannot get a courier payment → not_driver_pays', u38(:DR, format('select * from record_store_payment(%s, 100, ''CHK-K'', null, ''dsp-key-K001'')', (select id from ex where k = 'K'))) like 'ERR:not_driver_pays%');
select u38(:DR, format('select deliver_order(%s, 110)', (select id from ex where k = 'K')));
select c38('BOTH PATHS: Kebab platform part = 90 (order K only); the courier-paid part and its payments are untouched',
  v38(:F, format('select row(cp_net_due, cp_paid_confirmed, pp_net_due, pp_available)::text from store_position(%L)', '50000000-0000-0000-0000-000000000001')) = '(360.00,400.00,90.00,90.00)',
  v38(:F, format('select row(cp_net_due, cp_paid_confirmed, pp_net_due, pp_available)::text from store_position(%L)', '50000000-0000-0000-0000-000000000001')));
select c38('BOTH PATHS: the platform pays Kebab 90 for K', u38(:F, 'select * from record_store_settlement(''50000000-0000-0000-0000-000000000001'', 90, ''bank'', ''BK-K'', null, ''done'', ''pss-key-0006'')') = 'ok');
select c38('BOTH PATHS: then a courier payment on an OLD courier-paid order does not reopen the platform part (still 0)',
  u38(:DR, format('select * from record_store_payment(%s, 100, ''CHK-B2'', null, ''dsp-key-B002'')', (select id from ex where k = 'B'))) like 'ERR:already_recorded%'
  and v38(:F, format('select pp_available::text from store_position(%L)', '50000000-0000-0000-0000-000000000001')) = '0.00');
-- an order with no method set (store not configured when it was placed) is shown apart, payable by neither path
update orders set pay_rules = null, driver_id = :DR, status = 'delivered' where id = (select id from ex where k = 'D1');
select c38('no method on the order → shown as «unassigned» (90), not payable by the platform', v38(:F, format('select row(unassigned_due, pp_available)::text from store_position(%L)', '50000000-0000-0000-0000-000000000001')) = '(90.00,0.00)',
  v38(:F, format('select row(unassigned_due, pp_available)::text from store_position(%L)', '50000000-0000-0000-0000-000000000001')));
select u38(:T, 'select set_store_pay_rules(''50000000-0000-0000-0000-000000000001'', true, true, true, ''driver_pays'')');
select c38('the old cash_balances counts only orders from before the start, none of the new ones', v38(:F, 'select coalesce(sum(balance), 0)::text from cash_balances()')::numeric = (select coalesce(sum(cash_collected), 0) from orders where status = 'delivered' and cash_collected is not null and cash_settled_at is null and created_at < acc_start()), v38(:F, 'select coalesce(sum(balance), 0)::text from cash_balances()'));
select c38('a courier / merchant cannot record platform settlements', u38(:DR, 'select * from record_driver_settlement(''d0000000-0000-0000-0000-00000000000d'', ''platform_to_driver'', 1, null, null, ''pds-key-0009'')') like 'ERR:not_allowed%'
  and u38(:M, 'select * from record_store_settlement(''50000000-0000-0000-0000-000000000001'', 1, ''cash'', ''x'', null, ''done'', ''pss-key-0009'')') like 'ERR:not_allowed%');
select c38('app users cannot write the record tables directly', u38(:F, 'set local role authenticated; insert into platform_driver_settlements(driver_id, direction, amount, before_amount, after_amount, recorded_by, client_key) values (''d0000000-0000-0000-0000-00000000000d'', ''platform_to_driver'', 1, 1, 0, auth.uid(), ''pds-key-xxxx'')') like 'ERR:permission denied%');

-- ================= rollbacks =================
\set ON_ERROR_STOP off
\i sql/rollback_patch38.sql
\set ON_ERROR_STOP on
select c38('full rollback with records → refused, nothing changed', to_regprocedure('record_driver_settlement(uuid,text,numeric,text,text,text)') is not null
  and (select count(*) from platform_driver_settlements) = 4 and v38(:F, 'select cash_held::text from driver_position(''d0000000-0000-0000-0000-00000000000d'')') = '110.00');
\i sql/rollback_patch38_keep_records.sql
select c38('partial rollback: checkout no longer enforces the agreement (live place_order)', po38('Pizza', 1, 'card') ~ '^[0-9]+$');
select c38('… records, positions and the old-cash split kept (held 110 from order K, advance 0, old cash_balances still excludes new orders)', v38(:F, 'select row(cash_held, advance_due)::text from driver_position(''d0000000-0000-0000-0000-00000000000d'')') = '(110.00,0.00)'
  and v38(:F, 'select coalesce(sum(balance), 0)::text from cash_balances()')::numeric = (select coalesce(sum(cash_collected), 0) from orders where status = 'delivered' and cash_collected is not null and cash_settled_at is null and created_at < acc_start()));
\i sql/schema_patch38.sql
\i sql/schema_patch38.sql
select c38('patch 38 re-applied twice: enforcement back, records intact', po38('Pizza', 1, 'card') like 'ERR:online_not_allowed%' and (select count(*) = 4 from platform_driver_settlements));

\pset tuples_only off
select n, case when ok then 'PASS' else 'FAIL' end as r, label, left(got, 80) as got from r38 order by n;
select 'PATCH38 ' || count(*) filter (where ok) || '/' || count(*) from r38;
