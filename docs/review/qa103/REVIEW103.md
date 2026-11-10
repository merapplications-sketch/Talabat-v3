# TALABOT — independent REVIEW103

Date: 2026-11-10 (Asia/Dushanbe).
Scope: independent source/evidence checks and new gap probes against the pinned candidate. This is not third-party certification. No candidate repair, live SQL, deployment, main/protection change, protected orders/accounts/MFA or settlement changes.

**Final SQL103: REJECTED as a complete migration/rollback candidate (QA103-S01). Client candidate: REJECTED (C01/C02); target/production acceptance: BLOCKED / NOT READY.** Limited historical recovery and HMAC algorithm checks pass; this does not accept all environments.

## Provenance
- Candidate: `bb7b9e585a9995be7d5154baf6bc256377e0f86f`.
- Programmer evidence: `651696a3fdc51d393bcddef3effd71d6b9634845`.
- Independently fetched remote Git tree and matched Git blob IDs of all16 files; matched all16 SHA256 values. Evidence commit changes only5 documentation/evidence files after candidate.
- Independently read original CI jobs129720760396 and129720760919 at run42784056173. Native19 cases, admission4, restore and client15 pass. This is reviewed programmer CI evidence, not new independent execution of those cases.
- Independent native probe commit: `4cb516cc8d1a2ffa2bc8274ceaef3196404fc4a1` on `review/qa103-independent-20261110`. All16 candidate hashes verified again in workflow before execution.
- Independent native run: https://github.com/merapplications-sketch/Talabat-v3/actions/runs/42808981791 — FAILURE, intentionally retained because the rollback acceptance assertion fails. Four other independent cases pass. PostgreSQL17.6 is a real server with a partial synthetic fixture, not Supabase HTTP.
- Independent JS results: three reproductions using separate controller instances sharing storage and actual generated customer place() body. Latest C02 composes actual controller with actual generated function; RPC/readOrder are synthetic. No real browser/Safari claim.
- Initial independent run42808849338 had two harness setup errors: consecutive synthetic cash orders had not been acknowledged. The harness now marks only its own synthetic approvals accepted between seeded orders; product assertions/functions were unchanged. S01 reproduced in both runs. This setup error is not a product defect.
- Original native103 tests and assertions were not edited. Three captured dependency bodies (promo_eval, loyalty_balance, loyalty_spend) exactly match REVIEW102's private snapshot and their recorded hashes.

## Independent findings and reproduction

### QA103-S01 — rollback fingerprint depends on caller float serialization (medium, acceptance blocker)
Location: `tests/native103/rollback.sql:3-4`; compare `functions.sql:7` (`extra_float_digits=3`).
1. In a disposable PostgreSQL database install unchanged103 and ephemeral key.
2. Set session `extra_float_digits=0`; create order with typed float8 coordinates38.123456789012344 /68.12345678901234.
3. Replay identical parameters before rollback: replayed.
4. Apply supplied rollback.sql inside test DB, keep the same caller setting and parameters.
5. Replay: conflict/idempotency_mismatch, although inputs have not changed.
Cause: rollback constructs JSON before the resolver without the fixed float context used by create_order103. Numeric scale trimming cannot restore discarded precision. This is a false conflict/availability defect, not an observed duplicate debit or account leak. Status-only retrieval still has its own read path; it does not repair verified replay.
Required programmer action: one versioned typed-input canonicalization boundary used by creation, all verified recovery/unique paths, conversion and rollback; test caller float settings and high-precision coordinates without redefining existing v1 MACs.

### QA103-C01 — late success removes another active attempt (high)
Location: `tests/native103/client.js:40` unconditional removeItem(activeSlot).
1. Tab A sends K1; hold its success response after server completion.
2. Tab B recovers K1 and verifies its saved order; starts K2, still pending.
3. Deliver A's old K1 response. Its completion clears the account active pointer, which now refers to K2.
4. Tab C submits K3. Reproduction observes1 place_order103 RPC while K2 remains unresolved.
No server financial duplication is claimed by this mocked transport test; the client prohibition on a different key before reconciliation is demonstrably broken. Server per-key idempotency does not reject different keys by itself.
Required action: ownership/generation-aware cross-tab coordination, conditional completion and atomic arbitration. A bare get/remove check is not a comprehensive simultaneous-tab fix. Reproduce delayed responses and initial simultaneous submissions.

### QA103-C02 — success erases cart edited in flight (high for data preservation)
Location: `client.js:38` compares submit argument to its stored copy; `build-client.py` generated place() unconditionally clears current S.cart on keepCart=false.
1. Run generated customer place(), backed by the actual candidate controller; defer create RPC result.
2. Change live S.cart during the wait.
3. Return verified created response and successful saved-order re-read.
4. Observed live cart becomes{} instead of retaining the edit.
This is a VM state test, not proof of a Safari interaction. Source cart mutation helpers add/delLine/clearCart also lack an S.busy guard, so no global immutability guarantee was found. The controller only knows the original payload, not live cart revision.
Required action: capture and compare live cart/context revision before clearing; preserve changed cart and related gift/time/notes fields. Test through actual UI/controller integration and real browser.

### QA103-C03 — rejected/unresolved attempt has no complete lifecycle (known open gap, independently reproduced)
After a definite address_required rejection, submitting corrected data with same key only queries status; another key is blocked by active pointer; retrySaved uses original invalid payload. Exposed API has no reconciliation-aware end/edit/cancel operation. Data is retained and automatic new creation is prevented, but the user can remain stuck. Programmer handoff already acknowledged this gap; it is not a newly discovered hidden defect.
Owner decides cancellation/abandonment and retention policy. Programmer implements distinguishable confirmed rejection vs uncertain outcome and tests recovery/reload/multiple sessions. Never simply delete the key to bypass uncertainty.

