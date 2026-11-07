# Continuation .18 — bounded offline evidence and narrow persistence repair

Baseline HEAD: `2491da72befb3bffcfc7d7a9ebb902a2173fd868`. No live sessions, DB, network, deployment, protected orders/accounts or production used. Parent explicitly authorized the two narrow source edits after evidence. Parent owns build/integration/deployment; no whole ASVS requirement is closed by this packet.

## Confirmed local persistence and repair

Actual SDK `_saveSession` with synthetic data serializes `access_token`, `refresh_token`, expiry/type and `user`; synthetic user retains id, email and user_metadata. Actual SDK `_removeSession` clears its own auth keys but leaves app approval/cart keys. The source auth event handler clears proof blob URLs on SIGNED_OUT and does not clear those persistent app entries. This adds concrete partial evidence to V14.3.1/V14.3.3; the SDK session-token exception does not itself classify all user metadata as acceptable. No SDK storage changes made.

Actual `approvalWrite` persisted the full JSON argument object inside a localStorage key, including merchant note and item list. Actual `cartLoad` ignored expired/malformed/invalid cart data without deleting it. Synthetic evidence: storage.json, storage.cjs. Never printed real credentials or personal records.

Authorized repair:
- `public/talabat-core.js`: approvalWrite computes a SHA-256 argument fingerprint; uses it in the persistent key. On retry of existing old-format data, it copies the existing request UUID to the hashed key before removing that exact plaintext key. Identical args retain the same request; changed args get another request; storage-write failure preserves legacy key and sends no RPC.
- `public/customer.html`: existing invalid/expired branch now removes the stored cart. Current carts and the approved24-hour acceptance window are unchanged.

Regression: baseline3/9, repaired9/9; core syntax check passed. Files persistence-before.json, persistence-after.json, persistence-regression.cjs, persistence.patch. Existing unrelated tests were not repeated.

Limits: hashing is not encryption or a complete privacy guarantee for low-entropy inputs. Historical old-format keys for other argument sets remain until their exact retry migration; no broad destructive cleanup was authorized. Current carts intentionally retain notes/item choices for their existing retention period. Expired entries are removed when cartLoad runs; no background deletion guarantee. No full V14 pass and no new shared matrix status change is proposed.

## Uncovered renderer checks

Ten new offline cases passed for actual finance-receipt HTML and driver map-query builder. Receipt fields tested closing-title/script, attribute/image-handler delimiters, entity/quote/backslash/Unicode separators, javascript string and non-Latin text; parsed result introduced no script/image/iframe/object/embed/SVG or handler attributes. Driver location text remained one correctly encoded query value on fixed HTTPS Google origin, with no injected extra query/hash. renderers.py/json. This is limited V1.2.1/.2/.3 evidence, not all-sinks acceptance.

sink-inventory.json contains566 candidate locations across first-party files (text assignment, HTML assignment, dynamic handlers, interpolated URL attributes and navigation APIs). It is a searchable location inventory, not an AST-complete sink inventory or proof of data provenance. Fixed UUID/enum handler inputs must not be called exploitable based on syntax alone. Further manual provenance work is required.

## Worker path behavior

23 offline requests exercised real built Worker with percent/double encoding, query/hash delimiters, NUL, CRLF, backslashes, Unicode punctuation, dot segments and non-assets. worker-paths.mjs/json.

Observed: encoded single-dot extension canonicalizes; encoded letters resolve normal public app shell; browser-standard URL parsing resolves ordinary/percent-encoded dot segments before Worker receives pathname; double-encoded slash/dot sequences and encoded path separators do not get decoded twice to another route; unrecognized metadata/source paths return404. Canonical redirect remains relative and encoded CRLF query stays encoded. No external redirect/header injection or unexpected source-file disclosure in these cases. These are specific routing observations; role HTML shells are public and backend authorization remains independent. Full V1.1.1/V1.5.3/V13.4.1/V13.4.7 acceptance not established.

## External resource inventory

external-destinations.json and storage-inventory.json contain locations, not secret values. Runtime external destinations found:

| Destination | Role | Existing control / limit |
|---|---|---|
| jsDelivr Leaflet1.9.4 JS/CSS | Executable/style assets | Exact version and integrity/CORS attributes present; no network revalidation here. |
| OpenStreetMap tile service | Coordinate-indexed image tiles | Dynamic tiles, no SRI; referrerPolicy origin. Need documented exception/trust decision per V3.6.1 and data disclosure classification per V14.2.3. |
| Google Maps | User navigation | Fixed HTTPS origin and encoded/numeric parameters at reviewed builders; carries location/address when used. |
| Supabase test host | Auth, API, Realtime, storage | Application backend; managed response/control coverage remains separate. |
| www.w3.org | SVG namespace URI | Namespace text, not evidence of a network request. |

No external webfont loader found in first-party textual source. Dynamic database-supplied image URLs mean source literals cannot enumerate every live destination; broad `img-src https:` allows remote image hosts. No claim of tracker absence or all-assets SRI acceptance.

## Remaining work

Prioritize provenance review of dynamic handlers/URLs from sink inventory, complete browser storage data classification, safe migration strategy for dormant legacy approval keys, browser termination/DOM/Realtime cleanup and backend/upload bypass controls. Current note/cart retention policy should be agreed explicitly before changing it. Provider response and browser behavior remain outside this offline packet. Continue existing acceptance plan; do not change341 untested/four failed based solely on these narrow checks.

## Follow-up: migrate dormant approval keys at authenticated load

Parent authorized scoped migration after the initial repair. `migrateApprovalKeys(userId)` now runs immediately after the authenticated profile resolves and ME is assigned, before the application becomes ready. It snapshots only the current-user approval prefix; permits only the two known approval operation names and decimal revision; requires an exact serialized JSON object and a valid stored request UUID. It hashes the original argument bytes, saves/verifies the same UUID, and only then removes that exact plaintext key. Every matching dormant argument set is visited; no matching retry is required.

Existing valid hashed UUIDs are not overwritten. If hashed and legacy entries conflict, both are preserved and approvalWrite returns approval_unavailable for that conflicted operation; it does not issue a potentially ambiguous mutation or erase a pending UUID. Malformed JSON, invalid UUIDs, unknown operations and other users' entries are left untouched because safely reconstructing their intent is not established. A changed current identity stops migration. Failed writes retain the original entry.

Migration regression7/7; original persistence suite9/9; extracted authenticated-load sequencing test1/1; core syntax valid. Files migration-regression.cjs, migration-results.json, migration-load-order.cjs/json, persistence-after-migration.json. Parent owns browser/build/deploy verification. This supersedes the earlier limit that well-formed dormant keys wait until their exact retry. Malformed/conflicting keys can still persist and require explicit safe reconciliation; no broad deletion or all-storage privacy claim.
