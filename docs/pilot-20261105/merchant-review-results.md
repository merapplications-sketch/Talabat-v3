# Merchant review results

Supersedes the pending authentication and three-RPC statements in merchant-review-continuation.md. The isolated test frontend source is committed at b67b37773dc29f48d3d3841ce436705179421cb4. This candidate commit records evidence; the deployed test frontend has its own source repository.

The correct merchant signed in successfully using a separate review session. Original sessions were preserved. The previously failing MFA attempt belonged to another account; no MFA factor, password or account permission was changed.

| Operation | Existing UI | Direct authenticated HTTP owner | Direct authenticated HTTP nonowner |
|---|---|---|---|
| brand_stats | Statistics rendered | 200 with rows | 200 empty rows |
| branch_create | Created branch with copied menu | 200 created | 400 P0001/not_allowed |
| brand_sync_menu | Changed target menu price to source value | 200 success | 400 P0001/not_allowed |

Provider logs independently confirmed the UI POST requests returned 200 under the merchant identity. Direct HTTP runner returned six passing checks. Synthetic fixture stores stayed closed and were deactivated after testing; no fixture orders were created. The temporary HTTP runner was removed from public assets and retained as test source. Full build security checks and seven role-session isolation cases passed.

Only application behavior change (inside start):
```js
// Separate review login without replacing or signing out the existing merchant session.
if (role === 'merchant' && new URLSearchParams(location.search).get('session') === 'merchant-review') sessionRole = 'merchant-review';
```
This precedes authStorageKey assignment. Existing role keys, server authorization, MFA and design remain unchanged.

No production, protected order, receipt, settlement, mail, paid-service or domain changes. Broader security acceptance, synthetic-account MFA verification and sender configuration remain open and are not implied by these narrow results. No private account identifiers, MFA metadata or order records are included in this public evidence note.
