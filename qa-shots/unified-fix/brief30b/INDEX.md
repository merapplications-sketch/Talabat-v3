# BRIEF-30b — AE-01 · AE-02 · AE-03

Code under review: [`8cd90a8ac14ff01413b63f79c5db676c0081d34d`](https://github.com/merapplications-sketch/Talabat-v3/commit/8cd90a8ac14ff01413b63f79c5db676c0081d34d)  
Review branch: `review/unified-fix-brief15-20261117`  
No deployment.

## Required checks

Both runs completed successfully on the code SHA above.

| Check | Result |
| --- | --- |
| [Home — run 44803626527](https://github.com/merapplications-sketch/Talabat-v3/actions/runs/44803626527) | Success |
| [H-01 — run 44803626534](https://github.com/merapplications-sketch/Talabat-v3/actions/runs/44803626534) | Success |

## Screenshots

These are unchanged files from the successful Home run's `brief24-home-cart` artifact (ID `14660474061`). They show the original customer page with synthetic offline QA data in WebKit, not a live catalog or a physical phone. The three page screenshots are actual 375 × 812 viewports; no full-page capture is used. The cuisine image is a focused 343 × 112 clip.

| Evidence | Image |
| --- | --- |
| Initial restaurant viewport; campaign does not obscure the first restaurant | [Restaurants](ru-375-brief30b-restaurants-viewport-fixture.webp) |
| Full one-line campaign text above navigation | [Campaign](ru-375-brief30b-campaign-viewport-fixture.webp) |
| Empty filtered result and unobstructed reset button | [Empty filter](ru-375-brief30b-empty-filter-viewport-fixture.webp) |
| Distinct burger artwork, steak photo and pilaf photo | [Cuisine closeup](ru-375-brief30b-cuisines-closeup-fixture.webp) |

Source ZIP SHA-256: `a33735bd932ba3eca500ffab0835652b05b5a692c61a933f0d72861d39b9ff02`.

## Behavior verified

- **AE-01:** Appropriate available cuisine art is retained; other cuisines use distinct catalog photographs with circular cropping. Restaurant cuisines do not fall back to a grocery basket. Missing or failed photos leave a usable text filter.
- **AE-02:** The complete short campaign copy fits on one line, without ellipsis. The floating pill stays 12 px above navigation, or above the cart bar when present. It remains hidden where it would overlap restaurant details or the empty state. Authored copy that exceeds the available width must be shortened at its source; the pill does not truncate it.
- **AE-03:** Filtered zero results show the requested RU/EN message, a small icon and reset button. Reset clears cuisine, search, sort and active filters. The check verifies that the whole button is above the fixed controls and can receive a pointer hit.
- Automated coverage includes RU 375, EN 390, admin audience behavior, Home smoke and financial parity.

## QA photo attribution

The fixture photos demonstrate the catalog-image fallback. They are sample photographs, not photographs of Romant or its actual menu. Source metadata and image bytes are retained in [`qa-fixtures/home-brief30.json`](https://github.com/merapplications-sketch/Talabat-v3/blob/8cd90a8ac14ff01413b63f79c5db676c0081d34d/qa-fixtures/home-brief30.json).

- **Steak:** [Restaurant Steak.jpg](https://commons.wikimedia.org/wiki/File:Restaurant_Steak.jpg), Brianbesley, [CC0 1.0](https://creativecommons.org/publicdomain/zero/1.0/). The fixture uses an unchanged 250 × 333 Wikimedia thumbnail, displayed with a circular CSS crop.
- **Pilaf:** [Plov.jpg](https://commons.wikimedia.org/wiki/File:Plov.jpg), Atilin, [CC BY-SA 3.0](https://creativecommons.org/licenses/by-sa/3.0/). The fixture uses an unchanged 330 × 247 Wikimedia thumbnail, displayed with a circular CSS crop. The photograph and its cropped rendering retain that license.
