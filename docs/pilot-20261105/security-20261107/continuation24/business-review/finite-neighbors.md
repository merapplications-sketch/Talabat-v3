# Finite monetary value follow-up — 2026-11-07

Read-only source assessment after parent confirmed and patched deliver_order accepting NaN/Infinity. No SQL calls, fixtures, source/database mutations or repeated tests in this follow-up. Inputs: current-catalog.json, numeric-triggers.json, rpc21-inventory.json and previously extracted definitions.

## Confirmed finding: scope of impact

Parent reports rollback-only synthetic proof that a valid assigned driver could complete delivery storing non-finite cash_collected, and applied pilot_delivery_cash_finite_guard. Catalog shows cash_collected is unconstrained numeric; captured numeric probes show the old null/<0 predicate does not reject NaN or positive Infinity. ASVS V2.2.1 (valid monetary input) and V2.2.2 (trusted-service validation) apply narrowly. Parent owns before/after execution evidence and final severity.

Financial integrity impact: the collected-cash fact can be invalid while status becomes delivered; finance_driver_orders includes that fact in financial views. Do not claim an infinite settlement: inspected cash_balances and finance_execute sum immutable cash_platform_share rather than cash_collected. A non-null collection permits eligibility, but accepted finite zero/short collections with a note are already part of existing business behavior. No alteration to that policy is proposed. Loyalty generation uses item subtotal/discounts rather than collected cash; no reward amplification from this field alone is shown.

## Exact neighboring candidates; not confirmed failures

| Candidate | Observed source | Missing proof / next evidence |
|---|---|---|
| stores.fee_base and fee_per_km | validate_store only rejects coalesce(value,0)<0. delivery_calc adds fee_base to delivery amount; place_order also uses fee_base for courier pay under free delivery. | Current stores constraints, write grants/RLS, caller permissions and an approved rollback-only special-value test. fee_per_km is not consumed by inspected delivery_calc, so do not invent downstream impact for it. |
| menu_items.price | validate_item inspects name length and discount ceiling, not finite price. price_line returns menu price + selected option deltas. | Current menu_items price constraints, item approval/write rules, safe synthetic rollback proof. Negative-value prevention is distinct from nonfinite-value prevention. |
| item_options.price_delta | price_line validates option membership/availability/count, then sums price_delta unchanged. | Current option table constraints and write policies; effect of actual calculation and order triggers. No live accepted invalid option demonstrated. |
| Other existing app_settings keys | set_setting checks ranges for an enumerated set of known keys, then updates any existing matching key. | Current allowed keys and table constraints. All inspected delivery/loyalty keys have upper/lower bounds; no specific unbounded monetary key identified, so this is inventory completeness only, not a defect. |

All candidate mapping is partial V2.2.1/V2.2.2; dependent cross-field consistency relates to V2.2.3. Do not mark them failed before verifying effective constraints and runtime reachability.

## Neighboring guard shapes inspected

- finance_execute wallet adjustment uses abs(round(amount,2))>100000; return_action rejects amount<=0 or amount>9999999999.99 and scale>2. These have upper bounds unlike the old cash guard. Source review predicts rejection under PostgreSQL numeric ordering but is not runtime evidence.
- ticket_set_status bounds refund against order total plus prior refunds. Its protection assumes finite order total/prior amounts; a poisoned upstream total is a separate prerequisite not demonstrated here.
- place_order tip uses a finite allowlist; caller fee is compared to calculated fee, and requested wallet amount is compared to the bounded selected debit. These are distinct from simply accepting p_cash; no special-value acceptance established.
- set_my_cashback, set_store_loyalty, set_store_free_delivery and set_my_free_delivery use bounded ranges. No new bypass established.
- Current order_items catalog confirms qty NOT NULL plus 1–50 check. Earlier quote_lines NULL-quantity candidate cannot persist a NULL quantity through customer_confirm_order insert under these constraints; malformed proposal/error UX remains untested. Do not retain this as a proven monetary-integrity vulnerability.

## Limits

Current-catalog covers orders/order_items, not the candidate store/menu/option schemas. Trigger inspection alone cannot replace omitted constraints or other write paths. No complete financial, numeric-validation or concurrency ASVS requirement is closed. No finance passed-all claim, deployment claim, real-device claim, or independent-review claim is made.
