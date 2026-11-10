# SQL103 — review candidate, development / isolated tests only

Baseline source102:7297d5fcf2fcf21a844461fd132066c4b7660896; evidence:06e88ba2a5465eebb294a3bba17f5bd6f9dc4668. REVIEW102 accepts limited QA01/02/03 only; owner authorized historical read-only compatibility for103. No live SQL/deployment/main/protected-order changes. New SQL is under tests/native103; not a migration automatically invoked by any deployment.

## Recovery / result contract
`place_order103` keeps existing named arguments but returns `{status,key,id?,input_match?,reason?,contract_version?}`. IDs are decimal strings, avoiding JS integer precision loss. Legacy `place_order` keeps its bigint signature and delegates to103; non-success throws, never returns a null success. `order_request_status103(key)` is a pure read path: absence is `unresolved/not_visible`, never proof the previous transaction rolled back.

| Result | Meaning | Client behavior |
|---|---|---|
| created | New committed operation once caller transaction commits | Re-read own saved order; clear unchanged cart only on confirmation |
| replayed, input_match=true | Same identity/key and verified protected request fingerprint | Re-read saved order; no mutation |
| replayed, input_match=null | Status-only retrieval of a bound operation; current inputs were not compared | Re-read; preserve edited cart |
| historical_recovered | Original own saved order, no documented binding or new-version marker | Read only; input_match=null; preserve current cart |
| conflict | Bound request content differs | Keep key/data; never overwrite order or generate replacement key |
| unresolved | Missing evidence/key, not-yet-visible result, timeout/deadlock, transport or re-read failure | Read again; no automatic mutation retry |
| rejected | Current create invocation rolled back / invalid or unauthorized | Preserve data; not an automatic authorization to abandon an older attempt |

Authorization precedes every lookup. Saved group recovery checks the ORIGINAL group's current host/store/order link. It does not trust a supplied replacement group. History retrieval ignores supplied creation input without claiming equivalence, and does not insert a fingerprint. For new operations group->caller/key advisory->profile ordering remains; lookup is repeated after waiting. Same caller/key is serialized. Different-account lookup cannot return another account's ID.

`orders.request_contract_version=1` is written atomically with new103 creation. Missing new fingerprint therefore becomes unresolved rather than silently downgraded to history. Existing102 raw binding without conversion also stays unresolved. New requests require non-null valid keys; historical null-key operations cannot be recovered by an invented key.

## HMAC contract v1
Algorithm: pgcrypto HMAC-SHA256 using >=32 random bytes per immutable key ID. Domain-separated UTF8 payload:
`["TALABOT/order-create",1,customer_uuid,client_key,[store,items,tip,payment,address,lat,lng,promo,fee,wallet,points,extra]]`.
Fingerprint metadata stores caller/key, order FK, contract_version=1, key_id and 32-byte MAC only. No raw address, pin, recipient or cart is stored there. Canonicalization is executed by the server, not a client-supplied digest.

Canonical JSON rules:
- Object keys sorted with C collation; JSON escaping supplied by PostgreSQL.
- Array order retained, including item and option arrays. No sorting/deduplication of those arrays.
- PostgreSQL numeric values strip insignificant decimal scale; 1 and1.0 compare equally. Float8 uses extra_float_digits=3 at creation. No application rounding of coordinates or money added.
- ONLY top-level extra SQL NULL / JSON null / {} collapse to {}. Other nulls, missing nested properties, empty strings, false and zero remain distinct.
- Preserve strings exactly, including whitespace, address text, promo case and timestamp representation. No reconstruction from truncated fields, current menu prices or normalized saved order values. Semantically equivalent timestamps with different string forms may conflict by design.
- All twelve effective typed arguments are included conservatively. Unknown extra properties are included, even when current creation ignores them. UUID arguments are server-typed; strings inside JSON remain strings.
- Any different contract needs a separately reviewed version and verifier; do not reinterpret v1 records. Current schema only admits v1.

Keys: schema.sql contains NO key material and does not provision a production key. Tests use ephemeral random bytes only. Provisioning requires an approved owner/secret-management channel. Keys are in an owner-only RLS table, with no client policies; client roles and service_role direct table access are revoked when present. Database owners/backups remain trusted and can access key material: this is not an external-HSM/KMS implementation. Confirm target ownership, default ACLs, role inheritance and backup encryption before approval. Do not log payloads, MAC computation inputs, keys or raw DB dumps.
Rotation: insert a new random key ID; switch active flags atomically (one active key index). Old bindings verify with their stored old key ID, not the active key. Updating key material/ID in place is rejected; FK prevents deletion of in-use key versions. Never silently rehash an old operation using current inputs. A missing verification key yields unresolved.
Retention: no automatic TTL is implemented. Retain binding, marker and verification key for as long as replay of the corresponding order is supported. Owner must approve retention/backup access before live use. Removing a binding must not clear the version marker or make it legacy. Client payload is local, account-scoped, retained for unresolved attempts; known unchanged success clears it. A privacy/reset UX for unresolved local data requires an explicit reconciliation policy, not silent expiration.

