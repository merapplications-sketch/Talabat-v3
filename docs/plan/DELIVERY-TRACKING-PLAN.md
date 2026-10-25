# TALABOT — delivery & tracking improvements: plan (24 Oct 2026)

Latest planning delta: section 9 (25 Oct, multi-city/navigation/quota gaps; extends section 8). Earlier proposals remain historical; no routing activation is approved by this update.
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


## 9. 25 Oct — Completion of navigation evaluation: differences only

Baseline: `727835abfb3648063aef06f57d56930a5f536a85`, same repair branch
`fix/v82-pre-owner-audit-20261024`. Remote head checked before this update. Sections 1–8 remain historical evidence;
this section extends the recommendation without repeating the completed comparison or Dushanbe tests. No activation,
provider switch, touch/chat repair, live order, SQL, account, finance, dispatch, merge or deployment change.
Status: code findings and public-demo observations below are verified within their stated bounds. Architecture,
thresholds and implementation scope are PROPOSED, not approved or implemented.

### 9.1 Multi-city: map coverage is not operational service availability

TALABOT scope includes Dushanbe, Khujand and later cities. Do not encode one city as the allowed navigation area.
Source inspection found an actual Dushanbe bias, so a blanket claim that no city is hard-coded would be incorrect:

| Finding in this baseline | Meaning / future correction, not performed now |
|---|---|
| `driver.html`, `map(q)` appends ` Душанбе` to text-only Google Maps searches | Wrong-city risk for Khujand when coordinates are missing. Remove unconditional suffix in the future approved change; use the actual order/store address and its city, prefer validated coordinates. External navigation remains a separate action |
| `[38.5598,68.787]` in `talabat-core.js` location picker and generic map, `driver.html` mission initialization, `assets/driver-tech/waiting-map.js` CITY | Dushanbe default camera positions, not city boundaries. Use relevant confirmed order/address/store coordinates or authorized GPS first; configurable fallback must be clearly unconfirmed, never mistaken for GPS or silently accepted as an address |
| No `maxBounds` / `setMaxBounds` city rectangle in the inspected map/routing files; waiting-map stores filter checks active/valid coordinates | These components are not constrained to Dushanbe. This does not prove nationwide operational availability or correct cross-city dispatch |
| Route proxy `LIMITS.maxStraightKm = 60` | Pairwise straight-distance request guard, not a radius centered on Dushanbe. A long intercity request can be rejected by TALABOT even if provider data exists. Keep guard pending explicit decision |
| `delivery_calc`, `sql/schema_patch18.sql`, still called by later order patches | Delivery eligibility uses distance from the selected store and configured `delivery_max_km` (source fallback 15), with existing road-factor estimate. Global settings, not a demonstrated city polygon. This is source evidence, not verification of deployed DB values |

No city-specific `city_id`/service-zone policy was established in the inspected source. Claude must reconcile actual
store coverage, current dispatch/eligibility and deployed configuration before enabling a new operating city; do not
invent zones, change distance/price equations, enable intercity orders or run old SQL. Asia/Dushanbe is a timezone,
shared by Khujand, not a map boundary. Coverage of map tiles, geocoding and roads must each be assessed independently.
A city can have a visible map and routable roads while remaining outside approved operating service areas.

### 9.2 Khujand: additional public address and route samples

Observed 25 Oct 2026 through Geoapify's official public Routing Playground [K1], using its visible autocomplete and
Generate response; no TALABOT connection, personal addresses, provider account or extracted key. Mode `drive`.
Coordinates below are public demo selections, latitude then longitude:

| Public address resolved by autocomplete | Selected coordinate | Limit |
|---|---|---|
| Panjshanbe bazaar, Шарқ, 735690 Khujand, Tajikistan | 40.2793400, 69.6332017 | Public market point; no premise/entrance verification |
| Ismoili Somoni Avenue, 735690 Khujand, Tajikistan | 40.2761447, 69.6345640 | Street representative point, NOT a verified house number. Several similarly named suggestions appeared |

| Directed sample | Response distance | Response time |
|---|---:|---:|
| Market → selected avenue point | 789 m | 62.335 s |
| Selected avenue point → market | 2,459 m | 182.413 s |

These are two directed routes between two nearby points, not city-wide testing. The difference may reflect road
connectivity/one-way routing; it was not independently driven or verified as legally/currently passable. Searching
`Khujand Fortress` did not yield a selectable suggestion in this demo attempt: an address-search limitation, not proof
that roads or the city are unsupported. No house-number, courtyard, new suburb, bridge, closure, traffic, scooter,
GPS-following, rerouting, ETA accuracy or actual iPhone navigation acceptance is established. No Dushanbe test repeated.
Future city acceptance needs owner-selected non-private representative entrances/streets and field validation; these
samples do not automatically open Khujand for operations. No Yandex city routing test was performed.

