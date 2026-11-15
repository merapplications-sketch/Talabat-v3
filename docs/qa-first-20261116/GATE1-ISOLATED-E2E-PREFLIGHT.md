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
