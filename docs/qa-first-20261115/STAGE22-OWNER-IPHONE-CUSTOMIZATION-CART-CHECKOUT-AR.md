# TALABOT — Stage22 / Owner iPhone QA: Customization → Cart → Checkout (RU)

**Date:** 2026-11-15 (Asia/Dushanbe). **Scope:** Read-only inspection of owner-supplied `IMG_8325.jpeg`, `IMG_8326.jpeg`, `IMG_8327.jpeg` (each 709×1536 px) plus *exact existing static-demo ZIP source only*. **No live checkout submission; no production or code change.**

**Live URL shown:** `talabot-safari-demo-20261115.pages.dev`. Earlier proof: [independent Stage22 live report](./STAGE22-INDEPENDENT-LIVE-PAGES-QA.md) and [owner iPhone Home/Restaurant observations](./STAGE22-OWNER-IPHONE-SCREENSHOTS-OBSERVATIONS-AR.md). Screenshots are retained in the owner conversation and **not uploaded to the PUBLIC GitHub repository**.

## Observed on the real iPhone/iOS web-viewer screenshots

1. **Product customization visible:** original product hero, long Russian name, base display `13.5 TJS` struck-through `18 TJS`, required portion group selected **Маленький**, optional extras `1/3` with **Бекон +3 TJS** checked (others unchecked), quantity **2**, CTA **Добавить в корзину — 27 TJS**. Modal controls and sticky footer visibly render. This image does not prove option validation for missing required group (previous in-memory test covers that separately).
2. **Cart reached and reflects selections:** same dish, **Маленький, Бекон**, quantity **2**, product total **27 TJS**, original `36 TJS` struck through, free-delivery progress says **add 123 TJS** (threshold 150 TJS in demo fixture). Actions `Добавить ещё`, `Перейти к оплате`, and recommendations visible. **Observed progression across three screenshots**; no recorded click events or actual state persistence after reload.
3. **Checkout reached (NOT submitted):** mock address `пр. Рудаки 100` with entrance/floor/unit/test note, “as soon as possible” delivery, wallet balance **50 TJS** toggle visually **OFF**, points eligibility message, payment-method heading, sticky total **39 TJS**, bottom **Сдвиньте, чтобы заказать** slider. **No completed swipe, payment confirmation, network capture, order ID or genuine payment** is shown. Treat this as checkout UI render PASS, *NOT safe order-block verification*.

## Price arithmetic verified against original demo source — not an unsubstantiated defect

The actual 55-file ZIP from the owner chat was inspected **read-only**:
- `demo-fixture.js` synthetic `i1` base **15 TJS**; portion **Маленький +0** and **Бекон +3**. Effective deal **25%** gives **(15+3)×0.75 = 13.5 TJS/unit**, × **2 = 27 TJS**. The 36 TJS crossed-out original = 18×2. This matches screenshots.
- `demo-fixture.js` synthetic `delivery_quote:{fee:12,fee_full:12,base:10,extra:2,km:4.2,...}`. `index.html` `calc()` uses quote fee and `total = subtotal - discounts - ... + fee + tip`, with wallet toggle off in screenshot. So **27 + 12 = 39 TJS** shown on checkout **is consistent with the fake fixture, and is NOT proof of a pricing bug**. 12 consists of **10 TJS delivery base + 2 TJS distance extra**. Do not extrapolate this fake tariff to the real approved CASH/PRICE/commission contract.
- **UX visibility gap P2:** the three screenshots do not show an expanded per-fee breakdown alongside the sticky 39 TJS; need test whether the **10+2 split and any tip/discount totals** are actually visible and accessible when user scrolls to order summary, before declaring presentation PASS or defect. Do not change approved pricing.

## Registered limited QA statuses

| ID | Priority | Observation and status | Next valid check |
|---|---|---|---|
| **IPH22-08** | PASS limited | Customization → cart → checkout screenshots in RU on physical iPhone-like embedded web viewer; chosen portion/bacon/qty persist visibly between screen renders | Still requires actual *Safari.app* identification and stateful refresh evidence |
| **IPH22-09** | PASS fixture math | Price `13.5×2=27`; checkout `27+12=39` with synthetic quote `base10+extra2`, matches approved demo code | No authorized real pricing/financial validation; keep business policy locks |
| **IPH22-10** | **P2 UX verification gap** | Sticky checkout total 39 TJS while line-item 27 TJS; detailed delivery base/extra charge not visible in supplied crop | Verify readable total breakdown after scrolling on live site; if present mark PASS, else submit owner-scoped proposal (no autonomous UI edit) |
| **IPH22-11** | **P1 safety/unverified** | Order slide CTA active-looking in Russian; **NOT dragged to completion**, no observed fake `demo_only` UI response, no request log | Independent same-origin-only fail-closed interception *before* synthetic GUI gesture; never ask owner to complete order or enter payment |
| **IPH22-12** | **P2 mobile layout verification gap** | Footer fixed at bottom, payment methods heading visible while options extend beyond screenshot | Verify all payment choices/summary reachable on scroll and never covered by footer at 320/360/390/430; not a proven occlusion defect |
| **IPH22-13** | Pending | Three new screenshots still Russian in embedded iOS web viewer; no English device page or native Safari.app proof | Open canonical site directly in standalone Safari (English `/?lang=en`) and show first screen, without order interaction |

## QA status/next step

**New direct visual evidence closes the *screen-reachability* gap** for RU product-customization, selected extras, fake cart and checkout **up to the uncommitted slider**. Exact demo arithmetic **consistent**; no verified financial defect. **Does not close** per-request CSP enforcement, network-attempt/blocked egress, GUI slider fake checkout, any real order/payment prevention via browser, EN real device, native Safari.app identity or full 320–430 geometry matrix. Formal Stage22 independent final safety and full UX sign-off **NO-GO pending evidence**, not an observed production compromise.

**Management restrictions:** No real customer/payment/order interaction, no authenticated production account, no new publishing, no design/brand/color/price changes, no GitHub main/CI/Cloudflare/Supabase/production change. Historic pilot and demo banner colour concerns remain owner-DEFERRED. This document is **one docs-only addition** on existing isolated review branch, with owner screenshots retained privately in chat and not copied to public repository.