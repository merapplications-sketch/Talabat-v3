# TIP02-QA-01 — isolated client recovery fix

Base: independent QA `d950dfc4f22ba40c0e884549641c47a9ac4960d6`, containing NULL-01 source `3279fefd7ac135ea5554a5ff76404a6ae510eb65`.

Only TIP-02's generator and tip helper change. The generated retire function validates key/sequence ownership, updates consumed tip state without saving, then detaches the completed key and saves both in the same draft record. No await or storage write occurs between those state mutations. Explicit later tip selections retain their existing null marker and are not consumed. Rejection retirement remains unchanged. Historical native105 files and the generated core are unchanged.

Run from a checkout containing this commit and the pinned recovered client inputs checked by native103/ui-source-hashes.json:

```sh
python tests/tip02/build-client.py RECOVERED_ROOT LOCAL_OUTPUT
CANDIDATE_UI=LOCAL_OUTPUT/customer.html CANDIDATE_CORE=LOCAL_OUTPUT/talabat-core.js RESULT_FILE=local-results.json node tests/tip02-qa01/recovery.test.mjs
CANDIDATE_UI=LOCAL_OUTPUT/customer.html RESULT_FILE=c03c04-results.json node tests/native105/client.test.mjs
```

For before/after reproduction, generate the baseline with the two original TIP-02 files from the base commit in a separate checkout, then run the SAME new recovery.test.mjs against that output. Expected baseline: 5 failures / 20 cases. Candidate: 20 PASS plus 15 affected C03/C04 cases. The test imports only harness definitions from the pinned independent QA file already present in the base; it does not rerun the independent suite or change its assertions.

The recovery test snapshots each actual mock-localStorage write produced by generated customer code, reconstructs a fresh VM from each snapshot, and explicitly submits the next order. It also restores the pre-write state and simulates a failing storage write. The integrated cases use the actual generated order controller with synthetic RPC and a serialized transactional store. This is NOT Chromium, IndexedDB, Safari, HTTP, real browser termination or an OS durability test. No SQL tests are run because SQL is unchanged.
