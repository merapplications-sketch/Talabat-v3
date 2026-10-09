# v38 — dish option sheet
- Fix: picking an option no longer scrolls the sheet back to the top (scroll preserved on re-render).
- Add button is always tappable; if a required group is missing it scrolls to it, highlights it and shakes.
- Group counter "1/3" for multi-choice groups; background page is locked while the sheet is open.
- tools/sheet_check.py (fails without the fix: scrollTop 400→0).
- Not done in this batch: restaurant-page tabs, cart/checkout redesign (existing section tabs kept).
