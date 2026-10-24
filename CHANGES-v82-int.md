# v82 — integration for review: tech v81b + driver A v06 + T3 (v56) + T4 (v58 driver) + T5 (v59 restaurant). Not merged, not published, no SQL.
Branch `tech/v82-int` = `tech/v81` (3c8cdb9) + merge of `design/driver-a-v06-on-v81-20261023` (ff8b9a2). customer.html = v80, unchanged.

## What came over (reviewed per difference, not as «newer files»)
| Part | Source | Files | Server needs (T1 live) |
|---|---|---|---|
| T2 core functions v80 calls | v59 / v60 read-only | talabat-core.js | existing tables only ✔ |
| T3 admin UAT1 items, forms kept on refresh, ids as JSON, history paging, people lookup fix, staff with `stores` see requests | v56 (+ v57 core lines that are inert without patch 36) | admin.html, talabat-core.js | patch 35 absent → search uses the loaded orders (existing fallback); leads card empty without patch 36 rows |
| T3 safety | new | admin.html | `PARTNER_ON=false`: no new banner can point to the not-activated partner page (v57) |
| v81 fix | v81 | admin.html | «add store» kept (stores_admin policy ✔) |
| T4 one delivery confirmation at a time; OSM tiles send the site origin; driver A chat keeps the typed draft | v58 / v56 | driver.html, talabat-core.js, assets/driver-a/driver-a.js (logic line only) | — |
| T5 neutral rejected / cancelled, «Чистыми к получению» + breakdown, recorded commission per order, ids as JSON, same-screen patch | v56 / v59 | merchant.html, talabat-core.js | recorded order fields (existing) |
| Approved v56 staff look | v56i–j (owner UAT) | via core `staffUI` | phones unchanged; icons + side menu on screens ≥ 1024 px — **hand-off H5** |
Not taken: v57 partner page / Edge Function / patch 36 (T8), v60–v61 finance (frozen), security-check changes.

## Driver A link items
| Item | Status |
|---|---|
| LINK-01 restaurant payment / courier settlement | No published rule or field exists: the published flow has the courier collect the customer cash (`due`) under his cash limit (`cash_balances`); paying the restaurant by the courier is patch 38 = frozen with decisions 1–8. Nothing inferred from totals; «Мои деньги» stays off. Owner decision D-L1 below |
| LINK-02 maps / location | CSP allows Leaflet (jsdelivr), tiles (https:), fonts (self) ✔ static; OSM origin fix ported; driver_location / watchPosition unchanged. Live tiles, GPS permission and denial → T6 on a device |
| LINK-03 server checks | screen guards ported and mock-tested (one confirmation, one accept per gesture); first-courier race, offer expiry, cash limit, retries → T6 live |
| LINK-04 v61 fixes | reviewed: driver-side v58 fixes ported; v60–v61 driver changes are accounting (frozen) → not ported; driver / core not replaced |
| LINK-05 photo / contact / auth | storage policies confirmed live (proofs private, own folder + order check; media own folder); a real upload and sign-in per role → T6 |
| LINK-06 iPhone | open (no device here) |

