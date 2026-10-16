# UAT batch 1 — test log (branch fix/uat1-v56)

Kept here so the details are not re-explained in every report. Chromium (Playwright) unless written otherwise.
**Safari / iPhone cannot be run in this environment**; nothing below is evidence for Safari.

## How to run
| Test | Command | What it covers |
|---|---|---|
| Admin UAT fixes | `python3 tools/admin_uat_check.py` | the 10 UAT items, sample consistency (totals, commission formula), forms at 360/390/430 RU/EN |
| Forms / refresh / back / reload | `python3 tools/form_keep_check.py <admin_preview> [--quick]` | 7 forms × redraws RU/EN, portrait/landscape; real polling; rotation; conflicts with server edits; Texts states; reload restore (within 30 min, not after sign-out); back to origin (rating, ticket, customer, courier); customer history paging; real taps on ticket / rating / assign / map close; diagnostic log has no personal data |
| Staff look | `python3 tools/staff_ui_check.py <admin_preview> <merchant_preview>` | every menu entry by real tap (admin 12, restaurant 4), side menu ≥1024px, no sideways scroll, preview strip never over the page, no cut button text, bottom menu does not hide content, icon-only buttons named, no emoji in controls/headings, restaurant page patched on real refresh (search text + same field) |
| Preview safety | `python3 tools/preview_check.py <admin_preview>` | every write refused, 0 Supabase requests |
| Map tiles | `python3 tools/map_tile_check.py <admin_preview> <leaflet_dist>` | OSM tiles carry the site origin only; pages still send no Referer |
| Other apps | `qa_all, flow_check, cart_check, courier_check, smoke, hdr_check, overflow, overflow2, sheet_check, branch_check` | customer, restaurant, courier screens and flows (shared core file) |
| SQL | `sql/test_patch35.sql` on local PostgreSQL | admin_search_orders (patch 35 is NOT applied anywhere) |

Previews are built with `python3 tools/build_preview.py <dir> admin|merchant` (demo data, writes refused, no Supabase).

## Analytics numbers vs source (demo data)
- Admin tiles: orders 7 = loaded orders; revenue 415.00 = «Итого» of the 1 delivered order (ord4); commission 44.00 = ord4 commission
  = (440 items − 0 store discount − 0 happy hour) × 10 % (place_order formula).
- Restaurant «Аналитика» (day): done 1 (ord4), revenue 440 = items − store discount; «После комиссии» 374 = 440 − 44 (10 %) − 22
  (free delivery paid by the restaurant, fee_waived); declined 2 = ord5 cancelled + ord6 rejected.
  Note (not changed): this screen takes the store's CURRENT commission % for every order, not the % stored on the order.
- Earlier demo-data errors (fixed in test data, not in the app): fixed commission 10 for every sample; text ids (`t1`, `ord4`) that
  production never has; no About/Privacy rows.

## Look (v56i → v56j)
- v56i changed the phone layout (white header, card borders/radii, button and field sizes, KPI order, tab icons, restaurant title row).
  The owner did not approve it: v56j restores the v56h layout, sizes and spacing on phones/tablets and keeps only the shared icon family;
  the dark side menu stays for screens ≥1024px.
- Preview strip: no longer sticky (it covered page titles while scrolling); the counter/buttons are at the top of the page.
- Restaurant: the store selector takes the full width on phones (name readable); the logo was cut by the cover's clipping (layout bug
  present before v56h, independent of data) — fixed. An empty grey cover with a picture icon = the demo store has no photos (data, not layout).

## Safari evidence so far (owner, iPhone)
- Jumps at the moment of rotation (resize 0 ms), last redraw 3–4 s earlier, no app scrollTo → not moved by the app.
- Probable cause (not proven): iOS text enlargement in landscape → page re-flow. `-webkit-text-size-adjust:100%` added (admin, restaurant).
- The preview log line `TRACE` after a rotation shows text size, page height, top anchor, app scrollTo and redraws — needed from the iPhone.
- Return after 190 s in the background: page not reloaded, position kept. Draft kept on Safari: not yet confirmed.

## Follow-up 16 Oct 15:54
- Jump 302→0 at 15:12:23 happened WITH `text-size-adjust:100%` already in place → text enlargement does not explain it. Open.
  Code paths that can move the page without a tap all go through `window.scrollTo` (render keep-position, scrollHold after a full
  rebuild, reload restore) and are logged as «app scrollTo» when the move is >80 px. No other scroll API is used in admin
  (no scrollIntoView, no body overflow toggling, no autofocus; focus() only in the link picker after a tap).
- TRACE wording fixed: the old line measured the first `.card small` on screen (a different element after a redraw) and called any
  change "iOS text inflation". Now: a fixed hidden probe, computed size + rendered width, neutral wording, no browser name.
- 15:13:56 load after 16 s in background: the app reloads itself only on a tap (error banner / boot retry) or on sign-out
  (logged as «sign-out» / «INACTIVITY SIGN-OUT»). Cause of that reload not proven (the browser, by elimination); the screen/draft
  restore after a reload exists since v56f (sessionStorage, ≤30 min); whether it ran on Safari is shown by «screen restore after load».
- Restaurant «Аналитика» vs recorded commission (tools: scratch script, demo data changed in the preview only):
  A as is: 1 / 440 / 374 (= recorded). B order recorded at 8 % (35.20), store now 10 %: screen still 374, recorded gives 382.80.
  C plus happy-hour discount 40 (recorded commission 32.00): screen still 440 / 374, recorded gives 400 / 346.
  → the screen uses the store's CURRENT % and ignores the happy-hour discount; it differs from the commission stored at order time
  whenever the % changed or a happy hour applied. Not changed (needs owner decision).
