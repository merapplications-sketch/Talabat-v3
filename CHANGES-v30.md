# v30 (feature branch: batch1-fixes) — based on stable v29
Modified: talabat-core.js, admin.html, merchant.html, driver.html, customer.html (stamps/version only)
No SQL patch required.

## Fixed
- Admin: inputs 16px -> no iOS zoom while typing.
- Lang/Sign-out chips moved from fixed overlay into a top bar in normal flow (no overlap with headers/pills).
- Admin/merchant/driver: render keeps focused input, caret and scroll position (search box no longer loses keyboard; tab lists don't jump to top). Merchant main-tab switch still scrolls to top.
- Admin banner editor: no autosave; draft + one Save button; from/to dates validated; image/link/title/order/active in draft.
- Admin new store: defaults for all fields; delivery fee required (clear message).
- Login: client-side throttle after 5 failed attempts (30s doubling, max 5 min).

## Regression checks run
JS syntax of all pages; inline-handler names all defined; no duplicate i18n keys; XSS heuristic scan (no unescaped data in templates); Chromium test of focus/scroll wrapper.

## Not changed (needs your input)
Checkout distance wording, options sheet, multi-branch, RBAC (next batches).
Server-side OTP/login rate limits: set in Supabase > Authentication > Rate limits.
