# TALABOT — delivery & tracking improvements: plan (24 Oct 2026)

Latest planning delta: section 8 (25 Oct, internal navigation/provider review). Earlier proposals remain historical; no routing activation is approved by this update.
Matched once against `tech/v82-int` (code + repo SQL patches 17–34). Improve and connect what exists; no rebuild.
No new proximity, settlement or permission policy is assumed. Budget 0; same Supabase project, accounts, free services.

## 1. What exists (proven in the repo)
| # | Topic | Exists | Not there |
|---|---|---|---|
| 1 | Maps | Leaflet + OSM in driver (waiting + mission) and in pickers; straight line «не дорожный маршрут»; Google Maps links (driver 3, A 1, customer 2) | street route, road distance / ETA source; routing host not in CSP |
| 2 | Customer address | addresses table (patch 17 / 25), map point picker (`TLB.pickLocation`), entrance / floor / apartment, optional landmark note; `orders.lat/lng` copied to the order; driver reads `a.lat/a.lng` | an explicit «pin confirmed» check before ordering; proof that the saved point = the order point = the driver point (test to add) |
| 3 | Gift / recipient | patch 32: `is_gift`, table `order_recipient` (name + phone), readable only by customer, the order's courier and staff; driver card «Подарок — получатель» + call button | separate recipient role in chat; delivery code (none in repo); server-side code check; recorded exception |
| 4 | Contact | order chat (customer ↔ courier, drafts per order), tel: links, recipient call in gift orders | chat with a recipient (not an app user); verified routing of contact on gift orders (test) |
| 5 | Restaurant | accept / reject (reasons), prep time chips → `set_prep_time` RPC, status ready; customer sees stages | prep time edit after accept (check), ready time shown to customer / courier (check) |
| 6 | Customer tracking | stage list, courier name / chat on the order page; courier sends position (`driver_location` RPC every ≥ 8 s) | customer map, courier position read path (function / table not in repo SQL → read-only check), draggable card, «current order» shortcut, share link |
| 7 | Lock screen | PWA only | Live Activities / Dynamic Island need a native iOS app (ActivityKit + APNs) |
| 8 | Voice note / arrival alert | courier quick replies («Я подъезжаю…»), «Я на месте» message | voice note, automatic approach alert |

## 2. Batches (order)
| Batch | Content | Needs |
|---|---|---|
| A (now, no approval) | H9 hand-off; read-only query `sql/verify_delivery_readonly.sql`; tests: address point saved = order point = driver point; gift contact routing; chat / call on gift orders; merchant prep edit + ready shown | owner runs the query once |
| B (logic, no SQL) | route + distance + ETA in driver mission and customer tracking via a free routing source; «Навигатор» deep links (Google / Apple / Yandex) from the exact pin | decision Q1 (provider) |
| C (customer tracking) | customer map with courier position, draggable card (stage, courier, contact), current-order shortcut | query result (read path exists?) else SQL Q3; UI team screens |
| D (gift + code) | recipient separated from owner in the order view; 4-digit delivery code shared to the recipient by the owner; courier enters it; server check; recorded exception when impossible (reason + photo) — code = proof of handover, not of payment | Q4 + SQL patch (approval) |
| E (share link) | temporary tracking link for the recipient: stage + map only, no code, no account data, expires at delivery | Q5 + SQL / Edge Function (approval) |
| F (evaluations only) | lock screen: Live Activities impossible in PWA → alternative Web Push (iOS 16.4+, home-screen PWA, free VAPID, sender = Edge Function) — cost 0, needs SQL + function; voice note (MediaRecorder, Supabase Storage, 15 s, ≤ 300 KB, private bucket) ; approach alert (courier distance from the pin) | decisions Q6–Q8 |

