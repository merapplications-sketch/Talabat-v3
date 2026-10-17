# Customer design v06.1 — intake and mapping (17 Oct). No app file changed in this step.

Branch `design/customer-v06` from `fix/trial-v61` @ c991f3b (v61 and everything before it kept). Read only: the handoff package
and the addendum. No live SQL, no publish, no merge, no real data. Receiving the design closes none of the old notes.

## 0. Package check
| Item | Result |
|---|---|
| Base `TALABOT-Customer-v06_1-CLAUDE-HANDOFF.zip` sha256 | `3826803f…cf75bc` = the value named in the addendum manifest |
| `Tools/verify_integrity.py` + `SHA256SUMS` (base) | PASS, 242 files |
| Addendum `SHA256SUMS` | PASS |
| Addendum images (37) | every file byte-identical to a file already in the base package (`source_file` hashes match) — no new image |
| Fonts | TalabotRevision = Nimbus Sans 400/700 (AGPL-3 + font exception, «web shipping review Pending»); TalabotUI = DejaVu Sans (older layer) |
| Logo | `Assets/brand/TALABOT-Original-RU.png`, used byte for byte |

## 1. Screens → current app (`customer.html`; all data through `TLB.*`, no direct DB reads)
Ready = every visible element has a current function and real data. Partial = ready except the listed element.

| Design screen | Current view / functions | Status | What is missing / differs |
|---|---|---|---|
| Restaurant (v06.1) | `vMenu`, `menuSecs`, `gCard`/`lRow`, `ctlG`, `brChips`, `shareStore`, favourites, cart bar | Partial | Cover / logo / dishes come from the store's own data (the design photos are demo). **Info card «Мин. заказ»: no store minimum exists in the data** (only the loyalty minimum). **Menu category tabs: owner decision «no tabs, one scroll» (HANDOFF)**. «Комбо» banner: no combo data, image has baked text. «Подробнее о ресторане»: destination = existing store info (address / map / description) |
| Customization (sheet) | `itemSheet`, `shPick`, `shOk`, `shAdd`, `TLB.optionsOf` | Partial | **Options have no image field** → option cards text only (the burger / sauce pictures are demo). «Особые пожелания» per dish: server already accepts `note` per line (120 chars, patch 31+); the solo cart does not send it yet (cart line key change, client only) |
| Cart | `vCart`, free-delivery threshold, `youLike`, group order, note, cart bar | Ready | «Вернуть товар» (undo after remove) is new, client only. «ДЕМО» labels not shipped |
| Checkout | `vPay`: `whenCard`, `ptsCard`, `walletCard`, substitution, door, gift, tip, promo, summary with km breakdown, earn line | Ready (styling) | **Design has no payment-method block** → the current one stays (store agreement, cash-only notice). **Order button stays the 2-second hold** (owner decision v58), group / one-time note / too-far kept |
| Order details (delivered) | `vTrack` done: `cxCard`, `rateCard`, `proofCard`, `receipt`, `settleCard` (UAT012 + v61), `reorder`, `reportBtn` | Ready (styling) | Demo ad card not shipped. Live tracking keeps its current page (no reference) |
| Wallet | `vWallet` (balance, points, vouchers, rules, histories) | Ready | Cashback history = wallet entries `cashback` (exists). UAT009 history kept |
| Profile | `vMe`, savings, settings, support, about, privacy | Ready | — |
| Address edit | `vAddrForm` (Дом/Работа/Другое, map point, street*, house*, entrance, floor, apt, note) | Ready | Same fields and required marks as today |
| Restaurants list | `vCat('rest')` + chips | Partial | **Cuisine circles: no cuisine data on stores.** «Самые популярные — по числу заказов»: no per-store order count readable by customers. «Рекомендуем» paid card: no placement data. «Для вас» tile: no personal data source. Ready: search, rating 4.0+, with offers, sort, high rating, order again, all, closed |
| Home B | `vHome` sections (HOME-MAP.md) | Partial | see §2 |

Pages without a new design keep their current look and function (orders list, tracking, search, offers, favourites,
address list, notifications, support list / chat, settings, about / privacy, group order, category lists other than restaurants).

## 2. Home B, section by section
| Home B block | Current function | Status |
|---|---|---|
| Logo + delivery address + notifications | `hHead` (cart button also kept) | Ready (logo added) |
| Search + filter | `hHead`, `hfSheet`, `hfApply` | Ready (field stays 16 px — UI rule; design 14 px) |
| Bento: 3 campaign tiles | admin top banners (`heroH`) | **Blocked (assets):** the 3 original layers have baked text and arrows; no clean images. Can show admin banners in the bento shape (real images from admin) |
| 6 categories in one row | `HOME_CATS`, `catTile` (3D icons) | Ready; layout differs from the 10 Oct 3×2 grid |
| «Ваши любимые снова» | `lastH` (re-order sheet re-checks prices) | Ready |
| «Лучшие предложения» (4 campaign tiles) | `bestH` (real happy hour / discount, free delivery) | **Blocked (assets + data):** 4 composite images with baked prices; demo discounts. Real offers can use the tile shape without those photos |
| «Популярные рестораны» | `ofCat(['rest'])`, `sCard` | Ready |
| «Флеш-распродажа» (Продукты / Сладости / Подарки) | happy hour in `bestH` | **Blocked:** sweets photo missing; no confirmed campaign amounts |
| «Рядом с вами» | distance `kmOf` (real) | Ready as a list sorted by distance; «Доставка уточняется» when no time |
| «Купоны и награды» | `walH` → Wallet | Ready |
| «Смотрите и открывайте» (editorial) | none | **No data source** (static editorial) — hidden under the «only real data» rule |
| DineOut banner + places | `dineH` | Places ready; **banner background blocked** (gold panel has baked text) |
| «Предложения партнёров» | `bottomBn` (admin bottom banners, partner link) | Ready (admin images) |
| Not in Home B but existing | hero carousel (admin top banners, happy-hour countdown), recommended dishes `recH`, group strip, cart reminder | **Kept** — placement to confirm (§4.2) |

