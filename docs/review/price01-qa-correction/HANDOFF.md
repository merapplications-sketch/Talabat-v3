# PRICE01 correction checkpoint

Source: **50b796985112002f4c47aa4dd2bd1373ffd7aeff**.
Branch: `review/price01-isolated-20261111`.
Parent: `019d1038681661ad3441d64e0f202139c704adcc`.
Independent findings addressed: `7ed670824340e6a7ac4df62844d96516205fbb7a`, PRICE01-QA-01 and PRICE01-QA-02 only.

Start with [REPORT-AR.md](REPORT-AR.md), [RESULTS.json](RESULTS.json), [SOURCE-MANIFEST.json](SOURCE-MANIFEST.json), and `tests/price01-qa-fix/README.md` at the source commit. Latest evidence commit is documentation only; use the source manifest for the tested executable identity.

Implemented complete saved option comparison and exact decimal evidence arithmetic. Local25 native PostgreSQL17.6 +25 Node VM test cases pass. Count each final logical test once; the cross-layer matrix was extended to six cases and rerun separately. No new browser/hosted result or CI run is claimed.

STOP: **INDEPENDENT QA**. Do not start rollout or PHASE2. Do not change HMAC, financial formulas, NULL01, TIP02, historical recovery or protected orders. Do not rerun unrelated green suites. Library evidence transfer, G1C-PREC03, CASH-CHANGE and Admin work remain separate; this checkpoint changes none of their decisions.
