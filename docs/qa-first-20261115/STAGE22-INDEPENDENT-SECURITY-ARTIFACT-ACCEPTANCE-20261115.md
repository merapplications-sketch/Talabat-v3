# TALABOT — STAGE 22 / Independent Security QA: Actual HAR, GUI Fake Checkout and Visual Evidence

**Date:** 15 November 2026, Asia/Dushanbe  
**Sole assignment:** [Issue #48](https://github.com/merapplications-sketch/Talabat-v3/issues/48) · [Management #26](https://github.com/merapplications-sketch/Talabat-v3/issues/26). **No new phase, tests, product changes or deployment.**  
**Published demo:** https://talabot-safari-demo-20261115.pages.dev/  
**Executed reference:** [GitHub Actions #43694105608](https://github.com/merapplications-sketch/Talabat-v3/actions/runs/43694105608), job **132750740903**, test-code SHA **9ce0909a47248e696c2611116b0bf3c36198b319**, conclusion **success**.  
**Immutable deployed synthetic customer code:** approved candidate **3f74b29a7c4bcc89cef9e25dd73f574448ab7896**; no changes made.  
**Independent technical verdict:** **ACCEPT — guarded synthetic-demo security and GUI mock-order denial for this one recorded live session.** **Do not declare all of Stage22 UX/design accepted; independent designer review remains PENDING.** Real production TALABOT C-01/G1/release/PHASE2: **NO-GO**.

## 1. Artifact intake and independent checks (performed, not a repeat browser run)

Downloaded original GitHub Actions artifact **14153557488** `talabot-stage22-qa-synthetic-only`, **558,036 bytes**, ZIP SHA256 **7b435543647cba9cd6baa0ec0d3708a585948c14c9306d44361b6f790bc400a1**; independently computed hash matched the source; ZIP CRC test **5/5 PASS**. Source [artifact link](https://github.com/merapplications-sketch/Talabat-v3/actions/runs/43694105608/artifacts/14153557488), expires **2026-11-16T08:21:48Z** per GitHub. No private customer material was used. Five files extracted/read in the existing authorized QA container:

| File | Actual bytes / dimension | Independently calculated SHA256 |
|---|---|---|
| `case-result.json` | 17,404 B | `737b5b776c8c6ad74fe756b7f1b92c270b254bc6756749a3510259711d727581` |
| `stage22-network-sanitized.har` | 162,139 B | `6e59e0802874d30d3b80893bfcc0fe4ae7017c77d1affa3c80181b34925abad2` |
| `checkout-before.png` | 390×1482, 107,387 B | `15c3dac04c902d0df7a8a3d21023f9f99afaa95a4c6fa221d3c1a1802103f4f7` |
| `checkout-after.png` | 390×1482, 111,473 B | `c89da33559388765e194723a839dafc2e18bc5e5af0808127d84a49fb0506a8e` |
| `en-home-390.png` | 390×2445, 334,102 B | `afa6530d29b6a10add1c8b3fa8ca3833d2eabb4877f5ec38090a281a56e1d9d0` |

Inspected all three **original** screenshots visually, with no redraw or reconstruction. Before/after checkout image difference is confined to **bounding rectangle x=83–307, y=688–766**, corresponding to the red mock-blocking notification; no order-success view replaces the checkout screen. The full-page screenshots are **one 390px English fixture scenario**, not 320/360/430 checkout UX certification.

## 2. Actual HAR independent security audit

Parsed the real sanitized HAR as JSON. **57 entries**: **56 first-party HTTPS GET** to `talabot-safari-demo-20261115.pages.dev` returned **HTTP 200**, and **1 intentionally synthesized** GET to `qa-stage22-denied.invalid/never-sent` was denied (`status:-1`, `net::ERR_BLOCKED_BY_CLIENT`). **0 POST**, **0 unexpected off-host URLs**, **0 recorded WebSocket attempts**, **0 logged page errors**, **0 browser console errors** in `case-result.json`. The JS guard registered HTTP+WS blocking **before navigation** and disabled service workers, independently corroborated in the exact pinned test script `docs/qa-first-20261115/stage22_guarded_browser_test.py`.

HAR response MIME counts: **24 image/webp**, **18 text/html**, **10 application/javascript**, **4 text/css**, **1 unknown** for the deliberately blocked external request. Actual direct-page preflight in `case-result.json`: `/`, `/demo-guard.js`, `/demo-fixture.js`, sample `/assets/3d/hamburger.webp` each **200**, expected HTML/JS/WebP MIME, and expected SHA256 for source HTML/guard/fixture. Root response included actual `connect-src 'none'; form-action 'none'` CSP and `X-Content-Type-Options:nosniff`.

The HAR is **redacted**: no Authorization/Cookie/Set-Cookie header or `postData` observed in inspected entries; the writer removed those fields and response bodies before exporting. No production hostname, payment request, account/API credential or recorded externally allowed call appears in this bounded trace.

**Scope caution:** One guarded Chromium session with an intercepted deny probe proves **no unexpected outside-origin connection observed for the exercised paths**, not universal non-egress under every interaction, nor server-side penetration-test or formal medical/financial/business flow acceptance. The blocked `.invalid` URL is intentional QA traffic, **not an application leak**. This HAR records the public static simulation, not production.

## 3. GUI Slide-to-place-order — independently accepted

Actual `case-result.json` confirms: `status:PASS_GUARDED_SYNTHETIC_SCOPE`; mock guard `{blocked:true,api:true,global:true,phone:true,addresses:true}`; valid fixture/cart + enabled thumb + open synthetic store + address-present; the pointer down **acquired HOLD**, with `max:300`. Real Playwright pointer movement reached `progress:1.00` (accepted threshold **0.96**) and ended with pointerup; `__demoBlockedActions` changed by **+1**, screen state stayed `S.v='pay'`, `busy:false`, `success_visible:false`. Screenshot-after visibly shows **“DEMO: No real orders or payments”**, with the same fake payment screen, no successful-order banner. HAR has **0 POST** and no successful off-host request.

**VERDICT: ACCEPT — P1 from first run (`MOCK_SLIDER_NOT_PROVEN_SAFE`) is CLOSED for the tested *synthetic* GUI swipe.** The earlier zero-counter run was an invalid/incomplete harness precondition; it is **not a product bug**. Neither a real order nor a real payment was created or attempted by the reviewer; production side effects were not measured and cannot be certified.

## 4. Independent visual/UX findings — handoff for designer, no UI modifications

**Observed from the original screenshot evidence:**
- **English home at 390:** original orange brand, homepage bento/category icons, favourites, restaurant cards, DineOut, footer/navigation visibly render. Some restaurant/item titles are Russian fixture **content/proper names** despite English UI; do **not** assume all must be translated UI labels. Intentional carousel partial card visibility should not be mislabeled global overflow.
- **English fake checkout before/after at 390:** heading, synthetic address, cash-to-courier method, checkout CTA, order summary visible in full-page capture. Directly visible `Subtotal 30 TJS − Discount 4.5 TJS − Happy hour 3 TJS + Delivery 10 TJS = Total 32.5 TJS`; **arithmetic and displayed fee line correct** for this fixture. Prior owner RU `27+12=39 TJS` already reconciled separately. Whether fee's **base/extra split** and every required button are accessible after scroll on 320px is **NOT measured here**. Sticky CTA visible at 390, not a proven all-size overlap-free pass.
- **Confirmed P2 network asset anomaly:** HAR carries **8 unique first-party paths** containing literal/unexpanded `${...}` template placeholders, each requested **twice** (16 requests total), including `/$%7Besc(st.cover_url)%7D`, `/$%7Besc(st.logo_url)%7D`, `/$%7BA3(d[5])%7D`. Their HTTP responses are **200 text/html** SPA fallbacks though the request's `Accept` header requests **image/**. This is a **reproduced broken URL/MIME response pattern** for those image requests, **not** an external egress incident, and **not yet evidence of an obvious visible broken picture**. `checkout` page reported `broken_image_paths:[]`; that probe does **not** scan all Home/menu/restaurant images. Eight category WebPs visually render in Home.
- **Existing P2 untranslated interface labels:** English product customization group labels `Размер порции (обязательно выбрать)` and `Добавки` were seen in historical in-memory fixture examination; **not re-opened in this successful run**. Distinguish display labels from native restaurant/item names.
- **Existing P2 demo disclaimer contrast:** historic white text on `#F1511B` measured ~**3.54:1**, below WCAG AA normal-text 4.5:1; **OWNER-DEFERRED**. Do not recolor, alter fonts or redesign.
- **Existing title/CTA accessibility concerns:** long names ellipsized; 320px scroll/touch target and bottom fixed-action overlap still require a **designer's** independent screenshot/DOM-based judgement. The accepted real hosted 8/8 RU/EN × 320/360/390/430 covers **document language, demo banner and no document-wide overflow**, **not** every component's tap target.

**Requested designer response in existing #48 only (PM coordinates, no new stage):** a single evidence-based `UX ACCEPT / UX CONDITIONAL / UX BLOCK` referencing original run artifact and accepted owner RU + native EN iPhone captures; exact screen/path for each proven P1/P2; visible effects of literal-template image requests (naturalWidth/currentSrc/which section); UI vs fixture language; fee breakdown visibility; CTA/sticky bar occlusion at 320–430; long-name readability; respect deferred banner colours. If runtime evidence missing, state `UNTESTED`, not `FAIL`. Do **not** modify source, styling, product policies or cloud configuration. No assumption that a GitHub comment automatically activates another Work chat.

## 5. Residual security risks / final boundary

**Accepted limited security:** approved static binary identity and sample HTTP headers, fail-closed off-origin behavior for tested session, successful GUI gesture triggering the mock-only guard, no recorded POST/payment/real-order success, RU/EN and 320–430 previously accepted bounded smoke. **No P0/P1 exploitable external egress or genuine payment behavior was reproduced in this run.**

**Still open, not grounds to rewrite approved code without authorization:**
1. **Full UX design/translation review not signed off** — designer coordination request is outstanding.
2. **8 literal-template image URLs with HTML fallback** — confirmed first-party network defect pattern; visual impact and exact originating UI controls still need designer/QA classification.
3. **Non-exercised flows** and physical iPhone cross-browser state transitions not covered by this HAR; no universal negative-proof guarantee.
4. **Defense-in-depth** prior passive analyzer reported `script-src 'unsafe-inline'` and missing HSTS, X-Frame-Options/`frame-ancestors`; note as P2 security posture review **without** claiming present exploit, and without changing accepted inline-heavy UI autonomously.
5. **Artifact availability:** GitHub Actions original evidence expires **2026-11-16T08:21:48Z**. The audit includes hashes, request counts, precise provenance and original run link; avoid relying on expiring ZIP as the only durable record.

## 6. Independent acceptance / manager handoff

| Decision | Independent answer |
|---|---|
| Synthetic-only **live network interception / restricted-origin egress** | **ACCEPT — PASS for captured workflow** |
| Synthetic **full UI swipe → mock `demo_only` guard / no visible false success** | **ACCEPT — PASS for captured workflow** |
| Website live 8/8 RU/EN viewport smoke | **Already accepted earlier; not repeated** |
| Original customer designs, English customization, image URLs, 320px hitboxes, fee disclosure | **DESIGNER SIGN-OFF PENDING** |
| **Final Stage22 across roles** | **PENDING PM decision after independent designer review; not an unconditional GO** |
| Public visual demo | Already published under owner authorization; no new publication |
| Real TALABOT product / G1 / C-01 / release / PHASE2 | **NO-GO** |

No code, design, root application, cloud hosting, production, account, order, payment, workflow or CI mutation was performed. This report lives **only on an isolated Stage22 documentation review branch** with an explicit diff check against the PM evidence checkpoint. Coordination happens in existing Issues #48 and #26; the designer must still respond independently if PM requires separate role approval.