## Transition / rollback plan
1. Independent QA inspects pinned candidate, private target snapshot and role/default grants. Confirm pgcrypto in extensions, trusted migration/function owner, all existing checks/triggers, keys provisioning and secret backup plan. Fail on unknown schema drift; no production permission implied.
2. Pause new ingress / drain old executions for deterministic cutover. Apply schema.sql + functions.sql + migrate102.sql in ONE transaction; key provisioning via approved private mechanism. An interrupted transaction must restore the previous valid schema/function state.
3. Existing98/no-binding orders remain untouched and recover read-only. Old clients still call the same public bigint wrapper. Do not run an unmanaged old function or writer beside103 and assume it verifies fingerprints: it cannot. Tests cover an in-flight98 writer winning, followed by103 recovery; they do not bless arbitrary bypass writers.
4. Existing trusted102 bindings: owner-only convert_bindings102_to103 verifies identity/key/order and original 12-field record, fingerprints it, sets version marker, then removes that raw record atomically. It never fabricates records for orders with no original binding. Conflicting/incomplete source stops conversion. Keep the private pre-migration backup; do not upload it. Conversion must be separately approved before live use.
5. Rollback.sql makes public creation recovery-only. It retains verified history, fingerprints, keys and markers, and still rejects mismatches. It DOES NOT restore98's unchecked replay behavior. Unseen keys return unresolved/rollback_read_only. Existing in-flight transactions must still be drained/reconciled.
6. Re-upgrade reapplies103 definitions and validates core shape/uniqueness/FK invariants while retaining records. This is not a universal schema drift reconciler: compare the complete target catalog separately.
7. Restore drill uses a distinct synthetic database and restores key+fingerprint together. Actual provider/Storage restore remains outside this evidence.

## Client candidate, without design change
build-client.py verifies source hashes and generates an isolated functional overlay from the recovered customer.html/core. Original144 export and deployed pages are untouched. No CSS/layout changes. New messages use existing alerts and RU/EN language selection; no preview is published.
The controller saves frozen payload/key before send, scopes it by account, permits one pending send, and keeps an account-level unresolved pointer even if cart code clears its key. A new key cannot bypass that pointer. Recovery runs before new group/time form validation. Explicit user-confirmed retry first reads status and resends ONLY the stored payload with the same key when not visible; no automatic fallback to the legacy RPC. A missing original payload cannot be resubmitted by guesswork.
Server success is followed by a scoped own-order re-read and order-list refresh. Malformed response, identity switch or failed re-read preserves data and reports unresolved. Historical recovery and edited carts preserve cart contents. Definitive rejection does not automatically mint a new key; editing/replacing a failed frozen request is not fully designed here and remains an independent UX/QA acceptance item.

Four-app impact: customer/shared core gets the candidate adapter; merchant, driver and admin source are not modified. They continue using persisted orders/status/receipts. Their end-to-end behavior with103 has NOT been proved. Controller/VM tests use synthetic HTTP/RPC responses and are not hosted RBAC or real-browser/device evidence.

## Catalog audit and remaining fidelity
REVIEW102's captured target has10 policies and17 triggers across five tables; fixture had0 policies and1 trigger.103 adds its marker trigger, not those17 target triggers. No claim of full target RLS/grant/trigger equivalence.
New fidelity.sql matches captured orders/wallet GENERATED ALWAYS identity, order_items UUID+gen_random_uuid default, and seven FK additions/replacements where referenced tables exist. Existing customer/store FKs and selected102 NOT NULL/default clauses remain. Missing driver_id/ticket_id/auth.users-dependent FKs, missing columns, text-vs-enum types, target ACLs/policies and transitive trigger paths remain unrepresented. Defaults/new relation constraints are locally checked, not verified against current live state.
Captured promo_eval/loyalty_balance/loyalty_spend bodies are exercised with synthetic minimal tables and explicit synthetic loyalty_setting. Their hashes are recorded. delivery_calc/happy_hour remain doubles. Wallet function and cash/fulfillment fragments are captured code, but target trigger closure is incomplete. Passing promo/loyalty tests does not validate hosted settings or all operations touching those tables.
Lock map retained: group->request key->profile->promo advisory / loyalty lots ordered expiry,id ->effects/fingerprint. Key rotation/legacy conversion requires drained ingress. A deliberately opposite-order caller can still deadlock;40P01/55P03 produce unresolved and require reconciliation, not a new key. No global deadlock-freedom claim.

## Independent review handoff
Re-run historical98->103 and102->103 conversion; mutate each fingerprint field; check null normalization, object/array ordering, key rotation/ACLs/privacy, binding-insert rollback, account/group access loss, missing/new marker behavior, mixed writer limits, TCP cuts, contention/admission, rollback/reupgrade and restored keys. Inspect the generated client overlay, including re-read failure and account/cart changes. Accept from independent execution and source review, not this report.

External blockers unchanged: original private DB evidence/build-gate, required GitHub release rules, approved hosted user sessions, four-app E2E, Storage sameURL+sameToken GET/HEAD/Range revocation and provider response SU-543851, provider recovery, actual iPhone Safari. No new access appeared; no repeated diagnosis or protected data access performed.
