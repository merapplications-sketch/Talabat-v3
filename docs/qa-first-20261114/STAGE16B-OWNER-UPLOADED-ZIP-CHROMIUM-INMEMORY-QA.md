# TALABOT — STAGE 16B / OWNER-UPLOADED IMMUTABLE ZIP / ISOLATED CHROMIUM QA

**Date:** 2026-11-14 · Asia/Dushanbe  
**Parent:** [MASTER #26](https://github.com/merapplications-sketch/Talabat-v3/issues/26) / [Stage16 #42](https://github.com/merapplications-sketch/Talabat-v3/issues/42) / [Stage20 #46](https://github.com/merapplications-sketch/Talabat-v3/issues/46)  
**Exact corrected candidate SHA:** `3f74b29a7c4bcc89cef9e25dd73f574448ab7896`  
**Disposition:** **ZIP IMPORT PASS / ISOLATED IN-MEMORY CHROMIUM LIMITED PASS / REAL HTTP & SAFARI UNTESTED / PUBLIC PREVIEW NO-GO**.

## 1. Genuine owner-side ZIP receiver acceptance (new evidence)
The owner uploaded **the existing exact Stage15 ZIP** directly to the management conversation. Its bytes were genuinely mounted in that conversation's test container, independently hashed and opened:
- `talabot-safari-demo-3f74b29a.zip`, **967,486 bytes**, SHA256 **`20e674ae017b92a02ca937336f2fa54293fd79fc23e9d8ff559bd564046b82ae`** matches Stage15's pinned receipt.
- ZIP has **59 entries**, **45 original WebP**, one `safari-zero-cost-customer/` root, **59/59 CRC32 PASS**, no path traversal. File contents really extracted to an ephemeral QA directory.
- Corrected `demo-fixture.js` independently recomputed Git blob SHA1 **`a2336b6471c96a9a5ca921ccd13805eedf506e0b`** (MATCH); no source, assets, original app or approved UI changed.
**This closes binary import for THIS ChatGPT conversation's filesystem ONLY**, not a separate publisher/consultant Work session.

## 2. Browser test setup and exact scope
Python Playwright launches Chromium, fresh unauthenticated mobile-like contexts; all nonlocal URL requests are abort-routed. **Local browser navigation to loopback HTTP, file://, data:, and synthetic HTTPS was denied by the host administrator** with `net::ERR_BLOCKED_BY_ADMINISTRATOR`. No server-origin visit succeeded. To obtain meaningful limited dynamic evidence without external requests, the test harness used an `about:blank` page with the **unchanged original HTML, CSS, and JS file bytes** inserted *in memory* (local CSS/JS embedding only for harness), test-only localStorage shim, and manually dispatched load event for deferred guard. No real HTTP headers/MIME/resource fetching or true browser-origin storage persistence was simulated. The exact ZIP and source files remained unmodified.

## 3. Actual limited in-memory Chromium observations
| Scenario | Observed result | Evidence level |
|---|---|---|
| RU/EN × 320, 360, 390, 430 viewport | **8/8 PASS**: app rendered, matching browser language and synthetic disclaimer, **0 document-level horizontal overflow**, **0 JS page exceptions** | In-memory browser initial-view smoke, NOT real HTTP E2E |
| EN browser with saved RU; RU browser with saved EN | **2/2 PASS**, using test-controlled localStorage shim | Storage-precedence simulation, NOT actual origin reload |
| RU → EN manual switch | **PASS**, choice stored in shim and banner translated | In-memory UI/code |
| Food category button | **PASS**, actual UI click opened category | In-memory GUI |
| Restaurant menu | **PASS**, fake restaurant and 16 fake menu entries displayed | In-memory app function |
| Customization | **PASS**, required option group displayed | In-memory UI/code |
| Attempt to add missing required option | **PASS**, cart stayed 0, missing group `g1` highlighted | Negative validation |
| Fake cart | **PASS**, one synthetic dish added, quantity 1 and cart view displayed | In-memory app function |
| Fake payment screen | **PASS**, screen opened without actual payment attempt | In-memory navigation |
| Direct synthetic real-order guard | **PASS**, `TLB.placeOrder(...)` returned `{error:'demo_only'}`, blocked count 0→1 | Guard negative test, NOT actual backend transaction |
| Deliberate transport-block test | **PASS**, fake `fetch('https://example.invalid')` rejected, denied counter 0→1 | Guard negative test, no external request |
| Chromium instrumented requests / WebSocket / JS console | **0 observed** in about:blank harness | **NOT proof of real hosted zero external egress** |

Artifacts physically generated in the conversation: `qa_results.json`, original-size screenshots of RU/EN home, category, restaurant, customization, fake cart and fake checkout, plus one test-only RU screenshot with **13 of the original WebP** embedded as data URIs. These screenshot binaries are **not GitHub attachments**. The owner-facing downloadable evidence bundle and report live in the originating ChatGPT conversation.

## 4. Explicit remaining gates
**NOT TESTED:** proper local HTTP origin execution, served `_headers` CSP and MIME, loading 45 WebP over HTTP, pixel-perfect Safari design, persisted `localStorage` across actual origin reload, `?lang` query precedence, order/payment gesture path with observed real browser request trace, physical iPhone Safari. In-memory resource shimming and synthetic asset placeholders must not be mistaken for broken hosted image paths. The previously identified fake notice 3.54:1 contrast P2 and old pilot dark login colors remain **DEFERRED**, not design authority.

**Separate publisher Stage20 still blocked:** no authorized JWT-aware Pages upload mechanism/zero-additional-charge proof; NO Cloudflare project, deployment or HTTPS Safari link created by these tests. Do **not** send an invented demo URL. Stage9 formal product E2E 0/51, Admin 0/21, G1/release/PHASE2 NO-GO unchanged.

## Management verdict
**ACCEPT** real owner-uploaded ZIP import and limited, reproducible, in-memory Chromium QA. **DO NOT promote** this to complete Stage16 HTTP/browser acceptance, independent security/UX pass, public Safari GO, functional C-01 or production release. No additional developer/code/UX edits were requested or performed. Actual HTTP/browser-network safety and real-device Safari stay pending a compatible authorized test/hosting channel.

**Preservation:** No approved source, finance, pricing/roles, SQL, Supabase, Cloudflare existing pilot, CI, main, original UI or fake fixture changed. This report is one additional Markdown file in an isolated documentation branch.
