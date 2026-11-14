# TALABOT — Pilot-First Execution Order (Owner priority 2026-11-14)

**Decision:** Pilot with existing features **first**, maintain approved owner agreements; staged improvements **later**. Do not add or redesign a competitor feature during pilot-readiness.

## Current exact handoff
- Master register: [Issue #26](https://github.com/merapplications-sketch/Talabat-v3/issues/26)
- Last executed team deliverable: [Stage13 programmer #39, commit `3f74b29a`](https://github.com/merapplications-sketch/Talabat-v3/commit/3f74b29a7c4bcc89cef9e25dd73f574448ab7896) (synthetic preview only)
- Proven: one demo fixture-line correction; 8/8 simulated language cases, **not browser acceptance**
- Unproven: full browser execution, no-egress proof, actual iPhone Safari; current-source operational E2E 0/51, Admin 0/21, G1 0/6
- **Next only role:** independent technical browser/security reviewer on corrected Stage13 candidate, followed separately by independent UX/device reviewer if executable. No broad re-audit, new feature or release.

## Separate tracks — never merge evidence
| Track | Content | Required before next phase |
|---|---|---|
| A — Safe no-login visual demo | Static mock customer; original design, fake products/cart, no real financial/auth/API calls | Fully materialized candidate + local/browser network/DOM/screenshots/RU/EN validation, independent review; owner approval for exact static public hostname before publisher acts |
| B — Operational functional QA | Real app code in verified non-production isolated test environment; customer/driver/merchant/admin/backend | Idempotency, permissions, finances, state transitions, GPS, timeout/race, account isolation, G1 provenance, backup/restore and complete test receipts |
| C — Limited live pilot | Owner-approved real service under written narrow conditions | B gate outcomes and release/ops/rollback/finance approval; scope, market, operator contacts, evidence limits, stop criteria |
| D — Stabilization | Incidents, dispatch reliability, support and measurable operations | Owner acceptance of pilot learnings, no unauthorized risk expansion |
| E — Future feature proposals | Abroad payer/local Tajik recipient comes first for product research; other global competitor gaps are candidates | Source-verified gap, market case, legal/PSP/FX/privacy feasibility, cost, security/test plan and new explicit owner approval |

## Practical sequence (single next role at a time)
1. **Manager** verifies Stage13 handoff/current source and assigns the independent browser/security retest only.
2. **Independent reviewer** performs safe source-matched local static browser run if technically available. Capture requests, console, DOM/screenshots, 320/360/390/430, RU/EN and checkout-block test. Mark BLOCKED honestly when the verified artifact/runner is absent.
3. **Independent UX** checks the same proven candidate on real mobile Safari and approved design, no redesign. Any old pilot color feedback stays deferred until a scoped owner decision.
4. **Publisher/OPS** proposes exact no-cost isolated static HTTPS hostname only after audit, but cannot publish until owner explicitly authorizes exact site/artifact.
5. In parallel only when separately assigned and safe, follow **Track B** test gates and minimal approved fixes. Do not use Track A as substitute for B.
6. **Manager** consolidates quantitative release gates, asks owner to decide actual limited pilot. No fixed date, number of merchants or orders is assumed by this document.
7. **After pilot evidence**, prepare abroad-to-local-recipient requirements and competitor feature ranking without changing original accepted workflow.

## Risk priority / stop checks
P0/P1 access, finance, idempotency, driver's delivery/cash and source/deploy drift before UI polish or new features. See [risk register](RISK-AND-TEST-PRIORITIES.md) and [full comparator tests](../research/TALABOT-Competitive-Features-Risks-20261114.md). Do not use missing browser evidence as PASS.

**Forbidden unless separately authorized:** code/design changes, `main`, merge, publish, live API/SQL/Supabase/Cloudflare, credentials and MFA/roles, orders/settlements, payment provider calls, paid tooling, restoring production backups or inviting more than one parallel role for the next stage.
