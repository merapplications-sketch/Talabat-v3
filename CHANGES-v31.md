# v31 (feature/batch2-driver-admin) — based on v30
Modified: admin.html, driver.html, talabat-core.js (version), stamps in all pages.
- Driver: header name truncates with ellipsis, ID shown as "ID XXXXXX", pill no longer overlaps.
- Admin: driver card header clickable; driver screen now shows activity (today/total delivered + earnings, last seen) and last 30 orders (click opens order).
- Admin: red sticky banner + beep when support requests wait for a reply (live via existing realtime).
No SQL. Regression: JS syntax, inline handlers defined, no new unescaped data.
