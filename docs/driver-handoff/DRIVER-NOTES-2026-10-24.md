# TALABOT — driver: one notes log + one hand-off to the UI team (24 Oct 2026)

Branch `tech/v82-int`. Technical side done by Claude; design / visual application = UI team (ChatGPT). No publish, no SQL.
Local = Chromium + fixture (mock). Live = published app + real DB (not done).

## 1. Done (technical, local checks)
| Item | State |
|---|---|
| H1 cash breakdown / H2 offline strip / H3 delivery wording / H6 restaurant amount hidden | merged (UI team), tests follow |
| Waiting home (ab8fd6c) + real map binding (GEO, Leaflet / OSM, restaurants with valid coordinates) | v82c |
| H8 map failure: full message + «Повторить» only when nothing loads; partial = small notice; self-recovery | v82d–e |
| «Рестораны» wording; never «Поблизости нет ресторанов» until D-W1 | v82d |
| Map stability: frame once per task / stage; GPS moves markers only; user pan / zoom kept | v82f |
| Panel jump: panels re-created on each render slid from their CSS top (460 / 240 px) → no transition during re-render | v82g |
| Preview frame fix (export only); direct preview link on branch `preview-driver-waiting-map` | v82d |

## 2. Hand-off to the UI team (one list; nothing here was redesigned by Claude)
| # | Screen | Request | Technical side ready |
|---|---|---|---|
| H4 | customer v80 store page | UAT015 note sits inside the folded points line — confirm placement | — |
| H5 | admin / restaurant | v56 staff look now included (icons, side menu ≥ 1024 px) — confirm | — |
| H7 | driver A pickup stage | with H6 the collapsed sheet shows no headline amount — confirm or choose one | — |
| H9 | driver A mission screen | add a «Моё местоположение» control (as on the waiting screen) | call `aMapRecenter()` (assets/driver-tech/map-view.js): frames the task again and ends the user's free view |
| H10 | driver A waiting / mission | panel `transition: top` is skipped during re-renders by `html.a-rerender` (map-view.js); if the panels are restyled keep the `.w-sheet` / `.a-sheet` class names or tell Claude | done |
| H11 | waiting map texts | provider texts wMapFail / wMapFailHint / wMapRetry / wMapPartial / wMapPartialRetry (RU / EN) live in waiting-map.js — wording review welcome | done |

Files the UI team owns and Claude touched (logic only): `assets/driver-a/driver-a.js` (4 «nearby» strings, earlier chat-draft line),
`driver.html` (delivery lock, 2 script tags). Everything else of Claude is in `assets/driver-tech/`.

## 3. Open decisions (owner) — not worked around
- D-W1: source and radius of «nearby» restaurants (none in the repo; map shows all active restaurants with coordinates).
- D-L1: does the courier pay the restaurant (patch 38 frozen; amount hidden).

## 4. Still to test (not provable locally)
- iPhone Safari round (one batch): waiting map, offer arrival, mission map, panels, permission denied, airplane mode.
- T6 live pass on the published app (needs Chrome extension or the owner); LINK-02/03/05; LINK-06 iPhone.
- T7 merge of `tech/v82-int` after owner approval (no SQL).

## 5. Delivery & tracking requests (added 24 Oct, 13:58) — plan: `docs/plan/DELIVERY-TRACKING-PLAN.md`
- Batch A started: pin chain checked locally (customer point = stored order point = courier point, flow_check);
  read-only query `sql/verify_delivery_readonly.sql` ready for the owner (courier-position read path, recipient / chat
  policies, prep / status functions, realtime tables).
- UI requests for batches B–D (route line + distance / ETA + «Навигатор», customer tracking map + draggable card + current-order
  shortcut, recipient / code screens) are listed in the plan, section 3 — one hand-off with H9.
- Blocking questions Q1, Q3–Q8 in the plan, section 4 (plus D-W1, D-L1).

## 6. Update 24 Oct 14:48 (after the live read-only result)
- Batch A done as far as possible without approval (plan sections 5–6). New UI hand-offs:
  - H12 driver A mission: show the restaurant prep time «Готовится, ~N мин» (field `prepTime`, as driver.html did).
  - H13 customer v80 order page: show the prep minutes while preparing (field `prepTime`; no «ready at» column exists).
- Review proposals P1–P5 recorded in the plan, section 7 — nothing started.
- One UI hand-off list now: H4, H5, H7, H9 (`aMapRecenter()`), H10, H11, H12, H13 + plan section 3 (B–D screens, after approval).

## 7. Update 24 Oct 15:08 — batch B + C prepared for review (nothing deployed / applied)
- One UI pack: `docs/driver-handoff/UI-PACK-2026-10-24.md` (H4, H5, H7, H9–H13 + B1, B2, C1, C2 after approval).
- B + C review and the single external approval list: `docs/plan/B-C-REVIEW.md`.
- New files: supabase/functions/route/ (index.ts, handler.js), assets/driver-tech/route-layer.js, core TLB.route /
  TLB.courierPosition, sql/verify_tracking_readonly.sql (read-only), sql/proposed/patch39_order_courier_position.sql (not applied).
- Local checks: route function 14/0 · driver route 13/0 · courier position OK · affected: map stability, driver A UI, H, T4,
  flow, core v80 — all clean.

## Working rule (owner, 24 Oct 15:33)
- This log + `docs/plan/DELIVERY-TRACKING-PLAN.md` (with `B-C-REVIEW.md`) are the single reference; update by differences only.
- No repeat of done work or passing checks unless an affecting change or a proven failure.
- Waiting: approval for ORS key + function deploy, patch 39 (confirmed needed by the 15:40 result), merge to main.

