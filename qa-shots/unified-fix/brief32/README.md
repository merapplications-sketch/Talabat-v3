# BRIEF-32 delivery evidence

Scope: owner comments `7061725687`, `7061808632` (overrides), and `7061817909` (AI-07), from product baseline `1d54020a8a4de60e118b342b19fb8d0c3ab2e876`. Seven independently named product commits. No deployment or database writes.

## Verified candidate

The combined original-HTML WebKit run passed **746 assertions with 40 viewport/comparison screenshots**, plus the nested **78-check AI-05** run and its before/after videos. The independent Home smoke and financial comparison against `c5a8ff8a2d3a74301a3f35130a8f84316528449c` also passed. The primary Home hero is pixel-identical to the product baseline. The hero source remains literal BRIEF-31d except the explicitly requested countdown formatter.

The primary catalogue fixture matches the reported state: **two restaurants, no DineOut eligibility, no admin banners**. It uses the observed restaurant names/cuisine descriptions with synthetic offline menu/pricing/photo fixtures. Configured-banner screenshots and the third-card sizing case are explicitly separate fixtures. These are browser acceptance results, not production or physical-phone screenshots.

All product hashes, test dependencies, network traces, assertions, and screenshot hashes are recorded in [the combined results](acceptance/results.json). The exact pushed SHA is additionally checked by the existing Home and H-01 GitHub workflows; their run links are supplied with delivery.

## Requested changes and evidence

| Item | Result | Evidence |
|---|---|---|
| AI-01 | Existing scooter/burger/DineOut artwork fills the story frame; dark gradient, white copy, dark CTA; top story bars; edge taps/swipes; broad white-sheet arc. Original auth nodes/handlers remain. | [RU login](acceptance/ru-375-customer-login-story-1.webp), [DineOut story](acceptance/ru-375-customer-login-story-3.webp), [isolated auth/artwork audit](ai01/README.md) |
| AI-02 | AF-06 stays active. Preview data is loaded only for the exact preview hostname or explicit `?demo=dineout`. It remains separate from core stores, menus, and orders and carries `Тест`. | [Ordinary host: hidden](acceptance/ai02-ru-375-ordinary-host-empty-hidden.webp), [localhost opt-in](acceptance/ai02-ru-375-query-opt-in.webp) |
| AI-03 | Three original Restaurants banners, their original appearance, and independent destinations return when no managed banners exist. | [Original/candidate pixel comparison](acceptance/ru-375-default-banners-baseline-candidate.webp) |
| AI-04 | Orders artwork uses cover; dots sit inside; pause control removed. Existing countdown visibility/deadlines stay unchanged; segmented red-orange pill has day/hour/minute and last-24-hour modes. | [Days](acceptance/ai04-ru-375-orders-long-configured-fixture.webp), [Last 24 hours](acceptance/ai04-ru-375-orders-last24h-configured-fixture.webp), [No admin banners](acceptance/ai04-ru-375-orders-no-admin-banners.webp) |
| AI-05 | Small cart/favourite changes update existing controls without rebuilding the page. Known plain/segmented timers retain their live nodes; deadline changes/expiry use the full path. | [Integrated results](acceptance/ai05-integrated/results.json), [before video](acceptance/ai05-integrated/baseline-ru375-clicks.webm), [after video](acceptance/ai05-integrated/candidate-ru375-clicks.webm) |
| AI-06 | Cuisine choices use the existing declared restaurant description and cover. Romant contributes `Local & European`; blank KFC data stays unclassified. Menu sections and drinks are excluded; missing/broken-image types stay hidden. | [Cuisine row](acceptance/ru-375-restaurant-cuisine-types.webp), [missing types](acceptance/ru-375-cuisines-no-types.webp), [existing-field evidence](ai06/data-source.json) |
| AI-07 | Popular logo squares are 120×120px at 375px; font/card DOM, heart, Express, headings, and rows remain unchanged. | [Before](acceptance/ai07-ru-375-before.webp), [after](acceptance/ai07-ru-375-after.webp), [isolated 2.7-card geometry](acceptance/ai07-ru-375-three-card-geometry-fixture.webp) |

## AI-05 measured cause and result

The original quantity path replaced `#app`, removing the existing normal-flow add notice. Repeat `+` and `+` across notice expiry shifted visible Home content **58px** while the numeric scroll position could remain unchanged.

The candidate has **0px visible anchor drift and zero whole-app replacements across all nine tested small interactions**. Original notice appearance/lifetime remain. Browser scroll anchoring can compensate numerically when that existing notice enters/leaves flow; the visible content stays fixed. This report uses per-frame viewport geometry and source videos, not a claimed CLS score. Active plain/segmented countdowns, explicit deadline change/expiry, and Enter-key focus handoff are additionally covered.

## Scope and network isolation

The final source guard checks the whole customer source outside the named DineOut, timer, Orders controls, and small-render regions; frozen core/finance/backend/SQL, other app entrypoints, brand assets, dish/group styles, and existing Home styles remain unchanged. AI-03 default-banner comparisons have zero differing pixels against `8cd90a8a` in RU375 and EN390.

Final AI-02 gate testing evaluates the unchanged loader with plain location objects and a fetch stub. Browser navigation is restricted to localhost; positive query opt-in loads the real checked-in JSON. No virtual-host navigation is needed. Login CTA tests also use localhost destinations. No live database operations are performed by any acceptance harness.

## Reproduce

```sh
python tools/ci1_fast_webkit.py APPROVED_C5_BASELINE OUTPUT_DIR
```

The CI workflow provides the read-only approved worktree. The current-brief runner is `tools/brief32_webkit.py`; AI-05 has an additional `--integrated` mode that retains its runtime checks while the master verifies the combined source scope.
