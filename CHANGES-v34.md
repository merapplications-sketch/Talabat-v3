# v34 (feature/staff-roles-v34) — staff roles (RBAC)
**Order: run sql/schema_patch26.sql in Supabase FIRST, then merge/upload the UI.**
- SQL patch 26: `staff_members`, `has_perm()`, `my_perms()`, `staff_set/staff_remove/staff_list` (admin only, audit-logged). 24 functions + 14 policies now check a permission instead of "admin only".
  Permissions: orders, support, finance, stores, content. NEVER delegated: owners, roles, app settings, staff management, audit log, commission/discount changes, store-request decisions, customer phone override, store delete.
- Tested on a replica of the live schema: 117 attack/permission checks pass (sql/test_patch26.sql). Patch is idempotent.
- Core: staff sign in on admin.html with their normal account; the server (my_perms) decides. Super admin unchanged.
- Admin: tabs shown by permission; new Staff tab (add by email, tick permissions, disable, delete).
- security-check.html: build SC-33, 6 new checks.
Regression: tools/smoke.py (6 scenarios incl. staff views) — 0 errors.
