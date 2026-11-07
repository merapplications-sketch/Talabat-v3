Latest evidence commit a76bc38759db2858c25bf6a010248aa8f8ddfccf, Library17. Additional .30 unchanged-source tests after that commit: direct private helper denied; customer order reassignment denied by table privileges; return status customer5keys/driver12keys/outsider denied; return driver reassignment blocked by existing return_order_protected; orders staff active read/replay succeeds, inactive/permissionremoved both denied. Files in continuation30; pending next evidence save. Supabase dashboard secure login returned declined: do NOT retry unless user asks. App MFA/session remains valid, not provider login.

# Current .30 — account AND current-resource guards before replay

Source abe3a5144894b82327a27944c4f1358959d83cf8; hosting40; deployment appgdep_6aef85cf84c08191a42f9a122a0beed6 succeeded2026-11-07T20:11:12.810364Z. Gate21/integrity14; exact archive+commit checked before save. See continuation30/REPORT.md and registry.

Applied test-only migrations: pilot_return_action_account_guard, pilot_approval_account_guard, pilot_merchant_replay_current_access, pilot_return_replay_current_access. All succeeded; do NOT retry expired earlier request. Banned replay in3RPCs fixed, active allowed. Removed store owner replay in merchant+return fixed; owner allowed, unrelated customer retained. Return revoked-after-reactivation and MFA AAL1/AAL2 regression preserved. Latest cleanup allsynthetic0/pilotrestoredtrue. SQL evidence in continuation27/29, source security/db bindings .30.

MFA IS COMPLETE for synthetic: verified1/AAL2session1, UI .27 + refresh/Auth200. User timeout not auth failure. Preserve tab4/session; no reenrollment/password reset. Source report/SQL account tests not blanket live JWT proof.

Next independent work remains: cached customer order ownership/state coverage, full operation/sink/private schema inventory, provider/recovery/backup/alerts/concurrency blocks per report. Do not declare exhausted or ready. Preserve five accounts and1/2/3, #3unsettled. Historical notes below may mention older pending migrations/factors0; superseded above.

# Current .29 — three cached-result account guard fixes applied and retested

Source e02316d0941dff957e21907dc0c1aaadf5786b6b; hosting39; deployment appgdep_6aef8462c2d481919240b69d0e1aa737 succeeded2026-11-07T20:05:09.298317Z. Exact archive and committed source passed verify-archive, gate21 groups / integrity14 cases. See continuation29/REPORT.md and publication.json.

MFA completed, NOT blocked: verified factor1/sessionAAL2=1, UI .27 home survived reload, refresh/Auth200. User timeout did not prove Auth failure; no reenrollment/password change. Browser tab4 preserved synthetic session.

New DB migrations pilot_return_action_account_guard and pilot_approval_account_guard applied to test only. Banned cached reads were demonstrated in order_return_action/customer_confirm_order/merchant_review_order; now rejected with active allowed. Return tests also reject revoked session after reenabling and required AAL1, allow fresh AAL2. All temporary fixtures rolled back. Exact SQL and before/after in continuation27; migration/evidence bindings in .29 source security/db. Approval migration first malformed separator then confirmation expired; corrected request succeeded; do NOT retry applied migration.

Independent evidence:25 local canonicalization cases,4 literal ticket text cases,152-function public/finance/security inventory. No fullASVS closure. Matrix statuses331 incomplete/2failed/12NA retained. Current role removal with active account on cached results remains next separate test; all monetary/old JWT/provider/recovery/backup/alert acceptance remains explicit. Do not claim work exhausted. Protected1/2/3 unchanged,3unsettled.

# Current .27 — MFA live success and exact commit/archive binding

Source 5a85f8c0ade674fe7ec7db7845ae75ee9123749d; hosting 37; deployment appgdep_6aef7b93421c8191b7fe5e848362cccb succeeded. See continuation27/REPORT.md. Gate 21 groups / integrity 14 cases. Committed source byte comparison closes dirty checkout gap. Source and archive checked before save; published core/MFA bytes matched.

User completed synthetic factor: verified=1, current session AAL2=1. UI .26 home opened and refresh/Auth HTTP200. Do not request enrollment again or read OTP/secret. Current tab4 same synthetic session. MFA recovery/factor loss remains separate. No protected account/order changes.

New evidence continuation26: cross-store writes, ticket/chat isolation, ticket quota, zero cleanup, GraphQL disabled. continuation27: cart boundary source tests, publication, current registry. Canonical overall statuses unchanged, bounded partial evidence appended. Historical .26 and .25 descriptions below are historical, including factors0.

