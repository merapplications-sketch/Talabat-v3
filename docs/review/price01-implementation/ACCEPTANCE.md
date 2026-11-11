# PRICE-A through PRICE-G — evidence map

Tested source: `bb01f11b855a2898f3f0b0f8908de827be68844b`.
Results below describe development evidence, not independent acceptance or hosted readiness.

| Gate | Executed evidence | Result / boundary |
|---|---|---|
| PRICE-A | native01/02/03/04/05/09; red.json + corrected red-delta.json; diagnostic parent evidence retained | PASS local: all4 paths, up/down/missing consent, one successful order/spend, atomic financial rollback. |
| PRICE-B | native03/06/07/09/22/25; UI17 | PASS tested local cases: offsetting prices, option delta/removal, store/item discounts, HH, promo, points/wallet/floor/fee waiver. Cash allocation guard preserved; no invented funding rule. |
| PRICE-C | native08/13; UI07/08/09/17 | PASS local: mutation after binding, deterministic profile-lock wait, changed displayed catalog, changed consent context. No target deferred-trigger proof. |
| PRICE-D | native04/10/14/15/17/23 | PASS local affected checks: ordinary/group/scheduled, historical rawNULL/stored0 and sent20/stored0/tip3, current explicitNULL rejection, HMAC conflict, RC/RU versus RR/serializable isolation. No hosted authorization claim. |
| PRICE-E | native11/12/13/16/18/19/20/21/26; UI05/06/13/14 | PASS local transport/session cases. TCP cut before/after COMMIT is actual local proxy traffic.55P03 is real lock timeout.40P01 is a deliberate PostgreSQL exception after binding, not a natural deadlock reproduction. Unknown stays unknown; no automatic changed key. |
| PRICE-F | UI01–17 on generated UI + real controller; simulated three-context transactional store and persisted-write restarts | PARTIAL:17/17 Node VM PASS. Chromium launch blocked before page; IndexedDB/Safari/device restart not proved. No hosted E2E claim. |
| PRICE-G | native14/24 and closed/recovery checks13/17/20/26; reproducible build/source hashes | PASS isolated atomic DDL/rollback/reapply tests. Provider restoration, hosted writer inventory and deployment approval remain blocked. |

## Native groups, reproducible names in native.py

| # | Focus |
|---|---|
|01|Up/down, all four entries, zero committed effects|
|02|Missing proof, all four entries|
|03|Opposing item prices with unchanged total|
|04|Exact proof, all four entries, tip99 payout/commission, one debit on replay|
|05|Null/shape/version/decimal/nonfinite/unknown-field rejection|
|06|Option price, store/item discount, HH and promo changes|
|07|Exact decimal comparison; no tolerance|
|08|Late synthetic trigger changes saved price; complete rollback|
|09|Real retained promo/loyalty functions on synthetic tables; points/wallet/promo rollback and accepted result|
|10|Pre-contract bound and unbound rawNULL/stored0/tip3 recovery, all entries|
|11|Real TCP loss before/after successful COMMIT, later catalog change|
|12|Three independent connections, same key, one creation/debit|
|13|Proved profile lock wait then changed price; closed key cannot reopen|
|14|Recovery-only rollback, re-upgrade, supported RU and rejected RR/serializable|
|15|Ordinary/group/scheduled eligibility, changed-consent HMAC conflict, explicit NULL all entries|
|16|Closure cap, authorization, new helper ACL isolation|
|17|Retained106 stale-snapshot closed-key assertions across all entries/isolation levels|
|18|Different keys, same account, open-order admission boundary|
|19|Different accounts, same key, independent creation|
|20|TCP loss before/after rejection COMMIT, immutable closure reconciliation|
|21|Actual55P03 plus injected40P01; no partial effect/false closure; same-key retry|
|22|Full wallet after decrease, total floor, free-fee allocation rejection, eligible full-wallet waiver|
|23|Pre-TIP01 sent20/stored0, group placed and schedule crossing40-minute boundary; original result after upgrade|
|24|Interrupted transactional rollback/re-upgrade, repeated install, retained definitions/MACs/closures|
|25|Removed option and existing fee/points guards; no point consumption|
|26|Success wins and closure wins with observed blocking, each entry, no duplicate order/debit|

Final effective native result is26 distinct passing groups, combined from native-final(01–21), native-22, native-delta25(24/25), native-23 and native-26. It is deliberately not labelled a single26/26 full run: green unaffected groups were not repeated after test-only additions. All used the same final executable SQL/client hashes recorded in SOURCE-VERIFICATION and FILES. Test-only fixes are disclosed in evidence/LEDGER.md.

## What did not change

No canonical103/request_payload103/mac103/resolve103 definition change. No epsilon, accounting, fee, commission, cash allocation, loyalty or tip formula change. No rehash or historical data update. No schema/table data migration. No closure-budget policy change. No existing grants/RLS or CI edits. No return to an unguarded old creator on rollback.

Existing source hashes and generated diffs support this assertion; local historical snapshots include order, item, wallet, recipient/phone, group, fulfillment and binding rows. Tests additionally inspect promo/loyalty tables when those paths are used. This does not claim exhaustive identity of a live Supabase catalog.
