# Driver A v06 — visual integration for review

Base: `tech/v81` at `770be064461ab2fda40263d526bb243ec4f30cfa`, including customer v80 and Claude's admin addStore fix. No merge, deployment, database/account change or SQL.

`driver.html` retains its source controller and adds `assets/driver-a/driver-a.css` and `driver-a.js`. The adapter renders existing current data and calls the current TLB service functions. The design package's fake data, controllers, map, timers and financial examples are not application code.

The sheet and horizontal action use independent axis locks. Partial/cancelled/vertical action gestures do not confirm. Waiting and success lock repeats; failures preserve the current server-backed stage. The sheet body clears the fixed dock, preserves inner scroll during rerender, and supports keyboard and a no-gesture confirmation. Shared auth forms retain their current handlers and receive driver-scoped branding only.

Actual current-core data gaps versus design v61, and precise integration requirements, are in `CLAUDE-LINK-REQUIREMENTS-AR.txt`. Restaurant payment is unavailable; never infer it from order totals. Financial history/settlement v61 is not activated by this branch.

Run the scoped browser test (requires Playwright, Python3, Chromium):

```sh
node tools/driver_a_ui_check.cjs
```

`CHROMIUM_PATH` may point to an installed Chromium binary; `TALABOT_DRIVER_QA_OUT` selects output. The test fixture extends the repository's existing `tools/qa_all.py`; no real backend or database is contacted. It is never imported by application pages. This does not claim Safari, physical iPhone, maps, GPS, live auth or real database acceptance.

The offline review artifact is a separate export of this actual driver/core rendering with local test services. Its iframe/CSP adaptation belongs only to the review export; production frame protection/CSP remain intact.
