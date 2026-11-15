# Gate1 baseline extraction — intentionally BLOCKED

Source of truth: the production database **public schema only** of the project referenced in approved `tech/v82-int` core JS, ref `dzydscryrnahnneydnry`. Owner-authorized scope: schema DDL/metadata only (tables, columns, constraints, indexes, enums, policies, functions, triggers, grants). Never query/copy production data rows, `auth.users`, `storage.objects`, Vault or private credentials.

On 2026-11-16, Supabase read-only catalog, table introspection, migration listing and type generation all failed with **database connection timeout**, with no schema definitions returned. Consequently the following required artifacts do NOT exist, by design:

- `schema_baseline_dzydscryrnahnneydnry_20261116.sql` — must contain **genuine** verified schema-only DDL, not a synthetic/fixture schema.
- `schema_baseline_dzydscryrnahnneydnry_20261116.json` — manifest of the above with `source_ref` = `dzydscryrnahnneydnry`, `sha256` (actual file checksum), `extracted_utc` (actual offset-aware UTC timestamp), `schema_only:true`, and explicit boolean `patches17_34_included`.

After read-only extraction succeeds and the owner-approved authentic DDL is archived, `tools/gate1_local_prepare.py` can validate these and stage a disposable local-only migration set inside CI. Until then, CI intentionally BLOCKS before any Supabase Docker startup or E2E/network operation.

No remotely linked Supabase, cloud project, production account or paid service may be introduced. See existing Gate1 report and [owner brief](https://github.com/merapplications-sketch/Talabat-v3/blob/9f28710569064d7fab6c5c98baa49a2214c4bd10/docs/management/GATE1-PROGRAMMER-BRIEF-2-20261116.md).
