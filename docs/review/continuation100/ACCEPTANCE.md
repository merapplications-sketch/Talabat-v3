# Batch 100 — recovery and security acceptance

Base `f7244a94dfd74a3c2aca6cbc087849482511f6cc`. No production mutation, live SQL, account/MFA changes, protected order access or settlement.
Original 144-file export remains unchanged. Unrecovered local reference `945623e50b9ed3d120897b90aa661890e394dfd6` is still not available.

## New source recovery

The historical engineering handoff identified exact commit `b4016fb64b03138830df54f2377d81455fb170a4` for continuation56. Its objects were accessible in the existing historical checkout. This new pointer allowed exact retrieval without repeating an unfocused source search.

Recovered byte-for-byte:
- `functions/qa-proof-cache56/index.ts` SHA256 `b28ade14b1b3f092ca48eccf6bbf3c85aa7e560a080987fca9ea0bb9c1d14b59`
- `.openai/hosting.json` SHA256 `232b96b3f4e9f2cdc21802c0aadaa50c4e50a5b344158570b3e66dbf0adca4f8`

Public copies are under `tests/fixtures100/`, never a deployable function directory. CI copies them into an isolated export only. Hosting configuration is historical test input, NOT established current deployment configuration. Proposal expired on 2026-11-08 and is not deployed or extended.
Original fixture-cache56 assertions run unchanged and pass with their historical mocked clock. No Storage behavior at the provider is proven.
The live isolated project's Edge Function read returned Function not found, consistent with the historical handoff saying the proposal was never deployed. No attempt to deploy it was made.

## Build gate and acceptance

Original build-gate was executed after recovering hosting config. It FAILS its expected customer-handler assertion because the build reaches the missing private evidence check first. Do not label this original test PASS.
Original build fails at `db-evidence-binding` / missing `security/db/tested-evidence.json`.
A new behavioral negative control proves that missing private evidence blocks the original build and removes stale output and build receipt. No assertions or production gates were bypassed.

The acceptance evaluator rejects missing, failed, skipped, mocked, stale-commit or unreferenced mandatory evidence. Even complete input yields REQUIRES_INDEPENDENT_REVIEW, never READY. It validates records, not their authenticity; it is an additional QA tool, NOT a replacement for the original build gate, signed evidence or GitHub branch protection. Its tests passing do not mean the mandatory gates passed. Current acceptance report is BLOCKED.
Mandatory categories: public CI, private DB evidence, hosted user RBAC, integrated role E2E, Storage revocation, provider recovery, actual Safari device, independent SQL QA.

## Real integration and private channels

Isolated project has no development branches; no dedicated empty branch or authorized user-session configuration was available. Creating a real backend would require schema deployment and account/session provisioning outside this task's no-live-SQL/no-account-change boundary. Administrative access is not user RBAC.
HTTP99 is retained. No new passwords, MFA codes, replacement sessions or admin impersonation. Hosted HTTP and full E2E remain unexecuted. No private CI target with established access controls and evidence delivery was supplied; protected evidence remains excluded from public artifacts.

## SQL 92/96/98 QA package

Pinned SQL hashes and reviewed lock order are in continuation99/QA-HANDOFF.md. New integrity tests bind the three exact files to these hashes. This is byte integrity, not live schema equivalence.
Preconditions for independent QA BEFORE any application:
1. Confirm isolated target and reserved synthetic actor/store/order IDs; prohibit protected IDs and global dispatch.
2. Capture current function definitions, owners, security mode, search_path, EXECUTE grants, table/column grants, RLS, indexes and all dependent triggers. Hash the snapshot and preserve it privately.
3. Match `orders_client_key_uq` on (customer_id,client_key) with non-null predicate; verify account/session guards, wallet/cash/approval triggers and callable signatures. Reject drift instead of substituting assumed definitions.
4. Validate that candidate is cumulative 98, preserving 92 unique-violation behavior and 96 advisory serialization. 92 or 96 alone does not contain 98 admission ordering.
5. Review group-row -> advisory caller/key -> profile-row locks against every related caller. Existing tests do not prove global deadlock freedom, especially group/promo/loyalty paths.
6. Run current native suite plus ordinary/new key, replay, different account, open/hour boundary, failed transaction and TCP before/after COMMIT acceptance. Original SQL suites provide additional captured-trigger evidence.
Rollback plan (not executed or authorized live): stop synthetic test ingress; resolve in-flight request outcomes by key; restore exact pre-change function/grants in an approved transaction; verify hashes, grants and invariants. Do not delete orders, reverse real wallets or reset sequences. Reverting to a version with the known race is not acceptance; keep release blocked and prefer a forward repair. No runnable live migration is provided as implicitly approved.

