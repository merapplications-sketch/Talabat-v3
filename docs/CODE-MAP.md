# TALABOT Gate1 — CODE MAP

- `driver.html` ← `shiftAck/startShift/endShift/ping` ← F-01 server-ACK-gated online/offline and fail-closed heartbeat.
- `driver.html` ← `chatDraftGet/chatDraftSet/sendChat/chatSheet` ← F-03 per-driver/order chat draft across insertion failures/reload.
- `driver.html` ← `confirmDeliver` ← F-04 refuse short/over/overprecision cash before delivery, report shortage separately.
- `talabat-core.js` ← `deliver/gate1DeliveryFlights/reportDriverCashShort/errKey` ← F-02 in-flight deduplication and F-04 report RPC + errors.
- `sql/proposed/gate1_cash_and_idempotent_delivery.sql` ← `deliver_order/report_driver_cash_short` ← F-02 row lock/one transition and F-04 Q14 support reporting, NOT APPLIED.
- `tools/gate1_contract_checks.cjs` ← four named deterministic source-function checks, NOT real DB E2E.
- `tools/gate1_e2e.py` ← G1-E01..11 tied to 51-case matrix, fail-closed unexecuted E2E marker.
- `tools/check_all.sh` ← all named source checks + existing core contract check + mandatory E2E, fail closed on any BLOCKED.
- `.github/workflows/gate1-20261116.yml` ← authorized branch-only CI, no production values/other repos/deploy.
