# TIP-02 local candidate

Parent: TIP-01 accepted by independent QA529e1bd347a350314f22626361b7e30d5037ae4d, codebcf651a7784617545354d2c6d7fe3d74d026c611.

Apply only in a disposable local PostgreSQL17.6 UTF8 cluster with pgcrypto, after103→104→105→106→TIP-01. New non-null tips accept0 (none) or whole1..100; invalid numbers raisebad_value after authorized prior-key lookup. Numeric signature rejects nonnumeric text before entering the function. NULL is NOT newly approved: legacy storage behavior remains, and its raw fingerprint stays distinct from0.

## Local reproduction

These inherited harnesses create/drop candidate103. Never use an application cluster. Use a new local cluster on127.0.0.1:5432, and set PGUSER to its owner. Dependencies: psycopg3, Node, pinned client input hashes in native103/ui-source-hashes.json. No hosted secrets needed.

```sh
export TIP01_ISOLATED=yes TIP02_ISOLATED=yes PGHOST=127.0.0.1 PGPORT=5432 PGDATABASE=postgres
TIP02_BASELINE=yes python tests/tip02/native.py # expected:1 group,12 failing boundary subcases on TIP01
python tests/tip02/native.py
python tests/tip02/retained.py
python tests/tip02/regression.py
python tests/tip02/build-client.py RECOVERED_INPUT_ROOT LOCAL_OUTPUT_DIR
CANDIDATE_UI=LOCAL_OUTPUT_DIR/customer.html node tests/tip02/client.test.mjs
CANDIDATE_CORE=LOCAL_OUTPUT_DIR/talabat-core.js node tests/tip02/controller.test.mjs
CANDIDATE_CORE=LOCAL_OUTPUT_DIR/talabat-core.js node tests/tip02/isolation-client.test.mjs
CANDIDATE_UI=LOCAL_OUTPUT_DIR/customer.html node tests/native105/client.test.mjs
```

Run native104/cart-regression.test.mjs in a disposable copy whose public/customer.html is the generated TIP02 file. Expected:7 new PostgreSQL groups,10 retained/manual transport groups,46 server regression tests;10 UI VM groups,6 core/controller groups,3 isolation client groups,15 C03/C04 VM groups,5 cart tests. Actual IndexedDB/browser/Safari/HTTP remain separate gates. No new browser PASS is claimed.

The generator preserves original105 files and emits local customer/core candidates. UI choices remain5/10/20 plusOther amount, withNone=0;3 is manual only. Draft/raw invalid text is preserved. Validation is before allocating a new key, also after quote awaits, but after existing-key recovery. Consumed tips reset after success; a later explicit selection is preserved as a new draft choice. The controller checks existing attempt ownership before new non-null payload validation; no HMAC format or attempt-store version changes.

Rollback remains104 recovery-only for public entrypoints with all writers quiesced. Re-upgrade through TIP01→TIP02 before re-enabling writers. Do not restore a legacy creation function over new manual-tip requests. Never drop bindings/keys/closures or reprice historical orders.

See docs/review/tip02/REPORT-AR.md and the offline component-only preview.html. The preview has no order API, accounts or network access; it is not a hosted app or E2E proof.
