# BRIEF-31 — review delivery and viewport evidence

Implemented AF-01–AF-06 and AG-01–AG-06 from the owner's [updated brief](https://github.com/merapplications-sketch/Talabat-v3/issues/48#issuecomment-7052011112), retaining AF-04/AF-06 from the [original brief](https://github.com/merapplications-sketch/Talabat-v3/issues/48#issuecomment-7051574803), and applying the [supplied DineOut artwork override](https://github.com/merapplications-sketch/Talabat-v3/issues/48#issuecomment-7052345068).

## Delivery revision and acceptance

- Review branch: `review/unified-fix-brief15-20261117`.
- Base: `2498961686bf81aa3b1fe73e3099af487d09ec93`.
- **Code + tests + guard revision:** [`cd7e0b6bcf7d66abfb6732d72f704ac12c6f899f`](https://github.com/merapplications-sketch/Talabat-v3/commit/cd7e0b6bcf7d66abfb6732d72f704ac12c6f899f).
- Final product revision: `b55bf5fd4cf38061551a6f8ee78f5154dc177bb5`; product tree `5434d55a7d2239a5e953f088bd4fdbf2182b5d6b`.
- **Home: SUCCESS** — [run 44834383823](https://github.com/merapplications-sketch/Talabat-v3/actions/runs/44834383823), on the code revision above. Its log confirms `CI1_HOME_RU375_SMOKE_PASS; FINANCIAL_PARITY_PASS`, `BRIEF31_PASS 358 assertions; 34 viewport screenshots`, and `CI1_FAST_WEBKIT_PASS`.
- **H-01: SUCCESS** — [run 44834383817](https://github.com/merapplications-sketch/Talabat-v3/actions/runs/44834383817), on the same code revision: **24/24** original-app local authenticated contexts, **0 blockers**.
- This directory is an evidence-only `[skip ci]` delivery. H-01 may also append its own evidence-only commit; neither changes the tested product.

The retained local acceptance run passed **358 assertions across all 12 IDs** in **21 isolated browser contexts**, with zero unexpected external requests, JavaScript errors, failed local requests, or HTTP errors. It captured **34 focused viewport screenshots**, plus **one separate Home smoke screenshot**. All captures use the actual WebKit viewport: **RU 375×812** and **EN 390×844**. They are not full-page captures or resized screenshots.

[`results.json`](results.json) is copied unchanged from the final accepted run. It records each assertion, network/runtime observations, source hashes, execution times and screenshot hashes. Local product HEAD `eb12d4d14ae1fa1120d17c73f2db52d074a7a120` and remote product HEAD `b55bf5fd4cf38061551a6f8ee78f5154dc177bb5` have the **same complete tree**; commit IDs differ because the connector recreated commit metadata. The subsequent code revision adds only the acceptance harness and authorized CI guard changes. GitHub then reran the full focused suite successfully on that exact code revision.

- Local results SHA-256: `31971baecc1e9a1d980d0e82d567e1aeeeeddaa88145cb10c779a66d1e55002a`.
- Acceptance harness SHA-256: `904ac29c1d9a2d13f3783ac87dc15d2c256bdb32ae2d0776b147e5a06dc15b32`.
- Controlled fixture clock: `2026-11-18T09:00:00Z`.
- Accepted local run: `2026-11-20T23:03:12Z`–`23:04:01Z` (UTC); source remained unchanged throughout.
- [`manifest.json`](manifest.json) lists byte sizes, Git blob IDs, SHA-256 hashes and image dimensions. [`ci-results.json`](ci-results.json) records the final remote statuses; text summaries preserve the relevant log lines without credentials.

## Item commits and resulting behavior

| ID | Item commit | Implemented behavior |
| --- | --- | --- |
| AF-01 | [b8106214](https://github.com/merapplications-sketch/Talabat-v3/commit/b81062148470a95ef4442f4f824fccdf4e262cb7) | One admin banner editor: main/localized images, multiple placements, optional localized CTA, AC-03 destination/link, order. A blank CTA creates no overlaid button; the whole slide remains clickable. |
| AF-02 | [510bc116](https://github.com/merapplications-sketch/Talabat-v3/commit/510bc116924a4e7526a3bf8a5e41e2890975e446) | Exact banner end date/time; countdown only on its banner, day format above 24h, removal at expiry. No inferred timer from an unrelated promotion. |
| AF-03 | [742b057b](https://github.com/merapplications-sketch/Talabat-v3/commit/742b057b18546efeef6b3fc8d6b34ff5ae67ce91) | “на твой вкус” / “for your taste”; eligible admin pins first with advertising badges, then automatic filling excluding drinks, extras and sauces. |
| AF-04 | [3e7c12f8](https://github.com/merapplications-sketch/Talabat-v3/commit/3e7c12f826695607aa88a407b696457b4635c171) | Removes dish-options overhang; option labels, badges and prices fit the 375px viewport. |
| AF-05 | [a892fdd4](https://github.com/merapplications-sketch/Talabat-v3/commit/a892fdd414aa0d2b56c95b04dbd1c0b10328ded2) | One larger My orders slide with the whole image visible; default 3s rotation, per-placement admin duration when exposed, pause/resume and safe touch handling. |
| AF-06 | [e37aadfb](https://github.com/merapplications-sketch/Talabat-v3/commit/e37aadfb2ab3b92fe3a6a3a36a566da4496b62f5) | Hides the entire DineOut section when no restaurants qualify. |
| AG-01 | [d29a5835](https://github.com/merapplications-sketch/Talabat-v3/commit/d29a583536c6c3271c8dbced08eafb0df6446cd4) | Popular shows 2.5 smaller cards at 375px; removes the decorative slashes from the heading. |
| AG-02 | [b45f43f2](https://github.com/merapplications-sketch/Talabat-v3/commit/b45f43f2eeeaa6b6244fc864ee001d5dfc939bc6) | Exact owner-supplied RU/EN artwork; TG uses RU as instructed; localized alt text. |
| AG-03 | [e04c22fe](https://github.com/merapplications-sketch/Talabat-v3/commit/e04c22fef7f2c8cc0de7e77973bd39b1b8dd7193) | Restaurant top rail uses managed advertising banners with separate destinations and a 16px first inset. |
| AG-04 | [9269c265](https://github.com/merapplications-sketch/Talabat-v3/commit/9269c2655616382a5eed72b2550a8b04ab214523) | Circular sort icon; orange dot for non-default sorting; selected text appears inside the sheet only. |
| AG-05 | [f6bc91dc](https://github.com/merapplications-sketch/Talabat-v3/commit/f6bc91dcbef481bf834eeb57120aa7d1424a8a8f) | Upward draggable options surface over the dish picture; picture shrinks; rounded edge and shadow, with click/keyboard alternatives. |
| AG-06 | [82c072e9](https://github.com/merapplications-sketch/Talabat-v3/commit/82c072e9f388b949d98759ccb75c98b2edda82cc) | Back preserves the group and returns to the previous screen; a persistent resume pill reopens it; one fixed-position close/reopen toggle. |

Four focused review follow-ups preserve default action selections, side-only placement, current-file upload results and concurrent-edit warnings; keep the entire orders card visible; and pause rotation for the full duration of a held touch/pointer, including cancellation and resume cooldown. These are included before the final product revision and covered by the accepted suite. The source comparison also preserves required modifiers and existing financial calculations.

## Viewport evidence

Each pair below uses RU 375×812 and EN 390×844. The admin interface retains its existing Russian copy in both browser contexts; the screenshots show the requested viewport sizes and separate localized banner settings.

| Evidence | RU / 375 | EN / 390 |
| --- | --- | --- |
| Admin placements and localized uploads — AF-01 | [RU](ru-375-admin-banner-placements-images.webp) | [EN](en-390-admin-banner-placements-images.webp) |
| Admin action, optional CTA and exact expiry — AF-01/02 | [RU](ru-375-admin-banner-actions-expiry.webp) | [EN](en-390-admin-banner-actions-expiry.webp) |
| Admin per-placement timing — AF-05 | [RU](ru-375-admin-placement-timing.webp) | [EN](en-390-admin-placement-timing.webp) |
| Admin sponsored dishes — AF-03 | [RU](ru-375-admin-taste-pins.webp) | [EN](en-390-admin-taste-pins.webp) |
| Managed Home banners — AF-01/02 | [RU](ru-375-managed-home-banners.webp) | [EN](en-390-managed-home-banners.webp) |
| Managed campaign destination — AF-01/02 | [RU](ru-375-managed-campaign-sheet.webp) | [EN](en-390-managed-campaign-sheet.webp) |
| Taste advertising — AF-03 | [RU](ru-375-taste-advertising.webp) | [EN](en-390-taste-advertising.webp) |
| Dish options collapsed — AF-04/AG-05 | [RU](ru-375-dish-options-collapsed.webp) | [EN](en-390-dish-options-collapsed.webp) |
| Dish options expanded — AF-04/AG-05 | [RU](ru-375-dish-options-expanded.webp) | [EN](en-390-dish-options-expanded.webp) |
| Whole orders banner — AF-05 | [RU](ru-375-orders-large-banner.webp) | [EN](en-390-orders-large-banner.webp) |
| Empty DineOut hidden — AF-06 | [RU](ru-375-empty-dineout-hidden.webp) | [EN](en-390-empty-dineout-hidden.webp) |
| Compact popular rail — AG-01 | [RU](ru-375-popular-rail.webp) | [EN](en-390-popular-rail.webp) |
| Supplied DineOut artwork — AG-02 | [RU](ru-375-dineout.webp) | [EN](en-390-dineout.webp) |
| Restaurant advertising and sort icon — AG-03/04 | [RU](ru-375-restaurant-advertising.webp) | [EN](en-390-restaurant-advertising.webp) |
| Sort sheet — AG-04 | [RU](ru-375-sort-sheet.webp) | [EN](en-390-sort-sheet.webp) |
| Preserved group and resume pill — AG-06 | [RU](ru-375-group-preserved-resume.webp) | [EN](en-390-group-preserved-resume.webp) |
| Single group toggle in closed state — AG-06 | [RU](ru-375-group-closed-toggle.webp) | [EN](en-390-group-closed-toggle.webp) |

Separate existing Home smoke: [RU 375×812](ru-375-home-smoke.webp).

## Optional field activation and scope limits

The implementation obeys the requested **no SQL** boundary. [`sql/proposed/brief31-banner-system.md`](../../../sql/proposed/brief31-banner-system.md) documents the contract; it is not a migration.

- The unified optional fields use `banners.presentation`. The editor enables them only when a returned banner exposes that field or an approved backend already exposes numeric setting `banner_presentation_ready=1`. Missing fields remain disabled with an explanatory notice. Existing main image, title, target, order and dates stay editable.
- Per-placement duration uses existing returned keys `banner_rotation_<placement>_seconds`, with a default of 3 seconds. The editor never silently creates absent keys.
- Sponsored dishes reuse exposed `stores.home_sponsored_dishes`. If absent, those admin controls remain disabled. Existing server permissions still decide whether writes succeed; failed saves preserve the draft.
- `ends_at` already exists; admin entry/display uses Asia/Dushanbe, UTC+05:00, and stores the exact ISO deadline.
- This delivery demonstrates both present-field and missing-field contracts with synthetic rows. It does **not** claim production schema activation or a successful write to production.
- No `talabat-core.js`, driver, merchant, backend SQL or financial logic change; no merge or deployment. H-01 uses its existing disposable local schema workflow. No physical iPhone was tested.

AF-04's original owner screenshot was not recreated pixel-for-pixel. The fixture reproduced horizontal options overhang, and final checks verify long labels, required badges and option prices fit without horizontal scrolling. Merchant spelling mistakes were not edited.

## DineOut source integrity

Both 1200×400 WebP files were copied byte-for-byte from owner source commit `3032c7cb2bacc8cad43e0f5d098a31d20ac3d486`. Guards pin their exact Git blobs:

| Asset | Git blob |
| --- | --- |
| `assets/customer-c/dineout-header-ru.webp` | `63bca41639ccefcbde4bf8c9d8049303d5e9fdd9` |
| `assets/customer-c/dineout-header-en.webp` | `c70b04c0ca131f0456eaddcb3299d67593ce70d3` |

## Reproduce

From a checkout with the Git history, Playwright 1.57.0, Pillow 11.3.0 and WebKit installed:

```sh
git worktree add --detach /tmp/talabot-approved-home c5a8ff8a2d3a74301a3f35130a8f84316528449c
python tools/ci1_fast_webkit.py /tmp/talabot-approved-home qa-artifacts/ci1-fast
```

For only the focused 12-item suite:

```sh
python tools/brief31_webkit.py qa-artifacts/brief31
```

The suite serves the original checkout HTML/CSS/JS on loopback, substitutes synthetic SDK data, and fails on unexpected foreign requests. It does not contact a production database. H-01's separate successful workflow is the authentication acceptance gate.
