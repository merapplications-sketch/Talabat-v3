# Regression scope104

Original103 source files were retained unchanged. Native104 loads the19 original103 unittest assertions and changes only candidate wiring (104 overlay and104 rollback). New104 cases add float/session permutations, existing103 record compatibility, terminal rejection/correction, unconfirmed timeout, rejection-fence concurrency, ACL/account isolation, rollback/re-upgrade.

Fast regression was executed against the GENERATED104 customer/core in a separate directory, not the untouched original public files. First run:37/38 groups passed; cart-resume91's five tests failed because its narrow source extractor omitted the two new helper functions. Its success fixture also used the old bare-id response. An adapter includes the helpers and supplies typed verified success; all original five assertions remain unchanged. Adapted runner passed38/38 groups. No application assertion or business rule was relaxed. This is an explicit harness compatibility change, not a hidden passing substitution.

The older SQL/PGlite groups are unchanged historical candidates; their green103 evidence is retained rather than rerun and mislabeled104. Direct104 SQL evidence is native PostgreSQL with partial synthetic target dependencies. Browser tests exercise real Chromium/IndexedDB/tabs/process crash but mock server RPC. None constitutes hosted HTTP/RBAC, real Safari or full four-app E2E.

Local Chromium launch was attempted and failed because environment sandbox denied socket/ptrace operations; remote disposable CI is the browser execution path. This limitation does not justify calling VM tests real-browser evidence.
