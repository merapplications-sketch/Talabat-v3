# v52 — batch 2 (courier app + restaurant cancel reasons) — owner, 10 Oct 19:58

**Needs `sql/schema_patch34.sql`** (after 33). Branch stacked on `feature/batch1b-v51`.

## Courier
- Active order = full-screen map (restaurant, customer, courier position, dashed route) with a bottom sheet
  (tap the handle to expand; pin button re-centres). Leaflet + OpenStreetMap, loaded once; works without the map offline.
- 4 swipe steps (a half swipe does nothing): «На месте в ресторане» → «Заказ забран» (locked until the restaurant presses
  ready, server rule unchanged) → «На месте у клиента» (also sends the customer "I am here") → «Заказ доставлен».
- Distance and money on the sheet and the offer: km to the next stop, km restaurant → customer, delivery fee + tip.
- Cash box: "Take in cash X" with the order amount, points and wallet shown apart.
- "Leave at the door": the delivery cannot be closed without a photo (camera). Photos go to a PRIVATE bucket `proofs`
  (<courier>/<order>/…jpg); only that courier, the customer of the order and staff can open them (short-lived link).
- Cancel alarm: if the restaurant/admin cancels the order the courier has, a loud ring + full-screen notice with the
  reason until he taps OK. Screen stays awake during the order (wake lock); live updates via the existing websocket.

## Restaurant cancel reasons
- "Reject" (new orders) and "Cancel order" (while preparing) open a sheet: out of stock / too busy / closing / other
  (+ message; required for "other"). Not possible once the order is ready (the courier may be on the way).
- Customer: instant notice anywhere in the app, and on the order page an apology card with the reason and the note;
  wallet money and points come back automatically (existing triggers). For "out of stock": similar dishes and
  similar restaurants of the same category that are open now.
- Admin order detail: reason, courier arrival times, door photo button. Restaurant: "courier is at the restaurant" chip.

## Tests
- `sql/test_patch34.sql` 27/27 (arrivals, idempotent, pick-up only after ready, photo required + folder check,
  storage policies: upload only by that courier for that order, read by its customer/courier only, private bucket;
  reasons, note for "other", also while preparing, not after ready; one deliver_order); 28–33 all pass.
- New `tools/courier_check.py` (real swipe gestures, photo upload path, cash breakdown, cancel alarm) 0 fails;
  `tools/flow_check.py` now swipes all 4 steps and cancels with a reason (FLOW FAILS 0); qa_all 0 issues incl. new
  screens (steps, photo dialog, cancel alert, reject sheet, rejected order, notice); cart/smoke/hdr/overflow/sheet/branch OK.
- security-check SC-52: patch 34 installed, customer cannot cancel as the restaurant / mark arrivals / upload photos.
