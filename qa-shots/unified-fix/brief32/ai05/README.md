# BRIEF-32 AI-05 — stable small updates

## Cause measured before the fix

`quickAdd` / quantity buttons call `add → afterCart → render`. The original render replaced all of `#app`, including its photos, horizontal rails and the normal-flow status notice inserted by `safe-toast.js`.

On the original RU/375 application, the first add inserted the existing 58px notice. The next `+` removed it through the full render: `scrollY` stayed fixed, but every Home section moved upward by 58px. The same visible movement occurred when pressing `+` across notice expiry. Cold image/hero measurements were already stable; missing image dimensions were not the reproduced cause.

## Scoped change

The existing Home/menu templates still produce the control markup. A bounded updater applies changes only when the rest of the generated markup is identical: quantity controls, favourite hearts, Home header buttons, the cart bar, menu reward copy and its existing bottom spacer. The comparison ignores the live countdown's changing display text when its deadline and known structure are unchanged. For AI-04's segmented renderer, only the three numeric texts and their temporal accessible label are normalized in detached comparison templates; mode, language, units, separators, other structure and outer attributes remain compared. Its existing live DOM nodes/timer stay in place. Any other change uses the original full render. Existing direct flow notices are retained during a same-view full render. Keyboard activation hands focus from Add to the new plus button, and from the final decrement back to Add.

There are no CSS or template changes, new layout rules, notification redesigns, or changes to prices, permissions, auth, the dish sheet or group-order logic. The source outside the `RENDER` section remains byte-identical to the accepted base. The literal BRIEF-31d hero remains unchanged.

## Reproduction and result

Both runs serve the original app source with the same offline SDK input: only KFC and Romant Restaurant from `home-brief25b.json`, both open, store discounts zero, no admin banners or Happy Hours, descriptions `""` and `"Local & European"`, and the original four food records/asset URLs. Browser: WebKit; viewport: 375 × 812.

| Measurement | Original | Candidate |
|---|---:|---:|
| Repeat `+`: maximum visible anchor drift | 58px | 0px |
| `+` across notice expiry: maximum visible anchor drift | 58px | 0px |
| Whole-app replacements across 9 small interactions | 9 | 0 |
| Maximum visible anchor drift across all 9 candidate interactions | — | 0px |
| Initial Home screenshot | Reference | Pixel-identical |
| Hero/photo size before and after image decode | Stable | Stable |

The nine interactions cover first add, repeat `+`, minus, removal of the final item, re-add, `+` across notice expiry, favourite, menu `+` and menu minus. All **78 checks passed**, including exact original/candidate control output, literal expected quantities/cart prices, and isolated source-scope guards. No runtime, HTTP or transport errors were observed.

A separate, explicitly seeded Happy Hours test adds one active schedule to the same offline input. Two quantity taps more than one second apart retain the live countdown node, advance its text, and cause zero full-app writes/zero visible anchor drift. Changing the schedule's deadline causes one full render with the new deadline; expiry causes one full render and removes the expired timer/offer. Two focused Enter-key cases verify Add → plus and final decrement → Add focus transitions. This schedule exists only in the dedicated QA case, never in product defaults or the main screenshot input.

Clock/day segmented comparison cases exercise the real updater with minimal test-only known markup in the isolated checkout. Integrated runs require the actual AI-04 `countdownHTML` / `updateCountdown` API and actual segmented child nodes in the real-click test. A separate read-only import of the current AI-04 formatter also passed both comparison cases; the formatter source was not copied into this commit. That supplemental result is recorded in `segmented-formatter-check.json` with the formatter's SHA-256.

The original flow notice remains in normal flow for its original lifetime. The browser adjusts the numerical scroll offset as that space appears/disappears, while the visible content anchor remains stationary. These are per-frame WebKit pixel metrics, **not CLS**. Chromium could not launch in this environment (`socket() failed: Operation not permitted`); the supplied WebKit videos satisfy the requested video evidence. No physical iPhone or production/backend test is claimed.

## Evidence

- [Original interaction video](baseline-ru375-clicks.webm)
- [Candidate interaction video](candidate-ru375-clicks.webm)
- [Original Home](baseline-ru375-home.png) · [Candidate Home](candidate-ru375-home.png)
- [Per-frame metrics, input rows, checks and source provenance](results.json)
- [Actual AI-04 formatter compatibility check](segmented-formatter-check.json)

Base: `99db45a7f713615468e7ce9f2cb3c5493826a4e3` (product code `1d54020a`). Candidate `customer.html` SHA-256: `ba9aa9796c14d85c52c254685b0182d4ed19c6c4ab01936fc514c6be9686ab40`.

Unchanged customer bytes outside `RENDER` SHA-256: `68090e2da525afd604943cbb44416133c8e8a31163a6a9bf98e0857ceb5a48f3`. Unchanged literal hero SHA-256: `831021e2186f17fa9abb88e37a68b83307927b6e01d6f55bc43430c92c1fd371`.

Run from the repository root:

```sh
python tools/brief32_scroll_webkit.py qa-shots/unified-fix/brief32/ai05
```

`TALABOT_WEBKIT` may point to the local dependency wrapper. The baseline is read from its immutable Git revision; all external requests are intercepted. This is the isolated AI-05 source/QA result, before integration with the other BRIEF-32 items. No CI rerun, push or deployment was performed for this local item.

The consolidated BRIEF-32 runner may append `--integrated`. That skips only the two isolated customer/other-product byte guards, because the master runner verifies the combined authorized changes. All runtime, geometry, screenshot, video, timer, focus and source-stability checks remain active.
