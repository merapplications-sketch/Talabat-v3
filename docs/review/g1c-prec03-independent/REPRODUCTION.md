# Independent precision evidence — local reproduction only

This folder is a report and a focused test harness, not a migration or deployment package.
Read REPORT-AR.md for the limits and the one corrected harness extraction failure before the successful run.

Inputs (not bundled; do not publish private AUDIT107 bodies):

- `source/merchant.html`, `source/talabat-core.js`, `source/isolation.sql`: exact blobs in EVIDENCE.json. The latter is `tests/native106/isolation.sql` from source106, read as text only; the entire file is not executed.
- `private-inputs/selected-definitions.json`: array of objects `{oid, definition, source_line}` extracted from version0 `target-definitions.json`. Required OIDs are listed in native-results.json.
- `private-inputs/catalog-excerpts.json`: array `{name, version, matches:[{content}]}` with exact version0 snippets from target-constraints.json and target-triggers.json. No fetched row data or secret is needed. Keep original object boundaries in snippets. Required IDs and constraint names are in native-results.json.

The owner has authorized local synthetic verification only. Do not point these tools at a hosted database.

Run `node input-path.mjs` to generate input-results.json with actual-source handlers and a mocked transport.

For the native probe, set `PRECISION_PG_BIN` to a local PostgreSQL 17 executable directory; initialize a NEW cluster using `initdb -D runtime/data -A trust --no-locale -E UTF8`. This trust configuration is for a disposable, isolated local test environment only, not a server policy. Run `python native-path.py` from this folder. The runner starts that cluster on loopback port42755, creates a fresh uniquely named synthetic database, executes the probe, writes native-results.json, and stops the cluster in the same process. It never connects to Supabase. Do not reuse an operational cluster. The generated `runtime/probe-private.sql` and runtime data contain private historical function bodies and must stay private.

Private function bodies are installed unchanged in a partial synthetic schema. Auth, permission helpers, and the null-image helper are explicitly substituted. The order wrapper uses literal source106 line-pricing and aggregation blocks, not the full order RPC. No hosted HTTP, RLS, browser, IndexedDB, Safari, current settings or full target equivalence is proven by this harness.

PASS for PG07/PG09 means the known shortfall was independently reproduced, not fixed. Expected121 comes from the accepted G1-C analysis; no tested formula is used as its own oracle.

EVIDENCE.json hashes the final committed report/harness/result files. Original captured definition hashes and extracted source-block hashes are in native-results.json. Editing this report or harness requires a new evidence version; do not overwrite original AUDIT107 files.
