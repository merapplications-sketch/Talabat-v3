# TALABOT — Claude / ChatGPT Work Continuation Entry Point
**STATUS:** Documentation-only **proposal** on isolated owner review branch `docs/owner-pilot-ai-playbook-20261114`; not merged into `main`. Reading this file is not permission to modify, deploy, test live services or spend money.

**Start with this exact recovery guide:** [Cross-chat / Claude handoff](docs/management/CROSS-CHAT-CLAUDE-HANDOFF-20261114.md). Its operational snapshot is dated and MUST be updated from the newest [MASTER Issue #26](https://github.com/merapplications-sketch/Talabat-v3/issues/26), current assigned Issue, and HEAD **before** acting.

## Role, authority, workflow
- TALABOT only: `merapplications-sketch/Talabat-v3`; UX/Admin `merapplications-sketch/talabot-tailadmin-review`. Never touch Smile Up or silently mix branches.
- Owner-approved decisions in [the original agreement document](docs/OWNER-AGREEMENTS-AR.md), [PM continuity](docs/continuity/PHASE1-CURRENT.md) and Issues are controlling, not this condensed guide. **Approved locks never change without explicit owner permission**.
- **PILOT FIRST:** current accepted Customer/Driver/Merchant/Admin quality, finance, security, live tracking for customer/driver/authorized admin, recovery/capacity. Future features are backlog, require separate owner go.
- **One current executor** at a time (unless manager distinctly assigned independent, non-overlapping work), precise Issue and SHA, independent reviewer, evidence and manager acknowledgement. Do not repeat accepted test runs unless their source/env evidence is invalidated.
- No autonomous merges/deployments, production or Supabase/Cloudflare/SQL/account/financial/security changes, new services, packages or paid resources. Only execute an owner-authorized scoped task on appropriate isolated branches.
- Classify `VERIFIED_RUNTIME` vs `SOURCE_ONLY` vs `UNTESTED/BLOCKED`. Do not confuse screenshots or JS simulations with server E2E. No false `PASS`, zero-loss/invulnerability claims.
- **VERIFIED historical test standard**: the owner's remembered 'Awas/AVAS' means **OWASP ASVS 5.0.0 Level 2**, applied as a checklist/reference by prior Work/manager/technical review, not a scanner. The 2026-11-09 owner-held Work handoff recorded 345 historical ASVS items: 1 PASS, 2 FAIL, 330 UNTESTED, 12 N/A; not today's production evidence. AVA JS runner and OWASP ZAP are *different* tools, not proven used. See [historical security evidence map](docs/qa/OWASP-ASVS-L2-HISTORICAL-VERIFICATION-20261114.md) and [tooling inventory](docs/qa/TEST-TOOLING-REALITY-20261114.md). Do not copy sensitive historical raw security results to public GitHub or re-run old tasks blindly.

## References
- [Entry and approvals: AGENTS.md](AGENTS.md) · [Rules](docs/ai/RULES.md) · [Decision protocol](docs/ai/DECISION-PROTOCOL.md)
- [Pilot gate matrix](docs/qa/OWNER-PILOT-SHOWSTOPPERS-20261114.md) · [Protected readiness plan](docs/launch/PILOT-EXECUTION-ORDER-20261114.md)
- [Capacity alerts and protection](docs/launch/PROACTIVE-CAPACITY-RESILIENCE-PLAN-20261114.md) · [Free hosting and admin alerts](docs/launch/ADMIN-ALERTS-FREE-HOSTING-DATA-SAFETY-20261114.md)
- [Store distribution and eventual repo privacy](docs/release/PLATFORM-DISTRIBUTION-AND-REPO-PRIVACY-20261114.md) · [Later proposed features](docs/roadmap/OWNER-PRIORITIZED-PROPOSALS-20261114.md)
- **Currently documented next publisher scope:** [Stage19 #45](https://github.com/merapplications-sketch/Talabat-v3/issues/45) with owner's [#44 consent](https://github.com/merapplications-sketch/Talabat-v3/issues/44); check latest comments, especially after Cloudflare reconnection. No verified public synthetic Safari URL yet in last inspected evidence.

**Always hand off before context/tool limit:** write latest accepted SHA, exact blocker, one next authorized role, PASS/FAIL/BLOCKED counts and evidence URLs to GitHub; update cross-chat recovery guide when source changes. Do not assert future ChatGPT Work conversations will start automatically.

## New security/ops update (2026-11-14)
- [Current OWASP ASVS 5.0.0 L2 pilot security gates](docs/qa/OWASP-PILOT-SECURITY-EXECUTION-GATES-20261114.md): 12 scoped groups, no testing or new security finding from this documentation. Historical 345 rows are a private owned source not proven pushed; do not re-run or leak raw historical evidence.
- [Stage20 #46](https://github.com/merapplications-sketch/Talabat-v3/issues/46) was BLOCKED by the officially undocumented JWT auth transfer in the connected Pages Direct Upload mechanism, no new Pages project/url or file upload; earlier Stage19-only state above is superseded by newest master #26. Do not keep looping on ZIP/Git App/asset upload attempts without new supported capabilities and permission.
