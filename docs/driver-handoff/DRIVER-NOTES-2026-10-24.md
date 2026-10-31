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
  customer https://raw.githack.com/merapplications-sketch/Talabat-v3/7f60d160e589c3117686526ad92c8bbc3d5ae49f/customer.html, driver …/driver.html,
  restaurant on the published merchant app. `ALLOWED_ORIGINS` not touched (route function not deployed).

## 13. 24 Oct — Pre-owner audit, isolated repair branch (no merge / deployment)

Source / coordination:
- Started from the actual `tech/v82-int` head `bef04020e9c5bfcdf497a994fcc41bfdd706e0b5`, not the older preview.
  Read this log, UI-PACK, integration changes, saved H/C QA and T1 evidence before testing. Remote integration head
  rechecked unchanged before handoff. Repair branch: `fix/v82-pre-owner-audit-20261024`.
- Existing successful unchanged H/driver-map checks remain prior evidence; no replacement review package was built.
  Driver A / v80 / Claude fixes retained. Only the fixes below and their test harnesses changed.

Confirmed defects and repairs:
1. C1 hung RPC: the previous 10-second UI deadline did not cancel the request or release `busy`. A never-settling
   transport prevented the next location poll; leaving/returning could leave the old transport outstanding.
   Reproduced against the exact base: after 10.1 s + the next 5 s, RPC calls = 1, expected 2 (regression assertion failed).
   Repair: optional AbortSignal through `TLB.courierPosition`; abort on timeout/reset/navigation/background/pagehide;
   release pending UI work, keep 15-second cadence and epoch guards. No RPC arguments, SQL or location permissions changed.
   Current regression verifies repeated timeout cancellation/retry, no late repaint, cancel while hidden, fresh return,
   no continued polling after completion and no duplicate calls/maps during repeated render.
2. WebKit audio failure: `AudioContext.resume()` rejection escaped the synchronous try/catch. Actual local WebKit
   produced `InvalidStateError: Failed to start the audio device`; the global reload alert covered checkout controls.
   Repair: consume the resume rejection. Audio remains optional; no delivery/order action depends on audio success.
   Forced rejected-resume test passes in both engines and the previously blocked WebKit order flow now finishes.
3. H14: missing `assets/brand/talabot-ru.png` restored byte-for-byte from the approved original RU artwork, also present
   at `assets/driver-a/brand/TALABOT-Original-RU.png` (identical to the recovered design package).
   SHA-256: `e05393ddc1b94bd27dba52f40e11d670b8b5a3a0e8bbc740cf2aea46f2851e36`.
   Real image decoding/naturalWidth checked at 360/390/430 in both engines. No replacement logo designed.
4. QA fidelity, not an application-policy change: catalog fixture assumed `menu_items.approved=false` for every new dish.
   Read-only live inspection found default true, with `item_approval` forcing false for pharmacy only. Aligned the
   restaurant catalog fixture/assertion with that existing rule. No DB/default/trigger/approval behavior was changed.

Executed evidence — LOCAL, isolated Supabase/Storage/RPC doubles, not live operation:
- `python tools/flow_check.py`: Chromium 134, width 390, final combined fixes: FLOW FAILS 0; 23 screen checkpoints.
- `FLOW_BROWSER=webkit FLOW_W=360|390|430 python tools/flow_check.py`: WebKit 18.4, all three widths: FLOW FAILS 0 each;
  23 screen checkpoints each. Customer cart/payment/order → merchant prep 15 min/accept/ready → driver offer/accept/
  arrive/pickup/cash delivery → customer rating/admin visibility; cancellation/rejection/busy-driver side paths.
  The earlier unpatched WebKit run failed at checkout due to the audio error; it is not counted as a pass.
- `CHROMIUM_PATH=<headless-shell> TALABOT_UI_QA_OUT=/tmp/... node tools/ui_c_check.cjs`:
  27 C1/C2 state/width cases at 360/390/430 plus lifecycle, invalid/null/error/old timestamps, map failure/retry,
  one/multiple/current-order shortcuts, cart/navigation spacing, overlay exclusion; zero JS errors.
- `python tools/pre_owner_check.py`: Chromium + WebKit at 360/390/430: rejected audio recovery, H14 image decoding,
  location timeout/cancel/retry/null/background/return/end, no overflow; gift recipient tel-link rendered using the
  existing recipient data path; driver sheet scrolling, chat draft and reachable send control at height 520.
  No telephone link was activated or external message sent. Reduced viewport is NOT a physical keyboard test.
- `python tools/admin_login_check.py`: mock admin login errors/lock/session reload/signout/role refusal/staff sections OK.
- `python tools/catalog_check.py`: aligned fixture OK: store/cover/logo/banner create/edit, dish/photo, sizes/extras,
  customer visibility/required selection/pricing. Real file inputs, isolated storage; no live uploads.
- `python tools/cart_check.py`: CART FAILS 0: persistence, options, unavailable lines, retry idempotency key, gift input,
  group-cart return and busy state. `python tools/driver_t4_check.py`: OK, repeated delivery lock/failure recovery,
  chat draft/late response handling and tile referrer. `python tools/courier_position_check.py`: API parsing/null/errors OK.
- Reused existing waiting/sheet/map stability evidence where unaffected. New reduced-viewport checks exercise scroll,
  but no claim of physical iPhone keyboard, GPS, WebKit touch implementation or background OS behavior is made.

LIVE inspection — strictly read-only:
- Confirmed the connected project matches the application's Supabase project. Patch39 function already exists; not run again.
- Inspected live `order_courier_position(bigint)`: only own order (`customer_id=auth.uid()`), only `pickedup`, joined assigned
  driver's coordinates/time; anonymous execute forbidden, authenticated execute present. This is deployed-definition
  evidence, NOT a real second-account isolation test or a live positive tracking demonstration.
- No pickedup order with a usable assigned-driver location was available at inspection time.
- Catalog RLS enabled on stores/items/groups/options/banners. Existing media/public and proofs/private buckets and their
  policies/defaults/triggers inspected; existence of policies is NOT proof that actual account writes/uploads succeed.
- Browser inventory contained only about:blank; no authenticated TALABOT sessions or existing-account login credentials
  were available. Therefore live login, four-role order, saving/uploading, receiver chat/call, location freshness/access
  isolation and real reconnect were not completed. No test order created; no production rows/accounts/files changed,
  no records deleted, no balances settled. Do not count any synthetic orders as the authorized live test order.

Limits / remaining gates:
- Existing-account authenticated live round (one retained test order) is still required, including account isolation and
  real GPS updates during pickedup; cannot be replaced by these mocks or the read-only SQL inspection.
- Physical iPhone Safari: location permission/real stale or absent GPS, background/foreground, true keyboard/safe areas,
  vertical sheet vs horizontal confirm gesture, and reconnection during a slow request. Local WebKit is emulation only.
- No live OSM tile/CDN or phone-call completion proved; fixture maps/media failures were isolated on purpose.
- Route function, B1/B2 and frozen financial packages remain on hold and were not classified as defects or enabled.
- No SQL mutation, permission/account/financial-policy/dispatch change, main merge or app deployment.
- Preview handoff: one `customer.html` raw.githack URL pinned to the repair commit; ordinary branch preview, not a deployment
  or an isolated data sandbox. The driver and other apps at the same commit remain available from the branch source.

## 14. 25 Oct — Owner correction: interactive map/layout and cross-session chat (same repair branch)

- Continued from `91b179586146823f7605720bde38c5b21d73de49` on
  `fix/v82-pre-owner-audit-20261024`; remote branch checked unchanged before saving this delta.
  Scope is map usability/space and message visibility, not another screen-jump fix. No redesign, merge or deployment.

Map diagnosis and repair:
- Confirmed with real Leaflet: `DM.dragging.enabled()` and `DM.touchZoom.enabled()` were both true. In the exposed map
  area, `document.elementFromPoint(...)` returned `#app`, not a map descendant. The full-height positioned mission
  UI container was intercepting gestures above the sibling `#dmap`. This was an overlay bug, not deliberate map locking.
- Mission `#app` now passes pointer events through its empty area. Header, detail sheet, confirmation dock, recenter
  control and modal overlays explicitly retain pointer input. Waiting/customer UI and order logic are unchanged.
- Added 44 px Leaflet +/- controls and exposed the map region to accessibility. Existing recenter is positioned from
  the header/offline offset instead of `bottom:620px`, which could put it outside usable space on shorter screens.
- Default sheet keeps at least 180 px of map where its measured content/viewport permit; the existing expanded and
  collapsed snaps remain. No cards/content/design A replaced. Short-phone sheet content remains independently scrollable.
- Addresses in the task summary remain plain text; external directions remain the separate `Навигация` button.
  Map-unavailable hint now explicitly names that button. B1/B2, route function, routing/ETA and straight-line policy untouched.

Chat diagnosis and repair:
- Two distinct isolated browser contexts/users with a shared order reproduced this: customer message inserted;
  driver's normal scheduler fetched it; `TLB.unread(id)=1`, but `.a-chat` count was 0 while heading to/at the restaurant.
  `aTools` only rendered chat at stage >=3, despite deployed chat policy allowing assigned-driver conversations during
  preparing/ready/pickedup. The existing chat button also had no unread badge at delivery stages.
- Chat control is now present in every assigned active task stage, with the actual `TLB.unread(id)` badge/accessibility
  label. Unassigned offers still have no conversation control. Existing send/read services and permissions are unchanged.
- In isolated delivery-stage testing, customer-to-driver data receipt already worked before this delta. This repair
  addresses the proven UI visibility gap; it does not establish the cause of every possible live delivery failure.
- Confirmed read-only on deployed DB: chat_insert requires own sender, assigned driver, participant and status in
  preparing/ready/pickedup; chat_read uses can_see_order; order_chat is in supabase_realtime publication. Logs inspected
  without copying message contents/identities. These checks do not prove authenticated message delivery or Realtime events.

Affected verification only:
- `MAP_LEAFLET=<Leaflet 1.9.4 dist> TEST_ENGINE=chromium|webkit python tools/driver_map_chat_check.py`:
  six map width/height cases per engine (360/390/430 x 700/844), actual Leaflet with isolated 1 px tiles. Verified map hit
  target, real mouse pan/centre change, +/- zoom change, grip drag/collapse, sheet-body scrolling and vertical swipe not
  confirming an order. Explicit external navigation link and plain summary address checked. No horizontal overflow.
  Chromium additionally passed two-finger touch zoom injected through CDP without moving the sheet or confirming an action.
  WebKit tested mouse pan and zoom buttons; this is not physical iPhone pinch testing.
- `CHECK_PART=chat ... tools/driver_map_chat_check.py` passed independently in Chromium 134 and WebKit 18.4:
  preparing, ready, pickedup; in each phase customer types/sends -> driver's real unread badge -> driver opens/reads ->
  driver types/replies -> customer sees the reply once. Separate contexts and user IDs, no receiver reload/render calls.
  Shared test DB normalizes order_chat.order_id to bigint like Postgres; no production code type workaround introduced.
  Realtime intentionally absent in the double: the app's existing 10 s driver / 25 s customer polling proves fallback.
  The initial 20 s receiver-test deadline was too short for customer polling; corrected to 35 s, not an app polling change.
- `python tools/driver_map_stability_check.py <Leaflet dist>`: MAP STABILITY CHECK OK (18), including waiting map,
  mission, GPS/re-render/panel/viewport stability, retaining user view and recenter. No JavaScript errors in affected checks.
- Existing successful unrelated checkout/catalog/auth tests from section 13 were not repeated.

Still open / limits:
- No signed-in TALABOT sessions were available in this turn's browser inventory (no tabs). No existing-account secrets
  were available. Real customer+driver sending/receiving, actual Realtime, and real tiles/GPS remain unverified live.
  No live chat, test order, account, SQL/permission or balance change was performed.
- Physical iPhone Safari pinch/drag/keyboard/browser chrome still needs device acceptance; local WebKit is only an engine
  simulation. This delta does not activate B1/B2 or claim that a street route now exists.

## 15. 25 Oct — Internal navigation requirement: planning delta only
- Owner accepted the saved touch/chat repairs; neither reimplemented or re-tested. Reviewed their source `a03a9d7...`.
- One consolidated reconciliation/provider recommendation appended to section 8 of `docs/plan/DELIVERY-TRACKING-PLAN.md`.
  It distinguishes prepared B1 street-route display, optional customer B2, internal visual navigation gaps, and an absent
  turn-by-turn engine. Recommendation: Geoapify Free as one proposed route upstream, reusing map/proxy, NOT an activation.
- Research corrects prior ORS commercial-use uncertainty (official team permission found); records the separate current
  personal-data clause, attribution, free limits, actual Geoapify Dushanbe public-demo route samples and remaining limits.
- Only plan/log files changed. No app/SQL/accounts/secrets/functions/providers/merge/deployment changes. B1/B2 and route
  activation remain suspended pending the explicit decision. Full inputs, owners and acceptance gates are in the plan delta.


## 16. 25 Oct — Navigation evaluation gaps completed (planning only)
- Extends accepted evaluation baseline `727835abfb3648063aef06f57d56930a5f536a85`; details in section 9 of
  `docs/plan/DELIVERY-TRACKING-PLAN.md`. No repeated Dushanbe comparison/tests or accepted touch/chat repairs.
- Recorded hard-coded Dushanbe text suffix and camera defaults; separated map/route coverage from operating service
  policy and the existing pairwise route guard. No source correction or service-city activation performed.
- Added two Khujand public-demo directed routes/address selections with limits; added Yandex PWA/license/product-cost
  assessment and Geoapify foreground navigator work beyond geometry (progress, turns, off-route recalculation).
- Added all-fleet/all-city credit scenarios and proposed durable shared cap/depletion behavior with no automatic paid
  plan. One recommendation retained, approval/owners/acceptance gates explicit. ORS and B1/B2 remain held.
- Changed only this log and existing plan; app, SQL, accounts, financial logic, dispatch, deployment and accepted fixes
  remain unchanged. This documentation review is not proof of live navigation, deployed city rules or actual Safari.


## 17. 25 Oct — Approved navigation architecture / external choices implemented in source
- Continues baseline `2523d554ebaac4c4591c3613e5126d629e89cf59` on the same repair branch. Latest owner authorization
  permits this source delta; no activation/deployment/SQL/main merge or second paid/embedded provider is authorized.
