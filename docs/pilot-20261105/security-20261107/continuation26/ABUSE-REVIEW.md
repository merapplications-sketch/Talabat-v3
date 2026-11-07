# Continuation26: request-abuse and cost-control source review

2026-11-07. Read-only current Worker/core plus saved rpc21 definitions and prior continuation24 business review. No SQL/network mutations, load tests, secrets or repeated tests. Current provider configuration and newer database function fingerprints must be checked separately before treating saved SQL as current deployment evidence.

## Concrete inspected boundaries

| ASVS | Control | Evidence / limits |
|---|---|---|
| V2.4.1 | Worker static routes | Only GET/HEAD outside /csp-report; unknown assets404 and other methods405. No outbound proxy or paid-service invocation in Worker. This is not DDoS protection or a request-count ceiling. |
| V2.4.1 | CSP report intake | Maximum actual streamed body16384 bytes,2-second read deadline, encoding/content-type checks, finite directive/status output. Log cap10/minute is per warm isolate and runs after body parsing; distributed isolates or new instances reset the count. It is explicitly best effort, not a global quota. No live bypass test needed or claimed. |
| V6.1.1, V6.3.1 | Login AF counter | Core AF is process-memory n/until/t0. After5 failures it backs off30s up to300s. A page reload starts a new AF object; independent clients do not share it. This is demonstrably client UX throttling, not server brute-force protection. Provider429 is handled; actual Supabase anti-abuse configuration remains required. Do not label provider protection absent merely from this client code. |
| V2.4.1, V6.1.1 | Recovery request | busy disables duplicate in-flight button submissions only; resetPasswordForEmail goes directly to provider. Reopening/reloading does not establish a server quota. Email spend ceiling, per-address/IP throttles and enumeration resistance require actual provider evidence. |
| V2.4.1 | Promo guessing | Saved check_promo holds per-user advisory transaction lock before reading10-minute limits (10 bad/60 total), and records attempts as returned results instead of throwing them away. Happy-hour early promo_offer return precedes insertion: such calls consume no recorded promo quota. They also do not evaluate/guess the promo code; do not describe this as a successful coupon guessing bypass. It leaves endpoint-compute traffic outside that counter. |
| V2.4.1 | Location writes | driver_location updates an approved online driver only when loc_updated older than3s. This limits writes per row, not HTTP invocations or connection costs. |
| V2.4.1 | Chat/tickets/store applications/errors | Saved chat counter20/minute; ticket creation5open/10daily; ticket replies20/hour per ticket+sender; store requests3pending/5daily; client errors10/hour. These are server checks, unlike client throttle, but count and insert are not visibly serialized in these functions. |

## Narrow source candidates, not live-confirmed vulnerabilities

1. Concurrent count-before-insert races exist as a concrete scheduling possibility in trg_chat_limit, create_ticket, ticket_reply, request_store and report_client_error: two transactions can observe threshold-minus-one before either insert becomes visible. ticket_reply updates its parent ticket after insertion; that later serialization does not recheck the earlier count. Other constraints/triggers may narrow effects; full effective schema and approved isolated concurrent proof are needed. No high-volume traffic was generated. Proposed minimal fix only after confirming: per-principal lock before count+insert (or existing stable row lock) with documented common lock order. Do not change quota values.
2. Earlier place_order per-customer count-before-profile-lock candidate remains in continuation24 report; not duplicated as a new finding. Pilot global capacity has its own lock and covers a different limit.
3. Worker CSP cap can be exceeded globally across isolates by design, and limits logs only after parsing. It must not be used as evidence of a hard cost cap. Apply provider-wide WAF/rate limiting only after confirming account/zone/routing authority; no such changes made here.
4. Client AF backoff can be reset by ordinary reload, since object initialization sets n/until/t0 to0. This is a demonstrated source property, not proof of server credential-stuffing vulnerability. Do not fix by imposing new customer login requirements.

## Provider and route separation

The application SDK invokes Supabase auth/database/storage directly. The reviewed static Worker does not proxy those operations. Consequently Cloudflare rules covering only the published site hostname cannot be assumed to cover Supabase endpoints. Need concrete active zone/routes/rules and provider-side auth/API/storage rate configuration. Also inspect authenticated upload count/byte retention quotas; client JPEG conversion and file-size checks do not establish aggregate storage-spend limits. Existing proof authorization evidence is preserved and not retested.

No hard spending ceiling for mail/OTP, maps, storage, egress or Worker execution was proved. Budget alerts notify after/near thresholds; a ceiling requires an enforced reject/disable mechanism over every billing path. Internal map routes remain disabled; no paid service was enabled. Read-only static Worker inspection cannot establish DDoS resilience or provider incident alert delivery.

V4 scope: method/body/content-type handling above gives limited API request evidence only. No full V4 requirement is closed from this review. V6.3.1 remains dependent on actual provider configuration and approved low-volume lockout tests, which must avoid repeated attempts during an active ban. Recovery MFA preservation and real event delivery remain independent open items, not resolved by the busy button.

## Next evidence, without changing customer policy

- Compare saved rate functions to deployed definitions and inspect effective insert constraints/triggers.
- Use an approved disposable/rollback-only multi-session harness for identified quota schedules; do not repeat rejected setup or create permanent records to evade restrictions.
- Obtain actual Supabase auth email/IP limits, CAPTCHA configuration if any, storage limits/retention, hard spend behavior; distinguish configured from verified.
- Obtain Cloudflare active route/rule coverage and plan limitations, and verify logging caps versus request caps.
- Name incident notification recipient and verify delivery through approved synthetic event once available; no external messages sent in this review.

No requirement-wide pass, production changes, load test, or independent penetration-test claim. No protected data/accounts/order balances were touched.
