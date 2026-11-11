# PRICE-01 — narrowly scoped contract proposal, NOT IMPLEMENTED

Owner business rule is already approved: any changed item price, up or down, needs explicit approval of new price and total before a new order/debit can commit. This document does not ask to reapprove that rule, prices, discounts, tip policy, rounding, financial formulas or a deployment.

## Exact authorization needed

Approve a versioned **price-consent request/response extension for isolated development**, mandatory on NEW creation across all four candidate entries. A legacy client without that evidence must no longer create a new order; it remains able to recover an existing one. This intentionally changes the old-client creation compatibility documented in SQL103. The algorithm/domain/input order/canonicalization/key policy of HMACv1 remain byte-for-byte unchanged.

Preferred placement: a dedicated `p_extra.price01` object with its own `version:1`. The name/schema is a proposal, not an already accepted or deployed API. Existing HMAC already binds the entire extra object, including unknown properties; no MAC exception, excluded field or separate fingerprint is proposed. Existing records are not migrated or rehashed.

Proposed concrete shape (synthetic values, TJS):

```json
{
  "price01": {
    "version": 1,
    "lines": [{
      "item_id": "40000000-0000-4000-8000-000000000092",
      "qty": 1,
      "base_price": "20",
      "options": [{"id": "70000000-0000-4000-8000-000000000092", "price_delta": "3"}],
      "unit_price": "23",
      "restaurant_discount": "2.30",
      "happy_hour_discount": "0",
      "net_items": "20.70"
    }],
    "totals": {
      "subtotal": "23",
      "restaurant_discount": "2.30",
      "happy_hour_discount": "0",
      "promo_discount": "0",
      "points_value": "0",
      "delivery_fee": "2",
      "tip": "0",
      "wallet_used": "5",
      "cash_due": "17.70",
      "total": "22.70"
    }
  }
}
```

Amounts are explicit finite decimal strings in TJS for lossless transport, not a new rounding rule. Lines must match original item/quantity/option identities; item/option order in the frozen original payload is retained. Restaurant discount and HH incremental discount are separate; neither is counted twice. The example follows existing synthetic arithmetic23−2.30+2=22.70 and22.70−5=17.70; it is not an operating price. Comparison parses amounts exactly and rejects missing/malformed/nonfinite amounts; it must not use a tolerance to authorize a changed price. No server price is replaced by a client price. Exact serialization is frozen before send and is never retroactively applied to history.

Proposed response extension: keep the existing rejected/closed/no_effects/closure_id/state_version envelope, with `reason: price_changed` and an optional `price_review` containing version1 and the server-calculated shape above. No customer identity/address/key material is echoed inside price_review. A review may be actionable only after a real committed closure receipt; an unresolved response is not approval to resubmit. The authoritative closure remains immutable. If the review response is lost, first recover the original outcome; obtaining a fresh price review cannot change that old attempt or reopen its key.

## Reviewable behavior

1. A new checkout freezes the actually presented item/option prices, quantities and line discounts, plus the presented financial breakdown and final total, alongside the exact submission context. Metadata must distinguish constituent prices even when changes offset in the total. Capture approval at the user's explicit confirmation, not by assigning a newer server result silently.
2. Compare against the server pricing used for persistence inside creation's transaction. A quote/preflight alone is insufficient. A later catalog change must either leave the persisted approved snapshot intact or produce a fresh review with no committed order/debit. No later helper/trigger may reprice after the final comparison; this must be demonstrated for every dependency included in the candidate.
3. Missing/malformed consent or a changed price cannot become success. For mismatch return a bounded non-sensitive review describing old/new item/option prices and totals, with a new reason such as `price_changed`. Preserve existing `created/replayed/historical_recovered/conflict/unresolved/rejected` meanings. Definitive rejection still requires atomic rollback plus committed closure proof before the client retires the old attempt.
4. UI shows the differences and new total using current approved components. Explicit acceptance is distinct from showing/refreshing a price. Editing cart/options/promo/tip/address/schedule or a newer tab draft invalidates the pending review. A delayed reply cannot replace a newer review or draft. No redesign.
5. Price reapproval never mutates a sent payload. For a proven terminal rejection, use existing endRejected confirmation and closure fence, then a new explicit attempt/key. No background key replacement, no automatic replay with updated prices. Closure-resource denial stays unresolved and cannot authorize a replacement.
6. A pre-change attempt without consent is recovered first. If its order exists, return original saved prices and fingerprint. If unresolved, keep original key/payload; absence alone is not rollback proof. A safe server rejection of a not-created legacy request must be obtained under the established lock/fence protocol before any new price-approved attempt. Do not append a price field to its saved payload.
7. The old bigint wrapper must fail clearly for missing/changed approval; it cannot remain a bypass. The modern wrapper may carry review detail. Internal/private creator enforces the same condition; no grants or RLS changes.
8. Any preflight/review generation must not persist an order, spend wallet/points, consume promo or create a false closure. Do not implement a quote by executing arbitrary financial side effects and assuming external effects roll back. Independent review must inspect actual transaction boundaries.