- Section 10 of the existing tracking plan records the single Geoapify adapter, provider-neutral contract/view split,
  central server policy and tracking/internal/external states. Yandex Maps / 2GIS / Google Maps are external launch choices
  only, using the same actual restaurant ID coordinates then saved customer pin; text/city fallback removed.
- Missing global ledger is fail-closed. Service-only atomic `navigation_reserve_budget` RPC binding prepared for Claude's
  separate approved schema/permission proposal; no DB/RPC/grant created, no secret configured or upstream activated.
- Verification: server contract 39; browser navigation assertions 68 distinct across Chromium Android UA / WebKit iPhone UA
  at 360/390/430, including additional affected movement/deviation/cancellation cases. Local DB/GPS/upstream doubles;
  original chat/pickup/delivery still work under simulated quota. No claim of live/native-device proof.
- Evidence: NAVIGATION-QA-2026-10-25.json. One isolated fixture preview navigation-review.html; no old packages rebuilt.
  Physical installed/absent-app launch checks and live budget/location integration remain open; see plan section 10.

## 18. 25 Oct 15:13 — consultant hand-off b47ed9b integrated + shared routing budget (Claude)
- Fast-forward of the whole chain 91b1795 → b47ed9b onto `tech/v82-int` (tracking cancellation, optional audio recovery,
  customer logo, map gestures, driver chat with unread count, navigation facade / Geoapify / external Yandex · 2GIS · Google).
  No commit taken alone; earlier Claude fixes untouched.
- Shared budget (proposed, NOT applied): `sql/proposed/patch40_navigation_budget.sql` — `navigation_reserve_budget(...)`,
  3 closed tables (RLS on, no policies, all privileges revoked from anon / authenticated incl. TRUNCATE), service_role only.
  One ledger for all drivers / cities / instances; per-provider row lock → no race past the cap; idempotent request id;
  rolling window ≥ 24 h (provider reset time is not published); SQL hard limits cap ≤ 3 000, rps ≤ 5, credits ≤ 100;
  cache checks refused when exhausted; no refund on ambiguous errors. Rollback lines in the file.
- Binding: `index.ts` calls it with the service key under either name (SUPABASE_SERVICE_ROLE_KEY / SUPABASE_SECRET_KEYS).
  Missing RPC / key / timeout / bad answer → «tracking» (no route, no ETA); order, chat and delivery unaffected.
  `single-file-for-dashboard.ts` regenerated from the current modules (TypeScript syntax check: 0 diagnostics).
- Checks (local; new binding only): `tools/navigation_budget_check.mjs` 21/0 (PostgreSQL 16 / PGlite: cap, cache, idempotency,
  rate, hard limits, window, privileges, handler binding across two cities, fail-closed);
  `tools/navigation_budget_concurrency_check.mjs` OK (real PostgreSQL 17, 40 parallel connections: cap 6 held exactly,
  rps 4 held, no deadlock). Consultant checks not repeated. Simulated routes still not proven live; Yandex / 2GIS / Google
  launch on real devices still open.
- Secret for activation: `GEOAPIFY_KEY` (Supabase → Edge Functions → Secrets). `NAVIGATION_CONFIG` only at activation.
  `ORS_KEY` is no longer read by the function (can stay or be deleted).

## 19. 25 Oct 15:48 — review of f4e38dc: six blockers fixed (nothing applied / deployed)
1. Time after the lock: `navigation_reserve_budget` / `navigation_settle_budget` read the time (`navigation_budget_clock()`)
   only after `FOR UPDATE`. Real PostgreSQL 17: a request that waited for the lock across an hour + second boundary is judged
   and booked at the new time (new hour bucket, rate counter restarted); released inside the same second → still «rate».
2. Cost: fixed reservation replaced by `routeCredits()` from Geoapify pricing-details (waypoints − 1; +1 per 500 km when the
   route is > 500 km, counted as ceil; + `detailsCredits` 1 as a conservative surcharge for `instruction_details`, whose price
   is not published). Excess after the real response is settled (`navigation_settle_budget`), even above the cap. Scope: only
   requests through this proxy are counted — other use of the Geoapify account is invisible; dedicated key + cap ≤ 2 400.
3. Attribution: fixed «Powered by <a href="https://www.geoapify.com/">Geoapify</a>» (server text never inserted as HTML),
   Leaflet attribution moved top-right on the mission map (bottom corner is under the sheet).
4. Default rollback = disable: `NAVIGATION_CONFIG` internal:false + `sql/proposed/patch40_disable.sql` (revoke execute);
   no table dropped, no booking reset; hour buckets are no longer deleted by housekeeping.
5. Quota test = `"dailyCredits":0`: refused at once, no upstream call, ledger unchanged.
6. Privacy: live text = `app_pages` row `privacy` (body_ru / body_en, admin `set_page()`); RU / EN addition prepared in
   `docs/plan/PRIVACY-NAVIGATION-DIFF.md` (two points only, server-side request, Geoapify ≤ 24 h retention, external apps,
   customer sees courier position while on the way). Not applied.
- Checks run (fixes + missing cases only): navigation_budget_check 26/0 (PGlite) · navigation_budget_concurrency_check OK
  (PostgreSQL 17: 40 parallel, lock-wait boundaries) · navigation_contract_check 39/0 (handler changed) ·
  navigation_attribution_check OK (360/390/430). Dashboard copy regenerated, TypeScript: 0 diagnostics.

## 20. 25 Oct 16:10 — review of f174ce9: three remaining blockers (nothing applied / deployed / merged)
1. Cost before the call: request restricted to published-price options (2 waypoints, drive, ru; `details` removed — the step
   text and indices stay, the unused maneuver type goes). Formula corrected to the docs: one pair = max(1, ceil(km / 500))
   (630 340 m = 2). No pre-call ceiling can be documented (length known only afterwards, no max-length option) → the cap is
   NOT guaranteed before sending; routing stays disabled; plan section 11 marked BLOCKED for the owner's decision.
2. Settlement: one request id per route call for reservation + settlement (same ledger row); settle always, before the
   `config_changed` check; RPC error → throw, only `recorded:true` accepted, 3 tries with the same id (idempotent, «conflict»
   on a different total); unconfirmed → route withheld; unsettled > 60 s blocks every reservation («unsettled»), housekeeping
   keeps such rows; owner recovery SQL in patch 40. `patch40_disable.sql` follows the new signature.
3. Privacy: RU / EN now say «как правило» / «generally», successful requests only, no period for other cases; live text match
   stays open until `app_pages/privacy` is read. Not applied.
- Checks (missing cases only): navigation_budget_check 43/0 (PGlite; new: restricted request, docs example, same id, repeat /
  conflict / unknown, RPC error, no recorded:true, lost reply, unsettled guard + housekeeping + recovery, settle before
  config_changed, upstream error); navigation_index_binding_check OK (index.ts: RPC args, error → throw);
  navigation_contract_check 39/0 (consultant test: settle double + cap 2 for 1 credit per call); concurrency check OK
  (PostgreSQL 17, reserve function changed). Dashboard copy regenerated (0 syntax diagnostics, all module lines present).
  Time / attribution / rollback / dailyCredits 0 closed by the consultant — not reopened.

## 21. 25 Oct 17:12 — consultant closed add55b3; one test point (internal routing off)
- External Yandex / 2GIS / Google: the driver UI gets them ONLY from the Edge Function `route` (`TLB.navigation({op:'config'})`
  then `{op:'links'}`); no local fallback. The function was never deployed (log 10–12) → live the «Навигация» sheet shows
  «unavailable», no links. Not provable from here: the workspace cannot reach the project (allowlist) and Chrome is not linked.
- Server step needed (owner, separate approval; NOT done): deploy `route` from `single-file-for-dashboard.ts`, JWT verification
  ON; secrets: `NAVIGATION_CONFIG` = `{"internal":false,"external":true}` (or unset — same result), `ALLOWED_ORIGINS` +
  `,https://raw.githack.com` for the test only; `GEOAPIFY_KEY` not needed, patch 40 not needed. Local check of that exact mode
  (handler, empty key, ledger and upstream that would fail): config «tracking/disabled», links yandex,2gis,google, route request
  «disabled», foreign origin 403, upstream 0 calls, ledger 0 calls.
- Everything else of the test (order, chat, waiting / mission maps, courier tracking C1 via patch 39) uses DB / RPC already live.
- 17:45 owner approved deploying `route` for external navigation only at bb37893 with `{"internal":false,"external":true}`;
  the unchanged file (sha256 ac32b015…bf860) and dashboard steps sent. Deploy done by the owner — result pending. No Geoapify / patch 40 / main.
- 18:24 live: function deployed (JWT ON); Invocations show only OPTIONS 200, no POST, no options in the app.
  Diagnosis: the app's supabase-js 2.117.2 asks for apikey, authorization, content-type, x-client-info — all allowed (real
  Chromium). Gateway 401s would appear in the same log (function_edge_logs), so the POST never left the browser = CORS refusal
  after the preflight. Only reproducible cause: page origin not matched in `ALLOWED_ORIGINS` — the handler then answered the
  preflight 200 with another origin's header; Chromium blocks the POST (exact live pattern). The secret's value cannot be read
  from here; the new log will confirm it.
  Fix (handler only): preflight from a non-allowed origin → 403 (visible in Invocations); secret entries reduced to their
  origin (spaces, quotes, trailing «/», full page URL). JWT unchanged. Check: `tools/navigation_cors_check.mjs` OK (Chromium +
  supabase-js 2.117.2: headers, POST reaches, 3 links, missing origin → OPTIONS 403, tolerant entries); contract 39/0.
  Dashboard file regenerated (0 syntax diagnostics) — owner redeploys `route` with it.
