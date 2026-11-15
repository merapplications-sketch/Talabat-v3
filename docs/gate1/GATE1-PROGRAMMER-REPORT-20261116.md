# TALABOT — Gate 1 programmer delivery / F01–F04 — 2026-11-16

**Controlling owner-approved scope:** [Issue #48 comment 6900524996](https://github.com/merapplications-sketch/Talabat-v3/issues/48#issuecomment-6900524996), [exact brief](https://github.com/merapplications-sketch/Talabat-v3/blob/8188fe2cc6b7f9d006719243345b1cb8dbf2566c/docs/management/GATE1-PROGRAMMER-BRIEF-20261116.md), master #26. **Role:** programmer only.

**BASE_SHA:** `09ef07fd29fb5c5a3e323c23c7331e577567ab1e` on `tech/v82-int`, verified before work; protected `main` untouched.  
**Candidate branch:** `dev/gate1-f01-f04-20261116`.  
**FINAL_SHA:** recorded by the containing Git commit; verify current branch HEAD and compare the exact changed files.  
**Status:** **SOURCE PATCH PREPARED; GATE1 E2E BLOCKED / QA NO-GO / RELEASE NO-GO / PHASE2 NO-GO.** No deployment, no DB migration, no cloud changes.

## Scope and surgical changes

| ID | File/function | Result / test boundary |
|---|---|---|
| F01 / D-02, D-07 | `driver.html`: `shiftAck`, `startShift`, `endShift`, `ping` | Shift transitions gated by `driver_ping` ACK (8-second timeout); cannot display Online before ACK; failed/timeout ON remains offline, failed OFF retains online; heartbeat fail-closed/offline and toast. Existing visual layout preserved. |
| F02 / D-10, D-14, B-07, B-10 | `talabat-core.js`: `gate1DeliveryFlights`, `deliver`; proposed SQL `deliver_order` | Share one in-flight promise per order; server `SELECT FOR UPDATE`, pickedup-only single transition, identical completed retry returns without second UPDATE/trigger/financial receipt. Nonidentical completed replay raises `already_delivered`. **Not proven against Postgres concurrency.** |
| F03 / D-11 | `driver.html`: `chatDraftGet/Set`, `sendChat`, `chatSheet` | Courier draft isolated by driver/order key, persisted in local storage, retained on rejected insert/reload, cleared only after server insert ACK. Existing quick-chat and display components unchanged. |
| F04 / D-08 | `driver.html` `confirmDeliver`, `talabat-core.js` `reportDriverCashShort`; proposed SQL `report_driver_cash_short` | Reject under-collected cash as delivered at **client and server**; separate assigned-driver-only support ticket, no delivery/financial write; exact amount may complete; Q13 precision fail-closed; over-collected path deferred to Q09–13 contract / independent financial verification, not credited or auto-adjusted. Q14 Option A retained. |
| Original CASH-01/PRICE/RETURN/financial SQL | unchanged | No settlement/accounting/trigger replacement or adjustment; no old completed order modified. |

### Relevant source files and rollback

- `driver.html` original Git blob `4621f280711ddba411a18a499883654bfcccc0f5`, proposed blob `8ddce269b27a6a697a75cd2d3ff430d0b592078b`. Original `customer.html` and `merchant.html` unchanged.
- `talabat-core.js` original `41034f64fc27ae6323499d0f28e29716aeb66498`, proposed `daa9564c694c8f152e2cfade19607ad739fe9ee8`.
- SQL only `sql/proposed/gate1_cash_and_idempotent_delivery.sql`, blob `782efd4ba9e04eb27d0df5136faf8ccdb1474693`. **This SQL has never been executed**; it is an independent security/financial acceptance candidate. `sql/schema_patch34.sql` stays untouched.
- One `tools/check_all.sh` runs tests + existing core check + real-E2E gate; the 11-case gate **always refuses to assert PASS without authentic requests to verified `talabot-test`**. A fail-closed marker is not an E2E test implementation.
- `docs/CODE-MAP.md` gives source-function list. `.github/workflows/gate1-20261116.yml` is restricted to this branch, no cloud secrets injected.

**Rollback for this review candidate:** delete/revert this isolated branch after a PM review. Do not rollback any deployment, main, Supabase or production application; none was touched.

## Available validation vs unavailable real verification

- Original 10 inline `driver.html` JavaScript sections parsed by V8 `new Function`: **PASS syntax only**.
- Updated `talabat-core.js` parsed by V8: **PASS syntax only**.
- Proposed SQL is **source-reviewed only** for correct row lock/authorization, Q14 undercash rejection, replay no-update, support ticket and GRANT; no Postgres parser/transaction execution, no migration application.
- `tools/gate1_contract_checks.cjs` has four named fixture/source-function checks (F01–F04). Their existence and syntax validation are NOT proof of passed execution. The permitted single command is `bash tools/check_all.sh`; it fails with a nonzero code if any mandatory step is unavailable.
- `tools/core_contracts_check.py` remains source-original; its Node QR/jsQR+Chromium dependencies need a prepared test runner. A missing dependency is **BLOCKED**, not skipped/pass.
- No physical Safari or current root release regression tests claimed; previously accepted owner visual work is preserved and is outside this task.

### Eleven required E2E scenarios — 0 executed, 11 blocked

| Gate1 case | Legacy 51-case IDs | Required isolated test | Actual |
|---|---|---|---|
| G1-E01 | C-11/C-14/B-04 | Customer submits cash order | BLOCKED |
| G1-E02 | B-07/C-15 | Restaurant accepts order | BLOCKED |
| G1-E03 | D-02/D-07 | Driver Online after ACK | BLOCKED |
| G1-E04 | D-03 | Driver accepts offer | BLOCKED |
| G1-E05 | D-06 | Driver pickup | BLOCKED |
| G1-E06 | D-08/D-09 | Exact-cash delivery | BLOCKED |
| G1-E07 | D-10/D-14/B-07/B-10 | Two simultaneous confirmations + replay after COMMIT, one receipt/ledger effect | BLOCKED |
| G1-E08 | D-08/B-07 | Under-collection Q14 rejects delivery + creates authorized support report | BLOCKED |
| G1-E09 | D-11 | Driver chat success, failed insert, reload retention | BLOCKED |
| G1-E10 | C-16 | Customer tracking updates | BLOCKED |
| G1-E11 | B-03/D-01 | Cross-account order / unauthorized driver negative RLS | BLOCKED |

### Exact test-environment blocker and safe unblock

The connected Supabase account currently lists only three projects: primary `Talabat`, historic `TALABOT isolated pilot 20261106`, and an inactive earlier `Talabat-tj`; **none is the separately approved `talabot-test`**. All existing projects are excluded. No SQL, E2E, account creation, secrets, login or financial transactions were attempted there. The available Supabase creation tool requires **explicitly selected organization** and separate confirmation of any quoted nonzero cost. The brief authorizes **only $0 / free** and forbids inferring an existing project is a test substitute. This session has not received a named authorized organization choice; therefore no new project was created. GitHub environment secrets are likewise unconfigured/not accessed here.

**Minimal owner/PM decision gate:** PM confirms the intended Supabase organization for new `talabot-test` (the connected account currently exposes one organization) and that creation is truly **$0**, then authorizes test-only schema/fixtures/isolated runner. If project creation quotes any charge, **STOP**. After provisioning, a true 11-case HTTP/Auth/RLS/Postgres concurrency runner (not the fail-closed marker) must be implemented and executed, then obtain an independent financial/security review of `SECURITY DEFINER` functions, ticket authorization, duplicate receipts and Q09–14 before acceptance. Do not request primary/pilot service credentials.

### Honest completion classification

- **Source changes**: prepared on a separate candidate for PM review, *not* approved/integrated into operational code.
- **Four regression scripts**: staged but pending actual execution on matching GitHub branch/runtime.
- **Required 11 live E2E**: **0/11** — BLOCKED by absent approved test DB/fixture.
- **Security/finance/role acceptance**: pending separate independent auditor.
- **GO/NO-GO:** NO-GO for Gate1 closure, merge, deploy, primary pilot and PHASE2.

**No unauthorized changes:** protected original design, approved Driver A/B, Home B, Restaurant v1.6, Customization A, DineOut Gold, Q09–Q17, CASH-01, RETURN-01, SCOPE-01, PRICE/RATINGS/TIP/106/107, patch37–40, production data, main and external projects all untouched.
