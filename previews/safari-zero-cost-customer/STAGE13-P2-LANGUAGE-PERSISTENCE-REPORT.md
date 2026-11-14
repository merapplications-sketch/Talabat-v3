# TALABOT — STAGE 13 / Programmer P2 Synthetic Demo Language Persistence
**Scope:** [Issue #39](https://github.com/merapplications-sketch/Talabat-v3/issues/39) · [Master #26](https://github.com/merapplications-sketch/Talabat-v3/issues/26)  
**Status:** **DEMO-ONLY P2 SOURCE FIX COMPLETE — STATIC/SIMULATED REGRESSION PASS — BROWSER/Safari BLOCKED — NOT PUBLISHED**  
**Source candidate (unchanged parent):** `2bae45cc5a21372123228befcbe87c19d6aac974`  
**Source location:** `previews/safari-zero-cost-customer/demo-fixture.js`  
**Original fixture blob:** `33fd29146d3a4f4369e5762e094c7afe1fad0071`  
**Corrected fixture blob:** `a2336b6471c96a9a5ca921ccd13805eedf506e0b`  
**Product source lock:** `1cb85361d698d5da787d927a4c9ae7bd213c68c1`

## 1. Authorized correction — one source line only

Original line 2 of the demo fixture:

```js
window.__ROLE='customer';window.__TALABOT_SYNTHETIC=true;try{localStorage.setItem('tlb_demo_lang','ru')}catch(e){}
```

Corrected line 2:

```js
window.__ROLE='customer';window.__TALABOT_SYNTHETIC=true;
```

Exactly **57 characters removed**, no other line changed. Original `window.__ROLE='customer'` and `window.__TALABOT_SYNTHETIC=true` remain. All fake stores/items/orders, the in-memory `supabase.createClient`, and network/order/payment guards remain byte-identical. Existing UI `index.html`, `demo-core.js`, `demo-guard.js`, `_headers`, CSS, all copied assets, manifest and every product/root file are **unchanged**. No redesign, new UI, configuration, login or purchase capability.

## 2. Regression evidence: V8 simulated source behavior, **not a browser E2E**

Before storing the corrected blob, source fragments were read from the unchanged candidate:
- `index.html` line 8: `window.tlbPreferredLanguage` (manual saved preference wins; else browser language; unsupported => RU).
- `demo-core.js` line 41: `setLang(l)`, persisting manual `tlb_demo_lang`.
- corrected `demo-fixture.js` line 2: test-only fake customer flags, no unconditional language write.

These exact extracted source functions were executed in an isolated JavaScript V8 simulation with controlled `localStorage`, `navigator.languages`, `window` and `document`. The full corrected fixture was separately syntax-parsed with `new Function` **without executing its application APIs**.

| Test | Expected | Simulated observed | Result |
|---|---|---|---|
| Empty storage, browser `en-US` | EN | EN | PASS — SOURCE SIMULATION |
| Empty storage, browser `ru-RU` | RU | RU | PASS — SOURCE SIMULATION |
| Empty storage, unsupported `tg-TJ` | RU fallback | RU | PASS — SOURCE SIMULATION |
| Stored EN, browser RU | EN | EN | PASS — SOURCE SIMULATION |
| Stored RU, browser EN | RU | RU | PASS — SOURCE SIMULATION |
| User manually selects EN, then reloads | EN | EN | PASS — SOURCE SIMULATION |
| User manually selects RU, then reloads | RU | RU | PASS — SOURCE SIMULATION |
| `localStorage` blocked, English browser | EN fallback, no exception | EN | PASS — SOURCE SIMULATION |

**8/8 source-function simulations PASS. 0/8 real browser/viewport configurations executed.** No DOM, screenshot, real Safari, console capture or page network request trace was generated or claimed. The current runner does not have a mounted, complete, approved 58-file preview plus safe loopback browser host; no new tooling or services were installed. Treat executable acceptance as **BLOCKED**.

## 3. Source and safety regression

- Static comparison after edit: **one differing source line**, same total line count. The original fake-session implementation (`getSession`) and `fetch`/WebSocket disabled adapters remain.
- Corrected fixture syntax: **PASS** in V8 parser. Production tokens `supabase.co`, `sb_publishable_`, the primary project identifier and CDN domains: **zero matches** in corrected fixture; literal external HTTP(S) service URLs: **zero**.
- Remaining 57 preview files are inherited unchanged from [Stage10 candidate](https://github.com/merapplications-sketch/Talabat-v3/tree/2bae45cc5a21372123228befcbe87c19d6aac974/previews/safari-zero-cost-customer). Existing Stage11 independent security asset integrity (50/50 assets) remains valid for those unchanged files; **not re-tested**.
- `?lang=en` / `?lang=ru`: unchanged existing `index.html` logic reapplies explicit URL parameter on each reload, which can override a different stored manual choice. **Observed in source only**, no precedence contract altered or fixed. Manager/QA to document/test when executable browser is available.
- **UX12-F-02 / P2 demo notice contrast** is **DEFERRED**: white 11px text on original `#F1511B` calculated around 3.54:1 against WCAG AA normal-text 4.5:1; no owner-approved change to banner colors/typography. Historical darker pilot-login colors are a **separate deferred owner note**.
- Browser zero-external-egress evidence: **NOT EXECUTED**, not a security PASS. Original mock-only demo / CSP source claims remain limited to static evidence.

## 4. Handoff and strict safety gates

**Next PM task:** independent source diff and safe browser re-test on this exact new candidate; validate RU/EN first visit, manual toggle, refresh, explicit URL query precedence, and fake checkout negative actions at 320/360/390/430. Capture actual screenshots, console, HTML geometry, and outbound/blocked request log on a separately approved local static host; physical iPhone Safari remains separately UNTESTED. Independent security/UX sign-off and specific owner approval are mandatory before a zero-cost static host/publisher releases anything.

**No** modification to root `customer.html`, `talabat-core.js`, source design, financial Q09–17, accepted PRICE/RATINGS/TIP/106/107, operational orders, SQL, Supabase, Cloudflare, CI, main, production or permissions. **No** installation, deployments, merges, force push, C-01/Auth-profile, real order or payment. **Formal E2E 0/51, Admin 0/21, G1/Release/PHASE2 NO-GO** unchanged.

**Disposition:** programmer handoff complete for **one isolated demo-only P2 language fix**; awaiting PM review and separately commissioned independent retest.