## Representation and financial invariants

- TJS unit labels explicit. Financial values derive from the existing arithmetic; no new price/percent/floor, epsilon removal or formula change. Proposed transport uses unambiguous finite decimal values, with validation and comparison specified before coding; it must not round an unapproved difference away.
- Item and option identities, quantities and the matching review context are bound. Compare per-line components and total; total-only equality cannot hide offsetting changes.
- Do not normalize historical payloads or sort their arrays. New consent serialization must be deterministic before freezing; HMAC keeps its existing whole-payload rules.
- Retain manual tips0/1..100 and explicit-NULL rejection, including consumed-tip completion and explicit later tip selection. Tip remains outside commission/points and inside driver payout exactly as before.
- Wallet/points/promo and mixed-payment results must be derived by the existing functions and compared as displayed. Independent expected test values come from documented rules and synthetic inputs, not by accepting fixture output as the oracle.
- No TTL/resource quotas/cost decisions or production defaults are introduced. Reuse closure budget semantics unchanged.

## Proposed files, without editing historical sources

| Future delta | Purpose |
|---|---|
| New tests/price01 candidate SQL overlay/generator | Apply after accepted NULL01; add validation/final comparison and bounded review response to creator/wrappers, preserve old definitions as history. |
| New tests/price01 client overlay/generator | Apply after accepted TIP02 generator; capture explicit consent, render review, preserve ownership and durable frozen payloads. |
| New price-contract/client/native tests | Acceptance conditions below. Existing TIP and106 assertions stay intact. |
| docs/review/price01 | Source diff, evidence, invariants, QA handoff and rollback constraints. |

No modification is proposed to schema keys/bindings/closures, canonical103/mac103/request_payload103, historical103–106/TIP source, financial formulas or accepted TIP02 behavior. If implementation reveals that one of those is necessary, stop at that narrower conflict before altering it.

## Acceptance matrix after approval

| ID | Required proof |
|---|---|
| PRICE-A | Reproduce baseline failures, then zero committed order/debit/points/promo effects for unapproved up/down changes on all four entries. Missing consent also fails safely; same-price approval succeeds once. |
| PRICE-B | Item/option/store/item discount/HH/promo changes; changes with equal net total; option removal; free delivery, total floor, wallet/points interactions. Existing formulas and tip isolation unchanged. |
| PRICE-C | Price changes before quote, after display, between approval/send, during lock wait and during dependency reads. Compare the exact stored snapshot; no check-then-use window. Independent PG connections and bounded lock assertions. |
| PRICE-D | Ordinary/group/eligible scheduled order; authorization first, expired group/time recovery, historical rawNULL/stored0/tip3/sent20-stored0, v1 MAC replay/mismatch, all106 isolation fences. |
| PRICE-E | TCP before/after COMMIT; same-key concurrent retries; different keys/accounts; closure wins/success wins/resource denial; one order/spend; no payload injection/new key for unknown attempts. |
| PRICE-F | Explicit price approval/decline, cart edits, three tabs, reverse replies, lost ACK, intermediate saves/reload and C03/C04/TIP02 consumed-tip recovery. Separate Node VM from real Chromium/IndexedDB; Safari remains open until actual execution. |
| PRICE-G | Atomic install/reapply, recovery-only rollback and re-upgrade preserve completed orders, MACs and closed keys. Old writer creating without approval cannot be re-enabled as a rollback. |

Run only affected suites plus the justified regression set after executable changes. No new CI/hosted test claim arises from this diagnostic commit. Independent QA must run the fixed candidate, not accept it from this proposal or successful reproduction assertions.

## Resume

The requested owner decision is only the contract extension/old-client creation cutoff above. After approval, implement and test locally on a child branch; do not re-run the completed baseline controls unless their inputs change. Hosted matching, authorized HTTP identities, browser evidence and QA remain distinct gates. PHASE2 NO-GO.
