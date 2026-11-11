# TIP-01 isolated acceptance

Base: `86eb978e1aeb2be4a9d90999dc9b5a1267cb33df`. Apply only after103→104→105→106. `acceptance.sql` changes one accepted-tip membership expression; never edit the historical overlays. GC-05 remains open.

## Reproduce locally

Use a **new disposable PostgreSQL17.6 UTF8 cluster** with pgcrypto, listening only on127.0.0.1:5432, and psycopg3. These inherited harnesses create/drop `candidate103` and `native98`; restore uses `tip01_restore_source` and `tip01_restore_target`. Do not point them at an existing application cluster. Run from repository root. Set PGUSER to the local cluster owner. No hosted credentials are needed.

```sh
export TIP01_ISOLATED=yes PGHOST=127.0.0.1 PGPORT=5432 PGDATABASE=postgres
TIP01_BASELINE=yes python tests/tip01/native.py # expected four tip20 failures on106
python tests/tip01/native.py
python tests/tip01/regression.py
python tests/tip01/admission.py
PREPARE_RESTORE=1 python tests/tip01/restore.py
pg_dump -Fc tip01_restore_source -f /private/local/tip01.dump
createdb tip01_restore_target
pg_restore -d tip01_restore_target /private/local/tip01.dump
python tests/tip01/restore.py
```

Choose an existing private local path for the dump. It includes synthetic signing material: never publish it. Keep the PostgreSQL process alive for the whole test invocation. Expected final counts:23 new tests,46 retained tests,4 admission scenarios,1 separate-database restoration. The accepted106 exclusion of the superseded105 RR expectation is retained verbatim in meaning; its stronger106 no-effect matrix runs.

Client inputs must match `tests/native103/ui-source-hashes.json`. Generate105 UI with `python tests/native105/build-client.py INPUT_ROOT OUTPUT_DIR`; the SQL change does not alter that UI. Run `tests/native105/client.test.mjs` with CANDIDATE_UI set, `tests/native106/client.test.mjs`, and native104 cart regression against that generated public/customer.html in a disposable copy. For Chromium use native105/browser.mjs against the same generated UI. The current run's launch was blocked by process-singleton socket permissions; see evidence. VM results are not browser/HTTP proof.

Rollback:104 recovery-only wrapper with all writers quiesced; preserve keys/bindings/closures. Re-upgrade through106 plusTIP-01 before enabling any writer. Restoring106 alone is not the TIP-01 re-upgrade. See `docs/review/tip01/REPORT-AR.md` for scope, blockers and review acceptance.
