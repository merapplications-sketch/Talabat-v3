# RATINGS-INTERNAL-01 — isolated read contract v1

Status: TEST-ONLY CANDIDATE. No endpoint, SQL, RLS, grants or operational consumer is installed.
Policy: `05428e37d9779fa2af0845e640fe85553c8b6974` (TARGET-ALIGNMENT-PLAN.md:273–277).
Preparation contract/audit: `98dc238fbf5693595496def998399275c47b078b`, `docs/review/ratings-internal01-independent/READ-CONTRACT-AND-ACCEPTANCE.md`.
The audit describes historical source and AUDIT107's isolated-target evidence, not current deployed state. This candidate does not re-read or publish private AUDIT107 files.

## Proven rules

For each **store_id**, count every non-NULL internal `store_stars`; average is `round(avg(store_stars),1)`. Positive half ties round upward, matching the historical numeric expression in `sql/schema_patch18.sql:377–407`. Integer coefficient arithmetic implements the same rule without binary midpoint drift. `source=talabot`, `subject=restaurant` are fixed. There is no threshold5 and no access to Google `rating/rating_count/google_place_id`, cached `app_rating`, driver averages, or the administrative300-row list. Driver-only rows do not affect restaurant sum/count. Support `handled_at` does not exclude a low score. Branch IDs remain separate even with identical brand/name; no brand-average inference.

## Candidate API and completeness boundary

`readInternalRatings(adapter, options)` accepts explicitly supplied store IDs, page size, max rows/pages and timeout, optionally an AbortSignal. Values in the tests are **test budgets**, not approved production limits, TTL or SLA. The local candidate has no network adapter, no database driver and no operational imports.

The test adapter opens a read session with:

- `source: talabot`, `coverage: complete_internal_history`, exact requested scope, stable opaque `version`, and independent `total_rows` for that scope including driver-only rows.
- `page({after, limit, signal})`: rows in strictly increasing, unique canonical `order_id` text order, snapshot version and explicit `has_more`.
- `close()`: release read resources, including a late open after timeout. A real adapter must honor AbortSignal and bound underlying work; JavaScript cannot forcibly terminate an arbitrary uncooperative service.

The reader checks every page, key progression, duplicates, scope, star validity, version, final count and resource budget. No result is published until all pages finish. A truncated history, missing metadata, source/scope mismatch, mid-read error, version change, timeout or cancellation returns unavailable, never a partial average or false empty result. No retries, writes, rewards, rating submissions or Google calls occur.

**Trust boundary:** adapter metadata is a required assertion, not proof that an arbitrary remote source is honest or complete. A hosted adapter still needs independently verified full-history access, provenance, snapshot consistency and identity enforcement. A provider falsely labeling its last300 rows as a complete history cannot be detected solely by this interface. RLS-filtered rows cannot be declared a full public-store history. Do not expose private ratings through a client-side SELECT to implement this candidate.

## Output and pagination

| Field | Meaning |
|---|---|
| result.state | ready only when all requested branch reads are complete; otherwise unavailable |
| snapshot | source read-version token, NOT last-review timestamp or current-deployment proof |
| rows_read | complete internal row count inspected; includes driver-only rows; null on unavailable |
| stores[].store_id | exact branch identity, never derived from name or Google place |
| stores[].rating_count | count of restaurant stars, including1–4 ratings; null on unavailable |
| stores[].average | one-decimal numeric value when rated; null for empty/unavailable |
| stores[].state | ready / empty / unavailable; empty requires confirmed complete read |

Results are immutable. `selectPage` is a **test-only selector**, not a replacement for accepted app ranking formulas. Caller explicitly chooses descending average or count, optional minimum average and page size. Sorting uses the same internal summary; ties preserve caller input order and rated results precede empty ones. Unknown results cannot pass a threshold or become zero. The4.5 test uses the stored one-decimal average, as in the source consumer. Operational combined popularity/offer/search formulas are not changed.

Selector cursors are in-memory capabilities bound to the exact immutable result object and query; they are not HTTP tokens. Pages retain a constant filtered total independent of page length. A cursor from another snapshot or filter is rejected. A future wire cursor requires a separately reviewed scope/version/integrity contract. No assumption that elapsed fetch time equals last-rating time, no freshness SLA, no automatic stale-response installation into UI.

## Comments: withheld, not silently empty

`commentsProjection()` always returns `state: withheld`, `reason: publication_contract_pending`, `reviews: null`, `review_count: null`. It never reads raw text, names, phone numbers, account/order/driver IDs, support metadata or HTML. Rating counts remain independent of publication eligibility.

Proposed whitelist for a **later approved** public restaurant-only projection: opaque public review reference, store_id, restaurant stars, approved timestamp granularity, and explicitly authorized plain restaurant text. Author identity is omitted unless a separate policy approves a limited form. HTML is not trusted; encoding is required at the future renderer. PII detection alone does not authorize publication. No automatic splitting, translation-based classification or exposure of historical mixed restaurant/driver comments. `handled_at` is not publication approval. Future fields, provenance verification, moderation and historical treatment need owner approval and independent privacy/RBAC review before implementation.

## Old rating recovery

Full aggregate history is tested with600 and701 rows. This does not implement private per-order recovery. The old `ratingOf` path relying on latest300 cannot prove an old order has never been rated. A later authorized point lookup by order_id must verify current requester ownership/permissions server-side, distinguish not-found from unavailable, and reconcile lost ACK without invoking `rate_order` again. The existing order-wide primary key and reward contract remain unchanged; no new replay or edit semantics are introduced here.

## Separate approvals and evidence before integration

1. Owner-scoped implementation approval for the actual server read adapter/endpoint and any SQL/schema/grant/RLS change; none are selected or applied here.
2. Independent full-history/provenance and real transactional snapshot proof; test concurrent commits and target trigger/aggregate behavior with explicit isolated DB authorization.
3. Consumer integration approval for customer/core/map and other displays, applying the same store_id read result while preserving accepted ranking formulas and layouts. No designer branch was edited.
4. Comment publication policy: exact public fields, author policy and treatment of historical mixed texts. No historical publication is authorized by this read candidate.
5. Hosted HTTP/RBAC, request revocation, private old-order recovery, browser/Safari, actual freshness and cache behavior remain unproved.
6. Load/p95/p99 and resource budgets require a separate approved load plan. The701-row unit case is correctness evidence, not a capacity claim.

Stop at independent review of this local candidate. PHASE1 PARTIAL/BLOCKED; PHASE2 NO-GO.
