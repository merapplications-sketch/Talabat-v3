# Local evidence and reproduction

No live credentials, Supabase calls, financial transfers, or production database used. Base: 09ef07fd29fb5c5a3e323c23c7331e577567ab1e. All profiles and financial data in screenshots/tests are synthetic.

## Browser
Chromium 133 at `/tmp/polish-chrome`, Playwright installed in the session. `node tools/finance-fix/ui_check.cjs /path/to/chromium` runs the main current-application tests; `READ_DELTA=1`, `FINAL_DELTA=1`, and `HEADER_DELTA=1` resume the saved checkpoint for subsequent changed/error cases. Saved result aggregates 49 unique checks, not 49 identical reruns. The final header/layout delta rechecked only the affected header and history layout. Browser Supabase CDN is replaced with a fixture and all other HTTP is blocked; no real session or financial RPC used. Screens: 390×760 and 1280×900, some full-page captures. Not physical phone/Safari browser chrome tests. WebKit unavailable.

## Native PostgreSQL
Used PostgreSQL **17.6**, `@embedded-postgres/linux-x64@17.6.0-beta.15`, plus `pg@8.16.3`, installed outside the repository at `/tmp/talabot-finance-pg`. The tests only accept loopback 127.0.0.1:55439 and a synthetic database. Run against a disposable database only: `postgres_check.cjs` recreates the synthetic public schema. Never point this harness at an existing application database.

On an ordinary machine, start PostgreSQL as its unprivileged owner on that loopback port (database postgres, fixture user nobody); run:

```
node tools/finance-fix/postgres_check.cjs
node tools/finance-fix/proposal_b_check.cjs
node tools/finance-fix/validation_delta.cjs
```

`TALABOT_PG_MODULE` may identify the installed pg module; it does not change the fixed database target. A's 28 checks use separate connections and real PostgreSQL locks/transactions. B's 8 checks cover proposed schema/RLS only. After adding rejection of a null operation, only the 3 affected validation checks ran against the retained fixture, not the unaffected concurrency suite again.

### Restricted-session runtime caveat
This container has one OS UID, refuses setuid/unshare, and cannot bind Unix sockets. The local engine was started with `-k '' -h 127.0.0.1 -p 55439`; temporary cluster at `/tmp/talabot-finance-pgdata`. For PG's root/ownership startup checks only, an LD_PRELOAD shim ([source](../../../tools/finance-fix/runtime_identity.c)) reports UID 65534 and maps root-owned file stat IDs consistently. Actual OS ownership/privileges were unchanged. No SQL, locking, transaction, network or application behavior is emulated by this shim. This is native PostgreSQL, not PGlite, but not a production-equivalent deployment environment. The shim is a test setup workaround, not part of the application or proposed SQL, and is unnecessary on a normal non-root host.

Compiled `cc -shared -fPIC -o /tmp/finance_identity.so tools/finance-fix/runtime_identity.c -ldl`. Package hydration used its bundled `scripts/hydrate-symlinks.js`; binaries and libs under `node_modules/@embedded-postgres/linux-x64/native/`. `initdb` and `pg_ctl` used `LD_PRELOAD=/tmp/finance_identity.so` and `LD_LIBRARY_PATH=<native/lib>`. Start, run tests and stop in one shell execution because background processes do not survive this managed session boundary. Server was stopped after testing; no resource or paid service created.

## Compatibility limits
A requires review of current live ACLs, policies, function overloads and other writers before deployment; the supplied preflight is SELECT-only and unexecuted here. Existing support refund/cancellation/customer wallet-payment paths are outside the office-cash/manual-adjust patch. No change to global has_perm, assigned-driver delivery, pricing or frozen finance. B has no posting writer and does not establish offset/partial receipt/payout rules.