## 3. Requirements for the designer / visual programmer (one list)
- H9 «Моё местоположение» on the mission screen → `aMapRecenter()` (ready).
- Batch B: route line style, distance / ETA line, «Навигатор» button (driver mission + customer).
- Batch C: customer tracking screen: map + draggable card (stage, courier, chat / call) + «current order» shortcut while browsing.
- Batch D: recipient block in checkout / order view; code display for the owner + «share with recipient»; courier code entry + exception path.
- Batch F (only if approved): voice note recorder in checkout; approach notice.
- Open from earlier: H4, H5, H7, H10, H11 (see DRIVER-NOTES).

## 4. Blocking questions (only these)
1. Q1 routing source (free): OSRM public demo (no key, no SLA, «not for production») or OpenRouteService (free key, 2 000 routes / day) or GraphHopper (free key, 500 / day)? Each must be added to CSP.
2. Q3 after the read-only query: may the customer read the courier position of HIS order (only while out for delivery)? If the read path is missing it is an SQL patch.
3. Q4 delivery code: for all orders or gifts only; what is the recorded exception (who may approve, photo required?).
4. Q5 share link: allowed at all; lifetime (until delivered?).
5. Q6 Web Push instead of lock-screen widgets: yes / no.
6. Q7 voice note: allowed; who may hear it (courier of the order only); kept how long.
7. Q8 approach alert: at what distance / time — no number is assumed.
Open from before: D-W1 (nearby), D-L1 (courier pays restaurant).

## 5. Live read-only result (owner, 24 Oct 14:48 — `docs/live/verify_delivery_2026-10-24.csv`)
Proven live (structure only):
- Saved addresses always have a pin: `addresses.lat/lng` NOT NULL; landmark = `addresses.note` (optional). Orders keep
  `orders.lat/lng` (nullable) + `orders.address` text. No separate landmark / entrance columns on the order (they are in the text).
- Courier position is stored on `profiles.lat/lng/loc_acc/loc_updated` by `driver_location` (security definer).
  `profiles` is NOT in the realtime publication; profiles read policies were not in this query → a customer read path is
  NOT proven (expect: missing).
- Gift: `orders.is_gift` + `order_recipient(order_id, name, phone)`, read only by admin / orders / support permission and
  the order's parties (policy text truncated in the export).
- Chat: `order_chat` read = `can_see_order(order_id)`; in realtime. Orders, order_events, order_offers in realtime.
- Restaurant: `set_prep_time(p_id, p_min)`, `set_order_status(p_id, p_to)`; `orders.prep_time` integer NOT NULL; no ready_at.
- No delivery-code column / function. Extensions pg_cron / pg_net / http / postgis: none installed.
Not proven: profiles policies (who can read a courier position), insert policy text of chat / recipient, Safari / iPhone,
live end-to-end order.

## 6. Batch A results (local + code reading; no change to v80 / driver A design)
- Pin chain: customer point = stored order point = courier point (flow_check, mock) ✔.
- Gift contact routing (code): chat and «Я на месте» go to the order owner; the recipient is reachable by phone only
  (driver.html + driver A note with call) ✔ — consistent with the review proposals below.
- Restaurant prep: set and edited while pending / preparing (15 / 30 / 45 min chips, `set_prep_time`) ✔.
  Gaps (UI, not logic): driver A mission does not show «Готовится, ~N мин» (driver.html had it) → H12;
  customer v80 does not show prep minutes (data `prepTime` is in the order) → H13. A «ready at» time needs an anchor
  (accept time) that is not stored as a column → only «~N мин» can be shown without SQL.

## 7. Proposals for review (24 Oct 14:48) — NOT started
| # | Proposal | Needs before start |
|---|---|---|
| P1 | Street routing: evaluate a free source (recommended OpenRouteService Standard key; OSRM public as fallback), check its terms and protect the key (Edge Function proxy) before adopting | owner approval of source + key handling |
| P2 | Customer tracks the courier of HIS order only while out for delivery; ends at delivered / cancelled | SQL read function (security definer, last position only) — approval |
| P3 | Delivery code for gifts first, shared by the owner with the recipient; server check; when the code is impossible an authorised staff member approves before the order closes, with reason + evidence; a call alone never confirms delivery | SQL patch + staff screen — approval |
| P4 | Temporary tracking link for the recipient: stage + map only, no code, no account data; ends at delivered / cancelled | SQL / Edge Function — approval |
| P5 | Postponed: voice note, Web Push, automatic approach alert; use the existing chat / call / «Я подъезжаю» meanwhile | — |

