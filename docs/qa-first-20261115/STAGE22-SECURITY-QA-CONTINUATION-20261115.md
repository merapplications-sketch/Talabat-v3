# TALABOT — Stage 22 / Independent security QA continuation

**Date:** 2026-11-15 01:36 Asia/Dushanbe (2026-11-14T20:36Z).
**Assignment:** [existing Issue #48](https://github.com/merapplications-sketch/Talabat-v3/issues/48) and [master #26](https://github.com/merapplications-sketch/Talabat-v3/issues/26).
**Target:** https://talabot-safari-demo-20261115.pages.dev/
**Decision:** **PLAYWRIGHT/CDP HOOKS AVAILABLE / GUARDED LIVE ACCESS BLOCKED BY ADMINISTRATOR / SECURITY AND FULL INTERACTION NO-GO / PHASE2 NO-GO.**

This is a continuation of Stage22, not a new stage. No source, ZIP, CSS, product, Cloudflare, Supabase, CI, SQL, account, production or paid service was modified.

## 1. Previously accepted evidence preserved — not repeated

Read the latest [Issue #48 PM continuation](https://github.com/merapplications-sketch/Talabat-v3/issues/48#issuecomment-6883793507), including:
- [Russian iPhone visual screenshots](https://github.com/merapplications-sketch/Talabat-v3/issues/48#issuecomment-6883614942): accepted within their limited iOS embedded-viewer scope.
- [Live Russian customization, fake cart and mock checkout screenshots](https://github.com/merapplications-sketch/Talabat-v3/issues/48#issuecomment-6883696706): quantity 2, 27 TJS cart, 39 TJS checkout; PM already verified the 12 TJS synthetic delivery fee explains the difference. **Not a proven price bug.** No completed slide action.
- [Native iPhone Safari Private English home](https://github.com/merapplications-sketch/Talabat-v3/issues/48#issuecomment-6883745392): limited English visual proof already accepted; language persistence on reload not proven.
- [Earlier passive security headers](https://github.com/merapplications-sketch/Talabat-v3/issues/48#issuecomment-6883258108): third-party analyzer reported presence of CSP, nosniff, Referrer-Policy and Permissions-Policy. **Not a new raw HAR or complete CSP enforcement test.**
- PM reports Cloudflare Browser Run CDP previously returned **HTTP 401**; no permission change, token workaround, paid use or repeat probe was attempted.

No new source/ZIP audits or redundant phone screenshot requests were performed.

## 2. New actual Playwright capability gate

The local QA runtime has Chromium **144.0.7559.96** and Python Playwright 1.57.0. Before navigation, an **anonymous disposable Chromium context** was configured with:
- service workers blocked, downloads disabled; incidental preflight viewport 390×844 (not UX test evidence).
- **HTTP route interception installed before navigation.** Only HTTPS requests to exact hostname talabot-safari-demo-20261115.pages.dev on port 443 could continue. All other attempted URLs would be logged and aborted.
- **WebSocket interception installed before navigation**; non-allowlisted WS destinations logged and closed.
- Request, response, requestfailed, websocket, console and pageerror handlers; Playwright HAR recording enabled.

**Preflight DNS:** OS getaddrinfo for the Pages hostname returned **gaierror [Errno -3] Temporary failure in name resolution**.

**Single guarded live-navigation attempt:** Chromium returned **net::ERR_BLOCKED_BY_ADMINISTRATOR** from Page.goto to the approved HTTPS origin, waiting for DOMContentLoaded. It occurred **before any request event could be observed**. Results from the instrumented browser:
- 0 request events.
- 0 response or response-header events.
- 0 requestfailed events (administrator rejection was reported at navigation level).
- 0 WebSocket events.
- 0 page console or JavaScript error events.
- 0 outside-origin attempts reaching the interception hooks.
- HAR generated with **one page metadata record and zero entries**; **this is NOT evidence of zero application egress**.
- Attempt to screenshot yielded **Page.captureScreenshot: Unable to capture screenshot**; there is **no actual website screenshot**. This is an environment capture failure, **not** a TALABOT UI defect.

**Exact genuine evidence attached within the same docs-only branch:**
- [Playwright-generated, empty initial navigation HAR](evidence/initial_navigation.har).
- [Structured request-gate and browser error record](evidence/network_gate_evidence.json).

Local artifact hashes (at capture time, not equivalent to hosted-site source hashes):
HAR SHA256: 8943235f62877efc1e90f3419419830bdce9116470472ee2e8387aaaef99f6fe.
JSON SHA256: 3b11e94f8b6db2e6a0817392ab2fa0194c826e0d760b1892c215b23d77d6f844.

**CAPABILITY finding:** HTTP/WS interception APIs exist and hooks were installed fail-closed before navigation, but the browser was **not allowed to reach the public Pages origin**. No live-site network capture or UI execution happened. The lack of logs is attributable to environment policy and must never be counted as a network security PASS.

## 3. Requested case outcomes

| Case | Result in this continuation | Evidence/constraint |
|---|---|---|
| Authorized Playwright/CDP-style HTTP/WS capture and host allowlist | **LOCAL CAPABILITY PRESENT** | Pre-navigation route, route_web_socket and HAR configured |
| Reach live published Pages site in same guarded environment | **BLOCKED** | DNS failure and net::ERR_BLOCKED_BY_ADMINISTRATOR |
| HTTP responses, CSP/MIME/security headers, attempted and failed egress | **UNTESTED ON LIVE SITE** | No navigation response; empty HAR is not safety evidence |
| Full dummy Slide to place order gesture, demo_only, no real order/payment and no false success | **NOT RUN** | Must not click until network hard gate passes |
| RU/EN manual language choice persisted across actual reload and query precedence | **NOT RUN** | Existing iPhone RU/EN visual proofs preserved; no reload evidence |
| Responsive 320/360/390/430 × RU/EN, DOM overflow, target measurements/screenshots | **0/8 new runs** | 390 preflight viewport does not count as a rendered site |
| English customization UI labels Размер порции / Добавки | **NOT REPRODUCED LIVE** | Previously reported P2, still open for scoped follow-up |
| Delivery-fee breakdown discoverability | **NOT RUN** | PM already confirmed 27+12=39 synthetic arithmetic; visibility untested |
| Bottom fixed navigation obscuring buttons | **NOT RUN** | No DOM rectangles or clicks; do not assume a defect |
| Demo banner white-on-orange contrast | **OWNER-DEFERRED P2** | Historic ~3.54:1; no design change authorized |
| iPhone Safari visuals | **HISTORICAL LIMITED ACCEPTANCE** | Actual owner evidence preserved, not duplicated |

**New true executed user journeys: 0.** No real account, order, wallet update, payment, checkout gesture or external production service call was performed. No new production vulnerability was reproduced.

## 4. Precise unblock requirement without owner work or paid services

The missing combination is **(A) an already-authorized browser with network access to the existing published Pages origin AND (B) CDP/Playwright interception active before first navigation**, recording every successful, attempted and blocked HTTP(S)/WS/redirect request, response status/headers, CSP violations, console events, real screenshots and DOM geometry while denying off-origin traffic.

The **local** Playwright browser has capture APIs but cannot access the site due to administrator policy and DNS. The previously used remote TinyFish browser reaches Pages, but **does not expose CDP/HAR events or a fail-closed interceptor**. The prior Cloudflare Browser Run CDP attempt received **401** and is not an authorized free alternative now. **Do not bypass these controls, buy a subscription, ask for passwords or require the owner to set up a device.** QA platform/operator may supply an existing approved no-extra-cost browser with both properties; otherwise record this hard blocker in the same Issue #48 until available.

Only when an approved combined environment actually works: verify network interception with real requests; stop on the first outside-host attempt even if blocked; then execute the already-planned fake Slide to place order, ensure no real order/payment or false success; test RU/EN reload, 320–430, translation, fee breakdown and fixed-footer overlap. Keep data fictitious, no live logins, no new phase.

## 5. GO / NO-GO

- Playwright and HTTP/WS interceptors **AVAILABLE LOCALLY**.
- Live Pages access under the allowed guarded browser **BLOCKED**.
- Successful live HAR/security-egress proof **NOT AVAILABLE**.
- Full simulated checkout swipe and no-real-payment proof **NOT EXECUTED**.
- Manual language persistence, full size matrix and UX details **NOT EXECUTED THIS CONTINUATION**.
- **Final Stage22 security/full interaction acceptance: NO-GO (environmental blocker, not a proven application defect).**
- Already deployed static visual demo is unchanged; prior visual evidence remains valid in its narrow scope.
- Actual TALABOT product C-01/G1/release/PHASE2 remain **NO-GO**.

No changes were made to source, approved design, Cloudflare/Supabase, accounts, production, main branch, CI or financial records. Documentation and genuine preflight evidence were added only to the existing isolated Stage22 review branch.
