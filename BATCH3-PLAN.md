# Batch «delivery proof · support refunds · cash settlement» — preparation only, NOT implemented (17 Oct)
Base: `fix/uat3-v59` @ c6c8593 (v59b, kept unchanged). Mapped against the repository and the owner's live read of 17 Oct (batch 2).
Missing live definitions: `sql/verify_batch3_readonly.sql` (one read-only result). No SQL run, nothing published or merged.
Out of scope: points expiry policy, cancellation responsibility, Safari.

## What the source shows
| Item | Source (live = read 17 Oct, repo = sql/) | Gap |
|---|---|---|
| UAT005 proof photo | live deliver_order: path format only `<courier>/<order>/<file>.jpg`; repo patch 34: private bucket «proofs», insert only by that courier while the order is picked up, read by courier / customer / staff | the server never checks that the file EXISTS (or its type / size); a typed path passes |
| Support refund | repo ticket_set_status (patch 26, live not read): cap = orders.total − earlier 'refund' of the order; one refund per ticket (unique index) | total ≠ money really received: wallet part already returned on cancel ('return') is refunded again; uncollected cash and points value are counted; no lock on the order → two tickets of one order can pass the cap at the same moment |
| ticket_refund_room (live) | total − 'refund' only | same base as above, so the screen shows a wrong maximum |
| Cash settlement (live settle_driver_cash) | finance only; settles ALL unsettled cash; sum read, then update, without a lock; no amount, receiver, reference or remainder recorded (only cash_settled_at per order + audit_log of that column) | no partial amount; two staff at once → the second returns a sum that was already received; no receipt record |
| Cash limit | admin screen: warning ≥ cash_limit, manual «pause orders» (accept_blocked); repo driver_accept checks accept_blocked only; dispatch_next not in the repo | where the limit really acts is unknown until the live read |
| Refund lookup on the receipt (v59b) | latest 60 wallet operations on the phone | not per order |

## Unified scope (after approval and the live read)
1. Proof photo (UAT005) — deliver_order: when a photo is given (always for «leave at the door»), it must exist in storage
   (bucket proofs, exact path, uploaded by this courier, image/jpeg, ≤ 1 MB, uploaded after pick-up) or the delivery is refused
   (`photo_missing`). Courier app: clear message + retry upload. Prerequisite: the function owner can read storage.objects (query §9);
   no update / delete policy on proofs (query §3).
2. Support refunds — one rule in ticket_set_status AND ticket_refund_room: refundable = money really received for the order
   (wallet part not returned + recorded cash + card part as decided below) − all earlier refunds of the order. The order row is locked
   for the check (two tickets cannot pass together); one refund per ticket stays. Admin screen shows the breakdown of the maximum.
3. Cash settlement — new immutable record `cash_settlements` (driver, amount > 0, received_by, received_at, reference, note,
   due_before, remaining_after); new function receiving ANY positive amount ≤ the amount due, under a lock on the courier
   (concurrent receipts serialise). Courier balance = recorded cash − received. Admin: amount field (default = all), reference,
   history; courier app: history with time, amount, receiver, remaining. The limit stays only a rule for NEW orders, independent of settlement.
4. Refund lookup per order — the receipt reads the wallet entries of THIS order (refund + return) directly, so the 60-operation limit
   and its note go away; on a failed read the receipt says «not checked».
Tests: local PostgreSQL (functions, locks with two sessions, storage stand-in) + screens of courier / admin / customer affected only.

## Blocking decisions (owner)
1. Card / Apple Pay part of an order: no payment provider, so a charge is not proven. Count it as received for the refund cap,
   or refuse refunds on that part until a payment record exists?
2. Points part (points_value): excluded from money refunds, or returned as points by the ticket?
3. Cash: partial receipts with a running balance (recommended) — and what to do with an amount above the due: refuse (recommended)?
4. After the live read: should passing the cash limit block new offers automatically and lift after settlement, or stay manual?

## Prepared package (17 Oct, local only — NOT applied, nothing published or merged)
Live read 17 Oct used as the base (`verify_batch3_readonly`): dispatch_next / eligible_couriers do NOT use the cash limit (only the
manual accept_blocked), deliver_order checks the path format only, ticket_set_status / ticket_refund_room cap = total − refunds,
settle_driver_cash settles all without lock or record; the proofs bucket is private (1 MB, image/jpeg), no update / delete policy
on proofs; the owner of deliver_order (postgres) can read storage.objects.

