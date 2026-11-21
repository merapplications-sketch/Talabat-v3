# AI06 — declared restaurant cuisine types

The existing catalogue stores its displayed restaurant type in `description`,
already exposed by the unchanged customer binding as `STORES.d`. The inspected
schema and core have no dedicated cuisine column. The sanitized source record
is in `data-source.json`: Romant Restaurant declares `Local & European`; KFC's
description is empty. KFC therefore receives no invented `Fast food` label.

The cuisine source now groups those existing restaurant descriptions and uses
an existing restaurant cover (`STORES.i`) as the type image. It never reads menu
sections, dish photos, or a fabricated artwork mapping. Blank descriptions,
Drinks/Напитки/Beverages, and the previously excluded sauce/add-on labels do not
produce types. Missing or failed covers hide the entire chip; if none remain,
the row disappears. Selecting a chip filters real restaurant IDs, and a failed
image clears its selection so no invisible restriction remains.

The original circle sizes and filter layout are retained. Only the type label
wraps to two lines, making `Local & European` readable in the existing 72px chip.
No customer binding, core, database, countdown, card, product-sheet, group,
logo, or financial logic was changed.

**75 focused AI06 assertions passed**, with six original-HTML WebKit screenshots.
The initial red run in `regression-before.json` rendered menu sections such as
Burgers, Drinks, Steaks, and Pilaf instead of the declared restaurant type.

The principal fixture has two restaurants, zero DineOut offers, and zero admin
banners. Separate synthetic variants verify two explicitly declared types,
case/whitespace grouping, non-restaurant exclusion, missing data/images, and
actual image-decoder failure and recovery. `Fast food` exists only in the
explicit test variant. The full AI03 + AI06 run also passed **161 assertions**;
both original default-banner comparisons still have zero differing pixels.

Run from the checkout root:

```sh
python tools/brief32_restaurants_webkit.py /tmp/brief32-ai06 --case ai06
python tools/brief32_restaurants_webkit.py /tmp/brief32-restaurants --case all
```

The harness uses synthetic offline SDK responses only. It performs no live
queries or writes. These checks do not claim physical-device or production QA.
