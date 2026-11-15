# TALABOT — Stage22 Programmer | Demo-only EN customization display-label correction

**Scope:** [Existing Issue #48](https://github.com/merapplications-sketch/Talabat-v3/issues/48) · [Master Issue #26](https://github.com/merapplications-sketch/Talabat-v3/issues/26) · **One unified owner task, programmer internal handoff**  
**Reference source / corrected synthetic Safari demo:** `3f74b29a7c4bcc89cef9e25dd73f574448ab7896`, branch `review/safari-stage13-demo-lang-p2-20261114`  
**Isolated candidate:** `review/stage22-synthetic-en-options-20261115`  
**Status:** **DEMO SOURCE CORRECTION PREPARED — 16/16 V8 SOURCE-FUNCTION REGRESSIONS PASS — LIVE BROWSER QA NOT RUN — NO PUBLICATION / NO MERGE**

## Why this exact change

Real owner-approved synthetic-only QA runner [Actions #43719066978](https://github.com/merapplications-sketch/Talabat-v3/actions/runs/43719066978) and its [PM evidence report](https://github.com/merapplications-sketch/Talabat-v3/blob/f804aed17d36a7c0a36955a158c96b050047fb5f/docs/qa-first-20261115/STAGE22-TARGETED-UX-320PM-20261115.md) directly reproduced English 320px product-sheet *UI control option* labels in Russian. They are synthetic test-fixture names, not merchant proper names. The actual original Customer and fake JSON fixture data **must not be rewritten**.

## One code-file insertion, no other source changes

**Modified file:** `previews/safari-zero-cost-customer/demo-guard.js` (source blob before `fceff4bfd547d61e3f10b19f17cdf642bbb1a755`).  
**Location:** within existing synthetic-only `demo-guard.js` before the existing load handler. The rest of the guard (real payment/order disable, status notice) is intact.  
**Mechanism:** wrap existing `TLB.optionsOf(itemId,all)` **only when `window.__TALABOT_SYNTHETIC===true`**. The wrapper reads `TLB.lang()` when the menu/sheet/cart calls `optionsOf`, translates `g1/g2` and `o10–o23` **only for synthetic item `i1` and `lang==='en'`**, and returns shallow-copied display objects. On RU or unsupported locales or any other item, the exact original result is returned. All original fixture IDs, group required/max/sort flags, choice prices, availability, cart-key semantics, options and original Russian values remain unchanged.

| Original synthetic UI label (RU, unchanged) | English display only |
|---|---|
| Размер порции (обязательно выбрать) | Portion size (required) |
| Добавки | Add-ons |
| Маленький / Средний / Большой | Small / Medium / Large |
| Сыр / Бекон / Халапеньо / Соус | Cheese / Bacon / Jalapeño / Sauce |

**No changes** to `index.html`, `demo-core.js`, `demo-fixture.js`, `manifest.json`, `_headers`, assets/CSS, original `customer.html`, actual products, accepted visual design or live site.

## Executed source-function regression evidence (not Safari/browser)

V8 executed the **actual corrected guard source** in a mock `window` with source-extracted `g1/g2/o10–o23` fixture values; its original `noAction` guard was invoked and confirmed to refuse a dummy order. **16/16 PASS**:

1. RU unchanged; 2. EN group labels; 3. EN all seven choice labels; 4. IDs, required/max/sort, option price and availability unchanged; 5. RU after EN toggle unchanged; 6. fake cart labels update with EN; 7. other item unaffected; 8. fixture Russian source unchanged; 9. exact prior guard and fixture blobs confirmed; 10. existing load handler retained; 11. no network invoked; 12. corrected JavaScript parses; 13. non-demo mode does not translate; 14. unsupported `tg` unchanged; 15. zero new origins/keys introduced; 16. synthetic no-real-order guard still returns `demo_only` and increments blocked-actions counter without making an order call.

**NOT EXECUTED HERE:** actual 320px browser candidate rendering, WebKit/iPhone Safari, request/HAR recheck, deploy or end-to-end functional transaction. Do not infer 16/16 UI PASS or claim published UI was corrected. **Approval of candidate and targeted independent UX/SEC browser test belong to PM/independent roles.**

## P2 literal template image-request investigation — no speculative fix

The already executed [Stage22 320px capture](https://github.com/merapplications-sketch/Talabat-v3/blob/f804aed17d36a7c0a36955a158c96b050047fb5f/docs/qa-first-20261115/STAGE22-TARGETED-UX-320PM-20261115.md) showed **8 distinct same-origin malformed `/$%7B...` image-intended URL templates, answered 200 HTML**; source HTML contains JavaScript `<img src="${...}">` template literals. The **request initiator / preload parser source is not identified with execution evidence**. In the same targeted real browser session **29/29 Home and 19/19 merchant/menu actual DOM images had `naturalWidth>0`**; no visible missing image was demonstrated in those two screens. A separate checkout run had previously proven fake order interception. Therefore **document P2 asset-request hygiene / unknown other-screen impact**; **do not modify assets, approved visual components or URL logic** or assert eight visible broken images. The independent reviewer may inspect request initiators if a clearly reproducible user-facing defect appears; no broad re-run required.

## Safety, acceptance boundary and next role

- No app code/design/approved palette/original brand change; no change to Q09–17, PRICE/RATINGS/TIP/106/107, real product catalog, SQL, Auth, roles, Cloudflare, Supabase, CI, `main` or hosted preview.
- No test order/payment/production network call; no publication, merge, deployment, new QA workflow or paid tool.
- Existing scoped Stage22 **security ACCEPT** (earlier genuine full-swipe + blocked outside-origin HAR) and earlier RU/EN mobile width smoke remain preserved, **not re-executed**.
- **Next only:** PM reviews exact isolated diff; independent designer/QA runs one source-pinned EN-320 option-sheet/cart RU/EN toggle verification with fail-closed egress and screenshot before any further approval. **Stage22 overall remains CONDITIONAL until independent UX + PM sign-off**.
- Real product C-01/G1/release/PHASE2 remain **NO-GO**.