Files: `sql/schema_patch37.sql`; rollbacks (see «Rollback» below); `sql/test_patch37_setup.sql` + `sql/test_patch37.sql`
(isolated stand-in data); `tools/patch37_race.py` (two real sessions on a LOCAL test database: first on a local copy of the live
definitions read on 17 Oct, then with patch 37 — not experiments on production);
`tools/patch37_ui_check.py`; app changes in talabat-core.js, customer.html, admin.html, driver.html.

1. Proof: `proof_exists()` (internal) — bucket proofs, exact path, uploaded by this courier, finished upload (size 1 B–1 MB),
   image/jpeg, current (not archived / delete marker). deliver_order raises `photo_missing`; everything else unchanged.
   Courier app: the message, and the photo must be taken again.
2. Refunds: `order_refund_cap()` used by both functions. Proven paid = wallet spent and not returned (wallet ledger) + recorded
   cash of a delivered order (at most its cash part). Card / Apple Pay without capture data, unrecorded cash and points = not paid.
   Room = proven paid − earlier support refunds; 0 while the order is in progress (`order_not_finished`), because a refund
   and the automatic return of a later cancel would otherwise pay the wallet part twice. ticket_set_status locks the ticket,
   then the order (the cancel / return trigger updates the same row). One refund per ticket kept. No compensation path created.
   Admin: the maximum with its breakdown. Customer receipt: refunds of THIS order read from the server (no 60 limit).
3. Cash: `cash_settlements` (immutable, RLS: finance or the courier himself; written only by the function), `receive_driver_cash`
   (finance; any amount > 0 and ≤ owed; lock on the courier; idempotent per form key; records amount, receiver, time,
   reference, note, owed before, remaining). `settle_driver_cash` keeps its signature for old screens (one receipt of all owed).
   `cash_balances` = owed. The limit is not involved. Admin: amount / reference / note + history.

### Allocation of a partial receipt to orders — FOR REVIEW (no choice made)
- A (prepared in the SQL): running balance. Owed = recorded cash − receipts; orders are not marked. Simple, exact for money;
  the per-order line «принято / не принято» in the admin order card no longer changes for new receipts (to be replaced after the decision).
- B: oldest orders first. A receipt closes whole orders in date order; the order it stops in keeps a partial amount
  (needs a column for it). Per-order status stays meaningful; more code.
- C: whole orders only. The admin picks orders; the amount must equal their sum. No partial amounts (conflicts with «any positive amount»).

### Blocking decisions only
1. Allocation model A / B / C (above).
2. Refunds only after the order ends (`order_not_finished`) — part of the rule that prevents paying the wallet part twice.

Activation order when approved: SQL patch 37 first, then the app files (the old admin «receive all» keeps working meanwhile).

## Review v60b (17 Oct, local only)
### Rollback
- `sql/rollback_patch37.sql` (full): checks FIRST, before any change, whether cash receipts exist; if yes it stops with
  `rollback_unsafe` and nothing changes (also when run without ON_ERROR_STOP: the transaction is aborted). Without receipts it
  restores the five live definitions exactly and removes every patch-37 object.
- `sql/rollback_patch37_keep_cash.sql` (partial, when receipts exist): restores deliver_order, ticket_set_status and
  ticket_refund_room exactly as live and removes the proof / refund helpers; the cash part stays, so money received keeps counting
  and is never shown as owed again. No order is marked by hand.
### Refund + status change sequences (totals given back to the customer, test_patch37 «S…»)
- SA delivered (wallet 50 + recorded cash 150) → support refund 200 → admin sets «cancelled» (allowed by the live
  set_order_status): 250 given back for 200 paid (the automatic return adds the wallet 50 again) and the collected 150 drops out
  of what the courier owes. GAP — not closed by patch 37.
- SB cancelled before delivery (wallet 40) → refund: refused; 40 back for 40 paid. Correct.
- SC delivered → admin cancels first → refund of the cash part: refused; 50 back for 200 paid and the 150 is neither refundable
  nor owed by the courier. GAP.
