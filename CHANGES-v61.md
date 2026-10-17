# v61 — trial batch: courier accounting per the owner's operation + refund sequences (local, NOT applied)
Branch `fix/trial-v61` from `prep/batch3-v60` @ a946b8c (v60e). v58 / v59b fixes and the delivery-photo check kept.
No live SQL, no publish, no merge, no real data. The customer design is NOT changed (only two receipt values corrected, below);
the approved design is to be applied later ON TOP of this branch, keeping its fixes and functions.

## 1. Courier accounting («courier pays the place»)
- Owner's example: meal 100, delivery 20 → the courier pays the place 100, collects 120, keeps 20 → 0 to hand over, 0 owed.
- The rule is kept on each order: `pay_rules.courier_pay = 'keeps_fee_from_cash'` (snapshot at checkout; history untouched).
- A recorded payment to the place counts as paid; the place's confirmation is optional; a disputed payment is held apart
  (not paid, not taken from the courier, not paid to him); no responsibility is assigned.
- The platform commission stays owed BY THE PLACE (shown, not deducted from what the courier pays); how it is collected is open.
- Payments on unfinished / cancelled orders are kept apart (not netted, not owed automatically — open decision).
- «Platform settles» reviewed separately: the courier hands over all the cash; his pay is paid by the platform (never netted).
- A later status change erases neither collected cash nor the courier's pay for a delivered order.
- Positions: `driver_position` (collected, paid to places, pay kept, handed, net, to hand over, owed to him, platform-paid pay)
  and `store_position` (bill, paid by couriers, unpaid, disputed, open, owed by the place; platform part; unassigned).

## 2. Refunds (patch 37)
- Proven paid = wallet (spend − automatic return) + collected cash, whatever the status; minus every support refund.
- The automatic wallet return on cancel / reject is capped by what is still refundable → SA (refund 200, then cancel) = 200
  back, not 250; SC (cancel, then refund the cash 150) = 200, not 50; refund while in progress then cancel = 30 for 30.
- Points stay in their own ledger (never counted as money). No new entitlement; the two proposal files are not adopted.

## 3. Apps
- Admin: store card (bill / paid by couriers / unpaid, confirmation optional, disputed, open, owed by the place, platform part);
  courier card (collected, paid to places, pay kept, to hand over, owed to him, platform-paid pay apart); order card: the
  recorded automatic return (capped) instead of the whole wallet part.
- Courier: per order «pay the place / collect / keep / hand over» and the amount prefilled with the bill; «my money» as above.
- Restaurant: settlement card (bill, received from couriers, left, owed to the platform, platform part); confirmation optional.
- Customer (no design change): the receipt of a cancelled order shows the RECORDED automatic return (it can now be smaller, or 0).

## Checks (local PostgreSQL stand-in / Chromium previews — not the live DB, not iPhone)
test_patch37 72/72 · patch37_race 14/14 · test_patch38 100/100 · patch38_race 17/17 · trial_v61_integration 20/20 (four apps,
one database) · patch38_ui_check 50/50 · patch37_ui_check 11/11 · uat3_check 70/70 · flow_check 0 fails · ui_rules 0 fails ·
qa_all (four apps) — see STATUS-PLAN.md. Not re-run (unaffected, core unchanged): smoke, cart, courier, merchant_stats, v58 checks.
Stand-in fix: the patch-38 stand-in lacked the live trigger `trg_orders_wallet_return` (now added; found by the integration check).
