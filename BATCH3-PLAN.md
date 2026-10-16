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
