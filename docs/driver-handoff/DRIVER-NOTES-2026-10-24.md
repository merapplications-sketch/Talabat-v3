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
