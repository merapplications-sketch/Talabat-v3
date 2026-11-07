# Test authentication reset checkpoint — 7 November 2026

Approved test project fsvrsvqfknogwmhccera only. CSP connectivity fix remains deployed as Sites v11 / app pilot-mobile-20261107.3. Auth logs now report invalid_credentials, not network transport failure.

User explicitly authorized resetting existing five test accounts. On 2026-11-07T00:20:39Z, performed a tightly scoped administrative SQL update of auth.users encrypted_password (bcrypt cost 10) and updated_at for the five exact UUID/email pairs. Generated distinct random 128-bit passwords with mixed class prefix/suffix; no plaintext credentials in Git. Credentials delivered privately in TALABOT-test-access.md. No new accounts, role changes, financial changes, or production access. Identity mappings and confirmation were checked; accountant retains active finance-only staff permission; driver approved; merchant owns existing synthetic stores.

Post-reset query confirms same account UUIDs/roles and order 1 delivered,total40,settled2026-11-06T18:43:49Z. Merchant's delivered password was verified against stored bcrypt (boolean true, no hash disclosure).

One secure browserAuth submission after reset still displayed wrong email/password. Values submitted are not visible to the agent and cannot be compared. Do not claim successful UI login or infer user typo. No retry loop or second reset. Manual existing-account entry is the next bounded verification. Remaining: five-role UI login proof and cash journey from buttons to receipt. Never resettle order 1. No changes to app layout or login safeguards.
