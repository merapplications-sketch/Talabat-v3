# v43 — Definition-of-Done audit (all 4 apps)

No SQL to run. No new pages or features: only fixes found by screenshotting every screen of every app (with data and with empty data).

## Call / map buttons — one compact style everywhere
- Driver: the wide outlined "Navigate / Call / Chat" buttons are now compact round icon buttons (42 px) on the right of the restaurant / customer row. Orange = route, green = call, grey = chat (with unread badge).
- Merchant: courier row = bike icon + courier name + round green call button.
- Customer: restaurant contacts (offer page) were underlined orange links → rows with icon + text + round route/call button. Saved address "Open on map" link → small pill. Courier card call button uses the same round style.
- Admin: 8 different 📞 / 🗺 emoji buttons → one compact pill component (`tel()`, `mapL()`), green for calls, grey for map, no emoji.

## Bugs found and fixed at the root
- Customer profile: the settings button showed an empty circle, and the menu "sections" button had no icon (icons `gear`/`menu` were never defined).
- Driver: "Preparing, ~ min" (no number) when the restaurant did not set a time → now "Preparing".
- Customer / merchant: when the courier's name is not loaded yet the card showed "?" and an empty name, or an empty blue box → now "Courier assigned" with a bike icon.
- Admin support: ticket reason showed the raw key `rs_late` (labels existed only in the customer app) → labels moved to the shared core.
- Merchant profile: category showed the raw value `rest` → "Restaurants".
- Merchant "Add branch": the phone field and the category dropdown were unstyled browser defaults → same field style as the others.
- Admin order cards: long status ("Ready for courier pickup") was squeezed into a round blob → order number + status on one line, restaurant name below.
- Versions showed v41 → v43 everywhere.

## Empty states — one component per app
- Customer: icon + title + hint on every list (cart, orders, wallet, addresses, support, favorites, offers, search, category, menu).
- Driver history, merchant (orders, filters, menu, search, analytics history, requests), admin (orders, stores — was blank, couriers, staff, banners, promo codes, ratings, logs, customers, tickets): icon + title instead of plain text cards.

## QA harness (tools/qa_all.py)
- New checks: icons that render nothing (EMPTY-ICON) and snake_case raw keys (RAWKEY rs_late …). Both verified to catch the old bugs on v42.
- New pass: every list screen with NO data (customer 10, merchant 5, driver 2, admin all tabs) at 360/390/430.
- Fixture fix: wallet entry kind `topup` does not exist in the database (only refund/spend/return/adjust).