## Scope judgments
| Area | Judgment | Basis / limit |
|---|---|---|
| Historical own-key recovery | ACCEPTED in isolated tested scope | New independent READ ONLY transaction recovers ordinary/group/scheduled98 orders after103, input_match=null;3 orders/3 spends/0 fingerprints unchanged; other account sees no ID. Current auth and original group authorization inspected. |
| New bound replay, NULL/{} and array ordering | ACCEPTED in original tested scope | Original tests/logs inspected; typed conservative12-field contract includes identity/key/domain; no arbitrary normalization claimed. |
| HMAC algorithm / Unicode | ACCEPTED in tested scope | Independent Python HMAC oracle matches pgcrypto for Unicode/nesting/escaping; composed/decomposed Unicode remains distinct as contract states. Does not certify every Unicode/numeric input. |
| Key rotation / loss | CONDITIONAL; operational approval BLOCKED | Original rotation tests verify old key IDs. Independent missing-secret fault returns unresolved for verified replay, no mutation; status-only returns replayed,input_match=null (not HMAC proof). Normal FK blocks in-use deletion; fault injection removed FK in disposable DB only. |
| Complete canonicalization across rollback | REJECTED | S01 demonstrates environment-dependent replay. |
| Atomicity / sampled concurrency | ACCEPTED only for covered paths | Original native TCP/admission/binding/promo/loyalty/wallet assertions inspected; new mid-conversion failure rolls back both converted records and markers. No universal deadlock-freedom claim. |
| Migration and rollback package | REJECTED pending S01; target deployment BLOCKED | Recovery-only rollback policy is appropriate, but execution changes fingerprint serialization. Mixed arbitrary writers not supported; must drain ingress. |
| Client / multiple tabs | REJECTED | C01/C02; C03 lifecycle incomplete. No hosted or Safari acceptance. |
| Target schema / production | BLOCKED | Snapshot comparison incomplete; no current full isolated-target parity, private build gate, hosted identities or release approval. |

## HMAC and privacy details
The server covers12 typed arguments: store/items/tip/payment/address/lat/lng/promo/fee/wallet/points/extra, plus domain/version/customer/key. Arrays remain ordered; object keys use C collation; numbers trim decimal scale; only top-level extra null/{} collapse. Structured JSON boundaries prevent field-concatenation ambiguity. Whitespace/case and Unicode composition remain significant by design. Key length>=32 random bytes, immutable key IDs/material, one active key, stored key_id per binding; no raw address/pin/recipient in fingerprint rows. No production secrets found in reviewed new source or reviewed log output; this is a scoped inspection, not proof of all platform logging settings. Workflow uploads only synthetic JSON evidence, not secret-bearing database dumps. Database owner/backups remain trusted; no external KMS/HSM, expiry, constant-time comparison guarantee or full side-channel assessment is established. Local unresolved payload contains personal input and lacks an approved expiry/abandonment lifecycle.

## Transactions, locks and target fidelity
Observed103 order: original group lock -> account/key advisory -> profile -> promo advisory -> loyalty lots (expiry,id) -> remaining effects/binding. Original native tests cover40P01/55P03 and TCP loss without automatic re-send. Captured other operations include ticket->order, finance request/driver locks and profile locks, and driver/profile/group updates. Full transitive trigger lock graph is not reproduced; artificial opposing lock tests do not prove a real target deadlock nor exclude one.

REVIEW102 private snapshot had10 policies/17 triggers across five tables versus fixture0/1.103 adds its own marker/key triggers, not the missing target closure. Identity for orders/wallet, UUID/default for order_items and7 FK additions/replacements were checked in source; selected102 NOT NULL/default checks remain. Missing columns remain orders18/profiles13/wallet4/group1; target enums order_status/user_role remain text in fixture. group_orders.id default gen_random_uuid remains absent in fixture. Missing driver/ticket/auth.users FKs, exact grants/default grants/inherited roles, RLS policies and transitive triggers are not closed. No target schema was changed. Captured promo/loyalty bodies are genuine, but minimal tables/loyalty settings and delivery/happy-hour dependencies remain synthetic. This catalog is the retained REVIEW102 snapshot, not a fresh live export.

## Before any live transition
Independent acceptance of repaired candidate, owner operational approval, authorized isolated target parity and roles, safe secret provisioning/rotation/backup/retention, drained old writers and a durable reconciliation inventory, reviewed transactional conversion of only actual102 records, validated recovery-only rollback, and restore proof on approved provider are required. Do not reconstruct historical inputs from normalized order rows. Old uncontrolled writers cannot honor new fingerprint contracts.

## Programmer and owner handoff
Programmer: fix S01/C01/C02, implement approved C03 lifecycle, add focused regression tests; retain historical/atomicity/auth protections and existing bindings. Do not change approved design without preview/approval. Re-review source delta plus critical103 regressions, not every historical green group.
Owner/access: approve unresolved/rejected lifecycle and local-data retention; provision isolated hosted finance/orders/outsider channel, private DB/build-gate evidence, complete catalog/role/trigger export, secret-management and provider recovery path. Storage SU-543851/sameURL+sameToken GET/HEAD/Range and actual Safari remain open; no new access/evidence was available and old diagnosis was not repeated.

Resume: next repair batch against pinned bb7b9e5, with this independent probe commit and explicit findings; then REVIEW104/reassessment. No operational approval is granted by this report.