Next available work: complete per-ID source/operation evidence from triage, supported live checks with retained synthetic AAL2 session; independent provider/recovery/backup/concurrency preparation. Do not claim all available work exhausted. Do not create permanent financial fixtures to bypass rejection.

# Current .26 — 8 November2026 Asia/Dushanbe
Source0b700644507783ec7bf02fed0d4569f1da07698c, hosting36, deploymentappgdep_6aef781bf3dc8191b54df688a3e0bb63 succeeded2026-11-07T19:12:45.451991Z. Source .25 and evidence5ec5794 verified first. See continuation26/REPORT.md and publication.json.

New release integrity gate binds all checkout input files except.git/dist/node_modules/generated receipt,21 passed groups and exact Worker/manifest output. Packaging ran verify-release; verify-archive checked pushed HEAD and exact archive entries/bytes. Old .25 tar rejected. Six published assets byte-identical to tested source. Provider archive content hash separately recorded; never equate it with raw tar hash.

New rollback-only SQL cases: own/cross-store menu writes/reassignment; own/foreign ticket reply/staff sender forgery; own/foreign chat/sender forgery; ticket20allowed/21rejected. Synthetic cleanup0; no protected records or permanent financial fixture changed. ASVS V8.2.1/2/3 andV2.4.1 partial only. Full matrix331untested/2failed/12NA unchanged.

MFA factors still0. User step already explained: synthetic setup button, enroll manually, enterOTP inUI, confirm. Do not request another password or inspect MFA secret. Prior handoff tab4 synthetic scope may remain .25; do not reload during manual entry. Old-device/provider/backup/alert/concurrency blocks remain. Remaining technical work exists; no all-work-exhausted or readiness claim.

Latest evidence commit5ec5794bdaf29ddfbef22bb2d22b626cbdf11634. Source/deploy .25 recorded below.

# Current .25 — regression prevention added; review still open
Source bb73be06f4f60d3125eccc7c6fd45fda9b72db42, hosting35, deployment appgdep_6aef74a0afc481918ac4eb9641b22fd5 succeeded2026-11-07T18:57:55.085244Z. See continuation25/REPORT.md, publication.json and regression-register.json. Previous .24 source7060283f2166390abab4291aa7d95cb9ba721e45.

Build now runs20 local regression groups, removes stale output before testing and on post-build test failure. Mutation fixture proves reintroduced handler bug blocks build. DB migration/test evidence bound by hashes; no claim local binding reruns SQL. Auth unknown-error redaction repaired .25. Existing five role namespaces preserved.

Secure login submitted successfully: Auth diagnostic200, synthetic not banned/new session not revoked, factors0 and MFA requiredtrue. Data denial is AAL1 gate, NOT incorrect password. Browser tab4 is the synthetic scope with MFA setup modal open; no factor enrolled or secret read. Manual enrollment requires user interaction; do not repeat password login or change customer MFA.

Remaining open: full331 per-ID triage (continuation24), failedV6.3.3/V7.4.2, live MFA/recovery, full revoked-token/Realtime/file coverage, true finance concurrency, provider/backup/alerts, actual older devices. Do not claim all available work exhausted. Preserve protected1/2/3 and3unsettled. First live step after manual setup: verify factor status without reading secret, AAL2 current UI then expected allowed/denied operations; preserve completed local tests.

Historical checkpoints follow.

Latest evidence commit bb81d61a3d669d9eba8839af427c9d26740831d6 on candidate/pilot-readiness-20261105.

# Current continuation24 — work remains open

Application .24 source7060283f2166390abab4291aa7d95cb9ba721e45 hosting34 deployed2026-11-07T18:21:27.950632Z. Test database fsvrsvqfknogwmhccera only. See continuation24/publication.json and REPORT.md.

New six bounded repairs: raw RPC detail; boot error-page local-only logout; customer inline-handler entity escape; late proof download after clear; passive signout residual UI; nonfinite cash delivery (live DB migration pilot_delivery_cash_finite_guard, rollback before/after proof). No general ASVS acceptance. Original2 failures remain;331 detailed triage available,122 executable-now/90 additional-test/119 externally-dependent whole closures. Independent work remains even in external rows.

Browser runtime changed: old role tabs absent; current .24 login page verified only. Must use secure browserAuth for renewed credentials; no password extraction or reset. Synthetic MFA completion and live recovery remain unproved.

All synthetic finite-cash rows rolled back; protected orders1/2 delivered/settled unchanged,3 delivered/cash40/unsettled. Do not create durable finance fixtures to bypass prior rejection. Do not repeat successful tests unrelated to changed source.

