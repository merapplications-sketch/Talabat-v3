# v53 — new customer home screen (owner reference image + brief of 10 Oct 21:21)

No SQL. Branch stacked on `feature/batch2-v52`. Only `customer.html` (+ `assets/3d/`) changed.

## Layout, top to bottom (each section shows only real data; empty ones are hidden)
1. Orange header: delivery address (dominant), notifications (active orders + unread messages), cart with counter;
   search with a filter button (category, open now, free delivery, discount, rating 4.5+, sort). The search row stays on screen.
2. Categories 5 × 2 with 3D icons: Рестораны, Супермаркеты, Аптеки, Кондитерские, Цветы, Электроника, Товары для дома,
   Автотовары, Зоотовары, Все категории (sheet with all 12 incl. Красота, Подарки, Магазины).
3. Hero carousel (swipe, dots, auto-rotate 5 s, pauses after touch, off with reduced motion): admin banners first,
   then slides built from live offers — happy hour with its real countdown, biggest store discount, free delivery,
   and a neutral "Любимые блюда рядом" slide.
4. Two cards: groceries (green) and flowers (pink).  5. Your last order with one-tap repeat (prices re-checked).
6. Popular nearby (restaurants) · 7. Supermarkets nearby · 8. "Всё для дома" banner · 9. Pharmacies · 10. Flowers & gifts —
   one store card: photo, badge (discount / Express / New / closed), heart, rating with count, delivery time (only from
   measured preparation time + distance, otherwise distance or fee), description, benefit chip.
11. Best offers: Flash Sale = real happy hour with real end time (or the biggest discount, no timer); free delivery.
12. Top brands (only brands with branches on the platform). 13. Special occasions (cakes, gift sets, party goods).
14. Recommended: real best sellers, else dishes marked popular; quick add. 15. Wallet & points with the user's numbers.
16. Admin bottom banners. 17. "Делаем каждый день вкуснее — Душанбе с нами ❤️". 18. Bottom nav unchanged (5 tabs).
- Batch-1 sections merged: happy-hour rail → hero slide + Flash Sale; loyalty card → wallet section; re-order rail →
  last order; express rail → Express badge; best sellers → Recommended. Rotating search examples replaced by one placeholder.
- Icons: Microsoft Fluent Emoji 3D (MIT, `assets/3d/LICENSE-fluentui-emoji.txt`), 44 WebP files, 190 KB, lazy-loaded.

## Tests
qa_all customer 0 issues at 360/390/430 online/offline incl. the empty-data pass and new screens (filters, filtered
results, notifications, all categories); flow_check, cart_check, smoke, overflow, header checks pass.
