# v32 hotfix/offline-banner-v32 — based on v31 (main)
Modified: talabat-core.js (offline banner), driver.html (header spacing), version stamps.
- Offline banner is now its own red strip in normal flow at the very top (pushes the header down) instead of a fixed overlay on top of it; sticky headers (.top) offset below it.
- Driver header: banner-aware top padding; name ellipsis, ID and status pill never overlap.
- Checked in Chromium at 320/375/430px: banner above header, name left of pill, no horizontal scroll.
No SQL.
