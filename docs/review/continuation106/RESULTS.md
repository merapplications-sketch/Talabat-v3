# BATCH106 closure — 10 November2026, Asia/Dushanbe

Candidate saved/tested in isolation; REVIEW106 independent acceptance pending; NOT READY.

Source and tests:86eb978e1aeb2be4a9d90999dc9b5a1267cb33df.
Branch:review/batch106-20261110. BATCH105 branch/source untouched.
CI:https://github.com/merapplications-sketch/Talabat-v3/actions/runs/42829377671 — completed SUCCESS, postgres and required106 passed.
Baseline reproduction commit:564a79080bfef76ef000885e02617c57791dc73e; run:https://github.com/merapplications-sketch/Talabat-v3/actions/runs/42828844940.

S03 was independently reproduced by this implementation task on unmodified105: an older RR transaction created and committed1order/1spend(-5 synthetic units)/1binding after another transaction committed1closure for the same key. A passing baseline job means the bug was reproduced, not that105 is safe.

Repair: shared private create_order103 refuses RR and SERIALIZABLE with unresolved/unsupported_transaction_isolation before order effects. RC and RU remain supported. All three public creation wrappers reach that helper; the legacy bigint wrapper raises order_outcome_unknown. No success/final-failure claim is fabricated. Same key must be reconciled in a fresh supported transaction; no automatic retry/rekey.

Verified cases from original PostgreSQL17.6 CI logs:
-10/10 new test groups; includes16 entry/isolation matrix subcases, zero orders/spends after committed closure, closure-first/success-first races, fresh-transaction replay, rollback/re-upgrade, catalog/grants and explicit real40001 fault atomic rollback.
-10/10 compatible105 resource groups.
-26/26 SQL103/104 regression groups on106 overlay, including S01/HMACv1/history/promo/loyalty/wallet and TCP before/afterCOMMIT.
-4/4 admission/concurrency cases.
-Separate pg_dump/restore verification passed for saved order/key/fingerprint and closure/policy/triggers.
-3/3 client response-contract cases passed using unchanged104 controller and synthetic RPC/in-memory store: unsupported isolation,40001 and transport failure retain frozen inputs/key, block replacement and refuse false terminal end.

The prior105 RR quota-epoch assertion is explicitly superseded because106 refuses earlier; stronger matrix verifies no effects. It was not altered in105 or counted as passing. Existing105 generated UI and test source hashes were unchanged. Chromium15/client15/cart5/local38 results are retained105 evidence and were NOT rerun/rebranded106 evidence.

Verified entry set:public.place_order,public.place_order103,public.place_order104,security_private.create_order103 (private owner/internal only). Fixture catalog asserts public wrapper grants and no authenticated direct orders INSERT. No target Supabase catalog/HTTP/role-session proof was obtained. No claim covers arbitrary owner SQL, unknown overloads or unapproved legacy writers.

S03 is repaired within tested contract, subject to independent QA. S02 overall resource policy/HTTP rate/body/CPU/WAL controls remain open, as do target parity, private evidence/build-gate, hosted HTTP/E2E, real Safari, cross-device reconciliation, Storage and provider recovery. Numerical production limits were not chosen. No retention change or fence deletion.

Review bundle:CONTRACT.md,REVIEW106.md,SOURCE-SHA256.json,RESULTS.json and original Actions artifact. Source/tests are pinned; subsequent evidence-only commit does not require rerunning successful tests. Actions artifact expires after7days; committed per-case summary and tests persist.

Next: independent REVIEW106 of86eb978e1aeb2be4a9d90999dc9b5a1267cb33df, with target/operational verdict separate. No liveSQL/main merge/deployment/account/MFA/protected orders1/2/3/settlement3 action was performed.
