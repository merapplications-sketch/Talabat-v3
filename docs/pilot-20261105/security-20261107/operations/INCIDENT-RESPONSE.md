# TALABOT incident response — candidate, not exercised

Prepared 2026-11-07. Local documentation only; no external actions performed.

## Immutable exercise boundary

Only Supabase `fsvrsvqfknogwmhccera` and `https://talabot-isolated-safari-20261106.alwarikahtan.chatgpt.site` are in scope. Current coordinating-reviewer baseline: .19 source `fd665456d30eb28612c13da93df7e6d71da9ec94`, hosting29, deployment `appgdep_6aef2b64e05c819181b2d2aa9a925f1b`, succeeded2026-11-07 13:45:27UTC. Customer and merchant sessions observed working per root. Consult `../CURRENT-RESUME.md` before any exercise; verify source/deployment/DB mapping again at kickoff. This document does not independently establish runtime controls. Production `dzydscryrnahnneydnry` is prohibited, including reads, key rotation, restore, deployment and traffic. Any project mismatch means STOP.

Protect orders #1/#2/#3, their amounts, states, receipts, proof objects and settlement fields. #1/#2 retain their original settlements; #3 remains delivered and unsettled with recorded platform due 5 TJS. Receipt count last reported: 2. Do not use these orders as fixtures or compensate against them. The five existing role accounts and their credentials are protected. Existing fixtures 901/902 are historical, not blanket permission for reuse.

## Evidence and capability limits

- Test dashboard reports Free Plan does not include project backups. No current restore was performed. Historical restore references do not establish current recoverability.
- Managed Cloudflare zone was inaccessible to the connected account. DDoS/WAF coverage, direct Supabase endpoint protection, enforceable cost caps and delivered on-call alerts are unverified.
- Database blocked-account policies and session-hook evidence are narrower than complete Auth revocation. REPORT leaves V7.4.2 open; do not assume banning, frontend logout or key rotation ends every existing access token, signed URL or Realtime subscription.
- .19 adds a locally tested bounded CSP receiver and sanitized console emission. Curl verifies customer200/core200/missing404 CSP/report-uri and report POST204; earlier urllib403 is a client-path limitation. Browser-automatic delivery, provider responses and durable retention remain unverified. Logs completeness, retention, tamper resistance and external delivery are not established. Never put tokens, passwords, full signed URLs, precise GPS or customer data in an incident ticket.

## People and initial actions

Before a live exercise, name an incident commander, Supabase administrator, hosting/provider contact, independent evidence custodian and notification recipient. Names/channels are currently UNASSIGNED; notifications have not been tested. An unreachable owner is an escalation gap, not proof of automated coverage.

For a suspected event: record UTC discovery time, reporter, symptoms, affected endpoint/project and last-known-good deployment. Verify project identity using a read-only provider view before every administrative action. Preserve redacted request IDs, deployment identifiers, relevant audit-log ranges and object metadata. Hash downloaded evidence and restrict access; keep originals separate from analysis. Record all actions with UTC start/end, actor, scope, result and reversal plan. Do not delete logs or “clean up” suspected attacker artifacts before preserving evidence.

Severity: suspected privileged credential theft, unauthorized monetary writes or cross-tenant exposure is critical; loss of isolated-test availability or synthetic data is high within this exercise. Actual user data exposure or a production indicator triggers STOP of testing and owner escalation, without probing production.

## A. Suspected secret or privileged key leak

1. Identify the credential class without copying its value: publishable/anon identifier, user token, service-role/secret key, signing key, repository token or provider-account credential. A public anon key alone is not proof of a privileged leak; assess its permissions and RLS exposure.
2. Preserve location, first/last exposure times, affected commit/deploy IDs and a safe fingerprint. Search authorized test source/history/log locations for that fingerprint. Do not paste the credential into a scanner or chat.
3. Commander chooses containment appropriate to confirmed capability: restrict affected test endpoint or revoke the specific compromised credential using the provider-supported workflow. This plan does not authorize global rotations, paid services or managed-zone changes. Verify all affected consumers before replacement; prepare a rollback that never restores a compromised secret.
4. For service credentials, investigate bypass-RLS access and unauthorized writes. For signing credentials, inventory token lifetimes and issuer verification behavior; provider rotation semantics must be confirmed before claiming old tokens invalid. For repository/provider tokens, revoke token and inspect sessions, CI secrets, deploy hooks and access grants.
5. Update authorized consumers through the secret manager, deploy a reviewable test build, and verify normal least-privilege access. Independently verify the old credential is rejected through each applicable API, not merely removed from source. Never test privileged credentials against production.
6. Compare synthetic ledger/order/storage snapshots and inspect access logs for the exposure interval. Missing logs means exposure extent is UNKNOWN. Document retained tokens/signed URLs and residual access until measured expiry/revocation.
7. Close only with replacement success, old-credential rejection evidence, consumer inventory, integrity reconciliation and named owner acceptance. Rotate/revoke history and notification evidence remain required.

