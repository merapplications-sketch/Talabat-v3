# v36 — multi-branch restaurants

**SQL (run first, after patch 26):** `sql/schema_patch27.sql` (tested: `sql/test_patch27.sql`, 67/67 on a replica).

- Core: `brand_id,branch_name` in the stores query with tiered fallback (old DBs keep working); API `brandCreate/Attach/Detach`, `branchCreate`, `brandSyncMenu`, `brandStats`, `brandRoute`, `brands()`; error texts `name_taken`, `no_template`.
- Customer: one card per brand in lists (open branch first, then nearest to the chosen address); "Other branches" chips on the menu page; lookups use the full list.
- Merchant (Profile tab, brand owner only): branch list with 30-day orders/revenue, "Add branch" (name, address, phone, map point), "Sync menu".
- Admin (store edit): create brand (owner email), attach/detach a store.
- security-check SC-34: patch-27 checks. `tools/branch_check.py` added.
- Menus are copied, not shared. Verified on Chromium + replica DB only.
