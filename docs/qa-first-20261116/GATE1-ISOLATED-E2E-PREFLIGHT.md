# TALABOT Gate1 — Real Supabase E2E readiness / 11 cases

## Strict preflight
- Actual separate free Supabase project named `talabot-test`; it is **not yet created** and cannot be substituted by the existing Talabat, historical pilot, or inactive Talabat-tj projects. The source branch includes only `sql/schema_patch17.sql` through `schema_patch34.sql`; initial schema provenance is **missing**. The code MUST NOT invent a toy production schema.
- Github Secrets only `SUPABASE_TEST_URL`, `SUPABASE_TEST_ANON_KEY`, `SUPABASE_TEST_SERVICE_ROLE_KEY`. Their values are never printed or committed. Non-secret `GATE1_TEST_PROJECT_REF` must match exact test HTTPS origin, with hard-coded fail-closed denylist for protected project refs.
- One test-only ephemeral role/fixture JSON written **outside repository** by the authorized test project setup, referred to via `GATE1_TEST_FIXTURE_PATH`. Required: `project_name=talabot-test`, `project_ref`, `synthetic_only=true`, five synthetic role JWTs (customer/merchant/driver/outsider/other_driver), `place_order_args`, `cash_due`, `other_driver_order`. No real emails/customers/tokens.
- `tools/gate1_e2e.py` checks ALL prerequisites before network and exits `3 BLOCKED` if missing. If present it performs eleven REAL PostgREST/RPC HTTP cases and refuses redirects/off-origin targets. This does not use a mock session.

## Eleven scenario mappings (51-case Stage1 matrix)

| Test | Original scenario(s) | Check |
|---|---|---|
| E01 | C-11/B-04 | Cash order creation |
| E02 | C-15/B-07 | Merchant accepts |
| E03 | D-02/D-07 | Driver online ACK |
| E04 | D-03 | Driver accepts |
| E05 | D-06/B-07 | Ready and pickup |
| E06 | D-08/B-07 | Matched cash delivery |
| E07 | D-10/B-07/B-10 | Two concurrent delivery sessions and post-COMMIT replay |
| E08 | D-08/B-10 | Underpayment denied, support report persisted |
| E09 | D-11/B-03 | Chat authorized/foreign insert denied |
| E10 | C-16 | Customer tracking status updated |
| E11 | B-03/D-01 | Outsider and unassigned driver RLS denial |

**No E2E PASS until real test project and synthetic fixture exist.** F03 chat draft-after-error/reload is separately tested in a source-function simulation; real device browser behavior still requires independent verification. `tools/core_contracts_check.py` preserves previously accepted checks and runs in the same command. No formal product launch, C-01, CASH-01, production SQL or deployment.

## Mandatory financial-effect attribution for E07

The approved proposed `deliver_order` writer intentionally returns **HTTP success** for an **identical post-COMMIT retry** and avoids a second `UPDATE`. Therefore two concurrent identical submissions must not be treated as “two deliveries” merely because both HTTP calls succeed.

To certify one financial receipt/effect, the **new isolated test fixture** must additionally supply `finance_receipt: {"table":"<verified ledger/receipt table>","order_key":"<verified order FK column>"}` from the independently verified, complete `talabot-test` schema. `tools/gate1_e2e.py` refuses to run without this mapping. It reads that table with TEST-ONLY service_role and requires **exactly one** receipt for the test order and no change after identical replay; delivery `done_at` and `cash_collected` must also remain byte-for-byte unchanged. If the actual schema does not contain such an attributable financial/receipt effect, mark the gate **BLOCKED** and obtain a finance/DB contract decision; never substitute an arbitrary events table or claim a receipt was proved.

## Correct RPC names and chat lifecycle

- F04: the already proposed SQL names its driver-only ticket creator **`public.report_driver_cash_short`**, writing `support_tickets` and `ticket_messages` — NOT `report_cash_shortfall` / `cash_shortfall_reports`.
- E08 checks the returned ticket ID, the single support record and driver message, the Q14 shortfall rejection and unchanged `pickedup` status; identical second report must not duplicate the ticket.
- E09 creates a fresh synthetic **active** order for chat authorization instead of sending a message after a different test case completed delivery.
- E07/E08/E09 are unexecuted **until** the original project/seed/role/finance contract has a real test-only implementation. Source-only checks or syntactic compilation are NOT E2E acceptance.


## Brief-2 / LOCAL CI override of obsolete cloud setup instructions (2026-11-16)

**Owner instruction:** [#48 / 6901725324](https://github.com/merapplications-sketch/Talabat-v3/issues/48#issuecomment-6901725324). The cloud `talabot-test`, GitHub cloud Secrets and remote ref from the earlier sections of THIS document are now **SUPERSEDED / MUST NOT BE USED**. Accepted test target is a disposable LOCAL Supabase Docker instance in branch-only CI with exact API origin **`http://127.0.0.1:54321`**. Never run against any remote Supabase host.

**Authentic baseline contract:** `sql/baseline/schema_baseline_dzydscryrnahnneydnry_20261116.sql` and matching adjacent `.json` manifest with `source_ref`, `sha256`, `extracted_utc`, `schema_only:true`, `patches17_34_included`. Both files are currently **ABSENT** because schema-only production metadata reads timed out. Do not create placeholder SQL or guess table/ledger/role definitions. `tools/gate1_local_prepare.py` checks both before staging any local migrations; failure exits 3.

Once the authentic schema is provided, the authorized CI workflow starts a Docker-local Supabase, applies the validated baseline + proposed Gate1 SQL (and patch17–34 only if manifest records them absent), creates five **synthetic LOCAL Auth identities** with matching isolated catalog/order seed outside Git, then runs `tools/check_all.sh`. The seed creator is **not yet available** because the authoritative baseline is unavailable. Never use real users/orders or copy any row from production.

**E07 financial receipt:** The finance ledger table and order foreign-key column must be audited from baseline. If absent, E07 may be marked BLOCKED *alone* with genuine 10/10 other PASS and documented financial-contract gap; never invent a new ledger or call source-only F02 simulation a real receipt proof.

**Evidence to date:** previous source F checks + offline Chromium core PASS; schema extraction timed out; local E2E 0/11 executed, 11 BLOCKED. GitHub Actions nonzero is the required fail-closed behavior until the missing baseline and safe synthetic fixture are available.
