# V1.1.1 canonicalization inventory — continuation27

2026-11-07. Read-only current first-party source, baseline provided by parent .27 commit5a85f8c0ade674fe7ec7db7845ae75ee9123749d; parent may change release metadata concurrently. Saved SQL definitions are supporting historical evidence and need deployed-definition attribution. No source edits, provider calls, live payloads or repeats of closed handler tests.

ASVS5.0.0 V1.1.1 requires decoding once, only where encoded input is expected, before further processing/validation. The observations below are partial coverage, not requirement closure.

| Boundary | Decode/canonicalize | Following processing | Narrow assessment |
|---|---|---|---|
| Worker URL | URL(request.url) parses URL; decodeURIComponent(url.pathname) once in try/catch | Decoded pathname is checked by own(ASSETS,key); fixed clean-URL aliases; encoded redirect preserves raw query | No second explicit percent decode found in this handler; malformed encoding400. Asset lookup is a whitelist, not filesystem traversal. URL parser normalization itself requires testing as a separate interpretation layer. |
| Worker CSP body | Streaming UTF-8 TextDecoder fatal=true then JSON.parse once | Object shape, directive allowlist, integer status; output constructed fresh | JSON string escape decoding is expected at parse boundary. No downstream decode of supplied URL/policy fields (not retained). Existing CSP tests remain intact and were not repeated. |
| Customer store/group deep links | URLSearchParams.get performs query decoding | Strict UUID regex then lowercasing; not decoded again | Encoded percent characters surviving the query decoder fail UUID validation. First duplicate query key is selected by get; it is a consistent client selection, not proven authorization confusion. |
| Core role/session/diagnostic query flags | URLSearchParams.get | Exact values accountant, asvs-review,1 | These select session namespace/test UI, not SQL role authority. No second decoder found. Presence of UI controls is not proof of backend permission. |
| Cart note key | encN uses encodeURIComponent plus encoding of !'()*~; pk splits raw key at literal ^ and decodes note suffix once | Whitespace normalization/trim and120-character bound; lineNotes sends note text via JSON RPC | A note intentionally containing %27 is stored as %2527 and comes back as literal %27 after one decode; no second percent decode located in this note path. SQL truncation is not a percent decoder. No handler test repeated. |
| Cart/local preferences | JSON.parse localStorage | Domain-specific load validation and server recalculation | JSON decoding is expected. Storage is untrusted input, but existence of JSON.parse alone neither proves unsafe use nor full validation. |
| Approval legacy-key migration | JSON.parse old argument suffix | Requires object, roundtrip JSON.stringify equality and UUID request ID; SHA256 new key | Not recursive decoding. Serializing canonical object preserves the decoded value, not executing it. Existing migration tests not repeated. |
| Return request | JSON.stringify structured args, SHA256 retry key; amount String | Server typed arguments; ref upper/btrim then structured payload comparison | Client hashes raw ref, server compares uppercase/trimmed ref. Semantically equivalent client strings can yield distinct retry UUIDs; downstream source_ref/stage constraints must govern duplicate effects. Not a demonstrated duplicate-refund bypass. |
| Phone SQL | norm_phone removes non-ASCII digits then accepts fixed992/9-digit/leading0 formats | Returns canonical +992 text or NULL | Normalization happens before format validation. It is intentionally lossy and does not prove ownership; phone-update authorization was tested elsewhere and is not reopened. |
| Promo SQL | upper(trim(code)) | Lookup, attempt tracking and rules | Case/whitespace canonicalization before comparison, not percent/HTML decode. No alternate decoder found in saved functions. |
| Image URL SQL | check_image_url checks allowed data:image or fixed media URL prefix | Browser/storage URL interpretation follows | This function does not canonicalize URL. Need complete current image-sanitization and storage evidence before evaluating encoded path/format differences. Existing image tests not repeated; no new exploit claimed. |

## Interpreter transitions needing accurate classification

HTML entity decoding of generated inline handlers is an HTML interpreter boundary, not an extra percent decoder. Previously fixed customer recommendation entity injection is already recorded with proof; it is not a new V1.1.1 finding. JSON serialization followed by HTML attribute parsing requires both correct context encodings, as already repaired. This inventory does not downgrade that existing proof or rerun it.

URL() may normalize literal and percent-encoded dot segments before the explicit Worker decode. The Worker then uses a closed ASSETS key map, so filesystem escape is not inferred. Double-percent forms such as %252e retain a percent sequence after the one explicit decode and must not be described as automatically recursively decoded.

## Bounded next tests, not run here

1. Pure local Worker route matrix using the actual asset map: single/double encoded slash/dot, malformed percent/UTF-8, duplicate slash, encoded question/hash, clean URL redirects. Assert lookup target and redirect count; no network traffic and no arbitrary-file-read expectation.
2. Pure cart-key roundtrip using real encN/lk/pk functions: literal percent sequences, caret, quote, Unicode combining text, malformed suffix and whitespace. Assert intended normalization and exactly one decode; exclude already closed HTML-handler cases.
3. Local deep-link extraction matrix: double-encoded UUID punctuation, duplicate store/group/session keys and plus handling. Assert UUID rejection or deterministic documented selection. This checks parsing only, not database authorization.
4. Current image validator/consumer inventory before any payload test: distinguish data:image parsing, media URL path normalization and actual content verification; reuse prior successful image evidence first.
5. Return reference duplicate-equivalence review against current unique constraints and stage guards. Source key differences alone are not a financial flaw; no permanent financial fixtures or repeated rejected concurrency setup.

## Outcome

No NEW demonstrated double-decoding exploit found in this bounded inventory. Full V1.1.1 remains partially assessed: SDK/provider decoding, all form consumers, image paths, current SQL attribution and alternate write endpoints are not exhaustively covered. No requirement-wide pass or independent-review claim. Protected accounts/orders/receipts, production and customer login policy unchanged.
