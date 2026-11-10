# Batch102 — cumulative SQL repair candidate, NOT live deployment

Base a3cf44e83175c544df60b1f2d06bce3404f76ca3. Prior tests b740a3ac0227eabcfc3d5b12c8f321a499eed921. Independent QA rejects92/96/98 pending repair. This candidate requires renewed independent review and owner authorization before any application. No production state, accounts, MFA, protected orders or settlement changed.

## Reproduction and repair
The new replay tests failed against exact SQL98 with bad_group and bad_time. SQL NULL reached a NOT NULL violation under the corrected fixture; no target empty-order/live debit claim is made. Another red control confirmed old SQL98 returned the same ID for a changed quantity.

Candidate: tests/native102/candidate.sql (old92/96/98 files remain unchanged).
- Require authenticated/enabled identity first. Parse schedule syntax but defer moving time-window validation until after recovery.
- Retain group row lock BEFORE key advisory lock and profile lock. Check current group host and store before recovery. Defer mutable group status/expiry to new-operation admission. Recovered group must still link to the same order.
- Keep caller/key-scoped lookup. NEW private order_request_bindings records all twelve typed request arguments excluding the separately scoped key, using JSONB exact equality. Binding and order/financial effects commit or roll back together. No price-based reconstruction, truncated field comparison or invented historical bindings.
- A mismatch rejects with idempotency_mismatch. Existing key without verified binding rejects with idempotency_unverifiable. This intentionally tightens the prior changed-payload replay behavior; independent reviewer must assess compatibility and a separately approved legacy recovery plan. It is not silently deployed or claimed compatible with every historical request.
- NEW keys still undergo time40minutes..3days, group open/closed+expiry, payment, profile-serialized open5/hour20 and all downstream business checks.
- Candidate callers serialize before lookup; a unique violation from an unrelated constraint or an uncoordinated legacy writer is rethrown. Never return a cached ID through an exception path that bypasses binding.
- SQL NULL/non-array items fail explicitly before insert. No weakening of target constraints.

## New relation / rollout prerequisite
security_private.order_request_bindings has caller/key primary key, unique order FK, non-null JSONB request, RLS enabled with no public client policy, and client grants revoked. It stores potentially sensitive request content and must remain private in database/backups/logs. Source code and synthetic reports contain no real request data. CREATE deliberately fails if the object exists: review schema drift; do not auto-overwrite it.
The migration is NOT authorized live. Confirm schema ownership, CREATE privileges, owner rights/ACL preservation, execution grants, target snapshot and retention/legacy policy with QA. Old keys cannot safely be backfilled from lossy order rows. Rollback must preserve binding data privately; restore exact prior function/ACL only with separately approved ingress pause/outcome reconciliation. Dropping the table or restoring known races is not release acceptance.

## QA03 fidelity
constraints.sql derives selected existing-column NOT NULL/default clauses from the independent2026-11-10 catalog, including subtotal NOT NULL DEFAULT0. It is a fixture overlay, not a production schema change. Synthetic id types, text instead of enums, absent columns/policies/triggers and minimal tables still prevent full equivalence. Target evidence stays private; only reviewed structural clauses are included publicly.
Original declaration of delivery_calc/happy_hour dependency doubles remains. Captured cash snapshot/guard and fulfillment registration execute locally; synthetic_end_failure injects rollback. Promo/loyalty full paths, every deployed RLS policy/grant/trigger, authentication provider, inventory and live scheduling guard are not proved. Schedule tests exercise the general candidate body without enabling scheduling in the hosted environment.

## Review evidence instructions
Run node --test tests/native102/replay.test.mjs with PGLITE_MODULE pointing to pinned @electric-sql/pglite dependency. This is embedded PostgreSQL, not independent server connections.
CI102 additionally runs native.py on PostgreSQL17.6 with separate connections, real TCP interruption before/after COMMIT, one order/debit/binding invariants, group/scheduled contention, payload and new-key denials, lock timeout and a deliberately opposite-order caller deadlock. That deadlock test demonstrates a residual caller-order risk and recovery, NOT global deadlock freedom.
admission.py executes the original native98 four assertions unchanged with only fixture/candidate path substitution: open/hour limits, three keys and two accounts. Original95..100 suites remain unchanged and run separately. restore.py checks a separate synthetic restored DB including exact replay binding; not Supabase/Storage recovery.
Independent reviewer should rerun red controls against98, inspect102 delta and private catalog, independently test ownership loss, mismatches, legacy keys, limits and failure atomicity. Do not accept from this report alone.

## QA04 proposed enforcement (NOT applied)
Current branch read: review and main protected:false; GET /rulesets []. Managed connector lacks repository administration for protection writes. No settings changed.
Owner/admin proposal for release-target ruleset: require pull request and independent approval; disallow force/deletion; require fresh required checks on exact candidate SHA; restrict bypass actors; require branch up-to-date or approved merge queue. Validate check-context names and trusted GitHub App IDs from actual check runs before applying.
Public contexts: sql97 required, native96-required, CI99 isolated-public, CI100 public-tests, CI102 required102 (confirm names/app IDs, avoid ambiguous same-named contexts).
ADDITIONAL private checks must attest original db-evidence-binding and original build-gate, hosted RBAC, integrated four-role E2E, SQL independent acceptance, Storage revocation, provider restore, actual Safari. Do not configure non-existent contexts and call the work complete. First provision approved private runner with real original evidence and a trusted minimal result publisher; keep raw files/logs/artifacts private. acceptance100 is not an authenticated attestation nor a replacement for these checks.
Controlled acceptance trial must reject missing/failed/stale/private evidence and allow no bypass via green public CI. Owner approval required before repository rule changes.

## External dependencies unchanged
No new authorized HTTP user-session/private evidence channel, provider ticket response, restore target or physical Safari connection appeared. No repeat diagnosis or account/session creation attempted. HTTP99, Storage sameURL+sameToken GET/HEAD/Range matrix, E2E and recovery run sheets remain ready but unexecuted hosted. Full release acceptance remains BLOCKED even if all public suites pass.
