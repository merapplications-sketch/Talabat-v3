# v61 — activation and rollback order (FOR REVIEW ONLY — nothing here has been run on the live database)

Branch `fix/trial-v61` (base chain: v56 → v57 → v58 → v59b → v60e → v61). Every step below is a proposal for the owner's review.
Tested only on a local PostgreSQL with stand-in data and a local copy of the live definitions read on 17 Oct, and in Chromium
on read-only previews. Not tested on the live database, not on iPhone.

## A. Before anything (read-only, no change)
1. Run `sql/verify_batch3_readonly.sql` on live and send the CSV. Claude compares it with the 17 Oct read (`live_b3.csv`):
   if any of `deliver_order`, `ticket_set_status`, `ticket_refund_room`, `trg_wallet_return`, `place_order`, `cash_balances`,
   `settle_driver_cash` changed since 17 Oct, the rollback files must be refreshed first (they restore the 17 Oct definitions).
2. Run `sql/reconcile_transition_readonly.sql` and send the CSV: what the old cash records hold before the start date.
3. Backup: a Supabase backup / point-in-time point noted, plus a CSV export of `orders`, `wallet_entries`, `support_tickets`.
4. Decisions needed before step C.4–C.5 (list in the report / BATCH3-PLAN.md): start date, method per store,
   online payment off for «courier pays» stores while no payment provider exists.

## B. Order of application (DB first, then apps — new apps need the new functions; old apps keep working on the patched DB)
| # | Step | Who | Effect on users | Check right after |
|---|---|---|---|---|
| 1 | `sql/schema_patch37.sql` (one transaction) | owner, SQL editor | delivery photo must exist; refund cap = proven paid − refunds; automatic wallet return capped by what is still refundable | `select to_regprocedure('order_refund_cap(bigint)'), to_regprocedure('proof_exists(text,uuid)');` both not null |
| 2 | `sql/schema_patch38.sql` (one transaction) | owner | none until a store is configured (defaults = today: online / wallet / points allowed, no method); new orders keep their rules | `select count(*) from stores where settle_method is not null;` = 0 |
| 3 | Publish the apps of `fix/trial-v61` (after the approvals of the earlier branches in the chain) | owner | new screens; money cards say «could not load» only if step 2 is missing | open each app, no error |
| 4 | Store agreements: admin → store → «Оплата и расчёты» for EVERY store in the trial | stores staff | checkout follows the agreement | customer checkout of one cash-only store |
| 5 | Start of the new accounting: admin finance, once (`set_accounting_start`) — after the old cash is settled with the old button | finance | money records start; old cash stays in the old screens | positions of one courier = 0 |
| 6 | First real order on a «courier pays» store, numbers checked against the owner's example (pay 100, collect 120, keep 20 → 0 / 0) | owner + one courier | — | admin → courier card |

Nothing is migrated automatically: orders before the start stay with the old `cash_balances` / «receive all».
The option files (`option_refund_after_finish.sql`, `option_no_cancel_after_delivery.sql`) are NOT part of activation.

## C. Rollback order (reverse: apps first, then 38, then 37)
| # | Step | When | What it keeps |
|---|---|---|---|
| 1 | Re-publish the previous app version (current main) | any problem in the apps | data untouched |
| 2a | `sql/rollback_patch38.sql` | only while NO money record exists (it refuses otherwise, under a table lock, before any change) | — |
| 2b | `sql/rollback_patch38_keep_records.sql` | money records exist | records, positions and the old/new split; checkout stops enforcing the store agreement (live `place_order` back) |
| 3 | `sql/rollback_patch37.sql` | after 2a/2b | restores the 17 Oct `deliver_order`, `ticket_set_status`, `ticket_refund_room`, `trg_wallet_return`; refunds already made stay (the wallet ledger is insert-only) |

Every file is one transaction (all or nothing) and can be applied again (tested: rollback, then patch twice).
