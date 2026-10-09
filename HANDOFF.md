# Talabat v3 — hand-off for a new conversation (state at v44)

## Who / how to work
- Owner: Arabic speaker (Dushanbe), apps in Russian/English, currency TJS. Explain in SIMPLE Arabic, one clear message at the end of each batch: what changed, how it was tested, links, exact steps for the owner.
- Role: Full-Stack & Security Lead. Do NOT invent pages/features that were not requested (the "Info" tab was removed for this reason). Work the approved backlog in order. Never hand over anything before `python3 tools/qa_all.py` reports 0 issues (plus smoke/hdr/overflow/sheet/branch checks).
- Never edit main directly: feature branch -> owner merges via GitHub PR link. Commit trailers: `Co-Authored-By: Claude <noreply@anthropic.com>` + session link.

## Stack
- 4 single-file apps (customer/driver/merchant/admin .html) + shared `talabat-core.js`, Supabase `https://dzydscryrnahnneydnry.supabase.co` (publishable key in core), GitHub Pages: `https://merapplications-sketch.github.io/Talabat-v3/<app>.html?v=N`. Repo: `merapplications-sketch/Talabat-v3`.
- Test accounts admin@/merchant@/driver@/customer@test.com, password `Test1234!` (weak: delete/change before launch).
- Each app has its own auth storage key; wrong-app accounts get a "wrong app" screen with a link.

## Branch state
- `main` = v43 (PR #13 DoD audit merged by the owner).
- Newest: `feature/e2e-ux-v44` (v44, on top of main): https://github.com/merapplications-sketch/Talabat-v3/pull/new/feature/e2e-ux-v44 — end-to-end flow test, single-scroll restaurant page, merchant bottom nav, clean-up; see CHANGES-v44.md. No SQL.
- OWNER DECISION: the restaurant page has NO tabs (no top/horizontal section tabs). One vertical scroll with section titles. Do not add tabs back.
- The owner sent a mandatory "Definition of Done" protocol (v43): every batch = self-QA at 360/390/430 online+offline, one design system (buttons/cards/headers/empty states), compact modern call/map buttons, no raw keys/overlaps, batch delivery with a report table. Follow it.
- v41 included: staff RBAC (patch 26), multi-branch restaurants (patch 27), overflow clip (v37), dish sheet scroll/validation fix (v38), driver header pill fix + full-width offline strip (v40), QA harness + fixes for branch sync button and hidden discount badge (v41).
- `feature/rest-tabs-v39` is OBSOLETE (Info tab removed).

## SQL (run in Supabase SQL Editor, in order)
- `sql/schema_patch26.sql` then `sql/schema_patch27.sql` (owner said he ran both). Tests on a local replica: `sql/test_patch27.sql` (67/67). Earlier patches 17-25 assumed applied.
- Security page: `security-check.html?v=41` — owner has NOT yet reported its result; ask for the summary line ("OK: n passed" / "PROBLEM").

## Test tools (python3 + playwright; run from repo root)
- `tools/qa_all.py` (~6 min, run in background: every screen x 360/390/430 x online/offline; must print `QA ISSUES 0`; also runs an empty-data pass; env QA_APPS=driver QA_W=390 narrows, QA_NOEMPTY=1 skips the empty pass).
- `tools/flow_check.py` (FLOW FAILS 0: full order life-cycle across the 4 apps with a shared in-memory DB, screenshots in /tmp/flow), `tools/cart_check.py` (CART FAILS 0), `tools/smoke.py` (TOTAL ERR 0), `tools/hdr_check.py`, `tools/overflow2.py`, `tools/sheet_check.py`, `tools/branch_check.py`.
- Limits: Chromium + mocked Supabase only; nothing verified on a real iPhone or the live DB.

## Open items waiting on the owner
1. Merge the v44 PR. 2. Report security-check result. 3. Confirm admin@test.com has role admin in `profiles`. 4. Say in which app/page the "app wider than the iPhone screen" issue appears (v37 clips overflow defensively; cause unknown). 5. Real-device feedback on v41.

## Approved backlog, in order (not started unless noted)
1. Cart + checkout polish (customer) — DONE in v42 (owner may still list extra wishes).  2. Restaurant page tabs — DECIDED: no tabs, single scroll (done in v44).  3. Loyalty/cashback/points, happy-hour promos.  4. Auto-cancel after 5 min (pg_cron), live driver GPS tracking, offline cache + sync.  5. Push notifications, batch delivery, heatmaps, partner requests, offers/ads.  6. OTP signup via WhatsApp/SMS (needs provider; no domain yet).  7. Before launch: delete weak test accounts, set Supabase Auth rate limits.
