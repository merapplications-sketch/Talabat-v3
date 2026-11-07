# Finance valid-record tests

Isolated project fsvrsvqfknogwmhccera only. No production calls, DDL, protected-account impersonation, or updates to orders1/2/3. Dedicated synthetic customer920, driver921, staff922 and store923 (UUID prefix90000000) existed only in a rollback transaction. Staff permissions finance/support were confined to the synthetic actor. Fixture insert collisions would abort. A delivered cash order was inserted as privileged test setup, then snapshot_cash generated its cash allocation using an unchanged copy of the approved policy. This tests finance operations against a valid record, not full delivery workflow. Only synthetic IDs were appended transaction-locally to the pilot allowlist. Lock timeout2s; statement timeout15s.

| Case | Observed |
|---|---|
| Successful refund | 60 credited |
| Same ticket refund replay | already_refunded; no duplicate |
| Second ticket refund41 against remaining40 | refund_too_high |
| Second ticket refund40 | Accepted; aggregate100 in2 rows |
| Exception after refund25 | Rolled back; refund aggregate0 before retry |
| Exception after settlement | Rolled back; cash_settled_at null and command status null |
| Settlement retry after exception | Accepted, amount5, one order |
| Same request settlement replay | Exact same JSON result |
| Same request changed target | request_conflict |
| New request against already settled set | nothing_to_settle |
| Final receipt consistency | One command, one receipt, one receipt-order |

No bypass confirmed in these cases. Refund retry is duplicate rejection rather than a request-key response replay; clients must handle already_refunded without issuing another refund.

ASVS5 bounded evidence: V2.3.3 (L2) exception-driven transaction rollback for refund/settlement; V2.3.2 (L2) per-order refund cap and one-settlement behavior. V2.3.4 (L2) locking was inspected but this suite is sequential, so it does not establish concurrent settlement/refund correctness. No complete ASVS requirement is closed by this suite.

Limits: SET LOCAL ROLE authenticated and synthetic JWT claims exercise database authorization context only. No real authentication, HTTP retry, GUI, actual TCP disconnect, process crash, or multi-session race was tested. Injected exceptions occurred immediately after successful function return inside a PL/pgSQL subtransaction, so the evidence proves rollback of the operation and its transactional effects, not a mid-statement/network interruption. Existing real-HTTP wallet concurrency evidence was intentionally not rerun.

Cleanup readback: original pilot hash restored; synthetic auth/order/wallet/command/receipt counts all zero. PostgreSQL sequences may advance despite rollback. Evidence files: finance-valid-records.sql, finance-valid-results.json, finance-rollback-verification.json.
