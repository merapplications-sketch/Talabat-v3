# Batch104 closure

Status: candidate saved and isolated tests pass; independent REVIEW104 acceptance pending; NOT READY for production.
Tested source/tests commit:fc4d914f54bb9c846c38a3f2d449046980fc8857.
CI: https://github.com/merapplications-sketch/Talabat-v3/actions/runs/42813660670 — all client/postgres/required104 jobs passed.
26 native tests (original19 retained +7 new),4 admission/concurrency cases,1 restore including key/fingerprint/terminal-rejection fence;11 Chromium cases including actual owned-process SIGKILL/reopen;5 preserved cart assertions in CI;38 local fast groups against generated104 customer/core.

S01 was reproduced on unchanged103 before the104 run and passes104 across float/session settings, rollback and re-upgrade. Existing103 fingerprint bytes remain unchanged. Original C01/C02 red observations are retained in baseline-client-red.json; Chromium104 reproductions now pass.

Earlier runs42811950637 and42812905253 did not close green: the browser test harness hung at the CDP Browser.crash route. The second run's checkpoint records10 passing cases before that deadline. Final harness obtains the PID of its own disposable browser via CDP and sendsSIGKILL; successful reopening verifies retained unresolved state. No test expectation was relaxed. First local fast run's cart extraction mismatch and typed-response fixture adaptation are documented in REGRESSION-NOTES.md. Local Chromium sandbox launch was unavailable; remote Chromium evidence is genuine.

Core changes:
- One typed payload helper fixes float serialization for create, verified replay, unique recovery and rollback without changingHMACv1.
- Atomic IndexedDB account/attempt UUID/version ownership rejects stale responses; network/read-back timeout stays unresolved.
- Live cart revision is compared independently; edited/foreign-tab carts are preserved.
- Server-confirmed rejection records a permanent same-key fence. Explicit end re-reads receipt; correction uses a new key only after ending. Unknown attempts cannot be timed out into a new key.
- No raw order private input is stored in the closure table. Frozen browser input is removed on verified success/explicit confirmed-rejection end. Other retention periods are proposals only, not deployedTTL.

Scope limits: same browser origin/profile coordination, not global cross-device intent locking. Old103 tabs/localStorage require reconciled rollout, not automatic destructive migration. Complete target RLS/triggers/grants/enums/transitive financial side effects, private build-gate evidence, hosted identities/HTTP/E2E, Storage/provider recovery and actual Safari remain unaccepted. Original103 acceptance is preserved only in its documented isolated scope.

Reproduce/QA: CONTRACT.md and REVIEW104.md. Full per-case evidence: RESULTS.json and GitHub artifacts. Source and generated artifact hashes supplied. No protected data, production secrets or raw database dumps were published.

Resume: independent REVIEW104 of fc4d914f54bb9c846c38a3f2d449046980fc8857; then targeted repair if findings remain. No liveSQL/main merge/deployment/accounts/MFA/protected orders1/2/3 or settlement3 actions were performed.
