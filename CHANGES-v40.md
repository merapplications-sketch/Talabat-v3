# v40 — header / offline fixes (+ Info tab removed)
- Driver header: the pill showed the long "No internet — you will not receive new orders" text (the shift label reused the `offline` i18n key). Now "Не на смене / Off shift"; the long text only appears in the red strip.
- Offline strip is now full-width (merchant/admin had an 18px/14px inset because of body padding).
- Removed the "Menu | Info" tab added in v39 (not requested).
- tools/hdr_check.py: checks text-vs-text overlap inside every header (clipped text handled), offline strip vs top bar vs header, horizontal overflow, at 360/390 online+offline, with a very long name. It reports the original driver bug on the old code.