### 9.3 Yandex added to the options — evaluated, not connected

| Product / issue | Verified implication for current TALABOT PWA |
|---|---|
| JavaScript Maps API [Y1] | Browser embedding is technically supported with HTTPS SDK, key/referrer configuration and its own renderer; therefore a web/PWA screen is possible. This is not an implementation test in our installed PWA or a drop-in route adapter for the current Leaflet map |
| Free-use terms [Y2] | Prohibit real-time vehicle/mobile-employee monitoring and dispatch use; open-access, storage and attribution conditions also apply. Do not assume the free JS license authorizes TALABOT fleet navigation |
| HTTP Route Details pricing [Y3] | Published entry example: 250K requests/year, Basic $1,250/year, storage option $1,625/year; commercial terms and extras apply. Not a zero-budget authorization for this project |
| Native NaviKit [Y4] | Android/iOS navigation SDK; public page mentions Unlimited free up to 10 vehicles, distinct from the free map tier up to 25K MAU. This is not a PWA SDK entitlement; do not mix product limits or claim every Yandex navigation option is paid |

Conclusion: Yandex has navigation products, but a zero-cost, licensed fit for this existing fleet PWA is not established.
Its native small-fleet offer does not justify rebuilding the map or native app. Any reconsideration needs written
product-specific licensing/territory confirmation and a separate architecture decision. No account, key, SDK or contact
request created. Country/region marketing is not proof of house-level Khujand coverage. Existing external maps remain
optional links; they do not provide TALABOT internal navigation.

### 9.4 Geoapify evaluated as input to a navigator, not a complete navigator

API documentation [G1] supplies geometry, legs, distance/time and localized maneuver data (`ru` included). Its traffic
models are free-flow/approximated, not proof of live congestion. The following is engineering assessment of what TALABOT
must implement; public route success proves none of these movement behaviors:

| Required experience | Available input versus missing TALABOT work |
|---|---|
| Follow real movement inside design A | Existing browser GPS + map are reusable. Add explicit internal navigation/follow mode, heading where trustworthy, accuracy/freshness gates and manual pan/recenter; GPS updates alone need no routing call |
| Remaining road distance and ETA | Project reliable fixes onto the active route, track segment progress, compute remaining geometry and segment-time estimates locally. Reconcile noisy/reversing fixes; do not use straight distance or simply count down the original total time. Show calculation/fix timestamps and approximate ETA |
| Recalculate off-route | No continuously running Geoapify reroute session is provided by the routing response. TALABOT detects sustained deviation beyond GPS uncertainty, debounces/cools down, requests a new route through the same server adapter and budget, discards obsolete responses and prevents overlapping requests |
| Turn-by-turn | API provides instructions/indices; TALABOT needs step selection, distance-to-turn, maneuver UI and advance logic tied to actual progress. Preserve original route geometry and step mapping separately from simplified display points; current proxy's 400-point output discards steps. Text Russian guidance is feasible but not implemented/tested; voice prompts need their own browser/voice acceptance |
| Restaurant then customer pin | Navigation targets the restaurant until pickup, then the saved order pin; cancel previous-leg requests, reject late results by order/leg/version and clear obsolete ETA. Never infer a destination from a city center |
| Background, lock, offline | PWA cannot be promised continuous background/locked-screen GPS or offline routing. On return validate fresh fixes, route, order/leg and quota before resuming; do not replay a stale maneuver. Cached geometry is not an offline navigation guarantee |

Scope clarification versus section 8.4: the owner's current request asks us to assess complete foreground navigation,
including turn guidance, not merely a route line. Proposed implementation acceptance therefore includes textual
maneuvers, progress and off-route recalculation. Native/background guarantees and spoken guidance are separate scope
choices; none are silently approved. B1 prepared route display and B2 customer display remain held; B2 is not the
restaurant→customer driver leg. Keep the same map/design A/TLB.route boundary and existing tracking permissions.

### 9.5 Shared free allowance: all drivers, all cities, all keys in the account

Published Free allowance [G2]: 3,000 credits/day and 5 requests/s. Ordinary short two-point routing is normally one
credit; extra options can increase cost [G3]. Daily limits are soft, so provider behavior is not our zero-spend guard.

Sizing formula (not a forecast):
Daily credits = sum over ALL cities/drivers/orders of (initial leg requests + refresh + deviation + retry requests)
× actual request credit cost + other account API consumption. Include autocomplete requests, geocoding and any tile
usage if later put on that account. Do not reset the allowance per city/driver/key or open accounts to evade limits.
Local GPS tracking, progress calculations and advancing already-fetched instructions do not consume routing credits.
Only upstream calls count; allow conservatively for failed calls/retries instead of assuming they are free.

Illustration: 8 orders/driver/day; 20 total active navigation minutes/order; 2 initial leg calls + up to 10 refresh calls
(at 120 s) + 2 combined deviation/retry calls = 14 calls/order at 1 credit/call. These are assumptions, not existing
behavior or an approved refresh schedule. Local progress should avoid unnecessary timed requests.

