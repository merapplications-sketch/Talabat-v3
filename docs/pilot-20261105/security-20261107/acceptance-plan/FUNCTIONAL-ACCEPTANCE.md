# TALABOT remaining acceptance — snapshot 2026-11-07

Read-only inventory; no source/database mutation, deployment or account operations. Current source reviewed: 5e80ea2271c628b50241eb6042e265adfb4973f0 (.10, hosting20). Implementation review, not independent penetration testing. Newer REPORT.md evidence supersedes earlier pending lines in the accepted checkpoint. Preserve orders #1/#2/#3; #3 stays unsettled. Do not repeat accepted cash journeys or settle driver balances collectively.

## Current evidence retained; do not rerun without a regression reason

| Area | Exactly established | What is still outside that evidence |
|---|---|---|
| Cash order/settlement | Earlier accepted cash journeys and receipts #1/#2 retained; #3 delivered and intentionally unsettled | No permission to close #3 or relabel its unpaid due as a defect |
| Merchant adjustment | #4 initial65, proposal40 blocked preparation until customer accepted; prepare/ready/offer/driver acceptance/arrival/pickup passed | Decline/timeout/competing proposal branches not established; #4 remains pickedup |
| Wallet spend/return | #5 spent20, cancelled before preparation, exactly one20 return; fixture adjustment reverted, final balance0; published receipt now shows confirmed refund | Concurrent wallet writers, other cancellation states, rollback/network ambiguity |
| Period report | 501-row synthetic test; paging500 with explicit failure if >50000/error; live3 delivered/1 cancelled/75 gross/75 net matched DB | Multi-day/date-zone boundaries and multi-store visibility; no need to repeat the completed501 fixture |
| DineOut | Approved function equality;25% card opens correct menu with25% | Owner's final visual acceptance; no table-booking product exists by implication |
| Support | New unlinked ticket sent, received, admin reply delivered live, resolved without refund; harmless HTML rendered literally | Refund workflow, attachment branches, rating/reply moderation, race behavior |
| Chat | Bidirectional text previously; incoming Safari actual message produced sound and visual alert per owner | New-order sound, app background/closed Push, ambiguous acknowledgement exactly-once |
| Offline draft | .9 owner confirmed draft retained/error while offline; after reconnect/manual retry SAFARI-OFFLINE-02 appears once in customer UI and DB | Automatic queue not provided; uncertain server-accepted/client-timeout duplicate case not proven |
| GPS/map | Owner confirmed GPS chat send; parent reports driver tiles36/36; earlier address/map browser checks | GPS refusal/stale accuracy/location off; real external navigation and continuous moving-map product |
| Camera/proof | Owner local camera preview succeeded; earlier synthetic proof upload and owner display succeeded | Actual phone camera-to-private-proof upload, failure/resume, unauthorized HTTP byte download |
| Catalog image | Merchant draft upload+preview worked and draft closed without saving an item; object exists | Customer upload denial was a policy-condition check, not real HTTP upload rejection; save/edit/remove whole item flow |
| Role login | Five roles and accountant isolation observed; admin30min timeout and secure re-login observed | Full Auth lifecycle, MFA, recovery, revocation and sensitive-action reauthentication |
| Security headers |75 local wrapper tests; .10 deployed customer200 HSTS31536000/includeSubDomains, COOP same-origin, CSP object-src none/base-uri none/frame-ancestors none, XFO and nosniff; map36/36 | All-response/endpoint coverage incomplete; fallback CSP still frame-only, inline allowances remain, reporting absent |
| Points | Rollback DB:2500 live,5000 expired excluded; redeem2000=>500 and value2; cancel=>2500; repeat cancel rejected | No full UI points journey/expiry display; fixed return-confirmation field only had automated rendering proof |
| Coupon/Happy Hours | Rollback DB valid10% persisted; duplicate reuse denied; overnight22:00/02:00 boundaries tested | UI eligible/ineligible dates, timezone and stacking precedence, cart-to-order display/history |
| Gift | Invalid recipient rejected; valid recipient flag persisted in rollback DB | Sender/recipient/merchant/driver complete UI, address/contact privacy and cancellation display |
| Group | Add quantity/state guards; expired checkout bypass fixed/retested rollback | Multi-participant UI, host/member ownership and removal, checkout races and complete totals display |

## Prioritized work queue

