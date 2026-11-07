# Protocol applicability review — continuation24

This is a bounded source review, not a live provider test. `component-files.json` records hashes of 16 deployable HTML/JS/JSON components. `per-id-decisions.json` preserves the official requirement text and provides a decision/gap for every V1/V4 row in the supplied 331-row triage (46 rows). No full requirement closure is proposed from this evidence alone.

## Actual component boundaries

- `worker/index.js` is the only supplied server runtime: static embedded ASSETS via GET/HEAD and a POST `/csp-report` JSON receiver. It uses WHATWG Request/Response/URL, TextDecoder and JSON.parse; it has no outbound fetch or runtime process/database binding. Static responses come from generated asset data rather than filesystem traversal. CSP intake bounds actual stream bytes/time, rejects unexpected encoding/media type, parses strict UTF-8, validates a small directive allowlist and projects primitive status/disposition into logs.
- Five role applications use shared `public/talabat-core.js`. Their backend is fixed HTTPS Supabase project `fsvrsvqfknogwmhccera`. Data calls use SDK REST table queries and named RPC; Auth and Storage also terminate at the provider. This is not a self-contained backend implementation: SQL functions and provider ingress/runtime configuration must be assessed separately.
- Shared core `subscribeRealtime()` subscribes to postgres_changes for orders, chat, offers, support and wallet events. WebSockets are therefore applicable, not absent. Vendored SDK `supabase-2.117.2.js` builds realtime/v1 from the HTTPS base then replaces protocol http with ws: the configured result is wss. Channel token provenance, revocation and Origin enforcement still need verification at the provider boundary.
- Receipts are client HTML/print; no application TeX or native document conversion service is part of this deployment. Browser storage JSON and SDK network JSON/binary messages remain actual deserialization boundaries.
- Build scripts are not request-serving runtime; their filesystem/process capabilities must be reviewed as CI supply-chain controls separately, not confused with exposed command-injection sinks.

## Decisions that affect triage

V1.2.5/6/7/8, V1.3.8/9 and V1.5.1 have concrete application-component non-applicability arguments in the JSON. They are **candidates only for the supplied application scope**, not claims about hidden managed services. No LDAP/JNDI/XML safety certification is inferred from string searches.

V1.5.2 remains applicable: JSON-only does not by itself certify safe object handling. The Worker projects allowed primitives without type instantiation, but other local state and SDK message handling need full coverage. V1.5.3 remains applicable across browser, Worker and provider parsers.

V4.3.1/2 must remain open: absence of a GraphQL frontend call cannot establish that the Supabase project's GraphQL endpoint is disabled or limited. PostgREST data expressions also fall within the data-layer cost question.

V4.4.1–4 remain applicable or requiring token-scheme confirmation. Browser WSS source configuration is useful partial evidence; REST CORS is not WebSocket Origin validation.

V4.2.1–4 are predominantly ingress/runtime boundaries. Local WHATWG Request tests cannot establish HTTP/2/3 framing or anti-smuggling at Cloudflare/Supabase. Provider evidence and bounded wire-level tests are required. Worker method restriction is partial V4.1.4, not coverage of Auth, REST, Storage or Realtime endpoints.

## No new vulnerability claim

This pass established scope and missing evidence, not a new exploit. Untested controls are not vulnerabilities. No live request, account, database, source or provider setting was changed. Root should combine the per-ID decisions with SQL/runtime/provider inventory before accepting any requirement closure.