- `order_not_finished` alone does not cover SA / SC (the order IS finished when refunded).
- Minimal handling, prepared for review only (NOT in patch 37): `sql/option_no_cancel_after_delivery.sql` — a delivered order
  can no longer be turned into cancelled / rejected (the only change is the admin line of set_order_status; its rollback restores
  the live definition). With it: SA → the cancel is refused, 200 back for 200 paid, the courier still owes 150; cancelling before
  delivery and rejecting non-delivered orders still work. It changes the allowed status transitions → owner decision.
  Alternative (also a decision, not prepared): change the return rule (return = wallet used − support refunds already made) and
  count recorded cash even after a cancel — more rules touched.
### Model A display
- Admin order card: a delivered cash order is shown «in the courier balance — money received is counted on the courier balance,
  not per order»; never «not handed over» just because cash_settled_at is empty. Orders marked by the old full settlement keep
  their mark, labelled «before balance accounting». Model A stays FOR REVIEW (B / C above).

### Blocking decisions (all still open)
1. Allocation model A / B / C.
2. Refunds only after the order ends (`order_not_finished`).
3. Delivered → cancelled / rejected: forbid it (option file), or change the return rule — or leave the SA / SC gaps.

## v60c — package per the owner's operating requirements (17 Oct 10:23), local only, NOT applied
The v60 «model A» (all cash a courier took = his debt; receipts on one running balance) is WITHDRAWN. Nothing old is migrated.

### Patch 37 (revised) — proof + refunds only
- Proof: the stored object must have a recorded type image/jpeg (a missing type is refused, not assumed), size 1 B–1 MB, current.
- Refund cap unchanged in principle (proven paid − earlier refunds, locks). «Refund only after the order ends» is now a separate
  PROPOSAL file (`option_refund_after_finish.sql`, with rollback) — NOT in the patch.
- `option_no_cancel_after_delivery.sql` (proposal): a delivered order stays delivered (also no delivered → ready → cancelled);
  calling with the same status again changes nothing (done_at kept). NOT in the patch.
- Rollback: plain (patch 37 keeps no money records).

### Patch 38 — store agreements + separate records
- Store agreement: accept_online / allow_wallet / allow_points (defaults = today) + settle_method (courier pays the store /
  platform settles / not set). Only admin / staff «stores» (guard trigger + audit). Checkout enforces it (server + app: a
  cash-only store shows only «cash» with a RU/EN notice; wallet / points hidden when not allowed). The rules in force are kept
  on each order (orders.pay_rules); historical orders untouched. No electronic capture is created (no provider).
- Records kept apart: customer collection (cash_collected, wallet ledger — kept whatever the status), courier → store payments
  (reference / photo, confirmed or disputed by the store or finance, who decided), courier pay owed (driver_payout of delivered
  orders) and paid (platform → courier), platform ↔ courier settlements both ways (receiver / payer, reference, before / after),
  store owed (the restaurant's existing net formula) and paid by couriers (non-disputed) or by the platform (method, reference,
  status pending / done / failed). Nothing netted automatically; a status change erases no collection or payment.
- No double payment of a store: one active courier payment per order; platform settlements capped by what is left (pending
  ones count); every write under a lock + per-form idempotency key.
- New accounting start (`accounting_start`, set once by finance at activation). Older orders stay with the old cash_balances /
  settle_driver_cash (which then only look at older orders). `reconcile_transition_readonly.sql` (live-compatible, read only)
  shows what the old records still hold, for review before the start is chosen.
- Rollbacks: full (refuses while any money record exists — checked under a table lock, tested against a concurrent insert);
  keep-records (only checkout enforcement goes back).

