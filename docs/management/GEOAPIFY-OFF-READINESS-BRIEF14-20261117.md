# TALABOT BRIEF-14 — Geoapify routing READY BUT OFF (2026-11-17)

**Status:** prepared for a *future owner-approved launch*, permanently **OFF** in this stage. No Geoapify subscription or API key has been requested, purchased, created, or supplied. No production Supabase Edge Function / SQL deployed and no real provider call made.

## Already prepared: authoritative SQL proposal, not a duplicate

- [\`sql/proposed/patch40_navigation_budget.sql\`](../../sql/proposed/patch40_navigation_budget.sql) already defines \`navigation_reserve_budget(...)\` and \`navigation_settle_budget(...)\`, durable shared hourly/rolling-budget ledger, idempotent request IDs, settlement and unsettled-transaction fail-closed guard. It is **proposed only** and has not been applied to production.
- Read-only review previously verified the production TALABOT Supabase project had **no such functions**: road-routing is therefore not ready to activate; the fallback remains external maps / tracking-only.
- The current \`route\` Edge Function defaults \`NAVIGATION_CONFIG.internal\` to **false**. The upstream Geoapify provider is only usable when its secret is configured server-side AND a separately approved budget ledger exists. Client JS never holds the provider key.
- \`tools/full_audit_nav_off.mjs\` exercises the exact source handler with a **dummy key and a blocked upstream spy**. Checks four fail-closed modes and existing SQL function/grant declarations. This test must make **zero** network/provider calls. Existing \`tools/navigation_budget_check.mjs\` provides deeper **in-process PGlite** SQL/reservation/settlement behavior tests, including duplicate requests and quota; no live account is required.

## Future activation only after the owner approves

1. **Owner approval:** choose provider, trial/cost/billing account, explicit monthly cap and disaster-stop rule. Do not create any account or incur any charges without this.
2. Security/backend review and **separate** authorized deployment of proposed \`patch40_navigation_budget.sql\`, after review of RLS, service-only execute grants, migration rollback/recovery and measured concurrent usage.
3. Set private **server-side** \`GEOAPIFY_KEY\` in the approved Supabase Edge Function secrets, never in browser, file, screenshot, GitHub Issue or CI log.
4. Review \`ALLOWED_ORIGINS\` and \`NAVIGATION_CONFIG\` for exact preview/production domains and tight \`dailyCredits\` / \`rps\` caps. Do not set \`internal:true\` until all tests pass.
5. On an explicitly approved, isolated deployment, flip \`NAVIGATION_CONFIG.internal=true\` **last** and test road polyline, coordinates, ETA, provider credits, duplicate/multiple drivers, quota and rollback.
6. **Emergency OFF:** set \`NAVIGATION_CONFIG.internal=false\` again at the server. Existing user external-map links remain usable, provided no independent policy disables them. No previous SQL data deleted.

## Scope caveats

A free Geoapify tier, any advertised quota, presence of an actual secret and final provider pricing **are not asserted** here. The owner must confirm current billing terms separately before activation.

No \`GEOAPIFY_KEY\`, no live activation, no external API or payment in BRIEF-14. Real iPhone navigation on Safari and native map app launching remain a separate owner UAT, not a substitute for this server/readiness test.