## Storage and provider ticket

Historical handoff records SU-543851 as an email support thread, with no independent tracking URL. The newly located record contains historical failure and no fix response. No inbox access or newer provider response was available. No support message sent.
Historical rejection of privileged fixture deployment is preserved; recovery for local testing does not authorize deployment.
`assessStorage` validates supplied GET/HEAD/RANGE records for warmed same URL and same token fingerprint, independently established revocation, denied bytes and control/outsider results. It rejects cached 200/206/304 and changed URL/token. Synthetic tests exercise this evaluator only; providerFixProven remains false.
Operator must additionally retain raw headers/timestamps securely, test valid and unsatisfiable ranges, legacy and future objects, and repeat after normal CDN cache lifetime. A purge, new URL or no-store header alone cannot close S54-STORAGE-CACHE-01.

## Recovery and actual iPhone Safari preparation

Existing native CI performs pg_dump and restores into a separate synthetic database, then checks relations, uniqueness/replay and rollback. It is not a hosted backup or object-storage restore drill.
Actual device run sheet (prepared, not executed): record iPhone model, iOS/Safari version, pinned preview commit, test actor and timestamps; verify login/logout, own-role denial, first-cash consent, merchant/driver transitions, receipt, background/resume, network-off then retry, camera upload and cleanup. Capture token-free results and distinguish actual device from Chromium viewport/WebKit simulation. No physical device connected in this task. Do not replay completed account-deletion/MFA tests.

## External action per blocker

- Private DB gate: provide original attestations in a private runner/workspace with approved retention/access; never public artifacts.
- Hosted RBAC/E2E: provide approved private user-session transport and quarantined fixture manifest. Approve any necessary backend provisioning separately.
- SQL acceptance: independent reviewer compares target catalog and signs pinned cumulative candidate; owner authorizes any later live application.
- Storage: provide actual reply in SU-543851 thread and authorized same-URL revocation measurements; no purge-only closure.
- Recovery: provide isolated provider restore target and storage inventory for rehearsal.
- Safari: owner/tester runs device sheet against pinned preview with authorized test accounts.
- Source completeness: recover original security branch/bundle when a new source is available; no completeness claim from export.

CI100 passing certifies its public tests only. Production acceptance remains BLOCKED.

## Coverage delta matrix

| Group | Source | Local result | Remote job | Acceptance |
|---|---|---|---|---|
| fixture-cache56 | exact historical source recovered | PASS original test | CI100 | mock only, no deployment |
| build-gate | original test + recovered historic manifest | FAIL (private-evidence blocker) | not counted PASS | BLOCKED |
| missing-private-evidence negative control | new behavioral test of original build | PASS | CI100 | proves fail-closed build, not release acceptance |
| acceptance validator | new | PASS | CI100 | record checks, no evidence authentication |
| Storage observation validator | new | PASS synthetic records | CI100 | provider untested |
| SQL/source fingerprint checks | new, pinned inputs | PASS | CI100 | not live SQL equivalence |
| headers/CSP, sessions52, driver permissions, SQL92, HTTP99 | unchanged | regression | CI99 | original scope retained |
| 18 SQL + 38 fast + HTTP98 + SQL98 | unchanged | regression | sql97 | captured/local scope |
| native contention/TCP/admission/restore | unchanged | remote regression | native95 | real PostgreSQL, synthetic data |
| hosted HTTP/full E2E/private evidence/Safari/provider restore | unavailable dependencies | BLOCKED | not run | never READY |

CI99's per-stage report still describes its own original export limitations; CI100 supersedes the aggregate fixture-cache56 recovery status. No failed original build-gate result is hidden by the new negative control.
