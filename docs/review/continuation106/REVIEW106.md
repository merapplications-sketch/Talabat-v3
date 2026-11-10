# Independent REVIEW106 package

Pin source86eb978e1aeb2be4a9d90999dc9b5a1267cb33df. Verify SOURCE-SHA256.json and original Actions logs/artifact at run42829377671. Earlier baseline-only run42828844940 proves S03 on unchanged105. Do not accept based on the programmer's summary alone.

1. Read CONTRACT.md, especially unsupported isolation behavior and scope of private/legacy entry points. Compare isolation.sql with only the first function of native104/functions.sql: the sole body difference must be the isolation guard. No HMAC/financial/business-rule changes.
2. In disposable PostgreSQL17.6 localhost with original fixture, run baseline.py. Assert B commits closure before A(RR) creates and commits one order/spend on unmodified105. The baseline intentionally demonstrates the bug; its green test means reproduction succeeded.
3. Install candidate and run native.py. Inspect every subcase of four entries × RC/RU/RR/SERIALIZABLE. Assert no effects, not merely a refusal SQLSTATE. Challenge current-identity checks, role grants, overloads and any alternate target creators separately.
4. Test closure-first and success-first races with independently blocked connections. Verify closure receipt/order states and wallet rows. Examine old-snapshot read-only status behavior: not_visible is not permission for a new key.
5. Examine real PostgreSQL40001 fault injection and explicit rollback/state equality plus same-key retry. It is not a naturally occurring SSI schedule. client.test.mjs checks unchanged client normalization using a synthetic RPC/in-memory store, not fresh IndexedDB/HTTP proof.
6. Retained regression:26 SQL cases,10 compatible resource cases,4 admission cases; TCP before/afterCOMMIT, deadlines/deadlock, historical/group/scheduled replay, HMAC rotation/S01 and wallet/promo/loyalty atomicity. The old105 RR quota-epoch expectation is explicitly superseded by earlier refusal, not weakened or reported passed.
7. Restore evidence covers a separate PostgreSQL dump/restore with successful binding/key and rejected-key receipt/policy/triggers; this is not provider backup certification. Review atomic install order and recovery-only rollback. Reconcile potentially missing operations before reopening a restored older snapshot.
8. Reuse unchanged105 UI/Chromium/local38 evidence; no new UI implementation. Full target catalog, hosted sessions/HTTP/E2E, private evidence and production resource policy remain unaccepted.

Required independent verdicts: S03 on the declared supported-entry/isolation contract; safe refusal/client behavior; transaction/closure invariants; rollout/rollback preconditions; target parity and production readiness separately. No live SQL/merge/deploy authorized. Findings return as a new task; stop at independent verdict.
