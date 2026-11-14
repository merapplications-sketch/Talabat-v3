# TALABOT — Proposed staged roadmap (not authorized development)

## Operating boundary
**First: pilot launch with currently approved features**, only after existing QA, finance, RBAC, deployment/source and rollback gates are passed. This file is an opportunity backlog, not an approved product/release specification. No new payment/provider, UI, SQL, role, financial or hosted changes without separate owner approval.

### Phase 0 — finish existing product
- Current customer Home B, restaurant v1.6, customization Direction A, DineOut Gold; approved Admin Template B and UX-02; drivers, merchants and core.
- Independent safety/operational testing using synthetic isolated fixtures, exact deployed SHA, release reconciliation, cash and settlement checks, physical Safari observations.
- Fix only confirmed, approved defects with test regression and no changes to locked policies.

### Phase 1 — supervised pilot and stabilization
- Start a limited, explicit-owner-approved operational pilot, define participating restaurants, drivers and service boundaries, and record incident/dispatch/settlement metrics.
- Daily review of failed orders, delayed dispatch, wrong addresses, refund claims, delivery proof and network reconnection. Define actual thresholds after evidence; invent no targets.
- Remain ready to stop/revert through a tested rollback procedure.

### Phase 2 — high-priority proposal: outside Tajikistan purchaser → local recipient
A customer abroad pays for an order intended for a recipient in Dushanbe or other Tajik area. This requires a distinct legal/payment/identity design and is **NOT pilot-approved**:
- Buyer identity, payer consent, recipient name/phone/address, relationship and data-sharing controls.
- Pricing in TJS, displayed foreign-currency/FX conversion, transparent service fees and exact settlement/refund currency.
- Payment service provider coverage/country legality, verification/KYC/AML/anti-fraud, chargebacks, 3DS, sanctions screening and legal limitations. Never assume support for specific foreign cards.
- Recipient contact and availability, substitution, unreceived orders, proof/PIN, return cases, local delivery fees, support languages and dispute path.
- Keep approved **CASH-01/SCOPE-01** unchanged for current pilot; cross-border prepaid orders require separate contract and financial approval, never implicit cash rule replacement.
- Pre-approve role/permissions, duplicate payment protections, FX failure and partial refund expected results, separate buyer/recipient privacy, audit trails and E2E.
- Require owner-approved business case and UX/spec, realistic provider fees, legal review, safety tests and release scope before implementation.

### Phase 3 — other evidence-confirmed opportunities
Possible candidates only after verifying they do not already exist in current TALABOT:
- Customer courier live map/ETA, PIN-based delivery, restaurant thermal printing/POS, expanded merchant-in-order chat and optional native calls
- Storefront direct fulfilment, parcel delivery/C2C, multi-stop route, corporate meal credit
- Household/shared basket, multi-store add-on, paid loyalty/subscriptions
- Other competitor features retained only as source-backed research, not automatically approved tasks.

## Proposal acceptance record
For each feature: `ID | user/business value | confirmed current source gap (SHA) | operation constraints | fraud/financial/privacy impact | incremental monthly cost | dependency | test matrix | owner approval status | stage | assigned team role`.

Reference: [competitor & risk benchmark](../benchmark/TALABOT-20261114-feature-risk-global.md) and [master Issue #26](https://github.com/merapplications-sketch/Talabat-v3/issues/26).