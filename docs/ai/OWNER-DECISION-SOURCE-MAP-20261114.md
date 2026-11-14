# TALABOT — Owner Decision & Evidence Source Map
Date: 2026-11-14 (Asia/Dushanbe)  
Status: **DOCUMENTATION INDEX FOR TEAM REVIEW — not a replacement or rewrite of owner-approved agreements**

## Objective and the authority of each statement

1. **Current owner direction in this conversation (2026-11-14):** prepare TALABOT for a **controlled pilot with the features already built**, test and correct source-confirmed risks, then sequence enhancements. **Ordering from abroad for a recipient in Tajikistan** is a high-interest future priority, **not an authorization to implement it now**.
2. **Historical APPROVED decisions:** governed by original referenced files and GitHub Issue #26. No new summary, `RULES.md`, `SKILL.md` or AI output may silently replace them.
3. **Competitor ideas:** research proposals only; "not proven" is not a claim of verified absence. Do not open feature-development tickets until the manager proves the gap on the newest source with owner's separate permission.

## Authoritative original sources (read the original; do not edit via this index)

| Area | Original source | Binding or known limit |
|---|---|---|
| Master scope, approved UI locks, role separation, QA gate | [TALABOT Issue #26 and its current comments](https://github.com/merapplications-sketch/Talabat-v3/issues/26) | Existing QA-first governance; owner/product changes require explicit authorization; 0/51 functional E2E and 0/21 admin E2E at prior audit |
| Cash settlement, returns, scope and language | [docs/OWNER-AGREEMENTS-AR.md @ verified source](https://github.com/merapplications-sketch/Talabat-v3/blob/1cb85361d698d5da787d927a4c9ae7bd213c68c1/docs/OWNER-AGREEMENTS-AR.md) | **CASH-01:** courier prepays restaurant, collects total, and owes platform only its allocated delivery-fee share; restaurant commission separate, assigned split snapshotted per order. **RETURN-01:** claim remains open until cash truly received. **SCOPE-01:** cash pilot primary; electronic gateway simulation is not operational payment acceptance. Language: supported browser preference first, explicit saved user choice wins later. |
| Roadmap/manager continuity | [PHASE1-CURRENT.md @ PM branch](https://github.com/merapplications-sketch/Talabat-v3/blob/docs/phase1-operational-coordination-20261111/docs/continuity/PHASE1-CURRENT.md) | G1-A/B/C/E/F PARTIAL; G1-D BLOCKED; PHASE2 NO-GO, earlier PRICE/TIP/106/107 acceptance preserved in exact context |
| Consolidated QA and source findings | [MASTER-QA-CONSOLIDATED-20261113.md](https://github.com/merapplications-sketch/Talabat-v3/blob/0ab523782ee1bf6f69e2e3be7ec6e96394d9ce6a/docs/qa-first-20261113/MASTER-QA-CONSOLIDATED-20261113.md) | F-01 driver Online ACK; F-02 repeat deliver RPC; F-03 lost chat draft; F-04 candidate undercollection vs Q14. These are source findings, **not proven active production incidents** |
| Stage13 fake-data Safari demo | [Issue #39](https://github.com/merapplications-sketch/Talabat-v3/issues/39), [3f74b29a delivery report](https://github.com/merapplications-sketch/Talabat-v3/blob/3f74b29a7c4bcc89cef9e25dd73f574448ab7896/previews/safari-zero-cost-customer/STAGE13-P2-LANGUAGE-PERSISTENCE-REPORT.md) | Demo-only RU/EN persistence line fixed; 8/8 simulated source tests PASS. **0 real browser/egress/viewport/Safari runs.** Public demo not authorized and no confirmed new URL |
| TailAdmin authoritative UX candidate | [talabot-tailadmin-review](https://github.com/merapplications-sketch/talabot-tailadmin-review/tree/review/ux02-v01-v05-candidate-20261112) | Template B, 4 A indicators, approved UX-02 V04 and owner single-line decision protected; contrast issue documented, not a general permission to recolor |
| Current features & future comparison | [Competitive research](../research/TALABOT-Competitive-Features-Risks-20261114.md) | Planned/backlog material: **not accepted production implementation**, do not infer gaps from text search alone |

## Approved decisions to preserve exactly (do not rederive or change formulas)
- Customer: Dynamic Marketplace B, Restaurant Details v1.6 Legacy Premium, Product Customization Direction A, DineOut Premium Gold, original logo, brand colors and approved text/language selection.
- Admin: Template B with the four KPIs inherited from A, accepted UX-02 V04, and owner-approved subsequent adjustments subject to their documented contrast/UX status.
- Financial: CASH-01, RETURN-01, SCOPE-01, Q09–17 and PRICE/RATINGS/TIP decisions within their original approval records. The cash example is **not** a default percentage.
- Evidence: Preserve valid source-specific tests/recovery records; do not repeat 106/107 just because a new report was written. No new live records, finance, MFA, permission, SQL or deployment changes.

## Missing evidence and unresolved items
- Neither the synthetic Safari visual preview nor actual limited live pilot has release approval. The formal C-01/Auth test remains separate and blocked by environment isolation proof.
- Exact current deployed build/service/database/CI mapping, independent scheduler, recovery/backup and financial reconciliation are not all established; **six G1 gates remain unaccepted**.
- Candidate risk ≠ user-visible live defect. All fixes require reproducible isolated evidence and role-specific approval.

## Safe handoff rule
Before an assigned role starts, recheck newest issue comments and HEAD; then produce one delta report with source SHA, exact task, actual checks, blocked items and next **single responsible role**. Publishing an Issue or file does not auto-start ChatGPT Work.
