# T1 — live read-only result (owner ran sql/verify_catalog_readonly.sql v81b, 24 Oct) — mapped
Raw: `verify_catalog_2026-10-24.csv`. Read only; nothing changed.

| Area | Live | Consequence |
|---|---|---|
| Patches | 26, 27, 29, 32, 33, 34 present · 35, 36, 37, 38 absent | 27 doubt closed. Admin search uses the loaded-orders fallback; partner page / leads stay off; finance v60/v61 stays frozen |
| Accounts | admin 1 · customer 2 · driver 1 · merchant 2 | enough for one live pass (T6) with the existing test accounts |
| Stores | RLS on; admin ALL (`is_admin`); staff with `stores` insert/update; read = active or owner or staff; triggers validate / phone / images / audit | admin «add store» (v81 fix) is allowed by the server |
| Dishes | RLS on; write = owner or staff `stores`; read = available+approved+active store, owner, staff; `approved` default true + approval / guard triggers | restaurant saves, admin approval path exists on the server |
| Sizes / extras | RLS on; write via the dish owner / staff; read needs a signed-in user; defaults max_sel 1, required false, available true; insert caps (trg_cap_*) | matches the mock defaults used in catalog_check |
| Banners | RLS on; write = perm `content`; read = active within dates; defaults is_active true, placement top, link_type 'none' | new banners are visible at once (as in the mock) |
| Photos | bucket `media` public, 1 MB, jpeg/png/webp; insert only into the own folder `<uid>/…`; `proofs` private 1 MB jpeg; no inline photos stored | core uploads `<uid>/<uuid>.jpg` JPEG ≤ 800–1200 px → allowed; the inline fallback would be stopped by the image triggers (by design) |
| Wallet / points | wallet_entries.order_id bigint, loyalty_ledger columns as the core reads them | T2 functions (orderWallet, pointsSnapshot) read existing columns |
| Rows | stores 5 (4 active), dishes 7 (all approved, all with photos), groups 8, options 15, banners 9 active | real catalog data exists for T6 |

Still not proven live: an actual save with each account (T6), storage upload by each role, realtime.
