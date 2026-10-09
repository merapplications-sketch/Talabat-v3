# v40 — header / offline fixes (+ Info tab removed)
- Driver header: the pill showed the long "No internet — you will not receive new orders" text (the shift label reused the `offline` i18n key). Now "Не на смене / Off shift"; the long text only appears in the red strip.
- Offline strip is now full-width (merchant/admin had an 18px/14px inset because of body padding).
- Removed the "Menu | Info" tab added in v39 (not requested).
- tools/hdr_check.py: checks text-vs-text overlap inside every header (clipped text handled), offline strip vs top bar vs header, horizontal overflow, at 360/390 online+offline, with a very long name. It reports the original driver bug on the old code.

## v41 additions — comprehensive QA
- `tools/qa_all.py`: opens EVERY screen of all 4 apps (customer 23 screens/sheets, merchant 9, driver 3, admin 11 tabs) with rich fixtures (very long names, all order statuses, closed/open stores, options), at 360/390/430px, online and offline, at top and bottom of the page. Detects: text under another element, text-on-text overlap, text pushed outside the viewport, text clipped to nothing (INVISIBLE), page overflow, raw i18n keys, undefined/NaN. Verified it flags the old driver header bug.
- Found and fixed by it: merchant "Sync menu" button stretched to full width and crushed the branch list (my v36 bug); discount badge (−15%) disappeared on long restaurant names in customer category/favorites lists.
