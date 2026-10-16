# v57 — restaurant onboarding: public partner page (branch `feature/partner-onboarding-v57`, from `fix/uat1-v56`). NOT merged, NOT deployed, SQL NOT applied.

Owner decisions 16 Oct 21:23: form without an account + Turnstile checked by the server; fields name / phone / category;
Dushanbe, RU/EN; banner at the bottom of the home screen controlled by the admin (section order unchanged); stores staff follow
up and change the status, only the admin converts / links / assigns the owner; commission by agreement, empty in the calculator.
Limits and retention: PROPOSED, not approved for production.

| Part | What | Files |
|---|---|---|
| Page | `partner.html`: text RU/EN (only what the apps do today), calculator, 3-field form, Turnstile box, states: needs check, wrong phone, sending (one send per tap), ok (general answer), busy, check failed, server unavailable / no network (values kept, «Повторить»), settings missing (form off). Token single-use: a new check after every send | partner.html |
| Calculator | own estimate from declared inputs (not the order settlement): S = avg × orders; − discount; − commission % (on sales after discount); − points/cashback %; − free delivery count × cost → «after the service deductions, before taxes»; profit only with food cost: − food cost % of menu prices − packaging × orders − other costs → «after the costs you entered, before taxes». Empty = «не учтено», 0 = included. Limits per field, free-delivery orders ≤ orders, both free-delivery fields or none. Not included listed; no guarantee | partner.html |
| Server | Edge Function `partner-lead`: origin allow-list, body ≤ 4 KB, fields, hidden field, Turnstile siteverify with the secret (success + action `partner_lead` + hostname), HMAC-SHA256 keys of phone and client address with `LEAD_HASH_KEY`, `lead_submit` with the service role. Missing setting / failed check → refused (503 / 403), never a fake success. Logs: result code only | supabase/functions/partner-lead/{handler.js,index.ts,README.md} |
| SQL | patch 36: `store_requests.kind` ('branch' unchanged / 'lead'), lead states new → contacted → converted / rejected, one open lead per phone (unique index, atomic), one lead per store; `lead_attempts` (keys only, every call counted, nothing resets), `lead_settings` (adjustable limits), `lead_submit` (service_role only, same answer for new / duplicate / phone limit), `lead_set_status` ('stores' permission), `lead_link` (admin, OFF by `link_enabled = 0`), `lead_cleanup`; banners link type `partner` | sql/schema_patch36.sql, sql/test_patch36.sql |
| Admin | card «Заявки с сайта» in Stores: contacted / reject (reason required); link control for the admin only, disabled (assign_owner not verified); Stores badge counts new website requests; banner link option «Страница для заведений» | admin.html |
| Shared | `TLB.leadDecide` (one method) + 2 error names | talabat-core.js |
| Customer | a banner with link `partner` opens partner.html | customer.html |

Open: `assign_owner` source is not in the project files (only its tests: admin only) → linking stays off. Protection against a
flood rests on Turnstile (server-checked, single-use) + client-address limit; the address header's reliability on Supabase is not
verified; the phone limit and the site brake are secondary. iPhone / Safari issues of v56: still open, not touched.

## Tests (local; Chromium / Node / PostgreSQL 16 — not Safari, not the live database, no real Turnstile)
- `psql -q -f sql/test_patch36.sql` → 50/50 (permissions, generic answer, counting, limits, states, link once / off, branch path unchanged, banners, retention)
- `python3 tools/lead_race_check.py` → 0 fails (20 parallel sends of one phone = 1 row + 20 counted attempts; phone limit and client limit exact under parallel sends)
- `node tools/partner_fn_check.mjs` → 33 pass (Turnstile, missing settings, origins, HMAC keys, no personal data in logs, every server answer)
- `python3 tools/partner_check.py <preview>/partner` → 72 pass (states, one send per tap, values kept, single-use check, calculator 3 cases vs formula, empty vs zero, limits, 360/390/430/landscape RU/EN)
- `python3 tools/lead_admin_check.py <preview>/admin <preview>/customer` → 0 fails (card, badge, actions, link off, staff view, banner opens the page)
- Re-run because shared / admin / customer files changed: smoke (4 apps) TOTAL ERR 0 · staff_ui 500/0 · admin_uat 0 · form_keep --quick 194/0 · preview_check 0 · qa_all customer QA ISSUES 0
- Not re-run (not affected): courier, restaurant analytics / ids, tab navigation, map tiles, diagnostics.
