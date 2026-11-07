## Root-confirmed continuation .19

All18 additional function retests passed; results-four-more-after.json completes the final four. Added helper-account-guard-fix.sql (migration pilot_revoked_session_permission_helpers): is_admin, has_perm, owns_store and my_perms now consult account_enabled. Before/after evidence uses only rollback synthetic actors. Revoked and required-MFA AAL1 claims previously retained helper permissions despite enabled=false; now deny. Active/AAL2 controls preserved. No raw HTTP/Realtime bypass claim. Original helper test confirmation expired twice; safer revised test tests active first and never deletes a revocation row. No global session revocation change. Cleanup-protected-19.json confirms fixtures/revocations/MFA rows0, protectedorders unchanged.

# Recovered RPC continuation evidence

Filesystem was reset. The JSON evidence here was recovered verbatim from surviving tool-store memory. proposed-all10-fix.sql was regenerated from a fresh read of all ten live function definitions; all ten were still unguarded. No DDL was executed by this agent. retest-all10.sql was reconstructed from original SQL and incorporates the validated clean-fixture corrections, synthetic driver allowlist, and the tenth threshold test. It has not yet been executed after recovery.

Only isolated project fsvrsvqfknogwmhccera. Synthetic UUID prefix 91000000. Each operation uses a sentinel-rolled-back subtransaction; fixture transaction ends ROLLBACK. No actual credentials, Auth sessions, protected account/order writes, file content, production, or DDL. Pilot allowlist adds only synthetic customer/store/driver IDs within rollback. Previous baseline and cleanup config hash: 33a73d3ef161a8677756d89717ce5c49. Previous cleanup found zero fixture users/stores/orders/groups/requests; sequences may advance on rollback.

These authenticated SQL role tests do not prove HTTP bypass. Existing pre_request barrier blocks disabled accounts at HTTP; findings are defense-in-depth gaps.

With app.bypass cleared before EVERY RPC and account_enabled=false, disabled actors successfully called group_get/add/remove/set, request_store, my_offers, my_rating, driver_accept, driver_decline, set_my_free_delivery. All ten had positive active-account controls. Returned group snapshots proved add/remove/status mutations; driver_accept returned true after assignment; decline state observed as declined; rating seeded5/count1 and offers included seeded order; store request returned UUID; free delivery threshold observed as123 on synthetic store only.

Cross-user group_remove/set rejected not_allowed; offers returned[], rating count0; non-driver accept rejected not_approved; foreign store threshold write rejected not_allowed. Share-link group get/add behavior was not classified as IDOR. Disabled driver_ping/location rejected not_allowed while active controls succeeded; these unchanged functions are excluded from retest.

Authoritative pre-fix evidence: results-clean.json, results-driver-accept.json, results-store-price.json. rollback-verification.json is the earlier cleanup proof. Proposal changes only account_enabled guard at PL/pgSQL entry or SQL WHERE filter, preserving business rules.

## Post-fix retest

Parent applied pilot_remaining_disabled_rpc_guards. Reconstructed retest-all10.sql executed successfully: all ten active controls preserved, eight disabled PL/pgSQL calls rejected account_blocked, disabled my_offers returned[] and my_rating returned avg=null/count0. Cross-user ownership controls retained. Authenticated role and account_enabled status captured per probe. Cleanup again found zero fixtures and the same config hash. This closes these ten direct-SQL defense-in-depth findings; it does not independently validate actual HTTP authentication or all remaining RPCs. Evidence: retest-all10-results.json, retest-assertions.json, retest-cleanup.json.
