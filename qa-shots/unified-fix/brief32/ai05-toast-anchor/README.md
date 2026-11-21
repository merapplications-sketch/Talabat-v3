# AI-05 corrective proof: flow-notice anchoring

## Reproduced cause

The prior small-update fix retained the Home/menu DOM, but the shared core notice was still inserted and removed in normal flow. With native browser anchoring disabled, the same actual Add interaction moved the reading anchor by 58px despite zero `#app.innerHTML` writes; the original 2.3-second expiry moved it by 58px again. The notice is 38px high with its existing 8px/12px margins. Stacked notices can shift by 50px because margins collapse, so the correction measures displacement rather than assuming a fixed height.

`before-notice-anchor.json` records this failing case on the unchanged product source at `31b6afa707f19128e3c3a5d1ce69cfc53e93b5a3`. The baseline before/after videos compare the original accepted render behavior at `99db45a7f713615468e7ce9f2cb3c5493826a4e3` with the corrected candidate on identical two-restaurant input.

## Narrow correction

Only `assets/shared/safe-toast.js` changes product behavior. For a direct `#app` notice on customer Home/menu, the new helper captures the current connected content node immediately before insertion/removal and corrects only the residual viewport displacement after the browser's own anchoring. It uses numeric `window.scrollBy(0, delta)`. It never restores a saved creation-time scroll offset.

At scrollY 0, the notice remains visible in its original flow position. A changed view, detached content, staff URL, nested modal host, or open dialog is excluded. Notice styling, text, roles, focus, core lifetime and the core file remain unchanged. Removing the explicitly marked helper block and two call-site lines restores the prior shared file byte-for-byte apart from its final newline; `source-scope.json` records this check and exact hashes.

## Final focused verification

Command, run from the repository with an available Playwright WebKit runtime:

```sh
python tools/brief32_scroll_webkit.py OUTPUT --integrated
```

The final source passed **105/105 checks** on Playwright 1.62.0 / WebKit 26.5 at RU 375×812. The final integration CI must verify the pinned Playwright 1.57.0 environment; this local report does not claim that version or a physical iPhone was tested.

| Browser anchoring setting | Actual interaction | Maximum visible anchor drift (px) | Whole-app writes |
| --- | --- | ---: | ---: |
| auto | first | 0 | 0 |
| auto | repeated | 0 | 0 |
| auto | expiry | 0 | 0 |
| auto | navigation | 0 | 0 |
| none | first | 0 | 0 |
| none | repeated | 0 | 0 |
| none | expiry | 0 | 0 |
| none | navigation | 0 | 0 |

The `none` setting is test-only CSS. Support/computed values are recorded, never required: browsers without this CSS feature must still meet the same zero-drift assertions.

The gate also passed notice expiry after a deliberate user scroll, navigation before expiry, visible top-of-page notice behavior, menu insertion/expiry, staff-path and open-dialog exclusions, all nine existing cart/favourite/menu interactions, active segmented countdown retention and comparison guards, changed/expired deadline fallbacks, keyboard Add/final-decrement focus, and delayed-image geometry. The Home screenshots remain pixel-identical. Runtime/network error collections are empty.

## Evidence

- `before-notice-anchor.json`: pre-fix per-frame reproduction, actual Add and native expiry, with no native browser anchoring.
- `results.json`: complete lossless final report, source/fixture hashes, per-frame measurements, all assertions and traces.
- `source-scope.json`: correction source boundary and byte comparison.
- `baseline-ru375-clicks.webm` / `candidate-ru375-clicks.webm`: same nine actual interactions on original/corrected source.
- `baseline-ru375-home.png` / `candidate-ru375-home.png`: unchanged initial Home capture.

The staff-path check exercises the exact pathname exclusion with the actual shared notice primitive; it is not a new full staff-app suite. No production/backend, deploy, database or money logic is exercised or changed by this correction.