## 8. 24 Oct 15:42 — ORS setup + TRUNCATE note (no permission change made)
- ORS: accounts moved to HeiGIT (account.heigit.org, since 25 Feb 2025); `api.openrouteservice.org` is deprecated and shuts down
  2–6 Nov 2026 → the route function now calls `api.heigit.org/openrouteservice/v2/...` (same key). Function check re-run
  for this change only: 14/0. Index.ts uses the project's public key under either name (legacy anon / new publishable).
- Secrets (Supabase → Edge Functions → Secrets): `ORS_KEY`, `ALLOWED_ORIGINS=https://merapplications-sketch.github.io`.
- TRUNCATE (from the 15:40 result, `profiles` only — the query was limited to that table): role `authenticated` holds
  DELETE, INSERT, REFERENCES, SELECT, TRIGGER, TRUNCATE, UPDATE on `profiles`; `anon` holds none there.
  RLS covers SELECT / INSERT / UPDATE / DELETE but NOT TRUNCATE. Known access routes for a signed-in user: the REST API and
  supabase-js have no TRUNCATE operation; Realtime / Storage none; a direct SQL session needs a login role (`authenticated`
  is normally NOLOGIN — to confirm). The one real route would be an RPC function that runs TRUNCATE or dynamic SQL and is
  executable by anon / authenticated. Not yet closed: other tables and those functions are unknown →
  read-only `sql/verify_grants_readonly.sql` (grants on all public tables, role login / bypassrls, such functions,
  default privileges). Any REVOKE is a separate SQL step for approval.

## 9. 24 Oct 16:16 — secrets saved by the owner (not verified from here)
- Owner reports `ORS_KEY` and `ALLOWED_ORIGINS` saved. This workspace cannot reach Supabase (no network / no access token),
  so their presence is not verified by Claude; names-only check = Edge Functions → Secrets list, or `supabase secrets list`
  (names + digests, no values). After deploy the function itself answers 503 `not_configured` if ORS_KEY is missing.
- Added `supabase/functions/route/single-file-for-dashboard.ts` (generated, same code) for a dashboard-editor deploy.
- Remaining before activation: owner approval of deploy + patch 39; how to test before main (see B-C-REVIEW, test path).

## 10. 24 Oct 16:20 — owner approval (route function + patch 39, after the routing terms are settled)
- ORS commercial terms from official sources: NOT clear. Plans page: Standard free (2 000 / day), «commercial use not allowed»
  written only under the Collaborative plan; ORS staff (2019): «we don't offer commercial plans», raise quota by e-mail;
  ORS (announcement): no free support for commercial users. No official sentence allows or forbids commercial use of the
  free Standard key → route function stays on hold until the owner gets a written answer (enquiry@openrouteservice.org)
  or accepts the risk. Patch 39 does not depend on ORS and may go first.
- Owner executes from the Supabase dashboard (steps in the chat of 16:20): patch 39 in SQL Editor; route function via
  Edge Functions editor with `single-file-for-dashboard.ts`, JWT verification left ON (default, recommended for user calls).
- Live test (one round, existing test accounts, one order): branch build at
  https://raw.githack.com/merapplications-sketch/Talabat-v3/97295f1abfece1fb7e7acef77f35e8756f14c91a/<app>.html, with
  `ALLOWED_ORIGINS` temporarily `https://merapplications-sketch.github.io,https://raw.githack.com`, restored after the test.
  Patch 39 check without a customer screen: SQL Editor «run as» the test customer.

## 11. 24 Oct 16:26 — patch 39 live
- Applied by the owner in SQL Editor (Success. No rows returned); `order_courier_position(bigint)`: anon = false, authenticated = true.
- Route function: still on hold (ORS commercial terms). C1 / C2 handed to the UI team (UI pack, same file). Live tracking test
  after the C1 screen exists, together with the iPhone round. No merge, no UI publish.

## 12. 24 Oct 21:35 — UI team H + C1 / C2 integrated (4ef3b68, base 17e650d = branch head → fast-forward, no conflict)
- Kept unchanged by it: driver.html, core, map-view.js, route-layer.js, admin, merchant; patch 39 not re-run; B1 / B2 on hold.
- Review: C1 calls `TLB.courierPosition(id)` → RPC `order_courier_position(p_order)` (patch 39, live); only in «track» of that
  order while `pickedup` and the page is visible; first read at once, then every 15 s, no overlap, 10 s timeout; stops on
  leaving the page, status change (render / 60 s check), hidden tab, pagehide; late answers dropped; null → «недоступно»,
  no old point shown. Map: existing Leaflet / OSM, courier marker only, not draggable. C2: active orders only, hidden in
  cart / pay / track / sheets, placed above the cart bar and navigation; body padding stays constant over renders (checked).
- Checks re-run because affected (driver-a / customer changed): map stability 18/0, driver route 13/0, courier position OK,
  flow 0. UI team's own H / C checks not repeated.
- Found, outside H / C: customer.html refers to `assets/brand/talabot-ru.png`, which is not in the repo (main has none either) → logo
  file missing in the published customer app; asset placement is a UI-team item (H14), not changed here.
- Live test (one round, existing accounts, one order) — branch build on the live project, no merge, no publish:
  customer https://raw.githack.com/merapplications-sketch/Talabat-v3/<sha>/customer.html, driver …/driver.html,
  restaurant on the published merchant app. `ALLOWED_ORIGINS` not touched (route function not deployed).
