# TALABOT — delivery & tracking improvements: plan (24 Oct 2026)
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
