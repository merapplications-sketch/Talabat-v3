# partner-lead — setup (NOT done; nothing here is applied or deployed)

The public page `partner.html` sends the 3-field form to this Edge Function. The function checks Cloudflare Turnstile with
the secret key, makes keyed hashes of the phone and of the client address, and calls `lead_submit()` (sql/schema_patch36.sql)
with the service role. The database refuses `lead_submit()` from anon and signed-in users, so the check cannot be skipped.

## Order (all by the owner, when approved)
1. **Database:** run `sql/schema_patch36.sql` in the Supabase SQL editor (after checking it on a copy). It stops by itself, changing
   nothing, if a banner uses a link type it does not know. Review the PROPOSED limits in `lead_settings` first:
   `per_phone_day 3 · per_client_hour 5 · per_client_day 15 · global_hour 200 · attempts_keep_days 30 · rejected_keep_days 90`
   (`update lead_settings set value = … where key = …`). `link_enabled` stays 0 (see 6).
2. **Cloudflare Turnstile:** create a widget (free) for the site hostname(s), e.g. `merapplications-sketch.github.io`
   (and the final domain later). Mode: Managed. You get a **site key** (public) and a **secret key** (server only).
3. **Secrets** (Supabase → Edge Functions → Secrets, or `supabase secrets set`):
   - `TURNSTILE_SECRET_KEY` = the Turnstile secret key
   - `LEAD_HASH_KEY` = a new random string, 32+ characters (e.g. `openssl rand -hex 32`); never shown anywhere, never changed
     lightly (changing it resets the phone / client counting)
   - `PARTNER_ORIGINS` = `https://merapplications-sketch.github.io` (comma-separated if several; exact origin, no path)
   - optional `TURNSTILE_HOSTNAMES` (default: the hostnames of PARTNER_ORIGINS)
   - `SUPABASE_URL`, `SUPABASE_SERVICE_ROLE_KEY` are provided by Supabase to every function automatically.
4. **Deploy:** `supabase functions deploy partner-lead --no-verify-jwt`
   (`--no-verify-jwt`: visitors have no account; the function does its own checks: origin, Turnstile, limits).
5. **Page:** in `partner.html` set `const CFG={fn:'https://dzydscryrnahnneydnry.supabase.co/functions/v1/partner-lead',siteKey:'<site key>'}`.
   With an empty CFG the page shows «Приём заявок временно недоступен» and sends nothing.
6. **Linking a request to a store** (admin): stays OFF until `assign_owner` is checked. Read-only check in the SQL editor:
   `select pg_get_functiondef(oid) from pg_proc where proname = 'assign_owner';` (also `select pg_get_constraintdef(oid) from pg_constraint where conrelid = 'banners'::regclass;`) — when its effect on the account role is known and
   accepted: `update lead_settings set value = 1 where key = 'link_enabled';` and `LEAD_LINK=true` in admin.html.
7. **Retention:** schedule `select lead_cleanup();` once a day (pg_cron, if available on the plan).
8. **Banner:** in the admin panel → Banners → new banner, placement «Внизу главной», link «Страница для заведений».
9. Before real traffic: `SCALING-AND-SECURITY.md` §A (email confirmation, CAPTCHA for sign-up, etc.) still applies.

## What the function answers
`ok` (200: new, already known or phone limit — the same answer), `bad_phone` / `bad_value` (400), `verify_failed` (403),
`busy` (429), `unavailable` (503: settings missing, Turnstile or database unreachable). Logs: the result code only.

## Tests (local, no services)
`node tools/partner_fn_check.mjs` (function with fake Turnstile / database), `psql -q -f sql/test_patch36.sql` and
`python3 tools/lead_race_check.py` (database on a local PostgreSQL).
