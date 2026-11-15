# TALABOT — STAGE 22 / Independent security acceptance of live HAR, mock checkout and screenshots

**Date:** 2026-11-15, Asia/Dushanbe.  
**Assignment:** [Existing Stage22 Issue #48](https://github.com/merapplications-sketch/Talabat-v3/issues/48), [master Issue #26](https://github.com/merapplications-sketch/Talabat-v3/issues/26).  
**Role:** Independent security/technical auditor — evidence review only; no new test, Stage, issue, code patch, merge, publishing, Cloudflare/Supabase/production or cost.  
**Actual live demo:** https://talabot-safari-demo-20261115.pages.dev/ (already published, synthetic data only).  
**Evidence-producing execution:** [GitHub Actions run 43694105608](https://github.com/merapplications-sketch/Talabat-v3/actions/runs/43694105608), job 132750740903, **success**, executable QA SHA **9ce0909a47248e696c2611116b0bf3c36198b319**, isolated review/stage22-one-shot-qa-20261115.  
**Original approved synthetic demo source:** 3f74b29a7c4bcc89cef9e25dd73f574448ab7896.  
**Independent decision:** **ACCEPT — demonstrated bounded synthetic browser security gate and mock checkout negative path; DESIGN/UX SIGNOFF PENDING; complete Stage22 owner-facing acceptance PENDING, NOT RELEASE GO; full production/C-01/G1/PHASE2 NO-GO.**

## 1. Actual evidence independently obtained and verified

The connected GitHub Actions tool provided **artifact 14153557488**; this review independently downloaded its binary bytes into the QA filesystem, inspected all five files and their original PNG pixels, parsed the case JSON and HAR, and read both executed harness code and workflow as well as job metadata. This is **NOT** acceptance based solely on the PM summary.

- [Actions artifact](https://github.com/merapplications-sketch/Talabat-v3/actions/runs/43694105608/artifacts/14153557488): file name **talabot-stage22-qa-synthetic-only.zip**, size **558,036 bytes**, independent SHA256 **7b435543647cba9cd6baa0ec0d3708a585948c14c9306d44361b6f790bc400a1**; ZIP file-integrity check **PASS**. The artifact has **five** entries, and GitHub reports expiration **2026-11-16T08:21:48Z** (do not invent durable raw-file URLs after expiry).
- **case-result.json**, SHA256 **737b5b776c8c6ad74fe756b7f1b92c270b254bc6756749a3510259711d727581**. Explicit status **PASS_GUARDED_SYNTHETIC_SCOPE**. Its network, fake-cart fixture, real pointer interactions, blocked-action counter, layout and display findings were read, not just its summary.
- **stage22-network-sanitized.har**, 162,139 bytes, SHA256 **6e59e0802874d30d3b80893bfcc0fe4ae7017c77d1affa3c80181b34925abad2**, JSON-parsed and independently counted. This is a **REAL hosted-session HAR**, not the earlier empty administrator-blocked preflight HAR.
- **checkout-before.png**, 390×1482, SHA256 **15c3dac04c902d0df7a8a3d21023f9f99afaa95a4c6fa221d3c1a1802103f4f7**.
- **checkout-after.png**, 390×1482, SHA256 **c89da33559388765e194723a839dafc2e18bc5e5af0808127d84a49fb0506a8e**.
- **en-home-390.png**, 390×2445, SHA256 **afa6530d29b6a10add1c8b3fa8ca3833d2eabb4877f5ec38090a281a56e1d9d0**.

All screenshots were **opened and visually reviewed from the actual PNGs**. They are entirely synthetic demo UI, not real patient/customer data. No current visual from any image-search service is used as evidence. No new browser session was run.

### HAR independent count and confidentiality review

| Property | Parsed original sanitized HAR |
|---|---|
| Entries total | **57** |
| HTTP methods | **57 GET; 0 POST/PUT/PATCH/DELETE** |
| Hosts | **56** exact canonical Pages host; **1** deliberately synthetic external qa-stage22-denied.invalid |
| Response statuses | **56 HTTP 200**, **1 status -1** for blocked synthetic off-origin attempt |
| Content types | **24 image/webp, 18 text/html, 10 application/javascript, 4 text/css, 1 x-unknown** |
| HTTP redirects | **0** observed HAR redirects |
| Attempted off-host app traffic | **0** within captured scope; the sole outside-host request was test-injected and blocked |
| WebSockets, page errors, console errors | **0** in case-result.json during this run |

The **negative off-host control** was explicitly attempted through the browser and blocked with **net::ERR_BLOCKED_BY_CLIENT**. Code installed exact-origin HTTP routing and WebSocket deny **before navigation**, disabled service workers and used a disposable anonymous Chromium context. The one denied .invalid request **must never be misclassified as a TALABOT external request or a successful real network connection**.

HAR sanitization was separately checked: no Authorization/Cookie/Set-Cookie headers, stored request postData, response bodies, passwords, access tokens, Supabase host, production endpoints, user email or credentials were present in the retained content. It contains user agent and benign fake/demo URL paths; the artifact nevertheless remains test evidence with no necessity to publish its full bytes in a new permanent public repository file.

**Boundary:** absence of off-origin requests and write methods is established for **this one browser session and captured routes**, not mathematically for all browser/client behaviors or every application operation. Zero observed WebSocket attempts is different from proving every imaginable attempted WebSocket is denied. The test is explicitly not a formal product penetration test.

## 2. Real GUI slide: independently ACCEPTED within mock scope

The executed test harness (docs/qa-first-20261115/stage22_guarded_browser_test.py at 9ce0909a) verified **load**, loaded demo guards on both the TLB API and global place handler, valid fabricated customer phone/address presence, store open, no range blocker, valid required selection, no busy state, and an actually **enabled** slider.

**Recorded DOM pointer trace from case-result.json:**
- Pointer down acquired original **HOLD** object, document visible, enabled thumb.
- The test used measured HOLD.max **300px** and recorded progress **1.00**, above the source minimum **0.96**.
- Pointer-up occurred, followed by lostpointercapture; this corrects the previously inconclusive first attempt in run 43684336979.
- **window.__demoBlockedActions incremented by exactly +1**.
- After action: page view **pay**, busy **false**, success_visible **false**, no real order view.
- The independently opened **checkout-after.png** displays the red toast **“DEMO: No real orders or payments”**. **checkout-before.png** shows the same synthetic checkout screen before the gesture.
- HAR: **0 POST**, **no production hostname** and no outside-host application request; no payment, real customer, account login or actual transaction was made.

**Judgment for V16B-01 / IPH22-11:** **PASS CLOSED for this single correctly instrumented synthetic GUI pointer swipe**, not a claim that every potential alternative order entry path or real server transaction has been tested. The earlier P1 “counter 0” test is **superseded as a harness-precondition failure**, not a real app failure. No modification to the published code or financial configuration was required.

**Fixture limitation:** test code sets fake cart state in the browser specifically to exercise the true rendered GUI slider; it does **not** prove a complete natural user navigation from Home to Customization to Cart. That visual journey is already evidenced separately by owner's earlier RU screenshots, and is not rerun here.

## 3. Actual UI evidence: what the screenshots prove and do NOT prove

**Home EN at 390:** original-looking logo, promo bento, category 3D images, restaurants, recommendations, offers, DineOut, and navigation are visibly rendered. Existing store/product names are partly Cyrillic as **fixture proper names**, which is not automatically a translation defect. Long names are ellipsized in summary cards. Full-page screenshot alone does not establish all touch target sizes, accessibility or 320–430 behavioral parity.

**Payment EN before/after at 390:** fake address and phone-free presentation, cash-to-courier choice, payment-method explanatory copy, a fixed/floating **Slide to place order** dock, and order summary. **Summary numbers seen in the actual PNG**: subtotal **30 TJS**, discount **−4.5 TJS**, happy-hour discount **−3 TJS**, delivery **10 TJS**, total **32.5 TJS**. Arithmetic: **30−4.5−3+10=32.5**; this is correct for this synthetic fixture. The delivery charge is **explicitly visible in the order summary after scrolling**; the screenshot does not establish that more granular base/extra quote decomposition is readily discoverable at 320px or without scrolling. Earlier owner fixture **27 + 12 = 39 TJS** used another synthetic quote and was already reconciled; not a proven real price defect.

**Sticky checkout controls:** in the 390px PNG, the cash option is visible and the slider dock does not visibly cover that choice. The full-page screenshot does **not** establish actual scroll/tap accessibility at 320/360/430 or all modal states. Designer must not label the fixed bar defective from the screenshot layout alone; must confirm any occlusion with visible element rectangles.

**P2 image requests: genuinely observed, visual impact unresolved.** Independent HAR contains **16 first-party GETs** to **8 unique URL paths** with unexpanded template expressions, including forms such as **/$%7Besc(st.cover_url)%7D**, **/$%7BA3(d[5])%7D**, **/$%7Besc(b.image_url)%7D**. All returned **HTTP 200 / text/html** from SPA fallback, **NOT image assets**. The eight main home WebP category images visibly render and the test's **broken_image_paths:[] check was performed on the checkout DOM only**, so it **cannot certify home/restaurant/menu images**. This is a confirmed bad-path/network-content observation, **P2 impact investigation for UX**, not evidence of broad missing image art and not an external egress violation.

## 4. Existing-risk handoff to the TALABOT designer (in the SAME #48)

**Security-to-UX independent coordination required; no new issue or Stage, no autonomous redesign:**

| ID / priority | Designer's exact review from already accepted evidence | Closure criterion / no redundant test |
|---|---|---|
| **UX22-I / P2** | Cross-reference **8 literal-template image paths / 16 responses** to *visible* img elements in 390 Home and prior RU iPhone merchant/detail screenshots. Are any visible covers/tiles broken, vs inactive template markup/hidden placeholders? | State confirmed visible defect with exact route/element/screenshots or **NO VISIBLE IMPACT PROVEN**. Images do display on home. No mass image replacement. |
| **UX22-L / P2** | Earlier English customization source/fixture has group-label UI strings **“Размер порции” / “Добавки”**. Distinguish actual UI group headings from fictional store/item names that may remain Cyrillic. | Independent English customization UX classification, specific strings/screens, correct expected interface vs fixture names; **not** infer from current EN Home screenshot alone. |
| **UX22-F / P2** | Checkout at 390 shows **Delivery 10 TJS**, total **32.5**, cash choice and dock. Earlier owner RU cart/checkout **27+12=39** also arithmetically valid. | Determine whether fee detail/breakdown is understandable/scroll-reachable at narrow sizes and whether footer masks any payment control. Distinguish readability from a computation bug. |
| **UX22-N / P2 potential** | Long fictional merchant/item names ellipsized on 390px home and previous RU iPhone shots. | Decide whether truncation preserves readable details in merchant/product view; actual tappable UI vs expected compact-card ellipsis. |
| **UX22-C / P2 OWNER DEFERRED** | Banner white text on original orange ~3.54:1 normal-text contrast under AA 4.5. Older dark pilot login colours are also DEFERRED. | Record/accessibility classification only. **NO** color, branding, font or approved layout change without express owner permission. |

The responsible designer should return **UX ACCEPT / UX PARTIAL / UX REJECT with evidence IDs** to **existing Issue #48**, for PM to consolidate. If the designer cannot be reactivated through this message, PM must hand off in their authorized role channel; a GitHub comment alone does not run a paused worker. No source code changes or re-performance of accepted 8/8 viewport home sweeps, ZIP, Safari screenshots or security actions.

## 5. Remaining security risks and final GO/NO-GO

**Independent security decision: ACCEPT (synthetic, bounded):**
1. Exact live host with pre-navigation allowlist, successful one-off synthetic off-origin block and request/HAR trace — accepted within observed session.
2. Real GUI slide under valid mock conditions — passed with one blocked-action invocation, unchanged payment view and no false success; all HAR methods GET.
3. No evidence of real-production endpoint call, real login, submitted order, payment, WS or externally transmitted data **in this session**.
4. Actual HTTP root, guard and fixture SHA aligned with accepted static package, verified 200/MIME/CSP in producer's case-result; existing passive security-header report remains separate.

**Residuals:**
- Complete demo-wide threat model/pentest and all other possible UI mutations **not tested**; scope remains a single guarded synthetic journey, not universal non-exploitability.
- Browser HAR cannot establish what an absent/unexercised UI branch might do, including future changes. Site has inline scripts permitted by CSP (accepted static implementation), and historical hardening notes about HSTS / frame restrictions remain **defense-in-depth** observations, not new demonstrated malicious connections.
- Eight placeholder URL paths return HTML as images; no proven displayed failure yet, but requires designer classification before claiming complete visual acceptance.
- EN customization group labels, fee breakdown discoverability and narrow footer controls require **independent designer verdict**, not an auditor's invention.
- Manual RU↔EN choice preserved through reload across user sessions remains outside current proof; earlier hosted 8/8 document language/banner/zero-global-overflow and EN explicit-query reload are **already accepted** and not rerun.
- Actual native iPhone Safari RU/EN initial viewing accepted in owner's earlier limited images; no production backend acceptance inferred.

**Final classification:**
- **GO / ACCEPT for Stage22 synthetic security hard gate and one GUI fake checkout negative test.**
- **PARTIAL / pending for Stage22 complete security + design/UX joint owner-facing signoff**, contingent on a designer's evidence classification and PM consolidated decision. Do not claim “full Stage22 GO” merely because the GitHub Actions run is green.
- **NO-GO for actual TALABOT production, C-01, G1, integrated E2E, financial processing and PHASE2.**
- No further test run, code change, merge, deploy, app/design/palette change, Cloudflare/Supabase/API/database action, paid service or new Stage was performed by this reviewer. This report is documentation-only on the **existing isolated Stage22 QA branch**, linked to issues #48 and #26.
