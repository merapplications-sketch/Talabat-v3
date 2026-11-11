# Independent review reproduction notes

This directory records QA of source `3279fefd7ac135ea5554a5ff76404a6ae510eb65` (TIP-02 plus NULL-01), not deployment approval. The parent evidence commit is `306665d5b1fa26eb6457c0ad828d4934b3519f62`.

## Inputs and safety boundary

- Use the pinned repository test files from the parent, not a moving branch.
- Native runner requires Python, psycopg3 and a **fresh disposable loopback PostgreSQL17.6 cluster**. It imports fixture helpers from the pinned106 chain, not its complete test suite. The inherited fixture drops/recreates the local database `candidate103`; never point it at an existing business/test target or hosted server.
- `TIP_FINAL_QA=fresh-local`, `PGHOST=127.0.0.1`, `PGDATABASE=postgres` are explicit local guards; an operator must still provision an empty cluster. No hosted credentials are required or allowed.
- Client tests require Node. Build the generated client using `tests/tip02/build-client.py` and the recovered base whose two input hashes are fixed in `tests/native103/ui-source-hashes.json`. The builder checks them. This review reused those already saved inputs; it did not refetch or publish private exports.
- Copy the two review scripts to the checkout root, or invoke their absolute paths while the working directory is the checkout root. Paths inside the scripts intentionally resolve against that root. Create `generated/` using the pinned builder first.
- No actual browser, IndexedDB, HTTP/RBAC, Supabase, production, or protected records are used by these scripts. The client storage and RPC are mocks. The native schema/dependencies and financial inputs are synthetic and incomplete relative to the target.

## Runs retained, without rewriting history

1. `independent_native.py`: 16 unique groups. Initial `qa-native-results.json`/log records15 PASS and1 harness ERROR. The test key `old20qa` was below the pre-existing minimum length; only that synthetic key was corrected to `old20qa_key`. Assertions and candidate were unchanged. `QA_CASES=test_06_pre_tip01_raw20_and_unbound_null_readonly QA_RESULT=qa-native-followup.json` reran only that group, which passed. Final unique-case status16/16; initial error remains in the evidence.
2. `independent_client.mjs`: the first run covered UI01..11 and CORE01..07, yielding17 PASS and1 FAIL. `qa-client-results.json` is that run, not overwritten by the follow-up.
3. After the failure, UI12 was added to reproduce it using the real candidate controller plus generated UI. `QA_CASES=UI_12_integrated_controller_accepts_checkpoint_new_key QA_RESULT=qa-client-reproduction.json` ran that one case only. Its PASS means the unsafe behavior was reproduced, **not that the candidate meets acceptance**.
4. UI11 captures a real candidate `localStorage.setItem` checkpoint and restores those exact bytes into a fresh VM. UI12 preserves the completed attempt in the controller's serialized mock store. Both simulate a process restart; neither claims an actual browser was killed.
5. `automaticExtraConfirmation:false` in `qa-crash-integrated.json` means no extra re-selection of the tip occurred in the reproduction. The harness explicitly called the normal next-order confirmation; there was no automatic second order. The report is authoritative on this distinction.

To select only a case, both runners support comma-separated `QA_CASES`; `QA_RESULT` selects a separate output file. Do not overwrite the committed original evidence. Future verification should first address TIP02-QA-01, then run the affected persistence/recovery cases; there is no reason to rerun all previously accepted106 suites.

## Static integrity

`evidence/PINNED-INPUTS.json` records the Git blob and SHA-256 of109 copied pinned files, two recovered UI inputs, and two generated outputs in separate lists. `qa-static.json` records whole-definition equality after exactly the documented TIP-02/NULL-01 substitutions. `qa-null-full.diff` is the complete final NULL overlay difference. Native01 independently verifies effective function body and metadata equality within the synthetic PostgreSQL catalog.

`evidence/RESULTS.json` consolidates unique-case status without changing any raw result. `MANIFEST.json` covers the saved review files except itself. No database dump, runtime directory, signing-key material, session tokens, or private source export is included.
