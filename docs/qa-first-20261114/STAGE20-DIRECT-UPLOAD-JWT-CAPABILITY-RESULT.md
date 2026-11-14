# TALABOT — Stage 20 / Publisher Direct Upload Capability Gate — EXECUTED RESULT

**Date:** 2026-11-14 (Asia/Dushanbe)  
**Owner-authorized scope:** [Issue #44](https://github.com/merapplications-sketch/Talabat-v3/issues/44#issuecomment-6876041179) · **Stage 20 assignment:** [Issue #46](https://github.com/merapplications-sketch/Talabat-v3/issues/46) · **Manager/master:** [Issue #26](https://github.com/merapplications-sketch/Talabat-v3/issues/26)  
**Previous new-path report:** [Stage19 Git integration gate, 163be860](https://github.com/merapplications-sketch/Talabat-v3/blob/163be860bf18b9f48cd0cd5b19d736172af6cc55/docs/qa-first-20261114/STAGE19-GIT-INTEGRATION-PREDEPLOY-RESULT.md)  
**Decision:** **P0 DIRECT-UPLOAD-AUTH BLOCKED / NO NEW PROJECT / NO UPLOAD / NO PUBLIC HTTPS URL / PHASE2 NO-GO**.

The owner has already authorized one zero-cost isolated public **static synthetic customer** visual preview; no repeat consent was requested. This stage is the **specific connector-based Pages Direct Upload feasibility check**, not another ZIP transfer attempt or generic architecture proposal.

## 1. Exact immutable source, source/asset scope and what was tested

- Direct GitHub branch read **PASS**: `review/safari-stage13-demo-lang-p2-20261114` currently points to approved corrected SHA **3f74b29a7c4bcc89cef9e25dd73f574448ab7896**.
- Source subtree direct-read **PASS**: `previews/safari-zero-cost-customer/` contains original `index.html`, `demo-core.js`, `demo-fixture.js`, `demo-guard.js`, `_headers`, `assets/`, plus README, two internal QA reports, and manifest.json.
- [Previously verified original ZIP manifest](https://github.com/merapplications-sketch/Talabat-v3/blob/b8210fe7ca325f2ac10af09e8abfd03de1353a0a/deliverables/stage15/zip-integrity.json): **59 total paths, 45 WebP**, ZIP SHA256 **20e674ae017b92a02ca937336f2fa54293fd79fc23e9d8ff559bd564046b82ae**, 967,486 B; original corrected demo fixture Git blob `a2336b6471c96a9a5ca921ccd13805eedf506e0b`. **No ZIP rebuilt, reread/rehashed locally or modified.**
- Approved **upload allowlist: 55 files** = `index.html`, `demo-core.js`, `demo-fixture.js`, `demo-guard.js`, `_headers`, and 50 original local `assets/**` (including **45 WebP**). **Explicitly exclude exactly four files:** `README.md`, `STAGE10-VALIDATION-REPORT.md`, `STAGE13-P2-LANGUAGE-PERSISTENCE-REPORT.md`, and `manifest.json`. This is an output selection; no source deletion or design change.
- Earlier PM **read-only connector memory-bridge proof** ([recorded in Issue #46](https://github.com/merapplications-sketch/Talabat-v3/issues/46)): successfully moved three verified exact GitHub byte sequences to Cloudflare execution memory: `index.html` **548,200B**, `demo-core.js` **146,907B**, and `assets/3d/hamburger.webp` **4,266B**. This proves a representative in-memory transfer **only**, NOT 55/55 files transported or asset-store upload. **This publisher role did not retransmit all 55 bytes after the blocking auth gate was established.**
- Previously accepted Stage10–19 **limited static** checks and original restrictive `_headers` CSP (`default-src 'none'; connect-src 'none'; form-action 'none'`), fake demo client and disabled actions are preserved. This stage made **no new full-source secret scan nor actual deployed code/transaction/browser trace**; no false security/runtime PASS is claimed.

## 2. Cloudflare actual account/project preflight — READ ONLY

- Existing authenticated Cloudflare account connector was available. Direct `GET /accounts/{account_id}/pages/projects` returned **success:true, exactly ONE project**, the original `talabot-pilot-20261106` at `talabot-pilot-20261106.pages.dev`.
- Prior PM safely verified Pages **Read and Pages Write** (the latter via read-only GET upload-token against existing old project **without using the returned JWT**) and preserved the evidence in [Issue #26](https://github.com/merapplications-sketch/Talabat-v3/issues/26#issuecomment-6876732813). No repeated upload-token retrieval here, and **no token recorded/revealed**.
- Existing Cloudflare project remained **untouched**. No new Pages/Workers/Functions, custom domain, environment variable, Git integration, Supabase binding, CI or account change.
- General provider published Free limits [Pages limits](https://developers.cloudflare.com/pages/platform/limits/) allow 55-file static sites (Free 20,000 files per site; each asset up to 25 MiB). Cloudflare [Pages Functions pricing](https://developers.cloudflare.com/pages/functions/pricing/) says static assets (that do not invoke Functions) are free/unlimited on Free and Paid plans. **This is generic provider tariff evidence, NOT proof of the specific connected account's plan or a guaranteed new-project invoice amount.**
- Account-specific subscription/Billing API previously responded **HTTP 403 / code 10000 (Billing Read not supported with this OAuth connection)**, and this Stage20 did not attempt to modify subscription, add billing scope, buy a plan or infer Free from the account `type:standard`. **Exact account Free/no-new-charge assertion UNVERIFIED.**

## 3. Direct Upload protocol and supported connector authentication — decisive gate

I consulted the current **Cloudflare OpenAPI** via connected `Cloudflare.search` and official API documentation, **without invoking upload methods**:

| Stage 20 endpoint | API method and declared request shape | Authorization needed | Status |
|---|---|---|---|
| Get short-lived upload token | `GET /accounts/{account_id}/pages/projects/{project_name}/upload-token` | Pages Write via account OAuth/API permission, yields short-lived **JWT**, tied to an existing project | API PRESENT; prior PM GET proof (old project) only |
| Check missing asset hashes | `POST /pages/assets/check-missing`, JSON `{hashes:[...]}` | **JWT from upload-token endpoint** | API PRESENT; **not invoked** |
| Upload content-hashed assets | `POST /pages/assets/upload`, JSON array with `base64,key,metadata.contentType,value` | **JWT from upload-token endpoint**, per [Cloudflare Upload asset API](https://developers.cloudflare.com/api/resources/pages/subresources/assets/methods/upload/) | API PRESENT; **not invoked** |
| Upsert asset hashes | `POST /pages/assets/upsert-hashes`, JSON `{hashes:[...]}` | Part of the same **JWT-authorized asset flow** | API PRESENT; **not invoked** |
| Create Pages deployment / attach asset manifest | `POST /accounts/{account_id}/pages/projects/{project_name}/deployments`, `multipart/form-data` | Pages Write plus an already completed valid asset-store/manifest workflow | API PRESENT; **not invoked** |
| Create new independent Pages project | `POST /accounts/{account_id}/pages/projects` | Pages Write and verified no-charge eligibility **before any mutation** | **NOT invoked as a permission test** |

**Critical supported-tool limitation:**
- The available connected Cloudflare execution surface provides `cloudflare.request({method,path,query,body,contentType})` — **NO documented `headers`, bearer-token override or JWT-session binding field**.
- The official Pages asset upload API explicitly requires a **different short-lived JWT** generated by the project upload-token operation, **not merely an account Pages Write OAuth credential**. The current connector does **not document an automatic JWT exchange or a supported way to pass this JWT to `/pages/assets/upload`**.
- There are no other connected native Cloudflare file-upload tools exposed besides `Cloudflare.execute/search/docs/whoami`. An undocumented custom Authorization argument, constructed direct HTTP request or borrowing the old pilot's upload JWT **would be a prohibited credential workaround** and is **not attempted**.
- **Therefore: authenticated Pages Direct Upload using the current exposed tool contract is NOT VERIFIED/SUPPORTED end-to-end.** This is **not** a claim that Cloudflare's official service lacks support; it is a **connector capability gap**. Do **not** create the new project first and hope uploading works; this could produce an empty/public project with no compliant artifact.

## 4. Executed outcomes — no overclaim

| Required result | Actual observation |
|---|---|
| Direct Upload endpoints available in Cloudflare API | **YES — confirmed schema for all named endpoints** |
| Pages Read / prior Pages Write scope | **YES — available/previously verified; not sufficient for JWT content upload** |
| Required Pages asset JWT usable by current connected Cloudflare call | **BLOCKED — no supported JWT header/session override documented; no upload test attempted** |
| In-memory GitHub → Cloudflare copy feasible | **YES FOR THREE PREVIOUSLY TESTED REPRESENTATIVE FILES**, not an all-files import |
| All 55 approved immutable files transferred | **NO (0 newly uploaded; 55/55 source files identified only)** |
| Asset hash/manifest upload to provider | **NOT EXECUTED** |
| New standalone Pages project created | **NO** |
| New HTTPS preview URL | **NONE** |
| Current account cost-free additional deployment guaranteed | **UNVERIFIED** (static-only generic pricing documented; account billing data inaccessible) |
| Served CSP/MIME/50 assets/45 WebP/locale screen | **NOT TESTED, no new site** |
| No external requests, real login, order or payment attempted by published site | **NOT TESTED — no browser/network capture** |
| Cloudflare old pilot and TALABOT production | **NO MUTATION** |
| Actual new production or financial operation | **NONE** |

## 5. Final STOP, security boundary, and next manager decision

**Stage20 P0 BLOCKED.** The new in-memory source transfer is technically credible but is **not an authenticated Cloudflare Pages asset upload channel** with this connector. Cloudflare asset-store JWT authorization cannot be supplied by any documented currently available connector API, and exact account-level Free plan/cost remains unverifiable. Both are required by the owner's fail-closed constraints. No new public project was created as a probe, and no source/ZIP rework or billing/permission/production change was performed.

**Only outstanding technical prerequisite:** a **documented, authorized connector or publisher workflow that handles the required short-lived Pages upload JWT natively** and confirms zero additional cost **before** creating any new isolated Pages project; it must accept the original 55 immutable GitHub blobs without re-building ZIP or modifying design/source. This could become available in another already-authorized publisher environment, but is **not demonstrated here**. Do not recommend injecting hidden JWT headers or using credentials from the old project. The original owner consent [#44](https://github.com/merapplications-sketch/Talabat-v3/issues/44#issuecomment-6876041179) remains valid; no repeat consent for the same static visual preview.

**Next actor:** PM receives a single **JWT connector capability BLOCKED** receipt; once a materially new and demonstrably permitted native Direct Upload auth/cost path appears, OPS resumes the **same** approved Stage20 asset publication. An independent security+UX reviewer must validate any actual future public candidate (served SHA/CSP/MIME, RU/EN×320/360/390/430, no unwanted egress, fake cart only) **before** any link goes to the owner.

**Preservation:** Previous accepted source and 59-entry ZIP intact. All approved original customer visual/financial policies, Q09–17, historical dark-login/DEMO notice P2 (DEFERRED), no CI/GitHub branch/Main/Cloudflare old project/Supabase change. Formal E2E **0/51**, Admin **0/21**, Release/G1/PHASE2 **NO-GO**.

**Git scope:** One new Markdown report on isolated branch `review/stage20-ops-direct-upload-gate-20261114`, based on previous Stage19 report commit `163be860bf18b9f48cd0cd5b19d736172af6cc55`; no application, ZIP, source, CI or site modification.
