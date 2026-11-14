# TALABOT — AI Operating Playbook | Owner Review Draft

**Compiled:** 14 November 2026 (Asia/Dushanbe)
**Status:** ISOLATED GITHUB DOCUMENTATION REVIEW CANDIDATE — NOT MERGED OR RELEASED.  
**Authority:** owner-approved decisions in their original sources take precedence. The AI playbook is an organizational proposal, not a new policy approval.


## START HERE — owner pilot release coordination (2026-11-14 latest)
- [Unified Owner Pilot / team continuity / who does what](docs/management/OWNER-PILOT-CONTINUITY-AND-RELEASE-20261114.md) — current single master operational status, how to continue across chats, owner first-pilot decisions and anti-duplicate rules.
- [Must-pass pilot test gates and source-confirmed P1 triage](docs/qa/OWNER-PILOT-SHOWSTOPPERS-20261114.md) — includes live tracking customer/driver/admin, money/order integrity, safety, device QA.
- [Apps on Google Play/App Store; merchant/admin delivery; repository-private transition](docs/release/PLATFORM-DISTRIBUTION-AND-REPO-PRIVACY-20261114.md).
- [Future features only after owner approval](docs/roadmap/OWNER-PRIORITIZED-PROPOSALS-20261114.md) — abroad payer → Tajik recipient, e-commerce merchant portal, promotions push, do-not-knock, kilometer meter and global comparison, carefully separated from the pilot.
- **Latest verified active stage**: [Stage18 approved](https://github.com/merapplications-sketch/Talabat-v3/issues/44); [Stage19 OPS publisher #45](https://github.com/merapplications-sketch/Talabat-v3/issues/45) has the only current task for a separate FREE synthetic Safari preview under strict security gates. **Not product launch**. Check Issue #26 latest comments on every resumption; previous Stage13-only checkpoint below is historical.
- Both GitHub repositories currently **PUBLIC**, owner requests Private conversion **after accepted first version**, with security and release/links review beforehand. **No automatic conversion**.
- The owner requested repair of proven P1/P2 pilot blockers, but no programmer test or actual source fix is claimed by this documentation upload. Keep Stage19 current single executor; then request independently proven minimal fixes in isolated branches and regression evidence. No merge/publish/financial changes without separately scoped authorization.

## Purpose
Use the screenshot's `RULES.md + SKILL.md + method` idea as an **evidence-first team operating system**, not as a claim that AI instructions eliminate code defects or override pre-existing owner agreements. The explicit owner business priority is **launch a controlled pilot using existing approved TALABOT features**, then consider staged enhancements. Ordering from abroad for a local recipient is an important **future feature** to research after pilot readiness, not an authorized current change.

## Contents
- `AGENTS.md` — small agent entry point (proposal).
- `docs/ai/RULES.md` — non-negotiable authority, safety, approved decisions and no duplication.
- `docs/ai/DECISION-PROTOCOL.md` — observable decision process and evidence requirements, not private AI reasoning.
- `.agents/skills/talabot-pilot-readiness/SKILL.md` — role-aware step-by-step audit procedure.
- `docs/launch/PILOT-GATES.md` — staged release-readiness gates; static demo is NOT the live pilot.
- `docs/launch/RISK-AND-TEST-PRIORITIES.md` — focused existing-feature risk tests and exit criteria.
- `docs/roadmap/POST-PILOT-PROPOSALS.md` — controlled future roadmap including abroad→local recipient.
- `OWNER-HANDOFF-TO-MANAGER.md` — one ready-to-send instruction for the TALABOT manager.

## Historical checkpoint (Stage13 — superseded operationally by START HERE)
- Master management register: https://github.com/merapplications-sketch/Talabat-v3/issues/26
- Stage13 programmer delivery: https://github.com/merapplications-sketch/Talabat-v3/issues/39
- Stage13 isolated demo source: `review/safari-stage13-demo-lang-p2-20261114` at `3f74b29a7c4bcc89cef9e25dd73f574448ab7896`.
- Stage13 8/8 source simulations passed for RU/EN, **not full browser or real Safari**.
- Formal current-source integrated E2E **0/51**, admin E2E **0/21**, all six G1 gates not fully accepted. **RELEASE NO-GO / PHASE2 NO-GO.**

These historical values were last read on 14 November 2026; assigned managers must recheck HEAD/comments before starting new work. The linked reports are controlling references within their accepted scope.

## Installation safety
This packet belongs **only to its isolated documentation review branch**. Review it against existing owner decisions before considering any merge into an approved branch. GitHub publication of these files is not a release and does not approve a product change. Writing files does not start ChatGPT Work agents, and a `SKILL.md` file is not automatic tool permission.

## Team entry points added for continuity
- [`docs/ai/OWNER-DECISION-SOURCE-MAP-20261114.md`](docs/ai/OWNER-DECISION-SOURCE-MAP-20261114.md): precise links to existing approvals, owner new priorities, present blockers and evidence; **not** a substitute for full originals.
- [`docs/launch/PILOT-EXECUTION-ORDER-20261114.md`](docs/launch/PILOT-EXECUTION-ORDER-20261114.md): gate-by-gate plan with an explicit **one-role-next** workflow.
- [`docs/research/TALABOT-Competitive-Features-Risks-20261114.md`](docs/research/TALABOT-Competitive-Features-Risks-20261114.md): previously authored RoaQ/talabat/Uber Eats/global comparison and risk catalogue, with future features classified as **proposals**.
- [`docs/research/TALABOT-Competitive-Features-Risks-20261114.html`](docs/research/TALABOT-Competitive-Features-Risks-20261114.html): formatted read-only companion.

## How to review or edit
In GitHub open the dedicated review branch, select any `.md` file and use the pencil **Edit this file** control. Commit revisions **to the documentation review branch**, not `main`; keep corrections scoped and record the source of every changed approved term. Use the linked master Issue #26 for team handoff and the next assigned issue for execution.

## Operational capacity and security — review-only extension (2026-11-14)
- [Proactive Capacity, Resilience & Security Plan](docs/launch/PROACTIVE-CAPACITY-RESILIENCE-PLAN-20261114.md): headroom monitoring, early warning, admission control philosophy, low-load options, disaster recovery, security gates, staged synthetic CAP-01..CAP-12 tests and source references. **This is a review-only proposal, not a deployment, billing authorization or amendment of accepted G1/financial policies.**
- **Owner monitoring note:** a separate hourly ChatGPT condition check is configured as supplemental surveillance; provider-native, minute-level alerts and live capacity instrumentation have NOT yet been established. Do not treat hourly checks as outage prevention.

## Admin alerts, free hosting choice, data-loss protection — owner review (2026-11-14)
- [Dedicated admin alert, Cloudflare-vs-Supabase Free and 24-risk data-safety specification](docs/launch/ADMIN-ALERTS-FREE-HOSTING-DATA-SAFETY-20261114.md). Adds **independent external alerts + TailAdmin incident record** as a product requirement for future technical approval; **not yet implemented**. No paid subscription, production changes, release, traffic tests or policy overwrite. See the existing capacity/resilience and owner decision references.