Next: continue per-ID actions, current finance numeric input constraints/write paths, complete source evidence persistence and independent reviewer package. .24 source and runtime tests exist; full live UI allowed-session regression awaits secure login. No source of production read or mutation authorized.

Historical resume preserved below.

Latest review evidence commit1df637e84def77a33cfb14e3004fdc49b2935510. Application remains .22.

## Latest review checkpoint on .22

See continuation23/UNIFIED-STATUS.md. New rollback-only permission-lifecycle case passed; V17 applicability reviewed; matrix retained345 IDs/253 L1+L2 and now331untested/2failed/12not-applicable. No new release. Four live workstreams have exact blockers recorded; other technical work remains open and is not labelled externally blocked.

Latest GitHub evidence checkpoint: a5f48adb67c6f7c6f1e1c64d91979e6687a50ddd.

## Current .22

Source4c78c739cd65c53746b07db6426cf5f66f178d8a; hosting32; deploymentappgdep_6aef4245e3288191a1d08a9323c9c3d5 succeeded2026-11-07T15:23:04.612543Z. Secure request-ID compatibility repaired/tested in three paths; new read-only public table/policy inventory recorded. See continuation22/REPORT.md. .21 accountant-session proof preserved without retest. No database writes this continuation. No security acceptance.

Latest evidence GitHub commit: a30dbb216719f9c57a7a7f0d8003f64252054c8b.

## Current .21 — 2026-11-07

Deployed source be4d6565c466664be1d67dacc678a3dea32d7888, hosting31. See continuation21/REPORT.md for finance session guard repair, proof info/list HTTP evidence, RPC inventory, provider/log evidence and exact blocks. No full security acceptance. Orders1/2/3 and receipts preserved; order3 unsettled. Prior statements below are historical.

Latest GitHub checkpoint: 7839e061d5d23d2515cee7b19d7de85ddff7401b. Customer-scope decision is approved; no general MFA rollout.

## Current .20 — customer authentication scope locked

Owner clarification implemented: normal customer bootstrap does not require the MFA module/API. No authenticator/QR/customer enrollment introduced. Synthetic MFA remains isolated; administrative gate and server account_enabled unchanged. Source fec375fb5860759813069c98ea2ab3a62940de26, hosting30, deployment appgdep_6aef38792f8c8191a8edfc15d4c5688f succeeded2026-11-07T14:41:15Z. Five scope regressions and existing MFA tests passed; four offline recovery cases passed. Required roster readback1 synthetic-only; protected accounts0; verified synthetic factors0. No minimum-device support claimed. Added actual-device/weak-network auth matrix and separate administrative recovery cases in auth-compatibility/ACCEPTANCE.md. Real old devices, actual recovery mailbox and user MFA enrollment remain unavailable/pending. Existing customer session verification after deploy is recorded separately when observed. No protected account/password/order changes.

GitHub evidence/isolated patch checkpoint: 0324609ddae119d06dab1d41843cb02addb9b530 on candidate/pilot-readiness-20261105. Sites source is separately fd665456d30eb28612c13da93df7e6d71da9ec94 (.19). Work continues after required synthetic MFA enrollment.

# Current continuation — TALABOT security and functional acceptance

## Current evidence checkpoint — .19, 2026-11-07, 13:45:27 UTC (work continues)

Deployed source **`fd665456d30eb28612c13da93df7e6d71da9ec94`**, hosting **29**, deployment **`appgdep_6aef2b64e05c819181b2d2aa9a925f1b`** succeeded at13:45:27UTC per root. Existing customer and merchant valid sessions were observed on .19. Isolated test project `fsvrsvqfknogwmhccera` only. This is the current checkpoint of the same ongoing acceptance plan; earlier .16/.17/.18 pending/current statements below are historical. No whole-ASVS, final readiness or independent penetration-test acceptance is implied.

