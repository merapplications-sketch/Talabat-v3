---
name: talabot-pilot-readiness
description: Evidence-first TALABOT pilot readiness, issue triage and safety regression; never interpret this skill as an authorization for production or feature development.
---

# TALABOT — Pilot Readiness Skill

## Before using
Read AGENTS.md, docs/ai/RULES.md, docs/ai/DECISION-PROTOCOL.md, docs/owner-playbook/SOURCE-OF-TRUTH.md, approved owner agreements, latest issue #26 comments and the role's assignment. Confirm the latest exact source branch and SHA. Approved historical checks should not be re-run without source/environment invalidation.

## When to use
- Pilot launch readiness of current approved functionality.
- Safe source/isolated browser/security review, synthetic cases and exact regression.
- Single-role QA handoff and production/source provenance comparison.
Never use this to propose/implement arbitrary new competitor functions or bypass approvals.

## Procedure
1. Pin the actual source and deployed environment separately; identify permissions and STOP conditions.
2. Trace a customer order through discovery → customization → cart → quotes/checkout → merchant accept/prepare → driver accept/GPS/pickup → proof/delivery → CASH-01 settlement → rating/returns/support.
3. Cover scheduled, gift, group and substitution flows known from source without inventing missing behavior.
4. Test identity isolation, RBAC/RLS, duplicate orders, idempotency after timeout, duplicate delivery acknowledgments, driver Online ACK, cash undercollection, financial reconciliation, chat drafts, GPS privacy, proof image ACL, offline recovery and release parity.
5. For each test supply ID, SHA/branch, isolation boundary, synthetic fixtures, preconditions, action, expected/actual, status, P0-P3, logs/images and next responsible role.
6. For visual-only Safari preview: prove no auth, no real money/orders, no outbound requests, correct RU/EN choices, viewport 320/360/390/430, source visual fidelity and fake-cart return. Formal C-01 is not this preview.
7. If missing exact artifact, isolated runner, authorized data or safe credentials, stop with BLOCKED. Do not improvise a production test.
8. If defect reproduced, request narrow approved fix on isolated branch; verify failure before and pass after independently. No unauthorized merge/deployment.

## Output
One compact evidence package linked to the assigned GitHub issue and master #26. Do not create tasks for other roles automatically.

## Post-pilot backlog
Abroad buyer → recipient inside Tajikistan is a later owner-prioritized proposal and needs independent financial, identity, fraud, currency, delivery-proof and consent review before approval.