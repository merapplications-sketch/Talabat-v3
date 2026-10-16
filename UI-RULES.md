# UI rules for repeated elements (v57d). Reference — not a redesign. Checked by `python3 tools/ui_rules_check.py`.

## Fields (text, number, phone, search, select, textarea)
- **Text size ≥ 16 px on a phone** (iOS Safari zooms into smaller fields). Checked live on every qa_all screen + partner page, and
  statically for inline `font-size` on fields.
- **Only valid CSS:** never `font:<size> inherit` (a font shorthand cannot contain `inherit` — the whole rule is dropped;
  that is how the partner fields became 13.3 px). Use `font-family:inherit;font-size:16px`. Checked statically.
- **Never block zoom:** the viewport stays `width=device-width,initial-scale=1,viewport-fit=cover` (no maximum-scale /
  user-scalable). Do not hide horizontal overflow to mask a layout bug.
- **One field rule per app, reused** (already the case; same values in each app):
  `padding 12px 14px · radius 14px · background #f3f3f6 · border 1.5px transparent · 16 px · focus: orange border + white`
  - customer: `.fld` · admin: `input,select,textarea` · merchant: `input[type=…], .fl select, .fl textarea` · driver:
    `input[type=text|number]` · partner page (v57d): same values; error state red border + light red (aria-invalid).

## Kept different on purpose (approved looks / different jobs)
- Search boxes inside a bar (customer home `.hsf`, customer `.sb`, admin orders search): borderless field inside a
  rounded bar — a different element (search bar), only its text size follows the 16 px rule.
- The 4 apps keep their own navigation: customer bottom nav, admin tab strip / dark side menu ≥ 1024 px, restaurant
  bottom / side menu, courier nav. Not unified by force.
- Buttons: customer `.btn` (+ `.s` secondary), staff apps `.b` (+ `g` grey, `r` red) — same role, two existing families;
  each app uses one family consistently.
- Cards: each app has one `.card`; the restaurant cover, the admin KPI tiles, the courier swipe bar are different elements.

## Fixed in v57d (safe, minimal)
| Where | Before | After |
|---|---|---|
| customer home search (`.hsf input`) | 14 px | 16 px (placeholder may show a few letters less) |
| restaurant reject note (`.rjta`) | 14 px | 16 px |
| courier phone field (apply screen, inline style) | 14 px | 16 px |
| partner page fields | own look (white, 1 px line, radius 12) | the shared field rule above; disabled state added |
| preview strip selector (tool only) | 12 px | 16 px |

## Proposals (visible change of an approved look — NOT done)
1. Restaurant header store selector (`.top select`, pill, 12 px, approved v56h header): under 16 px, so iOS may zoom when it is
   tapped. Options: 16 px text in the pill (header text larger), or a sheet with the store list instead of a native select.
2. Restaurant reject note (`.rjta`): grey-bordered field (#f7f7f9) while other restaurant fields are #f3f3f6 without border —
   could use the shared field rule.
3. Courier phone field on the apply screen: inline style duplicating the shared rule (#f7f7f9, 1.5 px #eeeef1) — could use it.
