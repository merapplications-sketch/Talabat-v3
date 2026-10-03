# Talabat: checklist for Supabase + launch (things that code cannot do for you)

## A. Do these in the Supabase dashboard BEFORE real customers
1. Authentication -> Sign In / Providers -> Email: turn **Confirm email ON** (it is OFF for testing), minimum password length **8**, turn on **Leaked password protection** (Pro plan).
2. Authentication -> Attack Protection: turn on **CAPTCHA** (Cloudflare Turnstile is free) so bots cannot create thousands of accounts.
3. Authentication -> MFA: enable TOTP and enroll the **admin** account.
4. Authentication -> URL Configuration: Site URL = your real app address; remove every address you do not use.
5. Authentication -> Providers: disable every provider you do not use (anonymous sign-ins OFF).
6. Project Settings -> Database: upgrade the **compute size** (Small/Medium) before launch; enable **daily backups / Point-in-Time Recovery**.
7. Database -> Advisors: open **Security Advisor** and **Performance Advisor**; fix everything marked red/yellow.
8. Realtime -> Settings: check the **concurrent connections** limit of your plan (each open app = 1 connection). Raise it before a big launch.
9. Storage: bucket `media` exists (created by schema_patch17.sql). Keep the 1 MB limit.
10. Run `security-check.html` with a throw-away customer account after EVERY SQL patch.

## B. Order of work after uploading schema_patch17.sql
1. Upload the new files to GitHub.
2. Open `migrate-images.html` while signed in to the admin app -> "Scan" -> "Convert now" (moves all old images out of the database).
3. Run `security-check.html` again.

## C. What the numbers mean (measured in a simulation of the real code, not on your server)
* Idle customer: old design 210 requests per minute, new design about 18 per minute (11x less). Hidden tab: 0.
* A server answers a request in a few milliseconds, so the real limit is your Supabase plan (compute size, realtime connections),
  not the app. Do a staged real load test (50 -> 200 -> 1000 virtual users, with k6) on a COPY of the project before launch.

## D. Known limits that need a developer later
* Push notifications while the app is closed (needs PWA + VAPID + a server function).
* Phone-number login with OTP (needs an SMS provider that sends to Tajikistan).
* Fully server-side search of dishes across all restaurants (today the app downloads the menus; fine up to a few thousand dishes).
* Subresource Integrity hashes for the CDN scripts (needs internet access to compute the hashes).
