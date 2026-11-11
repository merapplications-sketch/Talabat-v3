# PRICE-01 isolated contract candidate

Apply only to a disposable local PostgreSQL 17.6 fixture after the accepted
103 → 104 → 105 → 106 → TIP01 → TIP02 → NULL01 stack. This is NOT a hosted migration,
an operational activation script, or a replacement for the historical files.
Parent: `b75ff6d7df6911659c35296000317f5a1fcec983`.

`build-sql.py` derives the new creator/wrappers from the pinned original files;
`helpers.sql` adds strict version1 consent comparison. `candidate.sql` is the
generated output. Apply the complete file in ONE transaction. `rollback.sql`
retains recovery and closes all four creation entries; never roll back by enabling
an old unguarded writer. Keys, bindings and closures are retained.

## Build without running services

From repository root:

```sh
python tests/price01-impl/build-sql.py
python tests/price01-impl/build-client.py /path/to/pinned-input /path/to/local-output
```

The input has `public/customer.html` and `public/talabat-core.js`. Their SHA256
must match `tests/native103/ui-source-hashes.json`; the retained generator rejects
drift. Use the original pinned recovered input, not an arbitrary current app.
The output is an isolated customer/core pair; root operational app files are not
edited. No preview is published by these commands.

## Affected local tests

The harness imports retained fixture classes and functions, **not their full
accepted test suites**. Use a dedicated disposable local cluster with pgcrypto,
Python3/psycopg3 and PostgreSQL17.6. The harness drops/recreates its local database
`candidate103`; it is never suitable for a shared or hosted database. No real user
session or production secret is required; fixtures generate ephemeral key bytes.

```sh
TIP01_ISOLATED=yes TIP02_ISOLATED=yes TIP02_NULL_ISOLATED=yes PRICE01_ISOLATED=yes \
PGHOST=127.0.0.1 PGPORT=5432 PGDATABASE=postgres PGUSER=agent \
PRICE01_RESULT=/path/to/native-results.json python tests/price01-impl/native.py

CANDIDATE_UI=/path/to/local-output/customer.html \
CANDIDATE_CORE=/path/to/local-output/talabat-core.js \
RESULT_FILE=/path/to/client-results.json node tests/price01-impl/client.test.mjs
```

For a targeted rerun, `PRICE01_CASES` is a comma-separated list of native method
names; `PRICE01_CASE` is a client test prefix such as `PUI07`. For red reproduction
of native01..03 only, set `PRICE01_BASELINE=yes`; no historical file is changed.
For client red reproduction, pass the accepted TIP02-generated pair. Some newer
tests are implementation safety checks rather than baseline-bug reproducers.

The Node suite executes actual generated UI/controller code with simulated RPC,
localStorage and a serialized store. It is **not Chromium, IndexedDB or Safari**.
PostgreSQL is real; the schema, identities, delivery/HH settings and parts of the
dependency graph are synthetic. Selected promo/loyalty tests load the retained
public dependency definitions. No result proves Supabase target fidelity.

See `docs/review/price01-implementation/REPORT-AR.md`, `ACCEPTANCE.md`,
`COMPATIBILITY.md` and the evidence ledger before independent review.
