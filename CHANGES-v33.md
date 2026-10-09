# v33 (chore/pin-supabase-v33) — based on v32
- Fixed raw i18n keys shown on screen: admin footer "verL", merchant order card "payM", merchant empty search "noRes".
- Supabase library pinned to @2.117.2 in all pages (no silent upgrades). SRI hash not added (cannot verify the CDN bytes from here).
- New tools/smoke.py: opens the 4 apps in Chromium with a mocked backend, clicks every tab, fails on JS errors and raw keys / undefined / NaN. Run before every delivery: `python3 tools/smoke.py` (needs playwright).
No SQL.
