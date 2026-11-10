# Batch 101 — access resolution and independent QA handoff

Status: PARTIALLY COMPLETED / BLOCKED — NOT READY.
Source and test baseline: b740a3ac0227eabcfc3d5b12c8f321a499eed921.
This batch adds documentation only. No application, SQL, test, fixture or workflow changes. No repeat search for 945623e50b9ed3d120897b90aa661890e394dfd6. The 144-file recovery is still partial historical recovery, not a complete deployed-source attestation.

## Newly verified access
- GitHub review head remains the baseline above. Public Actions reads work. Installed-repository search for user:merapplications-sketch is:private tal returned zero results; this is scoped visibility, NOT proof no private repository exists.
- Branch listing reports protected:false for review/ci-native95-20261110 and main. Repository GET /rulesets returned []. Mandatory-check enforcement is NOT established at GitHub level. No branch protection or repository settings changed.
- Supabase administrative list_projects works. The previously identified isolated pilot remains ACTIVE_HEALTHY; production also exists and was not queried. A project name/healthy status does not prove fixture quarantine or identity permissions.
- TALABOT_HTTP99_CONFIG is absent in this runtime. No approved user-session input was available. No authentication bypass, token generation or service-role substitution attempted.
- Cloudflare whoami and account listing succeeded. Listing Worker scripts returned an authentication-retry request twice (initial attempt plus one retry), without script inventory. Account visibility does not establish Workers access or a testing environment. Stopped retrying.
- No connected support inbox or actual iPhone channel was established. No new provider response was obtained. No messages sent.

## Preserved CI evidence
All four runs were read again and are completed/success at baseline SHA:
- CI100: https://github.com/merapplications-sketch/Talabat-v3/actions/runs/42770057594
- CI99: https://github.com/merapplications-sketch/Talabat-v3/actions/runs/42770057598
- Native PostgreSQL: https://github.com/merapplications-sketch/Talabat-v3/actions/runs/42770057901
- SQL97 public: https://github.com/merapplications-sketch/Talabat-v3/actions/runs/42770057966

These are previous executions, not new batch101 tests. No code/configuration changes warrant repeating successful regression. The documentation commit does not acquire a new tested-SHA claim by inheritance. Coverage and limitations remain in ../continuation100/ACCEPTANCE.md.

## Private evidence operating contract — prepared, not provisioned
Required: an owner-designated private repository/runner or encrypted workspace, authorized custodian and reviewers, approved retention/deletion, and original historical evidence. Merely finding a private repository would not authorize its use.
Use a clean pinned source checkout on that private runner. Mount original security/db evidence read-only. Run the unchanged tests/db-regression-evidence.cjs and original build only inside that boundary. Keep stdout/stderr, build outputs, manifests and any failures private; do not attach them to public Actions. Public reporting may contain only a reviewed outcome, source SHA and opaque private review reference.
Reject missing files, mismatched digests, unknown provenance, failed checks or incomplete review. Do not regenerate historical records from synthetic fixtures. Authoritative migration filenames and SHA256 entries must come from the original tested-evidence.json; they cannot be inferred from this export.
Known required records from the original test: tested-evidence.json, cash-after.json, price-after.json, cash-rollback.json, return-replay-regression.json, return-cleanup.json, approval-replay-after.json, merchant-role-after.json, return-role-after.json; migration dependencies include pilot_return_action_account_guard.sql, pilot_approval_account_guard.sql and latest_rpc_migrations references. This is a minimum inventory, not a fabricated replacement attestation.
The original build-gate still cannot demonstrate its customer-handler assertion because missing private DB evidence fails earlier. The batch100 negative control already proves fail-closed build behavior; its success does not mean build-gate passed.
The acceptance100 record checker is not a signature verifier or a merge gate. External owner/admin action is needed to enforce required public and private acceptance checks on the intended release path. No READY based only on public CI.

## Independent SQL QA review sheet
Candidate is cumulative tests/native98/place_order.fixed.sql, preserving fixes92/96. Do not apply three replacement functions in arbitrary order. Exact binding:
- 92: d150ecfcfad5db659d4150ea29bb5ad196d11c8ff8a1289b4b7c8ad082f5d6dd
- 96: 938448863e8208c605174642bd0ad8f5eba59531d2e293df43e9f70c9bb00021
- 98: 9195c50736beda188008053e671a0288093edee78497cf459d974a79c370ac29

Independent reviewer must record name/identity, candidate SHA, private catalog snapshot digest, execution references, deviations and signed accept/reject. No reviewer sign-off has been obtained or implied by this preparation.

