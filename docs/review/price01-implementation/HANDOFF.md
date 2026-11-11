# PRICE-01 — continuation / independent QA

The original roadmap and owner addendum are unchanged. This is the authorized PRICE01 track only.

- Source/tests: `bb01f11b855a2898f3f0b0f8908de827be68844b`.
- Branch: `review/price01-isolated-20261111`.
- Parent proposal: `b75ff6d7df6911659c35296000317f5a1fcec983`.
- New executable scope:10 added files under `tests/price01-impl/`; no old executable source changed.
- Evidence/report: this directory, in the documentation child commit of that source.
- State: local candidate saved;26 PostgreSQL groups and17 Node VM cases effective PASS. PRICE-F PARTIAL; independent QA PENDING. No CI/hosted/browser acceptance implied.
- Preserve:103→104→105→106, HMACv1, historical keys, closures/resource guards, C01/C03/C04, TIP02/NULL01 and accepted consumed-tip recovery. Do not rerun unchanged accepted suites or reopen G1C-PREC03.

Next authorized step is INDEPENDENT QA of this precise diff and affected tests. Focus on displayed consent versus final persistence, post-helper comparison, atomic rollback/closure, old-client recovery, preserved frozen payload, late replies and intermediate draft writes. Use README in the source directory and ACCEPTANCE mapping. Browser evidence must be obtained separately in a functioning isolated Chromium/IndexedDB environment, then actual Safari; Node VM cannot close it.

Client reproduction requires the already pinned recovered inputs, not root customer.html/core from an arbitrary branch. Exact input hashes are in tests/native103/ui-source-hashes.json. The inputs were available and validated here; this commit does not republish them or private evidence. If the reviewer lacks that previously accepted pair, its availability is a concrete prerequisite for regenerating the same client. The new generator, its overlay, generated diff and output hashes are saved here; do not substitute a different input merely to make the build run.

Do not activate on hosted services. Before a future owner rollout decision: actual target dependency/writer inventory, authorized HTTP identities, browser/client readiness, complete transaction/external-effect evidence, recovery/backup proof and safe recovery-only rollback. The provider and operational evidence gaps remain those of PHASE1; no G1 gate is closed by this candidate.

PHASE1 PARTIAL / BLOCKED. PHASE2 NO-GO. No main merge, deployment, hosted SQL, account/MFA/RLS changes, protected orders#1/#2/#3 or due#3 action.
