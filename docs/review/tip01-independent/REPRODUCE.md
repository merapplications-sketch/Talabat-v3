# Independent TIP01 QA reproduction
Candidate: bcf651a7784617545354d2c6d7fe3d74d026c611.
Evidence parent: c7b6ce68555c1ec71169d94119129f3c11ebed73.
Reviewed base: 86eb978e1aeb2be4a9d90999dc9b5a1267cb33df.

Use a NEW DISPOSABLE local PostgreSQL17.6 UTF8 cluster, with pgcrypto and psycopg3, accessible only via127.0.0.1:5432.
Do not use an existing application cluster. No hosted credentials, service keys or real data are needed.
The harness creates/drops candidate103 and creates qa_tip_restore. Authentication roles/claims and all ledger data are synthetic.
The retained fixture has deliberately simplified delivery/Happy Hour/settings and only selected constraints; it is not a Supabase catalog replica.

From the repository root of this review commit, with the new disposable server running:

```sh
mkdir -p runtime
export PGHOST=127.0.0.1 PGPORT=5432 PGDATABASE=postgres
export PGUSER=YOUR_DISPOSABLE_CLUSTER_OWNER
export TIP_QA_LOCAL=fresh-cluster
python docs/review/tip01-independent/independent_review.py
```

Use a local cluster owner that already exists. This is NOT an instruction to change hosted users/roles.
Expected result:16/16 independent groups, with48 matrix creations and48 replays among those groups.
The baseline case explicitly verifies the pre-fix20→0 behavior before applying the exact candidate.
The tests intentionally use wallet7, menu37.35 and discount10% in selected cases, distinct from the programmer's principal20/5 example.
The TCP cut helper and fixture setup come unchanged from pinned106; assertions for this review are in independent_review.py.
No entire106 regression suite is loaded into the test runner; only methods defined by QA are selected.

The test writes qa-results.json and a PRIVATE runtime/qa-private-synthetic.dump. The dump contains synthetic signing material:do not publish it or treat it as operational backup evidence.
Keep the temporary server alive for this invocation and stop it afterward.
The review run reused available local PostgreSQL binaries and psycopg; no package installation or browser launch was performed.

Complete-definition static check:
extract from CREATE OR REPLACE FUNCTION security_private.create_order103 through end $function$; in106/isolation.sql and tip01/acceptance.sql.
Replacing the one old p_tip membership expression must make the196-line definitions byte-for-byte equal.
The recorded before/after SHA256 values and every reviewed Git blob are in qa-static.json.

The review did not rerun the programmer's23/46/4/15/3/5 suites wholesale. Their pinned source and saved logs were audited; independent runtime results are only those in qa-results.json.
Browser/IndexedDB, hosted HTTP/RBAC, live finance/delivery, provider backup/Storage recovery, actual Safari and production migration remain outside this reproduction.

