# v51 — batch 1-b (free delivery threshold, scheduled orders, group/office orders) — owner answers of 10 Oct, 18:43

**Needs `sql/schema_patch33.sql`** (after 32). Branch stacked on `feature/batch1-v50` (merge v50 first).

## Points value (owner decision 10 Oct 19:21)
- Earn 10 points per 1 TJS, pay 1000 points = 1 TJS off → 1% back, paid by the restaurant where the points are used.
  Patch 33 changes the untouched v50 default (100) to 1000; a value the admin set himself stays.
- New per restaurant (Admin → Loyalty → Per restaurant): "Points per 1 TJS" (empty = general rule). The value of a point
  when paying stays one for the whole app, so a balance means the same in every restaurant. The per-restaurant panel is
  now a labelled 2×2 grid (min order, cashback, points per TJS, free delivery from).

## Free delivery above a restaurant's own threshold (default 0 = off)
- The restaurant sets it in its app (Profile → "Free delivery from, TJS"); the admin also has the field in
  Admin → Loyalty → Per restaurant. Rule: dishes after discounts ≥ threshold → delivery 0; the waived fee is paid by
  the restaurant (`orders.fee_waived`, taken from its payout in the restaurant app).
- Customer: progress bar in the cart "Add X TJS more for free delivery" (only when the threshold is > 0), offer chip on
  the restaurant page, crossed-out fee on the bill and the receipt.

## Scheduled orders
- Payment page → "When to deliver": As soon as possible / Schedule (day chips + 15-minute slots, from 45 min to 3 days).
- Server checks 40 min .. 3 days (`bad_time`). The restaurant can accept/prepare only 60 minutes before the time
  (`too_early`); its card shows the time and "Accept from HH:MM". Customer, courier and admin see the time.

## Group (office) order
- Cart → "Group order": a link (`customer.html?g=<id>`, unguessable id) to share; colleagues sign in, add their dishes
  ("Add to the group order"); each person's lines with names; host or owner can remove; 3 h validity; refresh every 5 s.
- Host: Check out (adding closes, can reopen) → one normal order; same dish+options = one line, the note keeps who
  ordered what ("Zarina ×2; Bahrom ×1 (no onions)"). Placed once only. Cancel for everybody.
- Tables are closed to direct reads; everything goes through RPCs (group_create/get/add/remove/set).

## Fixes found on the way
- **Restaurant rules were not readable by the apps**: since patch 17 the stores table is readable column by column, and
  the columns added by patches 27 and 32 (brand, points minimum, cashback) were never granted. Patch 33 grants exactly
  the columns that exist; core loads them separately (an older database simply lacks them) and falls back cleanly on
  "permission denied". Without this, running patch 27 would have stopped the apps loading stores.
- Cart button / cart bar showed the amount without the happy-hour part; line prices rounded per unit (67.52 instead of
  67.50). Both now follow the server rule.
- "Express" badge and "New" badge overlapped on the express rail.

## Tests
- `sql/test_patch33.sql` 35/35 (threshold incl. who pays, scheduled time limits, too_early, group create/join/close/place
  once, privacy, column grants, commission still private); 28: 15/15, 29: 40/40, 30: 20/20, 32: 25/25.
- `tools/loyalty_parity.py` 300 random bills incl. free-delivery thresholds (93 waived) — 0 differences.
- `tools/cart_check.py` (+8: schedule sent/cleared, too-close time refused, fee 0 above threshold, group checkout lines,
  notes, group id, own cart restored), `tools/flow_check.py` FLOW FAILS 0, `tools/qa_all.py` QA ISSUES 0
  (new screens: pay-sched, cart-fd, group host/member/closed, group cart/pay).
- security-check SC-51: restaurant rules readable, commission private, customer cannot set free delivery, group tables closed.
