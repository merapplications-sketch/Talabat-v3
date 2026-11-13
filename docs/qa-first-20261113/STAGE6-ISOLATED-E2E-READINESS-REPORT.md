# TALABOT — STAGE 6 / Isolated E2E Test Readiness
**Date:** 2026-11-13 (Asia/Dushanbe) · **Status:** **READINESS AUDIT DELIVERED / EXECUTION BLOCKED / NO FIXES**  
**Task:** [Issue #32](https://github.com/merapplications-sketch/Talabat-v3/issues/32) · **Owner master:** [Issue #26](https://github.com/merapplications-sketch/Talabat-v3/issues/26) · **PM consolidation:** [five-stage report](https://github.com/merapplications-sketch/Talabat-v3/blob/0ab523782ee1bf6f69e2e3be7ec6e96394d9ce6a/docs/qa-first-20261113/MASTER-QA-CONSOLIDATED-20261113.md)  
**Source under review, main apps:** `1cb85361d698d5da787d927a4c9ae7bd213c68c1` · **TailAdmin:** `254757fab9d5fa80bffe22fa30de5e65aac2f153`  
**Authority:** inventory/readiness only, not test-service provisioning, environment writes, code repair, new tools, hosted login, CI dispatch, SQL, Cloudflare/Supabase changes, deployment, merge or PHASE2.

## 0. Executive determination / explicit test count

- **Immutable source identified: YES** (5 original executable client/core blobs on PM SHA + Admin candidate source tree and lockfile); local executable checkout **NO**. This is a *source availability* finding, not a deployed build attestation.
- **Reusable synthetic harness in existing GitHub files: YES** — `tests/pilot/lab.py`, `tests/pilot/compose.yml`, `tools/qa_all.py`, `tests/fixture.js`, original GitHub Actions workflow and Admin `native-preview`; no new test-harness code is required to **describe** the first scoped trial. Complete sandbox **NOT currently provisioned here**.
- **Already-running, matching, network-isolated local stack: NO evidence / not present** in this execution environment. No test account/session was used; no project traffic sent. Purely read-only host/version and GitHub metadata inspection was executed.
- **Current exact-source functional E2E:** 0/51 (20 customer, 14 driver, 17 backend). **TailAdmin runtime:** 0/21 (17 operational + 4 QA/review). **Authenticated four-app journeys:** 0/4. **Local current-source Smoke:** **NOT EXECUTED/BLOCKED**. Do not relabel browser-tool presence as app smoke. Historic tests retained unchanged.
- **Next smallest executable milestone:** a **separately authorized** single synthetic local-login-to-profile smoke (C-01) in a pre-approved disposable runner with the existing `tests/pilot` harness on pinned SHA, independently verified **fail-closed egress**. Run read-only UI/fixture smoke beforehand after source delivery. This requires **no product fix**, but **does** require explicit authority to materialize source, provision/start isolated disposable services and use pre-existing test runner. No action has been taken.
- **GO for documentation readiness only. NO-GO for execution and QA closure. PHASE2: NO-GO.**

## 1. Source/asset immutable manifest and freshness

**GitHub branch HEADs rechecked in this task:** PM `docs/phase1-operational-coordination-20261111` `1cb85361d698d5da787d927a4c9ae7bd213c68c1`; programmer snapshot `review/ci-native95-20261110` `651696a3fdc51d393bcddef3effd71d6b9634845`; Admin UX candidate `review/ux02-v01-v05-candidate-20261112` `254757fab9d5fa80bffe22fa30de5e65aac2f153`. Defaults `main` are `148cfae50000e983af2221a96057c507edac6d69` (primary) and `1ef305c5b1332c899c5ffdeb72b56235d42d6d00` (Admin); **NOT** substituted for candidate or assumed deployed. Remote GitHub refs and committed tree are visible; another developer's unpushed, uncommitted local state **cannot be checked** from this session.

### Primary repository · 5 executable client/core assets
| Role / entry | Immutable blob at PM source | Evidence | Required related local files | Status |
|---|---|---|---|---|
| Customer | `customer.html` / `9bc335f52ad58d7feab12ad8a2214bde9ab32330` | [Pinned file](https://github.com/merapplications-sketch/Talabat-v3/blob/1cb85361d698d5da787d927a4c9ae7bd213c68c1/customer.html) | `talabat-core.js`, `assets/**`, supplied synthetic SDK mock or isolated Auth+REST | SOURCE CONFIRMED / NOT EXECUTED |
| Driver | `driver.html` / `086929844b2080d7aa2afe1c2c57267cde245d40` | [Pinned file](https://github.com/merapplications-sketch/Talabat-v3/blob/1cb85361d698d5da787d927a4c9ae7bd213c68c1/driver.html) | shared core/assets, driver GPS/offer/receipt fixtures | SOURCE CONFIRMED / NOT EXECUTED |
| Merchant | `merchant.html` / `5f09dd5cc3d5abc9d6b0d3afa031342b05f5212c` | [Pinned file](https://github.com/merapplications-sketch/Talabat-v3/blob/1cb85361d698d5da787d927a4c9ae7bd213c68c1/merchant.html) | shared core/assets; merchant A/B/option and status fixtures | SOURCE CONFIRMED / NOT EXECUTED |
| Legacy Admin | `admin.html` / `062a68cfa740f2733cad39b5c4c5b0c635f54e55` | [Pinned file](https://github.com/merapplications-sketch/Talabat-v3/blob/1cb85361d698d5da787d927a4c9ae7bd213c68c1/admin.html) | shared core/assets/admin-finance, role gates | SOURCE CONFIRMED / NOT EXECUTED |
| Shared runtime | `talabat-core.js` / `f639bec1d23a812866e06eb1110940c77563387c` | [Pinned file](https://github.com/merapplications-sketch/Talabat-v3/blob/1cb85361d698d5da787d927a4c9ae7bd213c68c1/talabat-core.js) | `assets/vendor/supabase-2.117.2.js` / private or mocked synthetic API | SOURCE CONFIRMED / NOT EXECUTED |

The five pinned blobs match the previously audited programmer snapshot. Primary **assets tree** at PM source = `c437cdc288e9e2ed38ac251343b0c3e9169968ef`; vendor SDK blob = `b51e7b9e308e2162d873b84d412a9d37c398d3e0`. [Assets tree](https://github.com/merapplications-sketch/Talabat-v3/blob/1cb85361d698d5da787d927a4c9ae7bd213c68c1/assets/mobile.css) is **not** just mobile.css: a faithful source bundle must include referenced `assets/3d`, `assets/admin-finance`, `assets/finance-receipt`, `assets/driver-returns`, `assets/vendor` and nested data/icons; do not replace approved visuals. A full immutable checkout/tar of this commit is safer than guessing a subset of dependent assets.

### TailAdmin · separate source and build chain

- Candidate `254757fab9d5fa80bffe22fa30de5e65aac2f153` is **the single test pin**. [`package.json`](https://github.com/merapplications-sketch/talabot-tailadmin-review/blob/254757fab9d5fa80bffe22fa30de5e65aac2f153/package.json) blob `6a4904c335e7aff8008f591698b057ab6c6d5097`; [`package-lock.json`](https://github.com/merapplications-sketch/talabot-tailadmin-review/blob/254757fab9d5fa80bffe22fa30de5e65aac2f153/package-lock.json) blob `bf47f8ccb79adae0179e395ffe4efd326a966d15`; [`vite.config.ts`](https://github.com/merapplications-sketch/talabot-tailadmin-review/blob/254757fab9d5fa80bffe22fa30de5e65aac2f153/vite.config.ts) blob `e39350049229bf28ca0b920297b60332a3b6f91a`.
- Candidate [`src`](https://github.com/merapplications-sketch/talabot-tailadmin-review/blob/254757fab9d5fa80bffe22fa30de5e65aac2f153/src/app/globals.css) tree `7b9acf1d1e1d0ca698e60fa6ee0ef67242cbee0e`, [`src/app`](https://github.com/merapplications-sketch/talabot-tailadmin-review/blob/254757fab9d5fa80bffe22fa30de5e65aac2f153/src/app/globals.css) subtree `80d0b80e4b0f3da58e56b31994082ce434f7986e`. Recursively enumerated **37 actual page.tsx paths**, precisely **17 TALABOT operational + 4 QA/review + 16 generic/demo/auth**. No runtime route was visited.
- [Native preview](https://github.com/merapplications-sketch/talabot-tailadmin-review/blob/254757fab9d5fa80bffe22fa30de5e65aac2f153/native-preview/main.tsx) and [Vite preview config](https://github.com/merapplications-sketch/talabot-tailadmin-review/blob/254757fab9d5fa80bffe22fa30de5e65aac2f153/native-preview/vite.config.ts) exist; `npm run dev` points to `native-preview/vite.config.ts`, `npm run build:vinext` is main Vite/Vinext build. The local preview uses synthetic native component state; **not proof** that 21 actual App Router routes, backend or RBAC work. The native Vite config sets `host: 0.0.0.0`, so any authorized future runner must constrain it to loopback or an explicitly sealed interface (no default network exposure).
- Existing Admin candidate tests: 52 scripts in [`tests/`](https://github.com/merapplications-sketch/talabot-tailadmin-review/blob/254757fab9d5fa80bffe22fa30de5e65aac2f153/tests/ux02-mobile-consistency.cjs) tree; for example `ux02-mobile-consistency.cjs` is **SSR/source assertions**, not a browser geometry or 21-route E2E pass. `src/messages/en.json`, `ru.json`, `tg.json`, assets/public/operations-source and fonts remain part of its source bundle.
- **No Admin current-SHA published build digest or executable auth sandbox proven.** Historic Vinext build `ed5e33af...` success is not this candidate.

### Reusable artifacts and what they do *not* prove

| Artifact | Verified provenance or contents | Eligible reuse | Strict boundary |
|---|---|---|---|
| [Source35 recovery receipt](https://github.com/merapplications-sketch/Talabat-v3/blob/1cb85361d698d5da787d927a4c9ae7bd213c68c1/docs/continuity/evidence/20261112-source35-recovery/source35-recovery-receipt.json) | Previously accepted 28/28 hashes and 114/114 saved source files on historical Sites source `bb73be06...` | Keep as historic reference and navigation; **do not rehash or restore** | Different historical Sites source; not a source-matched 1cb/Admin candidate deploy or synthetic API proof |
| [Offline preview HTML](https://github.com/merapplications-sketch/Talabat-v3/blob/1cb85361d698d5da787d927a4c9ae7bd213c68c1/tests/generated/candidate-preview.html) · [inputs.json](https://github.com/merapplications-sketch/Talabat-v3/blob/1cb85361d698d5da787d927a4c9ae7bd213c68c1/tests/generated/inputs.json) | Git blobs `110bdab19ddfa769c7b563c0827d26a756ec1bef` and `4fa6cd778495f2a05912de9524319627859af692`; CSP includes `connect-src 'none'` and inline fake SDK | Existing **admin-only** mock visual artifact after exact source+network verification | Built-input SHA256 manifest not reconciled to current PM SHA here; content still contains literal production-Supabase URL strings (CSP alone is not an OS egress barrier); not an E2E host |
| [Synthetic fixture.js](https://github.com/merapplications-sketch/Talabat-v3/blob/1cb85361d698d5da787d927a4c9ae7bd213c68c1/tests/fixture.js) | Mock store/menu/order/addresses/ratings, UI mode, `window.fetch` rejects external requests | Offline UI rendering and empty/error visual states | Mock in-memory data; **no** real Auth/RLS, concurrent DB writes, money or Storage |
| [tools/qa_all.py](https://github.com/merapplications-sketch/Talabat-v3/blob/1cb85361d698d5da787d927a4c9ae7bd213c68c1/tools/qa_all.py) | Inline synthetic SDK, QA screens and network route interception | UI-only original four-app smoke once immutable source is locally available | Browser interception not enough to establish whole runtime egress isolation |
| [Pilot runner files](https://github.com/merapplications-sketch/Talabat-v3/blob/1cb85361d698d5da787d927a4c9ae7bd213c68c1/tests/pilot/lab.py) | Native synthetic GoTrue/PostgREST/DB login/integration/consent/driver flows already authored | Best existing **true E2E** starting point after separate authorization and latest-source pin | Requires disposable runtime; creates synthetic accounts/DB orders **only in sandbox**; never run against Supabase/cloud |
| [Compose sandbox spec](https://github.com/merapplications-sketch/Talabat-v3/blob/1cb85361d698d5da787d927a4c9ae7bd213c68c1/tests/pilot/compose.yml) | PostgreSQL17.6 pinned digest, GoTrue2.197.0, PostgREST14.18, Storage API1.81.0, Mailpit1.33.0; host mapped 127.0.0.1 | Reuse architecture; no new business logic | Local services absent today; several image tags not immutable by digest; loopback ports alone **do not** block container egress |
| [pilot-isolated Actions](https://github.com/merapplications-sketch/Talabat-v3/blob/1cb85361d698d5da787d927a4c9ae7bd213c68c1/.github/workflows/pilot-isolated.yml) | Existing `workflow_dispatch` suite choices incl `journey`; source `github.sha`, synthetic DB build, no production creds in workflow | Candidate for PM/owner-authorized *single* isolated suite; no need to create a new test suite first | **NOT TRIGGERED**. Workflow not available at default `main` path (GitHub contents API 404); dispatch eligibility/ref/source pin need confirmation. Runner installs packages, creates services, runs writes in lab—prohibited in this Stage 6 |
| [CI106 success](https://github.com/merapplications-sketch/Talabat-v3/actions/runs/42829377671) | Success on **`86eb978e1aeb2be4a9d90999dc9b5a1267cb33df`** | Historical regression envelope only | Not current 1cb or Admin 254 CI or operational acceptance |

**Immutable minimum bundles for proposed runs, no execution:** (1) original four `*.html` + `talabat-core.js` + referenced entire `assets/**` + `tests/fixture.js` or `tools/qa_all.py` for read-only *front-end mock*; (2) first true E2E must also include the **same source SHA** `tests/pilot/**`, `tests/base-lab/**`, `sql/proposed/**`, original migrations and a self-contained isolated Postgres/Auth/REST stack; (3) TailAdmin requires separate exact candidate `package*.json`, `src/**`, `public/**`, `config/**`, `native-preview/**`, `tests/**`, `vite.config.ts` and dependencies from locked install. **No archive was rebuilt or extracted in this task.**

## 2. Directly inspected local toolchain and workspaces

**Read-only shell and module resolution, 2026-11-13T13:14:26Z.** This machine is the available execution environment for this ChatGPT turn, not a statement about other team members' laptop or prior CI runner.

| Item | Observed on this machine | Can currently run a matching TALABOT E2E? |
|---|---|---|
| Node.js / npm | v22.16.0 / v10.9.2 | Interpreter YES; project/dependencies NOT MOUNTED |
| Python / Git | Python 3.13.5 / Git 2.47.3 | Tools YES; repository checkout NOT MOUNTED |
| Chromium | v144.0.7559.96 | Binary installed, no current-source pages |
| Python Playwright | 1.57.0 | Installed; not a sourced browser UI pass |
| Node Playwright | **NOT FOUND** (repo expects 1.56.1) | No `node_modules` |
| React / Next / Vite / jsdom / pglite / Supabase JS Node packages | **NOT FOUND** in this project-independent Node resolver | TailAdmin build blocked |
| Python `psycopg` / `psycopg2` | **NOT FOUND** | Native Postgres driver not runnable |
| Docker, Docker Compose, Podman | **NOT FOUND** | Cannot instantiate pre-authored Compose environment |
| PostgreSQL binaries `psql`, `postgres`, `pg_ctl`, `pg_isready` | **NOT FOUND** | Native local DB absent |
| Project checkout | Checked expected `/mnt/data/Talabat-v3`, `/mnt/data/talabot-tailadmin-review`, `/home/oai/share/Talabat-v3`, `/workspace/Talabat-v3`, and shallow mounted dirs: **ABSENT** | No immutable matching files to render |
| Synthetic runtime account file | `/mnt/data/tests/pilot/.runtime.json`: **ABSENT**; `.runtime*` ignored in repo | No synthetic Auth session available |
| Legacy local service endpoints | No listening match detected for loopback 8080/3000/5432/9999/5000/8025 in available socket view | No proven running lab |
| Direct `github.com` DNS | **UNRESOLVED** on this host | Clone cannot be assumed; GitHub connector read-only worked, but that is not local checkout |

**Smoke execution decision:** **BLOCKED / NOT RUN**, since there is no exact-source runnable local artifact and no provisioned isolated Auth/DB stack. Running an unrelated `data:` browser page would test only installed Chromium and is **not** recorded as TALABOT smoke. Historic read-only web login previews are source-unpinned and excluded. **0 new E2E/geometry screenshots/logs** from this task. No tests were silently passed; no dependencies installed, no services launched.

## 3. Synthetic fixtures: existing evidence vs missing state

- [`tests/pilot/lab.py`](https://github.com/merapplications-sketch/Talabat-v3/blob/1cb85361d698d5da787d927a4c9ae7bd213c68c1/tests/pilot/lab.py) defines **eight original named roles/accounts** at seeded lab init: `admin`, `accountant`, `merchant`, `customer`, `outsider`, `driver1`, `driver2`, `joiner`. It creates synthetic `@synthetic.invalid` identities and credentials only when executed within disposable GoTrue/Postgres, storing secrets in ignored permission-0600 `.runtime.json`/`.runtime.env`. **They are recipes, not existing authenticated sessions here.**
- `merchant2` and a second synthetic store appear in `expanded_privacy()` inside existing [lab.py](https://github.com/merapplications-sketch/Talabat-v3/blob/1cb85361d698d5da787d927a4c9ae7bd213c68c1/tests/pilot/lab.py), rather than initial eight-account seed. The basic `customer` and `outsider` may serve as two distinct customer actors once their effective roles are verified in the isolated DB. `joiner` tests pending driver permission; `accountant` has synthetic finance staff grant. No production identity, email or credential is to be imported.
- Full coverage still needs explicit setup state snapshots for two customer identities, **two distinct stores/merchant owners**, two driver profiles, admin/finance/support permission variants, denied/expired identities, and role×tenant negative cases. Reuse existing `merchant2` path if it fits; **do not silently generate new accounts or change roles under Stage 6**.
- Pre-authored fixtures include store `a0000000-0000-4000-8000-000000000005` and dish `a0000000-0000-4000-8000-000000000006`, plus mocked catalog/items/addresses in `tools/qa_all.py`; these are *synthetic lab identifiers only*. Protected operational order records **#1/#2/#3 and settlement #3 must never be queried or altered**. Lab order IDs must be tracked by their test-run origin, namespace and isolated DB ID, not assumed production-safe by numeric range.
- Required scenario fixtures missing as **verified currently runnable state**: full Q09–17 independent finance oracle and cutoffs (approved decisions unchanged); fake cash/card wallet outcomes, tips/commissions/precision snapshots; private proof bucket/object and signed URL revocation; fake Mailpit/realtime/push/chat; standalone dispatch job; deterministic request delay/lost-after-COMMIT / two-browser contention clock; redacted request-scoped auth/RLS and DB before/after traces; browser geometry captures for TailAdmin current SHA.
- Source tests can cover some of these **after approval**; do not invent that they have been seeded now. The existing hosted Supabase pilot is a **real cloud project**, and project health/history alone is **not** authorization for a synthetic test with it.

## 4. Fail-closed isolation gate — required before any authorized run

| Gate | Verifiable evidence before execution | Result now / owner |
|---|---|---|
| N0 immutable source | Target main `1cb85361d698d5da787d927a4c9ae7bd213c68c1`, TailAdmin `254757fab9d5fa80bffe22fa30de5e65aac2f153`; `git rev-parse HEAD` and source/asset+lockfile manifest with SHA, build digest, code/runtimes at single consistent ref | **BLOCKED** (no checkout/build); DEV + OPS |
| N1 account/endpoint separation | Inspect effective client build config + scripts + environment variables, and reject **any production host, project URL, publishable/service key, storage/bucket or payment/SMS endpoint**. No actual outbound contact with a forbidden endpoint as a “probe” | **BLOCKED**; SECURITY + DEV |
| N2 OS/container egress | Network namespace/firewall/runner policy **DENY all internet egress incl DNS** for browser, backend, Docker containers and test process; narrowly allow local service names/loopback; record explicit deny rules and interface before startup | **BLOCKED**; OPS/SECURITY |
| N3 browser allowlist & CSP | Playwright route aborts any non-lab origin; capture `request`, `requestfailed`, `response`; assert zero production/external requests and matching source. Existing `tests/fixture.js`/generated preview has no-network CSP but not enough alone | **BLOCKED**; QA |
| N4 service & data namespace | Loopback-only UI and PostgREST/GoTrue, isolated DB name and per-suite fixtures; no mounted production secrets, no direct live routes; synthetic IDs only; worker/job run only within same sandbox | **BLOCKED**; API/DB/OPS |
| N5 observed negative proof | Independently prove a **synthetic forbidden host** and non-allowlisted DNS/HTTP route cannot leave the sandbox, plus server-side deny logs; zero unexpected public network attempts during smoke | **NOT RUN**, requires environment; SECURITY+QA |
| N6 no money/incident | No real card, SMS, emails, external mail, published notification, settlement or original operational orders; mock providers and reversible local test DB | **NOT PROVISIONED**; FIN+OPS |

**Important nuance:** `compose.yml` binds its **host ports** to 127.0.0.1 but that does **not** prevent container egress. The already-checked offline `tests/generated/candidate-preview.html` contains a literal production-Supabase URL string despite `connect-src 'none'`; this proves why a search-for-URL + browser CSP + **OS egress deny** must be combined. The [historical hosted frontend builder](https://github.com/merapplications-sketch/Talabat-v3/blob/1cb85361d698d5da787d927a4c9ae7bd213c68c1/release/hosted-pilot/frontend.py) substitutes one project identifier but requires a new synthetic publishable key and creates output; **NOT RUN**, cannot be used as authorization to provision or publish. The TailAdmin Vite local preview defaults to 0.0.0.0; isolate it if later approved, without changing the locked candidate source.

## 5. T1–T7 dependency-to-owner matrix (Stage2/Stage3/Stage5)

| Gate | Existing source or prior evidence (no rerun) | Missing empirical acceptance | Responsible | Current |
|---|---|---|---|---|
| **T1** Source/build/attestation | Main 5 blobs; TailAdmin 254 tree/lock; source35 receipt; release/hosted-pilot builder | Pinned runnable two-repo copies, build digest, exact UI→backend writer versions, safe local origin | DEV + PUBLISHER/OPS | PARTIAL |
| **T2** Synthetic Auth/RBAC | `tests/pilot/lab.py` role registration; GoTrue compose image, local RLS tests | Executed two customers/drivers/merchants + admin/finance/support/denied, real isolated requests, MFA/expiry role×tenant trace | AUTH + SECURITY | BLOCKED |
| **T3** DB/API/Jobs | `tests/pilot/compose.yml`, `tests/base-lab/web`, proposed SQL candidates, pilot workbench | Current accepted schema/grants/RLS/active writers & matching API, wholly local Postgres/GoTrue/PostgREST, background scheduler and isolated snapshots | API + DB + OPS | BLOCKED |
| **T4** Commerce/finance | Historic PRICE/TIP, Q09–17 decisions, CASH-01, demo products/promo/fee | Approved versioned independent numeric oracle: discounts, rounding, fee, split, tips, under/equal/over cash, wallet, fake cards, settlement | FIN + DB | PARTIAL |
| **T5** Storage/messaging | Compose Storage/Mailpit, original upload helpers, chat/realtime source | Private synthetic proof bucket, TTL/revoke/role deny, fake push/notifications/realtime, redacted logs | STORAGE + QA | BLOCKED |
| **T6** Faults/races | Existing `tests/pilot/browser.cjs`, `driver-actions.cjs`, concurrent-journeys, historic CI106 results | Controlled abort before/after COMMIT, two sessions, DB/ledger snapshots and one-effect assertion on current SHA | DEV + API + QA | BLOCKED |
| **T7** Device/CI/UI | Chromium+Python Playwright installed; `tools/qa_all.py`; Admin tests, native preview, historic screenshots | Actual exact-SHA local run receipts, 21-route measured screenshots, 320/360/390/430/768/1440 RU/EN/TG Light/Dark, physical iPhone Safari separately, CI attestation | QA + UX + CI/PUBLISHER | BLOCKED |

Stage2 report [technical audit](https://github.com/merapplications-sketch/Talabat-v3/blob/ea06d61d349667f0a1135b63d923cc756159cc3d/docs/qa-first-20261113/INDEPENDENT-TECHNICAL-STAGE2-QA-REPORT.md), Stage3 [publisher](https://github.com/merapplications-sketch/Talabat-v3/blob/beabf7417a982df622b4acf711750e1bc1b0ca8a/docs/qa-first-20261113/RELEASE-DEPLOYMENT-STAGE3-QA-REPORT.md), Stage5 [UX auditor](https://github.com/merapplications-sketch/talabot-tailadmin-review/blob/f2b18e44a79db090a0c0d2ed715b5ee1ea9dad73/docs/qa-first-20261113/INDEPENDENT-STAGE5-UIUX-QA-REPORT.md) remain the original decision trail; no source F-01..04 or ten UI predicates re-analyzed here. **Q14 under-collection prohibition is already approved**, no policy redecision proposed.

## 6. Scenario-by-scenario 51 functional E2E readiness mapping

**Every case below:** original scenario from [Stage1 report](https://github.com/merapplications-sketch/Talabat-v3/blob/55a3fa5113202afdc3604179fd4a4919043dd11f/docs/qa-first-20261113/PROGRAMMER-STAGE1-QA-REPORT.md) under exact primary `1cb85361d698d5da787d927a4c9ae7bd213c68c1`; no Stage6 runtime execution. `PARTIAL/BLOCKED/UNTESTED` is the **previous source-review classification**, followed by today's **BLOCKED to execute**. Resources are pre-existing scripts/data recipes + additional fixture states required after authorization, **not created now**.

| ID | Original scenario | Required T gates | Explicit synthetic role/data/fault needed | Dependency owner | Historical → Stage6 |
|---|---|---|---|---|---|
| C-01 | فتح العميل→تسجيل الدخول بهوية اصطناعية صالحة/خاطئة | T1,T2,T3,T7 | Customer A; valid/invalid synthetic password; login gate and redacted Auth session | DEV+AUTH | BLOCKED → **BLOCKED to execute** |
| C-02 | دخول→إعادة تحميل→خروج→حساب آخر | T1,T2,T3,T6 | Customer A/B, expired and refreshed tokens, separate local storage | AUTH+QA | BLOCKED → **BLOCKED to execute** |
| C-03 | فتح Home Dynamic Marketplace B→تمرير الأقسام | T1,T3,T4,T7 | Two mock stores, banners, home categories, loading/empty/error | DEV+QA | UNTESTED → **BLOCKED to execute** |
| C-04 | فتح Restaurant Details v1.6→القائمة→المراجعات | T1,T3,T4,T7 | Restaurant A/B, published/unavailable items, reviews and details | DEV+QA | UNTESTED → **BLOCKED to execute** |
| C-05 | بحث عربي/روسي/إنجليزي→فئات→نتائج فارغة | T1,T4,T7 | Long RU/EN/TG search strings, categories, unmatched results | DEV+UX | UNTESTED → **BLOCKED to execute** |
| C-06 | اختيار منتج→إضافات Direction A→تعديل كمية | T1,T3,T4,T7 | Required/optional option groups and unit/quantity price oracle | DEV+FIN | UNTESTED → **BLOCKED to execute** |
| C-07 | إضافة سلة→حفظ→إغلاق/إعادة فتح | T1,T2,T6 | Customer A/B cart keys, expired 24h cart, reload/offline persistence | DEV+QA | PARTIAL → **BLOCKED to execute** |
| C-08 | إدخال promo/HH/loyalty→تغير محتوى السلة | T1,T3,T4,T6 | Promo valid/expired/minimum; happy hours, points and stale response | FIN+DB | PARTIAL → **BLOCKED to execute** |
| C-09 | عنوان جديد→quote→تبديل عنوان/منطقة بعيدة | T1,T3,T4 | Two synthetic coordinates, in/out-zone fee quotes, stale quote | API+FIN | PARTIAL → **BLOCKED to execute** |
| C-10 | حفظ عنوان ناقص/إحداثية مفقودة ثم صحيح | T1,T2,T3 | Missing house/map coordinates; valid address; forbidden cross-account mutation | AUTH+DB | PARTIAL → **BLOCKED to execute** |
| C-11 | إرسال checkout بالنقر السريع مرتين | T1,T3,T6 | One checkout p_key, rapid double-click, two concurrent requests, ledger snapshot | API+DB+QA | PARTIAL → **BLOCKED to execute** |
| C-12 | إنشاء طلب→قطع الاستجابة بعد COMMIT→إعادة إرسال | T1,T3,T6 | HTTP response lost after local COMMIT, replay original key and atomic receipt | API+QA | BLOCKED → **BLOCKED to execute** |
| C-13 | فشل checkout→إغلاق التطبيق→استعادة السلة والمفتاح | T1,T2,T3,T6 | Cart persisted with same key through page close and unknown RPC result | DEV+QA | PARTIAL → **BLOCKED to execute** |
| C-14 | دفع نقدي/محفظة/بطاقة→تغيير وسيلة→retry | T1,T3,T4,T6 | Cash, wallet balance, rejected unconfigured card and fake payment responses | FIN+API | BLOCKED → **BLOCKED to execute** |
| C-15 | طلب pending→cancel→تنازع قبول المطعم | T1,T2,T3,T6 | Merchant acceptance concurrent with customer cancel, outcome reconciliation | API+QA | PARTIAL → **BLOCKED to execute** |
| C-16 | فتح tracking→إشعارات→انقطاع الشبكة | T1,T3,T5,T6 | Status stream and synthetic notifications, disconnect/reconnect, clock | OPS+QA | BLOCKED → **BLOCKED to execute** |
| C-17 | تقييم ومفضلة وملف حساب عبر حسابين | T1,T2,T3,T5 | Two customers/tenant A-B, ratings, favorites, profile privacy negative reads | AUTH+SEC | BLOCKED → **BLOCKED to execute** |
| C-18 | DineOut Gold/الحملات→عرض→اختيار | T1,T4,T7 | DineOut Gold cards and synthetic campaigns; only approved offers | UX+QA | UNTESTED → **BLOCKED to execute** |
| C-19 | Group order: إنشاء/إغلاق→checkout | T1,T2,T3,T4,T6 | Host and joiner customer, group item/options, closing and single checkout | DEV+API | PARTIAL → **BLOCKED to execute** |
| C-20 | التذاكر/طلب رد→خطأ→إعادة فتح | T1,T2,T3,T4,T5 | Support tickets/replies, synthetic refund record without external payment | SUPPORT+FIN | BLOCKED → **BLOCKED to execute** |
| D-01 | دخول سائق/حساب غير مخول→محاولة driver RPC | T1,T2,T3 | Approved/pending/denied synthetic drivers, cross-role RPC denied | AUTH+SEC | BLOCKED → **BLOCKED to execute** |
| D-02 | بدء نوبة مع server ping فاشل | T1,T2,T3,T6 | Online/offline heartbeat ACK success/failure/timeout with synthetic driver | DEV+API | PARTIAL → **BLOCKED to execute** |
| D-03 | عرضين→قبول سريع مكرر/قبول متنازع | T1,T2,T3,T6 | Two drivers competing for a single offer; duplicate accept payload | API+QA | PARTIAL → **BLOCKED to execute** |
| D-04 | رفض عرض مراراً/بعد انتهاء المهلة | T1,T2,T3,T6 | Expired/rejected offers and repeated declines, no double-state | API+QA | PARTIAL → **BLOCKED to execute** |
| D-05 | GPS إذن/رفض/تراجع→دقة وإرسال متقطع | T1,T3,T5,T7 | Mock GPS allowed/denied/inaccurate, heartbeat; no real geolocation | DEV+QA | BLOCKED → **BLOCKED to execute** |
| D-06 | arrived store→ready→pickedup→arrived customer | T1,T2,T3,T6 | Merchant Ready, store arrival, pickup, customer arrival, invalid skip | API+DB | PARTIAL → **BLOCKED to execute** |
| D-07 | تشغيل النوبة→انقطاع→عودة/إغلاق | T1,T3,T5,T6 | Driver offline/recovery while assigned a synthetic active order | API+OPS | BLOCKED → **BLOCKED to execute** |
| D-08 | تسليم كاش أقل/أكثر/مساوٍ للمستحق | T1,T3,T4,T6 | Q09–Q17 approved cash oracle: &lt;due/=due/>due, 0/20/custom cap | FIN+DB | PARTIAL → **BLOCKED to execute** |
| D-09 | ترك على الباب→صورة مفقودة/فاسدة/نجاح | T1,T2,T3,T5 | Synthetic image, missing/corrupt proof, private path, signed link | STORAGE+AUTH | PARTIAL → **BLOCKED to execute** |
| D-10 | نقر «تأكيد التسليم» مرتين أثناء تأخر RPC | T1,T3,T4,T6 | Two quick delivery submits; single status/ledger effect, delayed ACK | API+DB | PARTIAL → **BLOCKED to execute** |
| D-11 | إرسال رسالة ثم قطع الشبكة/رفض insert | T1,T3,T5,T6 | Driver message refused/delayed, offline draft and same-order retry | DEV+QA | PARTIAL → **BLOCKED to execute** |
| D-12 | عرض المستحقات والإغلاق المالي والتسويات | T1,T2,T3,T4 | Synthetic driver earnings, paid/unpaid due, allocations/receipt reconciliation | FIN+DB | BLOCKED → **BLOCKED to execute** |
| D-13 | رابط خريطة→موقع مطعم/عميل→عودة | T1,T3,T7 | Mock restaurant/recipient coordinates; safe navigation URL, return state | DEV+QA | UNTESTED → **BLOCKED to execute** |
| D-14 | إعادة فتح السائق منتصف الطلب→تنازع تحديثين | T1,T2,T3,T6 | Two driver sessions, restart mid-order, conflicting status updates | AUTH+QA | BLOCKED → **BLOCKED to execute** |
| B-01 | جرد واجهات REST/RPC ونداءات العميل/السائق | T1,T3 | Version-pinned RPC/REST contract registry and redacted request/response trace | API | PARTIAL → **BLOCKED to execute** |
| B-02 | Auth/MFA/RBAC: أدوار/مفاتيح جلسة/انتحال | T1,T2,T3 | Role×tenant matrix, invalid/MFA/expired tokens; no live accounts | AUTH+SEC | BLOCKED → **BLOCKED to execute** |
| B-03 | تسريب بيانات بين حسابين/مستأجرين | T1,T2,T3 | Two customers, two merchants/drivers, cross-tenant denial and RLS evidence | DB+SEC | BLOCKED → **BLOCKED to execute** |
| B-04 | إرسال طلبين متزامنين بنفس p_key | T1,T3,T4,T6 | Duplicate p_key across concurrent local PostgREST sessions and snapshots | API+DB | PARTIAL → **BLOCKED to execute** |
| B-05 | timeout/unknown بعد commit→replay بنفس المفتاح | T1,T3,T4,T6 | Lost response after COMMIT, unknown ACK, fixed request key and replay | API+QA | BLOCKED → **BLOCKED to execute** |
| B-06 | SERIALIZABLE/RR/RC وإغلاق المفتاح | T1,T3,T6 | Synthetic isolation levels and key closure; preserve historic 106 acceptance | DB+QA | PARTIAL → **BLOCKED to execute** |
| B-07 | تسلسل status/إعادة محاولة بعد تغيير حالة | T1,T2,T3,T6 | State-machine invalid transitions and concurrent row locks | DB+API | PARTIAL → **BLOCKED to execute** |
| B-08 | عميل يرسل سعر/خصم/رسوم مخالفة للخادم | T1,T3,T4 | Altered client total/discount/fee, trusted server oracle, rounding | FIN+API | PARTIAL → **BLOCKED to execute** |
| B-09 | عمولات/بقشيش/نصيب سائق عبر تغير الإعدادات | T1,T3,T4 | Historical/frozen split config, restaurant commission, tip allocations | FIN+DB | PARTIAL → **BLOCKED to execute** |
| B-10 | تسوية نقد/مستحق→إعادة إرسال/تنازع | T1,T2,T3,T4,T6 | Synthetic cash settlement/idempotency, double request, receipt ledger | FIN+DB | BLOCKED → **BLOCKED to execute** |
| B-11 | دفع إلكتروني/استرداد→فشل طرف ثالث | T1,T3,T4,T6 | Fake payment gateway, refund pending/timeout, never external charge | FIN+OPS | BLOCKED → **BLOCKED to execute** |
| B-12 | Promo/loyalty/wallet: سباق واستنزاف رصيد | T1,T3,T4,T6 | Promo race, wallet points, ledger atomicity, independent balance oracle | FIN+DB | PARTIAL → **BLOCKED to execute** |
| B-13 | Storage proofs وSigned URL TTL/ACL | T1,T2,T3,T5 | Synthetic bucket, signed URL expiry/revoke, cross-account deny | STORAGE+SEC | BLOCKED → **BLOCKED to execute** |
| B-14 | إجراء إداري غير مصرح/اختراق API خاص | T1,T2,T3 | Forbidden admin/finance RPC, RLS grants and request-scoped audit | SEC+DB | BLOCKED → **BLOCKED to execute** |
| B-15 | فقد اتصال/مهلة/إعادة المحاولة/تصادم متزامن | T1,T3,T6 | Network abort, timeout, session crash and two writer races; DB snapshots | API+QA | BLOCKED → **BLOCKED to execute** |
| B-16 | dispatch_tick/realtime عند غياب عميل متصل | T1,T3,T5,T6 | Synthetic scheduled dispatch heartbeat while all clients offline | OPS+API | PARTIAL → **BLOCKED to execute** |
| B-17 | مصدر/CI/build→الإصدار النشط→الرجوع | T1,T3,T7 | SHA→frontend files→backend schema/writer→CI/deployment/rollback receipt | OPS+CI | BLOCKED → **BLOCKED to execute** |

**Coverage reconciliation:** 20 Customer + 14 Driver + 17 Backend = **51 cases**, zero executed in this Stage. Historic 106/107/PRICE/TIP are not rerun or added to this current-SHA numerator.

## 7. Admin source-matched readiness — 17 operational + 4 QA/review (21)

**Test pin:** `254757fab9d5fa80bffe22fa30de5e65aac2f153` only. 37 actual pages in source tree, **21 scoped**. Each selected route requires source digest and entry URL, synthetic role/fixture conditions, 6 viewport widths (320, 360, 390, 430, 768, 1440) × three locales RU/EN/TG × Light/Dark = 36 combinations *per route* (21 × 36 = 756 route-configurations, **NOT** 756 E2E tests passed). Independently cover long names, loading/empty/error, offline/denied, keyboard focus/touch, modal back/draft retention. Native preview alone is not route-server E2E.

### Operational routes (17)
| Case | Route (locale prefix applied) | Fixture/states | Gates | Owner | Runtime |
|---|---|---|---|---|---|
| A-01 | `/` | 4 A KPI + B analytics, no real user/order data | T1,T3,T4,T7 | UX+FIN | BLOCKED |
| A-02 | `/orders` | Statuses, search, filters, mobile cards, two synthetic orders | T1,T2,T3,T4,T7 | DEV+OPS | BLOCKED |
| A-03 | `/orders/[id]` | Realistic synthetic order details, optional items/date, unknown state | T1,T2,T3,T4,T6,T7 | DEV+API | BLOCKED |
| A-04 | `/restaurants` | Two mock merchants, long names, empty/error/denied | T1,T2,T3,T7 | DEV+QA | BLOCKED |
| A-05 | `/restaurants/[id]` | Merchant items/options and permission visibility | T1,T2,T3,T4,T7 | DEV+QA | BLOCKED |
| A-06 | `/drivers` | Two drivers, online/blocked status and availability | T1,T2,T3,T7 | DEV+OPS | BLOCKED |
| A-07 | `/drivers/[id]` | Driver earnings, assigned orders, denied finance persona | T1,T2,T3,T4,T7 | FIN+SEC | BLOCKED |
| A-08 | `/customers` | Two tenant-scoped synthetic profiles with long strings | T1,T2,T3,T7 | DEV+SEC | BLOCKED |
| A-09 | `/customers/[id]` | Private address/order/loyalty; deny cross-account | T1,T2,T3,T4,T7 | SEC+DB | BLOCKED |
| A-10 | `/notifications` | Unread/read alerts, loading/offline/denied and long TG | T1,T3,T5,T7 | UX+QA | BLOCKED |
| A-11 | `/notifications/[id]` | One-line mark-read owner variant, failure, return focus | T1,T3,T5,T6,T7 | UX+QA | BLOCKED |
| A-12 | `/finance` | Synthetic settlement/receipt, Q09–17 approved oracle | T1,T2,T3,T4,T7 | FIN+SEC | BLOCKED |
| A-13 | `/finance/[id]` | No real settlement, synthetic receipt detail and role deny | T1,T2,T3,T4,T7 | FIN+DB | BLOCKED |
| A-14 | `/reports` | Synthetic time-series metrics without claimed production totals | T1,T3,T4,T7 | DEV+FIN | BLOCKED |
| A-15 | `/reports/[id]` | Empty/error report, date range and persisted filters | T1,T3,T4,T7 | DEV+QA | BLOCKED |
| A-16 | `/settings` | Allowed/denied settings, language/theme and draft return | T1,T2,T3,T7 | AUTH+UX | BLOCKED |
| A-17 | `/operations/[section]` | Dispatch, support, ratings, campaigns, mock offline states | T1,T2,T3,T5,T7 | OPS+UX | BLOCKED |

### QA/review routes (4)
| Case | Route (locale prefix applied) | Fixture/states | Gates | Owner | Runtime |
|---|---|---|---|---|---|
| Q-01 | `/operations-review` | Isolated A/B operations review, read-only comparisons | T1,T7 | UX+QA | BLOCKED |
| Q-02 | `/review/operations` | Saved candidate source, presentation without real writes | T1,T7 | UX+QA | BLOCKED |
| Q-03 | `/review/image-cases` | Original image assets and source-checksum correspondence | T1,T7 | UX+QA | BLOCKED |
| Q-04 | `/visual-review` | 320/360/390/430 + tablet/desktop, RU/EN/TG, light/dark | T1,T7 | UX+QA | BLOCKED |

**Source-backed evidence:** [Admin real App Router pages](https://github.com/merapplications-sketch/talabot-tailadmin-review/blob/254757fab9d5fa80bffe22fa30de5e65aac2f153/src/app/globals.css) and [candidate tests](https://github.com/merapplications-sketch/talabot-tailadmin-review/blob/254757fab9d5fa80bffe22fa30de5e65aac2f153/tests/visual-review.cjs). No authenticated screens or physical Safari were executed in Stage6. Operational/Admin personas cannot be equated to the synthetic `previewPersona` alone.

## 8. Fastest permitted *future* path: one smoke, then one real E2E — STOP gates

**Step A · PM/owner scope approval needed, not granted by this report:** authorize copying the **existing** immutable source and already-reviewed fixture into a closed local/test runner; authorize starting an ephemeral browser for UI-only smoke on `1cb85361d698d5da787d927a4c9ae7bd213c68c1`. Before start: N0–N5 signed egress/source/identity proof, no external endpoint. Expected first **read-only UI smoke**: synthetic `customer.html` login/home shell with `tools/qa_all.py` in Chromium, one viewport RU, log `sourceSHA`, `blob`, render/no JS errors, blocked external requests, screenshot and user-visible synthetic marker. **NOT RUN NOW.** Mock shell ≠ authenticated E2E.
  
**Step B · separate owner scope for runner/services/test writes:** reuse the **existing** [`pilot-isolated.yml`](https://github.com/merapplications-sketch/Talabat-v3/blob/1cb85361d698d5da787d927a4c9ae7bd213c68c1/.github/workflows/pilot-isolated.yml) `journey` approach or the **same existing** `tests/pilot/lab.py` + [Compose](https://github.com/merapplications-sketch/Talabat-v3/blob/1cb85361d698d5da787d927a4c9ae7bd213c68c1/tests/pilot/compose.yml) on a pre-approved ephemeral VM/runner. Do not presume `workflow_dispatch` works: the workflow file was 404 at default `main` in this read-only check, and **no dispatch or workflow changes** are authorized. Scope only **C-01 synthetic customer browser → local GoTrue → local PostgREST profile read**, with valid and invalid synthetic credentials and no order/payment transaction. Existing `journey` suite itself performs synthetic writes and a broader set of cases; **do not trigger entire suite as a substitute for this narrow approval**. A one-case selection may require separate approval for test runner configuration or scripted selection; do not implement it autonomously.

**Step C · deterministic evidence required to call C-01 PASS:** same immutable source SHA in browser and server manifest; Auth identity `@synthetic.invalid`; redacted request/response and effective role; profile scoped correctly; failed credential rejected; zero outbound non-lab requests under independently observed egress deny; process/service disposed; no production or external writes. Until these receipts exist, C-01 **BLOCKED**, not PASS.

**Step D · once the first case is independently accepted:** expand only by PM assignments into the other 50 functional cases and 21 Admin routes, adding T4/T5/T6/Q09–17/physical Safari gates as each category needs. No work automatically proceeds because this readiness report exists.

**Short dependency chain:** PM approves bounded runner and source-copy scope → DEV/OPS supplies immutable matching source & locked dependencies → SECURITY verifies egress deny → API/DB/AUTH activates synthetic local stack and first persona → QA runs one read-only/synthetic login-to-profile E2E and captures evidence → independent gate review. This is smaller/safer than trying to activate the historical cloud pilot, resuscitate Pages, or rewrite app code.

## 9. CI status and preservation

- GitHub Actions exact `head_sha` query returned **0 runs** for main source `1cb85361d698d5da787d927a4c9ae7bd213c68c1` and Admin `254757fab9d5fa80bffe22fa30de5e65aac2f153`. This is an observation of the available runs API, **not a failing build**.
- Historical main CI106 succeeded on a different commit; Admin original Vinext succeeded on a different commit. Existing `pilot-isolated.yml` `workflow_dispatch` is present on the pinned PM branch but absent from the current default-main path. **No CI/action rerun, no Docker build, no deployment, no experiment or credential provisioning executed**.
- Keep accepted PRICE/RATINGS/TIP/106/107 and Source35 evidence in their original scopes; no re-extraction or retest performed. Source35 114/114 archive is not a current E2E source build attestation.
- Existing source/design/finance/RBAC remains untouched. Q09–17 including Q14 and UI V04 are **approved locks**, no product decision was requested or altered.

## 10. Single delivery, limits and owner handoff

| Deliverable | Decision |
|---|---|
| Sources and immutable SHA | **COMPLETE (read-only GitHub sources)** |
| Toolchain and infrastructure discovery | **COMPLETE (this runtime only)** |
| Presence of synthetic fixture *source code* | **YES, REUSABLE** |
| Running isolated sandbox and proven egress barrier | **NO, BLOCKED** |
| Current-SHA safe local smoke | **BLOCKED / NOT EXECUTED** |
| 51 functional E2E / 21 Admin current-source E2E | **0/51, 0/21** |
| Smallest bounded next step | PM/owner explicit approval for exact-SHA source copy + sealed ephemeral runner + existing synthetic auth/DB, then C-01 |
| Production changes, installations, hosted sessions, SQL, Cloudflare, Supabase, merge/deploy, code fixes | **NONE** |
| Overall | **STAGE 6 READINESS REPORT COMPLETE; TEST EXECUTION NOT READY / QA NO-GO / PHASE2 NO-GO** |

**No additional work is authorized by this report.** Return to manager for review of the isolated-runner scope; no self-started E2E or remediation.
