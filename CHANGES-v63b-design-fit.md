# v63b — visual fit to the v06.1 reference (local; not merged, not published)
Branch `design/customer-v06` on top of v63. Inside the current design task (no parallel work). `customer.html` (CSS + two small
markup points), `tools/design_v06_check.py` (new part D) and `tools/build_preview.py` (preview-only test photos). No SQL, no
data, no other app. Owner note 18 Oct 00:40 with three iPhone screenshots (store sheet, profile, cart — the notes that did not
arrive with the 21:16 message).

## How it was measured
- Reference pages (`Sources/pages/*.html`, with their own Nimbus Sans files) and the app at the **same CSS width (390)** with the
  **same kind of content**: the app fixture renamed to the reference content (Двойной чизбургер, Размер / Дополнительные
  ингредиенты, Romant Restaurant, Фарид Каримов…), with and without test photos, plus the normal long-name fixture.
- Every text role: font-size / line-height / weight, element heights, gaps — dumped from both pages and compared.
- The owner's screenshots are 1290×2796 = **430 CSS px** (iPhone Pro Max), not 390. Chromium at 430×932 reproduces them line
  for line (same breaks, same positions) → **no text enlargement by the phone** (no Dynamic Type, no text-size-adjust effect);
  the phone settings were not the cause. `text-size-adjust:100%` is now set anyway so Safari never inflates text.

## What made it look bigger / heavier (found, not assumed)
1. Weights: the app used 500 / 600 / 800 / 900 in many places; the design font has only 400 and 700, so in the reference every
   600 shows as 700 and every 800 / 900 as 700. On the iPhone system font 800 / 900 are real heavy cuts → heavier text.
2. Sizes not on the reference role: cart line name 16→18 and price 16/800→18/700, multi-choice option 14/600→13/400,
   «Особые пожелания» line 24→21, sheet button price 18/800→20/700, profile rows 15→14 (row 56→64), name 17→18, phone / link
   13→12, wallet balance 32/800→36/700, points line 34→41, checkout titles 16→17, captions 11→12, row titles 13→14, list
   section titles 18→20, restaurant name 16→15, rating 14→12, chips 13→12, Home category labels 600→400, «Все» 700→400 …
   (full table: preview → «Таблица ролей»). Some were too small, some too big — both corrected to the reference.
3. Spacing: section header top margin 24→16 on the store page (the 44 px header row added its own space), search 20→16,
   Home bento 6 px lower than the reference → 0; a separator line under each option group in the sheet (none in the reference)
   removed.
4. The font itself (kept by decision until the licence review): the system font is about 4–7 % wider than Nimbus Sans at the
   same size. This is the only remaining size difference and it is not corrected by shrinking text.

## Fixed defects
- Sheet without a dish photo: the «Хит» badge floated over the dimmed page (owner screenshot 1) → the badge sits on the photo only
  when there is one; otherwise it is a small pill above the dish name. Photo above the sheet when available: checked (test photos).
- Free-delivery line: amount bold, the rest regular (reference).

## Kept on purpose
Fields 16 px, every target 44 px (limits only — they did not enlarge text); option cards in two columns without pictures
(no option images in the data); everything listed in CHANGES-v63 §A that still applies.

## Preview with test photos
`customer/customer.html?photos=1` in the preview: harmless «TEST PHOTO» pictures on the preview's DEMO rows (stores, dishes,
3 top + 1 bottom demo banners) with a dark strip «ТЕСТОВЫЕ ФОТО (только превью)». Built only by `tools/build_preview.py`; the app
and its data are unchanged; without `?photos=1` the preview is as before.

## Checks (Chromium)
- design_v06_check 153/153: new part D — 30 text roles at 390 equal to the reference size / line-height / weight; only weights
  400 / 700 in the design layer; no floating badge without a photo; no separator under option groups.
- Affected suites re-run, none weakened: cart 0, sheet OK, hdr 0, ui_rules 0, smoke 0, qa_all customer 0, flow 0, uat2 48/0,
  uat3 70/70, patch38_ui 50/50. Not re-run (untouched): branch, patch37 (no change in their parts).
- Not tested: a real iPhone (Chromium at 430 matched the owner's screenshots, but it is not an iPhone check), the live DB.

## Decisions still open (only the real ones; already settled items are not asked again)
- D1 cart button in the Home header (recommend keep).
- D2 admin banners cropped to the bento tiles (recommend keep + upload size guide later).
- D3 list look for every category (recommend keep).
- D4 masked phone in the profile (recommend keep).
- D7 «Рейтинг» chip: sort (today) or «4,0+» filter.
- D8 bottom navigation in the reference style (all pages; recommend a separate small step).
Closed: D6 (the image arrived — these notes). Font: stays as decided; the measured remaining width difference is recorded above.
