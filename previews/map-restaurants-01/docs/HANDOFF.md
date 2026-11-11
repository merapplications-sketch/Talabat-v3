# TALABOT CUSTOMER — MAP-RESTAURANTS-01 / v1

Status: isolated static design preview published; awaiting owner visual review. No operational hosted backend implemented.

## Publication and provenance

- HTTPS: https://talabot-customer-map-review.alwarikahtan.chatgpt.site/
- Canonical repository: merapplications-sketch/Talabat-v3
- Branch: preview/map-restaurants-01-20261112
- Executable source commit: `94ba22d11f626dc524388b7e214f3638e754b071`
- Source directory: `previews/map-restaurants-01/`
- Policy/base commit: `05428e37d9779fa2af0845e640fe85553c8b6974`
- Separate publication source commit: `5d5718b3f72c8b293595df0c8e56a452c06ece59`
- Site: `appgprj_6af4d40df314819195a69370eefcbfbe`
- Saved version: `appgprj_6af4d40df314819195a69370eefcbfbe~appgver_d4477b0ccdd4819194e84392152d3cbc` (v1)
- Deployment: `appgdep_6af4d79dcb7c81919da7310f3f30ed87`; connector reports `succeeded`.
- Source marker: `dist/SOURCE.json` in the published artifact.
- Git comparison against the base confirms only additions under this preview directory. No production, Admin UX-02, main, existing customer or server file changed.

## Delivered

- Actual Leaflet / OpenStreetMap map with interactive pins, drag, zoom and fit.
- Restaurant/branch search plus category, internal rating and open-now filters.
- Selected restaurant card, menu and internal restaurant-review examples, branch-specific ratings.
- Back restores map viewport, query, filters and selected pin. Local session state is validated.
- RU/EN and responsive map/list/dialog composition using existing customer visual tokens and assets.
- Every catalog record, coordinate, state, menu and review is a clearly disclosed authored demo. Existing 3D pictures are illustrations, not restaurant photos.
- No Google rating import/fallback, paid API, 2GIS content, account/checkout or server write.

## Verification

- Syntax: PASS. Model tests: 9/9 PASS.
- Actual supported cloud Chrome viewport: 1363 × 936. Map loaded; filters, menu, branch reviews, pan/zoom and back-state restoration passed. See TEST-REPORT.md and evidence/.
- 320, 390, 1440 px, real iPhone/Safari, touch pinch: NOT TESTED.
- Remote UI verification: BLOCKED BY AUTHENTICATION. Published URL opened to "Sign in required". Automated approval review rejected clicking "Continue with ChatGPT" as an unauthorized authentication action, citing the user's no-login requirement. No bypass or audience change attempted. Publication success is confirmed by the connector; authenticated remote page rendering is not claimed.
- Screenshots are from the actual local preview, not the authenticated remote URL and not a phone.

## Resume point

Review v1 visually on the owner's phone. Preserve current preview and branch history. Do not connect live reviews until a public restaurant-only, branch-specific endpoint and privacy projection are approved and proven. Do not read admin ratings data in the customer client or reuse the legacy external-score fallback. Next changes require owner feedback within this feature. No production merge/deployment or Admin work is authorized by this handoff.
