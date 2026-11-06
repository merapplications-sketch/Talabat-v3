# Confirmed root cause — 2026-11-06 23:20 UTC

Approved site only: https://talabot-isolated-safari-20261106.alwarikahtan.chatgpt.site
App before fix: pilot-mobile-20261107.2; app source 98e786759bee7324f712c0cdd3e82d2dac7eba3a.
Sites v10/c93de1ab50a6de55b12a4b7bc8cf965832d2d645 only added a bounded diagnostic page; deployment appgdep_6aee60313b0c8191a6ecaf3d06b35937 succeeded. No unresolved deployment.

All four deployed HTML files retained production-only connect-src while talabat-core.js used test Supabase fsvrsvqfknogwmhccera. Confirmed directly in merchant's loaded DOM, not only local source:

`connect-src 'self' https://dzydscryrnahnneydnry.supabase.co wss://dzydscryrnahnneydnry.supabase.co`

This blocks test auth, REST and realtime before the request reaches Supabase. The separate diagnostic page had no such CSP, explaining its success. Real Safari reported the same failure as the cloud browser. This is not evidence of incorrect credentials.

Exact same-origin transport comparison (empty requests, no account credentials): native POST 400 validation_failed in1072ms; app connectionFetch POST400 in856ms; SDK default400 in346ms; SDK+app wrapper400 in337ms. All returned 'missing email or phone'. Empty-body backend POST with/without public Bearer also400. These rule out wrapper/SDK/public-header transport as the blocker in those conditions. They do not establish account login success.

Regression: check-hosted-csp.cjs failed all four apps before correction; passed all four after. tools/align-pilot-csp.cjs validates both bundle manifest and SB_URL against the approved test DB before changing only connect-src to test HTTPS+WSS. No wildcard/no removed CSP/no production access. Run it after copying source files and run the regression before every isolated bundle publication.

Fix bundle version: pilot-mobile-20261107.3. Preserves application logic, visual layout, all roles' storage keys, accounts/passwords, previous order and receipt. Removes temporary diagnostic page. No SQL/account/financial changes. Actual post-deploy login/cash results are recorded separately once observed; not claimed here.

## Resumed and deployed in new session
- Independently observed production-only CSP in the live merchant DOM before deployment.
- Retained the pending correction; affected CSP regression passed for all four apps and auth recovery tests passed.
- Published Sites version 11, source 25ca24c5407112de5fcff87aa5778f4ad72bb7a6; deployment appgdep_6aee64f157748191a5078ed71ffd6e93 succeeded at 2026-11-06T23:38:39Z.
- Reloaded actual merchant UI: pilot-mobile-20261107.3 and test-only HTTPS/WSS CSP confirmed. Login form renders.
- No account, SQL, order, receipt or financial mutations. Browser secure credential entry is required for final login proof and cash journey; do not claim completed before observing it.

## Post-deployment authentication result
Secure browserAuth request returned submitted. Fresh merchant UI displayed `Неверный email или пароль` (incorrect email or password), instead of no server response. Source maps this message only from invalid login / invalid_credentials. Login is NOT proven. Manual correction of existing merchant credentials is the remaining blocker; no password reset, new account, order, SQL or financial mutation performed. Cash UI journey remains pending.

