# TALABOT — review continuation on .22

Date2026-11-07; application source4c78c739cd65c53746b07db6426cf5f66f178d8a; hosting32 confirmed current. No new application release in this continuation. Test project fsvrsvqfknogwmhccera only.

## Executed new cases
1. Same synthetic SQL session claims before and after finance staff deactivation and permission removal. Before execute=true; deactivated execute=false/financial rows0; active staff without finance permission execute=false/rows0. Complete transaction rolled back; fixture user count0. This tests current database authorization, not live HTTP session termination.
2. Current application WebRTC applicability review:22 source/build-input files including vendor JavaScript, zero WebRTC/peer/TURN/STUN/media API references; Worker source only embedded assets/CSP receiver; Supabase Edge Function list empty. Application has no WebRTC media/signaling service. V17.1.1–V17.3.2 (all12 V17 requirements) are not applicable to this version, not passed tests. Reopen on introduction of those services.
3. Fresh synthetic MFA state:0 factors,0 verified factors,1 session, roster1. No seed, code or token read; no enrollment performed.
4. Reconciled all345 requirement IDs and253 L1/L2 rows; none omitted. Current full-requirement counts331 untested,2failed,12not-applicable,0passed. Many rows have partial successful evidence, which does not close the whole requirement.

## Four requested workstreams — exact blockers
| Workstream | Valid existing evidence | What still prevents live acceptance | Required next action |
|---|---|---|---|
| Administrative MFA and recovery | Offline UI/recovery checks; SQL AAL gate; synthetic-only roster | No enrolled factor; .invalid mailbox cannot receive reset mail; no approved lost-factor identity-proofing process | User completes existing synthetic authenticator setup/code submission. Provide a controlled deliverable test mailbox, not a protected account. Define who can verify synthetic lost-factor recovery. Do not send seeds/codes/passwords in chat. |
| Real settlement/refund concurrency | Prior real overlapping wallet case; sequential valid-record refund/settlement and rollback; prepared two-connection scripts | Automatic approval reviewer rejected committed synthetic fixtures; uncommitted rows cannot be shared by independent DB transactions | Explicitly approve the exact persistent fixture manifest in concurrency21/README.md:3 users,1store,1auto-ID100TJS cash order,2tickets, retained60TJS test refund and5TJS settlement receipt/audit,1pilot daily admission; test only, no money. Do not retry rejection without this decision. |
| Actual backup restore | Provider Free-plan limitation observed; restore runbook prepared | No verified full DB+Storage backup artifact, separate target or secure direct DB connection available; restore_project means resume a paused project, not backup restoration | Designate an existing disposable restore target distinct from test/production. Then provision its connection through an available secure mechanism; never reset protected DB credentials or paste a secret in chat. No paid branch/project activated. |
| Incident alert receipt | Auth audit/log queries and safe aggregates; bounded CSP receiver | No approved receiver/channel, delivery integration or retention guarantees | Specify one authorized email/channel and recipient for a clearly labelled synthetic incident notification; configure that receiver through provider-supported secure settings, then test receipt/acknowledgement. Logs alone are not receipt. |

## Other matrix rows remain open
Encoding/sink coverage; remaining validation/business logic; full browser/API controls; server file content validation; full authentication/token/session lifecycle; complete record/role authorization; relevant cryptography and transport; provider configuration; data lifecycle; architecture/dependency provenance; logging durability and incident response.
These are NOT all external blockers. Some are unfinished technical verification. Do not report the audit complete or say all available work is exhausted based on this checkpoint.
Customer MFA exception remains the owner's decision: no QR/authenticator/new condition introduced for customers. V6.3.3 remains failed/open with the need for a documented scope/rationale, not silently waived.
V7.4.2 remains failed/open: synthetic-only revocation and guards do not establish global session/Realtime termination.
Historical signed-URL survival until expiry remains distinct from denial of new signed URLs.
Old-device/weak-network compatibility remains untested until physical-device evidence.

## Preservation
.21 accountant revoked-session repair and proof access evidence retained without rerun; .22 request-ID compatibility repair retained. No protected users/passwords/orders/receipts altered, no financial operation committed, no production access or internal-route activation.
This document is a truthful checkpoint and consolidated gap report, not final security acceptance or an independent penetration test.

## Additional bounded injection/SSRF source review
Inspected dynamic SQL/outbound-database calls in public and the five application private schemas. The single executable dynamic SQL site is check_promo: a constant SELECT with USING p_store, not concatenated user SQL. finance_access matched the JSON key execute only. No http/pg_net/dblink/postgres_fdw extensions were installed. Worker has no outbound fetch, and Edge Functions inventory is empty. This is bounded source/config evidence for V1.2.4 and V1.3.6, not a complete runtime pass.
