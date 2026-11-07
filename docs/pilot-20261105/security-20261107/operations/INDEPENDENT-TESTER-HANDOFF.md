# TALABOT independent security tester handoff

Prepared 2026-11-07. Candidate scope, not a commissioned or completed independent penetration test. Implementer evidence is supplied for reproduction and challenge; no independence claim is made for it.

## Exact target and baseline

- Allowed application: `https://talabot-isolated-safari-20261106.alwarikahtan.chatgpt.site` and its confirmed customer/merchant/driver/admin/accountant flows. Confirm exact route mapping from deployed source before sending requests.
- Allowed backend: Supabase project `fsvrsvqfknogwmhccera`; Auth, REST/RPC, Realtime and Storage for this project only. Derive endpoint URLs from verified project configuration; do not enumerate other projects.
- Current coordinating-reviewer baseline: .19 source `fd665456d30eb28612c13da93df7e6d71da9ec94`, hosting29, deployment `appgdep_6aef2b64e05c819181b2d2aa9a925f1b`, succeeded2026-11-07 13:45:27UTC. Customer and merchant sessions observed working per root. Consult `../CURRENT-RESUME.md` before any exercise; verify source/deployment/DB mapping again at kickoff. This document does not independently establish runtime controls.
- Forbidden: production `dzydscryrnahnneydnry`; unrelated tenants; infrastructure/internal routing; third-party maps/CDNs/email infrastructure; provider-wide testing; paid activation; DDoS/load/flood testing; real personal data collection; external messaging.
- Preserve orders #1/#2/#3 and all associated proofs/receipts/ledger data. #3 is intentionally unsettled (5 TJS due). Do not settle, refund, reassign, cancel or otherwise mutate them. Preserve existing five role accounts and passwords.

## Kickoff gates and fixtures

Name independent tester and sponsor, agree dates, evidence retention/access, emergency contact and permitted request ceiling before active tests. Start low-volume serialized tests; concurrent finance tests need an individually agreed bounded two-connection case and disposable data. A numerical rate limit is not approved by this document. No privileged key delivery through chat or report; use the designated secret channel.

Create only explicitly authorized dedicated fixtures: customer A/B; merchant/store A/B; driver A/B; accountant; restricted staff; administrator; disabled variants. Use controlled mailboxes and synthetic names, contact values, addresses and non-personal images. Record each Auth subject/store/order/object/request UUID and initial state in a fixture manifest; do not forge Auth rows. Separate SQL rollback tests from persisted HTTP fixtures. Do not assume historical accounts or IDs 901/902 are disposable.

Before mutation, capture read-only protected-order settlement/receipt invariants and fixture ledger balances. Every test record must name its permitted object IDs and cleanup operation. Rollback SQL where suitable; persisted financial effects require traceable approved compensating entries, never deleting ledger history. No bulk settlement, global user ban or broad cleanup queries.

## Priority test work

| Boundary | Required bounded cases | Acceptance evidence / limits |
|---|---|---|
| Auth lifecycle | Two sessions; disable/re-enable; logout; refresh; fresh login; user/MFA endpoints; recovery; MFA enrollment/replay/recovery | Server responses and subsequent access across all applicable surfaces; frontend state alone insufficient |
| Authorization | Role×own/other store/object×read/write/field matrix; stale permissions; disabled users; all exposed RPC inventory reviewed by risk | Actual HTTP JWT tests plus SQL policy cases; RLS enabled or 110 callable functions is not test coverage |
| Storage | Authorized and unauthorized bytes/upload; wrong folder; content signature mismatch; oversize; prior signed URL before/after ban and expiry | Status, byte count/hash, object policy; SQL metadata result does not prove byte denial |
| Realtime | Unauthorized channel/object and ongoing subscription after permission removal/ban | Observed deliveries/denials before and after change; no inference from REST |
| Financial integrity | Same-key same-payload; same-key conflict; different-key contention; refund/settlement/wallet writer overlap; accepted request with lost acknowledgement | Prove independent connection overlap with timing/barrier evidence; exact ledger effects, no negative/duplicate drift; use dedicated orders only |
| Injection/client security | Role-specific input/output contexts, support/admin settings, HTML/JS attributes; unsafe-inline impact; headers on errors/assets/redirects | Harmless synthetic marker; no exfiltration endpoints or persisted payload in protected records |
| Availability/abuse/cost | Configuration review for login/recovery/OTP/fake account/order/storage/map abuse; direct Supabase path coverage | Provider evidence or explicitly unverified; no flood and no paid activation; alert is not a hard spending cap |
| Operations/supply chain | Source/history/SBOM/CI permissions; backup inventory, separate restore, alert delivery and response exercise | Evidence of actual configured controls and observed outcomes; a runbook or simulated tabletop is not technical acceptance |