| Combined fleet across cities | Orders/day | Routing credits/day | Against proposed 2,400 route allowance |
|---|---:|---:|---|
| 10 drivers total | 80 | 1,120 | Fits, subject to other assumptions |
| 20 drivers total, e.g. 10 Dushanbe + 10 Khujand | 160 | 2,240 | Only 160 routing credits remain |
| 30 drivers total across present/future cities | 240 | 3,360 | Exceeds even the whole 3,000 account allowance |

At 30-second refresh, the same assumptions become 44 calls/order: 80 orders cost 3,520 credits. At 14 credits/order,
2,400 supports at most 171 such orders/day, not an unlimited multi-city fleet. More expensive options reduce capacity.
Average request rate is concurrent drivers / refresh seconds, plus initial/deviation bursts; stagger and enforce a
shared limiter even if the average is low. Fleet size, daily orders and duration need actual operating estimates before
promising capacity. Existing per-user/per-instance rate limiter and five-minute cache are not a durable shared budget.

Proposed zero-spend envelope for approval: reserve 600/day for other usage and route cap 2,400/day (reduce routing if
other use is higher), shared account-level hard ceiling within 3,000; warning at 80% of route cap; aggregate <=4 upstream
requests/s with controlled bursts and bounded retries. All API access must be accounted for: an unmetered public key or
outside consumer defeats the cap. Maintain an atomic durable reservation ledger across server instances/restarts and
reconcile provider usage; establish the provider's actual daily reset window before implementation, not local midnight
by assumption. Claude must propose storage/permissions if needed; no SQL or permissions change is authorized here.

Required behavior at exhaustion/provider denial (proposal):
- Stop new routing calls globally, not per city. No automatic paid subscription, credit top-up, billed overage consent,
  provider switch, ORS fallback, retry loop or automatic dispatch/financial policy change.
- Keep map interaction/GPS and the last valid route with clear age/unavailable-state messaging. Estimated local progress
  is usable only against a still-relevant path and reliable fix; when off-route or switching legs, suppress stale guidance
  and ETA rather than present them as current. Never draw an invented street path.
- Offer external navigation explicitly. Order/chat/delivery-confirmation services remain available. No route quota
  failure is itself a reason to cancel an order or invent an amount.
- Resume gradually only after budget reset/authorized availability, rechecking current order/leg/location. No recovery
  request storm. Account/city usage monitoring must distinguish route, geocode and other credits.

### 9.6 One recommendation and approval gate

Retain the recommendation: Geoapify Free as the single proposed route upstream, through the existing server boundary,
with the existing map and design A, plus a TALABOT foreground navigation controller for progress, textual Russian turns
and budgeted off-route recalculation. This is feasible engineering scope, not a ready-made free navigation SDK or a
promise of unlimited fleet capacity, live traffic, reliable locked-screen navigation or all-city address quality.
ORS stays unchanged and suspended; no second provider is connected. No implementation authorized by this document.

| Next owner | Inputs / approval needed | Completion gate after authorization |
|---|---|---|
| Owner/coordinator | Approve the single upstream replacement proposal, foreground/text-turn scope and optional external navigation; accept finite capacity and degraded behavior; supply combined fleet/order estimates | Explicit decision recorded, not inferred from viewing samples |
| Claude | Above decision; location-data/privacy/attribution review; shared cap/reset/usage design; propose any necessary DB/permission delta separately | Normalized route+step contract, true timestamps, budget gate and error states; same business/financial/dispatch rules |
| ChatGPT visual programmer | Approved contract; existing A and accepted repairs | Internal mode, follow/pan, local remaining estimates, leg isolation and text maneuvers; remove unconditional Dushanbe address bias and unconfirmed defaults without redesign |
| Claude + visual programmer, then owner device check | One authorized provider; selected Khujand and other-city samples; existing test-account policy | Simulated movement/deviation/jitter/leg change/quota exhaustion and stale/offline recovery; affected tests only; field route/address checks and actual iPhone foreground/return acceptance remain open |

No extra design direction, scope-19-screen approval, production service-city activation or financial package decision is
implied. The above is a delta to the current plan, not a duplicate package or a completed live acceptance report.

Additional official sources checked 25 Oct (G references retained from section 8):
- [K1] https://apidocs.geoapify.com/playground/routing/ — two Khujand autocomplete selections and generated responses observed in browser UI.
- [Y1] https://yandex.com/maps-api/docs/js-api/common/connection/javascript.html
- [Y2] https://yandex.com/dev/commercial/doc/en/ and https://www.yandex.ru/legal/maps_api/en/
- [Y3] https://yandex.com/maps-api/products/router-api
- [Y4] https://yandex.com/maps-api/products/navikit
