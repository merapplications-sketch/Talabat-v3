# Cached-result authorization scope review — .30

2026-11-07. Published source attribution supplied by parent: abe3a5144894b82327a27944c4f1358959d83cf8. Read-only saved public/private function definitions plus continuation29 migrations/evidence; no SQL calls, mutations, new fixture or repeated tests. Older inventory is supplemented by four applied migrations reported by parent; whole-provider definition equivalence is not newly asserted here.

## Closed narrowly; do not repeat

Saved continuation27/29 evidence proves banned-account cached return/merchant/customer approval reads before guards and their rejection after account guards. Continuation29 current-access migrations move merchant/store/driver/customer role checks before cached return results for order_return_action and move current store authorization before cached merchant-review results. Preserve active replay successes and revoked-store-owner rejection evidence. These tests do not close every financial stage/actor combination.

## Remaining path inventory

| Path | Authorization observed | Residual coverage / candidate |
|---|---|---|
| customer_confirm_order cached result | New account_enabled precondition; stored request binds actor, operation, order and payload. Saved function returns cached result before loading current order/customer. | Conditional object-reassignment candidate: if an order customer_id can legitimately change, prior customer may still read old cached result. Need current write constraints/RLS and approved reassignment contract first. No supported ownership reassignment or live leak demonstrated; immutable customer identity could make scenario inapplicable. Result contains request/order/revision/state, not full amounts. |
| finance_execute | finance_private.accountant checked before cached command lookup; actor/operation/target/exact amount/note bound. accountant checks enabled account, active staff and finance permission. | Source supports immediate removal of finance role for replay. Need distinct runtime coverage for revoked finance permission, disabled staff, cross-actor request UUID and changed payload only where not already covered. Do not reclassify replay after transaction completion as an unauthorized new settlement. |
| finance_command_status | SQL filters request AND actor=auth.uid AND accountant(). | Wrong actor/removed permission yields no result in inspected source. Unlike execute, absence may be NULL rather than exception; callers should not infer success. Actual current helper/session guard coverage still matters. |
| order_return_action | Applied migration loads/locks order and checks current action-specific customer/driver/store-owner/orders-staff relation before prior.result. Account/session guard first. | Remaining untested cells: driver reassignment; revoked orders permission for refuse_refund; cross-actor command key; action/payload/order change; allowed replay after later stage. Stage changes should not necessarily invalidate a historical idempotent answer. Replaying must not mutate again; full stage/role tests incomplete. |
| order_return_status | account_enabled then current order relation: customer, assigned driver, owner or orders staff. | No early cache. Owner transfer/driver reassignment/staff revocation should affect reads via current relation; this is source evidence, not executed matrix. Customer receives reduced fields; other admitted actors receive payment/refund facts. Need explicit field-policy agreement and per-role runtime read assertions. |
| return_private.view_case | SQL STABLE helper, not SECURITY DEFINER in saved definition. p_customer determines reduced versus full fields. No own auth predicate. | Critical dependency is helper EXECUTE/schema/table grants and callers. Public status/action choose customer flag internally; untrusted direct caller must not obtain financial fields by passing false. Check actual grants before describing helper as exposed. No direct caller reachability was proved. |

## Exact ASVS mapping

- V8.2.1: current function permission before returning cached results.
- V8.2.2: current actor-to-order/store relation, including after reassignment.
- V8.2.3: reduced customer return fields versus privileged financial fields.
- V8.3.1: checks at SQL service boundary, not frontend visibility.
- V8.3.2: immediate effect of account/role/ownership revocation; previously proved cells retained.
- V2.3.1/V2.3.2/V2.3.3: stage, limit and atomicity semantics remain separate from read permission; idempotent cached historical result is not itself a stage bypass or new monetary effect.

## Prioritized next checks (only uncovered cases)

