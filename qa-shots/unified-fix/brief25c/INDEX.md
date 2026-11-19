# TALABOT — BRIEF-25c / owner review: Y-01…Y-04 + Y-06 + Y-07

**Final owner instruction:** [Y-07](https://github.com/merapplications-sketch/Talabat-v3/issues/48#issuecomment-7019030275) **supersedes W-07, X-09, Y-02, and Y-05**. No separate large DineOut hero remains. All screenshots are original customer-app **offline WebKit RU/375**, with synthetic QA stores and no production accounts or offers.

| Decision | Final review screenshot |
|---|---|
| **Y-01** — Flash, 1.5 cards; 88px photo; one-line price | [Flash](ru-375-flash-one-and-half-fixture.webp) |
| **Y-03** — Reel source-derived red discounts and offer pill (unlinked state) | [Dish discount](ru-375-reel-dish-discount-fixture.webp) · [Offer badge](ru-375-reel-offer-badges-fixture.webp) |
| **Y-04** — Styled comments with avatar/author, supplied time, icon submit, no default blue close ring | [Final comments](ru-375-reel-comments-designed-final-fixture.webp) |
| **Y-06** — A SINGLE reel screenshot showing discount badge **and** linked optional likes/comments/views together | [Linked social + badge (fixture)](ru-375-reel-badges-and-social-linked-fixture.webp) |
| **Y-07** — DineOut heading is the gold/dark banner, orange slanted dynamic discount ribbon, small existing 3D sushi food icon, 1.5 wide cards, cover with coloured centre-logo fallback, **bottom-right brand** and **top-left discount**, rating/count, measured distance | [Final integrated DineOut with visible 3D icon](ru-375-dineout-integrated-banner-visible-icon-fixture.webp) |

**Superseded screenshots (historical only):** [prior DineOut fallback layout](ru-375-dineout-branded-fallback-fixture.webp), [pre-eager-icon Y-07 preview](ru-375-dineout-integrated-banner-fixture.webp), [initial focused comments draft](ru-375-reel-comments-designed-fixture.webp). They are **not** the owner-review final layout.

**Data contract:** DineOut optionally reads `dineout_price_for_two_tjs` from the existing store object. A positive finite amount displays `≈ X TJS на двоих`; otherwise this part is **hidden** and only genuine measured distance appears. No field is populated or invented in product, and no SQL/core change was introduced. Clicking a DineOut card still uses the original restaurant-opening action.

**Optional social contract:** the Y-06 fixture injects `TalabotReelStats` only into the isolated browser; 37 likes, 2 comments and 215 views are synthetic values, never product defaults. Without the provider, controls remain hidden.

**Protection:** TALABOT review branch only. No SQL, `talabat-core.js`, Supabase, admin, merchant, driver, merge or production deployment. Previous owner-approved Y-01/Y-03/Y-04 and X decisions remain unchanged except where explicitly superseded by Y-07.

**Acceptance gate:** both Home WebKit/financial QA and H-01 (local authenticated roles + visual) must report `success` on the exact delivery SHA. The review screenshots alone do not authorize release.
