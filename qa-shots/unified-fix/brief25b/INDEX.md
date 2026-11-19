# TALABOT — BRIEF-25b / X-01…X-11 (review only)

Evidence from offline WebKit **RU/375**, using `qa-fixtures/home-brief25b.json` and `tools/brief25b_webkit.py`. All restaurant/reel/advertisement data in these screenshots are **synthetic test fixtures**, not verified live offers, ratings, or comments.

## Owner review captures

- [Two Flash Sale cards, row-first](ru-375-flash-two-fixture.webp)
- [Two Nearby cards, row-first, rating + ETA + delivery fee](ru-375-nearby-two-fixture.webp)
- [Recommended after Don't Miss, with visible «Реклама»](ru-375-recommended-after-ad-fixture.webp)
- [Four What's New reels, horizontal 2.5](ru-375-whats-new-four-reels-fixture.webp)
- [Reel #2 opened with connected mock likes, comments, views](ru-375-reels-second-linked-fixture.webp)
- [Reel #2 with synthetic comments panel open](ru-375-reels-second-comments-fixture.webp)
- [DineOut cover image, small logo, rating, distance, 2.5 cards](ru-375-dineout-two-and-half-fixture.webp)

The production UI hides reel social actions when the optional stats provider is absent. No fixtures or generated images have been added to production app defaults.

## Safety and provenance

- Branch: `review/unified-fix-brief15-20261117` only; not merged or deployed.
- Original approved `assets/customer-c/home-sections.css` was retained byte-for-byte at its start, with BRIEF-25b overrides appended.
- No changes to `talabat-core.js`, SQL schema, finance/dispatch behavior, or production data.
- Source owner assignment: [Issue #48 / BRIEF-25b](https://github.com/merapplications-sketch/Talabat-v3/issues/48#issuecomment-7015238650), with X-05…X-11 in the next two comments.

Full test definitions are inspectable in the repository; CI must be checked on the eventual delivery SHA rather than inferred from screenshots.