## B. Suspected account compromise

1. Determine whether this is a dedicated application test identity or a Supabase/GitHub/hosting provider identity. Preserve login/session/permission-change events and verified subject IDs; no password or recovery-code collection.
2. For a dedicated app fixture, contain via the authorized active-account guard and provider-supported session revocation. Record these as separate controls. Do not ban protected role accounts merely to simulate an incident.
3. For a provider identity, the authorized account owner secures the account, revokes suspicious sessions/tokens, restores approved membership and reviews recovery factors/CI access. Do not claim app RLS contains a compromised provider administrator.
4. In a controlled fixture, test two independent sessions: old access token, refresh, Auth user/MFA APIs where applicable, REST/RPC, Storage bytes, prior signed URL and existing Realtime subscription. Test during disablement and after re-enablement. Failure on one route does not establish global revocation.
5. Use a controlled mailbox/factor for recovery and MFA. Confirm fresh login works only under intended policy and old sessions do not silently regain access. Do not reset existing account passwords or send unsolicited recovery email.
6. Reconcile permissions, synthetic monetary records and data changes during the incident interval. Preserve suspicious changes before any approved correction. Close with demonstrated lifecycle behavior, owner communication and remaining-token exposure explicitly stated.

## C. Data loss or corruption

1. Confirm scope using read-only evidence. Record affected tables/objects, UTC last-known-good time and suspected writes/deletes. Stop further authorized synthetic writes; do not delete or restore the current test project.
2. Inventory recoverable artifacts: database snapshot/export timestamp, role/schema/RLS/functions/extensions, migration source, Auth recovery method and Storage object manifest plus actual bytes. Database export alone must not be treated as a complete Storage/Auth/provider backup.
3. Current gate: no verified backup or approved separate target exists in this handoff. If no recoverable artifact is found, report recovery capability UNKNOWN and escalate; do not invent a restore point or recreate financial history from UI totals.
4. Obtain an explicitly designated disposable restore project distinct from both the current test project and production. Confirm isolation, outbound-email/webhook disablement and authorized access before importing anything. No paid upgrade is implicit.
5. Restore using the provider-supported method appropriate to the verified artifact. Record tool/version, artifact hash, UTC start/end and all errors. Do not change DNS or point the live test application at the restored target during the drill.
6. Validate schema/migrations, RLS and grants, Auth behavior, Storage bytes/access policy, row counts/checksums and ledger invariants. Compare protected #1/#2 settlement snapshots and #3 unsettled state read-only. An available login page is not recovery acceptance.
7. Calculate measured recovery time from declared outage to validated service recovery; calculate recoverable-data gap from latest validated artifact to incident time. Record excluded services and manual steps. Cutover, if later authorized, needs a separate concrete plan and rollback criterion.

## Proposed objectives — UNAPPROVED and UNMEASURED

| Objective candidate | Proposed target | Evidence needed before commitment |
|---|---:|---|
| Database and linked Storage recovery point | RPO ≤24 hours | Protected, consistent scheduled artifacts; verified coverage of database and object bytes; restore validation |
| Isolated service recovery | RTO ≤8 hours | Timed separate-target restore, dependency configuration, integrity and access tests |
| Suspected privileged compromise triage | ≤30 minutes from alert receipt | Named staffed owner and actual delivered alert drill |

These are discussion targets only, not current guarantees, SLA or observed performance. No automatic backup, cost ceiling, WAF rule, notification or on-call rotation is created by this document.