| Area | Current bounded evidence | Remaining limitation |
|---|---|---|
| Admin inactivity | .18 implements a nonblocking, one-shot logout after30minutes idle; `tests/admin-idle.cjs` passed per root. | Unit regression evidence does not prove every server session/token has expired or a fresh30minute physical-browser test. |
| Image limits | .18 client checks width and height each≤16384, total≤64000000pixels and encoded output≤1MiB; `tests/image-limits.cjs` passed, including accepted48MP case, per root. | Client checks are bypassable. Server content validation, direct upload, pixel-flood resistance and complete V5 coverage remain untested. |
| Proof operation policy | .17 owner HTTP download of order#3 proof succeeded200/26651bytes. Single signing returned404. Batch transport returned200 but no item contained a signedUrl. SQL operation test independently returned owner download rows1/sign rows0. | This establishes denial of new signed-URL issuance for the tested owner path, with authenticated download preserved. Already-issued URL200 at44seconds after ban and400 at175seconds remains a distinct historical revocation failure; no retroactive revocation claim. Full disabled/info/list/role matrix is incomplete. |
| RPC disabled-account guards | All18 additional post-fix direct-SQL retests now passed, supplementing the initial3 fixes. Last four: active contacts/store-private/default-address/status controls preserved; disabled contacts/default-address/status rejected `account_blocked`; disabled store-private returned[]. Earlier10+store2+customer2 retests retained. | Full valid-record role/object/function and HTTP matrices remain open; SQL rollback tests are bounded defense-in-depth evidence. |
| Permission helpers | `pilot_revoked_session_permission_helpers` applied to `is_admin`, `has_perm`, `my_perms`, `owns_store`. Synthetic revoked sessions and MFA-required aal1 now return false/false/null/false; active and aal2 retain intended admin/owner capabilities. | Synthetic SQL claims do not prove live MFA or complete Auth termination. Parent ran active controls before adding revocation; no denylist DELETE, no expired-confirmation reuse, rollback only. |
| CSP and report receiver | .19 includes global first-party minimum CSP and `/csp-report`; source84/84 tests passed. Receiver bounds streamed body16KiB,2s read timeout and100ms cancellation; sanitized fixed-field console output sampled≤10/minute/warm isolate. | Actual curl: customer HEAD200 with full CSP/report-uri; core JS HEAD200 and missing-route HEAD404 with restrictive fallback/report-uri; report POST204. Earlier urllib403 is a client-path limitation, not evidence of an application block. Provider-generated responses, browser-automatic report delivery, durable retention and complete resource trust coverage remain unverified. Local sampling is not a global traffic/cost cap; existing inline allowances remain. |
| Persistent app data | Approval argument bytes replaced by SHA-256 key fingerprints. Current-user authenticated-load migration preserves request UUID, verifies hashed write before removing exact legacy key; invalid/expired cart removed on load, valid24h cart retained. Persistence9/9, migration7/7, authenticated-load order1/1 passed. | Hashing is not encryption. Conflicting/malformed/unrecognized/other-user keys remain for safe reconciliation; current cart notes remain intentionally stored. No full browser-storage privacy pass. |
| Valid-record finance | Rollback fixtures: refund60 then40 reaches100 cap; duplicate `already_refunded`, excess `refund_too_high`; injected post-return refund/settlement exceptions roll back effects. Settlement retry amount5, same-key exact replay, changed-target `request_conflict`, new request `nothing_to_settle`; one command/receipt/receipt-order. Cleanup restored config and zero fixture rows. | Sequential SQL subtransaction exceptions prove transactional rollback, not actual TCP disconnect, process crash, mid-statement interruption or concurrent settlement/refund. No protected order mutation or broad ASVS closure. |
| Synthetic MFA handoff | Secure synthetic login succeeded and enrollment modal is open per root. No factor has been created. Challenge/setup UI exists; private roster still synthetic-only. Earlier SQL aal1=false/aal2=true and protected-customer aal1=true retained. | User must complete enrollment through the secure authenticator flow. No actual factor enrollment, verified OTP, recovery, expiry/replay or resulting live aal2 session evidence yet. V6.3.3 remains failed/open. No seed, OTP or credential is recorded here. |
| Auth termination | Synthetic ban leaves0 Auth sessions; re-enable leaves0 sessions/refresh rows; UI400/session missing recorded. Only synthetic-scoped deletion applied. | Retained-JWT `getUser`401 not established. Broad Auth deletion was rejected by automatic review for broad logout risk and was not applied. V7.4.2 remains failed/open; multi-session and existing Realtime termination remain incomplete. |
| Financial concurrency | Two actually overlapping HTTP calls returned the same entry17 and serialized lock acquisition. Compensation18 restored fixture balance0; temporary probe dropped and synthetic grants removed. | One same-key case only; ambiguous acknowledgement, interrupted requests, different-key contention and full state transitions remain untested. |
| Supply chain and operations | .18 delta:3commits/16new text blobs yielded0 configured secret-pattern matches; offline rebuild byte-identical;6 changed assets verified and68 unchanged reused,74 total. Vendored Supabase, Leaflet loader/SRI, build script and Worker unchanged; local MFA module adds no external package dependency. Incident response/handoff written; tabletop remains simulated. | Bounded source/build identity does not prove complete upstream/bundled transitive provenance, all-secret scanning or security of changed application logic. Prior advisory applicability and GitHub permission limits retain original scope; SC-01 remains. No delivered alert, executed restore/incident drill, measured RPO/RTO or enforceable spending ceiling established. |