Review obligations:
1. Verify group-row -> per-user/key advisory -> profile-row lock order against all related entry points, including promo/group/loyalty and triggers. Existing targeted concurrency tests are not global deadlock proof.
2. Confirm existing-key replay precedes admission checks; profile lock precedes open5/hour20 counts; unrelated unique_violation does not become null-success.
3. Exercise same and different keys per account, distinct accounts, threshold crossings, rollback and lost TCP before/after commit. Require one order and one financial effect; resolve uncertain writes by idempotency key before retry.
4. Compare function signatures/owners/search_path/SECURITY DEFINER, EXECUTE grants, table/column privileges, RLS enable/force flags and policies, all dependent triggers, and partial unique index orders_client_key_uq(customer_id,client_key) WHERE client_key IS NOT NULL against the approved target snapshot.
5. Retain original pre-change definitions/grants privately. Rollback only in separately approved target: stop synthetic ingress, resolve in-flight outcomes, restore exact definitions transactionally, verify definitions and invariants. No protected rows or real balances modified. A rollback to the known race is not release acceptance.
Detailed preconditions and existing test coverage remain in continuation99 and continuation100. No live catalog equivalence or independent acceptance is claimed.

## Integration and recovery execution boundaries
HTTP99 remains the runner. Before writes, require owner-approved private configuration, finance/orders/outsider user identities with verified UUID/expiry/roles, pinned isolated origin, quarantined synthetic fixtures, known before-state and cleanup ownership. No protected IDs, unbounded audit data or production endpoints. A receipt ID >3 alone is not proof of synthetic authorization.
Verify identity first, then bounded GET, denial PATCH with before/after equality, allowed PATCH with re-read, role-scoped RPC/receipt and cleanup re-read. Lost response means unknown outcome: read persisted state before any mutation retry. Existing loopback HTTP tests are synthetic-server tests, not Supabase RLS proof.

Four-app E2E acceptance must link one synthetic correlation/idempotency key across customer creation, restaurant acceptance/preparation, driver assignment/pickup/delivery and admin receipt/settlement. Separate fixtures cover cancellation/refund/open claim. Reserve all identities and financial rows beforehand, prevent live dispatch/payment, retain safe before/after invariants, and independently confirm cleanup. Existing plans do not prove this journey executed.

Recovery acceptance requires a distinct provider target, approved backup and object inventory, restored object digests/metadata and authorization checks, restore duration and reconciliation. Existing native PostgreSQL synthetic restore is retained but cannot substitute for provider/object recovery.
Safari acceptance requires actual iPhone Safari evidence on a pinned preview, authorized test roles and the existing device run sheet. Desktop/viewport simulation is not device evidence.

Storage stays OPEN: require new evidence from SU-543851's original support thread plus authorized same-URL AND same-token GET/HEAD/Range after independently verified revocation. Capture private headers/times/bytes and valid/outsider controls; cached success, changed URL/token or purge alone fails acceptance. No Storage changes made.

## Dependency closure matrix
| Blocker | Exact external action and approval | Existing route / safe work without it | Closure evidence |
|---|---|---|---|
| Private DB/build-gate | Owner designates private runner, custodian and original evidence transfer | GitHub public source readable; no approved private target identified; contract prepared | Original binding + original build-gate PASS privately, provenance and review reference |
| GitHub acceptance enforcement | Owner/admin approves and configures required checks/release rules; no main change authorized here | Read access shows no protection/rulesets; fail-closed build retained | Controlled rejected acceptance for absent/failed mandatory evidence; admin-reviewed rules |
| Hosted HTTP/RBAC | Owner provides approved secure user-session transport and synthetic fixture scope; separate approval for any provisioning | Supabase admin metadata available; HTTP99 ready; admin auth insufficient | Real bounded identity/GET/PATCH/RPC evidence, denial invariants and cleanup |
| Four-app E2E | Test operator supplies quarantined actors/store/driver/orders and scoped approved environment | Existing journey plan retained, no protected data touched | End-to-end persisted transitions, idempotency and synthetic receipt/settlement reconciliation |
| SQL QA | Independent reviewer obtains approved target catalog snapshot and signs cumulative candidate; live apply later needs owner approval | Pinned source/native evidence available, QA sheet prepared | Reviewer decision with catalog hashes and actual isolated acceptance runs |
| Cloudflare environment inventory | Restore connector Workers-read authorization if this environment is needed | Identity/accounts work, scripts enumeration unresolved | Successful metadata inventory mapping exact test deployment and source SHA |
| Storage | Custodian supplies new provider reply and scoped revocation test authorization | No new inbox route; acceptance matrix retained | Same URL/token GET/HEAD/Range denied after revocation with controls |
| Provider recovery | Owner designates isolated restore target and grants scoped restore access | Native synthetic restore evidence retained | Backup/object restored digests, permissions, reconciliation and recovery timings |
| Actual Safari | Owner/tester provides physical device session and scoped test accounts | Run sheet available | Real iPhone Safari evidence tied to preview SHA |

## Resume
Do not re-search the missing Git reference or rerun green public suites without changed inputs. Start at the first newly supplied dependency above. Validate scope before writes. This batch is administratively closed with external blockers; it does not declare production ready. No main merge, deployment, live SQL, account/MFA changes, protected-order operations or settlement occurred.