- 19:27 live after redeploy: OPTIONS 403, no POST → the origin refusal is now confirmed (headers were never the cause). The
  edge log has no `request.headers.origin` (only `deno_origin`, the function's own host), so the received value is unknown.
  Added a limited refusal log (handler, Logs tab): `{"route_cors":"refused","method","origin","allowed":[parsed list]}` —
  origins only, no headers / keys / sessions / body / coordinates. CORS check re-run (affected): OK incl. the log line;
  contract 39/0. Dashboard file regenerated. Next: one opening of «Навигация», then read that log line.


## 22. 25 Oct 21:28 (+05) — live ALLOWED_ORIGINS correction (secret only)
- Verified project `dzydscryrnahnneydnry` / Talabat, org `bxhspuyufwkwfuggeowt`; dashboard account has access. Function `route` version 3, JWT verification ON. Reference source `9dbe13ab7535b1e5ce2b539f112d9577c6085cbe`.
- Replaced (did not delete) `ALLOWED_ORIGINS` with `https://merapplications-sketch.github.io,https://raw.githack.com` through the dashboard. Saved at 2026-10-25 16:28:11 UTC; dashboard SHA256 `858da38f721f870c2eb5bdc1b09e7375de0fab505fc3a9daa14fa4a8a6faeab2` matches the exact requested value. Other secret digests unchanged; NAVIGATION_CONFIG unchanged, internal routing remains unactivated. No code deployment, SQL, patch40, Geoapify, account or order changes.
- Live OPTIONS /functions/v1/route, Origin https://raw.githack.com, requested POST and authorization/apikey/content-type: HTTP 200, Access-Control-Allow-Origin https://raw.githack.com, methods POST/OPTIONS; request id `01a173e4-a960-79d0-8782-7a9f0a602405`, execution id `6987da75-ae9a-4c64-9e5b-28b0df275bed`.
- Unauthenticated POST {"op":"config"}: gateway HTTP 401 UNAUTHORIZED_NO_AUTH_HEADER (request id `01a173f4-2bf1-7485-9a0b-59c12e3b0552`). This confirms authentication remains required; it is NOT a successful authenticated function test. The gateway supplies its own wildcard CORS response on this 401; no wildcard was configured by this change.
- Quotes in the earlier refusal log originate from `origin: JSON.stringify(origin)` inside the JSON log. They alone do not prove literal quotes in the request header. After the secret correction OPTIONS is accepted; no code correction is indicated by that evidence.
- Pinned live driver page opened. Secure sign-in attempt returned “Неверный email или пароль” (invalid email or password). Authenticated POST config/links and actual Yandex/2GIS/Google choice visibility remain OPEN, as does real iPhone app launch. No successful unrelated checks repeated. Next: owner completes valid driver sign-in in the existing cloud-browser handoff; then open Navigation for an existing order without changing its state.

- Follow-up 25 Oct: owner completed driver sign-in. Opened Navigation for the existing picked-up task, without accepting/completing/changing the order. Live dialog displayed Yandex Maps, 2GIS and Google Maps, each with app/web links. Existing internal-routing-disabled / tracking-only message stayed visible. Map remained behind the dialog.
- Authenticated POST flow is functionally confirmed by those returned links: source route-layer.js clears links on opening and loads them exclusively with TLB.navigation({op:'links',to}); talabat-core.js uses sb.functions.invoke('route', {body,...}). No local/demo link fallback. Exact HTTP status/request-id for this authenticated POST was not independently captured. Attempt to reopen Supabase UI for additional observation was rejected by automatic browser review as outside its current origin authority; not retried or bypassed.
- Evidence: talabot-navigation-fixed-20261025.jpg (live browser capture). Closed: corrected allowlist, live preflight, authenticated app navigation options. Remaining: actual external-app launch on iPhone / device fallback behavior. No code fix or deployment required; no new SQL, secrets, accounts, order state or calculations changed in this follow-up.


## 23. 25 Oct — Driver A phone / navigation polish (review only, not deployed)
- Source matched against latest tech/v82-int `9dbe13ab7535b1e5ce2b539f112d9577c6085cbe`; independent branch `design/driver-polish-20261025` starts from local documentation checkpoint `2aea00986c61134cd09dd6885e095d3174f9fb90` (same application source). Sections 20 and its live CORS fix retained. No Supabase/JWT/SQL/Geoapify/main/deployment changes.
- Driver A only: 56px header plus safe-area; measured sheet/dock boundaries, compact collapsed summary with map space; current step + persistent «Все этапы» disclosure; earnings shown once, collection separately; existing legs / fee details kept in Order and amounts. Navigation/call/chat share 44px plates. No due(), cashBox(), payout/points formula, chat, tracking or delivery-service edits.
- Pickup success: the old generic toast at bottom:96 overlapped the swipe. Its UI-only replacement appears below the header, pointer-events:none, only after awaited server result; stale-stage duplicate guard retained after the visible notice expires. Existing TLB.setStatus / RPC refresh already awaits server acknowledgement and reload; tests confirm transition ready -> pickedup / step 2 -> 3. Pending and failed responses never show success.
- Chooser: one row/provider, primary Open + secondary Website link, fixed visible close, scroll body on short screens, Escape/focus return. One external-mode note; no unavailable ETA displayed, no repeated disabled copy. Server facade, provider allowlist and destination validation unchanged.
- Google / 2GIS website and app URLs returned by the service are identical HTTPS URLs. Google Maps documents that its universal URL launches the installed iOS app: https://developers.google.com/maps/documentation/urls/get-started . Therefore «Website link» replaces the browser-only promise; one short note explains the phone may open an app. No fabricated browser-forcing parameter or new link service. Yandex custom scheme preserved.
- Affected checks only: 156 distinct passes in isolated Chromium / Playwright WebKit at 360/390/430 x 780, chooser shortened to 520; extra pointer grip drag / content scroll / short mission / points-inclusive cash presentation at 390 on both engines. Full matrix: 24 per size/engine (144); extras 6 per engine (12). No page errors. Existing general/finance/backend suites not repeated. WebKit initial failed text assertion was trailing whitespace; assertion corrected to the actual heading text, UI unchanged.
- Evidence/preview: regenerated the existing `navigation-review.html` with `tools/driver_polish_preview.py`: one self-contained, explicitly labelled review fixture, no live Supabase, GPS, provider or payments; blank offline Leaflet tiles and synthetic points exist only in the review. Production CSP/frame guard unchanged. The existing broad navigation UI test's one affected link-hint assertion updated, not re-run. New affected checks: driver_polish_check.py + driver_polish_touch_check.py. Screenshot set below is from simulation, not an actual iPhone.
- Claude integration: shared files are assets/driver-a/driver-a.js, driver-a.css and assets/driver-tech/route-layer.js. Apply their narrow presentation diff onto current integration source; preserve map-view.js, waiting-map.js, talabat-core.js, driver.html, navigation-model.js, customer v80 and deployed route function/secrets. No service change needed for this polish. B1/B2 and routing activation remain outside scope. Before any later release: review this preview; actual iPhone safe areas/toolbar/touch/native app handoff and real server pickup remain acceptance items (no live order was changed for this batch).

- Screenshot files: polish-20261025/mission.png, collapsed.png, navigation.png, pickup-success.png. Reproduce isolated checks/build with `MAP_LEAFLET=/path/to/local/leaflet python tools/driver_polish_check.py` and `... python tools/driver_polish_touch_check.py` (Leaflet JS/CSS local directory; no live tile/provider requests). One preview at navigation-review.html; actual map tiles intentionally blank and labelled in the shell.

## 24. 26 Oct 02:24 — designer polish 79af0bb integrated (base 9dbe13a = branch head → fast-forward, no conflict)
- Shared files: `assets/driver-a/driver-a.js` / `.css` (sheet metrics, collapse, stage disclosure, money rows, success notice)
  and `assets/driver-tech/route-layer.js` (chooser layout, external note, Esc / focus). Kept unchanged by it: map-view.js
  (framing, a-rerender), waiting-map.js, Geoapify attribution, route function / CORS log, core, patch 39. Internal stays off.
- Affected checks only: driver_map_stability_check 18/0 (sheet metrics changed) · navigation_attribution_check OK
  (route-layer changed). Designer's polish checks ran on the identical tree — not repeated.
- External maps live: still waiting for the `route_cors` log line (section 21); the chooser shows no links until then.


## 25. 26 Oct — Connected Journey A R1 bound to the application (review branch only)
- Independent branch `design/driver-journey-r1-20261026`, integration base `461d442bb20c96b29f8ce6f32c932d5b44aeb3f8` (rechecked before handoff; no newer integration head). Design package TALABOT-Driver-A-Connected-Journey-R1(1).zip SHA256 `0239f12402a5933903c44c0f33410a9563e21c4b497226b2010b50ab5b62713f`. Designer R1 source/spec compared first. Logo and both 400/700 font files match the package hashes exactly and are unchanged. Designer's proposed local record was read as reference; the existing current record is appended, not replaced.
- Application changes: assets/driver-a/driver-a.js and driver-a.css only. Bind designer Work/Map distribution to existing task fields and handlers. Four short visible steps (acceptance remains separate n=0), destination, x.payout and cash due(x) / online-paid state, labelled 44px navigation/call/chat, next action together. Offer is shown directly in this layout, never auto-accepted. Details uses invoice/cashBox/notes/legs and retains decline and switching to another valid offer; existing sections and end-shift remain in menu with original conditions. Shift shown once; source unlockSound/testSound replaces the long sound banner. No demo data, map-demo.svg, demo-adapter.js, prototype service or alternate finance logic enters application assets.
- Layout: measured 52px header plus actual safe inset; panel and dock are separate flex items in available visualViewport height (100dvh fallback), preserving .a-sheet/.w-sheet/#a-sheet-body/#a-dock/#a-grip and html.a-rerender hooks. Work opens by default; Map compacts secondary text, retaining four steps, destination, amounts, tools and confirmation. Only the independent 44px grip drags (8px axis lock, 36px switch, vertical x1.3), with live height feedback, cancel restore and equivalent mode/keyboard controls. Original stricter horizontal confirmation swipe is byte-identical. Cancelled/dragged grip suppresses its following click until a fresh pointer down; Enter/Space remains usable.
- Exceptional text fix discovered by the new edge check: do not derive available bottom from an already displaced dock. Anchor to actual app bottom minus measured dock height; cap body and explicitly scroll it for exceptional titles/font sizes. Standard test data needs no scrolling. No line clamps, invented addresses or unbounded font shrinking. Missing store/customer address shown explicitly. Auxiliary details has a fixed close header/scroll body; existing chat and delivery form handlers preserved, with modal bounded to visualViewport height. Actual iPhone keyboard/Safe Area behavior still needs device acceptance.
- Preserved byte-for-byte versus integration base: aRun, aBlocked, aTaskStage, aActionLabel, aCashDetail; driver.html (due/cashBox/stepOf/deliverClick/confirmDeliver), talabat-core.js, map-view.js, waiting-map.js, route-layer.js and customer.html. finish UI result adds a timestamp only; completed notice requires successful original finish AND actual source order.status === delivered. No internal route activation; external config/links/filters/CORS unchanged. No SQL, JWT, server/secrets/accounts, dispatch, payout/points rules, main merge or deployment.
- Affected verification: 226 unique passes across actual driver/core with isolated service doubles. Full offer -> accept -> store arrival -> not-ready/ready pickup -> customer arrival (atCustMsg once) -> original cash discrepancy/note gate -> delivered server response, and duplicate/pending/failure controls. Chromium and Playwright WebKit at app 360x652, 390x716, 430x804 (explicit 44+84px simulated browser bars outside app); final layout-only pass also at 712/776/864px app heights (24+44px bars). Edge checks include partial/vertical/cancel gestures, measured simulated 32/24px safe insets, long/missing addresses, cash/online display, unread badge, draft + chat payload at 360px keyboard-height simulation, original photo requirement, one Leaflet instance and user pan/zoom across modes/render. One WebKit scroll check waits for the scroll frame; pan check waits for Leaflet inertia, not a UI fix. No unrelated successful general/CORS/backend suites re-run.
- One isolated actual-source preview: journey-r1-review.html, built by tools/driver_journey_r1_preview.py. It embeds the current application UI/core with existing test service doubles; blank Leaflet tiles and synthetic points only in the clearly labelled review, no live GPS, accounts, provider, order changes or payments. Browser bars and size selection live outside iframe. Start at offer and actually swipe; restaurant ready/preparing/failure controls are outside application. Sources of test evidence: tools/driver_journey_r1_check.py, driver_journey_r1_edges.py, driver_journey_r1_layout.py (MAP_LEAFLET local JS/CSS directory).
- Implementation screenshots from WebKit simulation at actual available viewport, not designer mockups: journey-r1-20261026/{offer,work-360,work-390,work-430,map,customer,handover,done,long-text}.png. No actual iPhone/Safari acceptance or live server mutations claimed. Remaining for Claude: integrate the narrow driver-a.js/CSS presentation diff after checking newer source; review preview, then live test real offer eligibility, server acknowledgements/photo upload, external-app return and real iPhone Safari/PWA toolbar, keyboard and safe areas. B1/B2, customer/admin pages and internal navigation remain out of scope.

## 26. 26 Oct 17:08 — Journey R1 1807c57 reviewed and integrated (base 461d442 = branch head → fast-forward)
- Reviewed against the designer package R1 (IMPLEMENTATION-AR) and the ui-ux-pro-max checklist: offer shown in the journey
  composition (package item 12), 4-step bar, destination + order #, money (earnings / collect or «paid online»), call · chat ·
  Навигация, one 44 px panel head (grip + Детали + Карта/Работа toggle — a non-drag alternative), drag only on the grip,
  visualViewport height for the keyboard / Safari toolbar, success notice after the server answer only. Demo adapter,
  map-demo.svg and fixtures are not referenced by driver.html / assets / core. Kept: map-view.js, waiting-map.js,
  route-layer.js, internal routing off, route function / ALLOWED_ORIGINS (external maps already verified on the phone).
- No blocker. Non-blocking notes for the designer: some secondary labels are 10–11 px (stage names in map mode, swipe help,
  «Без жеста», map status line) — below the 12 px guideline; the first offer opens automatically (others in «Детали»).
- Affected checks only: driver_map_stability_check — 2 expectations updated to R1 (offer opens the journey panel, sampled
  #a-sheet) → OK; navigation_attribution_check OK; driver_waiting_map_check — 2 expectations updated to R1 (offer → journey
  panel; one live map after leaving and returning), behaviour 75/75; the 2 remaining FAILs are history-scope diff assertions
  that already failed before R1 (461d442), not behaviour. Designer's 226 checks ran on the identical tree — not repeated.
- Still open (device / live): keyboard + safe areas on iPhone, live operations with the test accounts, return from the
  external map app with the order and chat kept.


## 27. 26 Oct — Safari page pull versus Driver A grip (review fix only)
- Owner iPhone evidence IMG_5724(2).jpeg on integrated `fee8b6f2318c3cf1bfa9f82b1da9d3dedd91a072`: pulling the mission grip also pulls the document, showing Safari refresh spinner/white area above the logo. Latest integration fetched and matched fee8b6f before editing; independent branch `fix/driver-grip-safari-20261026`. No concurrent integration edits overwritten.
- Narrow fix in assets/driver-a/driver-a.js + driver-a.css: while an actual mission/offer is displayed, lock the root overflow/overscroll and fix the body in the viewport; remove that class on utility/phone-gate exit. Grip and its child handle explicitly own touch-action:none; a grip-local non-passive touchmove listener cancels native document panning from the first movement. No document-wide touchmove cancellation; detail/chat scroll and Leaflet gestures retain their existing rules. Existing pointer thresholds, capture, cancel/release, mode button and horizontal confirmation handlers unchanged. This addresses the code-level opportunity for root rubber-banding; final native Safari acceptance is still required.
- 36 affected Chromium checks PASS at 360/390/430, app heights outer 780/844/932 minus simulated browser bars 128/68/128px. Native CDP touch repeated three down/up cycles per size/bar state (27 full cycles / 54 directional drags); header stays at viewport top, scrollY=0, dock above viewport bottom. Grip-child touch-action, cancelable touchmove prevented, Work/Map button, one Leaflet map with working pan, independent detail scroll, partial confirmation and root-lock removal on exit verified. JS syntax and diff whitespace checks pass. No R1 226 successful checks re-run.
- WebKit could be downloaded but could not launch: host lacks GTK4/GStreamer/other shared libraries; dependency installation failed with setgroups/seteuid Operation not permitted. No WebKit success claimed for this fix. Chromium is desktop phone/touch simulation, NOT an iPhone; native Safari pull-to-refresh, real toolbar expansion/collapse and external-app return remain device acceptance items. Evidence/results in grip-safari-20261026; reproducible limited runner tools/driver_grip_safari_check.py (GRIP_ENGINES=chromium for this host).
- Claude handoff: apply only the two application file diffs onto integration after checking newer work. Existing driver.html/core/map-view/waiting-map/route-layer, route secrets and all finance/server/account rules unchanged. No SQL, backend changes, internal routes, main merge or deployment. Test driver.html pinned to the fix commit on raw.githack.com; this is a review branch connected to the existing test project, not an integrated release. Integration by Claude and actual iPhone acceptance remain pending.

## 28. 26 Oct 23:10 — Safari grip pull fix c573842 integrated (base fee8b6f = branch head → fast-forward)
- Diff: `driver-a.css` — `html.a-mission-lock` (root height 100 %, overflow hidden, overscroll none) and fixed
  `body.a-mission` only while a task / offer is on screen; `#a-grip` touch-action none, no text selection.
  `driver-a.js` — non-passive `touchmove` on the grip only (preventDefault), lock class toggled in render0 and removed at the
  phone gate. Detail / chat scrollers, Leaflet, «Карта/Работа», swipe bar and visualViewport sizing unchanged.
- Log: duplicate section numbers renumbered in file order (old 13/14 of 25 Oct → 18/19, then 20–27); content unchanged.
- Integration checks (Chromium, local): navigation_attribution_check OK; driver_map_stability_check 18/0.
  Correction to section 26: that stability run had stopped at the waiting-map zoom step (the R1 offer keeps the journey
  panel open) and was reported OK by mistake. Test fixed, not the app: the offer is withdrawn before the waiting-map zoom
  step, and «a tap on the grip animates» became «a tap switches Work / Map» (R1 has no slide animation by design).
  Neither failure came from c573842.
  WebKit not available here either (only Chromium installed; Playwright reinstall not allowed) → the grip fix is NOT
  WebKit-checked. Designer's 36 Chromium checks ran on the identical tree — not repeated. Device acceptance of the drag
  on iPhone Safari remains open.

## 29. 26 Oct — جرد الماركت بليس للمصمم وكلود (قراءة وتوثيق فقط)

> Imported unchanged from `48974d1` (programmer, base fee8b6f); numbered 24 there. After the renumbering in section 28 its references map as: «§20» (external maps shown) = §22, «§23» (drag fix) = §27; «§11–13» unchanged. Read only — not re-verified beyond the spot checks in §30.

**المصدر:** أحدث `tech/v82-int` كما جُلب في هذه الجولة: `fee8b6f2318c3cf1bfa9f82b1da9d3dedd91a072`. الجرد لهذا المصدر تحديداً، وليس main أو إصدار إنتاج. إصلاح السحب `c57384269d0491d692c1803af7a9614cc7886195` مسلّم على فرعه؛ لا تعديل موازٍ عليه ولا استيراد أو إعادة تنفيذ له هنا. هذا ملحق للسجل نفسه، لا سجل قرارات جديد.

**معنى الحالات وحدود الحكم:** «موجود ويعمل» = مسار فعلي متصل في المصدر تؤيده النتائج المحفوظة المذكورة؛ لا تعني نجاح تجربة حية جديدة. «موجود جزئياً» = جزء محدد منفذ والباقي مفقود أو غير مفعّل. «واجهة فقط» = عرض بلا مسار حفظ/تنفيذ متصل؛ لا يصح وصف المسارات المتصلة أدناه بهذه العبارة. «غير موجود» = لم يُعثر على مسار متكامل له في صفحات التطبيق/core/SQL المحفوظة؛ ليس حكماً على أنظمة خارج المستودع. **غير المفحوص حياً ليس معطلاً.** لا اختبارات أو SQL أو اتصال بقاعدة البيانات أو تعديل تطبيق أُجري لهذه الجولة.

### جدول المطابقة

| الميزة | الحالة | مرجع المصدر وما ينفذه فعلاً | الدليل المتاح وحدّه | الخادم / قرار التشغيل / التسعير اللازم |
|---|---|---|---|---|
| طلبات المطاعم والمتاجر | **موجود ويعمل** | [customer.html](../../customer.html): `CATS`, `vMenu`, `vCart`, `vPay`, `place`؛ [talabat-core.js](../../talabat-core.js): `placeOrder`, `ordersQuery`, `setStatus`؛ [merchant.html](../../merchant.html): `vOrders`, `st`. فئات مطاعم وبقالة وصيدلية وجمال وزهور وهدايا وحلويات ومتاجر على مسار الطلب نفسه؛ الطلب لسلة تاجر واحد، لا سلة متعددة التجار. | E1: رحلة الأدوار الأربعة بمحاكاة الخادم محفوظة وناجحة؛ E2: كتالوج وصلاحيات وبيانات حقيقية موجودة. لا دليل جديد على إكمال شراء حي أو حفظ فعلي بكل حساب. | `place_order`, `delivery_quote`, حالات الطلب والصلاحيات موجودة؛ لا حاجة لبناء طلبات المتاجر من الصفر. فئات جديدة/سلة متعددة التجار تتطلب قراراً وعقداً منفصلاً. لا تغيّر العمولة أو أجور التوصيل القائمة. |
| الاستلام الذاتي من التاجر | **غير موجود** | `vPay` و`placeOrder` لا يرسلان نمط fulfilment/pickup؛ [sql/schema_patch33.sql](../../sql/schema_patch33.sql): `place_order` يفرض عنوان توصيل وإحداثيات، والمسار يذهب للسائق. كلمة pickup في حالات السائق تعني استلام السائق، وليست استلام الزبون الذاتي. | قراءة واجهة/عقد/RPC وSQL؛ لا مفتاح تفعيل أو مسار استلام ذاتي وجد في المصدر. | يحتاج نمط طلب خادم، انتقالات استلام وتحقق تسليم للزبون، وآلية احتساب/إلغاء أجرة التوصيل والعمولة. لا يختزل إلى إخفاء العنوان بالواجهة. |
| الطلبات المجدولة | **موجود ويعمل** | `customer.html`: `whenCard`, `slotsAll`, `optExtra`؛ `merchant.html`: `early`, `optChips`؛ `talabat-core.js`: `placeOrder`؛ `schema_patch33.sql`: `scheduled_for`, `set_order_status`. واجهة 45 دقيقة–3 أيام بخطوات 15 دقيقة؛ الخادم يقبل 40 دقيقة–3 أيام، والتحضير من ساعة قبل الموعد. | E3: `CHANGES-v51.md` يسجل SQL 35/35 وجدولة/too_early وcart checks؛ E2 يؤكد patch33 موجوداً. ليست جدولة سائق مضمونة أو حجز سعة؛ التحقق التشغيلي الحي غير مفحوص هنا. | البنية قائمة؛ يلزم قرار تشغيل حول ساعات المتجر، السعة، الالتزام بالموعد والإلغاء إذا توسعت الخدمة. لا رسم جدولة خاص مثبت. |
| الطلبات الجماعية/المكتبية | **موجود ويعمل** | `customer.html`: `grpStart`, `grpPush`, `grpCheckout`, `grpShare`, `vGroup`؛ core: `groupCreate/Get/Add/Remove/Set`؛ `schema_patch33.sql`: `group_orders/group_items` وRPCs. متجر واحد، رابط مجموعة، أعضاء مسجلون، صلاحية 3 ساعات، المضيف يغلق ويطلب مرة ويدفع فاتورة وتوصيلاً واحدين. | E3: اختبارات الإنشاء/الإضافة/الإغلاق/منع التكرار/الخصوصية مسجلة؛ E1 يفحص رجوع سلة المجموعة. تجربة متعددة الحسابات على الخادم الحقيقي غير مثبتة في هذه الجولة. | لا تبنوا تجميع الأطباق من جديد. دفع كل موظف منفرداً أو فاتورة على شركة ليس جزءاً من هذه الوظيفة ويحتاج عقداً وقراراً جديدين. |
| شريط الطلب الجاري | **موجود ويعمل** | [assets/customer-c/customer-c.js](../../assets/customer-c/customer-c.js): `current`, `ACTIVE`, `sync`. طلب واحد يفتح تتبعه؛ عدة طلبات تفتح النشطة. يظهر أعلى السلة والتنقل، ويختفي في الدفع/السلة/التتبع والحوارات المعينة. | E1 وE4: 27 حالة C1/C2 وحالات المقاس/المسافات والحوارات محفوظة؛ المصدر يعتمد `TLB.orders()` الفعلية، لا نصوص نموذج. قبول الآيفون الحقيقي لا يستبدل بالمحاكاة. | لا خادم جديد للشريط؛ يعتمد قراءة الطلبات الحالية. القائمة المحلية محدودة بأحدث 60 طلباً للزبون؛ لا يُقدَّم كبحث شامل تاريخي. |
| حالة المطعم والسائق + خريطة التتبع | **موجود ويعمل** ضمن الحدود | `customer.html`: `orderSummary`, `vTrack`, دردشة/اتصال؛ `merchant.html`: `st`, `set_prep_time`؛ core: `driverArrived`, `courierPosition`, `chat`؛ `customer-c.js`: `eligible`, `request`, `reset`. الموقع للطلب المملوك أثناء `pickedup` فقط، كل 15 ثانية، مهلة 10 ثوانٍ وإلغاء عند الخروج/الإخفاء/انتهاء الحالة؛ وقت تحديث وحالة عدم الإتاحة. | E1/E4: محاكاة الرحلة ودورة الموقع/الإلغاء محفوظة؛ السجل §§11–13 يؤكد patch39 وتفقد عقده حياً، لكن لم تكن هناك نقطة سائق صالحة أثناء التفقد. ظهور خيارات الخرائط الخارجية تحقق لاحقاً في §20. | تتبع الحالة والخريطة مستقلان عن الطرق الداخلية **المعطّلة بقرار**؛ لا ETA ملاحة مضمون ولا روابط تتبع عامة للضيف. GPS الحقيقي وخصوصية حساب الزبون والعودة من تطبيق الخرائط ما زالت تحتاج قبولاً حياً. |
| توصيل طلبات التاجر الواردة من واتساب/الهاتف | **غير موجود** كمنتج مستقل | لا نموذج إنشاء توصيل خارجي في `merchant.html` ولا RPC لهذا الفعل في core. `placeOrder` عميل مسجّل + عناصر قائمة؛ `shareStore` يشارك رابط القائمة فقط. ليست مشاركة رابط واتساب استيراداً لطلب واتساب. | بحث في صفحات التطبيقات/core وSQL المحفوظة عن مسار طلب التاجر/طلب خارجي؛ لا عقد متكامل. | يحتاج إنشاء شحنة باسم التاجر، بيانات مستلم ومصدر الطلب، صلاحيات، توزيع سائق، مسؤولية قيمة البضاعة/التحصيل والتسوية والإلغاء. يُحسم سعر خدمة التوصيل وهل تشمل عمولة منصة قبل التنفيذ. تكامل WhatsApp API ليس شرطاً للإدخال اليدوي، لكنه تكليف منفصل إن طُلب. |
| حسابات الشركات | **غير موجود** كحسابات شراء مؤسسية | الأدوار الحالية customer/merchant/driver/admin؛ `staff_members` في [schema_patch26.sql](../../sql/schema_patch26.sql) موظفو إدارة المنصة وصلاحياتهم؛ `brands` في [schema_patch27.sql](../../sql/schema_patch27.sql) علامات التاجر وفروعه. لا يمثل أي منهما شركة مشترية بموظفيها. | قراءة نموذج الأدوار والجداول وواجهات الإدارة؛ لا company budget/cost centre/invoice/approval flow في المصدر. | يحتاج شركة وعضويات وصلاحيات وحدود إنفاق وموافقات وفوترة وتسوية. قرار من يدفع ومواعيد السداد/الائتمان ضروري؛ لا تعاد تسمية staff أو brands بوصفهما هذا المنتج. |
| طلبات الموظفين على الشركة | **موجود جزئياً** | الموجود القابل لإعادة الاستخدام هو المجموعة المكتبية أعلاه وأسماء أصحاب الأطباق. لا ميزانية لكل موظف/دعم وجبات/موافقة مدير/تحميل فاتورة على الشركة. | E3 يثبت المجموعة ذات فاتورة مضيف واحدة، لا نظام مصروفات شركة. | إعادة استخدام المجموعة عند اختيار النموذج المناسب؛ بقية السياسات وتوزيع الدفع والفوترة تحتاج خادماً وتسعيراً/قرار تشغيل، ولا يُستنتج فصل الدفعات من أسماء الأعضاء. |
| المخزون والإتاحة | **موجود جزئياً** | `merchant.html`: `vMenu`, `tog`, `updO`؛ core: `shapeItem`, `updateItem`, `updateOption`؛ المتاح available/approved وStop-list وإيقاف خيارات إلزامية فارغة. | E1/E2: تعديل الإتاحة/الخيارات وقراءة الكتالوج والصلاحيات موثقة. لا مخزون وحدات أو حجز كمية أو موردين/مستودعات أو SKU/باركود/أوزان في المسار الحالي. | لا تعيدوا بناء إتاحة المنتج. المخزون العددي يحتاج حجزاً/خصماً ذرياً عند الطلب والتحرير عند الإلغاء، وتحديد مصدر الحقيقة ووحدات البيع والمزامنة مع التاجر. |
| البدائل والنواقص | **موجود جزئياً** | `customer.html`: `optsCard`, `optExtra`, `cxCard`/اقتراحات بعد الرفض؛ `merchant.html`: `optChips`, `rjOpen`؛ core: `rejectOrder`؛ [schema_patch32.sql](../../sql/schema_patch32.sql) و[patch34](../../sql/schema_patch34.sql). يُحفظ تفضيل اتصل/استبدل/احذف، وسبب رفض نفاد المنتج. | E1، `CHANGES-v50.md` و`CHANGES-v52.md`: رغبات الزبون ورفض الطلب/اقتراح البدائل موجودة. التفضيل ليس تنفيذاً تلقائياً للاستبدال. | لا رحلة اختيار بديل من التاجر وموافقة الزبون وتعديل أسطر الطلب/فرق المبلغ أو إكمال جزء من الطلب مثبتة. تحتاج عقداً خادمياً وقرار من يوافق وكيف يُسوّى الفرق؛ لا تعديل صامت للسلة. |
| الاسترداد | **موجود جزئياً** كمنتج شامل؛ **مسار المحفظة منفذ** | core: `refundRoom`, `ticketSetStatus`, `orderWallet`؛ `admin.html`: الدعم وحل التذكرة؛ `customer.html`: `settleCard`؛ `schema_patch26.sql`: `ticket_set_status`, `ticket_refund_room`، وسجل `wallet_entries`. استرداد معتمد للتذكرة إلى المحفظة مع سقف وربط بالطلب ومنع تكرار؛ إرجاع النقاط/المحفظة عند الإلغاء في SQL. | E1/E2: العقد وقراءة الدفاتر ووجود RPCs موثق؛ لا إرجاع فعلي جديد. SQL المحفوظ أقدم من أي احتمال تعديل حي، فلا يحل محل تدقيق صلاحيات/تزامن قبل توسيع الماليات. | لا دليل على رد مصرفي/بوابة بطاقات أو رد نقدي تلقائي أو استرداد كل سطر ناقص تلقائياً. يلزم قرار قناة الاسترداد والرسوم والمخوّل والحدود؛ لا تفعّل v60/v61/patch38 المجمدة لهذا الغرض. |
| عروض التجار | **موجود ويعمل** | `merchant.html`: `saveDisc`, `saveCb`, `saveFd`، خصم المنتج؛ core: `setMyDiscount`, `setMyCashback`, `setMyFreeDelivery`؛ `admin.html`: `vLoyalty`, `vPromos`؛ core `saveHH`, `checkPromo`. خصومات منتج/متجر، حد توصيل مجاني، نقاط/كاشباك، happy hours ورموز ترويج. | E1/E2 و`CHANGES-v46/v50/v51.md`: أدلة حفظ محاكاة ومطابقة حسابية/SQL تاريخية؛ وجود patch29/32/33 موثق حياً. الإعدادات الفعلية قد تكون صفراً/مطفأة؛ هذا ليس عطلاً. | الصلاحيات والحد الأقصى للخصم من الإدارة قائم. لا تُغيّر قواعد من يتحمل الخصم/التوصيل أو قيمة النقاط؛ يلزم اعتماد أي حملة أو تكلفة جديدة بدلاً من افتراض أرقام المثال. |
| بانرات التجار والإعلانات الممولة | **موجود جزئياً** | `admin.html`: `vBanners`, `bannerSave`, `vBannerEdit`؛ core: `banners`, `addBanner/updateBanner/deleteBanner`؛ `customer.html`: `inB`, `heroH`, `bottomBn`, `ordersAd`, `bannerGo`. صورة/ترتيب/موضع/بداية ونهاية/تفعيل/رابط متجر أو فئة. الإدارة ذات content تنشئ؛ لا بوابة شراء إعلان للتاجر. | E1/E2: حفظ بانر/صور بمحاكاة + 9 بانرات نشطة في لقطة 24 أكتوبر وصلاحيات حية. لا دليل تمويل أو billing/ميزانية/مزاد/موازنة ظهور. لفظ الإعلان في الواجهة لا يثبت أنه مدفوع. | يمكن إعادة استخدام عرض/تحرير البانر. التمويل يحتاج معلناً وحملة وميزانية وحدوداً واستحقاقاً وفاتورة/دفعاً وموافقة محتوى؛ يلزم نموذج تسعير (حجز موضع/مدة أو غيره) قبل البرمجة. |
| تقارير الإعلانات الممولة | **غير موجود** | `bannerGo` ينفذ الانتقال ولا يسجل حدث إعلان؛ لا impression/click/conversion ledger ولا campaign/CTR/ROAS في العقود المحفوظة. `merchant.html:vStats` تقارير طلبات، وليست أداء إعلان. | بحث صفحات/core/SQL؛ لا أدوات تقرير أو عقد قياس إعلانات متكامل. لم يُستدل من غياب صفوف على فشل خدمة. | يحتاج تعريف الظهور والنقرة والتحويل والنسبة الزمنية، منع التكرار/التلاعب والخصوصية والربط بالحملة والطلب، ثم API وتقرير. لا تحوّل عدد الطلبات أو ضغطات الواجهة إلى عائد إعلاني دون إسناد موثوق. |
| تقارير التاجر الحالية (لإعادة الاستخدام) | **موجود ويعمل** بحدوده | `merchant.html`: `vStats`, `orderSheet`, `brSec`؛ core: `brandStats`؛ `schema_patch27.sql:brand_stats`. طلبات/مبيعات/صافي مسجل وعمولة كل طلب، رفض وإلغاء، وتجميع الفروع. | `CHANGES-v82-int.md` يسجل merchant_stats ناجحاً؛ E1 يفحص الظهور عبر الأدوار. `vStats` يحسب من الطلبات المحملة، core حد التاجر 200؛ ليس تقرير سنة شاملاً مضموناً مهما كانت تسمية فترة العرض. | لا تعاد برمجة لوحة التقارير الأساسية. تقرير كامل غير محدود يحتاج استعلاماً/تجميعاً خادمياً مناسباً؛ لا تعرض صافي تقدير كتحويل مالي منفذ أو تقرير ممول. |
| روابط الطلب الخاصة بالتاجر | **موجود جزئياً** | `customer.html`: `shareStore`, `deepStore`, `openDeep` يفتح `customer.html?store=<UUID>` عبر مشاركة النظام/النسخ. المجموعة لها `?g=<UUID>`. الرابط يفتح قائمة التاجر ضمن تطبيق الزبون وبالدخول الحالي؛ ليس checkout ضيفاً أو رابط دفع خاصاً. | المصدر ونتائج branch/flow المحفوظة تثبت مسار الفتح؛ لا اختبار حي جديد لوصوله من واتساب أو Safari. | الرابط العادي لا يحتاج مشروعاً/خادماً جديداً. رابط مختصر باسم تاجر/نطاق خاص/QR وإسناد الحملات/سلة جاهزة يحتاج تعريفاً؛ لا تتعامل مع رابط المجموعة كرابط متجر دائم. |
| إدارة قائمة التاجر وصوره وفروعه | **موجود ويعمل** | `merchant.html`: `vMenu`, `openSheet/saveSheet`, `addO/updO`, `coverPick/logoPick`, `brSend/brSync`؛ core: `addItem/updateItem/deleteItem`, option APIs, `uploadImage`, `updateMyStore`, `branchCreate`, `brandSyncMenu`؛ `admin.html`: متجر/مالك/مراجعة. | E1 `catalog_check` محفوظ: منتج وصورة وأحجام/إضافات/غلاف/لوغو/بانر؛ E2 صلاحيات media وصور وRLS موجودة. الحفظ/الرفع الحقيقي لكل دور غير مثبت في الجولة المحفوظة. الصيدلية لها شرط الموافقة الحالي، لا تعمم قبول بقية الأصناف عليها. | الملكية/الموافقة/صلاحية stores وملف Storage الخاص بالمستخدم موجودة. مزامنة الفروع تنسخ القائمة وليست مخزوناً مشتركاً. استيراد Excel/POS أو محرر روابط/حملة جديد غير مثبت. راجع القيود التشغيلية قبل وعد التاجر برفع غير محدود. |

### الأدلة السابقة المعتمدة — لم تُعَد

- **E1:** هذا السجل §13 (Pre-owner audit): رحلة الزبون→التاجر→السائق→الزبون/الإدارة بمحاكاة Supabase في Chromium وWebKit، فحوص الكتالوج بمدخلات صور حقيقية وخزن معزول، cart/group وC1/C2. فقرة LIVE فيه تقول صراحة إن تسجيل الدخول والطلبات/الحفظ/الرفع الحي لم تكتمل؛ خطة اختبار لا تعني تنفيذه. [CHANGES-v82-int.md](../../CHANGES-v82-int.md) يسجل أيضاً نتائج catalog/flow/cart/merchant_stats السابقة.
- **E2:** [docs/live/T1-RESULT.md](../live/T1-RESULT.md)، [verify_catalog_2026-10-24.csv](../live/verify_catalog_2026-10-24.csv)، [verify_delivery_2026-10-24.csv](../live/verify_delivery_2026-10-24.csv): لقطة قراءة حية يوم 24 أكتوبر لوجود patch26/27/29/32/33/34، الجداول/RLS/RPCs وبكتات الصور. ليست شهادة نشر لكل SQL محفوظ أو كتابة ناجحة. الأعداد لقطة قديمة، لا أرقاماً حالية.
- **E3:** [CHANGES-v51.md](../../CHANGES-v51.md) مع [sql/test_patch33.sql](../../sql/test_patch33.sql) و[tools/cart_check.py](../../tools/cart_check.py): النتائج المسجلة SQL 35/35 وحالات الجدولة/المجموعة؛ لم نشغّلها. [CHANGES-v50.md](../../CHANGES-v50.md)، [CHANGES-v52.md](../../CHANGES-v52.md)، [CHANGES-v46.md](../../CHANGES-v46.md): رغبات الطلب/رفضه والعروض والنقاط، وتواريخ وحدود فحوصها.
- **E4:** [H-C1-C2-IMPLEMENTATION-2026-10-24.md](H-C1-C2-IMPLEMENTATION-2026-10-24.md)، [H-C-C-QA.json](H-C-C-QA.json) وهذا السجل §§11–13: العميل C1/C2 وRPC الموقع وقراءة عقده. التحديث الأحدث لنجاح خيارات الخرائط الخارجية في §20 ينسخ عبارة الانتظار القديمة اللاحقة في ملاحظة دمج R1؛ لا إعادة إصلاح CORS.

### المعطل بقرار مقابل غير المفحوص / غير الموجود

- **معطّل صراحةً:** الطرق الداخلية/B1/B2 (external=true/internal=false)، وماليات v60/v61/patch38. كذلك `admin.html:PARTNER_ON=false` يمنع إنشاء رابط بانر لشاشة شراكة v57 غير مفعّلة؛ patch36/Edge Function/Turnstile ليست حزمة تشغيل حالية. هذه شاشة استقطاب شريك، وليست إعلانات ممولة أو إدخال طلب توصيل.
- **غير مفحوص حياً:** حفظ/رفع كل دور، رحلة مجموعة حقيقية، جدولة فعلية مع تاجر، GPS الزبون وقيود عزله، استرداد حقيقي وصحة التقارير على حجم تاريخي كبير، وقبول iPhone. وجود ربط فعلي وفحص محاكاة لا يُبدل هذا الوصف إلى «معطّل» ولا «مقبول حياً».
- **غير موجود في المصدر المقروء:** نمط الاستلام الذاتي، طلبات توصيل خارج الماركت بليس من التاجر، حساب شراء مؤسسي وميزانيات الموظفين، مخزون عددي، رحلة موافقة بديل وتسوية فرق أسطر، شراء حملات وقياسها. لا توجد هنا ميزة مطلوبة لا تتجاوز «واجهة فقط» بكاملها؛ أجزاء واجهة مثل تفضيل الاستبدال/عرض البانر أُدرجت «جزئياً» مع حدودها بدلاً من مساواتها بالمنتج الكامل.

**التسليم الموحد للمصمم وكلود:** ابدؤوا من الموجود: مسار الطلب الواحد، المجموعة والجدولة، C1/C2، محرر قائمة التاجر وخياراته وصوره، البانرات والعروض وتقارير الطلبات. صمّموا فقط النواقص المذكورة بعد حسم عقد التشغيل والتكلفة والمسؤولية، ولا تعيدوا إنشاء ميزات موجودة. الجرد لا يعتمد تسعيراً أو سياسة أو حساباً جديداً، ولا يطلب تشغيل SQL أو نشر أو دمج. قبل أي تنفيذ لاحق تُطابق الفروق مع أحدث تكامل؛ وملحق الجرد يُلحق بالسجل الأحدث بدلاً من استبداله كله، خصوصاً إذا سبق دمج سجل إصلاح السحب §23.

## 30. 27 Oct 00:23 — marketplace expansion: integration requirements + open decisions (Claude; nothing implemented)
Basis: inventory §29. Spot-checked in source (226f05e): `place_order` requires address + coordinates (patch33 l.223);
no fulfilment / pickup mode anywhere; `scheduled_for` + `too_early` in patch33; `PARTNER_ON=false` in admin.html;
order lists limited per role (core `LIMITS`, customer 60). No SQL, server, account or app change made.

**Rules for any expansion package (designer + programmer)**
- Map every screen to a §29 row: «موجود» rows are bound to the existing handlers named there, never rebuilt. Design proposals
  for gaps may be shown at any time if clearly marked «proposal — not active»; an open decision blocks only ENABLING the
  related behaviour (owner, 27 Oct 00:30).
- Each server gap = its own proposed SQL file (next free number after the proposed patch 40 → patch 41+), RPC-only writes
  (security definer + role check), RLS on, no change to existing RPC signatures; read-only verify query first; owner applies.
- Anything that moves money (COD for merchants, substitutions with a price difference, refunds, paid ads) depends on the
  frozen finance work (patches 37 / 38, D-L1) — designed, not built, until finance is unfrozen.
- Paid services: none is enabled now (no payment gateway, SMS, WhatsApp Business API, paid ad server, own domain). This is the
  current state, not a permanent policy — any paid service is a separate owner decision (owner, 27 Oct 00:30).

| Gap (§29) | Integration requirement (technical) | Open decisions (owner) — blocking |
|---|---|---|
| Customer self-pickup | `orders.fulfilment` ('delivery' default / 'pickup'); `place_order` accepts no address only for pickup; delivery fee 0; never offered to drivers; merchant «выдан клиенту» step + customer handover code; cancel / no-show transition | Commission on pickup orders? Payment at the counter (cash) or prepaid only? No-show / cancellation rule and fee? Which categories (pharmacy?) and which stores opt in? |
| Merchant delivery requests (WhatsApp / phone orders) | New order source 'merchant_external': merchant creates a shipment (recipient name / phone / pin, items text, goods value, COD amount); same driver dispatch / tracking / chat; recipient tracking without an account needs the postponed share-link work | Price of the service and who pays it; COD collected by the courier for the merchant and its settlement cycle (finance — frozen); liability for goods; cancellation / failed-delivery fees; recipient consent to share their data |
| Corporate accounts + employee orders | `companies`, `company_members` (admin / approver / employee), period budgets, approval step, company invoice; reuse group orders (§29) for the office order | Prepaid company wallet or monthly invoice / credit? Per-employee limits and who approves? Invoice / tax document requirements? Do employees ever pay their own share? |
| Numeric stock | `items.stock_qty` (null = not tracked), atomic decrement inside `place_order`, release on cancel / reject, merchant edit UI | Which merchants / categories; units (piece / weight); oversell policy (block vs allow + substitute); source of truth if the merchant has a POS |
| Substitution approval | `order_item_changes` (merchant proposal → customer approve / decline with timeout), totals recomputed server-side, history kept | Default when the customer does not answer; maximum price increase; how the difference is paid / refunded (cash orders?) — finance |
| Refunds beyond wallet | Today only ticket → wallet (capped, de-duplicated). Partial line refunds would extend `ticket_refund_room` | Channels: wallet only (current) vs cash vs card — card impossible without a gateway; who may approve and up to what amount |
| Sponsored banners | `ad_campaigns` (store, placement, period, price, status, approval) linked to the existing `banners`; admin content role approves; merchant request screen | Pricing model (simplest at zero budget: fixed price per placement per day / week); payment (deduct from merchant balance = finance); placement / frequency rules; which categories may advertise |
| Ad reports | `ad_events` (impression / click, de-duplicated per user / session), conversion = order by the same user within N hours of a click; aggregates only to merchants | Definitions + attribution window N; retention period; merchants see aggregates only (recommended) |
| Merchant links / QR | Reuse `?store=` deep link; QR generated in the browser (free); optional `src` tag → needs `orders.source` to attribute | Own short domain or the current URL? Do merchants need campaign attribution now? |
| Full-period merchant reports | Server aggregation RPC instead of the loaded-orders limit | Scope only (periods / fields) — no policy decision |
| Multi-merchant cart | Not a §29 gap; would change `place_order`, dispatch and fees | Wanted at all? (recommend: not in this expansion) |

Suggested order once decided (least money / policy risk first): merchant links + QR → full-period reports → numeric stock
→ self-pickup → corporate (reusing group orders) → merchant delivery requests → substitutions / refunds / paid ads (after finance).
- 27 Oct 00:30 (owner): first limited scope after the full R1.1 package arrives — (1) tracking display with current data,
  (2) the existing group-order journey, (3) current merchant links + QR if possible without a domain or paid service.
  One work list (ChatGPT programmer / Claude) with existing files, handlers and acceptance criteria will follow the R1.1 review;
  financial / operational decisions kept separate. Drag + location fix stays with the ChatGPT programmer until delivered.

## 31. 27 Oct — repeated iPhone grip + customer location feedback (review fix only)

- Started from and matched latest `tech/v82-int` / owner-tested `226f05e0b3dd4be27f032ed10af6fc49a46b5330`. Separate branch `fix/driver-repeat-drag-location-20261027`. Kept c573842 root/body mission scroll lock; no parallel replacement of that fix. Scope: gesture lifecycle and customer location picker/send feedback only; no new layout, financial, server, SQL, account or permission rules.
- Evidence identification: IMG_5788(1).jpeg / IMG_5787(1).jpeg show the driver's arrow above Leaflet, `aReadyRecenter()` → `aMapRecenter()` in map-view.js. This re-frames the existing mission/driver+destination view; it sends NO chat location and requests no new GPS permission. With driver near Tashkent and destination near Dushanbe, fitting both points remains a wide view; that alone is not a failed share. IMG_5786(2).png shows the CUSTOMER pin beside «Отправить» in the courier chat: `sendLoc()` → `TLB.pickLocation()` → explicit pin confirmation → `TLB.chat(order,'client','LOC:…')`. Neither button was moved by this fix. The exact original on-device failure event was not captured; the unobserved live permissions/network condition is not guessed.
- Source-level reproducible gesture defect: old grip click handler allows `detail===0` to toggle even after a completed/cancelled drag. Explicit zero-detail compatibility-click regression on the exact 226f05e handler flips collapsed back to default. Old handler also leaves capture cleanup implicit and does not have a touch-specific terminal lifecycle. These are demonstrated code paths, not a claim that desktop automation reproduces Safari's complete event stream.
- `assets/driver-a/driver-a.js`: touchstart/move/end/cancel own a single touch identifier; ignore compatibility touch pointers, and use capture/release for non-touch pointers with failure cleanup. Release/cancel ends render deferral before snapping; pagehide/blur/hidden cancel safely. Tap/button/keyboard and completed vertical drag use the same existing aSnap/aJourneyToggle states. Suppress the follow-up click, including detail=0; suppression is held outside the bound node so a queued render replacing the grip cannot reset it. No gesture listeners on sheet content/map/confirmation. Existing thresholds (8 px axis, 36 px switch, vertical x1.3) and confirmation handler unchanged.
- Mode wording for designer coordination (PROPOSED, not applied): current label names the mode, button names the destination mode. Work retains the expanded secondary information; Map compacts it and exposes more Leaflet while retaining essential controls. User finds the distinction unclear. Consider action wording such as «Показать карту / Развернуть панель» with a short current-state explanation, without changing R1 composition; designer decision required. We kept «Карта/Работа», icon positions and amounts; no silent redesign or relabelling. The technical two-state destinations now match for button and drag.
- GitHub Pages comparison READ, not published: fetched actual `https://merapplications-sketch.github.io/Talabat-v3/customer.html` and `talabat-core.js` (HTTP200, Last-Modified 18 Oct). Pages HTML SHA256 `e599bf4403bd4c5e29a8b0120668e6964d97bf63c1bfe8f9bab25f0674f2d8ee`, core `77796be799c4677cfcc24c6e2c1104366bebae6db42dffc886f28d985cc6ae15`. Both differ from 226f05e integration files; Pages has no customer-c.js C1/C2 include. Its core equals the current main core at `148cfae50000e983af2221a96057c507edac6d69`; its HTML is NOT byte-identical to that main HTML, so no exact deployment commit is inferred. Both Pages and integration still say PGV customer-55: this stale label does not establish equivalence. Hashes/scripts and distinctions saved in repeat-location-20261027/pages-comparison.json. Both old/new sendLoc lacked response handling before this fix. Pages was not changed, and the branch fix does not update it automatically.
- `customer.html`: capture order ID at opening, prevent duplicate picker/send; visibly report loading/selecting/sending/sent/failure, and show success only after the existing chat reply. A slow reply shows unconfirmed, retaining the send lock until resolved so it is not automatically retried. Before sending, recheck the same page/order, driver presence, and existing preparing/ready/pickedup eligibility; navigation or status change may not send into another conversation. The original button location, role and status availability are unchanged.
- `talabat-core.js` shared file: only loadLeaflet/pickLocation feedback/lifecycle and RU/EN feedback strings changed. Optional picker hooks preserve old two-argument callers. Map-load failure/15 s deadline including an empty CDN script, geolocation wait/result/denied/unavailable/timeout, duplicate locate guard, close/late-response guard added. Automatic one-time location remains only when no starting point was passed; same highAccuracy/12 s native timeout/5 s maximumAge options; pin remains manually selectable and requires the existing explicit send. No live position sharing, watcher, permission widening or automatic send added. Core RPC signatures, chat transport/payload and access rules unchanged.
- Verification: 65 targeted assertions recorded, Chromium phone/touch simulation at widths360/390/430 and available heights after simulated 44+84 / 24+44 browser bars. Includes baseline zero-detail reversal, 27 repeated up/down touch cycles, partial release, touchcancel/restart, pagehide cleanup, capture failure, keyboard, identical button/drag layouts, deferred render + compatibility click, Leaflet pan, separate detail scroll and non-confirming partial horizontal swipe. Customer cases: blocked/empty map script, GPS waiting/denied/unavailable/timeout/success, hanging browser deadline, explicit confirmation, server pending/rejection/success, duplicate guard, close/late GPS and navigation/order/status guard. Source UI/core with isolated service/geolocation/tile doubles; NO real messages/accounts/GPS/database writes. Existing 226 R1 and 36 prior grip checks not repeated. WebKit unavailable due the known host shared-library limitation; no new install attempt or WebKit pass claimed. Real iPhone acceptance stays OPEN.
- Test artifacts: tools/driver_repeat_location_check.py (baseline pinned to 226f05e); repeat-location-20261027/{results.json,pages-comparison.json,driver-work.png,driver-map.png,customer-picker.png,customer-sent.png}. Driver and customer steps ran in separate continuations after a test harness expression accidentally returned a never-resolving chat stub; fixed the harness wrapper, not app logic, and did not rerun passed driver checks. 56 main checks + 6 additional deadline/empty-script checks + 3 deferred-render checks = 65 unique recorded assertions. Syntax/compilation and diff whitespace checks pass. Screenshots are actual source with isolated fixtures, not actual iPhone captures or demo assets copied to the app.
- Claude integration handoff: application diffs ONLY assets/driver-a/driver-a.js, customer.html, talabat-core.js. Merge narrow function changes against any newer Claude work, especially shared core/customer; preserve driver.html, map-view.js, waiting-map.js, route-layer.js, external navigation/CORS/config, due/cashBox/finance and source delivery/chat permission rules. Integrate and test driver and customer from the SAME pinned integration build; do not mix old Pages customer/core with the new driver. No main merge, deployment or server changes by this task. Owner acceptance: repeatedly drag both ways including interrupted/restarted touch with Safari bars shown/folded, use button alternate, verify map/detail/confirm independence; then customer pin wait/errors/confirmed chat and external return on real iPhone. Designer wording review and actual device acceptance remain pending.

## 32. 27 Oct 00:49 — grip + location fix f2f2999 integrated (merge onto a0c8077; separate from R1.1)
- Diff reviewed: `driver-a.js` aBindSheet (one touch identifier, pointer path only for non-touch, compatibility click
  suppressed after a gesture, cancel on pagehide / blur / hidden); `customer.html` sendLoc (order id captured, eligibility,
  loading / selecting / sending / sent / failed feedback, duplicate guard); `talabat-core.js` loadLeaflet(cb, fail) +
  pickLocation(cb, start, hooks) — hooks optional. C1 / C2, route-layer, map-view untouched. Only the log conflicted:
  both sections kept, the programmer's «29» renumbered 31.
- Integration checks only: driver_map_stability_check 18/0 (grip handler changed); courier_position_check OK (customer
  track view changed); NEW tools/address_picker_caller_check.py OK — the other, two-argument pickLocation caller
  (sheetHere «deliver to my location»): opens, GPS wait text, confirm → S.tmp point, cancel without a point, no errors.
  Programmer's 65 checks ran on f2f2999 — not repeated. WebKit not available here. iPhone acceptance (repeat drag,
  location share) open.

