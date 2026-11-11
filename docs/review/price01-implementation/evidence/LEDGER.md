# Execution ledger and scope

These are local test records, not provider logs, hosted HTTP evidence, independent QA or a CI run. PostgreSQL17.6 was bound to127.0.0.1 in a disposable cluster; each test recreates candidate103. No protected order or real account data is included. Raw PostgreSQL server logs, generated secret bytes and private AUDIT107 originals are deliberately not copied.

## Effective final results

- native-final:22 groups executed on the final executable SQL.01–21 passed.22 failed because the test expected a cash order with fee0 despite the existing synthetic cash allocation.50 guard.
- native-22: only22 rerun after correcting that expected business outcome. It now asserts cash_allocation_exceeds_fee with no effects and separately verifies the eligible full-wallet waiver. Candidate formulas and source were not changed to get PASS.
- native-delta25: added23/24/25 only.24 atomic DDL interruption/reapply and25 removed-option/fee/points guards passed.23 raised a harness TypeError: a newly re-executed class was not a base of the current fixture instance.
- native-23: only23 rerun after selecting the actual inherited Isolation106 class. The pre-TIP01 writer and assertions did not change; historical sent20/stored0 and expired group/schedule recovery passed.
- native-26: additional required success-wins/closure-wins races on each entry passed, with PostgreSQL blocking observation and exact order/debit/closure counts.
- SUMMARY.json aggregates these to26 distinct passing native groups. It retains original failed run results and does not overwrite them or label their original runs green. Native test additions/corrections did not alter executable candidate.sql.
- client-final:17/17 on final generated UI/controller. It includes simulated multi-context ownership and all-write-boundary recovery checks. No Node assertion is presented as an actual browser or IndexedDB test.

## Red reproduction and implementation feedback

- red: baseline candidate without PRICE01.01/02 encountered a harness error when baseline bigint success was incorrectly treated as a dict;03 correctly failed because an equal-total price change created an order.
- red-delta: only01/02 rerun with the proper assertIsInstance rejection assertion. Both fail on the baseline because it actually creates, as required for red reproduction. No weakened post-fix assertion.
- green-initial:01–03 pass on the first implementation. It is preserved as development history, not the final26-group certification. An intermediate16-group pass is not used in the final tally because the financial write placement was subsequently restored to original order. Final SQL preserves that order.
- client-red: missing PRICE01 behavior on the accepted previous client, with preserved old controls. client-display-red reproduces the newly exposed displayed-catalog approval defect. client-stale-red reproduces stale approved-context retention after cart edit. Both were corrected before client-final.
- No historical TIP/106 suite was rerun wholesale. Existing fixture/controller code is imported for affected scenarios only. The106 stale-snapshot closed-key regression is specifically rerun because every creation entry now has an additional condition.

## Evidence semantics

- TCP before/after COMMIT in native11 and20 uses the retained local TCP cutting proxy and separate PostgreSQL connections. The commit ACK is actually cut, not mocked. HTTP is not tested by that proxy.
- Native21 creates a real55P03 lock timeout.40P01 is deliberately raised by a synthetic PostgreSQL trigger after binding writes; it proves rollback/error handling, not naturally occurring deadlock topology.
- Native24 aborts actual DDL transactions via a test exception and proves unchanged definitions/data. It does not simulate provider backup restoration or operating-system power loss.
- The client store serializes transactions in memory. LocalStorage records are replayed into fresh VM contexts. Neither mechanism establishes IndexedDB crash durability or cross-device coordination.
- BROWSER-READINESS.json records the observed Chromium launch failure; no page ran. No public preview, Safari, hosted RBAC, E2E or new remote CI result is claimed.

Run definitions: `tests/price01-impl/README.md`. Current code fingerprints: `../FILES.json`. Pinned inputs/generated files: `../SOURCE-VERIFICATION.json`. Acceptance mapping: `../ACCEPTANCE.md`.
