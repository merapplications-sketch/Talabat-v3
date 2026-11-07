# Bounded client data and cryptography review — 2026-11-07

Reviewed working tree `/workspace/sites/talabot-security24/.sites-checkout`, continuing .22 base `4c78c739cd65c53746b07db6426cf5f66f178d8a`. Root agent owns subsequent fixes/commit/deployment. No provider, database, browser or protected-account operations were performed by this review. Evidence below is source-derived and synthetic local execution, not independent penetration testing.

## Confirmed findings and affected retests

| Finding | Severity and impact | ASVS 5.0.0 linkage | Evidence and result |
|---|---|---|---|
| In-flight proof download completes after clear/signout and creates a new object URL | Medium: private client file survives the intended cleanup boundary; no server authorization bypass demonstrated | V14.3.1, partial requirement evidence only | `proof-late-resolution-before.json` shows late URL created and never revoked. Root added epoch invalidation. `proof-epoch-after.json` passes overlapping old/new responses, normal authorized creation, cleanup revocation, fresh epoch and stale suppression. |
| Passive SIGNED_OUT leaves prior private UI visible | Medium: existing identity/order data remains visible in the application after passive local session termination; no new unauthorized server read demonstrated | V14.3.1, partial requirement evidence only | `passive-signout-before.json` shows callback leaves synthetic private DOM, ME, DB and ORD. Root added immediate body hide and deferred reload for passive events, with explicit signout counter. `passive-signout-after.json` passes expected helper behavior and preserves incomplete-remote-signout warning. |

### Reproduction

From any directory, pass actual candidate core to these scripts:

```
node proof-epoch-regression.cjs /workspace/sites/talabot-security24/.sites-checkout/public/talabat-core.js
node passive-signout-regression.cjs /workspace/sites/talabot-security24/.sites-checkout/public/talabat-core.js
```

Scripts extract actual source helpers. Downloads, JPEG metadata, Auth callback and DOM are synthetic. No real file or account is used. Before scripts/results retain the initial failure evidence; post-fix regression files are reusable.

### Exact passive-event dependencies and limits

The original auth callback cleared only proof object URLs. Core retains ME, DB, ORD, seenChat, lastStatus and unread; individual role bundles retain further state (for example customer ME/S and driver DRV). Pending loader promises mutate DB, and refresh completion reshapes ORD and schedules render callbacks without a session epoch. Merely nulling identity or emptying the application DOM therefore does not reliably prevent old callbacks from repopulating it.

The applied passive fix hides the body synchronously and schedules a full reload outside the Auth callback, discarding closure state on successful navigation. Duplicate passive events are suppressed. The explicit signout counter prevents early reload from suppressing the existing remote-revocation failure warning. Regressions cover error result, rejected promise and synchronous throw, and recovery of the counter.

Hidden UI is distinct from memory erasure: closure data remains until navigation completes. Synthetic tests do not prove actual browser reload completion, cross-tab/provider event delivery, or complete cleanup after failed explicit remote signout. These remain outside this bounded result. Do not close V14.3.1 in full from these tests.

## Other bounded source observations

- Recovery return URL is derived from `location.origin + location.pathname`, omitting query and fragment; no arbitrary redirect input was identified in that helper. This is not blanket recovery approval.
- Customer deep-link store/group identifiers use UUID validation. No secret/token-in-URL finding was demonstrated by this review.
- Role auth storage keys are enumerated/namespaced. This is client isolation, not proof of server authorization.
- Financial request UUIDs are idempotency identifiers, not authentication secrets. Their UUIDv4 entropy is not flagged as an authentication-key defect.
- Scheduling jitter and non-secret filename fallbacks using Math.random are not by themselves proven cryptographic vulnerabilities.
- Previously fixed persistence and signout cases were not independently rerun here; root retains their applicable evidence.

No further actionable V11 flaw was established in this bounded pass. This does not certify crypto key custody, provider encryption at rest, backup encryption, retention, all URL flows, or full V11/V14 compliance. Provider evidence and live behavior remain separate matrix work.
