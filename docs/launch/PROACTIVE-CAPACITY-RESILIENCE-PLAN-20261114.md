# TALABOT — Proactive Capacity, Resilience & Security Plan
**Document version:** 2026-11-14 / Asia-Dushanbe  
**Status:** OWNER-DIRECTION TRANSLATED INTO A REVIEW-ONLY PLAN. **NOT DEPLOYED; NOT AN APPROVED CHANGE TO CODE, INFRASTRUCTURE, COST OR BUSINESS RULES.**  
**Scope:** Existing TALABOT customer, driver, merchant, admin, Supabase and Cloudflare components. This supplement implements the *planning and evidence* side of the existing accepted `SCALABILITY & OPERATIONAL RESILIENCE` addendum; it does **not** replace or reorder the accepted G1-A..F/PHASE1 gates or the single-role dispatch currently in master [#26](https://github.com/merapplications-sketch/Talabat-v3/issues/26).

## 0. Owner direction and exact meaning

The owner favors **controlled admission** of *new* operations when verified safe capacity is almost exhausted, to preserve already accepted deliveries and financial integrity. The owner explicitly prefers prevention: measured spare headroom, early warning, preplanned upgrade/rollback, no panic purchases. **Do not interpret this as permission to auto-disable ordering, impose new quotas, change accepted order state/finance policy, or add services.** The exact fail-safe admission behavior and customer wording need a separate owner-approved design/operations contract.

Desired behavior: detect approaching capacity **before customer impact**; optimize existing traffic and database queries; alert operations; stage resources and a tested recovery plan; prevent duplicate orders/ledger effects; reject new work gracefully *before acceptance/payment* only under a subsequently approved policy; preserve the status of accepted work. Reliability is not a guarantee of zero downtime or perfect invulnerability.

Approved source-of-truth:
- [Existing scalability addendum](https://github.com/merapplications-sketch/Talabat-v3/blob/1cb85361d698d5da787d927a4c9ae7bd213c68c1/docs/review/continuation108/TARGET-ALIGNMENT-PLAN.md#scalability--operational-resilience--ربط-تكميلي-بالخطة-نفسها)
- [Owner agreements: CASH-01, RETURN-01, SCOPE-01, language, designs](https://github.com/merapplications-sketch/Talabat-v3/blob/1cb85361d698d5da787d927a4c9ae7bd213c68c1/docs/OWNER-AGREEMENTS-AR.md)
- [Current project QA and G1 gate truth](https://github.com/merapplications-sketch/Talabat-v3/blob/0ab523782ee1bf6f69e2e3be7ec6e96394d9ce6a/docs/qa-first-20261113/MASTER-QA-CONSOLIDATED-20261113.md)
- [Present risk register](RISK-AND-TEST-PRIORITIES.md)

## 1. Evidence inventory — what we know and do not know

| Point | Evidence / observation | Classification |
|---|---|---|
| Customer/driver core | Historical pinned `talabat-core.js`: separate stat/orders/misc/offers refresh groups; background tab pauses scheduled polling; some failures use incremental backoff; Supabase realtime triggers section refresh | SOURCE-VERIFIED AT PIN; no current deployed request-volume proof |
| Catalogue | Core includes candidate read limits for up to 1,000 stores, 5,000 items, 5,000 groups and 20,000 options in its stat loading path | SOURCE-VERIFIED LIMITS; **not** measured per-user bandwidth/CPU |
| Location | Driver UI has `watchPosition`, throttled `sendLocation` via `driver_location` RPC; do not infer actual DB writes per second or that GPS already streams over WebSockets | SOURCE-VERIFIED, runtime/provider workload UNKNOWN |
| Dispatch | `dispatch_tick` callable from app clients, independent scheduled job not proved | SOURCE-VERIFIED; independent job G1-B remains BLOCKED/PARTIAL |
| Supabase | Connected organization reported Free at audit; project-name listing had active and inactive entries; a queried project's advisor endpoint returned a hibernation error despite prior health summary. No raw usable live capacity charts obtained. | SNAPSHOT/CONFLICT, not an uptime/traffic measurement |
| Realtime quotas | Refer to [live Supabase limits](https://supabase.com/docs/guides/realtime/limits), then verify the exact project configuration before treating any numeric cap as effective | DOCUMENTED PLAN LIMIT, not a load test |
| Cloudflare | Deployment/source/current domain mapping not fully accepted in G1-A/F | DEPLOYMENT PROVENANCE UNKNOWN |
| Current tests | Historical functional 0/51 current-source E2E, Admin 0/21; G1 0/6 accepted at pinned consolidated QA. Newer synthetic Safari ZIP review is a separate visual-only track and never a functional capacity proof | RELEASE/PHASE2 NO-GO until new evidence |

**Important:** A document's project-status snapshot, a missing log result or source review cannot be presented as a live capacity number or an active security finding. Revalidate before making a purchase or user-impacting decision. Public repository documentation must not include service credentials, security test payloads, private metrics or detailed exploitable configuration.

## 2. Capacity is multidimensional, not disk space or orders/day

**Safe throughput** is constrained by the first bottleneck among: active authenticated/realtime sessions, message/event throughput, database CPU, RAM, IOPS, disk/WAL, connection/pool saturation, API and RPC latency, slow query/lock rate, dispatch worker throughput/queue age, storage egress, frontend resources and third-party payment/notification limits. For a given measured workload, document the minimum effective safe capacity with headroom; never convert 100 restaurants / 10,000 items into a promised user or order count.

Segment traffic into **catalogue reads**, **price/quote**, **new checkout**, **driver acceptance/transition**, **GPS**, **chat/notifications**, **finance/settlements**, **admin reports**. Record per-session request count and size, per-route P50/P95/P99, error rate and concurrency under normal, peak, burst, disconnect/reconnect conditions.

## 3. Observability: practical dashboard and what must be proved

**Owner dashboard** with three views:
1. **Customer impact:** externally observed availability, checkout/accept/deliver success by operation, API 5xx/429, latency P95/P99, stale data/map/location and rejected new work. Distinguish legitimate business rejections from platform errors.
2. **Headroom:** verified live plan and hard limit for realtime concurrent connections, messages/sec and joins/sec; DB CPU, memory, disk use, IOPS/IO balance, active/idle/queued DB connections, slow queries and deadlocks; API requests/sec, response bytes; delayed worker jobs, queue oldest age, third-party quota, estimated days to saturation.
3. **Integrity/security:** duplicate unique order keys, duplicate final delivery or money effects (**must remain zero**), unauthorized RLS/RBAC access, Auth abuse, unusual request bursts, suspicious WAF/429 patterns, privileged RPC exposure, backup verification and fresh restore evidence.

**Data sources:** Supabase Studio Reports (Free-supported database CPU, RAM, IOPS, connections, disk/size: [docs](https://supabase.com/docs/guides/observability/reports)), Supabase Realtime/API logs where actually available, Cloudflare Workers/Pages/edge analytics and notifications where enabled and eligible ([docs](https://developers.cloudflare.com/workers/observability/metrics-and-analytics/)), app-level counters/traces and independently hosted synthetic availability check. Supabase [Metrics API](https://supabase.com/docs/guides/observability/metrics) and managed external alerting are **conditional**: check current Free entitlements, secret handling, cost and access before planning automated scraping. Never expose a `service_role`/secret key in a browser or public repository.

**Missing now:** a live reliable 7–14 day metric baseline, authenticated deployed source-to-project map, alerts actually tested end-to-end, cost quotes and a named on-call/backup responder. Status: **BLOCKED/UNVERIFIED**.

## 4. Early warning and predictive upgrade — provisional thresholds, NOT active alerts

Use percentage of each **verified effective cap**, **rate of growth**, **time to cap**, impact symptoms and error-budget burn; one threshold cannot represent all services. Proposed starting bands for owner/technical review:

| State | Tentative trigger (per resource; must calibrate from 7–14 day baseline) | Action |
|---|---|---|
| PLAN EARLY | Sustained 50% of *verified* capacity or forecast crossing 70% in the next two weeks | Notify owner + engineer with exact metric/cap and trend; tune existing hot queries and prepare priced upgrade/migration plan |
| WATCH | Sustained 65–70%, rising P95/P99 vs baseline, increasing error/connection pressure, or shrinking disk IO budget | Same-day engineering review, limit nonessential polling if owner-approved; verify backup/recovery/rollout readiness; do **not** change plan/payment automatically |
| ACT BEFORE LOSS | Reaching 80–85%, rapid upward slope, confirmed retries storm or messages/sec quota errors; or customer transaction health deteriorating | Alert operations and owner promptly; enforce *preapproved* safe traffic measures; prioritize confirmed accepted operations; consider previously priced/prepared capacity step **only with owner authorization** |
| INCIDENT | Actual saturation, persistent 5xx/timeout, orders stuck, confirmed duplicate money/order or data leak | Incident runbook; contain blast radius, keep accepted order state consistent, stop unsafe new-work admission before charge, page accountable operator; preserve evidence |

**No hard current thresholds are approved.** Avoid alert fatigue: alert on sustained trend and/or short+long error-budget windows, suppress duplicate notifications, route by urgency. Use Google SRE [multiwindow burn-rate](https://sre.google/workbook/alerting-on-slos/) for impact-driven paging. A scheduled AI check at most hourly is only a **secondary review**; minute-level native provider alerts/synthetic health checks are required to catch rapid spikes.

**Capacity plan artifacts**: measured safe capacity, current growth slope, projected date reaching safe headroom boundary, upgrade quote and lead time, migration/maintenance plan, tested roll-back/failover and owner decision record. Reserve a meaningful headroom margin rather than waiting for 95–100%.

## 5. Demand reduction BEFORE paying for larger compute

Evaluate only where measured:
- Cache public, low-risk, rarely-changing catalogue/media at the appropriate layer with correct invalidation; never reuse stale confirmed prices, availability or authorization decisions.
- Replace broad periodic `select('*')` payloads and high per-client list limits with scoped fields, pagination/on-demand loading and differential refresh **only if performance evidence warrants a narrowly approved change**.
- Debounce/aggregate duplicate realtime refresh events; use jitter and bounded retry/backoff; respect hidden tabs; avoid large simultaneous reconnect waves.
- GPS: measure actual client updates, RPC and downstream consumers. Use freshness TTL, per-driver update ceilings/accuracy; consider ephemeral latest-location store only *if* measured bottleneck justifies it. Keep required delivery audit/evidence durable, with privacy and fallback.
- Dispatch and background: prove independent scheduled execution/heartbeats and idempotent worker claims; cap concurrency and work queues, expire stale tasks, measure queue age and recover safely. Do not interpret client `dispatch_tick` as a proven autonomous scheduler.
- DB: inspect slow queries, indices, lock waits, query plans, WAL/IO balance, connection pooling before increasing compute. Any SQL/index/policy change requires its own review/QA.
- Degrade safely: postpone recommendations/reporting/nonessential notifications before checkout/driver-state/money, but do not **acknowledge a financial event before durable commit**. Return a clear and truthful response if new checkout cannot be accepted safely.

**No automatic addition** of Redis, H3, a different WebSocket stack, paid queues, microservices, autoscaling workers or a new database. Select only after measured constraint + cost + test + owner approval.

## 6. Separate protection from external attacks

Use defense in depth: edge DDoS/WAF where traffic actually passes through it, per-route / role / account abuse limits, Auth CAPTCHA/rate controls, strong account/session handling, RLS & per-tenant ownership, server-side permission enforcement and idempotency, secret isolation/rotation, scoped privileged functions, dependency/CI scanning, secure audit logs and storage signed URL access checks. Verify external security services' plan availability.

**Architecture warning:** Cloudflare protection for the frontend's hostname does not automatically protect direct Supabase `*.supabase.co` requests. API/RPC/Auth abuse protections must be enforced at their actual entry point and database permission level. Never disable RLS, loosen financial controls or share secret keys to improve benchmark speed. Protect against security abuse without blocking legitimate customers or revealing account data.

## 7. Controlled test program — PROPOSAL ONLY / no execution authorized

| ID | Isolated acceptance scope | Required evidence |
|---|---|---|
| CAP-01 | Reproduce exact deployed/under-test source, project and limits | Immutable frontend/backend/RPC version manifest, resource and plan baseline |
| CAP-02 | Catalogue normal/cold/warm under 100-restaurants/10,000-items *synthetic sample* | response sizes, CPU/RAM, query count, P95/P99, freshness/authorization |
| CAP-03 | Customer/merchant/driver session ramp and RT connection/message/joins | peak safe concurrency, per-user connection fanout, subscription recovery |
| CAP-04 | Burst and simultaneous reconnect after network restoration | bounded retry, no thundering herd, no runaway DB connections |
| CAP-05 | GPS/reporting workload with real proposed driver update schedule | DB writes, IO/WAL, update age, stale-location controls, correct privacy |
| CAP-06 | Dispatch_tick and independent worker throughput/backlog | one driver/order assignment; worker heartbeats/queue age and recovery |
| CAP-07 | Checkout/accept/deliver/payment/refund under concurrency | **zero duplicate committed business/finance effects**, intact CASH-01 & Q09–17 |
| CAP-08 | Stop noncritical component, observe critical path degradation | essential operations remain correct, user-visible truthful status |
| CAP-09 | Long soak/memory growth/slow IO and sustained traffic | no uncontrolled leak, no drift, bounded backlog/recovery |
| CAP-10 | Bot/abuse burst with synthetic identities only | abuse bounded, valid traffic not unfairly blocked, RLS isolation |
| CAP-11 | Backup/restore and release rollback in isolated environment | verified artifact, actual recoverability and reconciled orders/finance; RPO/RTO not guessed |
| CAP-12 | Preapproved capacity/admission step rehearsal with explicit kill-switch | no partial charges/accepted lost orders; recover and monitor |

**Stop immediately** on any possibility of reaching a production URL, live data, real payment, secrets or a missing isolation safety proof. Load/spike/soak tests must have an owner-approved isolated environment and independent security gate, including the traffic rate/cadence, duration, resources and cleanup. Do not run on the production Supabase project, live Cloudflare endpoint or synthetic Safari static demo.

## 8. Prepared recovery / scaling runbook, not autonomous production actions

1. **Observe** alert and correlate externally observed customer impact, service/resource telemetry, deployment SHA and operator.
2. **Classify**: benign traffic burst, abusive traffic, DB/IO pressure, Realtime limit, slow query, job backlog, DNS/network issue, partner outage or deployment regression.
3. **Contain in approved scope**: stop runaway nonessential work, keep financial and order writes consistent; introduce only previously approved demand shedding for *new* work; never mark a committed order unsuccessful merely because the response was lost.
4. **Choose smallest safe solution**: eliminate a faulty query/retry loop, revert a bad release, restore failed worker, or execute a **prepriced, pretested** capacity change once the owner approves costs and maintenance effects.
5. **Verify** application functionality, integrity, roles/finances, active queue/dispatch and customer-visible recovery.
6. **Communicate** accurate incident status; record UTC timeline, impact, detection lead-time, contributing cause and follow-up prevention.
7. **Postmortem** blameless, one repeatable test and alert upgrade per distinct failure, not a new architecture rewrite by default.

**Supabase Free-specific caution:** quotas/pausing/retention and project state need live verification; free project inactivity pause and database disk limits can affect continuity. Compute-size changes may cause downtime and cannot be promised as zero-interruption automatic scale-up. Backups/restore capacity must be proved against the actual plan. See [pausing](https://supabase.com/docs/guides/platform/free-project-pausing), [compute/disk](https://supabase.com/docs/guides/platform/compute-and-disk), [free disk](https://supabase.com/docs/guides/platform/database-size) and [production checklist](https://supabase.com/docs/guides/deployment/going-into-prod).

## 9. Ordered owners / no roadmap collision

- **Manager**: recover newest master #26 and source/owner decisions, assign only ONE next role and save evidence with confidence; current Stage16 Safari ZIP/QA remains separately assigned and must not be diverted.
- **Technical reviewer**: read-only source and effective monitoring inventory, identify exact existing limits and probable bottleneck; no performance promises without data.
- **OPS/Publisher**: supply read-only deployment, quotas, provider alerts/backup/restore information, no account or billing edits.
- **Programmer**: make no architecture/refactor/service changes until a reproducible isolated performance or security failure is approved for a minimal correction.
- **Independent security/QA**: validate capacity, race/idempotency, recovery, abuse and availability on a sealed synthetic runner, with independently verifiable evidence.
- **Owner**: approve candidate SLOs and alert thresholds, real user-impacting admission behavior, financial guardrails, potential spend cap, capacity/HA/backup upgrades and specific deployment.
- **No unapproved code, data, plan, Cloudflare/Supabase, CI or production modifications. No publication or paid resources.**

## 10. Mandatory outputs before declaring pilot GO
1. Deployment source → actual project → current paid/free entitlements mapping.
2. Measured normal/peak/tested maximum safe throughput with headroom, not a guessed daily order count.
3. Effective dashboard covering DB, API, Realtime, dispatch, customer-facing SLI and financially important anomalies.
4. **Test alert receipt** to owner/operator at forecast/pre-breach threshold; confirmed notification channel and backup recipient.
5. Current 12 CAP-case evidence with PASS/FAIL/BLOCKED and isolated environment.
6. Security/RLS abuse review, backup/recovery proof, operational runbook and release rollback.
7. Owner-specific pilot GO/NO-GO with identified accepted risks, no implied Phase2 release.

**Explicit exclusions:** This planning document is not proof of current capacity, healthy production, 24/7 alert delivery or absence of vulnerabilities. Historical document statuses may change; newer accepted decisions and latest GitHub HEAD take precedence.
