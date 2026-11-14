# TALABOT — Proposed Future Stages (NOT AUTHORIZED IMPLEMENTATION)

The current owner priority is **pilot launch using approved existing features**. Keep international competitor research as a backlog only. All development starts after explicit separate owner decisions and the appropriate security/finance/design gates.

## Phase 0: pilot-readiness now
Existing customer, driver, merchant and admin modules. No new feature work or redesign. Source/CI/prod provenance, synthetic end-to-end QA, financial and RBAC assurance, independent security and physical Safari UI, recovery/ops handoff, then scoped owner release approval.

## Phase 1: supervised pilot and stabilization
Small owner-authorized operational scope, with real order/error/support/settlement metrics, complaint handling, dispatch reliability, delivery timings, refund reconciliations, lost-location/device conditions and documented incident rollback. Pick numeric thresholds later only after evidence; do not invent order counts or SLA.

## Phase 2: high-priority proposal — abroad payer → local recipient in Tajikistan
A user outside Tajikistan buys for a person inside Tajikistan (e.g. an expatriate ordering food for family in Dushanbe). This is a proposed **new payment/identity flow**; it is not already pilot-approved. Required product questions before implementation:
- Who is buyer, recipient, and contracting party? Separate profile/phone/address, consent, and which data each sees.
- Local delivery fees and TJS price; cross-border payer currencies, FX quote/fee transparency and settlement currency; taxes and provider legality.
- Payment method(s) actually supported in the payer's country; PSP coverage, compliance/KYC/fraud/chargebacks, 3DS/AML/sanctions and consumer protections. Do not assume a provider supports Syrian or other cross-border cards.
- Cash, payment at purchase and refunds must not silently override existing approved CASH-01/SCOPE-01. Define independent cross-border flows and get explicit finance/owner approval.
- Recipient availability, phone verification, unable-to-deliver cases, substitutions, delivery code/proof, return/refund liability, support language and privacy.
- Risk cases: duplicate cross-border charge, disputed payment after courier pickup, refund currency difference, fraudulent recipient/address, disclosure of payer identity, delayed/failed FX and wallet reconciliation.
- Positive and negative UAT, security review, and merchant/driver role behavior before any public launch.

## Phase 3: optional other competitor features, only after gap proof
Potential candidates: door-to-door parcel courier, merchant on-demand fulfillment API, corporate/team meals, shared household cart, multi-store add-on order, verified delivery code, POS/printer integration, optional subscriptions. Benchmark claims alone are not evidence of absence from newest TALABOT source.

## Feature approval record
`Feature | confirmed absent? (SHA/evidence) | market/user value | launch dependency | security/finance/legal impact | incremental cost | acceptance tests | owner decision | assigned release stage`.

No source/UI/financial logic, new provider, database schema, access permissions or deployments can be changed based solely on this document.
