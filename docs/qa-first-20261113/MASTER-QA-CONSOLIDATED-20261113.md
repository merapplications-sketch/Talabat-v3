# TALABOT — تقرير إدارة الجودة الموحّد / FULL PROJECT QA FIRST
**إصدار إداري:** 2026-11-13 / Asia-Dushanbe · **Owner directive:** [Issue #26](https://github.com/merapplications-sketch/Talabat-v3/issues/26)
**الحكم الحاكم:** **DISCOVERY HANDOFFS 5/5 RECEIVED; FULL PROJECT QA NOT COMPLETED; RELEASE NO-GO; PHASE2 NO-GO**.
هذا التقرير يجمع أدلة خمس مراحل في سجل واحد. قبول تقرير دور لا يعني اعتماد التطبيق أو ثبوت تشغيل أي حالة غير منفذة.

## 1 — مصدر الحقيقة والحماية
- مشروع العميل/السائق/المطعم/الإدارة القديمة: `merapplications-sketch/Talabat-v3`, PM source ref `1cb85361d698d5da787d927a4c9ae7bd213c68c1` على `docs/phase1-operational-coordination-20261111`. ليس إثباتًا أنه الإصدار المنشور.
- TailAdmin candidate: `merapplications-sketch/talabot-tailadmin-review`, `review/ux02-v01-v05-candidate-20261112`, SHA `254757fab9d5fa80bffe22fa30de5e65aac2f153`. لا استخدام تلقائي لـmain بدلاً من المرشح.
- PRICE/RATINGS/TIP و106/107 وsource35 المقبولة تاريخياً محفوظة وفق حدود المصدر والبيئة. لا تكرار بلا invalidation محدد.
- Dynamic Marketplace B, Restaurant Details v1.6 Legacy Premium, Customization Direction A, DineOut Gold, original logo/colors, Admin Template B / 4 KPI A, UX-02 V04, والتعديل الأبيض الصغير على سطر واحد لزر الإشعارات = LOCKED.
- ممنوع تغيير main/إنتاج/حسابات/MFA/أدوار/بيانات/الطلبات التشغيلية #1/#2/#3 أو المستحق #3، ولا SQL/دمج/نشر/force push/استعادة أو تعديل مالي. كل تقرير على فرع توثيقي مستقل فقط.

## 2 — الاستلام والفحوص المنفذة
| المرحلة | المسئول والتكليف | التقرير والـCommit | نتيجة الإدارة |
|---|---|---|---|
| 1 | Programmer [#27](https://github.com/merapplications-sketch/Talabat-v3/issues/27) | [Stage1 55a3fa51](https://github.com/merapplications-sketch/Talabat-v3/blob/55a3fa5113202afdc3604179fd4a4919043dd11f/docs/qa-first-20261113/PROGRAMMER-STAGE1-QA-REPORT.md) | ACCEPTED DOCUMENTATION / functional E2E 0/51 |
| 2 | Independent technical [#28](https://github.com/merapplications-sketch/Talabat-v3/issues/28) | [Stage2 ea06d61d](https://github.com/merapplications-sketch/Talabat-v3/blob/ea06d61d349667f0a1135b63d923cc756159cc3d/docs/qa-first-20261113/INDEPENDENT-TECHNICAL-STAGE2-QA-REPORT.md) | ACCEPTED INDEPENDENT SOURCE REVIEW / G1 incomplete |
| 3 | Publisher [#29](https://github.com/merapplications-sketch/Talabat-v3/issues/29) | [Stage3 beabf741](https://github.com/merapplications-sketch/Talabat-v3/blob/beabf7417a982df622b4acf711750e1bc1b0ca8a/docs/qa-first-20261113/RELEASE-DEPLOYMENT-STAGE3-QA-REPORT.md) | ACCEPTED READ-ONLY REPORT / release readiness NO-GO |
| 4 | Designer [#30](https://github.com/merapplications-sketch/Talabat-v3/issues/30) | [Stage4 5ff9e8c5](https://github.com/merapplications-sketch/talabot-tailadmin-review/blob/5ff9e8c50886ac772b722c812c8144b058f2deed/docs/qa-first-20261113/DESIGNER-STAGE4-UIUX-QA-REPORT.md) | ACCEPTED SOURCE INVENTORY / executable UX blocked |
| 5 | Independent UX auditor [#31](https://github.com/merapplications-sketch/Talabat-v3/issues/31) | [Stage5 f2b18e44](https://github.com/merapplications-sketch/talabot-tailadmin-review/blob/f2b18e44a79db090a0c0d2ed715b5ee1ea9dad73/docs/qa-first-20261113/INDEPENDENT-STAGE5-UIUX-QA-REPORT.md) | ACCEPTED INDEPENDENT EVIDENCE REVIEW / executable UX blocked |

All five stage-report commits were verified as **one added Markdown report each** versus their pinned bases; no application code modification within these deltas. This proves change scope **on those commits only**, not unknown local state or all repo history.

### Strict actual test coverage, distinct denominators
- Current exact-source integrated functional E2E: **0/51** (20 customer + 14 driver + 17 backend scenarios). Stage1 statuses: PARTIAL 24 / BLOCKED 21 / UNTESTED 6; no new functional PASS or FAIL.
- Stage1 deterministic **static source assertions**: **9 PASS / 5 FAIL of 14**. Two failures relate to one delivery in-flight lock; findings are four, not five independent incidents.
- Designer source-presence checks **10/10** independently corroborated by auditor (source only; 0 runtime PASS). No execution of matrix.
- Admin route templates **37** in tree = **17 operational + 4 QA/review + 16 auxiliary**; 0/17 operational and 0/4 QA/review inspected in a current-SHA executable (**0/21 combined**).
- Other app source-matched authenticated journeys: **0/4** (customer, driver, merchant, legacy Admin).
- Per-Admin route required widths 320/360/390/430/768/1440 × RU/EN/TG × Light/Dark = **0/36 per route**, not project-wide tally; long names/loading/error/offline/denied/focus/touch/modal/return all untested in this run.
- Historic Pages login gates and historical developer screenshots/CI are separate evidence, **not added to current-source executed coverage**. Physical iPhone Safari: **UNTESTED**.

## 3 — Source findings requiring safe execution proof (not live incidents)
| ID | Risk / provisional severity | Independent evidence | What is NOT established | Next proof owner |
|---|---|---|---|---|
| F-01 / P1 | Driver UI may show Online before server ping ACK; endShift similar | Stage1+2 inspected pinned driver/core source | Real current deployed behavior, network recovery | DEV/API/QA; synthetic ping fail/timeout/reload |
| F-02 / P1 | Repeated delivery confirmation can send overlapping client RPC calls | Stage1+2 driver client handler lacks pending lock | Duplicate DB transition/payout/external receipts; candidate SQL34 row-lock exists but active writer unknown | DEV/API/DB/QA, two-session/retry-after-commit |
| F-03 / P2 | Driver chat draft cleared before remote insert acknowledgement | Stage1+2 pinned driver/core | Live session failure reproduced | DEV/QA, synthetic rejected insert/reload |
| F-04 / P1 | Candidate cash delivery allows under-collection with note, contrary to **approved Q14**; over-collection needs Q09–17 contract | Stage1+2 driver & SQL34 and [PM owner decisions](https://github.com/merapplications-sketch/Talabat-v3/blob/1cb85361d698d5da787d927a4c9ae7bd213c68c1/docs/continuity/PHASE1-CURRENT.md) | Current active SQL writer; financial loss in production | FIN/API/DB independent oracle + active-version provenance; **NO POLICY REDECISION** |
| UX5-01 / P2 | Owner-approved white normal-weight small text on orange #F36831 = **3.072:1** vs WCAG AA 4.5:1 normal text | Designer+independent source/math | Current device rendering and clipping | PM documents known tradeoff; no style changes without OWNER |
| UX5-02 / P3 | Owner single-line handoff claims image SHA256 in metrics.json, but `captures: []`; 4 JPEGs exist | Stage5 source/evidence file verification | Per-image claimed checksum/current DOM attribution | Designer evidence custodian, docs-only correction when authorized |
| UX5-03 / P3 | 21 “business pages” label imprecise: 17 operational+4 review | Stage5 route tree enumeration | Any missing/broken rendered business route | PM label correction applied here; executable QA separately |
| UX5-04 / P3 | Generic TG common keys 5/10 identical English values | Stage5 messages source parsing | Actual TALABOT business route displays them | QA source-matched UI evidence before visual defect classification |

**No reproduced production P0 and no current-release runtime failures** were established; this does **not** certify absence. Old TG320 clipping dimensions came from older button code, not current owner-chosen single-line candidate; do not reopen without source-matched measurement.

## 4 — Release and environment gate
- Historical Pages deployment/source `ca8808dd` compared to PM `1cb85361`: **5/5 executable Git blobs differ**. Demonstrates historical-vs-source difference only; **current deployed version/digest not independently proven**.
- Historical CI106 SUCCESS on `86eb978e`, not PM/source under test; TailAdmin vinext/original BUILD success on older `ed5e33af`, not UX candidate. No corresponding exact HEAD CI observed in available API.
- Supabase primary/pilot project health and pilot migration metadata were read only in Stage3. They do **not** establish frontend ↔ active writer parity, RBAC, effective financial SQL, storage permissions or transaction safety. Cloudflare current release metadata inaccessible in authorized read path; do not bypass approval.
- Active `deliver_order` writer, independent external `dispatch_tick` scheduler, request-scoped AUTH/RLS trace, keys/reconciliation, DB/PITR/Storage/object backup and compatible rollback **BLOCKED**. Historical watchdog/CI not a current scheduler/restore receipt.

## 5 — G1 decisions and blockers
| Gate | Decision | Proof required; accountable role |
|---|---|---|
| G1-A | PARTIAL | Publisher+DEV: environment→current artifact/build digest→immutable customer/driver/merchant/admin/core SHA/route/backend |
| G1-B | PARTIAL | API+DB+Jobs: active RPC versions/callers and write boundaries, independent scheduler + heartbeat |
| G1-C | PARTIAL | FIN+DB: Q09–Q17 and CASH-01 contract, independent numerical oracle, rounding/split/settlements, active writer parity |
| G1-D | BLOCKED | SECURITY+DB: synthetic request-scoped auth/RLS/role/tenant negative tests; historical TRUNCATE grant context unproven active |
| G1-E | PARTIAL | OPS+FIN: keys custody metadata, command/event/receipt reconciliation, at-most-once effects |
| G1-F | PARTIAL | OPS+CI+QA+Storage: current SHA CI, backup/PITR/object bytes+keys, restore isolation, physical Safari, safe HTTP test channel |

**0/6 G1 gates accepted.** Acceptance cannot be upgraded by new reports alone. QA NO-GO, release NO-GO, PHASE2 NO-GO.

## 6 — Correct sequential work plan (no automatic remediation)
1. **STAGE 6 FIRST — programmer, read-only/safe-local test-readiness handoff:** recover reusable immutable source/build/fixtures from **existing** repository assets and existing authorized offline QA facilities; generate a concrete, verifiable source pin, dependency/runtime/endpoint inventory, synthetic test-role/fixture specification, network-to-production denial plan and executable smoke evidence **only if** an already-provided isolated runtime allows without provisioning, auth changes, installs or source changes. Otherwise supply exact named blocker. Do not begin code fixes. Link to master; manager independently reviews before any further role is tasked.
2. Once artifact/source mapping is verified, **Publisher/OPS** supplies sanitized non-secret active-source manifests or confirms access blockers, without Cloudflare access changes. Do not reassign same audit.
3. **Independent QA** runs approved synthetic integration/browser test matrix on exact SHA, preserving earlier scopes; physical iPhone Safari is separate.
4. Only when executable evidence establishes regressions: propose narrow separate P1/P2 fixes on isolated branches with independent regression checks and owner's approval for any change beyond already fixed contract. **No merge/deploy without explicit owner approval.**
5. After owner sees unified outcomes, resume G1-A..F and UX-02 candidate deltas; PHASE2 remains NO-GO unless separately approved.

## 7 — Governance and evidence acceptance
- Developer/designer/consultant/publisher/auditor reports may be accepted **as deliverables**, not operational GO.
- Each issue: status PASS/FAIL/PARTIAL/BLOCKED/UNTESTED, P0–P3, scenario/expected/actual, source SHA, runtime environment, synthetic fixtures, unedited screenshot/log, responsibility and closure criteria.
- New test tools/add-ons, external cloud sessions, production credentials, finance/rule/role/UI changes, SQL, actual publish/restore, or modifying accepted source require separate owner authorization.
- Registration/comment on GitHub **does not awaken a paused Work conversation**. Role execution starts only after real channel receipt; no asynchronous team execution is implied by this record.
