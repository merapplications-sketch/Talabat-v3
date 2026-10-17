# v63 — design v06.1, batches 2 + 3: the ten customer pages, for review (local; not merged, not published)
Branch `design/customer-v06` (on top of v62; v61 and everything before kept). Only `customer.html` changed (+ the check
`tools/design_v06_check.py`). Core, SQL, the other apps, the money rules and real data are untouched. This is the customer UI
complete **for review** — not a final approval. The image announced in the 17 Oct 21:16 message did not arrive (please resend).

## The ten pages
| # | Page | Batch | State |
|---|---|---|---|
| 1 | Restaurant (one vertical scroll) | 1 (v62) | unchanged since v62 |
| 2 | Dish sheet | 1 (v62) | unchanged since v62 |
| 3 | Cart | 1 (v62) | unchanged since v62 |
| 4 | Checkout | 2 | design layer on the same blocks: header, cards, «when», points / wallet switches, preferences, door / gift, tip, promo, summary, earn line, 2-second hold, payment block |
| 5 | Order details (delivered / cancelled) | 2 | status card, cancel card, rating, door photo, «Состав заказа» (photo, qty × price, options, request), «Чек» (same rows + settlement block), re-order, report |
| 6 | Wallet | 2 | «Кошелёк и баллы»: balance card, points card (vouchers, redeem rate, progress, expiry, earning rate always visible, rules under a link), wallet operations (folded), history tabs: points / cashback |
| 7 | Profile | 2 | user card (avatar letter, masked phone, account settings), savings, the same menu rows, language note, version |
| 8 | Address form | 2 | Дом / Работа / Другое, map point, the same fields and required marks, «Сохранить адрес» |
| 9 | Home B | 3 | header (logo, address, notifications, cart), search + filter, bento, six categories in one row, «Ваши любимые снова», «Лучшие предложения», «Популярные рестораны», «Рекомендуем для вас», «Рядом с вами», «Купоны и награды», DineOut, partner offers |
| 10 | Restaurants list (every category list and «all») | 3 | logo header, title + area, tiles «Скидки / Бесплатная доставка / Для вас», search, chips, sections «С высоким рейтингом / Заказать снова / Все рестораны» |

Kept on Home (not in Home B but existing): the group-order strip and the cart reminder (above the bento), the hero slides
(now the bento), recommended dishes, the filter sheet and notifications sheet, the search results list.
Data rules: every block shows only real data from the app (`TLB.*`); a block without data is hidden; no design photo, demo
value or baked picture goes to the app. Pictures are the stores' / dishes' own (or the «no photo» slot) and the app's own 3D icons.

## Defects found and fixed in this round
- Checkout switches were 50×30 tap areas → 64×44 tap area, same 50×30 look. Text buttons («Изменить» etc.) were 18 px high → 44.
- Profile «Настройки аккаунта» link 32 px → 44.
- Wallet: the earning rate line («Обычно N баллов за 1 TJS — в некоторых заведениях своя ставка», UAT015) had gone under the
  rules link → always visible again (uat3 caught it).
- Order details: after sending a rating the shorter «thank you» card could end up under the header → the page returns to the top
  in that case (flow_check caught it).
- Profile phone greyed by a global rule (class renamed).
- Preview packaging: earlier previews did not carry `assets/3d` (category / offer icons were missing in the preview only) → the
  v63 preview carries `assets/3d` and `assets/brand`.

## One list: differences, gaps and decisions
### A. Differences from the reference (by rule or by missing data) — shown, not hidden
1. Font: the current system font (Nimbus Sans waits for the licence review) — letters wider / rounder, some line breaks differ.
2. Fields stay 16 px (UI rule; reference 14 px). Every tap target ≥ 44 px (some reference icons are 36–40).
3. Restaurant info card: 2 columns (no minimum order in the data). No combo, dish descriptions, option pictures, dish favourites,
   «Смотреть все» (no data). Search is a field in the page; bottom navigation stays under the cart bar. Cart bar text
   «Посмотреть корзину». Prices «16.88 TJS», badge «Хит». Below 560 px of height the sheet grows so nothing is cut.
4. Home header keeps the cart button next to the bell (reference: bell only) — decision D1.
5. Bento = the existing hero slides: admin top banners first, then the real offers (happy hour with its real countdown, biggest
   discount, free delivery, a brand slide). Big tile = slide 1 (+ slides after the 3rd, swipeable with dots), small tiles =
   slides 2 and 3; fewer than 3 slides → one wide tile. No design photos (the 3 clean layers are missing; text tiles + 3D icons).
   Admin images are cropped to the tile shape — decision D2.
6. Categories: the six in one row with short names (Рестораны / Продукты / Аптеки / Красота / Цветы / Сладости; EN Food /
   Grocery / Pharmacy / Beauty / Flowers / Sweets). «Цветы» still opens flowers + gifts.
