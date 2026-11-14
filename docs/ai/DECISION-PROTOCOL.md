# TALABOT — Evidence-First Decision Protocol

Status: **PROPOSED FOR OWNER APPROVAL**. This is an observable work method and decision log, **not** a request to expose or override the AI's private chain of thought.

## Single current objective
Make the currently approved TALABOT features testable and safe for a **limited pilot**, then consider later roadmap features under separate owner authorization. Do not equate an earlier Safari screenshot with production or full pilot acceptance.

## Required sequential workflow
1. **Intake:** Write the user goal in one sentence, role, exact task/issue, allowable actions, prohibited actions, and single deliverable.
2. **Recover:** Read latest Issue #26 + current relevant issue, owner agreements, continuity, current branch HEAD and existing evidence. Note source-vs-live differences. Do not re-run completed valid tests.
3. **Classify:** Is this (A) current bug/risk, (B) existing incomplete feature, (C) unverified claim, (D) new feature proposal? Do not turn C or D into implementation.
4. **Prioritize:** First security/data access and financial integrity; then duplicate or impossible order/driver states; then customer/driver/merchant workflows; then launch UX; finally optional new features. Severity P0–P3 requires evidence, not intuition.
5. **Design test:** Specify case ID; preconditions; **synthetic** input; precise action; expected state including financial/role effects; negative/retry/race cases; required logs/screenshots; environment boundary and cleanup.
6. **Execute only when authorized and safely possible.** Otherwise output BLOCKED with exact missing prerequisite. Keep source-only findings separate from real device/browser E2E.
7. **Minimal correction only if owner/task authorizes:** one isolated branch, one precise fault, no changes to protected design or financial agreements; verify failing-before, passing-after and relevant regression. Separate reviewer signs off.
8. **Launch gate:** Manager consolidates functional QA, independent security, finance reconciliation, source-to-deployment mapping, restore/recovery evidence and physical Safari user experience. Production release remains NO-GO until specific approval is documented. Approval of a fake static preview does not authorize a live pilot.
9. **After pilot:** Record validated operational learnings and only then submit a proposal for staged new features: abroad purchaser → local recipient is high-interest, with identity, fraud, foreign payment, conversion, recipient privacy, disputes and reconciliation specified **before development**.

## Standard decision record (one per finding)
- Date / Task / Owner role
- Repository / branch / exact SHA / runtime URL if proven
- Scope and prior accepted evidence reused (cite URLs)
- Classification A/B/C/D, severity and confidence
- Expected vs actual, tested cases and counts
- Test evidence / screenshot / log / source lines
- What is established, what is *not* established
- Recommended next **single** role and specific action
- Approval needed and STOP conditions

## Concrete example: duplicate delivery confirmation
- Classification: A (source-identified risk; no live incidence claimed)
- Test: in an isolated fake-data environment, two rapid confirm actions plus timeout/retry at the same order and delivery state
- Required PASS: exactly one final delivery transition and one financial ledger side effect; no second collection or payout
- If no suitable isolation exists: `BLOCKED`, never `PASS`
- Do not modify delivery or CASH-01 rules until the authorized minimal fix is specified and independently reviewed

## Pilot-to-roadmap decision rule
Approve a new feature only with: `confirmed absence + user value + dependency/cost + security/financial risk + acceptance criteria + owner authorization`. Competitor features and descriptive documents are never an approval by themselves.
