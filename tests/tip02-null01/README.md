# TIP-02-NULL-01 — isolated owner-decision delta

Base:2665c4cdf51a86b08f3b87eab18a68271c9da3c5; TIP02 code9d9139ef6564b3ab17bcee8ffc2c5d736d039e52. Apply acceptance.sql AFTER TIP02. Historical files remain unchanged.

The sole executable change is the new-request guard: explicit NULL now raisesbad_value. Default0 is unchanged. Both prior-key lookups, current authorization, locking and the closure check precede this guard. No HMAC/payload, financial, ACL, isolation or client change. The existing coalesce at storage is unreachable for a new NULL; historical replay returns before this point.

## Local verification

Use a NEW disposable PostgreSQL17.6 UTF8 cluster with pgcrypto/psycopg3, listening on127.0.0.1:5432. The inherited fixture creates/drops candidate103 and creates synthetic authentication roles. Do not use an application cluster. Set PGUSER to its local owner.

```sh
export TIP01_ISOLATED=yes TIP02_ISOLATED=yes TIP02_NULL_ISOLATED=yes
export PGHOST=127.0.0.1 PGPORT=5432 PGDATABASE=postgres
TIP02_NULL_BASELINE=yes python tests/tip02-null01/native.py # expected4 subcase failures before fix
python tests/tip02-null01/native.py
CANDIDATE_CORE=PATH_TO_UNCHANGED_TIP02_CORE node tests/tip02-null01/client.test.mjs
```

Expected:11 PostgreSQL delta groups;3 client-controller groups with synthetic RPC. Build unchanged TIP02 core with its own build-client.py and the input hashes pinned by103. Do not rerun the entire accepted TIP01/TIP02 suites for this delta.

Cases include four entrypoints, omission versus0 versusNULL, bound/unbound historical NULL, same-key mismatch, other-account/auth checks, closures, NULL/0 concurrency, actual TCP loss before/after rejection COMMIT, historical NULL ACK recovery, all106 isolation levels, recovery-only rollback/re-upgrade. Rejection has no order/spend; public104 records a closure only when the existing resource policy permits it. No invented closure when resources are unavailable. The unchanged legacy wrappers retain their established error mapping; do not infer a closure from a generic error.

During recovery-only rollback, the creation wrapper may returnrollback_read_only for a closed request; its closure remains accessible throughorder_request_status104 and survives re-upgrade. Writers must remain quiesced. No downgrade to pre-decision creation functions is approved.

No hosted SQL/HTTP or remote CI. No new browser/Safari proof. Independent QA must review this delta before operational acceptance.
