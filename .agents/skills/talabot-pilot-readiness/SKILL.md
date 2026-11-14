---
name: talabot-pilot-readiness
description: Use for TALABOT existing-feature pilot readiness, independent risk triage, audit of customer/driver/merchant/admin journeys, and non-production regression evidence. Do not use to implement new features, change approved financial/design policy, or publish/deploy.
---

# TALABOT Pilot Readiness Skill

This workflow supports the **current-feature pilot** only. Read `AGENTS.md`, `docs/ai/RULES.md`, and `docs/ai/DECISION-PROTOCOL.md` before using it. The authoritative decisions are still `docs/OWNER-AGREEMENTS-AR.md`, latest GitHub Issue #26/comments, the latest assigned issue, and actual source/environment evidence.

## When to trigger
- A task explicitly asks to inspect launch readiness, audit, isolate a risk, verify a fix, assess a safe no-login fake-data Safari preview, or prepare a QA handoff.
- Do **not** trigger to invent or add features from competitors, repeat unchanged accepted tests, redesign approved UI, create new permissions/paid services, or alter production.

## Workflow
1. **Pin evidence:** newest assigned SHA, branch, repo, issue and the exact previously accepted baselines. Note any drift; never assume old SHA is latest.
2. **Map journey:** customer browse → item customisation → cart → checkout → merchant acceptance/preparation → driver acceptance/GPS/pickup → delivery confirmation → cash/settlement → rating/support/return. Cover Admin visibility and RBAC. Respect all approved variants and scheduled/group/gift flows.
3. **Risk checks:** account isolation/RLS; order and delivery idempotency; driver Online ACK; chat message persistence; location visibility; delivery proof; CASH-01 and Q09–17; discounts/price/tip; refunds/ledger; network recovery; backups/version provenance.
4. **Plan tests:** positive + negative + concurrency + timeout/retry + long strings/offline/locale/viewport. Assign unique case IDs and safe synthetic preconditions.
5. **Execution boundary:** only run approved isolated tests. Static-only audit can establish a source finding, but not a runtime PASS. Physical Safari must be observed on a real iPhone to count as physical Safari proof.
6. **Outcome:** deliver a compact table: `ID | finding | SHA/env | executed? | status | severity | evidence | responsible role | minimal next action`.
7. **Handoff:** one consolidated delta to the manager; no automatic changes or GitHub mutations without task-specific permission.

## Mandatory stop and escalation
Stop for unknown environment provenance, any suspected link to production, unapproved schema/finance/auth changes, inability to protect sensitive data, or owner decision conflict.

## Deferred feature track
Ordering from abroad for a local recipient is a prioritized **future proposal**, not an implicit pilot feature. Record it as backlog with a separate later acceptance and financial/legal/security design. Do not activate it in current QA tasks.
