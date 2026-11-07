# C31-LOG — raw first-party client exception logging
Source before abe3a5144894b82327a27944c4f1358959d83cf8; fix ea65f5289f3d19ccc5d3dbb65b59650e23e01370. New uncovered paths, not a proven regression of previously fixed generic RPC error wrapper.

Severity: Low for demonstrated browser-console disclosure. No real secret leakage, remote log exfiltration, session compromise or other-user access demonstrated. Scope: first-party client console only; provider/SDK logs remain separate.

Root cause: done()/other write, refresh, bootstrap and image/error paths passed arbitrary exception objects to console.error, while displaying a generic UI message. Synthetic marker in message/details/token survived intact in done() console output. Raw exception fields can contain backend details or submitted values.

Impact review: changed only console projections at17 core sites and checkout catch; preserved response errors, refresh/retry/boot functions, network detection, SQL, sessions, permissions, file handling and accounting. Existing errKey whitelist projects known codes; checkout catch uses a fixed code. No new network logging or UI changes.

Tests: extended existing security-errors-logout.cjs without removing assertions. Actual extracted done() before raw_marker_logged=true, after=false; both runs generic denial and successful {ok:true} with one refresh. Regression asserts all first-party core raw console.error(e/r.error/name,e) sites absent and checkout does not log raw e. The prior RPC/domain/success/logout tests remain.21 groups passed; exact commit, source bytes, receipt and tar verified before save/deploy.

Published: .31/hosting41, same test URL. Core JS bytes downloaded and matched local fixed source. Browser home resumed existing synthetic session without login or reenrollment. This does not claim a live fault was injected into every published logging path, nor complete V16.2.5/V16.5.1/V16.4.1 coverage.

Rollback: source .30 retained; do not restore its raw logs without carrying this patch and rerunning affected guards. DB guards from .28-.30 remain unchanged.
