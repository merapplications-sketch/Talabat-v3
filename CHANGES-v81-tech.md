# v81 (tech) — admin sign-in and the catalog path on the published v80 base
Branch `tech/v81` from `integration/customer-v80-current` (ca8808d). customer v80 is untouched (byte-identical).
Not merged, not published, no SQL run.

## Code change (logic only, no visible change)
- `admin.html` · `addStore()`: read `fee_per_km` only if the field `#sk` exists. The «add store» form has no such field
  (removed earlier), so the button threw a script error and **new restaurants could not be created from the admin panel**.
  New stores now save; per-km fee stays editable in the store edit screen as before.

## Tests (mocked Supabase, Chromium; not the live DB)
- `tools/catalog_check.py` (new) — 27/27: admin new store (form) + cover / logo photos to bucket `media`, owner link,
  top + bottom banners with photos and edit; restaurant dish with photo / price / section, sizes (required, 1 of 3) and extras
  (max 2) with prices; admin approval; customer sees store photos, both banners, dish photo, sizes / extras with prices,
  required size enforced, line 35+8+12+5 = 60 TJS.
- `tools/admin_login_check.py` (new) — 13/13: sign-in screen, no sign-up for admin, bad email / wrong password messages,
  correct admin -> all sections, session kept, separate per app, sign out, customer account refused with a link to its app,
  staff account limited by `my_perms`, lock after repeated failures.
- `tools/flow_check.py` — order confirmation now done by sliding the v80 control (was the old 2 s hold): FLOW FAILS 0.
- `tools/qa_all.py` (current version) — 4 apps × 360/390/430 × online/offline: QA ISSUES 0. smoke: 0 errors.
- `sql/verify_catalog_readonly.sql` (new, read-only) — column defaults, RLS policies, bucket and storage policies, triggers,
  owner / permission functions, account counts by role, row counts (incl. inline photos). Checked on a local PostgreSQL stand-in.

## Hand-off to the design / UI team (ChatGPT)
- Touched UI file: `admin.html`, one expression inside `addStore()`; no markup, CSS or text changed.
- `customer.html`, `merchant.html`, `driver.html`, `talabat-core.js`: unchanged.

## Not verified
- Live sign-in and saving on the real database and storage (Chrome extension not connected; this workspace cannot reach
  Supabase / GitHub Pages). The read-only SQL above covers the parts the mocks cannot (RLS, defaults, bucket).