- Restaurant search across real polling: before «автообновлений: 2» 15:56:47 «плов», after «автообновлений: 4» 15:57:10 «плов»,
  same input element, no focus taken; only the demo server data changed (no forced redraw).

## v56l — restaurant analytics from recorded values (16 Oct)
`tools/merchant_stats_check.py <merchant_preview>`: revenue = items − store discount − happy-hour discount (recorded on the order);
«После комиссии» = revenue − recorded commission − points − cashback − free delivery paid by the restaurant (all recorded per order).
Today's store % is no longer used. A 1/440/374 · B (8 % recorded) 382.80 · C (+happy hour 40) 400/346 · D (no recorded commission)
«—» + note. If more than the 200 loaded orders fall in the period, a note says the data is incomplete (from which date).
Restaurant search evidence kept from the follow-up above (not re-run). Safari jump and the 16-s reload: still open.

## v56m — restaurant order ids, order sheet commission, happy-hour correction (16 Oct)
- Bug (owner, real taps): Аналитика → История → #ord4 → `ReferenceError: ord4 is not defined`. Cause: 6 restaurant handlers wrote the order
  id unquoted (`OD=${o.id}`, `st(…)`, `rjOpen(…)` ×2, `TLB.patch(…)`): fine for numeric production ids, broken for the preview's text ids.
  Now written as JSON. Test `tools/merchant_ids_check.py <merchant_preview>`: every history row by real tap → details → close (same list,
  same place), reject sheet, prep-time chip, accept/ready; 390 px and 1366 px. Before the fix the first row failed with the same error.
- Correction of v56l: `orders.discount` already CONTAINS the happy-hour part (place_order: discount = store discount + happy hour;
  hh_discount = that part). v56l subtracted hh_discount a second time; reverted (revenue = items − discount). The v56l test case C used
  hh_discount without the matching discount, which production never stores. Corrected case C: discount 40 incl. hh 40, commission 32
  → 400 / 346.
- The order details sheet also used the store's current %: it now shows the commission and % recorded on the order («—» if none).
- Not changed (out of this batch): the customer (10) and courier (5) apps have the same unquoted-id pattern; production ids are numeric.

## v56n — admin menu strip moved when switching sections (16 Oct)
`tools/tab_nav_check.py <admin_preview>` — phone 390, RU+EN, real taps Orders→Stores→Couriers→Customers→Orders ×3, page sometimes
scrolled before the tap, a real data change every 4 s (automatic refreshes during the taps). Measured: strip top before / right after
/ 1.8 s after, gap strip→section, page sideways offset.
- Cause (proven by measurement): the part above the strip is not the same height in every section (Orders has the indicator cards +
  caption, +369 px); the page offset stayed the same, so the strip landed elsewhere: v56m RU Stores→Orders 333 → 702 although the
  page could be scrolled to keep it (needed 369, max 1299). No late jump (1.8 s later identical) and no sideways page scroll
  (scrollX 0, scrollWidth = width) in v56m either; the only sideways motion is the strip itself showing the chosen tab.
- Fix: on a section tap the strip is kept at the same place on the screen (one scroll right after the tap; if it was scrolled away
  it comes to the top). It moves only when the page cannot be scrolled that far (e.g. Customers still loading = short page, or
  the top of the page). Wide screens (fixed side menu): unchanged. After: 0 fails; before: 6.
- Separate from the Safari rotation jump, which stays open.

## v56o — iPhone round on v56n: Orders and Support still jumped (16 Oct)
`tools/tab_nav_check.py` extended: Support in the sequence, page-top Stores→Support→Stores, strip not under the sticky support bar,
taps on the visible part of the button (a covered/hidden strip is scrolled into view first, as a finger would). v56n: 6 fails, v56o: 0.
- Support (proven): the support bar was hidden only on Support → everything below moved up 50 px (333→283). Bar now on every tab.
- Couriers→Customers (proven): Customers is short while loading → the page could not be scrolled far enough (153→333). The page now
  keeps enough height until the next section tap (min-height on the content; no timer, no scroll lock).
- Orders on iPhone: not reproduced; candidates in `STATUS-PLAN.md` §1. Safari cases A–D: `STATUS-PLAN.md` §2 (all open).

## v56p — iPhone round 19:05:47–19:06:50 on v56o (diagnostics only, app code unchanged)
Reading of each line: `STATUS-PLAN.md` §1b. Proven: (1) Safari stacks have no "Error" first line → the log's caller skipped one frame
(«onclick» = `tabKeep`/`render`, «cuLoad<onclick» = `render`); (2) leaving Orders while it is scrolled < 369 px cannot keep the strip
(cards above it only in Orders) — geometry, look decision. Not proven: 19:06:50 top move (gradual, no app scroll, no redraw).
v56p log additions (no personal data): build id in the header and PAGE LOAD; «SECTION TAP» per section tap (from→to code, strip place,
offset before / after redraw / after keep, strip sideways offset, page height, extra height for a short section, moves in the next 0.8 s,
last touch); touch time on app scrollTo / JUMP / TRACE; TRACE wording «page reached the top with no app scrollTo … (mover not
identified)» instead of «browser put the page at the top». Test `tools/diag_check.py` (Chrome + Safari stack formats, one line per tap,
every field, no names/phones). Re-run: tab_nav_check, form_keep_check --quick, preview_check.
