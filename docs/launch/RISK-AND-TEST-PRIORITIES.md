# TALABOT — Current Feature Risks & Minimum Tests

Status: **candidate QA priorities**. Test in authorized offline/synthetic environment only. These are source-identified risks or verification gaps, **not proven production failures**. Preserve approved financial policies. Avoid retesting historic 106/107 cases unless affected by source/env drift.

| Order | ID | Risk | Synthetic test | Mandatory pass outcome | Evidence state |
|---|---|---|---|---|---|
| 1 | PILOT-R01 | Cross-account/role data leakage (RLS/RBAC) | Two synthetic customers and distinct driver/merchant identities; request each other's addresses, chats, orders, wallets, objects | Every unauthorized request rejected, no cross-tenant data | G1-D BLOCKED |
| 2 | PILOT-R02 | Duplicate checkout on double tap / post-commit retry | Same idempotency key twice with timeout after commit | One order and one financial side effect | Not current-SHA E2E passed |
| 3 | PILOT-R03 | Duplicate delivery confirmation | Rapid repeated confirmation, timeout/retry and concurrent call | One final delivery and one ledger effect | F-02 source risk P1 |
| 4 | PILOT-R04 | Under-collection vs CASH-01/Q14 | Cash less/equal/more than due; driver failure/network split | Match previously approved rule, exact reconciliation and no hidden under-collection | F-04 source risk P1 |
| 5 | PILOT-R05 | Driver shows Online before server ACK | Deny/timeout initial ping; reconnect then reload | UI does not claim server Online before ACK | F-01 source risk P1 |
| 6 | PILOT-R06 | Driver message draft lost on failure | Reject chat insert, disconnect network and retry | Text remains until successful acknowledgement, no duplicate message | F-03 source risk P2 |
| 7 | PILOT-R07 | Incorrect price/discount/fees/loyalty rounding | Tampered client price, simultaneous promo+HH+points, tax/fee and partial service failure | Server-calculated total consistent with approved PRICE/TIP contracts | Independent current-SHA proof missing |
| 8 | PILOT-R08 | Refund/returns/settlement misuse | Partial refund, return refused, payment proof missing, retry and concurrent approval | Claims stay open until actual funds confirmed, ledger never duplicated | RETURN-01 approved; E2E incomplete |
| 9 | PILOT-R09 | Delivery/GPS/proof / privacy | Outdated GPS, denied permission, wrong recipient, invalid photo/TTL, customer cross-order request | No wrong delivery closure, no leaked location or proof | Data path present; current E2E missing |
| 10 | PILOT-R10 | Merchant/order workflow | Scheduled order, late merchant acceptance, replacement approval, stop-list and driver acceptance race | Consistent state and amount; no cancellation/refund contradictions | Source present; runtime missing |
| 11 | PILOT-R11 | Offline and recovery | App killed after server commit, reconnect across roles and stale cache | Reconcile from server; no duplicate fulfillment | Current E2E incomplete |
| 12 | PILOT-R12 | Release parity/rollback | Compare exact customer/driver/merchant/admin/core, RPC/SQL, CI, storage, restore receipts | Exact deployed provenance, safe rollback and effective recovery | G1-A/F PARTIAL |
| 13 | PILOT-R13 | UI / physical Safari | 320/360/390/430 RU/EN (TG where actually supported); modal, focus, long content, dark/light | No clipping or blocked navigation; observed device screenshots | Not executed on exact new candidate |

**Priority rule:** No newly proposed competitor feature should displace critical R01–R12 safety and financial gates. Assign fixes to the authorized role on an isolated branch only after proof, with an independent regression and owner-authorized release boundary.

Sources: Master #26 https://github.com/merapplications-sketch/Talabat-v3/issues/26 ; Consolidated QA https://github.com/merapplications-sketch/Talabat-v3/blob/0ab523782ee1bf6f69e2e3be7ec6e96394d9ce6a/docs/qa-first-20261113/MASTER-QA-CONSOLIDATED-20261113.md ; Owner agreements https://github.com/merapplications-sketch/Talabat-v3/blob/1cb85361d698d5da787d927a4c9ae7bd213c68c1/docs/OWNER-AGREEMENTS-AR.md .