Latest implementer evidence includes18 additional disabled-RPC retests, four revoked-session/MFA helper guards, SQL refund/settlement rollback/replay cases, and local CSP84/84 and persistence9+7+1 tests. These are bounded evidence, not independent acceptance. Owner proof download/new-signing denial is HTTP-tested on .17; old URL immediate revocation and broad Auth termination remain open. Synthetic MFA enrollment modal is open but no factor created. Live .19 curl verifies customer200/core200/missing404 CSP/report-uri and report POST204. Earlier urllib403 is a client-path limitation. Provider responses, automatic browser report delivery and retention remain unverified.

Maintain the official ASVS 5.0.0 requirement IDs/descriptions in acceptance-plan. It lists 345 total/253 L1+L2 and tracks selected high-risk L3 controls; reconcile statuses against newer evidence. Allowed status labels: ناجح بدليل / فاشل / غير مختبر / غير منطبق مع السبب. Partial coverage belongs in notes and must not be promoted to whole-requirement pass. N/A needs architecture/configuration proof.

## Stop rules

Stop the affected test immediately for any production identifier, unexpected real personal data, protected-order/account mutation risk, unknown project routing, unbounded writes, service degradation, unexpected charge/external delivery or loss of fixture isolation. Stop concurrency if more than the authorized two connections/requests are needed. Preserve minimal redacted evidence, notify the named sponsor through the agreed channel, and await a scoped continuation decision. Do not attempt automatic repair, global rollback, bulk deletion or “prove impact” by further access. If no emergency contact is available, active testing does not start.

## Evidence checklist for every finding and retest

- UTC date/time, independent tester identity, exact deployed source/hosting identifier, backend project and relevant schema/migration snapshot.
- Requirement/test ID, preconditions, synthetic subject role/object ownership, fixture manifest and permitted mutation scope.
- Sanitized reproducible request/response with method/path/status, safe headers, request ID and outcome. Strip bearer/refresh tokens, API secrets, full signed URLs and personal data.
- Expected versus actual behavior, narrow demonstrated impact, affected surfaces and explicit untested routes. Separate observations from inferred risk.
- For concurrent operations: independent connection identifiers, barrier/start/end timestamps, demonstrated overlap, idempotency IDs and before/after ledger invariants.
- For restore: real artifact identity/hash/timestamp, distinct target, actual timing, schema/data/Storage/Auth validation and protected-state comparison. Simulations receive SIMULATED labels and no RPO/RTO measurement.
- For alerts: trigger, actual recipient/channel, receipt time and acknowledgement; configured destination alone is insufficient.
- Evidence artifact hashes, access/retention owner, safe cleanup result and final protected-order/fixture reconciliation.
- Severity rationale, precise fix recommendation, remediation source/migration, independent retest, residual risk and owner acceptance or explicit open status.

Deliver a signed scope statement, executive findings, reproducible technical findings, complete status matrix and remediation/retest ledger. Whole-system readiness cannot be inferred from closing the known findings. Backup/restore, managed WAF/DDoS/direct API coverage, cost ceilings and on-call alerts remain unverified until independently evidenced.
