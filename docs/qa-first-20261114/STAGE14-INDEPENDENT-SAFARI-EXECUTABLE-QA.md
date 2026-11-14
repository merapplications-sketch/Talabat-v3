# TALABOT — STAGE 14 / INDEPENDENT EXECUTABLE SAFARI DEMO QA

**Date:** 2026-11-14 · Asia/Dushanbe
**Assignment:** [Issue #40](https://github.com/merapplications-sketch/Talabat-v3/issues/40), [Master #26](https://github.com/merapplications-sketch/Talabat-v3/issues/26)
**Candidate:** [3f74b29a7c4bcc89cef9e25dd73f574448ab7896](https://github.com/merapplications-sketch/Talabat-v3/commit/3f74b29a7c4bcc89cef9e25dd73f574448ab7896) on review/safari-stage13-demo-lang-p2-20261114
**Parent demo:** 2bae45cc5a21372123228befcbe87c19d6aac974
**Approved product source:** 1cb85361d698d5da787d927a4c9ae7bd213c68c1
**Judgment:** **SOURCE CORRECTION VERIFIED / EXECUTABLE TEST BLOCKED BY EXACT-ARTIFACT TRANSFER / NO PUBLIC SAFARI GO / PHASE2 NO-GO**.

This is one final independent read-only handoff. No fixes, deployment, live requests, Cloudflare/Supabase/SQL actions, CI, login, real payment, C-01, merge or production test.

## 1. HEAD, source and approved-fix proof

- Independently checked current HEAD of **review/safari-stage13-demo-lang-p2-20261114**: **3f74b29a7c4bcc89cef9e25dd73f574448ab7896**. It matches the directive.
- [Exact Git comparison Stage10→Stage13](https://github.com/merapplications-sketch/Talabat-v3/compare/2bae45cc5a21372123228befcbe87c19d6aac974...3f74b29a7c4bcc89cef9e25dd73f574448ab7896): ahead 1 / behind 0, **only one executable file changed** at previews/safari-zero-cost-customer/demo-fixture.js, plus one new Markdown report. The executable diff removes one unconditional Russian-language storage assignment (one-line replacement). All original product files, original CSS/logo/layout, demo-core.js, demo-guard.js, index.html, _headers, manifest and 50 copied image/CSS/JS assets are unchanged.
- Independently fetched the corrected fixture via GitHub connector: Git blob **a2336b6471c96a9a5ca921ccd13805eedf506e0b**. Its line 2 retains fake customer identity/synthetic flag but **no longer overwrites tlb_demo_lang with ru**.
- Unchanged index.html blob 8d1e41a0acfcefb0f0f08a6dd494ac9b1a755357 preserves saved-language precedence at line 8. Unchanged demo-core.js blob 28e140065a889be0cd3a206b7ae8c965f7f1e182 saves manual choice via setLang.
- [Stage13 developer report](https://github.com/merapplications-sketch/Talabat-v3/blob/3f74b29a7c4bcc89cef9e25dd73f574448ab7896/previews/safari-zero-cost-customer/STAGE13-P2-LANGUAGE-PERSISTENCE-REPORT.md) reports 8/8 V8 **source-function simulation** PASS. Those results are **not actual browser E2E**. This independent review did not repeat them.
- Independent GitHub Contents directory metadata for the **corrected SHA**: **9 root files + 2 mobile CSS/JS + 2 driver-returns CSS/JS + 46 assets/3d files = 59 tracked paths**. Stage10 had 58; Stage13 added its own Markdown report. These are path counts, not 59 executable files. All prior 50/50 copied-asset hash acceptance is reused without re-execution.
- [Stage11 security QA](https://github.com/merapplications-sketch/Talabat-v3/blob/c90585b479f43143daa00504238a3732f962d625/docs/qa-first-20261114/STAGE11-INDEPENDENT-SAFARI-SECURITY-QA.md) previously matched 50/50 original copied asset Git blobs; [Stage12 UX QA](https://github.com/merapplications-sketch/Talabat-v3/blob/5a1df0998cf940f5881c6bd9e77748c38bfe2cbd/docs/qa-first-20261114/STAGE12-INDEPENDENT-SAFARI-CUSTOMER-UX-QA.md) examined approved visual structure. Stage13 did not change any of those files. **No repeat asset-hash audit, no original design audit, no PRICE/RATINGS/TIP or 106/107 retest.**

## 2. Actual environment and artifact acquisition

**Required exact input:** all **59 tracked paths** of the corrected preview directory (58 original Stage10 paths plus one Stage13 Markdown report), including all binary WebP assets, directly available to an isolated browser runner. **Not available in the local filesystem during this session.** Local test environment has Chromium **144.0.7559.96**, Python Playwright and Node, but no current preview directory or archive in /mnt/data. These installed tools do not constitute a browser test.

| Retrieval path | What was actually attempted / returned | Status |
|---|---|---|
| **Connected GitHub repository API** | Exact branch, commits and diff fetched. Corrected fixture and report read. A pinned WebP image from the unchanged demo was successfully retrieved in base64 (Git blob **aa7a0ecbeb020cd81ce25d09e85cb5954c6565fe**). | **Individual objects readable**; the connector returns content/base64 but exposes **no compatible complete-directory/ZIP → local sandbox materialization** here. |
| **Local mount and authorized existing files** | Checked /mnt/data; no candidate subtree or ZIP. Searched accessible Library/conversation for an exact Stage13 preview archive; only older TALABOT materials were surfaced. No older source or stand-in assets were substituted. | **No exact bundle** |
| **Alternative direct HTTPS archive HEAD, not Git clone** | Tried one curl HEAD to codeload.github.com for commit 3f74b29a; it failed: **curl (6): Could not resolve host: codeload.github.com**. GitHub HEAD showed the same DNS class. No archive bytes downloaded. Did **not** repeat old Git ls-remote/clone as a new test. | **Container DNS/outbound transport blocked**, not a failed preview. |
| **Alternative file downloader** | Downloader rejected unviewable archive URL; public web fetch of that URL returned DisabledError. | **URL approval/fetch boundary** |
| **Browser loopback** | Not started, because a partial HTML copy without all immutable images/assets would violate exact-artifact test scope. | **Not executed** |

**Blocker diagnosis:** GitHub connector access works for *individual* text and binary blobs. The available local test runner lacks a supported way to **materialize the complete 59-path immutable corrected preview directory** as a local directory/ZIP; direct outbound GitHub archive DNS is also unavailable. This is a **connector-to-local-runner artifact-transfer gap**, not a missing browser installation, a production-auth problem, a code execution failure, a requirement for paid hosting, or a reason to change Cloudflare/Supabase.

**Shortest no-owner-action internal handoff:** use the programmer/source custodian's **already-authorized workspace** to export the exact corrected commit preview subtree as a ZIP or directory copy and transfer it using an approved existing QA file handoff to the independent tester; include all unchanged assets and corrected fixture. If the QA executor already has archive-download access, a pinned GitHub commit archive is equivalent. Verify exact SHA and fixture blob against this report on receipt. Do not rehash historical unchanged assets without a mismatch reason. **Nothing was exported or transferred here, no new task opened, no owner equipment/subscription/technical action requested.**

## 3. Executable QA case matrix — honest numerator/denominator

| Case | Requested browser action | Result on corrected 3f74b29a |
|---|---|---|
| S10-01 | Open Home Dynamic Marketplace B without ChatGPT/TALABOT login | **BLOCKED — not executed**; no screenshot/DOM/login evidence |
| S10-02 | Categories/campaigns/DineOut Premium Gold | **BLOCKED — not executed** |
| S10-03 | Open Restaurant Details v1.6 | **BLOCKED — not executed** |
| S10-04 | Direction A required/optional extras and quantity | **BLOCKED — not executed** |
| S10-05 | Add/adjust fake cart and return | **BLOCKED — not executed** |
| S10-06 | Attempt checkout, real payment and messaging; no real effect or false success | **BLOCKED — not executed** |
| S10-07 | RU/EN browser defaults, manual switch, reload and explicit ?lang | **BLOCKED — not executed**; one-line fix verified SOURCE ONLY |
| S10-08 | 320, 360, 390, 430 × RU/EN layout | **BLOCKED — 0/8 viewport-language cells executed** |

**Real execution counts:** **0/8** app scenarios; **0/8** viewport-language cells; **0** Chromium page navigations; **0** captured HTTP request/response/requestfailed traces; **0** console traces; **0** DOM measurements; **0** real screenshots; **0** physical iPhone Safari tests. No screenshot, request log, or E2E PASS is fabricated. The absence of browser observations is **not** proof that the page makes zero external requests; likewise it is **not** a proven production-security failure.

## 4. Network, financial safety, language and design decisions

- **No-production connectivity:** Stage11 documented a fake Supabase session and RPC adapter, demo-only mutations, blocked fetch/XHR/WebSocket/EventSource and CSP connect-src none. Stage13 did not alter those files. **Static source safeguards remain preserved**, but **actual runtime zero-egress is not verified**. A browser request attempt to *any* off-lab origin must stop the future test whether it succeeds or is blocked.
- **Real checkout and payments:** No click or real transaction executed. **Source-only mock blocking** is inherited, not a current functional PASS. No claim of zero production-side effects from an unexecuted browser.
- **RU/EN:** The deterministic source cause of forced RU is removed, but EN→refresh→EN, RU→refresh→RU and first-visit English require real browser results. Existing ?lang precedence was not altered in Stage13 and remains an identified test dimension; do not infer an approved precedence change.
- **Protected design:** original Home B, Restaurant v1.6, Customization A, DineOut Gold, original logo/palette/styles are untouched by Stage13, establishing **unchanged Git source identity**. Actual pixel comparison at requested sizes was **not executed**.
- **Deferred, untouched:** historical dark pilot login colours; synthetic demo notice 11px white on orange with historical contrast ~3.54:1. These are not permissions for design modifications. Physical iPhone Safari remains separate from Chromium.

## 5. Next runner method and exact closure gates

After an authorized **existing-artifact** transfer (not a rewrite, CI job or new service), use the installed Chromium/Playwright under a fresh no-credentials browser profile and an egress-denied **loopback-only** static server. Record *all attempted and failed* requests, responses, redirects, fonts/images/scripts, fetch, XHR, WebSocket, form/navigation, CSP failures, console, and DOM dimensions. **Stop on the first off-loopback request attempt; no production access.** Then execute S10-01..08, record real screenshots and width/overflow/target boxes for each RU/EN viewport, verify no real checkout/finance/message request and no fake success, and assert saved language persistence across reload. Test explicit URL language selection independently. Do not re-run formal C-01.

| Gate | Current result | Objective closure proof / evidence owner |
|---|---|---|
| Stage13 P2 code delta | **VERIFIED SOURCE** | Exact corrected fixture blob and minimal diff already established; no programmer rework requested. |
| Complete runnable bundle | **BLOCKED** | Existing source custodian supplies exact immutable 59-path corrected preview archive through an approved internal route; QA confirms file identity. |
| Browser/network no-production | **UNTESTED** | Independent QA captures attempted requests, no off-lab attempts, no external login/redirect, CSP+console evidence. |
| No real order/payment | **UNTESTED** | In-browser negative checkout and mock side-effect evidence; zero real backend requests / false success. |
| RU/EN and 320–430 | **UNTESTED** | 8/8 requested viewport-language cells, manual/reload/browser-first-visit language results, original visual comparison screenshots and DOM metrics. |
| iPhone Safari | **UNTESTED** | Only actual physical-device evidence can confer Safari-specific PASS. |
| Free public static link | **NO-GO** | Separate static-only HTTPS origin (e.g. distinct free Cloudflare Pages pages.dev project with no production bindings, Workers/Functions or secrets) can be **evaluated later**, with publisher feasibility, independent security/visual signoff and explicit owner approval of exact SHA+hostname. Not created or published. |
| Formal QA, G1 and PHASE2 | **NO-GO** | Unchanged formal project gates; a visual demo cannot close C-01 or production acceptance. |

## 6. Final disposition and safety boundary

**Independent Stage14 decision:** the **single source P2 language correction is verified** against the exact corrected commit, but the required **executable browser/security/visual proof is BLOCKED by immutable artifact transport**. This is **not** a PASS, not a reproduced UI/app defect, and not a license to launch a Safari link. The only dependency is an **internal existing-file handoff** from the source-owning technical role to the existing QA runner; the owner is not asked for equipment, payment or technical steps. Keep the candidate isolated. Do not auto-dispatch new roles or reopen previous accepted audits.

**No changes made** to code, original design, demo guards, SQL, Supabase, Cloudflare, CI, main, or production. No real customer credentials, orders, payments, C-01, deployment, force push or merge. This report alone is added to an isolated docs review branch. **PHASE2: NO-GO**.
