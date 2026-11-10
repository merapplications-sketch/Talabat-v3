# Verification distinctions

- All12 local native104 source file hashes matched the pinned remote104 SOURCE-SHA256 manifest before handoff; no104 implementation was edited.
- Initial Node VM reproduction: C03 direct/recovery and C04 bad_time/promo/group/quote failed on generated104 for the expected stale-key/destructive mutation reasons; unchanged/unknown control cases passed. Expanded105 VM suite passes15 cases.
- First105 checkpoint CI42821307066: client passed; PostgreSQL baseline assertions observed12 rejected keys/12closures/zeroorders/zerospends, then result JSON export failed on Decimal serialization. Fixed only result encoding, not assertions.
- CI42821898901: baseline report exported; initial11 resource tests passed10 and one test setup errored because an authenticated fixture role could not SELECT orders to establish a repeatable-read snapshot. Changed snapshot acquisition to permitted pg_current_snapshot(), without widening grants or weakening the over-admission assertion.
- Local Chromium launch was attempted and failed at process_singleton socket() EPERM in the runtime. Chromium evidence must come from the isolated GitHub runner, not local Node VM. Hosted RPC remains untested.
- Local fast regression uses all38 available groups on generated105 customer/core; private db-evidence-binding is explicitly excluded. The five original cart assertions are preserved via104 extractor adapter. No claim of Full CI Coverage or private build-gate acceptance.
- A first fast-run invocation used the wrong working directory and did not start the suite; the corrected run completed38/38. No failed application test is hidden by this note.
- Browser105 adapter retains104 assertions and supplies the newly required cartSave hook in the two old minimal UI fixtures. Four new UI cases use the actual generated cartSave/cartLoad functions and real browser storage; only backend RPC/order readback and surrounding presentation/services are synthetic.

- The first full Chromium105 run passed14/15. The direct-success test accidentally returned the unresolved `place()` promise from Playwright evaluate, so the harness waited for its synthetic1500ms timeout before delivering the reply. Replaced the return expression with a non-returning block to inject the reply while the request is pending; kept the production deadline and every assertion unchanged.
