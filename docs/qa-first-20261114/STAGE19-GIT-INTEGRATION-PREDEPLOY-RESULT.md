# TALABOT — STAGE 19 / Git-backed Cloudflare Pages — Publisher execution result

**Date:** 2026-11-14 (Asia/Dushanbe)  
**Task:** [Issue #45](https://github.com/merapplications-sketch/Talabat-v3/issues/45) · **Owner approval:** [Issue #44](https://github.com/merapplications-sketch/Talabat-v3/issues/44#issuecomment-6876041179) · **Master:** [Issue #26](https://github.com/merapplications-sketch/Talabat-v3/issues/26)  
**Previous publisher receipt:** [Stage 19 at 99348d2c](https://github.com/merapplications-sketch/Talabat-v3/blob/99348d2c9d4b75947ef6951cfd37aeb089963138/docs/qa-first-20261114/STAGE19-PUBLISHER-FREE-SAFARI-STATIC-PREVIEW-RESULT.md)  
**Disposition:** **P0 BLOCKED — NO NEW PROJECT OR PUBLICATION; P1 STATIC SOURCE PARTIAL PASS; PHASE2 NO-GO.**

This review tests the **new Git-backed source path**, not the failed ZIP-to-local-file transport. No new consent requested. No app, original design, approved branch, ZIP, Cloudflare existing project, Supabase, production, GitHub Actions or account permissions changed.

## 1. Fresh source and scoped artifact integrity

- GitHub source branch [review/safari-stage13-demo-lang-p2-20261114](https://github.com/merapplications-sketch/Talabat-v3/tree/review/safari-stage13-demo-lang-p2-20261114) directly verified HEAD **3f74b29a7c4bcc89cef9e25dd73f574448ab7896**. No main or other feature source substituted.
- Immutable [Stage15 archive manifest](https://github.com/merapplications-sketch/Talabat-v3/blob/b8210fe7ca325f2ac10af09e8abfd03de1353a0a/deliverables/stage15/zip-integrity.json) states ZIP SHA256 **20e674ae017b92a02ca937336f2fa54293fd79fc23e9d8ff559bd564046b82ae**, 967,486 bytes, **59 files**, **45 WebP**, corrected fixture Git blob **a2336b6471c96a9a5ca921ccd13805eedf506e0b**. These previously accepted upstream receipts were **not rehashed locally**; no ZIP download or rebuild was attempted.
- Direct GitHub source-directory read at that exact commit confirmed top-level **index.html, demo-core.js, demo-fixture.js, demo-guard.js, _headers, assets/** as well as README, two QA reports and manifest.json.
- Direct static allowlist projection over manifest entries: **55 files, including the 45 WebP**, after excluding exactly **README.md**, **STAGE10-VALIDATION-REPORT.md**, **STAGE13-P2-LANGUAGE-PERSISTENCE-REPORT.md**, and **manifest.json**. No files deleted or modified in GitHub. This is **projected output**, not an actual built/published archive.
- If permission gates were to pass, Git root would be **previews/safari-zero-cost-customer/** and output must be **ONLY** the allowlisted assets. The minimal build-only copy command to exclude internal docs without modifying source could be `mkdir -p dist && cp index.html demo-core.js demo-fixture.js demo-guard.js _headers dist/ && cp -R assets dist/`, destination `dist`, no package install or external build dependencies. This **was not executed** and does not itself authorize creation.

## 2. Narrow prepublication safety observations (read-only; not repeated Stage10–16 audits)

- Inspected GitHub blobs for nine file types intended for the static projection: **index.html** (Git blob `8d1e41a0acfcefb0f0f08a6dd494ac9b1a755357`), **demo-core.js** (`28e140065a889be0cd3a206b7ae8c965f7f1e182`), **demo-fixture.js** (`a2336b6471c96a9a5ca921ccd13805eedf506e0b`), **demo-guard.js** (`fceff4bfd547d61e3f10b19f17cdf642bbb1a755`), **_headers** (`b7b2ae32cb9bfbc8b8dd563cc129ca6ebf75b1bc`), **assets/mobile.js**, **assets/mobile.css**, **assets/driver-returns/panel.js**, and **assets/driver-returns/panel.css**.
- Targeted string scan found **0 references** to three known production/pilot Supabase project IDs and **0 ordinary external HTTP/WebSocket asset URLs** in those nine text files. The one apparent `http://www.w3.org/2000/svg` string is an **SVG XML namespace**, not an external resource request. This is a **limited static search**, not a runtime network audit or exhaustive secret scanner.
- In the approved demo-core, `SB_URL` is **about:blank**, the key literal is classified as demo-only, and the fixture provides a mock Supabase client. The original _headers defines **Content-Security-Policy: default-src 'none'; connect-src 'none'; form-action 'none'** plus other restrictive directives. The demo guard intercepts order/payment calls in source. Auth/login-related function *names* remain in the mock-compatible core; their presence is not proof of a real login or a live authentication endpoint.
- No runtime browser, host uploads, served HTTP headers, actual asset SHA256 or Network panel were observed. **P1 = STATIC SOURCE CONFORMITY PARTIAL**, not a full published-bytes, financial, operational or E2E PASS.

## 3. P0 — existing Cloudflare access and no-charge requirement: measured result

| Prerequisite | Direct evidence | Disposition |
|---|---|---|
| Cloudflare Pages Read | Newly reconnected connector **GET /accounts/{account_id}/pages/projects** succeeded. It returned **exactly one project**, `talabot-pilot-20261106`. GET its detail also succeeded. | **PASS** |
| Existing pilot preserved | Read-only old project named `talabot-pilot-20261106`, subdomain `talabot-pilot-20261106.pages.dev`; latest known deployment ID `1a602ee4-6daa-4a76-a8aa-68339321cac5`. **No write to it.** | **PASS (untouched)** |
| Pages Write scope | PM separately verified a Pages Write-only read endpoint **without writing or using the returned upload credential**; [PM checkpoint in Issue #45](https://github.com/merapplications-sketch/Talabat-v3/issues/45#issuecomment-6876733434). No new action repeated here. | **Previously VERIFIED; creation still untested** |
| Generic Pages Free tier capacity | [Cloudflare Free limits](https://developers.cloudflare.com/pages/platform/limits/) document allowance for a project with 55 files and one new static project under general Free quotas; current inventory shows one existing project. | **Provider capability established; account-specific cost not confirmed** |
| Current account Free entitlement and zero extra charges | Read-only **GET /accounts/{account_id}/subscriptions** returned **HTTP 403 / code 10000**: this OAuth integration cannot use Billing Read/Write endpoint; account type `standard` is **not** a billing plan. No subscriptions, billing controls or payments changed. | **UNVERIFIED — P0 BLOCKER** |
| Cloudflare GitHub App already authorized for **this exact repo** | Current old Pages project's `source` was **null** in its GET result, so it supplies **no evidence of any Git-linked repo**. The Cloudflare OpenAPI Pages read surface exposes no pre-create repository-authorization verification operation. Attempted read-only GitHub `GET /repos/merapplications-sketch/Talabat-v3/installation` through permitted connector returned **endpoint not allowed**, not an installation result. This assistant's GitHub app access to the public repository **does not prove the separate Cloudflare Workers & Pages GitHub App has been installed for that repo**. [Cloudflare GitHub integration docs](https://developers.cloudflare.com/pages/configuration/git-integration/github-integration/) require explicit repository access. | **UNVERIFIED — P0 HARD BLOCKER** |
| New unused Pages name and HTTPS host | No new name reserved or project created; old project never modified. | **NOT EXECUTED** |

**Fail-closed rule in the user/PM directive:** **do not create a Pages project before *both* repo-specific Cloudflare GitHub integration authorization and free eligibility are established**. Neither can be proven with the currently exposed authorized read operations. A Pages POST may create a public project immediately and therefore is **not** a harmless Git-authorization probe. **No POST/PATCH/DELETE or deployment attempted.** No new GitHub installation, account grant, subscription or payment was requested.

## 4. P2/P3 — actual deployment and browser verification: NOT RUN

| Requested result | Actual status |
|---|---|
| One new independent Pages project | **NONE CREATED** |
| Public HTTPS URL | **NONE**; do not invent or send owner URL |
| Git source synchronization and deployed SHA | **NOT EXECUTED / NO DEPLOYMENT** |
| Excluded QA reports actually not publicly served | **PLANNED BUILD OUTPUT ONLY; NOT VERIFIED HOSTED** |
| New project auto-deploy freeze after initial commit | **NOT APPLICABLE** (no first deployment) |
| Live HTTP CSP, MIME, CSS/JS and WebP responses | **NOT TESTED** |
| New unauthenticated Safari login-free entry | **NOT TESTED** |
| Browser requests, including blocked external attempts | **NO TRACE**; do not claim runtime zero egress |
| Real order/payment disabled in served code | **NOT TESTED** |
| Independent live security and visual QA | **NOT STARTED** (no candidate site) |

## 5. Final operational handoff and precise next dependency

**Stage19 git-backed alternate path:** source/branch and projected static-only publication set are confirmed, Cloudflare Pages Read works, and the earlier *local ZIP transport* is no longer part of the proposed Git integration deployment. **But P0 remains BLOCKED by two specific external facts: (1) no confirmed Cloudflare GitHub App repo grant for `merapplications-sketch/Talabat-v3`; (2) account-specific Free entitlement cannot be read through the authorized OAuth connection.**

The project manager should only reassign this already-owner-approved publisher work **once an already-authorized, read-only way to establish both facts becomes available**. If a **new GitHub App installation, billing/read grant, paid plan or account modification** is required, this task's fail-closed rule forbids performing or requesting it autonomously. Do **not** substitute an existing production site, create a blank Pages project as an access probe, repeat ZIP transfer, modify source/design/manifest, or request owner devices/subscription. Owner consent for the approved exact static demo in Issue #44 **continues to stand**, no repeat consent needed for that scope.

**Final disposition:** **NO NEW PREVIEW / NO URL / P0 BLOCKED / P1 SOURCE PARTIAL / P2-P3 NOT RUN / PHASE2 NO-GO**. No existing Cloudflare site, Github approved branch/main, SQL, Supabase, production customer/order/finance, CI or account permission was modified. Original pilot's dark colors remain deferred. Formal product E2E 0/51 and Admin E2E 0/21 unchanged.

**Git handoff:** one documentation-only Markdown report on isolated `review/stage19-git-integration-p0-gate-20261114`, based on existing Stage19 documentation-only receipt `99348d2c9d4b75947ef6951cfd37aeb089963138`. No app files or Cloudflare/production changes.
