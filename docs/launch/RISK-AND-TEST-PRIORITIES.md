# TALABOT — Pilot Risk and Test Priority Register

**Status: review draft.** Source findings are not automatically production failures. This is a concise route index; [full test matrix QA-01..QA-52](../benchmark/TALABOT-20261114-feature-risk-global.md) supplies detailed cases and separates present-system checks from future conditional feature tests.

| ID | Priority | Scope / known evidence | Specific required synthetic acceptance |
|---|---|---|---|
| PILOT-R01 | GATE | Identity / cross-tenant RBAC, RLS; no current E2E proof | Two fake accounts in different roles cannot view/modify each other's orders, locations, wallets or signed proof URLs |
| PILOT-R02 | GATE | Checkout idempotency/retry; older review accepted only at historical SHA | Double click, retry after COMMIT/timeout, concurrent request => only one order and no duplicate financial impact |
| PILOT-R03 | P1 | Driver delivery confirm source F-02 (possible duplicate RPC) | Two simultaneous confirmation clicks plus retry => exactly one delivered state, receipt and ledger side-effect |
| PILOT-R04 | P1 | CASH-01/Q14 risk F-04 candidate accepts below-due collection | Less/equal/more collection cases checked against approved Q14 and Q09–17; exact platform share, no undercollection |
| PILOT-R05 | P1 | Driver startShift can show Online before server ping ACK, F-01 | Server refusal, lag, timeout, reconnect: UI never lies about acknowledged shift/online state |
| PILOT-R06 | P2 | Driver chat field cleared before remote insert ACK, F-03 | Chat insert rejected; unsent text preserved with safe retry, no repeated message |
| PILOT-R07 | GATE | Server price/tax/discount/HH/loyalty/tip and fees | Tampered client totals, stale promo, rounding, wallet/points conflict => server's approved oracle prevails |
| PILOT-R08 | GATE | Return, payment, partial refund and settlement contract | Retry and concurrent approval produce no duplicate cash or wallet effect; claim remains open until actually received funds (RETURN-01) |
| PILOT-R09 | GATE | Delivery GPS/proof privacy | Denied GPS, wrong customer pin, stale location, absent/corrupt photo, expired signed URL => no leakage or false delivery proof |
| PILOT-R10 | P1/P2 | Existing merchant workflow | Scheduled, substitution approval, stop-list, merchant/driver acceptance races => consistent exact price/state and correct permitted actors |
| PILOT-R11 | GATE | Offline and retry across apps | App closed after commit and reopened; network restored => server reconciles state, no duplicate dispatch/settlement |
| PILOT-R12 | GATE | Running environment parity/rollback | Current customer/driver/merchant/Admin/core and deployed backend pinned to exact revisions; isolated restore/rollback proven |
| PILOT-R13 | P2 | Device/visual fidelity | RU/EN and only actually supported TG routes, 320/360/390/430, tablet, focus, long strings, modal, no clipping; real physical Safari evidence |

## Test discipline
Each test must record **ID, branch/SHA, actual environment, fixture, actions, expected vs actual, PASS/FAIL/PARTIAL/BLOCKED/UNTESTED, severity, screenshot/log/request/financial receipts and next owner**. Source scan is SOURCE-ONLY. The absence of a usable test runner is BLOCKED. Formal C-01 vs fake Safari visual demo remain separate.

## Immediate sequential handoff
1. Manager independently receives the Stage13 demo-only P2 language correction at commit **3f74b29a** and confirms it did not modify original product source.
2. Independent QA/UX/security must run current exact-preview browser UI, RU/EN/reload, 320/360/390/430, no-outbound network traces and fake-checkout negative assertions if a safe runnable artifact exists. Else state exact blocker.
3. Public no-cost visual demo only after explicit owner approval of candidate and host. Formal Auth/profile C-01 separately held behind pre-existing safety gates.
4. Full operational pilot current-source tests and G1 evidence; no feature work before the relevant approvals.

Source: [MASTER #26](https://github.com/merapplications-sketch/Talabat-v3/issues/26), [Stage1 QA](https://github.com/merapplications-sketch/Talabat-v3/blob/55a3fa5113202afdc3604179fd4a4919043dd11f/docs/qa-first-20261113/PROGRAMMER-STAGE1-QA-REPORT.md), [owner agreements](../OWNER-AGREEMENTS-AR.md).
