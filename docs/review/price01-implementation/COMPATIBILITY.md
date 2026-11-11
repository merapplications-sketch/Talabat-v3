# Client compatibility and future activation boundary

Source: `bb01f11b855a2898f3f0b0f8908de827be68844b`. Contract extension is owner-approved for isolated development only. No operation below has been executed against a hosted service.

| Caller / attempt | Candidate behavior | Evidence / required follow-up |
|---|---|---|
| New compatible client, new key, exact version1 consent | Creates once if existing business/admission guards also pass | Native04,09,12,15,18,19,22; UI01/02 |
| New compatible client, new key, changed constituent price even same total | No committed creation/spend; closed104 response can offer bounded review | Native01,03,06–09,13; UI02/17 |
| Old client, new key, no consent | No creation: price_confirmation_required;104 can commit a closure | Native02,16; operational cutoff NOT activated |
| Old/new client, committed pre-contract request without consent | Recover original order after identity/current authorization; no new price check, rehash or repricing | Native10,23 across all four entries |
| New request with binding, identical original key/payload after ACK loss | Retrieve original result and stored prices, even if menu changed | Native04,11; UI05 |
| Same committed key with different consent/content | Existing HMAC conflict; not a new order | Native15,26 |
| Unknown attempt, old or new, no observed order yet | Keep original key and payload; explicit saved retry only; do not append consent or infer failure from absence | UI05/06/13; TCP11/20 |
| Immutable closed key | Never create or reopen; changing proof cannot override closure | Native13,17,20,24,26 |
| Closure resource unavailable /55P03/40P01 | Unresolved, no false closure; reconcile original key | Native16/21;40P01 is injected locally, not a natural deadlock proof |
| Legacy bigint place_order | Enforces same creation guard; throws on rejection/unresolved; no104 interactive-review contract | Native01/02/04/14/17; clients must use approved104 adapter for full workflow |
| Private creator | Same required consent and recovery ordering; remains unavailable to authenticated direct callers | Native01/02/04/14/16/17 |

## Required evidence before proposing activation

1. Independent QA accepts this exact source. Resolve any defects by new reviewed commits; do not replace historical103–106 or TIP inputs.
2. Identify the actual customer bundle/version/environment from deployment evidence, including caches/service workers and old open tabs. A local build or source commit is not proof of delivered client readiness.
3. Prove the new request/response pair over authorized isolated HTTP and the real UI: actual displayed prices, explicit review/confirmation, original payload recovery, browser durable state and Safari. Verify catalog updates, mixed payment, options/discounts and all four entry routes. Verify additional writers from the actual target catalog; absence in fixture is not evidence of absence on target.
4. Inventory and drain old writers and unresolved attempts; retain their exact payloads, keys, HMAC keys, bindings and closures. Do not fill missing historical consent. Do not purge unknown attempts by age. An unknown outcome needs its established reconciliation procedure.
5. Prove database dependency fidelity and transaction boundaries, including deferred triggers and external effects. A nontransactional effect before rejection needs separately approved deduplication/reconciliation evidence; local rollback is insufficient.
6. Present an explicit operational plan and rollback readiness to the owner for a separate decision. No date, allowed old-client percentage, resource quota, RPO/RTO or retention period is invented here.

## Safe rollback / re-upgrade

- Source comparison point is b75ff6d; **reverting a live creator to that point is not a safe operational rollback** after the contract is activated.
- Candidate rollback is `tests/price01-impl/rollback.sql`, applied atomically only in the local tests. It replaces public103 and the private creator with recovery-only implementations. Public104 and bigint routes delegate to that restricted behavior. New creation stays unavailable, not silently unprotected.
- Retain tables, rows, historical versions, HMAC keys, bindings and immutable closures. Do not delete or recompute them. Recovery-only behavior must be checked with all four routes and independent sessions before any future operational approval.
- Reapply the entire candidate in one transaction. Native24 verifies interrupted rollback/re-upgrade leaves the previous function set intact, successful reapplication is repeatable, and stored MAC/order/closure data are preserved. This is simulated transaction interruption in real local PostgreSQL, not a provider restore or power-loss test.
- Re-upgrade cannot activate old unguarded writers. A failed upgrade keeps the prior guarded/recovery-only state. Device loss, backup restoration and cross-device attempt reconciliation remain separate operational gates.

No hosted transition, grant change, old-client cutoff or deployment was performed.
