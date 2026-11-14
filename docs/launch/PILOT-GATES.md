# TALABOT — Pilot Gates / owner-controlled launch criteria

**Status: PROPOSED REVIEW CHECKLIST, NOT NEW AUTHORIZATION.** Existing approved G1-A..F and PHASE1/PHASE2 decisions are binding. The checkpoints below organize the evidence; they do not replace existing gates or declare a numerical target by themselves.

## Track separation
- **Track A — synthetic visual Safari demo:** no-login, static fake-data only, cannot issue real order/payments/requests. Separate source, isolated URL and no production connection. Security, functional rendering and network egress must be independently tested. Explicit authorization is required before public hosting.
- **Track B — formal C-01 and full operational pilot:** real Auth/profile and integrated test routes require an authorized isolated execution environment and independent security gate. A successful fake demo never unlocks C-01, PHASE2 or production.

## Gate 0 — accepted records, exact branch and evidence
- [ ] Current main/pilot/customer/driver/merchant/Admin and active backend/deploy versions known by SHA, digest and environment.
- [ ] Latest Issue #26 and [PHASE1-CURRENT](../continuity/PHASE1-CURRENT.md) reviewed, no accepted business rule changed.
- [ ] Distinguish historical tests/CI from tests actually run on the exact current source.

## Gate 1 — safety/isolation and tester access
- [ ] Nonproduction network and database boundary verified; no production credentials or unexpected outbound requests.
- [ ] Synthetic customer, merchant, driver and staff roles available only under approved environment.
- [ ] Effective role authorization, request-scoped RLS/RBAC and writer permissions independently tested.
- [ ] No installs, cloud deployments or paid services without scope-specific owner authorization.

## Gate 2 — money/order/driver integrity
- [ ] Checkout/commit/retry/duplicate requests produce at most one paid order.
- [ ] Driver duplicate confirmation and offline recovery keep one delivery/ledger effect.
- [ ] Cash split follows approved CASH-01 and Q09–Q17; no under-collection violating Q14.
- [ ] Returns stay open until received funds are actually recorded (RETURN-01).
- [ ] Wallet, points, promotions, discounts, delivery fee, refunds and settlements use independent expected outcomes.
- [ ] Merchant substitutions/approval, planned/scheduled orders and gift/group delivery do not change prices or roles without consent.

## Gate 3 — real customer journey / platform
- [ ] Existing approved Customer UI, merchant acceptance/prep, driver dispatch/GPS, support/rating and Admin operations pass full bounded test flows.
- [ ] Session, addresses, network interruption, idempotency, signed proof images and zero-cross-tenant access verified.
- [ ] RU/EN customer and supported Admin locales, 320/360/390/430 and tablet/desktop verified against approved design. Real iPhone Safari is separately evidenced.
- [ ] Known P1 failures fixed on authorized isolated branches with independent regression.

## Gate 4 — source/deployment/rollback
- [ ] Each live frontend, RPC, SQL writer, scheduler/worker, finance component, key and storage endpoint mapped to exact running revision and branch.
- [ ] Confirmed reconciled backups and actual isolated restore/rollback evidence, not a planned backup alone.
- [ ] Technical and independent QA/finance/security signoffs backed by artifacts.
- [ ] G1-A..F accepted by original approved criteria; no PHASE2 while gates remain open.

## Gate 5 — owner decision
- [ ] Manager delivers one GO/NO-GO report listing coverage, blockers, environment, defects, safe scope, limits, operations/incident owners and required approvals.
- [ ] Owner explicitly approves the *specific* pilot environment/build/operational boundaries. No implicit approval from code commits, reports or silence.

## Verified historical checkpoint as of 2026-11-14
Master #26: source-specific functional E2E **0/51**, Admin **0/21**, G1-A/B/C/E/F PARTIAL, G1-D BLOCKED; public release/PHASE2 NO-GO. Stage13 preview language simulated 8/8 PASS but browser/Safari and no-outbound runtime proof remain BLOCKED. Recheck for newer evidence rather than treating these counts as timeless.

Relevant current work: [Stage13 #39](https://github.com/merapplications-sketch/Talabat-v3/issues/39) and [Master #26](https://github.com/merapplications-sketch/Talabat-v3/issues/26).
