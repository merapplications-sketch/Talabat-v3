# MAP-RESTAURANTS-01 verification

## Source / unit checks

- JavaScript syntax checks: PASS for app, model and data modules.
- `node --test tests/model.test.mjs`: 9/9 PASS.
- Covers eligibility, missing/invalid coordinates, category scope, closed branches, intersecting filters, small internal rating counts, no Google fallback, branch/subject review isolation, fixture aggregates, map-state round trip and invalid cached state.
- Static ESM preview: no compile/build step. No operational server test is claimed.

## Actual UI checks

Supported cloud Chrome, **1363 × 936** CSS viewport:

- OpenStreetMap tiles loaded: 25 image tiles observed, with attribution.
- Map drag, zoom-in, selected pin and detail card: PASS.
- Search + open now + minimum rating: 6 all → 4 open → 1 matching Safran branch.
- Café filter with Safran query: 0; clearing query: 1 Morning café; resetting: 6.
- Menu and restaurant-only review tabs: PASS.
- Same-brand branch switch: separate 4.7 / 3 and 4.0 / 2 aggregates, separate opening states.
- Back from restaurant: exact observed search value, Leaflet pane/pin transforms and visible tile source restored (`evidence/map-return-proof.json`).
- RU / EN switch: PASS.
- Document width: 1363, no horizontal overflow at that viewport.
- Evidence: `map-desktop-1363.jpg`, `reviews-desktop-1363.jpg`.

## Not tested

| Target | Result |
|---|---|
| 320 px | NOT TESTED |
| 390 px | NOT TESTED |
| 1440 px | NOT TESTED |
| Real iPhone / Safari | NOT TESTED |
| Touch pinch, keyboard/safe-area on real phone | NOT TESTED |
| Long-list scroll restoration in real UI | NOT TESTED; state model covered |
| Live TALABOT backend / real partner locations | NOT CONNECTED |

Responsive CSS, dvh/safe areas, 16px mobile search input, mobile map/list dialog and bottom selection card are implemented. Desktop testing does not establish mobile acceptance. No unsupported viewport override or browser automation bypass was used.
