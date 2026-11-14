# TALABOT — Permanent Operating Rules

Status: **PROPOSED FOR OWNER APPROVAL**. This is an index of guardrails; the full owner-approved source documents prevail. Do not copy legal or financial formulas into this file as a second source of truth.

## 1. Scope and priority
- TALABOT repositories: `merapplications-sketch/Talabat-v3` (Customer/Driver/Merchant/legacy application and backend source) and `merapplications-sketch/talabot-tailadmin-review` (Admin UX). Respect separate source histories and branch ownership.
- Current business priority: **trial-launch preparation using existing features**, NOT broad new feature development.
- Competitor benchmarking is a **research backlog**. Any missing feature requires source verification, business justification, cost/risk assessment, separate owner approval, then a scoped task.
- Ordering from abroad for a recipient inside Tajikistan is an **important later-phase candidate**; do not activate before the pilot gates and separate approval.

## 2. Approved product and design locks
- Preserve the approved Customer Dynamic Marketplace B, Restaurant Details v1.6 Legacy Premium, Product Customization Direction A, DineOut Premium Gold, original logo/colors; approved Admin Template B and four A KPIs, UX-02 V04, and subsequent explicit owner decisions.
- Preserve accepted PRICE/RATINGS/TIP and historical 106/107 evidence only within their verified source/test scope. No artificial re-acceptance and no repeat testing without a reason tied to changed source/environment.
- For financial policy, refer to `docs/OWNER-AGREEMENTS-AR.md` including **CASH-01, RETURN-01, SCOPE-01**. No new percentages, cash treatment, refund logic, deadlines, or retroactive balances.
- Language precedence is recorded in `docs/OWNER-AGREEMENTS-AR.md`: first visit supported browser language, later explicit choice takes precedence. Do not silently force Russian again.
- Do not use a competitor's UI as permission to redesign TALABOT.

## 3. Security and authority
- No action in production, customer data, account/MFA/roles, Supabase/SQL, Cloudflare, money, secrets, service keys, hosted scripts, backups/restores, merges or deployments without **specific owner authorization** and assigned-role boundaries.
- Read-only tasks never create comments, issues, files, commits, tests with real writes, or deployments.
- QA uses synthetic data and an independently isolated approved environment; if unavailable, record BLOCKED/UNTESTED instead of improvising a hosted test.
- The public **static, fake-data Safari visual demo** and the formal **C-01 Auth/profile test** are separate tracks; static visual success never proves C-01 or production readiness.
- No paid resources, subscriptions or owner technical setup requests without a decision. Don't conceal needed blockers.

## 4. Avoid duplication and cross-team collisions
- Check newest HEAD, current Issue #26, task issue, prior evidence, active work and unrelated branch changes before proposing work.
- Manager assigns **one next responsible role at a time**; programmer implements only approved deltas, designer owns visual proposals, auditor verifies independently, publisher handles only authorized publication.
- Never claim that GitHub issue creation automatically starts a paused ChatGPT Work conversation.
- Existing approved work remains frozen until a precise request authorizes a change. No blanket refactor, dependency installation or new feature while fixing a P1/P2 defect.

## 5. Quality and evidence
- A feature is classified as: `CONFIRMED_SOURCE`, `VERIFIED_RUNTIME`, `PARTIAL`, `NOT_FOUND_IN_INSPECTED_SCOPE`, `BLOCKED`, or `FUTURE_CANDIDATE`.
- Each defect: steps, expected/actual, source SHA, environment, severity, reproduction, evidence URL, status, owner, minimal next test/fix, regression evidence.
- For test results use only PASS/FAIL/PARTIAL/BLOCKED/UNTESTED with actual denominators. Missing evidence is not evidence of absence.
- Report user-visible progress as concise actions and final conclusions; never claim hidden reasoning guarantees correctness.

## 6. Stop conditions
STOP and escalate to the manager/owner if:
- An instruction conflicts with a locked owner agreement.
- A test may reach production, finances, private information, or an unknown backend.
- SHA/candidate identity or deployment provenance is unknown.
- A P0 security/data-integrity risk is detected.
- A role is asked to perform outside its mandate or an unapproved publish/merge/change.