## 8. 25 Oct — Internal navigation: single scope reconciliation and provider recommendation (planning only)

Status: owner requirement recorded; recommendation below is NOT approval to integrate/activate a provider. Source reviewed:
`a03a9d7c5b71304d3a5d377c69f34dbe31a8b903`, same repair branch. Touch/map-space and chat repairs are accepted and retained;
no repeat implementation or re-test of them. No app/Edge Function/SQL/configuration/key/account/deployment changes in this delta.

### 8.1 Requirement and B1/B2 scope

The primary Navigation action must open navigation INSIDE TALABOT's existing driver A map: driver position, current
leg's destination, street route, remaining road distance and estimated remaining duration, updating as the driver moves.
Before pickup the destination is the restaurant's saved coordinates; after pickup it is the order's saved customer pin.
External navigation becomes a separately labelled optional action. Reuse existing Leaflet/map/gesture policy and services.

| Capability | What the saved source actually contains | Missing before this requirement is complete |
|---|---|---|
| In-app map and points | Working driver A map, live browser GPS marker, target markers, gestures/recenter; earlier repair preserved | Primary button currently remains an external Google Maps anchor; internal navigation mode/focus/follow control must be wired without recreating the map |
| B1 | `assets/driver-tech/route-layer.js` can draw an orange street polyline and road km / approximate minutes on the EXISTING mission map | Prepared, not live-verified; depends on the suspended route backend. B1 is a display integration, not a complete navigator |
| B2 | `UI-PACK` defines optional customer distance/time; it explicitly does not require a customer navigator | It is NOT the driver's next leg, turn guidance or a second routing engine. Keep B2 suspended; no duplicate customer route calls |
| Leg selection | `target(x)` picks restaurant coordinates before stage 3 and order lat/lng after pickup; request keys include task and stage | Validate missing coordinates without invented points; reset on actual leg/order change and expiry. Two delivery legs, not four; existing four stage keys may create extra requests |
| Prepared backend | `supabase/functions/route/` calls ORS driving-car through a server-held key, validates points, session/origin, timeouts; normalizes geometry/metres/seconds | Provider decision and authorized activation; existing auth only establishes a signed-in user, not an assigned active driver/order. Reuse existing permissions for cost/access checks; no new permission policy assumed |
| Updating while moving | Driver marker follows GPS independently; route requests occur on task/stage change, then only when BOTH >=120 s and >=250 m moved | No progress tracking along route, continuously updated remaining distance/ETA, off-route detection/recalculation or explicit follow mode. Current totals remain the last route calculation's totals |
| Freshness and failure | Local result has receipt time; server has a 5-minute per-instance cache. Failed refresh can retain an older valid route | Preserve true calculation time vs GPS time/cache receipt; clearly mark stale/offline/unavailable results. No false live ETA or silently fresh-looking cached route |
| Free-budget enforcement | 12 requests/user/minute and cache in per-instance Maps; geometry thinned to <=400 points | These are not a durable project-wide daily budget. Need shared quota accounting, single-flight/cancellation, backoff and a stop at the chosen free budget; do not assume this protection already exists |

The prepared B work is useful and reusable. Merely deploying its current function would display routes, but would not
finish the owner's internal navigation experience. Neither street distance nor ETA may change customer fees, driver
payouts, settlement calculations, dispatch or any frozen finance package.

### 8.2 Route display versus turn-by-turn guidance

1. Recommended first scope: internal visual route navigation. Keep the position marker moving using existing GPS;
   show the current street path, progress/remaining metres and an explicitly estimated duration. Refresh road calculation
   only when necessary within budget; a GPS update must not equal one paid/API routing request. Let pan suspend follow;
   use an explicit control to resume it. Preserve sheet scroll/drag and the independent horizontal delivery confirmation.
