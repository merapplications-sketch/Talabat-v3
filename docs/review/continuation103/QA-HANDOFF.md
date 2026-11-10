# Independent REVIEW103 acceptance request

This candidate is NOT approved for production. Reviewer must execute and inspect independently; programmer reports alone do not establish acceptance.

## Pin and reproduce
Use the source commit pinned by RESULTS.md, not an advancing branch. CI103 installs pinned PostgreSQL17.6 and psycopg and executes test_sql.py, admission.py, restore.py and client/VM tests. Read workflow for environment and commands. Never point these destructive disposable-database harnesses at a production cluster. Only loopback test PostgreSQL is accepted by the harness; additional isolation is the operator's responsibility.

Generate the client review overlay with `python3 ci97/unpack.py` then `python3 tests/native103/build-client.py isolated97 /tmp/client103`. Review the generated customer.html and talabat-core.js against the hashed recovered source. There is no deployed preview or hosted HTTP acceptance in this package.

## Required independent checks
1. History: authorized own legacy key yields original ID, input_match=null, unchanged tables in a READ ONLY transaction. Reject account/group access loss; never fabricate raw input or fingerprints.
2. Fingerprints: independently verify domain-separated HMAC and every input field, typed numbers, object/array ordering and null rules. Review trusted ownership, inherited grants, key provisioning/rotation/backup/retention. Confirm no raw private data in fingerprint records or logs.
3. Atomicity: failure after wallet/promo/loyalty changes must roll back all effects; one order, one debit and one fingerprint after reconciliation. Exercise independent connections and TCP before/after COMMIT; examine40P01/55P03 classification without automatic resend/new key.
4. Transition: drain old writers, transactionally install, convert only genuine102 records, interrupt/rollback/reapply, then restore keys and fingerprints to another database. Recovery-only rollback must preserve mismatch rejection and block new creation.
5. Target fidelity: compare private catalog snapshot and actual authorized target. The fixture is partial: target RLS, triggers, grants, enums, missing columns/FKs and transitive dependencies require additional acceptance. Do not alter target constraints to match the fixture.
6. Client: malformed/late/unknown replies preserve frozen attempt and cart; account changes cannot reveal earlier orders; own-order re-read is required. Try reload, multi-tab races, edited/rejected requests and old clients. Explicit retry uses original key/payload after status lookup. Multi-tab UX and rejected-attempt replacement are not comprehensively accepted here.
7. Four applications, hosted finance/orders/outsider sessions, original private build gate, provider Storage revocation and real Safari remain separate release gates. Public CI success is not a substitute.

## Review outcome requested
Return ACCEPTED / CONDITIONAL / REJECTED for each item, exact tested SHA, independent logs, untested target differences and blockers. Do not apply SQL or change main protection as part of this review.
