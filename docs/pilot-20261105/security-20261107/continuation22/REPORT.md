# TALABOT continuation .22 — 2026-11-07

## Executed, not merely planned
Source 4c78c739cd65c53746b07db6426cf5f66f178d8a; hosting32; deployment appgdep_6aef4245e3288191a1d08a9323c9c3d5 succeeded2026-11-07T15:23:04.612543Z (20:23 Asia/Dushanbe).
Approved test URL unchanged. .21 finance repair evidence is retained in continuation21 and GitHub a30dbb216719f9c57a7a7f0d8003f64252054c8b; its successful tests were NOT repeated.

## F22-01: secure request-ID compatibility
Existing approval, return and finance paths called crypto.randomUUID directly. When that API is absent but getRandomValues/subtle exist, the extracted approval path returned storage_unavailable without sending the request. Failing pre-fix test captured that exact result.
Fixed only these three request-ID creation sites: native randomUUID when present, otherwise UUIDv4 generated from16 cryptographically random bytes, with version/variant bits set according to Web Cryptography. No Math.random/timestamp fallback. If secure randomness is unavailable, existing error handling sends no RPC.
The idempotency storage keys, request retention and accounting rules are unchanged. No dependencies or new login conditions.
Post-fix offline test passed: all three paths without randomUUID, same approval key on retry, same return key on retry, unresolved finance command blocked, native path works, missing secure randomness causes no network operation.
Syntax check, diff whitespace check and74-asset build passed. Publication succeeded. No real financial operation was executed.
This is capability-level regression evidence in Node VM. It is NOT a real old-phone compatibility test, weak-network test or end-to-end finance proof. Minimum supported device remains unapproved.
Specification: https://www.w3.org/TR/webcrypto/#Crypto-method-randomUUID and https://www.w3.org/TR/webcrypto/#Crypto-method-getRandomValues .

## New read-only database surface inventory
Test project fsvrsvqfknogwmhccera only.36 public relations inspected: no public views/materialized views, and no relation readable/writable by anon/authenticated with RLS disabled.
56 policies inspected. Twelve restrictive policies exist. Other tables rely on permission/ownership helpers, order visibility, pre-request checks or catalog-read policies. No conclusion that all paths are tested; RLS being enabled is not proof of correct authorization.
No table/policy/role/record mutation in this continuation. No repeated protected-order probe was needed because this continuation made no database writes.

## Unchanged open gates
Synthetic MFA enrollment/recovery manual step; full multi-session/Realtime termination; historical signed links; complete valid-object RPC matrix; server file-content validation; persistent-fixture concurrency approval rejection; provider controls; independent backup restore; actual incident notification receipt; real older devices.
Do not turn this report into whole-ASVS passes. Existing345-row matrix and prior failures remain authoritative. No readiness or independent penetration-test claim.
