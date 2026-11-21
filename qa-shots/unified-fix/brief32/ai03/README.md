# AI03 — original restaurant banner defaults

The original application HTML was served unchanged in offline WebKit. The SDK
fixture contains KFC and Romant Restaurant, zero store discounts/Happy Hours
(therefore zero DineOut offers), and no admin banners. No live services or
database writes were used by these tests.

The three defaults were compared with the same fixture on the clean, pinned
`8cd90a8ac14ff01413b63f79c5db676c0081d34d` checkout. RU375 and EN390 rendered
the original labels, artwork, colors, card shapes, and horizontal scrolling.
Both default-row screenshot comparisons have **zero differing pixels**.
`regression-before.json` records the original failure: the candidate had zero
defaults where the baseline had three.

**86 assertions passed.** Each default's actual click was checked separately:
Discounts opens the discount-filtered restaurant list; Free delivery opens the
free-delivery list; For you opens all restaurants. Empty offers retain the
existing honest empty-filter state. A separate offer variant checks the actual
matching restaurants, and a managed-banner variant checks replacement of the
default trio, localized images, optional CTA, and unchanged destinations.

The BRIEF-31 leading-inset CSS rule is now restricted to managed restaurant
rails. This preserves the original default scroll snapping and leaves the
managed rail unchanged. No other product files were edited for AI03.

Run from the checkout root:

```sh
python tools/brief32_restaurants_webkit.py /tmp/brief32-ai03 --case ai03
```

Use `TALABOT_WEBKIT` only when a local WebKit executable wrapper is needed.
These are browser/viewport checks, not physical-device or production testing.
