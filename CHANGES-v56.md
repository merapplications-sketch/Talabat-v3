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

## v56d — forms wiped by automatic refresh (owner report 15 Oct, iPhone Safari, red PREVIEW)

| Cause found | Where | Fix |
|---|---|---|
| Every data event (realtime + polling every 10 s) rebuilt the whole screen. The redraw was skipped only while a field had focus; on iPhone the date picker closes = focus leaves, so the next refresh rebuilt the form. The promo form, the new-banner form, the new-store form and the loyalty settings keep their values only inside the input boxes → wiped. The page also jumped when the redraw came during the scroll / keyboard-closing animation | **shared app code** (admin.html), same in production on any busy day | Automatic redraw postponed while a field is open and until the finger has been still 1.2 s; values typed in forms are put back after an automatic redraw (unless the saved value behind the field changed meanwhile — then the saved value is shown); the new-banner picture preview is redrawn from memory; date/time fields of the banner editor and happy hours also store on `input` |
| The admin asked again every 10 s for profiles it can not find (a ticket/request whose person is missing) and reported "changed" each time → a redraw every 10 s even with no new data | **shared app code** (talabat-core.js) | Missing profiles remembered as unknown; "changed" only when a profile was really received |
| The demo tickets used `user_id` instead of `customer_id` → triggered the point above every 10 s | preview demo data only | Demo data fixed; the preview now simulates a data change every 10 s on purpose and counts the refreshes in the red strip, so the fix can be seen on the phone |

Banner editor and happy hours already kept their values (state in memory); they now also store date/time on `input`.
Tests: `tools/form_keep_check.py <preview_dir>` — real pipeline 4 cycles (promo values + scroll kept), 6 forms × 5 forced automatic redraws at 390×844 and 360×780 (values + scroll kept), picture kept, server change wins, redraw postponed while the date field is open / while touching. Before the fix the same scenario lost the values.

## v56e — one combined batch: forms, scroll, rotation, server edits (owner round 15 Oct 17:48)

Owner iPhone results on v56d: promo, banner edit, happy hours, points settings kept values; remaining: on the points settings
the page jumped to the top after rotating back to portrait (counters 49–51).

| Cause | Where | Fix |
|---|---|---|
| Automatic redraws were not held back during rotation / keyboard (only touch & scroll were watched). While iOS rotates and restores the page it can report a wrong scroll position for a moment; a redraw in that moment wrote that position back → jump. Not reproducible in Chromium (same scenario keeps the position before and after the fix) | admin.html (shared) | Redraw waits 1.2–1.5 s after `resize`, `orientationchange`, keyboard (`visualViewport`) and touch; an automatic redraw that would show the same screen does not touch the page at all; after an automatic redraw the position is held 0.5 s against late browser moves; `scrollTo` only when the position really changed; the kept-focus field is focused without scrolling |
| Values typed in forms without own state were restored only after automatic redraws; any click that redraws the same screen (e.g. «Добавить» happy hour while points settings were typed, language switch) still wiped them | admin.html | Restored on every redraw of the same screen; never carried to another screen/record (closing a form, opening another record starts clean); fields that already keep their value in memory are left alone |
| v56d showed the server value when someone else saved meanwhile → the admin's typing was replaced silently | admin.html | The typed value stays; an orange notice under the field shows the server value with «Взять значение с сервера». Banner and happy-hour editors: notice listing what changed on the server + «Открыть версию с сервера» (asks first); if the record was deleted, the editor stays with the typed values, a notice, and no save button |
| Inline `onclick="…;scrollTo(0,0)"` (11 places: open order from ratings/tickets/customers/couriers, ticket bar) scrolled the button, not the page — the order opened at the old scroll position | admin.html | `window.scrollTo(0,0)` |
| Same buttons wrote the order id unquoted (`D=${id}`): fine for numeric ids, broke with the preview's text ids | admin.html | id written as JSON (numbers stay numbers) |

Decisions for the owner (not implemented): see the report — block or confirm «Сохранить» when the server version changed (today: last save wins, as before).
Preview: every 10 s a demo courier goes on/offline, so every screen is really rebuilt (worst case); strip counts refreshes.
Tests: tools/form_keep_check.py (RU/EN, 390/844 portrait+landscape, 360, 430; 7 forms; real polling; rotation; conflicts; postpone rules; no carry-over).

