# v44 — end-to-end order flow + layout clean-up

No SQL to run. No new features.

## Restaurant page (customer) — one vertical scroll, as the owner decided
- Removed the sticky horizontal section tabs and the "sections" sheet. The page is now: cover → name/rating → description → branches → delivery fee → offer cards → sections one under another (each with its title).
- Removed duplicate chips under the restaurant name: "Closed" (the red banner already says it), "−15%" and "First order free" (the offer cards already say it). One chip left: "Delivery: 10 TJS".

## Clean-up (duplicates / noise)
- Cart: the restaurant name under every dish (it is already in the cart header).
- Tracking: the green "Order placed, the restaurant received it" banner stayed on screen until delivery; now only while the order waits for the restaurant.
- Courier profile: the version was printed twice.
- Admin: the filler sentence under the title; the 4 KPI cards now only on the Orders overview (on every other tab they pushed the content one screen down).

## Placement like the big delivery apps
- Restaurant app: the 4 sections moved from pill tabs at the top to a bottom navigation bar (thumb reach, same as the customer and courier apps), with the new-orders badge.
- Restaurant app: language and Sign out moved into Profile (they were floating pills above the header). The "no restaurant linked" screen got its own Sign out button.
- Language pill: an app that hides it (customer, courier, restaurant) now keeps it hidden even when the data loads before the page finishes building (race in core).

## Bugs found by the simulation
- Restaurant app showed "15 min / 30 min / 45 min" in English inside the Russian app → "мин".

## New test: tools/flow_check.py
One shared in-memory database serves the 4 apps at once; every step clicks the real button:
customer orders (cash) → restaurant sets 15 min and accepts → courier starts shift, sees the offer, accepts → a 2nd courier no longer sees it → restaurant sees the courier's name, marks ready → courier picks up → courier delivers (cash dialog) → customer rates 5/5 → admin sees the order and its detail; plus customer cancels a pending order and restaurant rejects one. Every screen at every step is checked with the qa_all rules and screenshotted. Result: FLOW FAILS 0, 21 screens clean.
The status rules mirror the SQL (set_order_status patch 26, driver_accept patch 18). It is not the real Supabase (no RLS/triggers/realtime).
