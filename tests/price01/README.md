# PRICE-01 baseline probes — no repair yet

These new tests reproduce the approved checkout-price problem on the accepted TIP02/NULL01 source. Passing a probe means its observation/control is reproduced; **it does not mean price protection passes**. Existing candidate source and accepted tests are unchanged.

Use a dedicated disposable local PostgreSQL17.6 cluster on127.0.0.1:5432, with pgcrypto available. The retained harness recreates database `candidate103`; never use a shared/hosted cluster. No real IDs/data/settings are required.

```sh
TIP01_ISOLATED=yes TIP02_ISOLATED=yes TIP02_NULL_ISOLATED=yes PRICE01_ISOLATED=yes \
PGHOST=127.0.0.1 PGPORT=5432 PGDATABASE=postgres PGUSER=agent \
python tests/price01/baseline_probe.py

# Generate accepted client with its original pinned input files; generator checks hashes.
python tests/tip02/build-client.py /path/to/pinned-inputs /path/to/generated
PRICE01_CORE=/path/to/generated/talabat-core.js node tests/price01/client_probe.mjs
```

`PRICE01_RESULT` chooses result path. `PRICE01_CASES` selects exact comma-separated native test method names; `PRICE01_CASE` selects a client case name prefix. Only price-specific probes execute; imported accepted suites are not automatically run.

Recorded runs and the exact source hashes are in `docs/review/price01/`. PostgreSQL uses real transactions/TCP; fixture and settings are synthetic. The client probe uses Node VM and mocked RPC/store, not a real browser/IndexedDB/Safari. No Supabase or deployment.
