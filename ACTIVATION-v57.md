# Activation plan — restaurant onboarding (v57). PREPARED ONLY: nothing below has been run, created or deployed.

Branch `feature/partner-onboarding-v57` is built on `fix/uat1-v56` (stability batch, NOT approved). Building on it does not
approve it. Limits and retention in `lead_settings` are PROPOSED. Real sending and lead → store linking stay OFF in the code.

## 1. Blockers, split by what they stop

**A. Stop RECEIVING requests at all** (the page cannot send / nobody can work on them)
1. Approval of v57 and a way to publish it: v57 sits on the unapproved stability batch → approve it, or split v57 onto main.
2. Patch 36 applied (after the read-only check, step 1 below).
3. Cloudflare Turnstile widget for the site hostname → site key + secret key.
4. Supabase function secrets: `TURNSTILE_SECRET_KEY`, `LEAD_HASH_KEY` (32+ random chars), `PARTNER_ORIGINS`.
5. `CLIENT_IP_HEADER` (+ `CLIENT_IP_POSITION`) — which header carries the real visitor address is NOT verified; without it the
   function refuses every request by design.
6. Edge Function deployed (`--no-verify-jwt`) and `CFG` in partner.html filled (function URL + site key).
7. Approval of the proposed limits / retention.

**B. Stop only CONVERTING a request into a store** (receiving works without these)
- Read on 17 Oct (live, `sql/verify_patch36_single.sql`): `assign_owner` — anon cannot execute; signed-in accounts can call it but it
  refuses everyone except the admin (`is_admin()` inside); finds the account by e-mail (case-insensitive); customer → merchant only;
  sets `stores.owner_id`; no store-existence check; the previous owner is replaced (only the admin panel asks first) and keeps
  the merchant role. Its changes ARE audited by the live triggers `trg_audit_stores` (owner_id) and `trg_audit_profiles` (role);
  `app.bypass` only skips `guard_profile`, not the audit. (Correction of the 17 Oct note «no audit»: none inside the function,
  but audited by triggers.)
- Linking a request (`lead_link`) and assigning an owner (`assign_owner`) are separate operations; neither calls the other
  (proven locally on the live shape: linking changes only the request; assign_owner changes only stores + profiles).
- Remaining: the owner's decision to switch linking on (`link_enabled = 1`, `LEAD_LINK = true`) and what «converted» means in
  practice (recommended: assign the owner first in «Магазины», then link). `assign_owner` itself is not changed.

**C. Stop only the BANNER** (the page still works by its direct link)
- If patch 36 prints `banners NOT changed`, the banner check has an unknown structure (query B) — decide on the new rule.
- The customer app must already contain the `partner` banner link (v57) before such a banner is created.

## 2. Steps in order (each: what · check · undo)
| # | Step | Check that it worked | Undo |
|---|---|---|---|
| 0 | Approve v57 (+ stability batch or a split); merge only then | — | — |
| 1 | Run `sql/verify_patch36_readonly.sql` (read-only, rolls back), send results | output only | nothing to undo |
| 2 | Decide limits / retention; adjust the values at the top of patch 36 if needed | — | — |
| 3 | Run `sql/schema_patch36.sql` (first on a copy / branch project if available) | no ERROR; read the WARNING / NOTICE lines; `select * from lead_settings;` | `sql/rollback_patch36.sql` (see §3) |
| 4 | Run `security-check.html` (new rows: anon / customer cannot submit around the check, cannot read or change requests) | all PASS | — |
| 5 | Create the Turnstile widget (hostnames) | site key + secret key exist | delete the widget |
| 6 | Verify the client-address header on a test deployment (README, CLIENT_IP_HEADER) | one header keeps the real address when forged ones are sent | remove the test build |
| 7 | Set the secrets (TURNSTILE_SECRET_KEY, LEAD_HASH_KEY, PARTNER_ORIGINS, CLIENT_IP_HEADER) | `supabase secrets list` shows the names | unset |
| 8 | Deploy `partner-lead` with `--no-verify-jwt` | a POST without token → 403 `verify_failed`; from another origin → 403; nothing written | delete the function |
| 9 | Fill `CFG` in partner.html, publish | the page shows the Turnstile box; one real test request appears in Admin → Stores «Заявки с сайта»; send it again → same answer, no second row | empty `CFG` again (form off) |
| 10 | Stores staff test: «Связались», «Отклонить» with a reason | status changes; staff without «stores» cannot | — |
| 11 | Banner (optional): Admin → Banners → «Внизу главной», link «Страница для заведений» | tap on the customer home opens the page | switch the banner off |
| 12 | Retention: schedule `select lead_cleanup();` daily (pg_cron) | `cron.job` row | unschedule |
| 13 | Later, only after B1: `update lead_settings set value = 1 where key = 'link_enabled';` + `LEAD_LINK = true` | admin links one request to one store; second link refused | set back to 0 / false |

## 3. Rollback
- **Fast stop (keeps everything):** `update lead_settings set value = 0 where key = 'global_hour';` (every send answers «busy»),
  and/or empty `CFG` in partner.html, and/or delete the function.
- **Full removal:** `sql/rollback_patch36.sql` — refuses while requests exist (export first, then
  `set patch36.drop_leads = 'yes';`) or while a banner links to the partner page; restores patch 19/26 and the original banner
  check. Tested locally: `python3 tools/patch36_ops_check.py`.

## 4. Gaps found in the review of the path page → server → database → admin (v57c)
| Gap | Fixed in v57c | Evidence |
|---|---|---|
| Staff accounts with the «stores» permission (not admin) never loaded the requests (only role admin / merchant did) — they could not follow up; the same was already true for branch requests | yes: requests loaded + live updates for staff with «stores» | `tools/lead_admin_check.py`: before 0 requests, after 4; card shown, no link control |
| iPhone zoomed into the calculator fields: `font:16px inherit` is invalid CSS, the rule was dropped, fields were 13.3 px (<16 px → iOS zooms) | yes: valid font rules; zoom by the user still allowed | `tools/partner_check.py`: before 13.33 px, after 16 px in every field; not yet checked on the iPhone |
| No read-only queries / rollback / ops test | yes: `sql/verify_patch36_readonly.sql`, `sql/rollback_patch36.sql`, `tools/patch36_ops_check.py` | 0 fails locally |
| Converting a request does not pre-fill the «new store» form | not done (convenience, not required) | — |

## 5. Match with the live database (read 17 Oct) — v57e
| Live fact | Patch 36 / rollback |
|---|---|
| `banners_link_type_check` = `link_type IN ('none','store','category')` (no NULL part) | simple form recognised: re-created with the same name + 'partner'; the other 5 banner constraints (2 NOT VALID) and the audit / image triggers untouched; rollback restores the exact definition |
| `store_requests` = patch 19/26 exactly (constraint names, NOT NULL owner/location, 2 indexes, read policy only, realtime on), 2 approved branch requests | apply keeps both rows identical (+ kind 'branch'), policy, indexes and realtime unchanged; rollback restores the catalog shape exactly |
| no trigger on `store_requests` (no audit of request decisions) | v57e adds `trg_audit_store_leads` (live `audit_changes`): UPDATEs of kind 'lead' only — status, store_id, staff note, who. Branch requests: unchanged behaviour |
| `audit_changes`, `guard_profile`, `is_admin`, `has_perm`, `norm_phone`, roles as expected; patch 36 names absent | no change needed |
Test: `psql -q -f sql/test_patch36_prodshape.sql` 27/27 (live definitions copied from the read). Also re-run: test_patch36 53/53,
patch36_ops_check 0, lead_race_check 0.
