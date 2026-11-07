# Continuation 24: bounded business-logic source review

2026-11-07 UTC. Read-only review of saved server definitions and prior test evidence; no SQL or network calls, no new fixtures, no app/source edits, no repeated sequential tests. Input hashes are in inputs.json. The restored source checkout contains no SQL files found by the targeted SQL search; saved definitions therefore establish the reviewed database snapshot, not an assertion about unobserved current provider state.

## Outcome

No NEW demonstrated financial exploit was established in this review. Several concrete coverage gaps below remain untested; they are not passed controls or confirmed vulnerabilities. Existing expiry fix and sequential refund/settlement evidence were reused, not rerun. No protected orders/accounts/receipts were changed.

## Inspected controls and narrow results

| ASVS 5.0.0 | Inspected code/evidence | Narrow result and limit |
|---|---|---|
| V2.2.1, V2.2.2, V2.2.3 | place_order, price_line | Store/item availability and store ownership relation are checked; options are resolved against their own groups, deduplicated and capped at 40. Quantities are clamped 1–50 and line count capped at 60. Server obtains item/option prices, discounts, delivery and commission; caller fee is an equality confirmation, not the source of price. No demonstrated client-total override. Underlying price/table finite-value constraints still need verification. |
| V2.3.1 | deliver_order, merchant_review_order, customer_confirm_order, fulfillment guards | Delivery locks order and requires assigned driver + pickedup. Price proposals reject closed states and refuse wallet/points/discount/promo/courier contexts needing support. Customer approval binds revision/base total/customer, enforces deadline, and locks order/approval. Closed-state bypass was not demonstrated. Admin set_order_status intentionally allows broad changes; the approved exceptional-admin procedure and complete audit requirements need evidence before declaring this acceptable or a defect. |
| V2.3.2, V2.3.4 | finance_execute | Request advisory lock precedes command lookup; replay verifies actor, operation, target and exact input. Settlement obtains driver advisory lock and selects eligible orders in ascending ID FOR UPDATE; only UPDATE RETURNING supplies totals. Wallet adjustments lock customer profile before balance check. Inspection supports intended serialization, but does not prove multi-connection behavior. |
| V2.3.2, V2.3.3 | ticket_set_status + existing finance-valid evidence | Ticket lock precedes shared order lock; aggregate refunds are capped against order total; one ticket cannot refund twice. Existing tests establish sequential cap/replay rejection and exception rollback only. No new tests repeated. |
| V2.3.1–V2.3.4 | order_return_action | Request then shared order lock; actor/operation/payload replay binding; staged depart/cancel/receive/refund actions; remaining claim checked when confirming. Multiple pending reports do not themselves credit money and confirmations recheck remaining. No duplicate monetary effect proved. |
| V2.3.2 | snapshot_cash and guard_cash_allocation | Snapshot uses approved per-store policy, locks order and policy, refuses platform share above fee; protected allocation columns cannot be changed after initial snapshot under inspected trigger. Broader financial write paths remain separate coverage. |
| V2.4.1 | pilot_private.guard_order | Admission global active/daily count occurs after dedicated advisory lock. This source observation does not establish overload resistance or provider cost caps. |

## Precise untested gaps and next safe steps

1. **Per-customer quota race (V2.3.2, V2.3.4, V2.4.1).** place_order checks hourly and unfinished-order counts before acquiring the profile row lock. Two different-key requests can both observe a count below the per-customer threshold before one waits. A later pilot global capacity lock controls a different resource and does not visibly recheck the customer count. This is a source-level race candidate, not an observed bypass. Next: a permitted isolated multi-session transaction harness proving the exact threshold schedule, including pilot guard and rollback, without durable records or protected data. Do not repeat a previously rejected concurrency setup or bypass its rejection. If confirmed, minimal candidate is to lock the customer before these counts or recheck the counts after obtaining the existing lock; verify lock ordering against group locks and other money paths first.

2. **Special numeric cash values (V2.2.1, V2.2.2).** Saved deliver_order checks p_cash NULL/<0; it has no explicit finite-value check or upper range. Finance_execute and return-action amounts have upper bounds, but deliver_order has a distinct validation shape. Need current column types/check constraints/triggers plus a harmless local PostgreSQL or approved rollback test for NaN/infinity parsing and rejection. Do not assume IEEE JavaScript comparison behavior applies to PostgreSQL numeric. No accepted nonfinite value or financial impact was demonstrated. A business upper bound must not be invented.

3. **Missing quantity/null paths (V2.2.1, V2.2.3).** fulfillment quote_lines uses `qty not between 1 and 50`, which does not itself reject SQL NULL. Need current order_items NOT NULL/check constraints and approved caller-level test before claiming a bypass. The eventual insert may correctly abort; a source predicate alone is not sufficient evidence of corrupted totals.

4. **Actual concurrent refund/settlement/retry (V2.3.3, V2.3.4).** Existing finance-valid tests are sequential and use exceptions after function completion. They do not establish TCP interruption, mid-statement crash, two independent DB sessions, lock starvation/deadlock handling or HTTP retry behavior. Source review cannot close this gap. Need a permitted test harness with rollback-only synthetic data visible to both sessions, or an explicitly approved isolated disposable database. No permanent financial fixtures may be created to evade the rejected setup.

5. **Legacy/exceptional administrator changes (V2.3.1, V2.3.5 additional L3 scope).** set_order_status grants admin a broad transition path; other guards prevent certain price/confirmation changes but do not alone document all financial closure restrictions. Need the approved admin exception policy and audit/approval evidence; do not change rules by assumption. Multi-user approval is not proved by role checks.

6. **Current server attribution.** Parent should compare current deployed definition fingerprints with the saved inventory before using these observations for current-version acceptance. Session revocation/permission wrappers from later releases must not be inferred absent merely because this saved inventory is older.

## Acceptance boundary

All rows are partial evidence. No full ASVS requirement was closed, no vulnerability was invented from an untested edge, and no live concurrency success is claimed. This is work by the implementation team, not an independent penetration test. Existing approved financial rules and protected orders #1/#2/#3, including the unsettled #3 amount, remain unchanged.
