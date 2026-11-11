# PRICE01-QA-01/02 — targeted local reproduction

Scope: only the two findings in independent QA `7ed670824340e6a7ac4df62844d96516205fbb7a`.
Base branch head: `019d1038681661ad3441d64e0f202139c704adcc` (executable source `bb01f11b855a2898f3f0b0f8908de827be68844b`).
No hosted SQL, deployment, schema changes, new permissions or financial policy changes.

## Tests and provenance

`client.test.mjs` uses the existing generated-client VM scaffold but literal expected decimal values, without calling SQL or the developer price oracle to construct expectations. It writes the actual UI evidence to JSON. `native.py` sends that JSON unchanged to PostgreSQL, checks stored amounts/replay, and injects synthetic final-write faults to prove complete option checking and atomic rollback. These are programmer-run reproducible regressions, not a new independent QA verdict.

- Q04: an unrequested zero-price saved option must reject across all four creators.
- Q12: unrequested +1/-1 saved options must reject despite unchanged total.
- Q09/U09: the real client proof for `20.1 × 3` must create once and replay unchanged across all four creators.
- Additional option identity, multiplicity, price, removal, and ordering cases; positive/negative option prices; restaurant/HH split; multiple lines; capped promo; exact sub-cent transport and strict drift detection.
- Three independent concurrent connections; real TCP cut before/after COMMIT; one order/one spend per committed key; recovery after a later catalog price change.

The saved option schema is an array of `{id,p,...}` entries, not a new per-option quantity field. Multiplicity is its entry count. The comparator now visits every saved entry once, using the approved IDs solely to recover ordering. It cannot hide extra IDs or multiply rows through a join.

## Run in a new disposable local PostgreSQL 17.6 cluster ONLY

Prerequisites: PostgreSQL **17.6** with pgcrypto, Python3 with psycopg3, Node supporting BigInt, and the two pinned historical client inputs verified by `tests/price01-impl/build-client.py`. Do not connect this harness to any existing/shared database: the inherited fixture recreates `candidate103`. The TCP fault proxy requires port5432 on loopback; if occupied, stop and use another isolated runtime, not the existing server. No production keys are needed or read.

For example, after setting `PG_BIN` to a local PostgreSQL17.6 installation:

```sh
qa_dir=$(mktemp -d)
"$PG_BIN/initdb" -D "$qa_dir" -A trust -U agent -E UTF8 --no-locale
"$PG_BIN/pg_ctl" -D "$qa_dir" -l "$qa_dir/server.log" -o "-h 127.0.0.1 -p 5432 -k ''" start
export PGHOST=127.0.0.1 PGPORT=5432 PGUSER=agent PGDATABASE=postgres
export PRICE01_ISOLATED=yes TIP02_NULL_ISOLATED=yes TIP02_ISOLATED=yes TIP01_ISOLATED=yes
python tests/price01-impl/build-sql.py
python tests/price01-impl/build-client.py /path/to/pinned /path/to/generated
export CANDIDATE_UI=/path/to/generated/customer.html CANDIDATE_CORE=/path/to/generated/talabat-core.js
node tests/price01-qa-fix/client.test.mjs
python tests/price01-qa-fix/native.py
"$PG_BIN/pg_ctl" -D "$qa_dir" stop
```

The pinned directory contains `public/customer.html` and `public/talabat-core.js`; SHA256 respectively:
`2bfd0802d24fc4d8f907103dc0221e993f7b03b65a8b5c6388966a3dbfd5d245` and `7b56879e5e96f28696345d298f914a89e964dba49ebcfd2a5998e849435156c7`.
Use the builder's pinned source reference; do not substitute default-branch HEAD.

Outputs: `price01-correction-client.json`, `price01-client-proofs.json`, `qa-client-quantity-proof.json`, `price01-correction-native.json`.
`QA_RESULT` controls the result path, `QA_CLIENT_PROOFS` and `QA_QUANTITY_PROOF` control the cross-layer files. `QA_NATIVE_CASES` selects comma-separated method names.

## Red/green comparison without replacing newer work

Create a separate checkout of base `019d1038681661ad3441d64e0f202139c704adcc`, copy only this correction's test directory there, and build its own generated client. On that base, R01/U09, R02, R03, R05, R07, R08 fail. Q04/Q12/Q09 fail with unchanged assertions. Select these native methods explicitly for the baseline:

```sh
QA_NATIVE_CASES=test_Q04_added_zero_option,test_Q12_offset_options,test_Q09_real_ui_quantity python tests/price01-qa-fix/native.py
```

The unmodified original QA Q04/Q09/Q11/Q12 and Q13/Q14 were also rerun from immutable commit `7ed670824340e6a7ac4df62844d96516205fbb7a`, under `docs/review/price01-independent/`. Q10 there is a diagnostic workaround that explicitly expects the old U09 bug to occur; it is not an acceptance case after repairing U09. Its assertions were not edited.

## Targeted retained regression

Existing tests/fixtures remain byte-identical. Native selected methods: 04,06,07,08,09,10,13,14,15,17,20 in `tests/price01-impl/native.py`; pass their full names via `PRICE01_CASES`. Client selected prefixes: PUI01,02,03,04,05,07,08,09,10,11,12,16,17 in `tests/price01-impl/client.test.mjs` via `PRICE01_CASE` one at a time. Selection covers changed snapshot/proof paths, TIP99/NULL/history, C03/C04 checkpoints, unresolved attempts, HMAC conflict, price race, atomic financial rollback, recovery-only rollback, re-upgrade and the106 isolation barrier. Unaffected entire historical suites were not rerun.

## Precision boundary

Only evidence representation/derived exact decimal addition, subtraction and integer multiplication changed. No tolerance or global two-decimal rounding was added. Existing `calc`, `baseOf`, `pctC`, financial totals, points epsilon and HMACv1 remain unchanged. In particular, the old UI `baseOf` already rounds its displayed unit: this correction does not remove that protected behavior. Raw base/option values such as `20.1234567`/`0.0000001` remain present in the evidence; a genuine disagreement with unrounded SQL pricing still rejects and requires explicit review. The codec cannot reconstruct digits already lost before a JavaScript Number reached it. Oversize evidence and non-finite values fail closed under the existing128-character representation contract. BigInt is transient only; the stored payload still contains ordinary decimal strings.

The generated core and all existing recovery/consent/attempt methods are unchanged. Pending payloads are never regenerated, and historical results are not repriced. Node VM is not Chromium/IndexedDB or Safari; native PostgreSQL with synthetic dependencies is not Supabase/hosted HTTP proof.

Stop: **INDEPENDENT QA**. PHASE1 remains PARTIAL/BLOCKED; PHASE2 NO-GO.
