# TALABOT — continuation .21, 2026-11-07

This is evidence for the continuing review, not full acceptance or independent penetration testing.

## Deployment and scope
Sites source be4d6565c466664be1d67dacc678a3dea32d7888; hosting31; deployment appgdep_6aef3b896bc0819184568c382471f53b succeeded 2026-11-07T14:54:19.659158Z.
Test Supabase fsvrsvqfknogwmhccera only. Source .20 fec375fb5860759813069c98ea2ab3a62940de26 remains rollback point.
UI change only adds metadata/list summaries to existing scoped proof diagnostic. Syntax/build74 assets passed before deployment. Customer authentication scope unchanged.

## Confirmed finding F21-01 — internal finance permission ignored revoked sessions
Before repair, finance_private.accountant() checked staff active/finance permission and banned_at but not account_enabled(). A rollback-only synthetic finance user with a revoked session returned finance_access.execute=true and five financial rows while account_enabled=false.
Existing REST pre-request gate already denied revoked sessions. Therefore alternate/internal access-control gap is proven, not an HTTP bypass. Severity: medium defense-in-depth finding; broader impact unproven.
Applied pilot_finance_revoked_session_guard: require account_enabled() before original finance staff predicate. SQL in ../finance-session-guard-21.sql.
After: valid finance access preserved; revoked execute=false, rows0. Required-MFA aal1 execute=false/rows0; aal2 execute=true. These are synthetic PostgreSQL claim contexts, not real OTP assurance.
Fixture cleanup: users0, MFA roster fixture0, revocation fixture0. No protected account was changed.

## Proofs
Authorized customer download200/26651bytes, info200, list200/one matching item; single and batch URL signing denied.
Synthetic required-MFA aal1/nonowner: download/info404, list200/empty, no signed URLs.
Do not attribute this combined negative case to either ownership or AAL in isolation. Historical bearer URL survives until expiry; no retroactive revocation guarantee.

## RPC and advisor coverage
Fresh inventory119 authenticated SECURITY DEFINER functions:17 triggers,76 direct guards,23 delegated guards,3 intended public projections by heuristic classification. Guard presence is not a pass.
Seven mutable-search-path advisory functions are SECURITY INVOKER; definitions inspected. No privilege escalation demonstrated. No speculative rewrite made.
Security advisors still include intentional restrictive/no-policy tables, callable SECURITY DEFINER functions requiring case-by-case review, and leaked-password protection disabled. Advisor presence alone is not an exploitable-finding verdict.

## Provider and operations
Cloudflare exact zone lookup chatgpt.site returned no accessible zone. Cannot verify managed host WAF/DDoS coverage or direct Supabase bypass protection.
Supabase logs expose login/token-revocation/status events. Aggregates saved in monitoring.json contain no credentials. QA contributes to counts; these are not incident counts.
No approved alert recipient/channel and no delivered alert evidence. Console logs and cost warnings do not establish delivery or an enforceable spending ceiling.
Free-plan backup limitation remains. No actual separate-target database+Storage restore, measured RPO/RTO, or approved independent restore destination.

## Real concurrency block
Prepared two-connection settlement/refund tests in ../concurrency21. Automatic approval review rejected persistent synthetic fixture creation, interpreting allowed testing as rollback-only. Setup was not executed; no substitute bypass attempted. Prior overlapping wallet evidence remains valid only for its original case.

## Remaining acceptance gaps
Live synthetic MFA enrollment/challenge/recovery; global/multiple-session and Realtime termination; historical bearer-link handling; full role/object/operation matrix; real concurrent settlement/refund and interrupted-acknowledgement tests; server-side file-content validation; provider controls/cost ceiling; delivered incident alerts; real backup restore; physical older devices/weak network.
The ASVS matrix retains343 untested,2 failed,0 whole-requirement passes. Partial successful tests above must not be promoted to whole-requirement acceptance.

## Preserved state
Fresh readback: orders1/2/3 delivered, total40/cash40; original settlement timestamps for1/2, order3 unsettled; receipts2. MFA roster1 synthetic-only; synthetic factors0. Passwords, production, internal routes and pricing/accounting rules unchanged.

## Required external actions, not generic permission
1. Existing synthetic security tab: user completes authenticator enrollment and code submission for asvs-security@talabot-test.invalid. No protected/customer account enrollment. Credential setup is a manual-browser requirement.
2. For genuine settlement/refund concurrency, approval review requires explicit permission to retain exactly the prepared synthetic customer/driver/finance-support user/store, one auto-ID100TJS order, two tickets, test refund60TJS and settlement5TJS receipt/audit records in test only. No real money or protected orders.
3. Restore drill requires a separate disposable PostgreSQL/Supabase target and secure connection availability, plus exported Storage objects; do not reset the existing project's database password or restore over it.
4. Incident delivery requires an approved receiving address/channel and recipient, then one labelled synthetic incident delivery test.
Provider-owned zone settings need provider evidence/access; no assumption that owner can administer chatgpt.site.