## 3. Missing assets → the one part each blocks (no substitution, no upscaling, no generation)
| Missing (addendum list) | Blocks only |
|---|---|
| Restaurant Legacy Premium cover without baked UI | the design DEMO cover only — the app shows each store's own `cover_url` |
| Large meal photo without baked buttons | demo only — the app shows the dish's own photo (240×199 crop not used as a full photo) |
| 3 Bento layers without text | Home bento with design photos (admin banners can fill it) |
| 4 «Лучшие предложения» photos | those 4 tiles with design photos |
| Combo banner | combo banner (also no combo data) |
| DineOut gold background | DineOut banner background |
| 3rd Home B restaurant photo (25 px strip) | demo card only — real stores use their own photos |
| Flash Sale sweets photo | the «Сладости» flash tile |
| Clean Big Mac / fries / nuggets / pizza | demo only — real dishes use their own photos |
Store logos, dish photos and covers in the app always come from the restaurants' own uploads; none of the design photos goes to production.

## 4. Points to settle before the parts that depend on them (everything else proceeds)
1. Store page menu tabs: design shows category tabs; owner decision (HANDOFF) «no tabs, one vertical scroll». Recommendation: keep one scroll; section titles styled as in the design.
2. Home order: Home B order vs the 10 Oct order (3×2 categories, hero carousel, recommended dishes). Recommendation: Home B order; the hero carousel (admin banners) takes the Bento place; recommended dishes after «Популярные рестораны».
3. Font: Nimbus Sans licence for web shipping not reviewed. Recommendation: batch 1 keeps the current system font; switch only after the licence is accepted.
4. Info card third column (minimum order) has no data. Recommendation: two columns until a store minimum exists (no substitute value).

## 5. Old notes log → design
**Tied to the installation (kept and re-checked inside it):**
- HOME-MAP rules: only real data; empty sections hidden; no invented times, countdowns or discounts.
- UI rules: fields ≥ 16 px, zoom never blocked, 44 px targets.
- Customer fixes v58–v61: cancel waits for the server (UAT002), chat drafts per order (UAT003), 2-second hold, UAT008 / 009 / 012 / 013 / 015 receipts and points, store payment rules at checkout (v60c), recorded automatic return (v61).
- QA-UAT1 follow-up: customer handlers with unquoted ids — the new markup quotes every id; the other handlers are unchanged (outside this batch).
- Backlog batch 4 linked by look only (not built): combo / family banner at peaks, order streak / rating rewards («Бонусы за заказ»).
- Owner 10 Oct home tweaks (3×2 grid, 3:2 banner, order) — superseded only if §4.2 is accepted.

**Independent of the design — open work:** v61 activation + 8 economic decisions; v57 onboarding activation; patch 35; admin
rating thresholds; payment provider; points paid by the platform for batch-4 rewards (SQL); receipt printing (restaurant);
backlog 4–7 (auto-cancel, GPS, offline, push, OTP, launch checklist); drafts after sign-out (Pending decision); restaurant
header selector 12 px proposal; test accounts; Safari notes (not opened now).

**Already fixed earlier — verification only, NOT re-implementation tasks (reopen only with regression evidence)** (corrected 17 Oct):
| Item | Fixed in | What is still pending |
|---|---|---|
| Admin back from a customer's order returns to the customer (Парвиз #9103) | v56f (`openFrom` / `ordBack`), tested | owner check on the phone |
| OSM map tiles «403 Access blocked» | v56 (tiles carry the site origin; `map_tile_check`) | check on the phone / real network |
| Customer history limited to 50 with no «more» | v56 (history by account + «show more») | identity of same-name orders needs real data |
| Store form delivery type «свободны» | v56 (two texts no longer share one key) | — |
| iPhone checks of v57c–v61 | — | owner iPhone round (not a code task) |

## 6. Files that change in the installation
- `customer.html` — CSS token layer (design colours, radii, spacing, shared metrics) and the render functions of the 10 screens.
  Same state (`S`), same handlers, same `TLB.*` calls.
- `assets/brand/talabot-ru.png` — the original logo (byte-identical copy).
- Tests: new `tools/design_v06_check.py` (360 / 390 / 430: elements real, no demo values, targets ≥ 44, fields ≥ 16 px);
  selector updates in `qa_all.py`, `cart_check.py`, `flow_check.py`, `uat3_check.py` only where markup changes.
- Not touched: `talabat-core.js`, admin / merchant / driver apps, SQL.

## 7. Proposed batch 1 (testable alone): the ordering path
Store page (v06.1 info card with two columns, offers strip, popular dishes, menu rows, no tabs) → dish sheet
(min(560px, 66dvh), text option cards, required / 0/3 counters, quantity, add with the real price; tick only after a real add)
→ cart (free-delivery bar from the store's threshold, line steppers with remove / undo, suggestions, group order, note) —
plus the shared token layer and the logo. Checks: cart_check, flow_check, uat2 / uat3 (affected parts), qa_all customer,
ui_rules, design_v06_check, side-by-side screenshots against the design at 390. Then batch 2: checkout, order details,
wallet, profile, address. Batch 3: Home B and the restaurants list (after §4.2).
