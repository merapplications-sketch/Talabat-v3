# TALABOT — AI-01b acceptance

Scope: [owner review](https://github.com/merapplications-sketch/Talabat-v3/issues/48#issuecomment-7063613993) plus [32px sheet correction](https://github.com/merapplications-sketch/Talabat-v3/issues/48#issuecomment-7063632254). Accepted base: `7cc3136280b491cf23c4bf7e8f723d48ccfb10ce`; AI-02 through AI-07 remain frozen.

## Delivered change

- Login defaults use the same original delivery and burger banner PNGs, plus the unchanged localized DineOut files. All four source files are SHA-256 pinned; see [exact artwork provenance](ARTWORK.md).
- Images fill the existing story frame with `object-fit: cover`. Delivery and DineOut keep their focal subjects on the right; the burger stays centered. The original artwork pixels and embedded lettering are unchanged.
- The white sheet has a straight horizontal top, exactly `32px 32px 0 0` corners and its existing light upward shadow.
- Authentication DOM, handlers, fields, story bars, swipe/tap behavior, timing, localized foreground copy, CTA and the previously accepted product changes are unchanged.

## Requested screenshots

These are actual viewport captures from the original application HTML in offline WebKit. Login images are the real repository assets, not substituted fixtures.

| Slide | RU / 375px | EN / 390px |
| --- | --- | --- |
| Delivery | [RU delivery](acceptance/brief32/ru-375-customer-login-story-1.webp) | [EN delivery](acceptance/brief32/en-390-customer-login-story-1.webp) |
| Burger | [RU burger](acceptance/brief32/ru-375-customer-login-story-2.webp) | [EN burger](acceptance/brief32/en-390-customer-login-story-2.webp) |
| DineOut | [RU DineOut](acceptance/brief32/ru-375-customer-login-story-3.webp) | [EN DineOut](acceptance/brief32/en-390-customer-login-story-3.webp) |

## Local verification

The integrated `tools/ci1_fast_webkit.py` gate passed: Home RU/375 smoke and approved financial parity, **788 assertions** covering SOURCE and AI-01 through AI-07, **40 screenshots**, and **105 nested AI-05 scroll checks**. [Main results](acceptance/brief32/results.json), [scroll results](acceptance/brief32/ai05-integrated/results.json), and [Home smoke](acceptance/ru-375-home-smoke.webp) are archived without modification.

The run started from the accepted base with the AI-01b changes in the working tree. Its `git_head` therefore records that base, while `product_sha256` records the exact tested product bytes, including the new PNGs. Every recorded product hash was compared with the delivery files, and `source_unchanged_during_run` is true. The frozen Home hero remained pixel-identical to the accepted reference.

The focused source guard permits only the exact image expression, 32px radius, delivery focal selector, two image additions and associated acceptance files. The H-01 workflow diff adds only the two exact PNG paths to its existing allowlist. No previous evidence is replaced.

The remote Home and H-01 workflows must independently succeed on the implementation commit. Their final run URLs and tested SHA are supplied with the delivery; these local results do not stand in for remote CI.

## Test boundary

Local visual acceptance uses the original HTML with an offline synthetic SDK. The existing H-01 workflow verifies actual login against disposable LOCAL Supabase. No physical phone or production backend was tested. No production data, schema, financial logic, credentials or deployment was changed.
