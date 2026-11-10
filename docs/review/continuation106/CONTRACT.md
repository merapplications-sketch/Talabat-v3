# BATCH106 — closed-key isolation contract

Base source105:3893352541f8a2a94ed87ee11863519e69ad45fb; evidence105:11c6b96366536103d3a4f009a3b988e17020cf76. The owner supplied REVIEW105 finding QA105-S03 and its reproduction sequence. Changes are on a separate review/batch106-20261110 branch;105 remains intact.

## Cause and chosen repair
The105 creation helper checks closure rows using the transaction's MVCC snapshot. Taking the account/key advisory lock does not advance a REPEATABLE READ snapshot. A transaction with an older snapshot can miss a committed closure and create the first order for that key (no order uniqueness conflict exists yet). The105 quota epoch protects closure insertion, not creation's read of a closure, so it cannot prevent this bypass.

Unchanged105 was reproduced on real PostgreSQL17.6: A fixed an RR snapshot; B committed a terminal receipt for K; A then called place_order104(K) and committed an order, one wallet spend(-5 synthetic units), and one fingerprint while the closure remained present. See baseline CI42828844940 and baseline.py; no live data was used.

106 chooses the expressly permitted unsupported-isolation refusal, not a claim of fresh MVCC under an advisory lock. One guard is added in security_private.create_order103 after current identity/account/key checks and before fingerprint building, resource lookups, locks or order/financial writes. The rest of the104 helper body is byte-for-byte unchanged, including HMACv1 and order rules. Existing ACLs are retained.

| Creation transaction isolation | Contract |
|---|---|
| READ COMMITTED | Supported; existing keyed lock and closure reread apply |
| READ UNCOMMITTED | Supported with PostgreSQL statement-snapshot behavior; included in the matrix |
| REPEATABLE READ | Refused before creation effects; unresolved/unsupported_transaction_isolation |
| SERIALIZABLE | Refused before creation effects; unresolved/unsupported_transaction_isolation |

This also refuses creation-endpoint replay under unsupported isolation. Read-only status endpoints remain available, but an old snapshot can legitimately report not_visible. The caller must end that transaction and explicitly reconcile the SAME original key in a fresh supported transaction; not_visible under a stale snapshot never authorizes a replacement key. No automatic transaction reset/retry or key replacement is implemented.

## Entry points / scope
1. public.place_order104 → public.place_order103 → private helper: JSON unresolved, no closure minted for isolation refusal.
2. public.place_order103 → private helper: same JSON unresolved.
3. public.place_order → public.place_order103: legacy bigint contract raises order_outcome_unknown; no success ID and no definite-failure claim.
4. security_private.create_order103: guard also applies to trusted internal/owner calls. Not executable by authenticated/anon.

The isolated catalog test enumerates names, signatures and role EXECUTE grants, asserts these are the only place_order*/create_order* entries in this fixture, and checks authenticated has no direct orders INSERT. This is not a complete Supabase target catalog audit or proof about unlisted service-role functions, triggers, legacy writers, arbitrary owner SQL or direct trusted table writes. Obtain a read-only target catalog/function/grant diff before any rollout; drain/revoke incompatible old writers through separately approved operational changes. No target SQL was run.

## Atomicity / races / errors
The matrix tests four entries × four isolation levels with A's snapshot established before B's committed closure, and verifies unchanged order/items/financial/group/binding snapshots plus zero orders/spends. Additional RC races cover both winner orders: success first yields no false closure; closure first prevents a waiting create. New valid and invalid calls under RR/SERIALIZABLE leave no financial or closure effect. Supported replay preserves the original order and one spend.

40001 is not treated as success. A synthetic serialization_failure is injected on real PostgreSQL after real order/wallet/binding writes for each entry, followed by explicit rollback, full state comparison, original-key lookup and explicit same-key retry with one spend. This is fault injection, not proof of a naturally occurring SSI schedule. The unchanged client controller is separately tested with unsupported-isolation JSON,40001 RPC error and transport loss: original key/payload retained, new key blocked, endRejected refused and no automatic write retry.

Retained SQL regression exercises TCP loss before/afterCOMMIT on successful creation; retained resource cases exercise TCP loss for closures. Rollback/re-upgrade and isolated dump/restore preserve fingerprints, HMAC keys, closures, policy and guards. No assertion equates a SQLSTATE alone with atomic safety.

## Regression boundaries
106 changes SQL only. C03/C04, core IndexedDB ownership and generated UI are unchanged; reuse105 Chromium15/15, client15/15, cart5/5 and local38/38 evidence at pinned105. Do not rerun unrelated UI suites solely to inflate counts.

Retain26 SQL103/104 assertions with106 overlay, four admission/concurrency scenarios and ten compatible105 resource assertions. The prior105 RR quota test expected closure admission to reach an epoch conflict;106 intentionally refuses the creation API earlier. It remains unchanged in105 and is explicitly superseded by the stronger106 unsupported-isolation/no-effects matrix. It is not silently removed or relabeled passing.

## Migration / rollback / privacy
Isolated install order:103 prerequisites →104 schema/functions/lifecycle →105 resources →106 isolation.sql, in one controlled migration with writers paused/drained. No production quotas are seeded. Do not apply104/105 alone over106 and reopen writers before reinstalling the106 guard.

Recovery-only104 rollback disables public new creation while preserving keys/fingerprints/fences and106's internal guard. On re-upgrade install106 last. Trusted owner/private-helper access is not an operational API and must remain restricted; an owner can alter code or bypass grants, outside this guarantee.

No retention policy changed. Do not delete closure fences to free quota or restore an old snapshot and reopen writes without reconciling missing committed operations. Unknown local attempts retain necessary original inputs; deleting local storage is not proof of server failure. Prior retention proposals remain unapproved. No new personal data or secrets are collected.

## Open operational gates
Independent REVIEW106; target catalog and runtime isolation verification; approved closure quotas and measured rate/body/CPU/WAL controls; closure-budget scalability; private build-gate/db evidence; authorized hosted HTTP/RBAC and four-app E2E; cross-device reconciliation; actual Safari; Storage/provider recovery. PostgreSQL evidence uses a partial synthetic schema, not live Supabase. NOT READY. No liveSQL/main merge/deploy/accounts/MFA/protected orders1/2/3/settlement3 actions.

Before any future rollout, a private read-only audit should identify pre-existing order/closure key collisions from earlier candidate use.106 prevents new supported-entry creations after a committed closure; it does not erase or silently repair any historical inconsistent rows. No such inconsistency is asserted in production, and no production audit or repair was performed here.
