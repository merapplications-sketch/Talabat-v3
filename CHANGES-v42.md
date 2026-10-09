# v42 — cart + checkout polish (customer app, backlog item 1)

No SQL to run. No new pages. Only the customer app and `talabat-core.js` changed.

- **Cart is saved on the phone.** If the page reloads or iPhone closes the app, the cart comes back (same restaurant, items, options, note, tip, payment method). Saved per account, kept 24 hours, removed after the order is placed or the cart is emptied. A restaurant that was switched off is not restored.
- **Dishes that are no longer sold are flagged.** If a dish was deleted, switched off, or one of its chosen options no longer exists, the line is greyed with "Нет в наличии", a red box offers "Удалить недоступные", totals ignore those lines, and "Перейти к оплате" stays disabled until they are removed. Before, the cart showed "?" at 0 TJS and the order failed on the server with a vague error. If the server still refuses an item (it changed a second ago), the app refreshes the menu and returns to the cart.
- **No duplicate orders on bad internet.** Each checkout now sends a one-time key (`p_key`, supported by `place_order` since patch 17 but never sent by the app). If the connection drops after the order was created and the customer taps again, the server returns the same order instead of creating a second one. The key is also saved with the cart, so it still works after a reload.
- A network failure while placing the order now shows an error message (before: nothing happened).
- "Перейти к оплате" shows the amount; "Оформить заказ" shows "Отправляем заказ…" while sending.
- Core: `TLB.reload()` (re-reads data), `placeOrder({key})`.

## Tests
- New `tools/cart_check.py` (20 checks): save/restore after reload, 24 h expiry, unavailable dish/option/switched-off dish, totals, blocked checkout, dropped connection → same key on retry, success clears everything, next order gets a new key, "sending…" label.
- `tools/qa_all.py` gained 2 screens: cart with unavailable lines, payment page while sending.
