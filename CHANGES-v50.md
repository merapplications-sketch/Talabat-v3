# v50 — batch 1 (customer home, loyalty vouchers, order wishes) — owner spec of 10 Oct, 18:00

**Needs `sql/schema_patch32.sql`** (after 31). Open questions sent to the owner (not built yet): who funds points
(redeeming restaurant vs a platform fund), push notification for the abandoned cart, free-delivery threshold value,
scheduled + corporate orders as batch 1-b.

## Loyalty (patch 32 + apps)
- 1000 points = 10 TJS (the old default 1000 = 1 TJS is updated only if never changed), used ONLY as whole vouchers,
  only when the dishes reach the minimum order (default 30 TJS, per restaurant in Admin → Loyalty → Per restaurant).
- Earning rounded UP for the customer (12.35 TJS → 124 points). +10 points for rating an order (once).
- Cashback: each restaurant sets its own % in its app (paid by it, taken from its payout); the app-wide % stays 0.
- Checkout: points switch OFF by default, shown when the customer has ≥ 1000 points; "N more points to a 10 TJS
  voucher" nudge; bright "You will get N points" pill; same pill on the restaurant page.
- Confetti + congratulations when a new voucher is reached (once).

## Home, in the owner's order
Sticky search (the address row scrolls away) with rotating examples + cart shortcut · 3×3 categories incl. "Offers" ·
top banners · Happy-hour rail with live countdown · mid-page loyalty card (points, progress bar, vouchers) ·
1-click re-order rail · Fast & nearby (⚡ Express = real average preparation ≤ 15 min over 30 days, from order events) ·
Best sellers (dishes, 🔥 Hit, quick +) · existing sections · in-app "dishes left in the cart" reminder after 15 min.
Last payment method remembered.

## Order wishes (checkout → restaurant, courier, admin)
If a dish is missing (call me / replace / remove the rest), Leave at the door, Gift (recipient name + phone; only the
customer, the courier of that order and staff can read it). Restaurant card shows chips; courier sees the recipient with
a call button and a "leave at the door" note (photo proof comes in batch 2).

## Tests
- `sql/test_patch32.sql` 25/25 (vouchers, minimum order per restaurant, rounding up, rating reward once, restaurant
  cashback, wishes + recipient privacy, best dishes, preparation speed); 28: 15/15, 29: 40/40, 30: 20/20.
- `tools/loyalty_parity.py` 300 random carts with vouchers (sizes 1000/500/1), minimums 0/30/80: app = database, 0 diffs.
- `tools/cart_check.py` +4 checks (wishes sent, points OFF by default, gift validation). qa_all 0 (with the new screens,
  raw-key check now also catches keys like "minU"), flow / smoke / header / overflow / sheet / branch 0.
