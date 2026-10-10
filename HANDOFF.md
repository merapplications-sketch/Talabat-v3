# Talabat v3 — hand-off for a new conversation (state at v49)

## Who / how to work
- Owner: Arabic speaker (Dushanbe), apps in Russian/English, currency TJS. Explain in SIMPLE Arabic, one clear message at the end of each batch: what changed, how it was tested, links, exact steps for the owner.
- Role: Full-Stack & Security Lead. Do NOT invent pages/features that were not requested (the "Info" tab was removed for this reason). Work the approved backlog in order. Never hand over anything before `python3 tools/qa_all.py` reports 0 issues (plus smoke/hdr/overflow/sheet/branch checks).
- Never edit main directly: feature branch -> owner merges via GitHub PR link. Commit trailers: `Co-Authored-By: Claude <noreply@anthropic.com>` + session link.

## Stack
- 4 single-file apps (customer/driver/merchant/admin .html) + shared `talabat-core.js`, Supabase `https://dzydscryrnahnneydnry.supabase.co` (publishable key in core), GitHub Pages: `https://merapplications-sketch.github.io/Talabat-v3/<app>.html?v=N`. Repo: `merapplications-sketch/Talabat-v3`.
- Test accounts admin@/merchant@/driver@/customer@test.com, password `Test1234!` (weak: delete/change before launch).
- Each app has its own auth storage key; wrong-app accounts get a "wrong app" screen with a link.

## Branch state
- `main` = v45 (PR #15 merged). Owner was told to run patch 28.
- Newest: `fix/points-restaurant-v49` (v49): points discount paid by the restaurant (display/settlement only, no SQL). https://github.com/merapplications-sketch/Talabat-v3/pull/new/fix/points-restaurant-v49
- Previous: `fix/hh-restaurant-v48` (v48, merged; owner ran patch 31): patch 31 (restaurant pays happy hour) + security page dish fix. https://github.com/merapplications-sketch/Talabat-v3/pull/new/fix/hh-restaurant-v48
- Previous: `fix/promo-limit-v47` (v47, merged; owner ran patch 30): patch 30 = robust promo guard (owner still saw the promo FAIL after v46). https://github.com/merapplications-sketch/Talabat-v3/pull/new/fix/promo-limit-v47
- Previous: `feature/loyalty-v46` (v46, merged): https://github.com/merapplications-sketch/Talabat-v3/pull/new/feature/loyalty-v46 — points, cashback, happy hour; NEEDS `sql/schema_patch29.sql`; see CHANGES-v46.md.
- ALWAYS attach every SQL file to the message with SendUserFile (the owner asked: he cannot find files in the repo by himself).
- OWNER DECISION: the restaurant page has NO tabs (no top/horizontal section tabs). One vertical scroll with section titles. Do not add tabs back.
- The owner sent a mandatory "Definition of Done" protocol (v43): every batch = self-QA at 360/390/430 online+offline, one design system (buttons/cards/headers/empty states), compact modern call/map buttons, no raw keys/overlaps, batch delivery with a report table. Follow it.
- v41 included: staff RBAC (patch 26), multi-branch restaurants (patch 27), overflow clip (v37), dish sheet scroll/validation fix (v38), driver header pill fix + full-width offline strip (v40), QA harness + fixes for branch sync button and hidden discount badge (v41).
- `feature/rest-tabs-v39` is OBSOLETE (Info tab removed).

## SQL (run in Supabase SQL Editor, in order)
- `sql/schema_patch26.sql` then `sql/schema_patch27.sql` (owner said he ran both), then `sql/schema_patch28.sql` (v45, promo guessing limit; wraps the existing check_promo as check_promo_base), then `sql/schema_patch29.sql` (v46 loyalty; replaces place_order with a 12-arg version adding p_points, adds happy_hours/loyalty tables, trigger trg_orders_loyalty). `sql/test_patch29.sql` 40/40 on empty PostgreSQL; `tools/loyalty_parity.py` compares app vs SQL bills (needs that local DB). Then `sql/schema_patch30.sql` (v47: replaces patch 28's guard; counts every non-success answer; `sql/test_patch30.sql` 20/20). Owner confirmed admin@test.com has role admin. Then `sql/schema_patch31.sql` (v48: happy hour paid by the restaurant; orders.discount includes it, hh_discount = its part).
- Owner decisions: cashback off until he enables it; happy hour paid by restaurant; iPhone width issue gone; FINAL loyalty: earn 10/TJS, 1000 pts = 1 TJS, min 1000, expiry on, cashback off; points + happy hour are the restaurant's cost; commission NOT reduced by points (it is computed before points).
- Security check SC-48: OK 126 passed, 2 WARN: brands/brand_stats missing => patch 27 NOT applied in the live DB (owner thought he ran it). Asked him to run sql/schema_patch27.sql. `sql/test_patch28.sql` runs on an EMPTY local PostgreSQL (self-contained, 15/15). Tests on a local replica: `sql/test_patch27.sql` (67/67). Earlier patches 17-25 assumed applied.
- Security page: owner reported (v44) one FAIL: promo guessing not rate-limited → fixed by patch 28; ask him to re-run `security-check.html?v=45` after running the patch (wait 10 min between runs: the test blocks its own account).

## Test tools (python3 + playwright; run from repo root)
- `tools/qa_all.py` (~6 min, run in background: every screen x 360/390/430 x online/offline; must print `QA ISSUES 0`; also runs an empty-data pass; env QA_APPS=driver QA_W=390 narrows, QA_NOEMPTY=1 skips the empty pass).
- `tools/flow_check.py` (FLOW FAILS 0: full order life-cycle across the 4 apps with a shared in-memory DB, screenshots in /tmp/flow), `tools/cart_check.py` (CART FAILS 0), `tools/smoke.py` (TOTAL ERR 0), `tools/hdr_check.py`, `tools/overflow2.py`, `tools/sheet_check.py`, `tools/branch_check.py`.
- Limits: Chromium + mocked Supabase only; nothing verified on a real iPhone or the live DB.

## Open items waiting on the owner
1. Merge the v44 PR. 2. Report security-check result. 3. (done: admin role confirmed) 4. (done: owner no longer sees the iPhone width issue) 5. Real-device feedback on v41.

## Approved backlog, in order (not started unless noted)
1. Cart + checkout polish (customer) — DONE in v42 (owner may still list extra wishes).  2. Restaurant page tabs — DECIDED: no tabs, single scroll (done in v44).  3. Loyalty/cashback/points, happy-hour promos — DONE in v46 (owner decisions: 10 pts/TJS, cashback to wallet, happy hour scheduled by admin, expiry, minimum; defaults 1000 pts = 1 TJS, min 1000, 90 days, cashback 0% — ask owner to confirm the value/defaults).  4. Auto-cancel after 5 min (pg_cron), live driver GPS tracking, offline cache + sync.  5. Push notifications, batch delivery, heatmaps, partner requests, offers/ads.  6. OTP signup via WhatsApp/SMS (needs provider; no domain yet).  7. Before launch: delete weak test accounts, set Supabase Auth rate limits.
