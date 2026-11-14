# TALABOT — Evidence-First Decision Protocol

**Status: DRAFT / saved for review on a separate documentation branch; not a new owner-approved policy.** This method concerns visible evidence and decisions, not an AI's hidden reasoning.

## Objective and precedence
The current objective is **safe pilot of existing approved TALABOT functionality**. The canonical owner approvals, later approved amendments and task-scoped authorizations take precedence. See [Source of Truth](../owner-playbook/SOURCE-OF-TRUTH.md), [Owner Agreements](../OWNER-AGREEMENTS-AR.md), and [Master Issue #26](https://github.com/merapplications-sketch/Talabat-v3/issues/26). Future feature research is not permission to implement.

## Task-level decision procedure
1. **Intake** — State desired outcome, assigned role, exact issue, permitted and forbidden actions, and one deliverable.
2. **Recover** — Read the latest master/role issue comments, approved agreements, continuity file, correct HEAD and previous accepted evidence. Do not silently overwrite newer state or rerun completed valid tests.
3. **Classify** — (A) source-confirmed risk/bug, (B) current partial feature, (C) unverified claim or gap, (D) future feature proposal. C and D are not automatic implementation work.
4. **Prioritize** — First security/data access, finance and idempotency; then driver/merchant/order state; then customer and UX; finally optional new features. Severity P0–P3 requires evidence.
5. **Design test** — ID, preconditions, synthetic fixtures, exact actions, expected backend/UI/financial outcome, timeout/negative/race paths, evidence, isolation and cleanup.
6. **Execute only when authorized and safely possible** — If source artifact, suitable isolated runner, credentials or permissions are missing, record BLOCKED. A static scan cannot be called browser PASS.
7. **Repair only the approved defect** — Isolated source branch, failing-before/passing-after proof, minimal delta, independent review and explicit owner-controlled release.
8. **Release decision** — Verify current source-to-deployment provenance, real effective backend, financial reconciliation, RBAC/RLS, recovery/restore, current-source integrated tests and physical Safari. No production/go-live from demo-only pass.
9. **Future phases** — Once pilot is authorized and stabilized, propose additional features with evidence, cost and acceptance tests. Abroad payer → Dushanbe recipient is an important future candidate, not yet an approved payment flow.

## Decision/evidence record template
- Task ID, date, designated owner and role
- Repository, branch, exact SHA and proven execution environment
- Governing approved terms and reused tests (links)
- Category A/B/C/D; priority P0–P3; confidence and known limits
- Steps, expected vs observed, tests executed, result PASS/FAIL/PARTIAL/BLOCKED/UNTESTED
- Screenshots, logs, request/network traces, financial oracle / SHA
- Safe fix only if authorized, independent acceptance and rollback considerations
- Next *single* responsible role, exact action and STOP conditions
- Owner decision needed; status: PROPOSED / APPROVED / DEFERRED / REJECTED

## Example — double delivery submission
Source risk F-02/P1: driver may send parallel delivery confirmation requests. Use two fast clicks plus late ACK and retry-after-commit in a completely isolated fake-data environment. PASS requires a single delivered state and at-most-once financial/receipt effects. Without an isolated host or effective writer version, mark BLOCKED. Do not change CASH-01 or actual money entries by inference.

**Feature threshold:** confirmed gap in latest source + reason for users/operators + operational/legal/finance cost + tests and dependencies + explicit owner approval. Never create a new feature from a competitor advert alone.