### Worked example (test_patch38, Plov 50 TJS, delivery 10, courier pay 10, commission 10 %)
| Order | Customer paid | Courier → store | Store owed (net) | Courier pay |
|---|---|---|---|---|
| A Kebab (courier pays) cash 110 | 110 cash | 100 (confirmed by the owner) | 90 | 10 |
| B Kebab mixed | 30 wallet + 80 cash | 100 (photo, confirmed by finance) | 90 | 10 |
| C Pizza (platform settles) cash 110 | 110 cash | — | 90 | 10 |
| E Kebab «card» (simulated, nothing captured) | 0 recorded | 100 disputed, then 100 again confirmed | 90 | 10 |
| D2 Kebab cancelled after the courier paid | 0 | 100 (kept; later disputed by the store) | 0 | 0 |
- Courier (before settlements): collected 300, paid to stores confirmed 200 + awaiting 200 → held −100 (the platform owes him);
  after E confirmed and D2 disputed → held 0. Pay earned 40, paid 15 (partial) → owed 25 — not netted with cash.
  Order G (Pizza) cash 110 → held 110; handed 60 (receiver «Finance Farhod», KASSA-7) → 50 left; G cancelled later → still 50.
- Kebab: gross 300 − commission 30 = owed 270; paid by couriers 400 → balance −130 (received more than owed, incl. 100 on the
  cancelled D2 and the commission not withheld); platform pays nothing (nothing_due).
- Pizza: owed 90; platform 50 by bank (pending → done with BANK-55) + 40 online (done, ON-1) → 0; a further payment → nothing_due.

### Blocking economic decisions (only these)
1. Courier-pays stores: how the platform commission is collected from the store (the courier pays the full receipt, so the
   store ends with a negative balance = what it owes the platform), and what «full receipt» is (the store's own price after its
   discount, i.e. today's «revenue» figure?) — today the courier records the amount actually paid.
2. Money paid to a store for an order that is then cancelled (D2): returned by the store to the courier, kept as the store's,
   or covered by the platform?
3. When a courier holds a negative amount (he advanced more than he collected): does the platform repay him as a separate
   payment (today: yes, only by a recorded platform → courier payment), and may cash he holds ever be offset against his pay?
4. The start date of the new accounting (after reviewing the transition reconciliation).
5. Proposals still open: «refund only after the order ends»; «a delivered order stays delivered»; SA / SC gaps otherwise remain.

## v60d — review fixes (local, NOT applied; no financial policy changed)
1. **Courier advance apart from his pay.** driver_position now gives: net cash on the CONFIRMED basis
   (collected − confirmed store payments − handed + advances repaid), cash held (≥ 0), advance due (the confirmed amount he paid
   stores beyond what he collected), and his pay — three separate balances. A third settlement direction `advance_repayment`
   (≤ advance due) is PREPARED FOR REVIEW; nothing repays an advance by itself and nothing is offset (paying his pay leaves the
   advance unchanged — tested). Whether and when advances are repaid stays a decision.
2. **Confirmed / pending / disputed kept apart** (courier and store views): pending = a precautionary reserve, never «paid»
   (cash may be taken from the courier only above the reserve); disputed = neither paid nor unpaid — not added back to the cash he
   holds, no responsibility assigned.
3. **No double payment across the two paths.** Store money is split by the method kept on each order: courier-paid orders
   (paid by couriers) and platform-settled orders (paid by the platform) never share a payment; orders without a method are shown
   apart and paid by neither path. Every store payment write (courier payment, its confirm / dispute, platform settlement and its
   status) takes the same store lock. Tested: in sequence (method switch, payments before / after) and at the same moment
   (settlement vs confirm, vs dispute, vs a courier payment; cash taken vs a dispute).
4. **Idempotency keys bound to the operation.** Each record keeps the request it was first sent with; the same key with the
   same data returns the original record (also after its status changed), with other data (order, amount, method, direction,
   reference, note, status) → `key_reused`. Concurrent replays serialise on the lock.
Checks: test_patch38 93/93, patch38_race 12/12, patch38_ui_check 40/40 + affected screens.

### Blocking economic decisions (all still open; nothing decided in this fix)
1. Courier-pays stores: how the platform commission (and store-funded points / cashback / free delivery) is collected from a
   store paid the full receipt by the courier (its confirmed balance goes negative).
2. A courier advance: whether / when it is repaid (the path is prepared), and whether it may ever be offset.
3. Disputed courier payments: who bears the amount and how a store that really was not paid gets paid (no path pays courier-paid
   goods a second time).
4. Money paid to a store for an order cancelled afterwards; cancellation / refund policy (proposal files still open).
5. Orders without a settlement method and the start date of the new accounting.
