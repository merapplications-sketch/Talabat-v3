# TALABOT — Proposed AI Team Rules

Status: Review draft stored on an isolated docs branch. These are proposed guardrails, not replacements for previously approved terms.

## Source of authority
1. The owner's explicit approved decisions and later approved amendments prevail over this file.
2. Refer to [OWNER-AGREEMENTS-AR](../OWNER-AGREEMENTS-AR.md), [MASTER #26](https://github.com/merapplications-sketch/Talabat-v3/issues/26), [PHASE1-CURRENT](../continuity/PHASE1-CURRENT.md) and [SOURCE-OF-TRUTH](../owner-playbook/SOURCE-OF-TRUTH.md). Do not silently replace or summarize away approved rules.
3. Preserve source and acceptance histories of main TALABOT and separate talabot-tailadmin-review UX repository.

## Product and delivery locks
- Pilot-first: test and stabilize existing approved customer, merchant, driver and administration capabilities before discussing new competitor features.
- Approved Customer UI: Dynamic Marketplace B, Restaurant Details v1.6 Legacy Premium, Direction A customization, DineOut Premium Gold, original Russian logo/brand. Approved Admin Template B, original A KPI four-card strip, V04/UX-02. Later explicit owner decisions remain binding.
- CASH-01: courier pays restaurant upfront, collects order, retains paid meal amount and own delivery share; owes platform only the platform delivery share. Restaurant commission is distinct. No invented percentage or retroactive financial adjustment.
- RETURN-01: claims remain open until actual funds are received and recorded. SCOPE-01: cash pilot is independent of any electronic payment work. No new rules without owner approval.
- Language: first supported browser language RU/EN, stored manual choice takes precedence; unsupported language falls back to RU. Never force RU after a stored selection.
- Honor previously approved PRICE/RATINGS/TIP, source 106/107 and historical tests at their exact accepted scope.

## Safety
- NO unauthorized production changes, merges, deployments, SQL, RLS, Supabase/Cloudflare, credentials, MFA, roles, storage, refunds, settlements, real data or cost.
- Synthetic Safari visual-only demo and formal C-01 Auth/profile E2E are separate tracks. A safe visual demo is not proof of release readiness.
- No new test installations, paid resources, live API traffic or secret access absent a scope-specific approval.
- Independent tests use approved isolated test environments only; if unavailable, record BLOCKED, never PASS.
- On SHA mismatch, financial/role conflict, production contact risk or P0 suspicion, STOP and escalate.

## Team process
- Check latest assigned issue, existing branch HEAD, previous evidence and in-progress work first. Avoid duplicate investigation, replacing newer commits or reopening accepted work without a specific invalidation.
- Manager dispatches a single next role. Programmer codes approved deltas only; designer proposes UI changes only; auditor checks independently; publisher acts only on release approval.
- A file, issue or comment does not activate an idle ChatGPT Work agent.
- Report status precisely as PASS, FAIL, PARTIAL, BLOCKED or UNTESTED. Every finding: SHA, environment, repro, expectation/actual, P0-P3, evidence, accountable role and next action.

## Future features
- Ordering from outside Tajikistan for a recipient in Dushanbe is high-priority post-pilot **research**, not approved implementation.
- Compare competitor functions as CONFIRMED SOURCE, VERIFIED RUNTIME, PARTIAL, NOT FOUND IN INSPECTED SOURCE, or FUTURE CANDIDATE. Do not build an already existing feature a second time.