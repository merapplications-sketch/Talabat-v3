# v62 — design v06.1, batch 1: store page → dish sheet → cart (local; not merged, not published)
Branch `design/customer-v06` (from `fix/trial-v61`; v61 and everything before kept). Only `customer.html` changed (+ the logo
file and one new check). Core, SQL, the other apps and the other customer pages keep their look and code. Approval of this
batch only; Home, the final font and batches 2–3 stay pending. Receiving the design closes none of the old notes.

## What changed
- Scoped design layer `.d6` (colours, radii, 44 targets / 38 plates / 20 icons, header icons 22, quantity 134×46, card 152 /
  photo 150×100, sheet radius 24) used only by the three screens and the menu-page cart bar.
- Store page: cover = the store's own photo (none → neutral dark panel), logo / name / short description / rating on it;
  44 px back / favourite / share; info card v06.1 (equal columns + 44 px orange arrow → «Подробнее о ресторане» sheet with the
  store's existing data: rating, category, description, address, map link); branches; real offers only; points pill;
  «Заказать снова» and «Популярные блюда» as 152 px rails; menu sections as cards; inline menu search; ONE vertical scroll,
  no tabs (owner decision). Tapping a dish opens its sheet.
- Add control: white + → orange ✓ with the quantity only once the dish is in the cart; dishes with options open the sheet
  first; required choices block the add; the menu row keeps «−» / remove for plain lines.
- Dish sheet: photo above (the dish's own), panel max min(560px, 66dvh); title / price and quantity / add stay outside the
  options scroll; single-choice groups as 2-column cards, multi-choice as rows with a counter (0/3); «Особые пожелания».
- Cart: line cards (photo, options, the dish request, price, quantity with remove at 1), «Вернуть» after remove (same line,
  place, quantity, request; also the comment when the last line is removed), free-delivery bar, suggestions, group order,
  comment, «Добавить ещё» / «Перейти к оплате».
- Dish request: a cart line = dish + options + request (server field `order_items.note`, 120 chars; already accepted by
  `place_order` / `group_add` — no SQL). The restaurant comment still travels as a line note: on the first line without its
  own request; when every line has one it is joined to the first and the comment field is capped so nothing is cut (an
  over-long note is refused before sending). Re-order keeps today's behaviour (old notes not copied).
- `assets/brand/talabot-ru.png` — the original Russian logo, byte-identical (sha256 e05393dd…). Not shown in these three
  screens: the reference places it on Home and the restaurants list (batch 3).

## Remaining differences from the reference (documented, not hidden)
1. Font: the current system font (Nimbus Sans waits for the licence review) — letters wider / rounder, a few line breaks differ.
2. Info card: 2 columns (delivery time when measured + delivery fee); no minimum order exists in the data; the time column is
   hidden for a store without measured preparation time.
3. Not shown because the data has no source: combo banner, dish descriptions, option pictures (text cards), dish favourites
   (the app has store favourites), «Смотреть все» links, «Специальные предложения» other than the real offers.
4. Search is a field in the page (no header icon); the bottom navigation stays under the cart bar on the store page.
5. Menu-page cart bar keeps its function and text «Посмотреть корзину» (the reference says «Оформить заказ» but opens the cart).
6. Prices keep the app-wide format «16.88 TJS» (reference «32,00 TJS»); best seller badge says «Хит».
7. Below 560 px of screen height (small phone / keyboard open) the sheet may grow to the screen − 56 px so the options, the
   request and the add button are never cut.
8. Test pictures: the preview / test data have no photos, so every photo slot shows the «no photo» state.

## Checks (Chromium, mocked Supabase — not iPhone, not the live DB)
- New `tools/design_v06_check.py` 109/109: line keys with request (round trip, safe characters, old keys unchanged), same
  dish with other options / requests apart, quantity / remove / «Вернуть» keep the request, reload keeps it, requests reach
  place_order and group_add, comment placement and cap, add button states, required choice; RU + EN × 360 / 390 / 430:
  overflow, targets ≥ 44, fields ≥ 16 px, no tabs, no demo values / design pictures / raw keys, info card columns, sheet
  height at 780–932 / 560 / 420 px (keyboard-sized) with the request field reachable, cart reachable above the fixed buttons.
- Existing, unchanged selectors (no check weakened): cart_check 0 fails, sheet_check OK, branch_check OK, uat2 48/0,
  uat3 70/70, smoke 0 errors, flow_check 0 fails; qa_all customer and ui_rules — see STATUS-PLAN.md.
- NOT tested: a real iPhone / Safari (keyboard and the fixed sheet behave differently on iOS), the live database.
