# Customer Home — current map (for fitting the next design). Read from `customer.html` (`vHome`) + CHANGES-v53/54/55. No UI changed.

Rule kept since v53 (owner): **every section shows only real data; a section with no data is hidden.** Order as rendered (v55 + v57 banner link).

| # | Section (function) | What it does / actions | Data source | Shown when |
|---|---|---|---|---|
| 0 | Header (`hHead`) | delivery address (opens address sheet), notifications (active orders + unread messages), cart with counter; search row stays on screen; filter button | addresses (`curAddr`), `TLB.orders`, chat unread, local cart (saved 24 h, v42) | always |
| 0a | Search / filter results (replaces the home) | results list; filters: category, open now, free delivery, discount, rating 4.5+, sort popular / rating / near | stores + menus (`TLB.allMenus`), `hfApply` | text typed or a filter on |
| 1 | Group order strip (`grpBanner`) | back to the open group order | group order state (v51) | a group order is open |
| 2 | Cart reminder (`cartNudge`) | «go to cart» / dismiss | local cart + time | cart left > 15 min |
| 3 | Categories (`HOME_CATS`, `catTile`) | 6 tiles 76×76: Restaurants, Groceries, Pharmacy, Beauty, Flowers & Gifts (= flowers + gifts), Sweets → category list | fixed list + 3D icons (`assets/3d`, MIT) | always |
| 4 | Hero carousel (`heroH`) | admin top banners first, then slides from live offers: happy hour with real countdown, biggest store discount, free delivery, brand slide; swipe, dots, auto-rotate (pauses on touch, off with reduced motion) | `banners` (placement top; link store / category / partner), `happy_hours` (`TLB.hhActive`), stores discount / fee fields | always (brand slide as fallback) |
| 5 | Your last orders (`lastH`) | delivered orders, «order again» (re-order sheet re-checks today's prices / availability) | `TLB.orders` (+ items) | ≥ 1 delivered order |
| 6 | Popular nearby (`ofCat(['rest'])`, `sCard`) | restaurant cards: photo, badge (discount / Express / New < 30 days / closed), favourite heart, delivery time, rating + count, description, benefit chip; tap → store | `stores`, `favorites`, `store_speed` (time only from measured prep time + distance), address distance | ≥ 1 restaurant |
| 7 | Best offers (`bestH`) | Flash sale = real happy hour with real end (else biggest discount, no timer); free delivery card | `happy_hours`, stores discount / fee | an offer exists |
| 8 | Recommended (`recH`) | dishes with price and quick add; tap → store | `best_dishes` (real best sellers), else items marked popular | ≥ 1 dish |
| 9 | Wallet & points (`walH`) | user's own numbers → Wallet | wallet, loyalty settings (`app_settings`) | always |
| 10 | DineOut (`dineH`) | banner «up to X % on the menu» (X = biggest real discount) + open restaurants with a discount, area + km | stores (rest, open, discount) | a restaurant has a discount |
| 11 | Bottom banners (`bottomBn`) | admin «paid ad» banners, rotating; v57: link `partner` opens partner.html | `banners` (placement bottom) | admin added one |
| — | Bottom navigation | Home, Orders, Wallet, Offers, Profile | — | always |

## Decisions to keep when the design arrives
- Only real data; empty sections hidden; no invented delivery times, countdowns or discounts (v53–v55).
- Removed on purpose in v54 (do not bring back without a decision): extra categories / «all categories», supermarket,
  pharmacy and flowers rails, brands, special occasions, Dushanbe banner, section icons.
- Points and happy hour are paid by the restaurant; commission computed before points (HANDOFF owner decisions).
- Flowers & Gifts tile opens two store categories (flowers + gifts); «shops» has no tile; DB categories unchanged.
- Admin controls banners (top / bottom, dates, links store / category / partner).
- Hooks to map a design onto: each row above is one function in `customer.html`; data comes through `TLB.*` in
  talabat-core.js (no section reads the database directly).

## Not known from the code / docs
- The approved new design itself (not received). Section order or wording changes are the owner's decision.
