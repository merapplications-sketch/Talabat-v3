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