## 33. 27 Oct — R1.1 (Marketplace Phase 1) review + one work list (nothing implemented)
Package: TALABOT-Marketplace-Phase1-R1.1 (designer). Reviewed against this branch + §29; inventory not redone. R1.1 adds
no server fields; demo data, map-demo.svg, sample times / amounts stay in the package. Merchant external delivery,
company accounts / budgets and paid ads = proposals, deferred.

**Data sources confirmed in source (the «Claude to confirm» items of LINK-READINESS)**
- Order amount = `o.total` (orders.total, core shape), payment = `o.payment`; arrives with the order row — no per-order
  amount request exists. «Не удалось загрузить» therefore = orders refresh failing; core already counts it (secFail
  'orders', banner after 2 failures) but does not expose it to the view → small core helper (C-1).
- Status event time = `order_events` (kind = status, at), already loaded per order by `TLB.loadOrderExtra` /
  `TLB.events(id)`; table is created outside the repo — customer read access UNVERIFIED (errors are swallowed → empty).
  Read-only check needed (C-2). Other times available: createdAt, arrivedStoreAt, arrivedCustAt, doneAt, scheduledFor.
- Courier position time = `at` from `TLB.courierPosition` (C1, patch 39 live).
- Delay statement: NO source (no field, event kind or message type) → «Заказ задерживается» stays hidden; server gap.
- Help: `reportBtn` / `canReport` already allow a ticket during pending…pickedup and 48 h after; chat / call exist.
- Merchant links: customer `shareStore` + `deepStore` (`customer.html?store=<uuid>`) exist; merchant.html has no
  share / QR. QR possible without domain or paid service (client-side generator, pinned CDN).

