# Batch 99 — safe acceptance handoff

Base: `7b7bfe01eb1f3439e9a28a9114fbec03e4460519`, branch `review/ci-native95-20261110`.
The 144-file export is hash-verified, not a full checkout or proof of deployed equivalence.
Local reference `945623e50b9ed3d120897b90aa661890e394dfd6` remains unrecovered.
No production SQL, main merge, accounts, MFA, protected orders or settlement changes.

## Public CI

`ci99.yml` unpacks the original export and overlays only new test utilities. Original assertions remain unchanged.
`worker-fixture.mjs` embeds recovered assets and original Worker source using the original CSP function for headers/CSP tests. It writes NO release attestation, NO deployment manifest, and deletes its temporary dist output after tests. Passing this fixture cannot pass the original release gate.

| Group | Source | Local | Remote path | Limitation |
|---|---|---|---|---|
| headers | original export | 32 passing cases | ci99 | recovered assets only; no deployed equivalence |
| csp-report | original export | 8 passing cases | ci99 | local Worker runtime |
| qa-sessions52 | original export | pass | ci99 | mocked provider sessions |
| driver-permissions | original export | pass | ci99 | synthetic PGlite |
| order-transaction92-fixed | original export | pass | ci99 | captured SQL and declared doubles |
| http99 transport + integration | new | 11 passing cases | ci99 | real loopback HTTP, synthetic server |
| build-gate | original export | blocked ENOENT | blocked | missing .openai; private DB evidence also required |
| fixture-cache56 | test exported | blocked | blocked | missing functions/qa-proof-cache56/index.ts; never invent a replacement |
| db-evidence-binding | test exported | blocked | private only | original attestations and protected evidence unavailable |
| 18 SQL groups | original export | regression | sql97 | excludes hosted HTTP |
| 38 fast groups | original export | regression | sql97 | excludes db-evidence-binding |
| native95/96/97/98 + restore | remote branch | prior remote evidence | native95 | native PostgreSQL synthetic fixtures |
| hosted HTTP/RBAC | new runner ready | blocked | never auto-run publicly | authorized user sessions unavailable |
| full role UI E2E | acceptance scenarios below | untested | blocked | no browser/session fixture established |

CI green means all executable public groups passed; blocked groups remain explicitly blocked. Full release coverage is NOT claimed.

## Reproduce

From the pinned branch: `python3 ci97/unpack.py`, copy `scripts/ci99/*.mjs` and `tests/http99/*.mjs` into matching directories under `isolated97`, then run `npm ci --ignore-scripts --prefix isolated97/tests/dispatch-isolated`.
From `isolated97`, set PGLITE_MODULE to its installed absolute module path and run `node scripts/ci99/run.mjs /tmp/ci99-results`.
Run original `scripts/ci97/fast.mjs` and `scripts/ci97/sql.mjs` separately for regression. Native CI owns the pinned PostgreSQL service and synthetic restore.

## HTTP runner

Use `node tests/http99/run.mjs`. Without TALABOT_HTTP99_CONFIG it exits 2 with BLOCKED.
Configuration is an approved private regular file with mode 0600, never committed or logged. Fields:
- origin: exactly https://fsvrsvqfknogwmhccera.supabase.co
- approval: isolated-synthetic-fixtures-only
- auditAllowlist: verified-empty (must be established by the operator; not an assertion of server state)
- apiKey: approved public API key, not service-role credentials
- fixture: receiptOrderId string (greater than 3, explicitly reserved synthetic fixture), receiptAmount positive number matching that fixture
- sessions: finance/orders/outsider each with token and optional already-expired expiredToken

No tokens in command line or chat. The runner checks all three /auth/v1/user identities before mutation. It never creates, refreshes, revokes or disables sessions. Only own-profile PATCH, bounded known RPCs and verified identity routes are allowed. finance_audit is restricted to the finance identity to avoid exposing protected records if a server guard regresses. Its nonfinance HTTP rejection remains untested; the isolated SQL test provides separate evidence.

GET retries transport failure once. PATCH/RPC never retry automatically after a lost response. Deadlines include body reading; redirects are blocked; responses are bounded; reports exclude response bodies and credentials. Cleanup restores the original name and verifies the complete captured profile. A failed cleanup halts subsequent roles and requires operator inspection, not blind retry. Existing-expired-token tests are BLOCKED when no token is supplied. They do not prove active revocation.

## SQL 92 / 96 / 98 acceptance

SHA-256:
- 92: d150ecfcfad5db659d4150ea29bb5ad196d11c8ff8a1289b4b7c8ad082f5d6dd
- 96: 938448863e8208c605174642bd0ad8f5eba59531d2e293df43e9f70c9bb00021
- 98: e37d815eaaee6c0f85c18a6cbd166ced98ec9ac86dc4f940fcf2e3e9f4489204

96 adds transaction advisory lock per caller/key before lookup. 98 moves the profile row lock before admission counts. Existing-key replay remains before admission. Fixture uniqueness is (customer_id,client_key) WHERE client_key IS NOT NULL. Do NOT deploy 92/96 alone as a replacement for 98's admission serialization.
Group row lock precedes advisory key lock, then profile lock. Other business-path lock orders and group/loyalty/promotion branches are not globally proven deadlock-free. No live catalog equivalence was established. Independent QA must compare current definitions/indexes/triggers to these pinned inputs before approving any future application.

## Synthetic role journey acceptance (prepared, NOT executed UI E2E)

Use a reserved customer, merchant and driver plus a synthetic order outside protected IDs. No actual money:
1. Customer submits once, loses response, reopens; read the same order/key and one wallet effect.
2. Merchant confirms availability and preparation; customer accepts first-cash terms before preparation.
3. Driver accepts and picks up; enforce transitions and reject a second competing actor.
4. Merchant records return, driver confirms actual returned amount; remainder stays an open claim.
5. Read receipt as finance; orders and outsider cannot retrieve another actor's financial data.
6. Disconnect at each transition; read state before retry, never interpret an absent response as rollback.
For every step retain request class/status, before/after IDs and counts, actor role and cleanup result, never tokens or personal data. These scenarios need the complete application fixture and authorized sessions; the HTTP99 profile/finance runner does not implement the full journey.

## Recovery and rollback

Keep immutable source SHA and test hashes. Native CI dumps synthetic DB, restores into another database, checks uniqueness/replay/rollback. This is NOT provider backup restoration evidence. Provider restoration requires a separate nonproduction target and validated object-storage inventory. No reset, force push or live rollback is authorized by this handoff.

## S54-STORAGE-CACHE-01 / SU-543851

Status: OPEN / no new provider response available in this session. Ticket ID is a reference, not proof of a fix.
For each GET, HEAD and Range GET, use the SAME private object URL before/after revocation; no cache-busting query, URL change or object overwrite:
- authorized session: establish allowed baseline; repeat to warm cache;
- independently revoked test session: repeat the exact URL/method/range after server rejection is independently established;
- expired token and outsider: deny without object bytes;
- valid control session: retain expected access;
- GET Range: test valid and unsatisfiable ranges without allowing 206/body after revocation;
- HEAD: deny object metadata after revocation; a body-less 200 is not a denial;
- retain cache headers, status, body length/hash and timings privately; never credentials/object content.
Do not close on Auth getUser alone, Cache-Control alone, a new URL, or a mock. Account/session mutation remains outside this task; use separately authorized revocation evidence.

## Remaining gates

Private evidence channel, historical source recovery, hosted user-session RBAC, true role UI E2E, provider storage fix verification, provider recovery rehearsal, full live-definition equivalence and independent QA acceptance. No production readiness claim.