| Priority | Acceptance unit | Existing evidence to reuse | Next bounded test and completion condition | Dependency/blocker |
|---|---|---|---|---|
| P0 | Finish auth/telemetry acceptance | .10 fixes correct accountant namespace, expose global-signout errors, filter telemetry;18 frontend regressions and server rollback filters passed; migration pilot_structured_client_error_telemetry applied | Reuse repaired-path tests; separately prove remote session revocation and review every other log sink/historical retention | Dedicated sessions and full log inventory; do not relabel completed repairs as open integration |
| P0 | Real HTTP access boundary | Current rollback outsiders and finance projection checks; historical REST ledger | Complete role×object×field read/write matrix incl cross-store, stale permission, Storage upload/download bytes, Realtime | Dedicated login-capable test identities; current signup blocked. Do not forge Auth rows |
| P0 | Monetary contention/ambiguity | Current request locks/source; sequential finance replay and conflicting request; historical refund/driver races | Barrier-synchronized current same-key/conflicting/different-key calls plus acknowledgement loss; assert ledger invariants and read-only reconciliation. Scope all wallet writers, settlement and refund | Two actual overlapping connections; concurrency-attempt output alone does not establish overlap |
| P0 | MFA/session/recovery | Five role login, admin idle timeout, bounded source review | Agree enforcement/recovery policy; dedicated identities test MFA enrollment/challenge, expiry/replay, session disable/logout/token rejection and sensitive financial reauth | Identity policy, controlled mailbox/factor, provider configuration; no existing account reset |
| P1 | Physical new-order alert | Real message audio/visual passed; new-order browser alert exists | One authorized dedicated new order/offer received while foreground Safari, owner confirms audible and visible output | Owner device window; do not reuse protected orders |
| P1 | Phone proof upload/navigation | Local camera and GPS send passed | Capture synthetic non-personal image through actual order proof flow and verify owner display; test denied camera/location and external navigation fallback | Owner device; dedicated permitted order state. Do not accidentally deliver/collect cash |
| P1 | Merchant modification negative branches | #4 accept path complete | Dedicated case decline/expiry and retry: no unauthorized preparation, totals and state consistent across both UIs | New isolated order; documented branch behavior |
| P1 | Points UI | Actual DB functions pass rollback tests | Dedicated UI redeem/cancel/history, expiry excluded from available balance, return once and receipt correct | Synthetic earned points fixture with rollback/cleanup plan; avoid shared balances |
| P1 | Promotions | Coupon/HH DB boundaries pass | UI cart→submit→receipt for valid/invalid/used coupon and HH boundary; confirm stored snapshots and stacking documented | Controlled clock/data fixtures and documented price precedence |
| P1 | Cashback | No current complete acceptance identified | Dedicated qualifying completion creates one award; excluded/cancelled order none; retry none extra; display matches ledger | Qualifying policy and isolated completion/cleanup |
| P1 | Gift/group UI | Limited rollback DB tests and expiry fix | Two dedicated customer identities: recipients/participants, ownership, totals, join/remove/expiry/checkout, failed/retried operation | Second real identity; role/privacy checks |
| P1 | Ratings/replies/support refund | Support no-refund text loop passes | Dedicated delivered fixture rating restrictions, store response, moderation; refund cap, partial/repeat/refund-ticket UI and audited ledger | Delivered synthetic fixture and explicit refund test scope; no protected-order change |
| P1 | Branch/menu management | Draft image preview only | Dedicated branch/item create/edit/availability/options/image/save, merchant isolation, customer refresh and stale cart rejection | Dedicated disposable store/items; preserve approved catalog/design |
| P2 | Reporting boundaries | Complete-period pagination fix already verified | Timezone/end-boundary, zero rows, cancellations/deductions and RLS across stores; compare aggregate result | Test data; no finance mutation required |
| P2 | DineOut visual signoff | Function parity + correct menu route passed | Owner compares approved /review reference with current screen and states accept or concrete discrepancy | Owner visual decision; no inferred redesign |
| P2 | Dependency/history/config review | Bounded secret scan and pinned assets | Full history/SBOM, CDN SRI, source-to-deploy mapping and CI/provider permissions with redacted results | Repository/provider evidence |
| P2 | Backups/alerts/incident | Historical separate restore artifacts exist; current operational coverage incomplete | Validate latest inventory/restore evidence equivalence, then isolated restore with consistency checks and real notification delivery/tabletop | Separate restore target, protected backup access, actual receiver/on-call owner |

## External product/service decisions — not accepted features or one-key fixes

Electronic payments/Apple Pay need provider contract, credentials, webhooks, reconciliation/refund policy and sandbox tests. Email/OTP need controlled delivery and abuse/recovery policy. Push/SMS/WhatsApp need platform/provider and consent decisions; foreground audio does not establish background delivery. VoIP needs signaling/media/TURN scope. Google rating requires its external destination/API policy. Voice address, table booking, automatic geofence, continuously moving driver map, printers and general ledger require explicit behavior and integration scope. Internal paid routing stays disabled pending cost decision. Permanent watchdog, backup schedule and alert/on-call delivery require operational ownership. Do not conflate any of these with currently proven defects.

## Historical evidence is not erased or silently promoted

`/workspace/scratch/b5c2c5a1aa04/talabat/docs/pilot-20261105/integration-acceptance-ledger.json` records prior real signup/password/refresh/forged-JWT rejection, REST address/cross-role isolation, order retry/reconnect, competing drivers, driver busy lock, refund contention and refund-storage atomicity. Those entries have November5 source hashes. Retain them as historical coverage; current .9 acceptance needs a source/config equivalence record or a narrowly justified retest. Historical ledger order numbers are NOT assumed to identify current protected orders.

The checkpoint references `hosted/audit-20261107/INVENTORY-AR.md` and repair handoff; those exact files were not found in the local sources searched. This inventory uses the explicit checkpoint corrections, current REPORT, source-review report, functional SQL report and historical ledger. It does not invent acceptance for missing original inventory rows.


## AUTH-COMPAT-20261107 owner-approved scope addition
Customer login must remain unchanged; no mandatory QR/authenticator. See ../auth-compatibility/ACCEPTANCE.md for physical older-device login/logout/recovery and weak-network rows (not tested), evidence requirements and unaccepted minimum support floor. Administrative MFA/recovery is separate. Existing closed tests are reused only when unaffected.
