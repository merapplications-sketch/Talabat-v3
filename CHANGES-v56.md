# v56 — UAT batch 1 fixes (admin panel). Branch `fix/uat1-v56` from main. NOT merged, NOT deployed.

Optional SQL: `sql/schema_patch35.sql` (read-only search function; without it the search covers only the loaded orders
and says so). No rules, discounts, points, cashback, commissions, permissions or balances were changed; no data written.

| # | Cause found in the code | Fix | Files |
|---|---|---|---|
| 1 | The orders list had no search; the panel only loads the newest 300 orders | Search box (order no., customer name, phone) + clear button, combined with the status filter; server search over ALL orders via `admin_search_orders` (same permission as reading orders: admin or staff with orders/support); fallback to loaded orders with a note | admin.html, talabat-core.js, sql/schema_patch35.sql |
| 2 | Every redraw rebuilt the tab bar / status chips (scroll reset); "Back" did not restore the list position, and inline `scrollTo` scrolled the button, not the page | Horizontal position kept, chosen item kept in view; Back returns to the same list position with filter + search kept | admin.html |
| 3 | Event kinds without a name (e.g. `at_store`, `at_customer` from patch 34) fell back to «Заказ оформлен»; durations used rounded milliseconds while times are shown with whole seconds | Real names for courier arrival; any other unknown kind shown as «Событие: <code>»; durations and total computed from the shown seconds. No events edited | admin.html |
| 4 | Payment card showed only the method name; commission shown for every order | «Оплата и расчёты»: money received (cash from the courier record; online = «не проверено», no payment-system data exists), wallet and points spent/returned from their records («записи нет» if missing), card refund «нет данных», tip and commission marked counted only for delivered orders (as the app's totals/payouts already do) | admin.html, talabat-core.js (wallet/points return times exposed) |
| 5 | "Free delivery (restaurant)" row + base + distance rows looked like 3 added charges | «Доставка (оплачивает клиент) 0.00», then an indented «Доставку оплачивает ресторан 22.00» with 10 + 12 inside it. Amounts unchanged | admin.html |
| 6 | iOS date/time inputs keep an intrinsic width; flex columns had no `min-width:0` | Date/time inputs fill their box; the happy-hour columns may shrink; checked 360/390/430 RU+EN: no field outside the screen, no horizontal page scroll | admin.html |
| 7 | Sender/time `<small>` was inline with the message text | Sender/time on its own line; text and location links wrap | admin.html |
| 8 | The banner editor button used the key `aSave` = «Создать магазин»; its action is `bannerSave()` (saves the banner) | Label «Сохранить изменения баннера». Action unchanged | admin.html |
| 9 | 3 definitions: card = every unhandled rating, filter = unhandled ≤3★, tile/badge = unhandled ≤2★ | One rule for «Требуют внимания» = not handled AND a 1–3★ mark (the filter's rule) for tile, filter, tab badge and card; unhandled 4–5★ cards say «Не обработано». The red "low rating" alert (≤2★) is unchanged — decision pending | admin.html |
| 10 | Tiles = the newest ≤300 loaded orders; revenue = sum of «Итого» of delivered ones; commission = sum of commission of delivered ones | Caption under the tiles with the period and the definition; money with 2 decimals. Formulas unchanged | admin.html |

Tests: `tools/admin_uat_check.py` 0 fails (search, permission/missing-function messages, filters, scroll, back, timeline
math, settlement, invoice, chat, banner label, rating counters, caption, forms at 360/390/430 RU/EN); `sql/test_patch35.sql`
16/16 (old orders, name, phone in any format, literal %/_, status filter, newest first, limit, admin/support allowed,
other staff/customer/anon refused, read-only); qa_all 0 issues; flow, cart, courier, smoke, header, overflow checks pass.
