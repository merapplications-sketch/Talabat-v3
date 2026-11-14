# TALABOT — STAGE 22 / Independent Live Cloudflare Pages QA

**Date:** 2026-11-15 · Asia/Dushanbe  
**Assignment:** [Issue #48](https://github.com/merapplications-sketch/Talabat-v3/issues/48) / [Master #26](https://github.com/merapplications-sketch/Talabat-v3/issues/26)  
**Actual public HTTPS target:** https://talabot-safari-demo-20261115.pages.dev/  
**Mode:** Read-only Cloudflare Pages API inspection + actual anonymous browser rendering + read-only published-file/URL retrieval. No source/ZIP re-audit, code/design fix, deployment, real customer, payment or C-01.  
**Decision:** **LIVE DEPLOYMENT PASS / INITIAL ANONYMOUS HOME RENDER PASS / PARTIAL RU-EN URL RENDER PASS / SECURITY + FULL UI ACCEPTANCE NO-GO / PHASE2 NO-GO.**  

This is a **post-publication** report. The earlier Stage21 failure-to-publish report is superseded by this actual deployment. Do not treat the current NO-GO as denial of publication; it is denial of claiming all requested independent HTTP/network/security/UX tests have passed.

## 1. Actual live configuration read — not a local source claim

Cloudflare connected API was queried using GET for the named Pages projects, without writing to Cloudflare:

| Item | Independently observed Cloudflare API value |
|---|---|
| New project | talabot-safari-demo-20261115 |
| Canonical domain | talabot-safari-demo-20261115.pages.dev |
| Latest deployment ID | **636ae248-c8ac-45b9-8183-5a9fa3ddb986** |
| Latest deployment URL | https://636ae248.talabot-safari-demo-20261115.pages.dev |
| Creation time UTC | **2026-11-14T19:27:47.487559Z** |
| Stage | **deploy / success**, ended 2026-11-14T19:27:49.058576Z |
| Production configuration | Counts observed **0** for env_vars, KV, D1, R2, Durable Objects, service bindings, AI bindings, analytics datasets, Hyperdrive and Vectorize |
| Preview configuration | Same exposed binding-category counts **0** |
| Old project | Separate project **talabot-pilot-20261106** still listed, latest deployment **1a602ee4-6daa-4a76-a8aa-68339321cac5**, created 2026-11-06T13:16:51.675973Z |

**Conclusion (CONFIG PASS, limited):** new and old Pages projects are distinct, new deployment is successful, inspected configuration has no listed backend bindings. **This cannot prove the client's network requests are absent, HTTP CSP headers are served, or there is no unrelated external integration outside the inspected fields.** No billing, permissions or project settings changed.

## 2. Actual live browser and public route evidence

Independent anonymous cloud browser run: [TinyFish run 85108617-41f9-4c9a-9eb7-ca2d90b80141](https://agent.tinyfish.ai/runs/85108617-41f9-4c9a-9eb7-ca2d90b80141), **status completed**, 4 agent steps, ~48 s. No credentials, site writes or checkout. Browser engine/viewport pixel values were not exposed by this run, so **do not classify it as physical Safari or 320/360/390/430 proof**.

- **Observed UI on actual HTTPS origin:** page title **TALABOT · Customer · pilot-mobile-20261107.2**; no TALABOT or ChatGPT sign-in challenge on initial view; orange demo disclaimer **VISUAL DEMO · Fake data · No real orders or payments** visibly displayed.
- **Observed sections:** home promotional bento, category row, favourites, best offers, popular restaurants, recommendations, nearby, DineOut, discount restaurants, coupons/rewards and five-item bottom navigation. Countdown visibly decremented (agent recorded approximately 23:22:53 to 23:22:30). This is on-screen client behavior, **not server clock-sync evidence**.
- **Observed initial home image rendering:** eight distinct original-looking 3D category URLs under the same Pages origin were returned as image references and described as rendered in the anonymous browser: hamburger.webp, pizza.webp, motor-scooter.webp, basket.webp, lotion-bottle.webp, pill.webp, flowers-gifts.webp and shortcake.webp. Separate TinyFish content retrieval opened hamburger.webp, pizza.webp and pill.webp (reported 256×256 for the latter inspected image titles). **Initial-screen images observed ≠ all 45 shipped WebP independently verified live**, and no byte comparison/content-type status was captured.
- **No page-level error banner** was seen; there is **no captured browser console log**. Do not turn “no visible errors” into “zero JS console errors.”

Separate published URL reads via TinyFish content retrieval (rendered content, **not raw HTTP status/headers**):

| Live URL path | Actual observed content/result | Decision |
|---|---|---|
| / | Rendered anonymous customer homepage, eight same-origin category image links | **OBSERVED RENDER PASS** |
| /index.html | Final URL canonicalized to /; rendered home | **OBSERVED CONTENT PASS**; HTTP status/redirect code unknown |
| /demo-core.js | Returned JavaScript-looking source content including synthetic SB_URL about:blank / synthetic no-key markers | **OBSERVED CONTENT PASS**; no full response-byte hash/MIME evidence |
| /demo-fixture.js | Returned synthetic fixture content with fake customer flag | **OBSERVED CONTENT PASS** |
| /demo-guard.js | Returned demo-only action-guard content | **OBSERVED CONTENT PASS**; **does not prove GUI checkout path** |
| /assets/mobile.css and /assets/mobile.js | Returned corresponding CSS/JS-looking content | **OBSERVED CONTENT PASS** |
| /assets/driver-returns/panel.js | Returned panel JS-looking content | **OBSERVED CONTENT PASS** |
| /_headers | Returned rendered homepage instead of plain _headers configuration | **NO RAW INTERNAL _headers CONTENT OBSERVED**; whether HTTP security headers were applied is UNTESTED |
| /manifest.json | Returned rendered homepage, not internal manifest JSON | **NO INTERNAL MANIFEST CONTENT OBSERVED**; HTTP status unknown |
| /STAGE10-VALIDATION-REPORT.md and /STAGE13-P2-LANGUAGE-PERSISTENCE-REPORT.md | Returned rendered homepage, not internal report text | **NO REPORT TEXT OBSERVED**; HTTP status unknown |

**Caution:** A Pages SPA fallback can render HTML for a missing file and still return a 200/404 depending on configuration; the browser content extractor did not expose actual response codes. Do not claim the missing-file routes are true HTTP 404 or that _headers is correctly interpreted as a response security policy.

## 3. RU/EN requests — actual live, but no persistence/viewport claims

Read-only remote browser/content extraction with URLs **/?lang=ru** and **/?lang=en** on the deployed domain:

- **RU:** final URL retained ?lang=ru, document language reported **ru**, title **TALABOT · Заказ · pilot-mobile-20261107.2**, headings rendered in Russian, including “Ваши любимые снова”, “Лучшие предложения”, “Популярные рестораны”. Eight home-category image URLs returned.
- **EN:** final URL retained ?lang=en, document language reported **en**, title **TALABOT · Customer · pilot-mobile-20261107.2**, headings rendered in English, including “Your favourites again”, “Best offers”, “Popular restaurants”. Eight home-category image URLs returned.
- **?lang=tg** (non-required, observational): rendered English due to browser/default language; this is not evidence of a TG translation.

**RESULT: URL-BASED RU and EN home rendering PASS (2/2).** **Manual toggle, localStorage preservation after reload, first-visit browser-language precedence, explicit query-parameter override priority, full translations inside customization are NOT EXECUTED.** RU/EN store/food names inside fixtures can intentionally retain original-language proper names; separate those from UI labels in future visual review.

## 4. Hard security gate: no invented raw HTTP or zero-egress claim

The user/PM requires raw status and security headers for /, /index.html, executable JS, CSS and image paths, plus a complete network trace including **attempted and blocked** requests before active UI interactions.

**Actual tool limits in this session:**
- The local container tried a read-only HTTPS HEAD request to the canonical Pages URL, but DNS lookup failed with **curl (6): Could not resolve host: talabot-safari-demo-20261115.pages.dev**. Direct download helper also failed. **No local raw status/response headers could be captured**.
- Public webpage open through the normal web reader returned **DisabledError**. Remote TinyFish content retrieval and browser worked for rendered content, but **neither exposes raw HTTP response status/headers, complete browser request/requestfailed/WebSocket/redirect events or Chromium DevTools protocol trace** in this execution.
- The cloud browser run explicitly reported **raw HTTP headers and network traces unavailable**; only that it did not itself open another origin during its limited navigation. **Not opening an external page in four browser steps does NOT mean zero attempted off-origin requests.**
- Therefore: **HTTP-STATUS = UNTESTED; response Content-Security-Policy / X-Content-Type-Options / Referrer-Policy / Permissions-Policy = UNTESTED; complete external egress including blocked attempts = UNTESTED; CSS/script/image MIME = UNTESTED; CSP violation/console log = UNTESTED.**
- Source/previous ZIP checks and metadata cannot upgrade these to PASS. A CORS/CSP rejection after a malicious attempt would still need a real browser trace and evaluation.

**Safety decision:** Since an interceptor that **blocks and logs** all off-origin attempts was unavailable, the mandatory network gate did **not pass**. Consequently this reviewer **did not click into restaurant/order/payment/cart/group order**, did not perform a checkout swipe, and did not claim safe transactional results. Read-only render/GET URL observations above are separate evidence only. No real user account or production payment was used.

## 5. Actual execution matrix and known UX findings

| Case | Actual coverage | Status |
|---|---|---|
| LIVE-01 Cloudflare project identity/deployment/binding metadata | API read of both exact project names | **PASS (CONFIG READ)** |
| LIVE-02 First anonymous home and fake disclaimer | Cloud browser run completed; visible sections + logo | **PASS (INITIAL HOME ONLY)** |
| LIVE-03 Initial visible image art | Eight category WebP observed/rendered; three direct image URLs inspected | **PASS SAMPLE ONLY**, all 45 and HTTP MIME untested |
| LIVE-04 RU/EN URL pages | 2/2 site GET views with respective headings/lang attributes | **PASS URL-BASED ONLY** |
| LIVE-05 Raw HTTP CSP/security/MIME headers | No compatible HTTP response inspection | **BLOCKED/UNTESTED** |
| LIVE-06 Exhaustive request/blocked egress log | No DevTools/interceptor | **BLOCKED/UNTESTED** |
| LIVE-07 Home→Restaurant v1.6→Direction A mandatory options→fake cart/back | Not clicked without hard gate | **UNTESTED** |
| LIVE-08 Complete fake checkout and slide CTA, real-order/payment negative assertion | Not triggered without hard gate | **UNTESTED** |
| LIVE-09 Manual RU/EN toggle and reload/persistence | No manual stateful browser test | **UNTESTED** |
| LIVE-10 320/360/390/430 × RU/EN, DOM rect/scrollWidth/clientWidth | No viewport-selection or DOM metric tool | **0/8; UNTESTED** |
| LIVE-11 Physical iPhone Safari | No physical device evidence | **UNTESTED** |

**Counts:** two required URL-locale home variants observed, one initial anonymous interactive browser visit, eight on-screen category images, zero accepted 320–430 geometry matrices, zero raw HTTP security-header captures, zero full egress recordings, zero successful fake-checkout negative-path executions. **Do not report the unexecuted tests as FAILs or PASSES.**

Existing Stage16B known issues (not automatically reopened as live findings):
- **V16B-01 / P1 validation gap:** “Slide to place order” appears as an actionable-looking checkout control in previous **in-memory Chromium** evidence. Direct mock TLB.placeOrder returned demo_only previously; **actual deployed CTA full swipe and absence of false success remain UNTESTED**. No production order is claimed.
- **V16B-02 / P2 source/UX observation:** prior **in-memory customization** retained Russian UI group labels “Размер порции (обязательно выбрать)” and “Добавки” under English interface. Live home RU/EN translation confirmed above; **live product customization still NOT TESTED**. Product names can remain native-language; interface labels should be separately evaluated.
- **V16B-03 / P2 accessibility (DEFERRED):** prior demo banner design white normal small text over **#F1511B** yields **3.5396:1** contrast using WCAG relative luminance formula, below normal text AA **4.5:1**; **this is a calculation for the previously documented CSS colours, not computed-style inspection of the active site**. The owner deferred palette/notice edits. No modification permitted.
- **V16B-04 / image placeholder ambiguity:** current live **home** displays eight category WebP; this improves evidence over the earlier about:blank harness but **does not resolve restaurant/menu placeholder status** until details are visited.
- **V16B-05 / mobile long strings:** widths, inner clipping and touch targets remain unmeasured on the deployed site; do not infer PASS from a single unspecified-width mobile-looking remote view.
- **V16B-07 / fake offers:** synthetic 25%-off and wallet/points visuals are fictitious; live disclaimer observed, but this is not verification of business prices or real promotions.

**Confirmed new production vulnerabilities/real orders:** none demonstrated. **Critical unclosed proof gap remains network/security instrumentation**; do not classify lack of proof as an exploited P0 finding.

## 6. Independent decision, exact closure owners, non-action record

**Verdict for public-demo owner read-only Safari sign-off: NO-GO at this security QA stage.** The URL is **already published and visible**, and isolated-source/static Pages configuration plus home rendering are observed, but **full security and interaction proof is missing**. Do not call it audited-safe, formally accepted or ready to extend beyond approved visual-preview scope.

**Objective closure prerequisites within existing Stage22 scope:**
1. **Publisher / technical HTTP reader:** from an approved network-accessible read-only environment record GET/HEAD **status codes and raw response headers** for /, /index.html, /demo-core.js, /demo-fixture.js, /demo-guard.js, mobile.css/js, sample WebP, _headers and an excluded internal report. Verify the real Content-Security-Policy, X-Content-Type-Options, Referrer-Policy, Permissions-Policy, content types, file bytes where appropriate. **Do not modify Pages**.
2. **Independent security QA:** on a fresh anonymous browser profile with an **interception layer that denies/logs non-specified Pages origin before navigation**, capture attempted/failed/successful resource requests, redirects, XHR/fetch, WebSocket, script/font/image, form and CSP console; stop on first unexpected attempt. No production account.
3. **Independent UX/QA on the same exact deployed origin:** only **after** step 2, record screenshot and DOM bounding boxes/overflow for 320/360/390/430 in RU/EN, manual language refresh, restaurant/details, Direction A required group and English interface copy, dummy cart/back, and GUI swipe negative case proving no real order/payment or false success. Physical iPhone Safari separately requires actual device evidence.
4. **PM:** review evidence and decide whether the existing approved static-demo URL can be described as security/UX accepted for owner's read-only visual use; no new publication consent or deployment requested. Keep historical pilot and actual product isolated.

**Non-actions:** No new deployment, CI, Git integration, Cloudflare/Supabase changes, code/colour/design edits, production service request, real user/order/payment, account authentication, financial operation or C-01. No new task opened by this auditor.

**Formal TALABOT production release / G1 / PHASE2: NO-GO**, unchanged by this already-live visual-demo assessment.

**Evidence anchors:** 
- [Active demo](https://talabot-safari-demo-20261115.pages.dev/)
- [Independent visual browser run](https://agent.tinyfish.ai/runs/85108617-41f9-4c9a-9eb7-ca2d90b80141)
- [Existing Stage16B issues/historical evidence](https://github.com/merapplications-sketch/Talabat-v3/blob/89823a116c9e49e004ad5c2e2a421cc9b15ba08d/docs/qa-first-20261114/STAGE16B-FINDINGS-PRIORITIES-NEXT-STEP-AR.md)
- [Manager assignment](https://github.com/merapplications-sketch/Talabat-v3/issues/48)