**Work list (files are owned by one side at a time; ChatGPT programmer = views / CSS, Claude = core contracts, checks)**

| # | Owner | Files / existing handlers | Task | Acceptance |
|---|---|---|---|---|
| T1 | Programmer | customer.html `vTrack`, `orderSummary`, `reportBtn`; assets/customer-c (C1 / C2 placement only) | Order: summary (#id, store, address, `o.total`, `o.payment`) → Restaurant card → Courier card with C1 map inside (pickedup only) → contact / help. Short statuses from `o.status` + `o.driver` (Claude table, C-3). Keep composition / receipt, chat, call, cancel (pending), help. | No new field / enum; total 0 shows «0 TJS»; C1 request / stop policy unchanged; no fake point; widths 360/390/430; no JS errors |
| T2 | Programmer | same view, after C-1 / C-2 | «Статус заказа: hh:mm» from `TLB.statusAt`, «Геопозиция курьера: hh:mm» from C1 `at`; unknown → «время неизвестно»; stale note from `TLB.ordersHealth`; values kept | Never fetch time / phone clock; last values remain on failure; note disappears on recovery |
| C-1 | Claude | talabat-core.js (sections loop) | `TLB.ordersHealth()` → {failing, lastOkAt} from the existing orders section result | Simulated failure → failing, data unchanged; recovery → clear |
| C-2 | Claude | talabat-core.js `loadOrderExtra` / `events`; sql/verify_* (read-only) | `TLB.statusAt(id)` = latest event of the current status or null; read-only query for order_events customer RLS | Owner result recorded; null when unreadable; no new SQL write |
| C-3 | Claude | this log | Status mapping: pending «Ждём ресторан»; preparing / ready without driver «Ищем курьера»; with driver «Назначен» (+ «Готовится» / «Готов» from status); pickedup «Везёт заказ» | Programmer uses it verbatim; driver assignment never implies «ready» |
| T3 | Programmer | customer.html `vGroup`, `grp*`, `whenCard` / `slotsAll` / `whenSet` / `whenDay` | Restyle per GROUP-HANDLER-MAP.csv; host pays one bill + one delivery via `grpCheckout` → `vPay` | Every handler in the map still reachable (remove / leave / cancel / reopen); close / checkout host-only (server decides); `expires_at` shown from the group; scheduling limits = existing slots + server rejection |
| C-4 | Claude | tools (fixture) + live steps | Binding check of T3 (host vs member controls, checkout path) + 2-account live acceptance steps | Check passes on the programmer's commit; live round by owner |
| T4 | Programmer | merchant.html (store section) | «Ссылка на магазин» + QR + share / copy for the merchant's own store | Opens the customer app at the same host with `?store=<id>`; works offline-free except the QR library |
| C-5 | Claude | talabat-core.js | `TLB.storeLink(storeId)` (customer.html in the same folder as the current page) + QR library choice (pinned, free CDN) and a check decoding the QR back to the link | No domain / paid service; link equals the customer deep link |
| C-6 | Claude | — | Integrate each commit, affected checks, one driver + customer link per round | — |

Order: C-1, C-2, C-3, C-5 first (core only — no overlap) → T1 / T2 / T3 / T4 by the programmer on the resulting commit
→ C-4 / C-6. Claude does not edit customer.html / merchant.html views; the programmer does not edit core contracts.

**Server / data gaps (not in this scope)**: delay statement (needs a field or event + who sets it); order_events customer
read if C-2 shows it closed (then one read RPC proposal). **Decisions kept separate (§30)**: merchant external delivery,
company accounts / budgets, paid ads, refunds / substitutions — no activation.

## 34. 30 Oct — core contracts C-1 / C-2 / C-3 / C-5 delivered (base 25225b8; views untouched)
Only `talabat-core.js` changed (+ a check and a read-only query). Drag / location fix, C1 / C2, customer / merchant views,
server, accounts and finance unchanged.
- **C-1 `TLB.ordersHealth()`** → `{failing, failures, lastOkAt, lastFailAt}`. A failed orders refresh keeps the last loaded
  orders untouched (amount `o.total`, status, driver, payment); the flag flips and the page repaints once on failure and on
  recovery. The times are attempt times on this phone — never shown as an order time.
- **C-2 `TLB.statusAt(id)`** → `{status, at, source:'event'|'placed'|null, state:'ok'|'loading'|'unreadable'|'none'}`.
  `at` = latest `order_events` row whose kind = current status (server time); pending without its event = order placement
  (`createdAt`). Reads the order's events on first call and again only when the status changes (error retry after 30 s).
  No event → `at:null` (`none`); not readable → `unreadable`. Never the refresh time, the courier time or the phone clock.
  Live customer permission on `order_events` UNKNOWN → owner runs `sql/verify_order_events_readonly.sql` (read-only; part 1
  as postgres, part 2 impersonating the test customer). Query validated on a throw-away PostgreSQL 17 (both parts).
- **C-3 `TLB.trackStatus(o)`** → `{restaurant:{key,label}, courier:{key,label}|null, ended, stale}`; RU / EN keys jr* / jc*:
  pending «Ждёт подтверждения» / no courier card; preparing «Готовится», ready «Готов», pickedup «Передан курьеру»;
  courier «Ищем курьера» (no driver), «Назначен» (driver, before pickup), «Везёт заказ» (pickedup), «Доставил»; while the
  refresh fails «Назначен ранее» / «Нет обновления». Driver assigned never maps to «Готов». Also: ordersStale, statusAtL,
  courierAtL, timeUnknown labels. No delay label (no source).
- **C-5 `TLB.storeLink(storeId[, appUrl])`** → `<customer.html next to the current page>?store=<uuid>` or null; drops the
  page's query / hash / session data; optional app URL. **`TLB.qrSvg(text)`** → Promise<SVG>, qrcode-generator@1.4.4
  (MIT) from jsDelivr pinned with SRI sha384; loads on first use only.
- Check: NEW `tools/core_contracts_check.py` 25/25 (Chromium, repo fixture): health flip + kept values + recovery; status
  time = the event, re-read on change, none / unreadable without substitutes; mapping table; link without session data;
  QR decoded back with jsQR = the link; tampered library refused (SRI); the link opens that store and clears the id.
  Affected only: courier_position_check OK, address_picker_caller_check OK.


## 35. 30 Oct — T1–T4 R1.1 UI delivery, base a417443 (independent branch; no deployment)

Branch: `ui/phase1-t1-t4-20261030`, parent exactly `a417443fa7d29682114c7c9351538f467325b29e`.
Designer input received before editing: Library `TALABOT-Marketplace-Phase1-Design-R1.zip` version 2, containing `TALABOT-Marketplace-Phase1-R1.1`. Read `PHASE1-HANDOFF-AR.txt`, prototype source/screens and `GROUP-HANDLER-MAP.csv`. Designer fixtures/map/amounts/times were not copied into the app.

- T1: order summary now shows the actual order id/store/address/`o.total`/payment; zero remains `0 TJS`. Independent Restaurant/Courier cards consume `TLB.trackStatus(o)` labels. Null courier hides that card. C1 is mounted inside the pickedup courier card. Existing composition/receipt is expandable; chat, call, location sharing, pending cancellation and help retained. Help arguments now safely encode real string order/ticket ids.
- T2: Restaurant time comes only from `TLB.statusAt(o.id).at`; C1 time only from the accepted point's `at`. Null uses `timeUnknown`. `ordersHealth().failing` adds a secondary warning while retaining the loaded order; recovery removes it. No generic update time or inferred delay message. C1 eligibility/request/reset/abort/polling/point validity and C2 logic are unchanged; only C1 text and mount placement changed.
- T3: group/participant cards and checkout dock use R1.1 spacing and surfaces. Actual `expires_at` is displayed; no name/deadline field added. Host close/reopen/cancel/checkout, member leave, and open-group own/host removal all remain. Checkout still closes the actual group then uses existing `grpCheckout → vPay`; no new billing path. Existing schedule slots/45-minute–3-day limits/15-minute steps and server rejection are unchanged; day/time are labelled native selects, now/later are keyboard-accessible buttons.
- T4: merchant Store section shows `TLB.storeLink(s.id)` (one argument), `TLB.qrSvg(link)`, native share and clipboard actions. Success only after resolved API calls; cancellation/denial/unsupported clipboard/failure are explicit. QR failure leaves both link actions usable; per-store cache prevents another store's QR/feedback leaking into view. No session/query/hash from merchant page copied.

Files for Claude: `customer.html`, `merchant.html`, `assets/customer-c/customer-c.js`, `assets/customer-c/customer-c.css`; targeted runner `tools/phase1_t1_t4_check.cjs`; evidence directory `docs/driver-handoff/phase1-t1-t4-20261030/`; this existing record appended only. Customer files are shared integration surfaces: merge the narrow tracking/group/schedule hunks and C1 draw/mount hunks, do not replace whole files. `talabat-core.js`, all driver files and the SQL file remain byte-identical to a417443. No server, permissions, accounts, finance, SQL writes, main merge or app deployment.

Validation: **119 affected checks passed**, real Chromium 133 headless with isolated service/share/clipboard/location replies and the real application/core/Leaflet. Initial 102 checks at 360/390/430, then 17 additional reduced-viewport/help/denial checks; successful unrelated checks were not rerun. Available app heights 652/716/804 simulate a 128px browser reservation (44+84), not measured Safari chrome/safe-area. Images at 390×716 are from the implementation, with synthetic test data only: tracking preparing, missing location, host/member group, schedule, merchant store link. `checks.json` records each assertion. WebKit unavailable: executable `/root/.cache/ms-playwright/webkit-2336/pw_run.sh` absent; standard Playwright browser download returned a truncated archive, so local Chromium was provisioned from the pinned npm package `@sparticuz/chromium@133.0.0`. This is neither Safari nor actual iPhone acceptance. No claim of live multi-account group, actual payment/scheduling, native share target or clipboard permission acceptance.

Read-only live check: verified project id `dzydscryrnahnneydnry` is Talabat, ACTIVE_HEALTHY, PostgreSQL 17.11. Reviewed the repository's `verify_order_events_readonly.sql`: both parts are SELECT only. Part 1 executed once via Supabase plugin; result saved in `order-events-part1.csv`: RLS=true, force RLS=false, SELECT policy `events_read` uses `can_see_order(order_id)`, authenticated SELECT grant present, event counts returned. These are administrative observations, **not customer-access proof**. Part 2 NOT executed: the plugin has no authenticated-customer role selector; SQL Editor in this browser redirects to sign-in. Do not substitute an admin result or spoof claims. Live customer read permission stays **unknown**; UI shows unknown event time if unreadable. Needed next: run Part 2 in SQL Editor as authenticated + existing test customer; `me` must identify the customer and `foreign_events_visible` must be zero, return CSV.

Parallel owner request: opened both exact 25225b8 links (driver/customer) in cloud Chromium; both reached the existing sign-in form. No authenticated app session or actual iPhone available, so no new live drag/location success is claimed. Historical successful checks remain valid evidence and were not rerun; physical iPhone acceptance is still open. URLs and exact limitations are saved in `live-readonly-status.json`.

Continuation: Claude integrates this single UI commit into tech/v82-int; no core contract changes needed. Verify Part 2 and authenticated live group/schedule/share/phone behavior, then owner iPhone acceptance. Branch-source preview is for review, not a deployed application update.

## 36. 30 Oct 22:54 — T1–T4 4db506d integrated (base a417443 = branch head → fast-forward)
- Review: views bind only the core contracts (trackStatus, statusAt, ordersHealth, storeLink, qrSvg); C1 keeps its
  request / stop logic, only its mount point (courier card) and its time line («Геопозиция курьера: hh:mm» / unknown)
  changed; composition moved into «Состав и чек»; chat, location pin, call, cancel (pending), help kept; group: existing
  grp* handlers, host-only close / checkout, «Приём до» from expires_at; schedule: same slots, labelled selects; merchant:
  link + QR + share / copy with failure states, QR failure leaves share / copy. No core, driver, server or finance change.
- Affected checks only: core_contracts_check OK (customer view changed), address_picker_caller_check OK. Programmer's 119
  Chromium checks ran on the identical tree — not repeated. WebKit / iPhone / live still open.
- order_events part 1 (owner, admin connection): RLS on; one SELECT policy `events_read` to public using
  can_see_order(order_id); authenticated holds table grants incl. INSERT / UPDATE / DELETE / TRUNCATE (no write policy →
  RLS blocks API writes; TRUNCATE is not reachable through the API — same note as profiles §8; no change proposed); kinds =
  every status + driver_assigned, at_store, at_customer. So C-2 has events for every status. Customer read is expected
  through can_see_order but NOT proven: part 2 (impersonating the test customer) still to run.

## 37. 31 Oct 18:00 — order_events customer read verified (C-2 permission note closed for this scope)
- Owner ran part 2 of `sql/verify_order_events_readonly.sql` in the SQL Editor impersonating the existing test customer
  (role authenticated; `me` = 7c5cf358-…-eed30ab18fb9, profile role customer). Result: `docs/live/verify_order_events_part2_2026-10-31.csv`.
- Read: the customer sees the events of his own orders (5 latest: 8 events each for delivered orders — every status +
  driver_assigned / at_store / at_customer; 4 for the rejected one). Isolation: `foreign_events_visible = 0`.
- Scope of the proof: this one test customer account, read only, 31 Oct. Matches the policy seen in part 1
  (`events_read` via can_see_order). C-2 `statusAt` therefore has a readable source for customers; no permission change,
  no re-run of checks. Still open: iPhone acceptance and the live journeys.

## 38. 31 Oct 18:30 — first iPhone journey (owner) + display fixes split (base f138973)
**Accepted — only what was tried:** one live order #9115 on iPhone Safari with the existing test accounts, placed
31 Oct 18:08 and delivered 18:14 (customer store page → order with wallet + cash → merchant → driver mission → delivered;
cashback 5.9 credited to the wallet 18:14). NOT closed by this round: group order, merchant link / QR, external navigation
(open + return), customer location pin, customer tracking screen states, repeated grip drag — each needs its own result.

**Claude — order 9115 reconciliation (source formulas vs the screens; no pricing / settlement change):**
- Items 180 + 80 + 15 + 20 = 295 = subtotal (merchant «Блюда»). Commission 5 % × 295 = 14.75. Cashback = round(paid ×
  store cashback_pct), paid = subtotal − discounts − promo − points = 295 → 5.9 ⇒ cashback_pct 2 (trg_loyalty, patch 33),
  paid by the restaurant. Merchant «Вам» 295 − 14.75 − 5.9 = 274.35 ✔.
- Customer wallet: −153.52 at 18:08 = wallet_used (place_order takes least(requested, balance, total)); driver «Получить
  от клиента» 161.48 = total − wallet_used (driver due()) ⇒ total = 315.00. total = subtotal − discounts − promo − points +
  delivery_fee + tip ⇒ fee + tip − discounts = 20; driver «Ваш заработок» 20 = driver_payout. Payment stays «cash» because
  the wallet did not cover the total — a mixed payment.
- Stored values to confirm: `sql/verify_order_9115_readonly.sql` (one read-only statement; validated on a throw-away
  PostgreSQL 17) → delivery_fee / tip / discounts / payout and the wallet rows.
- New core contract C-6 `TLB.paymentParts(o)` → {total, wallet, rest, method, restCash, mixed, points} from the stored values
  (rest = driver due() rule) + labels payWalletPart / payRestCash / payRestOther / payMixed. core_contracts_check +3 → OK.

**Claude — «Адрес ресторана не указан» (driver, Romant Restaurant):** code path is correct: stores are loaded with the
`address` column for every role; the store row is visible to the driver (its pin is on the map); the text is the existing
fallback when `stores.address` is empty. So the address is missing in the data — confirmed by the same query («store» rows).
Fix = data: the restaurant (merchant app, store settings) or the admin fills the address. No code change, no data change
by Claude.

**ChatGPT programmer — display only (designs, drag, tracking and money logic unchanged):** see the assignment in the
owner's chat of 31 Oct; covers top safe area on the store page, store-page loyalty text repeated, wallet rules repeated,
chat repetition, merchant order sheet («Блюда» = «Сумма по блюдам» shown twice; mixed payment line via C-6).


## 39. 31 Oct — mobile display corrections from babae790, no deployment

Branch `ui/mobile-polish-babae790-20261031`, exact parent `babae790464453f932c0a7585e68a1b6740dfc96`. Display scope only: `customer.html`, `merchant.html`, targeted test/evidence and this existing record. §37 customer order_events proof and §38 owner order #9115 acceptance are preserved; no old successful suite or live journey repeated.

**Cause and correction:** merchant order sheet's flex rows/nested `.items div` rules allowed long unbroken names/options/notes to exceed its width. With the original root clipping disabled as a diagnostic only, the 390px sheet had **1798px** intrinsic content width. After min-width/wrapping/grid fixes its content width is **390px**. No new root clip/hidden overflow or zoom restriction masks the defect. Sheet max height uses dvh with vh fallback and safe-area padding; its last row and store profile's last control remain reachable above the navigation. Customer cover actions/identity now use normal layout flow within the same cover, with safe-area padding and minimum height; exceptional titles wrap fully and increase height instead of colliding/clamping. Logo/assets, cover image treatment and approved colours are unchanged.

Restaurant reward line has one qualification note, without a repeated subtitle. Restaurant offer cards lose the old minimum height/padding and use compact wrapping, with smaller gaps before menu/search. At 390 with the same long-name fixture, menu navigation starts at 428px vs 444px before, while the full restaurant title is now readable (cover 230 vs 172px; normal-flow growth is intentional for long text). Offers stay horizontally browsable, no information deleted.

Wallet/Points are real top-level tabs. Wallet balance, all operations and cashback filter retained; Points has its own balance/vouchers/history. Next expiry is visible without expanding rules. Earning rate and conversion are not repeated in the rules. Buttons support arrow/Home/End and keep focus across asynchronous data renders. Original wallet/loyalty values/calculations and loaders are unchanged.

Chat: only adjacent entries with the same sender, body and finite timestamp are visually grouped, with count + expandable originals. Messages at different or unknown timestamps remain independent. Nothing is deleted or changed in the core; this is not claimed as a message-ID/server deduplication fix. Chat send/location/call contracts are unchanged.

Merchant order sheet: one undiscounted dishes-total line; when there is a discount, the original subtotal/discount/discounted-base breakdown remains. Payment presentation consumes **TLB.paymentParts(o)** only: wallet portion plus cash/remainder, mixed label. Does not subtract points again, recalculate payouts or change the existing commission/net expression. Before/after mixed-payment pictures use the same isolated fixture (not a new live #9115 check).

**Driver coordination request, not applied:** payment explanation is in `assets/driver-a/driver-a.js`, outside the allowed UI files. `mobile-polish-20261031/driver-payment-display-only-PROPOSED.patch` moves the existing `aCashDetail(task)` before `invoice(task)` in the Details modal only. Claude: please authorise/apply this one presentation hunk during integration, preserving `aCashDetail`, `cashBox`, `due`, invoice values, gestures, handlers and map lifecycle. Driver source stays byte-identical to base; no claim that the move was delivered or tested on iPhone.

Evidence: `mobile-polish-20261031/index.html` pairs 390px screenshots from the actual baseline and corrected app (restaurant, store, merchant profile/order/mixed payment, wallet, points, chat). Source fixtures are isolated service replies; no accounts, GPS, payment or SQL writes. `after-results.json`: **93 affected assertions**, Chromium 133 at 360×652 / 390×716 / 430×804 (128px outside-app browser reservation, simulated), intrinsic long-token reflow, 200% text stress, last-content access, tabs/keyboard, exact-repeat disclosure, C6 labels and protected-file byte checks. `before/after-intrinsic-stress.json` captures the 1798→390px result. WebKit executable unavailable; actual Safari chrome, keyboard and iPhone acceptance remain open.

Run instructions (test-only dependencies outside repo): install Playwright plus Chromium executable and Leaflet 1.9.4. `python tools/ui_hc_fixture.py /tmp/polish-fixture`; `node tools/mobile_polish_check.cjs <chrome> <deps-directory>`; `EXTRA=1 node tools/mobile_polish_check.cjs <chrome> <deps-directory>`; `STORE_ONLY=1 node tools/mobile_polish_check.cjs <chrome> <deps-directory>`. Baseline pictures were taken once from a detached worktree at babae790 with `MODE=before` and that worktree path as argument 4. No production dependency was added.

Handoff to Claude: merge these narrow UI hunks; core, driver, C1/C2, SQL, server config, accounts and money logic remain unchanged. Integrate the driver proposal only after scope permission. No main merge or app deployment.

## 39. 31 Oct 20:06 — mobile display fixes 6e27629 integrated + driver details order (owner-requested display patch)
- Correction to §38 (owner): the 20 TJS = total − items is arithmetic only; its split into delivery / tip / discounts stays
  OPEN until `sql/verify_order_9115_readonly.sql` returns. The driver payout of 20 does not prove the delivery fee.
- 6e27629 (base babae79 = branch head → fast-forward): store page safe area + intrinsic reflow (no zoom lock, no clipping),
  shorter store offers block, wallet / points tabs restored with balance, history and expiry, repeated chat entries grouped
  («Повторы: n», nothing dropped), merchant order sheet: one items row when there is no discount, payment block from
  C-6 paymentParts. Core, drag, tracking and money logic unchanged.
- Applied the programmer's display-only patch (owner request): `driver-a.js` details dialog shows aCashDetail before
  invoice — one line, order of two existing blocks only. NEW tools/driver_payment_order_check.py OK (breakdown before the
  invoice for a wallet + cash order, due 161.48 unchanged, grip / swipe present, no errors); screenshot
  docs/driver-handoff/mobile-polish-20261031/after-driver-details-390.png. core_contracts_check OK (customer view changed).
  Programmer's mobile checks ran on the identical tree — not repeated. iPhone / WebKit open.
- Observation for the designer (not changed): the driver details now name the wallet part three times (breakdown,
  invoice line, «Получите с клиента … из кошелька»).

## 40. 31 Oct 20:36 — second iPhone round (orders 9116): findings, Claude's limited fixes, split (base 3592de7)
**Owner results:** sizes improved. Grip DRAG FAILED on iPhone (tap on «Работа / Карта» only resizes) → real failure, to
the ChatGPT programmer. External maps opened from the restaurant stage (Yandex, Google seen); at the customer stage the
chooser showed «Дорожная навигация отключена» with no links; the chat point «Открыть на карте» opened Google directly.
Customer location pin: picker + GPS OK. Customer tracking: «Передан курьеру», «Везёт заказ», courier map 20:20 OK.

**Delivery fee audit (code; data query pending) — no pricing / finance change**
- Source: `delivery_calc` (sql/schema_patch18.sql, unchanged since) via `delivery_quote` (shown before ordering) and again
  inside `place_order` (patch 33: charged value; refuses `fee_changed` if it differs from the shown fee).
- Distance = `dist_km(store, customer pin)` — a straight line between two points (function defined outside the repo;
  definition requested in the query) × `delivery_road_factor` (app setting, default 1.3) = «≈ km по дороге» shown to the
  customer. It is an ESTIMATE, not a road route; no distance / routing service is called, so there is no service failure
  mode. Max `delivery_max_km` (15) → `too_far`.
- Fee: base = stores.fee_base (0 if fee_type free); fee_type «distance» adds ceil((km − delivery_free_km)/delivery_step_km)
  × delivery_step_price (platform settings; defaults 3 km / 0.5 km / 2 TJS). First-order free (free_first_delivery) and
  the restaurant threshold (free_delivery_min → fee_waived, paid by the restaurant). Courier payout = fee_full + tip.
- Findings: (1) stores.fee_per_km / fee_free_km are NOT used by this calculation (platform settings are). (2) A store
  without coordinates gets the base fee only and no distance limit. (3) Quote failure: the customer app refuses to place
  the order (no quote → error), the server recomputes anyway.
- 9116 from the screens: total 188 = 180 − 2 (points) + fee + tip ⇒ fee + tip = 10; payout 10. 9115: fee + tip = 20.
  Same restaurant — the split (base / extra / tip / waiver) and the km are in `sql/verify_delivery_fee_readonly.sql`
  (read-only, validated on a throw-away PostgreSQL 17); result to be recorded.

**Links audit:** server links (Edge Function) give the same coordinates to all three providers: Yandex `rtext=~lat,lng`,
Google `destination=lat,lng`, 2GIS `|lng,lat` (provider order); destination = restaurant pin until pickup, customer pin
after. Differences in the final point come from each app snapping the pin to a nearby address / entrance (Google «Nearby
Address», Yandex road entrance), not from TALABOT. Chat point was a forced Google link.

**Claude — limited fixes (this commit):**
- core `fmtMsg` + `TLB.openPoint(lat,lng)`: a shared point opens a choice of maps for exactly that point — in the driver app
  the same chooser (server links), in other apps a small sheet with the server links or, if unavailable, the coordinates to
  copy. No provider forced.
- route-layer: chooser shows «Проверяем навигацию…» while config / links load, an explicit failure + «Повторить» when they
  fail; «Дорожная навигация отключена» only when links really are empty. Chat point mode (`aNavigationOpenPoint`),
  returns to the chat on close; no internal-route offer for a chat point.
- driver.html map: the dashed straight line between the restaurant and customer pins removed (a straight line must not look
  like a road route); pins, own position and recenter unchanged.
- Checks: NEW tools/map_points_check.py OK (loading / failure / retry, chat point = exact coordinates, back to chat, no
  connector line, customer sheet without forced Google); navigation_attribution_check OK; driver_map_stability_check 18/0.
  Consultant's navigation_ui_check (Chromium): stops at «disabled -> tracking … прибытия недоступно» — the SAME failure on
  3592de7 before these changes (label text changed in 79af0bb); stale expectation, reported, not changed.

**Notifications (diagnosis, nothing changed):** messages arrive by realtime / polling only while the page is open and
visible: unread badge + `beep()` (Web Audio, needs one tap to unlock on iOS; the speaker icon = «sound not unlocked», not a
mute of messages). No Notification API, no service worker, no Web Push → nothing while Safari is in the background, while
the driver is in Google / Yandex Maps, or with the phone locked; the messages appear on return. System notifications would
need Web Push (iOS 16.4+ only for an app added to the Home Screen) + a sending server function — a separate decision.

**Address picker / 2GIS:** current picker = OSM tiles + pin + GPS (free). 2GIS MapGL / tiles: demo key one month with a
request limit; production cost per request (tariffs on each API page / api@2gis.com); vector tiles only through MapGL JS;
no activation. Free improvements possible without a provider: larger pin / labels, «my location» first, address search only
with a geocoder decision (OSM Nominatim policy: 1 request/s, no autocomplete; or the existing Geoapify account).

**Owner notes recorded:** store link / QR need a short explanation for the merchant; a raw.githack preview link is NOT
for final printing (QR must be printed from the published app address).

## 41. 31 Oct 20:48 — remaining audit items (proposals only; no pricing / finance / server change)
1. **Store without coordinates** → `sql/proposed/patch41_delivery_store_location.sql` (NOT applied): `delivery_calc` raises
   `store_location_missing` when the store has no lat / lng, so neither the shown fee (delivery_quote) nor the charged fee
   (place_order) exists and the order cannot be confirmed. Rest of the body identical to patch 18. Proven on a throw-away
   PostgreSQL 17 with the real patch 18 body: 4 sample pins give identical results before / after (10/1.3 km, 22/5.85,
   42/10.98, too_far); the store without coordinates went from «fee 10, km null» to the error. Read-only list of affected
   stores in the file header. Core already maps the error (`err_store_location_missing`, RU / EN); customer view to show it
   (programmer). Admin already warns «Для расчёта по расстоянию укажите точку ресторана» (aNoLocW) — not a block.
2. **fee_per_km / fee_free_km:** no editable field anywhere. Admin store form: the per-km input is no longer rendered; it shows
   the note «Цена за км задаётся в общих тарифах доставки (вкладка «Магазины»)» (aKmOld) and saves the stored value
   unchanged on edit (0 for a new store); fee_free_km is never shown or written by any app. Core only loads both columns.
   Nothing misleading to disable; proposal: drop them from the admin save payload later (pure clean-up, no price effect).
3. **Distance wording:** customer «≈ {km} км по дороге» (delivKm) and driver «{n} км до клиента» / «км до ресторана» present an
   estimate as a road distance → rename to «≈ {km} км (оценка расстояния)» / «≈ {n} км до клиента (оценка)» (programmer,
   texts only). Accuracy check: `tools/distance_compare.html` — store points (public) to sample points on 1–8 km rings,
   straight × factor vs road distance from the public OSRM demo server (testing only, 1 request/s, no customer points sent,
   points > 200 m from a road excluded); median road / straight, share of estimates off by > 20 %, CSV. Locally tested with
   a mocked router (16 pairs); live result needs the owner's browser (this workspace cannot reach routing hosts).
4. **External map destination:** sent coordinates identical (§40). Whether the app moves the final point is NOT verified:
   method = for one order, read the point each app shows at the end (Google «what's here» / Yandex long-press / 2GIS point
   card) and compare with the pin; cause stays open until then.
5. **Web Push proposal (not enabled; background message delivery is an operating requirement)**
   - iPhone: iOS / iPadOS 16.4+; only for the app added to the Home Screen (manifest `display: standalone`); permission asked
     from a tap inside the installed app; every push must show a notification (no silent pushes). Android Chrome: browser or
     installed. Each installed app (customer, driver) has its own subscription.
   - Cost: none for keys (VAPID pair generated once) or the Apple / Google push services; Supabase Edge Function calls and
     two small tables inside the current plan. No paid service.
   - Files: per app `manifest-customer.webmanifest`, `manifest-driver.webmanifest`, icons; one `sw.js` (push → show
     notification with tag `order-<id>`, click → open that order); core `TLB.push.enable() / disable() / state()`;
     an «Уведомления» control with explanation (Home Screen requirement on iPhone).
   - Server (proposed patch 42): `push_subscriptions(id, user_id, app, endpoint unique, p256dh, auth, created_at, last_ok_at)`
     RLS own rows; RPC `push_register / push_unregister` (auth user only, endpoint must be https of a push service);
     `push_sent(event_key, user_id) unique` for de-duplication; Edge Function `push` (VAPID secrets) called by database
     webhooks on `order_chat` insert and order status change; recipients = the other party of that order only (customer /
     assigned driver via the same rule as can_see_order), never the sender; payload = order number + short type («Новое
     сообщение по заказу #…»), no message text or coordinates; drop subscriptions answering 404 / 410; per-order rate limit.
   - Duplicates: one event key per chat row / status change → one push per user; tag per order replaces older ones on the
     lock screen; the in-app beep stays for the visible page.
   - Approval needed: patch 42, the function deploy, VAPID secrets, the Home Screen instruction for drivers.

## 42. 31 Oct 21:05 — live fee data: orders 9115 / 9116 reconciled (only this item closed)
Result: `docs/live/verify_delivery_fee_2026-10-31.csv`; live function texts saved in `docs/live/delivery_calc_live_2026-10-31.sql`.
- **9115:** items 295 + delivery 10 + tip 10 = total 315.00; wallet 153.52 + cash 161.48; driver payout 20 = fee 10 + tip 10;
  discount / promo / points / waiver 0. **9116:** items 180 − points 2.00 + delivery 10 = 188.00; tip 0; payout 10.
  Both: delivery_base 10, delivery_extra 0, delivery_km 0.47. The 9115 / 9116 amount split is CLOSED.
- **Tariff correction (to §40 / §41):** live platform setting `delivery_free_km` = **2.5** km (3 is only the fallback when the
  setting is missing); step 0.5 km, step price 2, max 15 km, road factor 1.3. Store Romant: fee_type distance, fee_base 10,
  free_delivery_min 350, free_first_delivery false. No price changed.
- **Distance:** live `dist_km` = haversine (straight line; 0.362 km for these pins, identical to the reference formula);
  0.362 × 1.3 = 0.47 = stored delivery_km < 2.5 → extra 0 → fee = base 10. Estimate, not a measured road distance.
- **Live delivery_calc = patch 18 body line for line** (30 / 30 body lines equal; only the header is printed differently by
  PostgreSQL). Patch 41 (proposed) differs from the live body by exactly the added guard line + its comment — nothing else.
- **Free delivery from 350 (free_delivery_min):** NOT in delivery_calc. In the repo it is applied in `place_order`
  (sql/schema_patch33.sql l.279–282: subtotal − discounts ≥ free_delivery_min → fee 0, fee_waived = fee, paid by the
  restaurant) and shown in the customer app (`calc()` → fw). Whether the LIVE place_order has the same lines is not read
  (read-only check: `select pg_get_functiondef('public.place_order'::regproc)` and look for free_delivery_min). For 9115
  (295) and 9116 (180) the subtotal is below 350 → no waiver, consistent with fee_waived 0.
- Still open (separate items): accuracy of the road estimate (tools/distance_compare.html), grip drag on iPhone,
  notifications / Web Push.

## 43. 31 Oct 21:34 — grip diagnostics link + live place_order check prepared
- `assets/driver-tech/grip-debug.js`, loaded by core only when the address has `?debug=grip`: passive capture listeners
  and a pointer-events:none overlay (touch / pointer / click counts, prevented touchmoves, grip touch-action, snap, sheet
  top, scrollY, visualViewport, lock class, last events). Observes only — drag result identical with and without it
  (Chromium touch simulation: default → collapsed both). Screenshot docs/driver-handoff/grip-debug-chromium-390.png.
  The programmer's debug item is covered by this; his drag fix stays his.
- This workspace cannot read the live database. `sql/verify_place_order_readonly.sql` (one read-only statement, validated
  locally with two overloads): one «definition i of N» row per place_order overload + every line with free_delivery_min /
  fee_waived / v_waived and its line number.
