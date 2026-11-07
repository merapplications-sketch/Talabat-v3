# Continuation 24 — bounded client source review

Date: 2026-11-07 UTC. Source: `/workspace/sites/talabot-security24/.sites-checkout`. Restored baseline .22 / `4c78c739cd65c53746b07db6426cf5f66f178d8a`; current source changed by parent during review. Exact customer file hashes are recorded in test JSON. This review did not change app source, use a browser, mutate a database, access production, or repeat closed security tests.

## NEW finding C24-CLIENT-01: entity-decoded JavaScript in cancellation recommendations

**Severity: medium confirmed unsafe rendering; potentially higher conditional impact if the full lower-privilege persistence and display path is demonstrated.** No session theft, account takeover or live stored exploit was attempted or demonstrated.

In `public/customer.html`, `cxCard(o)` renders out-of-stock cancellation suggestions with a store name in an inline handler. The former code serialized `s.n` with JSON.stringify and replaced only literal double quotes with `&quot;`. Existing ampersand entities were left untouched. HTML attribute decoding converted an entity supplied in the store name into a JavaScript delimiter before event compilation.

A synthetic string containing `&quot;` or `&#34;` followed by a harmless local marker statement escaped the intended `openN` argument. This is a context mismatch: JSON serialization handles JavaScript string syntax, but the resulting string also passes through an HTML attribute interpreter.

ASVS 5.0.0 mapping (partial evidence only):
- V1.1.2: perform output escaping at the final interpreter boundary.
- V1.2.1: context-appropriate HTML attribute encoding.
- V1.2.3: prevent dynamically generated JavaScript/JSON injection.

### Data flow and prerequisites

The recommendation card is only displayed for rejected orders with the out_of_stock reason, a compatible alternate open store, and a matching dish. `simDishes(o)` supplies `s.n` from STORES; clicking the `.sdi` suggestion triggers the handler.

Saved SQL definitions in `rpc21-inventory.json` show a possible merchant-origin data path: request_store accepts a trimmed 2–80 character name; decide_store_request requires admin approval and copies the name to stores. The new store initially has is_active=false and is_open=false. Admin approval, activation/opening, matching menu data, and the rejected-order display path are therefore prerequisites. Saved validate_store does not encode names. This is not a full live-schema constraint audit, and end-to-end persistence was not tested. Absence of input encoding is not by itself a defect; the unsafe output boundary is the demonstrated defect.

### Proof and proposed minimal fix

`customer-handler-proof.py` extracts the actual renderer and core esc helper, provides synthetic data, parses the emitted HTML attribute using Python HTMLParser, then executes only that handler inside a Node VM with openN stubbed. No network or database requests are made.

Reproduce:

```sh
python3 customer-handler-proof.py /workspace/sites/talabot-security24/.sites-checkout
```

`customer-handler-results.json`: former renderer preserved 4/7 literal arguments; two synthetic entity cases executed the harmless marker. A virtual in-memory candidate preserved 7/7 arguments and executed zero markers.

Minimal replacement: use `esc(JSON.stringify(s.n))` for the HTML attribute context, instead of replacing only quotes.

Parent subsequently applied a source fix and produced `customer-handler-after.json`: actual changed renderer preserved 7/7 arguments and executed zero markers. The post-fix file hash differs and is recorded in that JSON. This establishes a narrow local regression result, not a published-browser or whole-ASVS pass. Parent owns source commit/deployment attribution.

## Adjacent reviewed controls: narrow negative results

- Admin proof download handler interpolates deliveryPhoto into JavaScript after HTML escaping. Arbitrary strings would not be a sufficient safe contract, but the saved deliver_order RPC accepts only an assigned-driver/order-specific path with an `[A-Za-z0-9_-]{8,64}.jpg` filename and checks storage existence. Quotes/entities cannot pass that saved function. No reachable injection proved; treat alternative write paths and actual schema as remaining coverage, not a confirmed finding.
- Customer notification handler has the same quote-only helper pattern around order IDs, but observed data is bigint/normalized numeric. No string-control bypass proved. Do not infer another vulnerability solely from the sink.
- Inspected dynamic inline handlers largely interpolate bigint/UUID IDs, fixed enums, array indices, or internal navigation state. This is source triage, not complete proof of every caller/data source.
- Existing admin support/staff handlers already use HTML escaping around JSON serialization. Their previously closed tests were not repeated.
- `bannerGo` resolves store IDs against local store data, dispatches category navigation, or uses the fixed relative partner.html path. No arbitrary external redirect target appears in this function. This does not close all redirect/navigation requirements.
- Targeted first-party asset/core search found no eval/new Function; core innerHTML assignments inspected were static overlays. Full HTML pages use many template renderers, so absence in this limited search is not whole-app injection clearance.
- No first-party CSV export implementation was identified in a targeted filename/MIME/helper search. This alone does not establish spreadsheet-formula requirements as non-applicable.

## Boundaries / remaining checks

The review is implementer-assisted local source testing, not an independent penetration test. It does not prove stored exploit reachability, mobile/browser compatibility, live deliveryPhoto invariants across every write path, all output sinks, or any entire V1/V3 requirement. No accounts/passwords, protected orders, receipts, settlements, customer login policy, design or production data were modified. Existing successful proof-access, accountant-session and staff-revocation evidence remains intact.
