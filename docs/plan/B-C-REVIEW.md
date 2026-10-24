# Batches B + C — prepared for review (24 Oct 2026). Nothing deployed, no SQL applied, no merge.

## B — street route, distance, estimated time, navigation
- Source: OpenRouteService Standard (free): 2 000 directions / day, 40 / minute, free key from an account
  (openrouteservice.org/plans). The public pages do not state the commercial terms of the Standard plan and ORS says it no
  longer gives free support to commercial users → **owner checks the terms shown at sign-up** (or asks enquiry@openrouteservice.org)
  before the key is used. Fallback (not wired): OSRM public demo — no key, best effort, may be withdrawn. GraphHopper free = non-commercial only (excluded).
- Key protection: `supabase/functions/route/` (Edge Function, free tier). Key only in the secret `ORS_KEY`; signed-in users only;
  allowed origins only; points validated; trips > 60 km straight refused; 12 requests / user / minute; 5-min cache.
  Local logic check `tools/route_function_check.mjs` 14/0 (fake provider).
- App: `TLB.route(from,to)` (core) → `assets/driver-tech/route-layer.js` on the driver mission map: current leg only
  (driver → restaurant, after pickup driver → order pin); asked on task / stage change, then at most every 120 s after ≥ 250 m;
  replaces the straight line; label «По дорогам: N км · ~M мин» (road-speed estimate, no traffic, no countdown).
  When the function is missing / fails: straight line + «не дорожный маршрут» stay (as today). Before deployment each
  task / stage makes one call that fails (404) — harmless.
- Navigation: «Навигатор» opens Google Maps directions to the restaurant point / the exact order pin (was a search link).
- Quota estimate: ~4 legs per order + refreshes (≤ 1 / 2 min while moving) ≈ 10–15 requests per delivery → ~130 deliveries / day
  inside 2 000. Customer-side routing is not added (it would double the use).
- Local: `tools/driver_route_check.py` 13/0.

## C — customer sees the courier of HIS order, only while out for delivery
- Live structure (read-only, 24 Oct): position stored on `profiles.lat/lng/loc_acc/loc_updated` by `driver_location`;
  `profiles` not in realtime; profiles policies not yet read → `sql/verify_tracking_readonly.sql` (read-only) reads the
  full policies, grants and function bodies. **If an existing path already gives this, it is reused and patch 39 is dropped.**
- Proposed `sql/proposed/patch39_order_courier_position.sql` (NOT applied): one security-definer read function — the
  order's customer only, status `pickedup` only, last position + its time only; no table / realtime / dispatch change.
- App: `TLB.courierPosition(orderId)` (core) → `{lat,lng,acc,at}` or null. Ends by itself at delivered / cancelled (the function
  returns nothing). UI shows the age «обновлено N мин назад»; no staleness number is assumed. Local `tools/courier_position_check.py` OK.
- Customer screen = UI pack C1 / C2 (v80 is the UI team's file).

## Kept for the next batch / postponed
- Next batch (D/E): gift delivery code + staff-approved exception; temporary recipient tracking link.
- Postponed: voice note, Web Push, automatic approach alert.

## Live read-only result 2 (24 Oct 15:40, `docs/live/verify_tracking_2026-10-24.csv`)
- `profiles` SELECT: own row or admin; staff with orders / finance read drivers. **No existing path lets a customer read the
  courier position** → patch 39 is needed (no reuse possible). Status `pickedup` and `orders.customer_id` confirmed.
- `driver_location` writes at most one point / 3 s for an approved, online driver; `driver_ping(false)` clears the position →
  patch 39 then returns nothing (shown as «unavailable», never an old point).
- `can_see_order`, chat insert (customer or driver, only with a courier and status preparing / ready / pickedup) and
  recipient read (staff perms + the order's customer and courier) confirmed — no change needed.
- Note: `profiles` has the default Supabase table grants for `authenticated` (incl. TRUNCATE); rows are protected by RLS and
  TRUNCATE is not reachable through the API. No action proposed.

## One approval — external steps (in this order)
1. ✔ done 15:40 — read-only result received; patch 39 confirmed necessary.
2. Owner creates the free ORS account (account.heigit.org), checks its terms, and sets the secrets `ORS_KEY` and
   `ALLOWED_ORIGINS=https://merapplications-sketch.github.io` in Supabase → Edge Functions → Secrets. Endpoint: api.heigit.org.
3. Deploy the Edge Function `route` (Supabase CLI or dashboard).
4. Apply patch 39 (step 1 showed no reusable path).
5. Merge `tech/v82-int` to main (T7) — separately approved.
