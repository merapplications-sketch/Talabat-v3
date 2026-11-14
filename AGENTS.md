# TALABOT — Agent Entry Point

Status: **PROPOSED FOR OWNER APPROVAL**. This file is a lightweight entry point, not a new source of product policy. Applicable only to the repository in which it is checked in.

## Before every task
1. Identify your role, the owner's exact task, its scope, and permitted actions. An issue or file does not activate a paused agent; an actual active role/channel must receive the task.
2. Read `docs/ai/RULES.md` and `docs/ai/DECISION-PROTOCOL.md`.
3. Check the **latest** [master management issue #26](https://github.com/merapplications-sketch/Talabat-v3/issues/26), its latest comments and any specifically assigned issue; check the current SHA and candidate branch. SHA values in historical documents are checkpoints, not assumed current heads.
4. Consult the existing owner decisions `docs/OWNER-AGREEMENTS-AR.md`, the administrative continuity `docs/continuity/PHASE1-CURRENT.md`, and evidence specific to the module. Do not duplicate or supersede these sources.
5. Treat source, tests, deployed application, and owner approval as **different evidence levels**.

## Default operating mode
- Prioritize **existing-feature pilot readiness**, safety, financial correctness, and verified UX over new feature development.
- No autonomous code, design, financial, SQL, authentication, access-control, infrastructure, merge, deployment, or production-data changes.
- Read-only means no GitHub mutation, no environment writes, and no tests that might touch live systems.
- Do not touch other projects or combine TALABOT's application repository and TailAdmin code casually.
- Preserve prior owner-approved design and business decisions. On conflict: stop, cite the conflicting approved sources, and request an explicit owner decision.
- The proposed future **abroad-to-local-recipient ordering** remains a prioritized future candidate, **not** a pilot-scope authorization.

## Skill
Use `.agents/skills/talabot-pilot-readiness/SKILL.md` for pilot-readiness review, risk triage, and test evidence only when the task requires it. A skill is an executable *procedure*, not permission to change the product.

## Handoff
Report: role and task ID; exact repo/branch/SHA; what was actually read or executed; PASS/FAIL/PARTIAL/BLOCKED/UNTESTED; evidence links; risk; owner of next step; owner approvals required. Never convert a planned test into a PASS.
