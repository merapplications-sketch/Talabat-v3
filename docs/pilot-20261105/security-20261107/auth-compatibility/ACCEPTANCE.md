# Customer authentication compatibility and administrative MFA — same acceptance plan

Owner decision 2026-11-07: preserve approved customer login, logout and recovery. No mandatory authenticator, QR, new enrollment, new login method or paid fallback for customers. Synthetic MFA is testing authority only, not rollout approval. Any end-user authentication change requires separate owner approval. Administrative MFA/recovery remains a separate sensitive-access workstream.

## Confirmed current scope

Test project fsvrsvqfknogwmhccera readback: required MFA roster has one entry, exclusively synthetic85fea11e-738c-4221-ac29-51d4ff50d594; protected five accounts required0; synthetic verified factors0. No secret read or password/factor modification. Server restrictions remain unchanged.

.20 source fec375fb5860759813069c98ea2ab3a62940de26 removes the extra MFA bootstrap dependency from normal customer entry. Synthetic customer fixture still exercises the MFA gate; administrative entry retains it. This UI routing is NOT authorization and does not bypass server account_enabled/RLS. Five offline scope regressions passed: customer succeeds without MFA module or with MFA API failure; synthetic/admin fail closed; admin successful gate proceeds. Existing MFA unit checks passed. No enrollment or administrative enforcement rollout claimed.

## Minimum support status

No minimum device/OS/browser combination is accepted yet. Real-device evidence is missing; cloud Chrome and a phone-sized viewport do not establish compatibility. Device age alone is not a browser-engine version.

Updated .22: the confirmed direct randomUUID dependency in approval/return/finance paths is repaired with a secure getRandomValues UUIDv4 fallback; offline capability tests passed. This does not prove physical-device compatibility. SHA-256 key migration additionally needs WebCrypto/TextEncoder. These are capability constraints, NOT proof of login failure and NOT a validated whole-app support floor. MDN describes randomUUID as a secure-context API, cross-browser baseline since March2022: https://developer.mozilla.org/en-US/docs/Web/API/Crypto/randomUUID . Do not silently exclude older customers or substitute insecure randomness. Any compatibility fix must retain secure request IDs and idempotency.

## Dedicated physical-device matrix (all NOT TESTED)

| Cohort to obtain | Browser surfaces | Required record |
|---|---|---|
| Older iPhone able to run iOS15.x | Safari and installed Chrome iOS | Exact model, iOS build, browser build, engine, installed/PWA mode |
| Older iPhone on an earlier iOS (negative-boundary exploration only) | Actual available Safari | Exact model/build and first failing capability; no supported claim |
| Older Android8/9 phone with limited memory | Actual installed Chrome and system WebView if app uses it | Model, Android patch, Chrome/WebView exact versions and RAM |
| Android10/11 phone | Chrome and Samsung Internet where available | Exact versions, browser storage and privacy mode |
| Current iPhone/Android control | Safari/Chrome | Same cases and environment; no substitute for old-device rows |

For every actual combination run normal and weak-network cases: valid login; invalid password once without lockout loops; loading/error/retry behavior; reload and background/foreground; logout and Back/history; offline logout and remote-session status; password reset request and mail arrival; valid/expired/used reset link; password change and fresh login; account/role isolation. Preserve all five accounts and use dedicated synthetic customer mailbox and credentials for destructive recovery cases. No protected orders or financial mutations.

Weak-network test profile (planned, not executed): 400kbps download,128kbps upload,600ms RTT,2% packet loss; one10-second disconnect before submission and after response uncertainty, then reconnect. Record measured profile and timeout/retry behavior, not just selected emulator preset. Network emulation on an actual old device is distinct from CPU/viewport emulation. No flood or third-party load test.

Acceptance evidence per case: exact source/deployment, UTC, device/build, path, expected/observed outcome, safe screenshot or recording where authorized, response/error category without tokens, retry count and cross-role session integrity. Minimum supported floor is the oldest tested combination passing all critical auth cases plus affected order flow; a failed older device only proves that tested boundary. Security-update lifecycle policy is a separate owner decision, not silently imposed by this audit.

## Administrative MFA and recovery — separately open

Use dedicated synthetic admin/restricted-finance fixtures only; do not change protected five passwords/factors or production. Required live cases: enrollment verified by user, AAL1 denied sensitive RPC/files, AAL2 allowed, wrong/expired/replayed OTP, concurrent verify clicks, multi-session revocation, lost factor with approved independent identity verification, recovery abuse resistance and post-recovery old-session denial. Customer email recovery must not become an admin MFA bypass.

Read-only source recovery review and4 offline cases passed: mismatched passwords do not call update; pending double click sends one update; failed update stays in recovery; success requests global signout then fresh login and surfaces incomplete signout. No MFA unenroll or privileged entry is invoked by that function. These do NOT establish mail delivery, provider recovery semantics, actual token revocation or lost-factor recovery. Supabase MFA guide: https://supabase.com/docs/guides/auth/auth-mfa . Platform dashboard MFA and application-user MFA are distinct; do not transfer platform recovery assumptions to app users.

## Specific unavailable evidence

- Physical older iPhone/Android devices or an authorized real-device lab are not available through this session. No compatibility pass/minimum-support certification can be produced yet; no paid lab activated.
- Synthetic factor is not yet verified; previous manual enrollment handoff remains pending. No repeated enrollment request issued for this scope clarification.
- Synthetic .invalid email is not a deliverable recovery mailbox. End-to-end email recovery requires a controlled test mailbox configured through a secure channel; do not send secrets in chat or change protected account addresses.
- Provider/global Auth termination, restore and monitoring constraints remain in CURRENT-RESUME; this addition neither closes nor duplicates them.

Live .20 verification: existing customer session opened the complete customer home without MFA/QR; this is session reuse, not a fresh credential-entry or old-device test.