## Hand-off to the design / UI team (no change made by us)
- H1 driver A: the v52 cash breakdown (order − points − wallet = to collect) is not shown; only the amount to collect.
- H2 driver A offline: the shared offline strip (#tlb-off) covers the header text «Off shift» at 360 / 390 / 430.
- H3 driver A: delivery busy label is «Проверяем…» (dlvBusy «Подтверждаем доставку…» exists in the controller) — wording choice.
- H4 customer v80: the UAT015 estimate note on the store page is inside the folded points line (text present) — confirm.
- H5 admin / restaurant: the approved v56 staff look is now included (icons; dark side menu ≥ 1024 px; phones unchanged).
- H6 driver A «Оплата ресторану — Сумма не передана»: recommend hiding that row until D-L1 is decided.

## Checks (mock = Chromium + in-memory Supabase; nothing live)
admin_uat 0 · form_keep 194/0 · staff_ui 500/0 · tab_nav 0 · merchant_stats 0 · merchant_ids 1 (same on the untouched v59 branch
today: scroll-restore case, pre-existing) · uat2 47/0 (v80 slide + driver A) · uat3 70/70 · flow 0 · catalog OK · admin sign-in OK ·
driver T4 OK · core v80 OK · cart 0 · smoke 0 · driver A UI OK · courier 1 (= H1) · qa_all: 0 except driver offline 18 (= H2).
Tests changed only to follow approved controls (v80 slide, driver A menu / chat / labels); no check removed.

## v82b — driver A H1 / H2 / H3 / H6 from the UI team (f484f01, on eff0701) — 24 Oct
- Reviewed the commit diff only: `assets/driver-a/driver-a.js` + `.css` (presentation), their docs, `tools/driver_h_check.cjs`,
  `tools/driver_h_review.py`. driver.html / talabat-core.js / customer / admin / merchant: byte-identical. Merged with `--no-ff`;
  no newer integration work conflicted (T4 delivery lock and chat-draft rule kept as is).
- H1: cash breakdown reuses the existing `cashBox()` under the amount to collect (formula `due()` unchanged).
- H2: driver-scoped offset measured from the core offline strip; connectivity logic unchanged.
- H3: «Подтверждаем доставку…» while the delivery call is in flight only.
- H6: restaurant amount hidden (no zero / derived value). D-L1 still open. Side effect: at the pickup stage, collapsed sheet shows
  no headline amount (the only one there was the hidden restaurant row) → H7 for the UI team to confirm.
- Test tools (no check removed):
  - courier_check: driver A H1 branch (106 shown + 120 / 4 / 10 breakdown) → was the H1 failure, now passes.
  - uat2_check: the swipe must show «Подтверждаем доставку» (H3). build_preview now copies `assets/` — the earlier driver preview
    lacked the driver A layer, so the earlier uat2 driver part ran on the base driver screen; now it runs on driver A.
  - driver_a_ui_check: no headline amount check at pickup when H6 removes it (asserts the restaurant row is absent instead).
  - driver_h_check: waits until the sheet size is stable before measuring the last row (was flaky here: 2 of 3 runs failed
    while the sheet was still resizing; 4 / 4 after).
  - merchant_ids: row centred before the tap. Diagnosis: the 0→209 was Playwright scrolling a row half under the fixed bottom
    bar before tapping, not the app; a user-scrolled position (150) is kept after closing. Not functional — no app change.
- Mock results v82b: courier 0 · uat2 47/0 (driver A) · driver T4 OK · flow 0 · qa_all 0 (driver offline 18 → 0, H2) ·
  driver A UI OK · driver H 12 cases OK · merchant_ids 0 · smoke 0. Others unaffected (driver-a only) — not re-run.
- Not tested: live app / database, Safari, iPhone, GPS, live tiles, field network.

## v82c — driver waiting home (ab8fd6c, UI team) + real waiting-map binding — 24 Oct
- Reviewed ab8fd6c diff: additions at the end of driver-a.js / .css, docs, review tools. driver.html / core / customer /
  admin / merchant unchanged by it. Merged `--no-ff`; v82b corrections (H1/H2/H3/H6), T4 delivery lock, chat drafts kept.
- New `assets/driver-tech/waiting-map.js` (loaded before driver-a.js; one script tag added in driver.html) implements the
  local contract `window.TALABOT_WAITING_MAP_UI` (read / mount → update, resize, recenter, destroy):
  - location only from the existing GEO via getLocation(); no second watcher, no location write, no timer movement;
  - existing Leaflet 1.9.4 + OSM tiles (same referrerPolicy); one shared loader (waits for the core loader's tag if present);
  - restaurants: `TLB.stores()` (active records already loaded for the account) with valid coordinates only
    (finite, in range, not 0,0); closed = grey marker; no geocoding / midpoint;
  - view: start = driver + restaurants fitted into the uncovered strip (header..panel), re-fitted when the panel moves;
    a user pan is kept; «Моё местоположение» centres the real position in the strip;
  - states: map loading / ready (first tile) / error (Leaflet or tiles fail); nearby loading / ready / empty —
    «empty» only after a valid location AND the list was read; denied / loading / offline never shown as «empty»;
    onViewChange only on a state change (no render loop);
  - offline: last map kept, no live claim (UI shows «Нет соединения», button disabled).
- «Nearby»: NO approved radius / rule exists in the repo (my_offers dispatch SQL is not in the repo; delivery_max_km is the
  customer delivery limit, not a driver rule). Nothing invented: all active restaurants with coordinates are drawn,
  no radius, no ranking, no ETA. Decision D-W1 (source + radius of «nearby») is open.
- Tests: new `tools/driver_waiting_map_check.py` (local Leaflet copy, local tiles, mocked browser geolocation; 49 checks at
  360/390/430). flow_check taps the visible offer (the first aSelect in the DOM is the hidden collapsed mini card).
  Re-run (affected): waiting map 49/0 · UI-team waiting check OK · waiting offline OK · flow 0 · T4 OK · courier 0 ·
  uat2 47/0 · driver A UI OK · driver H OK · qa_all 0.
- Review page: `tools/driver_waiting_map_preview.py` → one HTML with demo data (fixture), REAL phone location + Leaflet + OSM;
  the probe follows navigator.onLine; one demo offer 25 s after «start shift». Never loaded by the app.
- Not proven: iPhone Safari, real GPS / permission prompts, real tiles, live database, live dispatch.

## v82d — H8 map failure + «Рестораны» wording + preview frame fix — 24 Oct
- H8 (waiting-map.js): when Leaflet or the tiles fail, the map area shows «Карта не загрузилась / Заказы продолжают приходить…»
  and «Повторить» (44 px), placed in the uncovered strip; panel, shift, offers and navigation untouched. Retry reloads
  the tiles (same map) or Leaflet (failed tag removed, one fresh tag); one automatic retry when the connection returns.
- Until D-W1: the provider never reports «empty»; strings in driver-a.js: wArea «Карта рядом» → «Рестораны»,
  wEmpty «Поблизости нет ресторанов» → «Рестораны не найдены» (+ EN). List source and dispatch unchanged.
- Preview black screen (v82c, Claude frame): cause = the app's frame guard (`if(window.top!==window.self) … display:none`)
  inside driver.html. Removed in the review export only (tools/driver_waiting_map_preview.py); the app keeps it.
- Checked (local Chromium headless 1194 only): driver_waiting_map_check 65/0; preview opens to «Начните смену» top-level
  and inside a cross-origin sandboxed frame; old export reproduced display:none in the same frame. Other checks not re-run.

## v82e — map failure states after the iPhone test (24 Oct)
- Cause of the iPhone report (full «Карта не загрузилась» over a working map): the message was hidden with the [hidden]
  attribute, which loses against its inline `display:flex` on the direct page (no reset sheet) → visible from the start.
  The local check read `.hidden` and missed it. Now shown / hidden with style.display; checks read computed display.
- Two levels: TOTAL (Leaflet failed, or no tile loaded and ≥4 failed) → full message + «Повторить»; any tile load later
  removes it by itself. PARTIAL (some tiles failed, others loaded) → small notice «Часть карты не загрузилась · Обновить»
  under the attribution line; the loaded part stays visible; cleared when the failed tiles load or are unloaded.
- «Моё местоположение» now centres at street zoom (≥16) so the accuracy circle is readable around the marker;
  accuracy circle tagged `w-acc` for the check.
- Checked (local Chromium headless 1194; local Leaflet copy, local tiles, mocked geolocation): driver_waiting_map_check 78/0
  incl. computed visibility at 360/390/430, partial notice, self-recovery, Tashkent marker + circle + re-centre.