7. «Ваши любимые снова»: one card per delivered order (store picture, store, first dish, «Сегодня / Вчера / N дня назад» up to
   6 days then the date, total) with «Заказать» = the existing re-order sheet (re-checks prices). Reference shows logo + time only.
8. «Лучшие предложения»: up to 2 real tiles (flash = real happy hour or the biggest store discount; free delivery = places
   that offer it), not the 4 photo tiles (photos with baked prices; demo discounts).
9. Hidden — no data: «Флеш-распродажа» by category, «Смотрите и открывайте» (editorial).
10. «Рядом с вами»: only when the address and the store have a map point; real distance; time only when measured, else
    «Доставка уточняется».
11. «Купоны и награды»: both tiles open the wallet (vouchers, points and balance live there); without a points programme the
    second tile says «Кошелёк и баллы».
12. DineOut: dark text panel + the app's pizza icon (gold photo background missing) with the real «до N%»; section title
    «Рестораны со скидкой»; place cards = open restaurants with a real discount.
13. «Предложения партнёров» = admin bottom banners as uploaded; hidden when the admin has none.
14. Bottom navigation keeps the current look on every page (the reference 80 px bar would change all pages) — decision D8.
15. Logo: the original Russian file is used in English too (no English logo file in the package).
16. Restaurants list: applied to every category list and «all» — decision D3. «Для вас» = the stores of your delivered orders
    (hidden when none). «С высоким рейтингом» = open, 4.5+, top 3; «Заказать снова» = up to 5 of your stores with «Последний заказ»;
    «Все рестораны» = all the others (every store appears once). With a search, chip or tile → one plain list. Back button kept.
    Not shown (no data): cuisine circles, «Самые популярные — по числу заказов», the paid «Рекомендуем» card, the promo panel
    with the burger photo. Chips kept as today: «Рейтинг» sorts by rating (reference «Рейтинг 4,0+» filter) — decision D7.
17. Checkout: the payment-method block and the 2-second hold stay (no design for them).
18. Order details: live tracking keeps its current page (no reference); the demo ad card is not shipped.
19. Profile: phone shown masked (+992900 ••• •• 00) — decision D4.
20. Test pictures: the preview data has no photos (every slot shows «no photo»); the screens were also taken with harmless
    test pictures («TEST PHOTO», `_ph` files) to show the photo state. None of them is in the app or its data.

### B. Decisions waiting (independent work continued; recommendation first)
- D1 Cart button in the Home header — keep (fast way back to the cart; Home B has no other cart entry).
- D2 Admin banners in the bento crop to the tile (big ≈ 1:1, small ≈ 1.35:1) — keep, and later give the admin upload a shape
  guide (admin app change, not part of this approval); alternative: banners in their own 3:1 strip above the bento.
- D3 List design for every category — keep (one look); can be limited to restaurants.
- D4 Masked phone in the profile — keep masked.
- D5 Font — keep the current font until the Nimbus Sans licence is reviewed.
- D6 The image from 21:16 — please resend; nothing was guessed for it.
- D7 «Рейтинг» chip — keep the sort, or change it to the «4,0+» filter.
- D8 Bottom navigation in the reference style — a separate small batch after this review (touches all pages).
- D9 Missing design pictures (3 bento layers, 4 offer photos, DineOut gold background, sweets flash photo, combo) — needed only
  if the owner wants design pictures instead of real data / icons; no substitutes or upscaled crops were made.

### C. Not tested
- A real iPhone / Safari (sticky header, keyboard, fixed bars behave differently on iOS). Chromium success is not iPhone approval.
- The live database; real store / dish photos and real admin banners (only test pictures; the banner path was checked with
  three test banners: 1 big + 2 small tiles, slides swipe, partner banner 3:1).
- Safari notes and the other open batches stay open (STATUS-PLAN).

## Checks (Chromium, mocked Supabase)
- `tools/design_v06_check.py` 149/149 — v62 part unchanged (109) + new part C: the 10 pages (Home, Home search, list, list
  «all», «Для вас», checkout, order details, wallet, profile, address) × RU / EN × 360 / 390 / 430 × without / with photos: no
  horizontal overflow, targets ≥ 44 (the screen-reader-only twin of the hold button excluded), fields ≥ 16 px, inside the design
  layer, no raw keys / undefined / NaN, no demo names or values, no design pictures, photo slots filled / «no photo»; Home: the
  original logo file, 6 categories in one row, every admin banner kept, Home B order, no section without data; list: every
  store exactly once, «Для вас» = your stores, «Скидки» tile = the discount filter.
- Existing suites, no check weakened: cart_check 0 fails, sheet_check OK, branch_check OK, hdr_check 0 overlaps, smoke 0
  errors, ui_rules 0 fails, flow_check 0 fails, qa_all customer (360 / 390 / 430) 0 issues, uat2 48/0, uat3 70/70,
  patch37_ui 11/11, patch38_ui 50/50.
