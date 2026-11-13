# TALABOT — Stage 10 / Synthetic Safari Customer Preview — Validation & Handoff

**Date:** 2026-11-14 / Asia-Dushanbe  
**Scope:** [Issue #36](https://github.com/merapplications-sketch/Talabat-v3/issues/36), management [#26](https://github.com/merapplications-sketch/Talabat-v3/issues/26).  
**Status:** **STATIC ARTIFACT BUILT / SOURCE AND URL SCAN PASS / BROWSER & PHYSICAL SAFARI UNTESTED / NOT PUBLISHED.**  
**Original accepted customer source:** `1cb85361d698d5da787d927a4c9ae7bd213c68c1`; original `customer.html` blob `9bc335f52ad58d7feab12ad8a2214bde9ab32330`, original `talabat-core.js` blob `f639bec1d23a812866e06eb1110940c77563387c`.  
**Existing offline fixture:** `tools/qa_all.py` FIX, blob `19a9643f3643364b48f8fa8ccd2dd5bafd22c6c4`.  
**Assembled artifact initial commit:** [`a1875d31e6d540ce7dc93cdce87976abd555d767`](https://github.com/merapplications-sketch/Talabat-v3/commit/a1875d31e6d540ce7dc93cdce87976abd555d767) (57 newly added files, original root source unchanged).

## A. Deliverable manifest (all paths relative to this directory)

| File | New Git blob | Function and provenance |
|---|---|---|
| `index.html` | `8d1e41a0acfcefb0f0f08a6dd494ac9b1a755357` | Exact original Customer HTML/CSS/layout/logo copied, with only demo-specific CSP, local script paths, banner, disabled external map navigation, isolated localStorage prefixes |
| `demo-core.js` | `28e140065a889be0cd3a206b7ae8c965f7f1e182` | Original shared core **copied**, source-specific production origin/public key removed, remote map/location/probe disabled, mock transport only; **not** a modification to approved shared core |
| `demo-fixture.js` | `33fd29146d3a4f4369e5762e094c7afe1fad0071` | Reused original QA inline synthetic Supabase stub, fictional restaurant/menu/orders/addresses and local 3D images, forced fake customer session, outbound transport APIs disabled |
| `demo-guard.js` | `fceff4bfd547d61e3f10b19f17cdf642bbb1a755` | No real order, payment, chat, delivery/settlement writes. Checkout action blocked and demo notice shown. |
| `manifest.json` | `56900c76f428ef24d60b27a54473ef1081341ff8` | Source SHA, original blobs, original asset blob list, release status, static scan status |
| `_headers` | `b7b2ae32cb9bfbc8b8dd563cc129ca6ebf75b1bc` | Equivalent HTTP CSP and strict no-camera/mic/location/payment policy for **future** reviewed static Cloudflare Pages use |
| `README.md` | `e010cfbc0c3d8ec55f43fb0d43955c75ee74bdfe` | Operating, review and no-deployment instructions |
| `assets/3d/*` | 43 existing original Git blobs including LICENSE | Original approved 3D local images, **not** regenerated images or remote dependencies |
| `assets/mobile.{css,js}` and `assets/driver-returns/panel.{css,js}` | 4 original blobs | Exact source-copy local assets, no remote scripts. |

**No product root file changed.** The full assembled tree was created as one new isolated review commit; its Git compare with the pinned source returned 57 added paths **all within** `previews/safari-zero-cost-customer/`. Screenshots are **not** attached because no browser run was performed; no screenshots were generated or fabricated.

## B. Specific static safety checks actually executed

| ID | Check | Outcome and scope |
|---|---|---|
| SC-01 | Exact source provenance, selected Customer Home/Restaurant/Customization/Cart/DineOut functions | **PASS SOURCE ONLY**: found in pinned original and copied demo |
| SC-02 | Original Customer embedded CSS block / original logo / palette retained | **PASS SOURCE DIFF**: original style block is included byte-for-byte |
| SC-03 | Single CSP `default-src 'none'; connect-src 'none'; form-action 'none'` with same-origin scripts/assets only | **PASS STATIC**: one meta tag in final HTML, mirrored in `_headers` |
| SC-04 | Executable HTML/JS/CSS external absolute URL scan | **PASS STATIC**: 0 external service literal URLs; the original inline CSS SVG `http://www.w3.org/2000/svg` is a **data:image** namespace, not a network fetch |
| SC-05 | Production Supabase host/publishable key, CDN and map tile literal search across final demo text files | **PASS STATIC**: 0 matches |
| SC-06 | Parse JS of `demo-core.js`, `demo-fixture.js`, `demo-guard.js` and 10 inline HTML script sections | **PASS SYNTAX ONLY**: V8 `new Function` parsed all without errors; not a browser execution |
| SC-07 | No login prerequisite in demo's synthetic SDK | **PASS SOURCE ONLY**: fake customer session is returned by in-memory stub; no real Auth request; browser behavior untested |
| SC-08 | Payment/order functions disconnected from real APIs | **PASS SOURCE ONLY**: demo guard returns `demo_only` without calling remote services; browser button path untested |
| SC-09 | Remote network request log, DOM loaded page, image rendering and no-console errors | **BLOCKED/NOT EXECUTED**. No matching local project checkout, no authorized static host; cannot assert zero *observed* requests |
| SC-10 | Real iPhone Safari 320/360/390/430; RU/EN; real screenshot and geometry | **UNTESTED**. Chromium/WebKit/desktop browser claims are NOT substitutes |

The CSP and mocked APIs are **defense in depth**, not substitute for an independent browser network trace. No actual `request`, `requestfailed`, Chrome DevTools, Safari Network tab, screenshot or DOM measurement exists from this task. No Supabase/Cloudflare/GitHub Actions or hosted test touched.

## C. Owner visual-journey coverage — what is prepared vs proven

| ID | Planned interaction on real accepted Customer components | Source readiness | Actual browser |
|---|---|---|---|
| S10-01 | Open no-login Russian Home — Dynamic Marketplace B | Included | UNTESTED |
| S10-02 | Navigate Categories/Campaigns, scroll, view DineOut Premium Gold | Included | UNTESTED |
| S10-03 | Open real Restaurant Details v1.6 legacy UI with fake store | Included | UNTESTED |
| S10-04 | Open original Direction A item sheet, select mandatory extras/quantity | Included | UNTESTED |
| S10-05 | Add item to fake cart, modify and return Home/Restaurant | Included | UNTESTED |
| S10-06 | Try checkout and confirm that actions are disabled/demo-only | Guard included | UNTESTED |
| S10-07 | Verify RU default and manually switch EN, restore mobile state | Existing RU/EN engine retained | UNTESTED |
| S10-08 | Each width 320, 360, 390, 430 — clipping, overlays, navigation, scrolling | Existing responsive CSS retained | UNTESTED |

**TG:** current approved Customer source implements RU/EN only; no unapproved TG translation created.  
**Owner's reported dark login colors:** DEFERRED; **no recoloring, logo/font changes, or redesign**.  
**Formal QA:** C-01 not invoked; 0/51 functional E2E and 0/21 Admin E2E unchanged. G1, Release and PHASE2 remain NO-GO.

## D. Proposed zero-cost, no-ChatGPT-gate HTTPS route — HOLD, not publication

**Safer proposal:** Publisher uses a **separate static-only Cloudflare Pages free project** with a distinct `*.pages.dev` origin, **deploying only this artifact directory**, with no environment bindings, no Supabase publishable/service keys, no Workers/Functions, no production domain takeover and no credentials. It will show the real original Customer design with local synthetic data, not TALABOT sign-in or ChatGPT sign-in. The required new project/URL **has not been created**. Free-tier suitability and exact chosen hostname must be checked by publisher before owner's separate publication approval. An alternative is a separate GitHub Pages repo, not existing TALABOT Pages config.

**Do NOT publish to** current production-facing `merapplications-sketch.github.io/Talabat-v3/`, historical pilot `talabot-pilot-20261106.pages.dev`, or ChatGPT Sites to avoid replacing/contaminating current builds or triggering a ChatGPT gate.

**Before owner approval to publish:** (1) independent security checks the final exact blobs, all local asset paths, CSP header and actual browser network events = 0 outbound; (2) independent UX tester performs the 8 scripted interactions and geometry at 320/360/390/430 RU/EN with real screenshots, protecting original design; (3) reviewer confirms host's public no-auth HTTPS availability without any production backend; (4) PM requests exact artifact+hostname approval from owner; (5) publisher alone deploys after that approval.

**No public demo URL exists at handoff**; the GitHub blob link is a source file, not a hosted Safari preview. Do not send it to owner as if it were the app.

## E. Next responsibility / decision

**Programmer:** this artifact and source-only validation are delivered; no further work without PM instruction.  
**Independent Security / QA:** browser request trace, service-connection negatives, inspect no leaked production identity/analytics and mandatory actual rendering proof.  
**UX Auditor:** compare 8 screens against approved visual snapshots, test scroll/long strings and Safari when available, no palette changes.  
**Publisher/OPS:** propose exact free project/hostname, verify distinct origin & no external bindings, no publication yet.  
**PM/Owner:** review complete evidence, authorize or withhold specific static preview publication after reviewer signoff.

**Absolute prohibited actions not performed:** product fixes, original source edits, real orders, C-01, account changes, live SQL/Supabase/Cloudflare, CI, production data, merge, force push, deployment, new paid resources. **This is one Stage10 handoff, not a release acceptance.**
