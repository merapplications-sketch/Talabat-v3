# First-party CSP coverage and report receiver — candidate for .19

Baseline source2491da72befb3bffcfc7d7a9ebb902a2173fd868 (.18). Root owns build/publication; this report records local evidence only until root appends deployment results. Scope: Worker/scripts/tests. No public asset bytes or DB mutations by this agent.

## Implemented

- All first-party Worker replies, including redirects/errors/method rejection, use default-src 'none'; object-src 'none'; base-uri 'none'; frame-ancestors 'none'; report-uri /csp-report as their default policy.
- Each asset has a complete policy. HTML with existing meta policies preserves existing resource directives and gains enforced object/base/frame/report directives. Existing application inline script/style allowances remain; this is not full XSS or strict-CSP closure.
- HTML lacking meta policy receives a restrictive policy. Existing inline blocks get build-time SHA256 hashes; /review styles and same-origin comparison images are preserved, scripts are denied when absent. Non-HTML assets receive restrictive fallback policy. The CSP on a JS/CSS response does not replace the policy of its embedding document.
- /csp-report accepts POST application/csp-report with same-origin or absent Origin, rejects explicit cross-site Fetch Metadata, unsupported content types/encoding and malformed data. No CORS grant is added. Anonymous report data is untrusted and is not authentication evidence.
- Body size limited to16384 actual streamed bytes, independent of Content-Length; timeout2seconds. No unbounded request.text()/json() buffering. Compressed request bodies rejected. Stream cancellation itself is bounded to100ms so a stalled cancel promise cannot stall the response.
- A valid legacy report emits at most one structured console record containing only fixed event/version, allowlisted directive, normalized disposition and integer HTTP status0–599. Document URL, blocked URL, source file, policy, script samples, user identifiers, IP and arbitrary text are never copied to application console output. A fixed two-scalar minute bucket caps application console output at10 records per minute per warm isolate; excess valid reports return204 without console emission. This is best-effort local sampling, not a global quota, traffic limiter or cost ceiling. Response204 is empty and no-store. Errors also no-store and protected.

## Tests

`node scripts/build.mjs` then `node --test tests/headers.test.mjs tests/csp-report.test.mjs` in isolated candidate snapshot:84/84 passed. Source snapshot contained74 assets.

Coverage: byte-identical GET bodies for every asset; HEAD, clean redirects/query preservation,404/400/405 and malicious encoded paths; required directives on every tested response; meta resource directives preserved; review style hash matches original bytes; report whitelist strips synthetic secret markers; origin/type/encoding/schema failures; invalid UTF8; stream exception; stalled stream cancelled after2seconds; exact16384-byte valid payload; oversized streamed bodies rejected with missing and falsely-small Content-Length; cap at10 records/minute, minute reset, invalid reports not consuming slots; unresolved cancel promise returns within its bound.

Result file: test-results.txt. Candidate path /workspace/scratch/talabot-csp18-candidate. Shared source changed only worker/index.js, scripts/build.mjs, new scripts/csp-policy.mjs, tests/headers.test.mjs and new tests/csp-report.test.mjs. Root should build against its combined current public assets and run these tests again.

## Acceptance boundaries

V3.4.3 first-party fallback minimum is implemented and locally tested. Existing unsafe-inline allowances and complete resource trust/endpoint coverage remain for broader assessment; do not grant whole-requirement pass merely because object/base directives exist.

V3.4.7 all first-party policies now name /csp-report, with functional local ingestion and sanitized console emission. After deployment verify actual GET/error/redirect headers, bounded POST response and a browser-generated report. report-uri is the legacy compatible format; no report-to endpoint group is advertised. Report-To/Reporting-Endpoints modernization is not claimed.

Provider gaps: Sites host may generate its own edge/auth/WAF error pages before this Worker; Supabase Auth/REST/Storage/Realtime and CDN/tile responses are outside this Worker. Their headers and response behavior need separate evidence. Worker console emission does not establish that Sites enables log storage, sampling, retention, access control or live log retrieval. No durable report store, downstream receiver, alert delivery, globally coordinated rate limit or incident monitoring was added. Network/reverse-proxy invocation logs may contain provider metadata independently of this sanitized application record.

## Technical references

MDN report-uri: https://developer.mozilla.org/en-US/docs/Web/HTTP/Reference/Headers/Content-Security-Policy/report-uri — legacy JSON POST application/csp-report.
Cloudflare Console: https://developers.cloudflare.com/workers/runtime-apis/console/ — console.log emits runtime logging events.
Cloudflare Workers Logs: https://developers.cloudflare.com/workers/observability/logs/workers-logs/ — log persistence requires observability configuration, which is not exposed/verified by this change.