Evidence files read for this checkpoint: `session-revocation/proof-http-17.json`, `proof-operation-results.json`, `lifecycle-http-14.json`; `rpc-continuation/REPORT.md`, `retest-all10-results.json`, `retest-assertions.json`, `retest-cleanup.json`, `results-customer-two-after.json`, `results-store-two-after.json`; `supply-chain/CONTINUATION-18.md` and `incremental-18.json`; `rpc-continuation/results-four-more-after.json`, `results-helpers-before.json`, `results-helpers-after.json`; `csp19/REPORT.md` and `deployed-curl-safe.json`; `asvs-scope-review/continuation18/REPORT.md`; `functional-sql/finance-valid-report.md` and its result/cleanup artifacts. Deployment, .19 customer/merchant observations, unit test results, helper migration and current secure MFA modal state are root-reported observations; this consolidation did not repeat runtime tests.

Remaining categories are distinct:
- **Confirmed failures/open deficiencies:** global termination and MFA requirements remain unmet; prior old signed-URL immediate revocation failure remains recorded; Known first-party CSP minimum/report-endpoint defects now have local84/84 and deployed curl evidence; full requirement coverage remains untested. New owner signing denial does not close all storage or authorization requirements.
- **Untested technical work:** live MFA/OTP/recovery; independent retained-token and multi-session checks; Realtime termination; remaining proof operation/role cases; valid-record RPC matrix; interrupted finance; server-side image checks; remaining provider response/CSP trust coverage and browser-automatic report delivery/retention; remaining functional branches and physical new-order audio.
- **Provider/access constraints:** inaccessible managed `chatgpt.site` zone; Free Plan dashboard reports no project backups; classic GitHub branch protection read403/integration administration gap. Rulesets[] does not establish absence of classic protection. Cost limits and alert delivery remain unverified.
- **User handoff now active:** synthetic enrollment modal is open after successful secure login; user completes authenticator enrollment. No factor or successful OTP should be inferred from opening the modal. The rejected broad Auth migration is a separate approval boundary.

Root final .19 cleanup confirms protected invariants unchanged and synthetic fixture rows0. Five existing accounts remain active; orders#1/#2/#3 retain original status, cash40/total40 and original timestamps; #1/#2 retain settlements; #3 delivered/unsettled/share5; receipts2. No protected order/account mutation recorded; final cleanup is root-reported.

ASVS matrix now records343 untested,2 failed,0 passed: V3.4.3 and V3.4.7 move from failed to untested with bounded remediation evidence; V6.3.3 and V7.4.2 remain failed. All345 official IDs/text/levels and253 L1+L2 retained. Current report evidence may postdate other matrix annotations; no requirement is promoted to pass. Previously persisted GitHub checkpoint `d9f97ddaddcb2c5a0edfc688ab209e9932ffef6c` on `candidate/pilot-readiness-20261105` is separate from .19 Sites source; root handles persistence of this new batch.

## Resume in the existing plan
1. Continue independently testable work while the user completes synthetic authenticator enrollment. After actual enrollment, verify challenge/OTP and live aal1/aal2 behavior in the synthetic scope; record expired/replayed/invalid-code and recovery results without secrets or expanding the roster.
2. Complete remaining proof operation/role checks and .19 regression as warranted. Reuse the confirmed .17 owner download and new single/batch signing denial; do not describe those cases as still wholly untested. Keep old URL lifetime/revocation evidence separate.
3. Reuse the completed18 additional RPC and four helper post-fix results; continue uncovered valid-record role/object cases. Preserve the distinction between SQL defense-in-depth checks and actual HTTP authorization.
4. Test independent retained synthetic tokens, multiple sessions and existing Realtime channels without retrying the rejected broad Auth deletion. Keep the scoped deletion result and UI400 limitation explicit.
5. Continue actual HTTP finance interruption/ambiguous-response cases beyond the completed SQL exception suite; complete provider/header and automatic-report/retention coverage, server upload validation and outstanding functional branches without protected settlement/account changes. Existing entry17/18 compensation is complete.
6. Continue provider/operations and supply-chain gaps according to actual access. Runbooks/tabletop are preparatory evidence; a real restore needs a separate destination. Save new source/evidence through the root workflow and record the exact new GitHub commit separately from Sites source.

Historical .16/.17/.18 statements and full previous evidence are preserved in REPORT.md. This resume supersedes the prior .16 deployment and “post-policy HTTP pending” statements. Work continues; no final acceptance decision is recorded.

Live .20 verification: existing customer session opened the complete customer home without MFA/QR; this is session reuse, not a fresh credential-entry or old-device test.
