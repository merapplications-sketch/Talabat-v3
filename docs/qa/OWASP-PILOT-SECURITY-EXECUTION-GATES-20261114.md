# TALABOT — OWASP ASVS L2 pilot security execution gates
**Compiled 2026-11-14 (Asia/Dushanbe) | Status:** REVIEW-ONLY SECURITY QA PLAN — NOT TEST RUN, NOT FIXES, NOT RELEASE AUTHORIZATION.

## The controlling standard and the existing work
- **Correct owner-recalled term:** **OWASP ASVS v5.0.0 Level 2**, not **AVA**. The first term is a security-requirements standard; AVA is a separate JavaScript unit test framework. **OWASP ZAP** is a separate scanner, and no successful execution of ZAP is substantiated by current project evidence.
- **Historical evidence:** owner-held private Work handoff `TALABOT-Project-Handoff-2026-11-09.txt`, project history `review/security90-20261109`, snapshot `6c4c15ee1bb09b868be27405dc3ec29d5a882336`; previous project-specific matrix of **345 items: 1 PASS, 2 FAIL, 330 UNTESTED, 12 N/A**. The number is a **project matrix count**, not a claim that the official ASVS L2 alone includes exactly 345 controls.
- The old Work checkout reportedly lacked a verified Git remote. **Do not assert the private 345-row matrix or old code fixes are pushed to the public GitHub repository.** Keep sensitive evidence private. See [historical ASVS evidence map](OWASP-ASVS-L2-HISTORICAL-VERIFICATION-20261114.md).
- The independent newer [QA-First](https://github.com/merapplications-sketch/Talabat-v3/blob/0ab523782ee1bf6f69e2e3be7ec6e96394d9ce6a/docs/qa-first-20261113/MASTER-QA-CONSOLIDATED-20261113.md) measures a distinct scope: **0/51 current-source integrated functional E2E**, **0/21 Admin runtime**, **0/6 G1 fully accepted**, not 72 test failures. Never combine the denominators or treat historical fixes as active deployment proof.

## Verified official reference documents (use stable releases)
- [OWASP ASVS v5.0.0](https://asvs.owasp.org/) — baseline security controls for web apps/APIs. **Level 2** is the team's previously selected assurance target; map controls by versioned IDs, applicability and evidence.
- [OWASP WSTG stable 4.2](https://wstg.owasp.org/) — executable test methodology for web sessions, access control, inputs, configuration; WSTG 5.0 is still development, not the stable baseline.
- [OWASP API Security Top 10 (2023)](https://owasp.org/projects/api-security-project) — especially object/function-level authorization, broken authentication, resource consumption and business-flow abuse.
- [OWASP Mobile MASVS + MASTG](https://mas.owasp.org/) — source and final Android/iOS mobile app storage, network, session, platform, resilient permissions/privacy, with mobile-specific device tests.
- [ZAP Automation Framework](https://www.zaproxy.org/docs/automate/automation-framework/) — an **optional** scanner orchestrator for a fully isolated synthetic test target, not a prerequisite or proof of compliance. Baseline passive scan still spiders the target and generates real requests. Active/API scans send probing traffic and may mutate state: **never run them against TALABOT production**, account, financial, Cloudflare, Supabase, or public URL without a separately approved isolated and bounded target.

## Owner pilot-first execution map (scoped priorities, NOT newly accepted test results)

| Test group | Current source concern/controlling gate | Required synthetic proof |
|---|---|---|
| SEC-01 Account/Auth | G1-D RLS/Auth/RBAC blocked; staff MFA | Login/session expiry/revocation, staff authorization, unauthenticated actions denied server-side, sensitive roles separately |
| SEC-02 Tenant isolation / BOLA | customer, merchant, driver, admin data in Supabase | Different authorized synthetic identities; customer A cannot see B order/location; merchant A cannot access B; driver only his assigned offer; admin permission boundaries |
| SEC-03 Privileged RPCs | `dispatch_tick`, `driver_accept`, `deliver_order`, privileges | Check every call's session/role/tenant/argument authorization; no privilege by calling RPC URL directly; misuse handled safely |
| SEC-04 SQL/transaction | duplicate checkout/driver accept/deliver; existing F-02/F-04 | Concurrent double-click, timed-out ACK, retry after COMMIT; **exactly one business/financial effect**, no accepted order disappears |
| SEC-05 Client input / price | menu variants/quantity/discount/financial rules | Server rejects edited quantity, negative/invalid price, stale price, unauthorized discounts without changing approved CASH-01/Q09–17 |
| SEC-06 Browser/web | customer, merchant, TailAdmin | Content Security Policy, XSS/injection prevention, safe output, clickjacking, CORS, cookie/session handling, redirects and download safety; no scanner PASS asserted |
| SEC-07 Data/Storage/privacy | proof image, signed URL, staff records | Cross-tenant private file read denied, TTL/revocation, deletion/access controls, no secrets or PII in public errors/logs, real file/DB restore under controlled conditions |
| SEC-08 API abuse/capacity | rate limits, credential stuffing, repeated GPS and realtime | Controlled bounded synthetic abuse; protections at actual Supabase entry point, not assumed from Cloudflare frontend WAF; no crash or legitimate users indefinitely blocked |
| SEC-09 Live location | owner requires tracking customer/driver/authorized admin | Location only for active permitted order, timestamp freshness, reduced precision when needed, no historical exposure, denial/reconnect/background behavior and user consent |
| SEC-10 Delivery/customer rights | leave-at-door, refunds, support messages | Full status machine, protected delivery evidence, no refund before cash actually received per RETURN-01, no duplicate support or disclosure |
| SEC-11 Dependency/build/release | public GitHub repos, signed packages, old vs deployed SHA | Scan dependency + leaked secrets and third-party bundles, CI exact SHA, harden artifacts, rollback, preserve historical secrets from publication |
| SEC-12 Store distribution | Android Google Play, iOS App Store future | MASVS/MASTG app build, local storage, network TLS, debug instrumentation, OS background GPS and push permissions, app integrity; **not** closed by Safari testing |

### Security evidence required per case
`requirement_id (e.g. v5.0.0-...)` → severity & role → original branch/commit → current branch/commit + environment & deployed writer → synthetic identity/fixture → steps (private; redacted summary public) → expected/actual → HTTP/DB/browser trace → result PASS/FAIL/BLOCKED/NOT_APPLICABLE → independent reviewer → minimal remediation & re-test SHA.

### Safety boundaries
- **Current master and active Stage issues govern dispatch**. Do not distract Stage20 publisher/OPS or any successor. A documentation file is not a newly dispatched security scan.
- All dynamic/active testing requires **isolated, synthetic, explicitly approved** app+DB+Auth with no real orders, money, storage, messages, production URLs/credentials or public attack traffic. Stop if isolation is uncertain.
- No security scans will be run solely because this plan exists. Do not run vulnerability probes on protected production endpoints or publish scan outputs containing secrets, PII, exploitable route details or high-privilege SQL on currently PUBLIC GitHub repos.
- Preserve **ASVS Level 2 owner-approved baseline** and all financial/design/security locks, then extend with WSTG/API/MASVS for relevant vectors. OWASP is a **security quality gate**, not a performance, UX, crash-resilience, Playwright E2E, or backup/restore substitute.
- An automated ZAP warning may be false positive or low risk; independent reviewer validates applicability and remediation. **OWASP ASVS Level 2 conformity cannot be certified by one scanner.**

## Planned handoff after the already assigned operations work
1. Technical/security consultant **read-only** cross-checks existence of the historical private matrix (without publishing it), maps each L2 requirement to live owner-approved source, active RPC and safe synthetic environment.
2. Independent QA executes uncovered controls progressively with **real traces**, only after isolated test authorization; records only narrowly scoped evidence and misses.
3. Programmer fixes reproduced failures in a dedicated isolated branch; financial/RLS/source lock decisions need explicit bounded authorization; reviewer re-tests same SHA.
4. Manager reconciles ASVS matrix and active **G1-D** with all release gates and gives the owner a concise GO/NO-GO; no autonomous rollout.

**Last project operations status at creation:** [Master #26](https://github.com/merapplications-sketch/Talabat-v3/issues/26) reports [Stage20 #46](https://github.com/merapplications-sketch/Talabat-v3/issues/46) JWT-authorized Pages Direct Upload **BLOCKED** and no new public Safari preview. Recheck comments after this timestamp; it is a deployment tooling block, **not an ASVS result**.