2. Turn-by-turn is a separate, unimplemented scope: extracting steps is only the start. It also needs manoeuvre indexing,
   GPS accuracy/heading/speed handling, advancing instructions, deviation/rerouting, Russian guidance/localisation and,
   if later requested, voice prompts. ORS returns steps when requested, but our proxy discards them and simplifies geometry;
   original step indices cannot safely be attached to that simplified line. No turn engine or navigation SDK is present.
3. This recommendation does not promise native/background/locked-screen navigation in the present web app. Foreground
   Safari/PWA location, denied permission, stale GPS, screen lock and resume need explicit device acceptance. No new native
   app, offline-map downloads, traffic feed or voice feature is approved here.

### 8.3 Verified provider review — 25 Oct (official sources and public demos)

**Recommendation: Geoapify Free Routing as the single proposed routing source for the visual internal scope, after owner
approval.** Keep Leaflet and the existing `TLB.route`/Edge Function boundary. If adopted, adapt/replace the suspended ORS
upstream inside the SAME function; do not add a second active routing provider, parallel SDK/map, automatic public-demo
fallback or new application. This is a proposed provider change, not completed or authorized implementation.

- Embedding: Geoapify documents drawing its GeoJSON routing result on Leaflet; the returned path is usable in our existing
  map. No iframe of a third-party navigator is required. Its response shape differs from ORS (MultiLineString and direct
  distance/time properties), so changing a URL/key alone would NOT make the current handler compatible. The browser can
  keep calling the same Supabase endpoint; no direct Geoapify client/CSP access is needed. Allowed preview origins still
  need explicit CORS configuration at the later authorized activation step. [G1]
- Commercial/free limits: official pricing permits commercial production with attribution; Free has 3,000 credits/day,
  up to 5 requests/second, no card required. A normal short two-point route uses 1 credit; advanced options/other APIs share
  the allowance. Required credits are not the number of GPS fixes. Free has no production SLA. [G2][G3]
- Terms caveat: the general terms still describe production limitations and reserve suspension/possible overage charges.
  Pricing gives the explicit production permission. For a zero-spend configuration use Free only, no automatic paid upgrade,
  and an internal stop below the allowance; do not present the allowance as guaranteed unlimited service. [G2][G4]
- Location privacy: routing sends coordinates to a third party. Geoapify's policy describes request logging (normally <=24 h
  for successful calls). Future integration must minimize payload to coordinates/mode, keep customer/order identities out,
  keep provider credentials server-side and account for this processing in the app's location notice. No real people's
  locations were submitted for this research. [G5]
- Dushanbe coverage was tested on the provider's own unauthenticated Routing Playground, not TALABOT and not a newly wired
  provider. `mode=drive`, public landmarks selected through its visible address search:
  - Rudaki Park `(38.5755304,68.7816707)` -> Airport Terminal 1 `(38.5485034,68.8142833)`:
    road geometry + **5,227 m / 380.691 s** and street instructions returned.
  - Reverse direction: **7,192 m / 525.074 s** with road geometry/instructions returned.
  This is two real service coverage samples, not proof of every alley/entrance, current road closure, traffic or scooter
  legality/coverage. The times are service estimates, not measured journey times. Steps returned by the demo are not an
  installed turn-by-turn navigator in TALABOT. Reproduce in [G6] using those two landmark selections and Switch waypoints.

**Correction to the old ORS blocker:** commercial use is NOT still wholly unclear. An ORS team reply on 12 Oct 2026
explicitly permits commercial Standard use; current public HeiGIT Plans also shows Directions 2,000/day and 40/min. [O1][O2]
Its GeoJSON output can be displayed on the current map, with the result's CC-BY-SA attribution obligations. However the
current Terms prohibit transmitting personal data apart from account-management data. [O3] Our inference: live driver GPS
and identifiable delivery pins require written clarification; sending no name does not itself settle that issue. This is
not a legal finding that all coordinates are forbidden. Thus do not activate the existing ORS function on the strength of
commercial permission alone. ORS Dushanbe routing was not authenticated/live-tested here; its global coverage statement is
not used as a substitute for city acceptance. The reviewed Geoapify option avoids keeping this specific ORS question as the
sole route forward; it still requires normal privacy/terms acceptance before integration.

