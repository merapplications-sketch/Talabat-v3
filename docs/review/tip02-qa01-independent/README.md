# Reproduce the targeted independent client QA

This folder records an independent delta review of source `d76269c9f3e5c02fe0be379ac8ba6356e624f9b8`, evidence parent `4d1c55c7e16dd9afe3380d4cc5f2482e82a4ea43`. No candidate files were modified. The new harness imports only setup/controller definitions from the unchanged prior independent harness; it does not run its green tests.

## Inputs

Use a checkout containing the fixed candidate and this report. The recovered base UI files are identified by `tests/native103/ui-source-hashes.json` (and copied hashes in SOURCE-VERIFICATION.json). `RECOVERED_ROOT/public/customer.html` and `RECOVERED_ROOT/public/talabat-core.js` must match those pinned inputs; a checkout's unrelated current application files are not substitutes.

Run from the repository root in an isolated local directory:

```sh
python tests/tip02/build-client.py RECOVERED_ROOT generated
node docs/review/tip02-qa01-independent/independent-recovery.mjs
QA_CASES=UI_11_success_crash_checkpoint_never_carries_consumed_tip QA_RESULT=original-regression.json node docs/review/tip02-null01-independent/independent_client.mjs
```

Expected candidate: 13/13 new groups, 24 matrix scenarios, 72 restore states; original failing case UI11 now passes. `QA_RESULT` may select an output path. `QA_UI` and `QA_CORE` select generated inputs for the new harness. These tests produce local evidence and synthetic records only; there are no HTTP requests or SQL operations.

For the independent red/green comparison, run only that same UI11 case from a separate old source3279… checkout with its old generated UI. The accepted source inputs are unchanged between3279… and the previous QA commit d950…. Expected old result: exit1, consumed tip99 sent with a new key. Do not run the entire prior suite or edit its Assertions. Old UI11 also writes a synthetic `qa-crash-checkpoint.json`; use a separate working directory for it.

The old harness hardcodes the old candidate ID in JSON. Raw outputs are preserved; SOURCE-VERIFICATION.json binds each result to the actual input SHA-256, command and working directory. The new13-group result identifies d762… directly.

## Limits

Node24.22.1 and Python3.12.14 were used. VM runs actual generated functions with mocked rendering/navigation, localStorage and RPC, plus a serialized synthetic attempt store for integrated controller cases. This is not a browser, IndexedDB, OS process crash, native PostgreSQL, financial settlement, HTTP/RBAC or Safari test. A snapshot restore checks application-level write boundaries, not filesystem durability. The former browser socket denial was not retried without a new capability.

Raw test outputs and source binding are included alongside the Arabic judgment. FILE-MANIFEST.json lists the review artifact hashes; it excludes itself to avoid a recursive digest. No private evidence or operational records are included.
