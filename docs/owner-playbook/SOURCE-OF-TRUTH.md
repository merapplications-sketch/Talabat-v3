# TALABOT — Existing approved decisions and continuity map

**Date of source review:** 2026-11-14 (Asia/Dushanbe)  
**Status:** An INDEX of existing source-of-truth documents, not a rewritten charter or final full audit. New playbook files are review drafts.  
**Repository boundary:** [Customer/Driver/Merchant/core](https://github.com/merapplications-sketch/Talabat-v3) and [separate TailAdmin UI repo](https://github.com/merapplications-sketch/talabot-tailadmin-review). Never import code across repos without explicit scope.

## Precedence: use existing approved facts
1. **Explicit later owner approval of the same topic** and original accepted record, with date and scope.
2. **[Owner agreements — CASH-01, RETURN-01, SCOPE-01, language and Safari](../OWNER-AGREEMENTS-AR.md)**. This file remains unchanged.
3. **[Master manager register #26](https://github.com/merapplications-sketch/Talabat-v3/issues/26)** and latest issue comments. This is the coordinated project gate/QA record, not proof of deployment or permission to write production.
4. **[Phase 1 continuity](../continuity/PHASE1-CURRENT.md)**, including later approved Master Plan Addendum 01 and phase dependencies. Read the most recent **effective** entries, not old superseded PENDING statements.
5. **[Original project technical plan](https://github.com/merapplications-sketch/Talabat-v3/blob/09ef07fd29fb5c5a3e323c23c7331e577567ab1e/TECH-PLAN.md)** and **[delivery/tracking design plan](https://github.com/merapplications-sketch/Talabat-v3/blob/09ef07fd29fb5c5a3e323c23c7331e577567ab1e/docs/plan/DELIVERY-TRACKING-PLAN.md)** are historical planning references; future changes may already supersede some details.
6. **[Continuation 108 six-stage target plan](../review/continuation108/TARGET-ALIGNMENT-PLAN.md)** including its addendum; do not reorder G1 or phase gates from this new playbook.
7. **[Consolidated QA](https://github.com/merapplications-sketch/Talabat-v3/blob/0ab523782ee1bf6f69e2e3be7ec6e96394d9ce6a/docs/qa-first-20261113/MASTER-QA-CONSOLIDATED-20261113.md)**, **[Stage 13 demo language fix](https://github.com/merapplications-sketch/Talabat-v3/issues/39)** and subsequent independent reviews. Preserve exact SHA/branch boundaries.
8. **[TailAdmin UX approved candidate](https://github.com/merapplications-sketch/talabot-tailadmin-review/tree/review/ux02-v01-v05-candidate-20261112)**: Template B, four KPI cards from A, V04 and later owner choices; do not treat UI-only reviews as runtime acceptance.

## Unchanged owner-approved operating rules — examples, NOT exhaustive
- CASH-01: courier pays restaurant upfront and collects total from customer; holds cost paid plus own share of delivery; owes platform *only* platform portion of delivery; restaurant commission separate. Actual split is configured per order. Do not reassign prior ledgers.
- RETURN-01: refund/return claim stays open until the return of funds is actually documented, not just promised by the restaurant.
- SCOPE-01: cash is the pilot's primary payment path; non-advance/electronic proposals cannot substitute it without explicit approval.
- Language: manual RU/EN selection overrides browser preference across visits, automatic first-visit choice uses supported browser languages, otherwise RU.
- Approved customer visual identity and journey: Dynamic Marketplace B / restaurant v1.6 / Direction A / DineOut Premium Gold / original Russian logo and palette.
- Admin approved Template B and four KPIs, original analytics, UX-02 accepted components. Historical pilot-login saturation concern is **deferred**, not an approved recolor.
- Prior tests PRICE/RATINGS/TIP and 106/107 are preserved only at their precise accepted SHA and environment, not assumed validated on the currently deployed release.
- No changes to main, hosted SQL/Cloudflare/Supabase, roles/MFA, finance, live orders #1–#3 and #3 settlement, deployment or costs without explicit authorization.

## Existing rollout gate — status as last checked on 2026-11-14
- Formal current-source E2E **0/51**, Admin **0/21**. This means **not executed/verified in the stated current-source environment**, not that the app fails those cases.
- G1-A/B/C/E/F remain PARTIAL, G1-D BLOCKED; **RELEASE/PHASE2 NO-GO**.
- Isolated public-free, no-login Safari **synthetic visual** candidate Stage13 `3f74b29a7c4bcc89cef9e25dd73f574448ab7896`: language 8/8 V8 function-simulated only; browser/security egress/actual iPhone Safari proofs remain BLOCKED; no public new URL.
- Independent exact-artifact browser/security/UX review precedes any separately approved free demo publication. This is not the formal C-01 Auth/profile test.

## New owner-prioritized goals — status
1. **Current priority:** safe trial launch with existing approved features, no additional product feature scope.
2. **After stable pilot:** review post-pilot roadmap options, particularly **ordering from abroad for a recipient inside Tajikistan**. No cross-border payment/FX/identity policy or implementation has been approved by this playbook.
3. **Competitor opportunities:** [Global feature and risk benchmark](../benchmark/TALABOT-20261114-feature-risk-global.md) is research, not automatic proof a feature is absent or authorization to develop it.

## Disagreement / update protocol
If this index or another new playbook file contradicts an approved source, STOP and quote both exact references to the owner. Do not rewrite or silently "harmonize" approved text. If a new owner decision is made, save the decision and its exact scope/date in Issue #26 and link the original source; preserve the old evidence. GitHub comments do not automatically activate ChatGPT Work agents.

## Scope review limitation
This index is based on several canonical published records and latest visible Issue #26. It is **not a completed exhaustive audit of every historical conversation, branch, decision or hidden working state**. The manager must compare it against later approved amendments before declaring it authoritative.