**Basemap is separate from routing:** keep the repaired Leaflet map and existing tiles during this decision. Standard OSM
tiles are best-effort, require attribution/referrer/cache compliance, and prohibit offline/prefetch/bulk downloading. They
are not an unlimited free fleet-hosting promise. If Geoapify tiles are later considered, they also consume shared credits;
that is a separate decision, not part of this provider recommendation. [M1]

Budget example, not approved capacity/pricing policy: at 20 simple routing calls per delivery, 3,000 credits allows at most
150 such deliveries before any other usage/reserve/retries. Recalculating each 8-second GPS send would consume 150 calls
in 20 minutes (about 20 deliveries/day before other use). Therefore reuse route geometry/progress locally and budget
recalculations; the current 120 s/250 m gate alone is not a finished navigation update policy or a hard zero-cost guard.

### 8.4 Added work and decision gate (nothing started)

| Order | Owner | Input / dependency | Delta and completion criterion |
|---|---|---|---|
| N0 — decision | Qahtan / coordinator | This review, Free terms and location processing; existing frozen scope | Confirm the single recommended source and visual-navigation scope. B1/B2 and route activation remain on hold until explicitly decided |
| N1 — route contract / budget | Claude | N0; current route function, existing Supabase project and app permissions | Adapt the one upstream, maintain normalized contract, true calculation timestamps, quota/error states and shared free-budget protection. No financial change. No SQL/permission mutation without separate proposed change/approval |
| N2 — internal action | ChatGPT visual programmer | N1 contract; existing driver A + preserved map fixes | Primary Navigation opens/focuses internal mode; explicit optional external directions. Reuse map; correct restaurant/customer leg switch; follow/pan/recenter, route progress and current remaining estimates; stale/GPS/offline states |
| N3 — affected acceptance | Claude + visual programmer; owner for physical iPhone | One approved active source, existing test accounts and authorized test order | Simulated movement + same-order late-response isolation, leg switch, deviation/retry/quota/GPS failures; then road samples across Dushanbe and physical Safari foreground/return test. Coverage samples above do not close this live gate |
| Separate, not included | Coordinator first | Additional explicit scope decision | Turn-by-turn text/voice/native-background navigation, if wanted later; no implementation implied by N0–N3 |

No code test reruns were necessary for this documentation-only update. Existing accepted repair source remains the parent
`a03a9d7...`; runtime files must be byte-identical across this planning commit. No provider account/key creation, emails,
secret reads/changes, function activation, SQL, app integration, merge or deployment performed.

Official sources / observation method (checked 25 Oct):
- [G1] Routing/Leaflet examples: https://apidocs.geoapify.com/docs/routing/#code-samples
- [G2] Free/commercial limits: https://www.geoapify.com/pricing/
- [G3] Routing credit calculation: https://apidocs.geoapify.com/docs/routing/#pricing
- [G4] Terms: https://www.geoapify.com/terms-and-conditions/
- [G5] Request-data handling: https://www.geoapify.com/privacy-policy/
- [G6] City samples: https://apidocs.geoapify.com/playground/routing/ (interactive DOM, visible response values; no account key extracted)
- [O1] ORS team reply, 12 Oct: https://ask.openrouteservice.org/t/free-plan-in-an-app-with-a-paid-tier-license-cc-by-sa-4-0-personal-data-and-attribution-questions/8079
- [O2] Current Plans: https://account.heigit.org/info/plans (read in browser; JavaScript page)
- [O3] Current Terms: https://account.heigit.org/info/tos (read in browser; JavaScript page)
- [O4] ORS route output: https://giscience.github.io/openrouteservice/v9.10.0/api-reference/endpoints/directions/requests-and-return-types
- [M1] Basemap policy: https://operations.osmfoundation.org/policies/tiles/