## v56f — owner round on v56e (16 Oct)

| # | Note | Finding | Kind | Fix |
|---|---|---|---|---|
| 1 | Page still jumps on iPhone Safari after rotating back to portrait | Not reproducible in Chromium (before or after). Every same-screen redraw still threw away and rebuilt the whole page (innerHTML), the strongest remaining suspect on iOS | production code, cause on iOS **not proven** | Same-screen redraws (automatic or tap) now PATCH the live page: unchanged nodes are not touched (same input elements, focus, open picker, height); only another screen/record is built fresh; scroll is held only after a full rebuild. Preview diagnostic log records every jump with what happened just before (last redraw: auto/tap, patch/full; resize/rotation; focus; who called scrollTo) |
| 2 | After leaving Safari and coming back: orders list, counter restarted, draft lost (17→10, min 30) | A restarted counter = the page was loaded again (all memory gone). Two possible sources: (a) iOS throws the page away in the background and reloads it on return; (b) the 30-minute inactivity sign-out (approved security rule) → sign-out → reload (in the preview the demo login comes back at once, so it looks like a plain reload; an alert «Сеанс завершён…» appears first). Which one happened is **not proven** — the log now shows it (PAGE LOAD type, time in background, INACTIVITY SIGN-OUT). In the preview the demo "server" itself is in memory, so 10/30 are its original values after any reload | production behaviour (a) / approved rule (b) | (a) the open screen and unsaved values of content/loyalty forms are kept for THIS tab (sessionStorage) and restored after a reload, only within the 30-minute inactivity limit (the last real action time is kept, so the inactivity sign-out still happens); never kept: searches, customer/support/staff fields; cleared on sign-out. (b) unchanged (security rule) |
| 3 | Texts tab shows «…» forever | The tab showed «…» while the page list was EMPTY, whatever the reason: no rows, an error, or still loading. Preview: demo data had no rows (production seeds them in patch 25). Production: a missing table/rows or a load error also gave «…» forever, and `set_page` only updates existing rows | preview data + production display | Separate states: loading / no rows (message: nothing to edit, patch 25 creates them) / error (+ retry); loads by itself if opened another way. Demo rows added |
| 4 | Back from ord4 opened from ratings goes to the orders list | «Назад» always went to the orders list | production code | Order opened from ratings, support ticket, customer card or courier card: «Назад» returns there with its filter and scroll position; from the orders list as before |
| 5 | ord4: items 440, «Комиссия (10%)» = 10 TJS | Demo data: commission was a fixed 10 for every sample order. Display and formula are correct (place_order: (items − store discount − happy hour) × %; promo and points do not reduce it) | preview/test data | Samples compute commission with the production formula (ord4 = 44.00); new test checks every sample |
| 6 | Pages look different | Compared every tab + order details + forms, main (v55) vs branch, same data, same clock, 390 px RU: every difference comes from an approved fix (tab strip keeps the chosen tab in view #2; search box #1; caption + 2 decimals #10; delivery block #5; «Оплата и расчёты» replaces «Оплата» and holds the commission line #4; event names/durations #3; chat lines #7; date/time fields 48 px high and, on iPhone, without the native grey style #6) + version stamp. Preview-only: red strip, demo data, language follows the browser on first open (Chrome in English → EN) | — | No redesign. Side-by-side images in the preview (compare/) |

Commission, discounts, points, cashback, permissions: unchanged. No production data written.

## v56g — v56f review + UAT findings on production v52 (16 Oct)

Reference note: on `main`, admin.html and talabat-core.js were last changed in v52 (commit e5fff87); v53–v55 changed only the
customer app. So for the admin panel "main" = the v52 the owner tested; the v56f comparison (main vs branch) is the v52 comparison.

| # | Note | Status | Finding / fix |
|---|---|---|---|
| 2 | Customers → Парвиз → #9103 → «Назад» goes to the general orders list (v52) | proven in v52 code; fixed in v56f (openFrom/ordBack), now tested for this path | Same fix, no duplicate. Test: customer card → old order → «Назад» = same customer, same search text, same loaded history, same scroll position |
| 3 | Map background: tiles «403 Access blocked» | cause proven in code + OSM policy; fixed, not verified on the phone | All pages have `<meta name="referrer" content="no-referrer">`; OSM refuses tile requests without a Referer. Tile layers (admin courier map, location picker used by customer/merchant/admin, driver courier map) now send only the site origin (`referrerPolicy: strict-origin-when-cross-origin`). Nothing else changed; the provider's block is not bypassed. Before/after test: Referer None → origin |
| 4 | Парвиз card shows 50 orders, ends at #9029, no «more» | limit proven in code; identity of the 72 same-name orders not proven (needs real data) | History = orders with the account's customer_id, newest 50, nothing more and no notice. Now 50 at a time with «Показать ещё», header «показано N из M» (M = exact count for this account id), page does not move. If M = 72 the extra orders belong to the same account; if M = 50 the others are other accounts with the same name |
| 5 | Store form delivery type shows «свободны» | proven | Two texts used the same key `aFree`: «Бесплатная» (fee type free = no delivery fee) and «свободны» (free couriers, later one won). Couriers' text renamed; the form reads «Бесплатная». Value, logic and price unchanged |
| 6 | Visual reference v52 vs v55 | clarified | See reference note above |
| 2b | (found while testing 2) An order that is not among the newest 300 loaded (old order from a customer card, a rating, a ticket) opened the general orders list instead of the order | proven in code (v52 and v56f) | `vDetail` silently dropped an unknown order. Now the order is fetched (`TLB.fetchOrders`, staff read permissions unchanged) and shown; if it does not exist / no access: a message + «Назад» |

## v56h — Chrome review of v56g (16 Oct)

| # | Note | Scope | Fix |
|---|---|---|---|
| 1 | Support ticket: «Something went wrong», `ReferenceError: t1 is not defined` | Preview data: demo ticket id is text (`t1`); production ids are numbers (bigint), where `TK.sel=${k.id}` works. Same pattern in 7 handlers (ticket card, assign courier ×2, rating resolve ×2, reopen rating, rating order) | Ids written as JSON in those handlers (numbers stay numbers, text is quoted). New tests use real taps instead of setting state by script (that is why the earlier test missed it) |
| 2 | Preview strip covers the map's Close button | Preview only | Strip is now below the app's full-screen windows (z-index 800 < 900) |
| 3 | No demo customer with long history | Preview only | Demo customer «Демо-клиент · 62 заказа» with 62 old orders that, like production, are NOT in the panel's loaded orders (only paged / by-id reads see them) |

## v56i — staff look (admin + restaurant) and Safari rotation analysis (16 Oct)

Safari (separate commit): the owner's log shows both jumps at the moment of the resize ("last resize 0 ms"), the last redraw 3–4 s
earlier and no app scrollTo → the app did not move the page. Neither admin nor restaurant pages set `text-size-adjust`: iOS enlarges
text in landscape and re-flows the whole page on each rotation (probable cause, not proven). Added `html{-webkit-text-size-adjust:100%}`
to admin/merchant only, and a preview TRACE (1.5 s of frames after each rotation: page height, text size, top anchor, app scrollTo,
redraws) to tell app move / layout reflow / browser reset apart. No scroll lock, no timers.

Look (separate commit), admin + restaurant only — customer and courier apps untouched:
- one icon family (24px outline, stroke 2 — the restaurant app's existing style) in talabat-core (`TLB.icon`); emoji in buttons,
  headings and fixed labels replaced; same function = same icon; icon-only buttons have aria-labels;
- shared stylesheet (`TLB.staffUI(role)`): light page, white cards with thin border, orange for the active item / main action, neutral
  secondary, red-outlined danger, 44px fields, semantic status colours kept;
- wide screens (≥1024px): dark side menu (admin: the same 12 entries with badges; restaurant: its 4 entries); phones keep the compact
  menus (admin horizontal strip, restaurant bottom bar);
- page header = section name; indicator cards icon + label + value (no growth figures);
- restaurant app: same-screen redraws now patch the page (`TLB.morph`, the admin's method moved to the core) instead of rebuilding it.
No functions, data, rules, permissions or session policy changed.
