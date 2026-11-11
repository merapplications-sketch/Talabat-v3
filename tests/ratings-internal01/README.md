# Isolated ratings read candidate

No dependencies to install. From repository root, using modern Node (tested version recorded in evidence):

```sh
node --test --test-reporter=tap tests/ratings-internal01/candidate.test.mjs
```

Only `candidate.mjs` is the proposed read algorithm; `fixture.mjs` is a synthetic in-memory snapshot adapter, **not PostgreSQL/Supabase or an RLS implementation**. The tests use literal expected averages/counts and adversarial pages; they do not import the historical aggregation function. No operational module imports this candidate. No SQL, network, real review records, credentials or third-party services are used.

24 cases: empty;1/2/4/5 ratings; restaurant/driver separation; branch separation; numeric half-up;701-row history; truncated300-page failure; permission/schema/network failure; invalid/duplicate rows; filters/ranking; stable query-bound pages; insertion between snapshots; snapshot drift; budgets; timeout/cancellation; private fields/comments; missing completeness evidence; unavailable ranking; forbidden-field getters;600-row historical impact; corrupt pages; active and late read-resource cleanup; absence of write paths.

The initial fail-closed stub failed16 of18 initial cases (two negative cases already passed); extended tests then caught late-open resource cleanup (23/24), repaired before final24/24. These are development red/green results for a new test candidate, not a claim to have executed old production code or current hosted failures.

See `docs/review/ratings-internal01-candidate/READ-CONTRACT.md` and `REPORT-AR.md`. Full-history/snapshot declarations must be independently established by a future approved adapter. Do not wire the test fixture into the customer app or map. Do not infer a production limit or SLA from test budgets/timing.