1. Read current helper ACLs/schema usage/table grants for return_private.view_case and confirmation/finance private tables. No mutation required. Verify callers cannot supply their own customer=false outside authorized wrappers.
2. Determine whether current customer_id reassignment is possible by any supported authorized path. If impossible and documented, record the cached customer relation candidate as non-reachable under current invariant, not a patched vulnerability. If possible, add current relation check before replay and run a bounded synthetic regression.
3. Review existing finance removal evidence before new tests; test only absent cached execute/status cells, preserving allowed replay and same-key exact response semantics.
4. Cover return action driver/orders-staff revocation and public status field reads with approved isolated synthetic rollback tests. No protected orders; no permanent finance fixture to circumvent prior restrictions.
5. Test stage authorization separately rather than conflating replay authorization with permission to create a new financial action. Keep actual multi-session concurrency open until permitted evidence exists.

## Outcome

No NEW demonstrated cached-result exploit from this saved-file review. Customer reassignment and helper ACL exposure are precise conditional candidates requiring evidence, not confirmed failures. The four fixes do not warrant blanket closure of V8, session revocation, all financial roles/stages or independent acceptance. No account/password/order/receipt/production changes were made.

## Update: private helper exposure bounded closed

Parent obtained current metadata: anon/authenticated schema USAGE=false; authenticated function EXECUTE=false and cases SELECT=false. `continuation30/private-helper-result.json` records actual authenticated direct invocation rejected with `permission denied for schema return_private`. This closes the specific direct-helper candidate for that tested role/access path; do not repeat it. It does not close all private helper ACLs or privileged service roles. Earlier candidate/next-step language above is superseded for this bounded check.

## Return-status field contract located in saved implementation

Sources: `rpc21-inventory.json` entry order_return_status(bigint), `continuation21/private-guards.json` entry return_private.view_case(bigint,boolean), and applied continuation29 return-action migration. Existing replay tests exercise cached markers and action access, not a complete field-projection matrix. Targeted review of available acceptance reports did **not** locate a separately signed/approved field-by-field policy. Therefore the following is the exact existing implementation contract to preserve and test, not a newly assumed owner agreement.

When a return case exists:

| Caller admitted by order_return_status | Expected top-level allowed keys | Restricted keys |
|---|---|---|
| Current order customer | departed_at, cancelled_at, received_at, order_status, can_document_departure | paid, currency, refused_at, confirmed_refund, open_claim, delivery_due, pending |
| Current assigned driver, current store owner, or current orders-permission staff, **unless also the order customer** | departed_at, cancelled_at, received_at, paid, currency, refused_at, confirmed_refund, open_claim, delivery_due, pending, order_status, can_document_departure | Raw case identifiers/actors/payment_ref/receipt_ref/refusal_ref/agreement ID are not selected by view_case |
| Unrelated, former owner, former assigned driver without another admitted relation, removed orders staff without another admitted relation | No successful result | All above |

`pending`, when populated, has only `ref`, `amount`, `method`. `can_document_departure` is true only for the current assigned driver, pickedup cash order, and the latest pre-order return agreement active. Customer equality controls projection even if that identity has another admitted role. No case means view_case NULL coalesces to `{}`, so public status has only `order_status` and `can_document_departure`; absence of timestamp/financial keys is expected then.

For action responses, view_case is called with `p_action='cancel'`, so customer cancellation receives only departed_at/cancelled_at/received_at; non-cancel action results include the financial projection. `order_status` and `can_document_departure` are public status-wrapper additions, not view_case fields. Cached replies preserve the historical projection/result; compare expected keys separately from freshness.

This inventory supports narrowly scoped V8.2.3 tests without inventing a business-policy change. If the field policy requires separate documentary approval, keep that documentation item incomplete; do not block tests of the existing restricted customer projection.

## Runtime updates after inventory
finance-replay-access.sql/result: active same actor returns marker through status+execute; second finance actor status=NULL/execute=request_conflict; inactive or removed finance permission status=NULL/execute=not_allowed. Eight assertions passed; rollback cleanup zero. These cached-result access cells are closed narrowly; no new money execution or true concurrency proof.
return-staff-permissions.sql covers current orders staff versus inactive/permission removed; return-driver-fields.sql covers customer restricted fields, driver fields, outsider denial and existing assignment guard. Customer direct reassignment denied by table grants; limited source search found no supported path. Preserve evidence; do not repeat these cells.
