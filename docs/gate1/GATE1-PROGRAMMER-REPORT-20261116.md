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

### Actual branch-CI execution — source checks PASS; whole gate correctly FAILED CLOSED

**Real GitHub Actions run:** [`43758572694`](https://github.com/merapplications-sketch/Talabat-v3/actions/runs/43758572694), executable candidate SHA `cda14fae01af436997284fc9169764b66586ac94`; job `132947993005`; **conclusion: FAILURE because required gates are BLOCKED, not because four source regressions failed.**

Actual unedited job-log lines:
- `PASS F01_online_requires_ack`
- `PASS F02_single_delivery`
- `PASS F03_chat_draft_kept`
- `PASS F04_cash_q14`
- `{"result":"PASS","pass":4,"fail":0,"scope":"mocked source functions + SQL source invariants, not database E2E"}`
- `BLOCKED` preserved core-contract check: missing pinned Node QR/jsQR modules / configured path, no packages installed.
- `GATE1_E2E: 0/11 PASS, 11 BLOCKED; no HTTP/SQL request issued` because separately approved `talabot-test` does not exist.
- `GATE1_NO_GO: incomplete or failing required test gates` exit 1, **as required by the fail-closed agreement.**

**Result accounting:** F01..04 **4/4 source-function mock checks executed PASS**, including artificial failed/timeout ACK, same-promise in-flight dedup, fake chat draft reload and Q14 short-cash client refusal; **0/11 real Supabase E2E executed**, no actual SQL transactional concurrency, receipt/RLS/financial reconciliation proved, no independent security PASS. Do not equate mocked source checks with production or DB validation.


- Original 10 inline `driver.html` JavaScript sections parsed by V8 `new Function`: **PASS syntax only**.
- Updated `talabat-core.js` parsed by V8: **PASS syntax only**.
- Proposed SQL is **source-reviewed only** for correct row lock/authorization, Q14 undercash rejection, replay no-update, support ticket and GRANT; no Postgres parser/transaction execution, no migration application.
- `tools/gate1_contract_checks.cjs` executed its four named mocked source-function checks **4/4 PASS** in actual GitHub Actions run `43758572694`; this is **not** a 4/4 live DB/E2E PASS. The single command `bash tools/check_all.sh` exited nonzero as required because full gates are unavailable.
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
- **Four regression checks**: **4/4 executed PASS** under GitHub Actions `43758572694` on the pinned branch candidate; only mocked source functions + SQL source invariants.
- **Required 11 live E2E**: **0/11** — BLOCKED by absent approved test DB/fixture.
- **Security/finance/role acceptance**: pending separate independent auditor.
- **GO/NO-GO:** NO-GO for Gate1 closure, merge, deploy, primary pilot and PHASE2.

**No unauthorized changes:** protected original design, approved Driver A/B, Home B, Restaurant v1.6, Customization A, DineOut Gold, Q09–Q17, CASH-01, RETURN-01, SCOPE-01, PRICE/RATINGS/TIP/106/107, patch37–40, production data, main and external projects all untouched.

## CI FOLLOW-UP 43760749446 — Final source/core readiness checkpoint, 2026-11-16

**This section supersedes older statements above that the existing core-contract runner was BLOCKED for missing test libraries.** The previous 2026-11-15 candidate code and its F01–F04 decisions are unchanged. All Gate1 work is still confined to `dev/gate1-f01-f04-20261116`; no production, demo, main, original SQL or Cloudflare changes.

| Evidence | Actual result | Precision/limits |
|---|---|---|
| [CI 43760444297](https://github.com/merapplications-sketch/Talabat-v3/actions/runs/43760444297) at `5364fa42225069ecce8b5f74878f22f778adc8d5` | Offline core-contract tests **PASS**, F01–F04 **4/4 PASS** | Workflow-only change: pinned qrcode-generator 1.4.4, jsQR 1.4.0 and Playwright 1.57.0 installed **temporarily on public GitHub runner**, not in application |
| [CI 43760749446](https://github.com/merapplications-sketch/Talabat-v3/actions/runs/43760749446) at `18da1acf35b6f31003dd27fff1a15a1144f9e7c8` | E2E Python syntax **PASS**, F01–F04 **4/4 source-function PASS**, previously approved **C-1/C-2/C-3/C-5/C-6 PASS**, browser **no page errors** | Genuine isolated Chromium on local fixture; HTTP requests to unrelated websites were aborted by the original core-contract test route |
| Eleven Gate1 live E2E cases | **0/11 PASS, 11 BLOCKED** | CI log explicitly says `SUPABASE_TEST_URL`, `SUPABASE_TEST_ANON_KEY`, `SUPABASE_TEST_SERVICE_ROLE_KEY`, `GATE1_TEST_PROJECT_REF` absent. **No HTTP/SQL request was issued** |
| New test runner | [`tools/gate1_e2e.py`](https://github.com/merapplications-sketch/Talabat-v3/blob/18da1acf35b6f31003dd27fff1a15a1144f9e7c8/tools/gate1_e2e.py) + [preflight/fixture contract](https://github.com/merapplications-sketch/Talabat-v3/blob/18da1acf35b6f31003dd27fff1a15a1144f9e7c8/docs/qa-first-20261116/GATE1-ISOLATED-E2E-PREFLIGHT.md) | Unlike the original fail-closed marker, the script now defines **11 actual test-only HTTP/RPC cases** (cash order → merchant → driver ACK/accept → pickup → exact cash → concurrent retry → cash-short support → chat → tracking → negative RLS). **Not executed or independently validated against Postgres** |
| Test environment | **BLOCKED** | Connected Supabase Free organization shows three **existing** projects, none named `talabot-test`; no project creation, schema migration, test accounts or GitHub secret changes occurred. Actual authoritative schema baseline, explicit project-organization selection, verified no-cost creation and ephemeral synthetic fixture are required before any live test |

**Source and SQL status:** F01 driver ACK, F02 client+proposed server locking, F03 saved driver chat draft, and F04 Q14 cash shortfall guard **remain source candidates only**. The [proposed SQL](https://github.com/merapplications-sketch/Talabat-v3/blob/c1ff40b460187cd7913624d8a8bc4089716d0ec3/sql/proposed/gate1_cash_and_idempotent_delivery.sql) was **not executed**. Existing CASH-01, Q09–Q17 and approved financial rules are preserved. Core-contract **PASS** does not demonstrate the source candidate's real server concurrency or live RLS authorization.

**Whole-command result: FAIL-CLOSED / NO-GO**, deliberately, not because offline source/core tests failed. The CI job's final nonzero exit is the correct response to missing mandatory 11-case backend E2E. No QA/security/finance final acceptance or production release is implied.

**Next single blocker for PM:** Select the authorized Supabase Free organization for `talabot-test`; verify that creating a separate project costs **$0**, stop on any nonzero quote; establish the authentic test-only baseline schema and synthetic fixture; then configure only the three named GitHub Secrets and non-secret test ref. Do not reuse Talabat, the old pilot or Talabat-tj. Once real 11-case HTTP/Postgres tests execute, schedule independent security/financial review. **C-01/G1/release/PHASE2 = NO-GO** until those gates pass.

## Gate1 E2E runner contract correction (subsequent programmer-source checkpoint)

Read-only examination of the previously staged real-test harness found two **test-oracle mismatches** before any test DB was provisioned: (1) F02 SQL correctly allows identical completed retries without a second `UPDATE`, whereas the former E07 harness expected an HTTP error for that valid retry; (2) F04 SQL defines `report_driver_cash_short` and uses `support_tickets` / `ticket_messages`, while the former E08 harness called unrelated placeholder names. E09 also used the already delivered test order for a chat insert.

The test-only harness is corrected to follow the committed SQL names, assert **state + financial receipt uniqueness** and unchanged completed `done_at` on retry, require a verified finance receipt mapping in the **test-only ephemeral seed**, and run chat against a new active synthetic order. These changes affect only `tools/gate1_e2e.py` and the test preflight documentation; **F01–F04 candidate source, proposed Q14 SQL, owner-approved finances, UI, and production remain untouched**.

**Status remains 0/11 executed E2E / BLOCKED**: the independent `talabot-test` and its authoritative schema, test-only JWTs and finance receipt mapping are still absent. Nothing here upgrades existing source checks into production QA.


## GATE 1 / PROGRAMMER BRIEF-2 supersession — 2026-11-16 (schema-only → LOCAL CI)

**Exact new owner-approved instruction:** [Issue #48 comment 6901725324](https://github.com/merapplications-sketch/Talabat-v3/issues/48#issuecomment-6901725324), full [GATE1-PROGRAMMER-BRIEF-2-20261116.md](https://github.com/merapplications-sketch/Talabat-v3/blob/9f28710569064d7fab6c5c98baa49a2214c4bd10/docs/management/GATE1-PROGRAMMER-BRIEF-2-20261116.md). Overrides **only** previous cloud `talabot-test` provisioning section. Do not request a cloud organization. Everything else in original Gate1 brief remains binding.

**Actual production-schema identity (read only from pinned ORIGINAL app source):** `talabat-core.js` at `tech/v82-int` commit `09ef07fd29fb5c5a3e323c23c7331e577567ab1e`, SB_URL ref **`dzydscryrnahnneydnry`**. Public frontend publishable key was **not copied, output or used**. Supabase project `Talabat` metadata returned `ACTIVE_HEALTHY`, but that is not proof of a reachable database.

**Metadata-only production reads attempted and outcome — BLOCKED by connection:**

| Authorized schema-only retrieval | Tool/SQL family | Actual response |
|---|---|---|
| Catalog counts | `Supabase.execute_sql` against `pg_catalog.pg_class`, `pg_namespace` | `Connection terminated due to connection timeout` |
| Relation/column metadata | `Supabase.list_tables`, `public` only | `Connection terminated due to connection timeout` |
| Migration list | `Supabase.list_migrations` | `Connection terminated due to connection timeout` |
| API type introspection | `Supabase.generate_typescript_types` | `timeout exceeded when trying to connect` |

The calls returned **zero schema definitions**. **No table-data SELECT, auth.users, storage object/rows, Vault value, secrets, money, production SQL write or migration** was read or attempted. Because the baseline could not be retrieved, **NO `schema_baseline_dzydscryrnahnneydnry_20261116.sql` was fabricated** and no baseline SHA256 or extracted timestamp is claimed. The existing repo contains patch17–34 but no verified initial schema; those patches cannot safely replace the production baseline.

**Prepared test-only LOCAL CI implementation, not yet executed as DB E2E:**
- `tools/gate1_e2e.py`: requires literal `http://127.0.0.1:54321`; no production/pilot URL, HTTPS host, proxy, redirect, GitHub cloud secrets or cloud project. Binds ephemeral synthetic role tokens and fixture to verified `GATE1_SCHEMA_SHA256`; enables `E07 BLOCKED` **only** if the real schema has no attributable financial receipt mapping, without inventing a table, while permitting the other ten cases to run once provisioned.
- `tools/gate1_local_prepare.py`: reads **only local files**, verifies manifest source ref, SHA256, schema-only/timestamp/patch inclusion, refuses row-copy directives/remote-link credentials; stages baseline and proposed Gate1 SQL as local-only migrations. Missing baseline/manifest exit **3 BLOCKED BEFORE** container startup/network.
- `tools/gate1_local_env.py`: parses `supabase status -o env` LOCAL values only, checks exact loopback, exports ephemeral anon/service keys inside the disposable runner with masking; no GitHub/cloud secrets.
- Branch-specific `.github/workflows/gate1-20261116.yml`: prepares pinned offline core dependencies, runs baseline gate **before** `supabase/setup-cli` or Docker; pinned CLI `3.1.0` stable (release 2026-11-09), runs `supabase start` and **`supabase db reset --local` only after verified baseline**, then `tools/check_all.sh` and teardown. No `supabase link`, `db push`, remote DB env, migration to cloud, or new cost.
- **Not yet generated:** five LOCAL synthetic Auth users, catalog/order seed, consented fixture in `$RUNNER_TEMP/gate1-fixture.json`. Authentic source-schema FK/default/RPC contracts and finance receipt mapping cannot be assumed before successful extraction; local suite refuses to claim results without them.

**Current acceptance:** earlier pinned 4/4 mocked F01–F04 and offline Chromium core contracts PASS (Actions `43761445301`), preserved; *this change does not rerun or supersede them*. Production-schema snapshot **BLOCKED**; REAL local DB E2E **0/11 executed, 11 BLOCKED due to unavailable source baseline & synthetic fixture**, not “only E07 blocked”. E07 financial attribution can be separately BLOCKED **only after** other ten genuinely execute and pass. **GATE1 NO-GO** pending extraction/access and independent security+finance audit; real C-01/release/PHASE2 NO-GO. No main, Cloudflare, other Supabase project, design or financial policy change.