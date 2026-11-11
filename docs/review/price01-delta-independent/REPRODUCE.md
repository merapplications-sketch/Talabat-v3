# Reproduce independent delta QA
Source50b796985112002f4c47aa4dd2bd1373ffd7aeff; source files must match delta-source-integrity.json.
Use only a NEW disposable local PostgreSQL17.6 cluster, UTF8, loopback5432, useragent, trust authentication. Harness drops/recreates candidate103; NEVER use an existing/shared database. No production credentials.
Copy the included independent_price_native.py, independent_price_boundaries.py, independent_price_client.mjs and delta scripts to repository root. Historical QA scripts are unchanged from the previous local review. Their hardcoded old source metadata is not the current tested-source identity.
Generate client using tests/price01-impl/build-client.py and its two checksum-pinned historical inputs. Set CANDIDATE_UI and CANDIDATE_CORE to generated paths.
Run:
- QA_CASES=U02,U04,U05,U07,U09 QA_RESULT=delta-client-prior.json node independent_price_client.mjs
- node delta-client.mjs
- PGHOST=127.0.0.1 PGPORT=5432 PGUSER=agent PGDATABASE=postgres PRICE01_QA=fresh-local python delta-native.py
Requires psycopg3, PostgreSQL17.6 pgcrypto and Node BigInt. Keep PostgreSQL alive in the same execution session as tests in runtimes that reap background children. Stop the disposable server after completion.
No developer acceptance assertions are used as new independent expected-price oracles. The native runner imports fixture setup and the pre-existing independent Q14. All new expected decimal values are literals; actual generated UI proofs feed SQL unchanged. Fault injection affects only the disposable synthetic fixture.
