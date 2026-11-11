# TALABOT CUSTOMER — MAP-RESTAURANTS-01

Isolated static design preview. No operational backend, account data, orders, checkout, database writes, or production changes.

## Sources

- Policy/base: `merapplications-sketch/Talabat-v3@05428e37d9779fa2af0845e640fe85553c8b6974`.
- Customer visual reference: existing `customer.html` / d6 customer UI (orange, system font, search, restaurant and menu composition). Existing customer file blob: `9bc335f52ad58d7feab12ad8a2214bde9ab32330`.
- Map reference: existing `loadLeaflet` / `TLB.mapView` in `talabat-core.js`, blob `f639bec1d23a812866e06eb1110940c77563387c`. Reuses Leaflet 1.9.4 and OpenStreetMap tile endpoint. No paid API, key, new map provider or 2GIS assets.
- Internal ratings audit: `review/ratings-internal01-independent-20261112@98dc238fbf5693595496def998399275c47b078b`, `docs/review/ratings-internal01-independent/READ-CONTRACT-AND-ACCEPTANCE.md`. Public comments projection is not proved connected; no direct access to admin ratings data.
- Existing customer source has a legacy external-score fallback when internal count is below five. This preview never uses that fallback; the original file is unchanged.

## Data provenance

`dist/data.mjs` is an authored fixture of six fictional restaurant/café/fast-food branches around Dushanbe. Coordinates are illustrative map positions, not verified partner premises. Names, opening states, menu items/prices and anonymous comments are fictional. These are not live TALABOT records.

`talabot.svg` is byte-extracted from the existing customer's embedded d6Logo. The five WebP illustrations are copied without changes from existing application assets; they are not restaurant photographs. The UI explicitly labels the sample, menu, reviews and illustrations. OpenStreetMap attribution is visible.

Each fixture rating is calculated from its matching branch's fictional restaurant-only comments. The model requires `source=talabot`, `subject=restaurant`, and exact `store_id`. Driver reviews and different branches are excluded. Empty/unavailable scores remain empty/unavailable; external `rating` / `rating_count` values are ignored. Small internal sample counts are allowed.

## Functional boundary

| Feature | Connection |
|---|---|
| Basemap, drag, zoom, fit | Actual Leaflet / OpenStreetMap network tiles |
| Pins and eligibility | Local fixture, active food venues with valid numeric coordinates |
| Search/type/rating/open filters | Functional local filtering |
| Restaurant, branch switch, menu, reviews | Functional navigation over demo data |
| Back to map | Browser history + validated session state; preserves center/zoom/query/filter/selection/list scroll |
| Live catalog, real photos, real opening hours | Not connected |
| Internal server reviews / rating endpoint | Not connected |
| Checkout or orders | Not implemented in this design scope |

## Run and test

Serve `dist/` over HTTP; no build/install step is required. Run `node --test tests/model.test.mjs`. See `docs/TEST-REPORT.md` for actual browser coverage and limitations.

All additions belong under `previews/map-restaurants-01/` in the canonical repository. No existing customer/admin/server file, main branch, permission, or production deployment is changed.
