# v46 — loyalty points, cashback, happy hour (owner decisions of 10 Oct 2026)

**Needs `sql/schema_patch29.sql`** (run after patch 28).

| Owner decision | How it works |
|---|---|
| 10 points per 1 TJS | Given when the order is DELIVERED, on what the customer paid for the dishes (not delivery, not tip, not what points paid). |
| Cashback to the wallet | % set by the admin (default 0 = off), credited to the wallet as "Cashback for an order" on delivery. |
| Happy hour from the admin | Admin → Loyalty → Happy hours: name, all restaurants or one, days, from–to (Dushanbe time, can pass midnight), % , on/off. Each dish gets the best of restaurant / dish / happy-hour % (never added). The extra part is paid by the platform (`orders.hh_discount`): restaurant revenue and commission unchanged. Promo codes do not apply during it. |
| Points expire | N days per earning (default 90); the oldest are used first; the wallet page shows what expires next. |
| Minimum to use | Default 1000 points; below it the checkout shows how many are missing. |

Value (admin can change): **1000 points = 1 TJS** → 10 points per TJS gives back 1%.

## Customer app
- Checkout: "Pay with points" switch (all usable points, capped at the dishes), summary rows "Happy hour −25%" and "Points (12 500)", line "You will get N points · cashback X TJS".
- Wallet: points card (balance, ≈ TJS, what expires and when, the rules) + points history; wallet history shows cashback.
- Home: dark "happy hour" strip (best running one, "until 15:00"); prices and badges everywhere include the happy hour; refreshed every minute.
- Receipts: happy hour, points used, points earned + cashback.
- Fixed while testing: discounts were rounded with floating point (18.9×3×15% = 8.5049… → 8.50 instead of 8.51), so the app could show 1 diram different from the database → the wallet / points amount was refused. Now rounded exactly like PostgreSQL.

## Admin
- New tab "Loyalty": the 5 numbers with a live example, happy hours list (running now / off), add / edit / turn off / delete.
- Order detail: happy-hour and points rows marked "platform", points + cashback given.

## Tests
- `sql/test_patch29.sql` (self-contained, empty PostgreSQL 16): 40/40 — settings + permissions, totals unchanged without happy hour, points earned / once / expiry, cashback once, spending FIFO, wrong amount refused, cancelled order returns points once, happy hour days / hours / one restaurant / past midnight / switched off, platform pays the extra, promo refused during it, nobody can write points or happy hours.
- `tools/loyalty_parity.py`: 300 random carts (prices with cents, store/dish discounts, happy hour, balances around the minimum, odd point rates) — the customer app's bill = place_order's bill in PostgreSQL: 0 differences (it found the rounding bug above first).
- qa_all (with loyalty data + admin editor screen) 0 issues; flow, cart, smoke, header, overflow, sheet, branch checks 0.
- security-check.html: 3 new rows (customer cannot add points, create a happy hour or change the settings).
