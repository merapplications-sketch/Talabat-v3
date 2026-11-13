# TALABOT — STAGE 7 / Independent Offline C-01 Runner Safety Review

**Date:** 2026-11-13 — Asia/Dushanbe  
**Role:** Publisher / Operations — independent read-only safety review  
**Authority:** [Stage 7 Issue #33](https://github.com/merapplications-sketch/Talabat-v3/issues/33) | [MASTER #26](https://github.com/merapplications-sketch/Talabat-v3/issues/26)  
**Input:** [Stage 6 Programmer Report](https://github.com/merapplications-sketch/Talabat-v3/blob/1075bcb2ffa3a8eb77c64c07b63ded404b40e3d7/docs/qa-first-20261113/STAGE6-ISOLATED-E2E-READINESS-REPORT.md) at commit 1075bcb2ffa3a8eb77c64c07b63ded404b40e3d7.  
**Application source pin:** 1cb85361d698d5da787d927a4c9ae7bd213c68c1, branch docs/phase1-operational-coordination-20261111.  
**Decision:** **PROPOSED C-01 ENVIRONMENT READINESS = NO-GO / EXECUTION NOT AUTHORIZED / QA NO-GO / RELEASE NO-GO / PHASE2 NO-GO.**

This is a bounded independent assessment of **one future synthetic C-01 customer login and local profile E2E test only**. No workflow, test, container, dependency installation, VM, cloud resource, database query, account creation or service has been executed. No source, configuration, application, CI or deployment change was made. No other 50 E2E cases or Admin UI tests were re-audited.

## 1 — Freshness and evidence provenance

| Item checked | Latest directly verified reference | Meaning |
|---|---|---|
| PM source branch | HEAD **1cb85361d698d5da787d927a4c9ae7bd213c68c1** | Exact source for this review, not presumed live |
| Stage 6 dedicated docs branch | HEAD **1075bcb2ffa3a8eb77c64c07b63ded404b40e3d7** | Current report input, not an executable release |
| Primary default main | HEAD **148cfae50000e983af2221a96057c507edac6d69** | Different source from PM reference |
| Source workflow | [pilot-isolated.yml at 1cb85361](https://github.com/merapplications-sketch/Talabat-v3/blob/1cb85361d698d5da787d927a4c9ae7bd213c68c1/.github/workflows/pilot-isolated.yml) | Exists on pinned nondefault source branch |
| Workflow on default main | Direct GitHub contents read **HTTP 404 / NOT_FOUND** | Not available at default-branch path; do not dispatch |
| Proposed Stage 7 review branch | review/qa-stage7-ops-isolation-20261113 based on PM source | Documentation-only target, independent of Stage 6 |

Local uncommitted/unpushed work from another person's environment cannot be verified by GitHub. This audit reads repository source; it **does not** independently confirm any running fully isolated VM, Docker installation, already pulled images, network firewall policy or actual C-01 credentials. Stage 6 described these as unavailable in its execution context; the current Stage 7 decision is **BLOCKED until independently evidenced**, not a claim that a VM cannot be built.

## 2 — Independent inspection of exactly the relevant existing assets

| File / pinned blob SHA | What it actually does | C-01 reuse verdict |
|---|---|---|
| [tests/pilot/lab.py](https://github.com/merapplications-sketch/Talabat-v3/blob/1cb85361d698d5da787d927a4c9ae7bd213c68c1/tests/pilot/lab.py) — **0a4a330621a261c31c7bae243dd4303a297b0631** | Lines 29–32 connect PostgreSQL on 127.0.0.1:5432, lines 53–75 REST/GoTrue on 127.0.0.1:3000/9999. Lines 115–121 generate local-only secrets. Lines 124–175 initialize schema and **eight** synthetic users (admin/accountant/merchant/customer/outsider/driver1/driver2/joiner), alter local roles and seed a store/item. Integration at lines 221 onward includes orders, finance, races and roles. | **PARTIAL: reusable Auth/DB routines but existing setup and integration suite exceed C-01**. Not a one-case selector; account initialization and GoTrue sessions cause **local** writes. |
| [tests/pilot/compose.yml](https://github.com/merapplications-sketch/Talabat-v3/blob/1cb85361d698d5da787d927a4c9ae7bd213c68c1/tests/pilot/compose.yml) — **db7a3053fff1418783fc2833657ab2f9bde3af6d** | PostgreSQL, GoTrue, PostgREST plus optional Storage/Mailpit. Host port mappings 127.0.0.1 only; **no internal Compose network or egress deny** is configured. | **SOURCE VERIFIED; EGRESS NOT SAFE BY ITSELF**. Loopback publishing controls ingress, not all outbound traffic from containers. |
| [tests/fixture.js](https://github.com/merapplications-sketch/Talabat-v3/blob/1cb85361d698d5da787d927a4c9ae7bd213c68c1/tests/fixture.js) — **dce8d7b20192a652af0c85300ab2a6ffe79e51e2** | Installs front-end demo state, stubs browser fetch and synthetic client datasets. | **NOT AUTHENTICATED E2E**: mocked session/Profile/RPC cannot prove GoTrue or PostgREST role isolation. Browser fetch interception does not isolate other processes. |
| [tools/qa_all.py](https://github.com/merapplications-sketch/Talabat-v3/blob/1cb85361d698d5da787d927a4c9ae7bd213c68c1/tools/qa_all.py) — **19a9643f3643364b48f8fa8ccd2dd5bafd22c6c4** | Visual multi-screen fixtures through file:// and Playwright route handlers, default 360/390/430 + offline/empty states. | **UI mock smoke only**, not appropriate to record C-01 Auth/profile PASS. Its browser route filter is not whole-VM egress protection. |
| [pilot-isolated.yml](https://github.com/merapplications-sketch/Talabat-v3/blob/1cb85361d698d5da787d927a4c9ae7bd213c68c1/.github/workflows/pilot-isolated.yml) — **6f32bb7b2ce80304d139ba75fb5c926bf73e1e36** | Runs ubuntu-24.04; downloads exact Git ref, pip dependency packages, Docker images; browser suites can npm ci and Playwright install. Has workflow_dispatch choices and broad journey/integration, with destructive local volume teardown. | **NOT viable for approved C-01 as-is**: workflow absent on main; broad suite; outbound build/download traffic; no sealed runner proof. No dispatch/CI changes allowed. |
| [tests/pilot/gateway.py](https://github.com/merapplications-sketch/Talabat-v3/blob/1cb85361d698d5da787d927a4c9ae7bd213c68c1/tests/pilot/gateway.py) — **199e3592c27c9280b02c3b787b4f54ced39111d6** | An **existing local bridge**: /auth/v1 maps to 127.0.0.1:9999, /rest/v1 to 127.0.0.1:3000. Rewrites HTML source project origin and JS SB_URL/SB_KEY for local testing; binds HTTP server to 127.0.0.1:8080. | **Useful after independent validation** of exact-source substitutions and deny rules; is not a network firewall, doesn't implement a production-compatible Realtime/Storage service. |
| [tests/pilot/package.json](https://github.com/merapplications-sketch/Talabat-v3/blob/1cb85361d698d5da787d927a4c9ae7bd213c68c1/tests/pilot/package.json) — **a476d952be4cec7972766cfd2d58b7a896d8bb70**; [lockfile](https://github.com/merapplications-sketch/Talabat-v3/blob/1cb85361d698d5da787d927a4c9ae7bd213c68c1/tests/pilot/package-lock.json) — **cfc0594cacc358abe74bf5726e86acbdbdcb4b27** | Existing dependencies include Playwright 1.56.1 and Supabase JS 2.117.2. | Version declarations only; actual browser binaries and downloaded artifact digests must be attested before any run. |
| [talabat-core.js](https://github.com/merapplications-sketch/Talabat-v3/blob/1cb85361d698d5da787d927a4c9ae7bd213c68c1/talabat-core.js) — **f639bec1d23a812866e06eb1110940c77563387c**; [customer.html](https://github.com/merapplications-sketch/Talabat-v3/blob/1cb85361d698d5da787d927a4c9ae7bd213c68c1/customer.html) — **9bc335f52ad58d7feab12ad8a2214bde9ab32330** | The original core **contains a production Supabase URL** (L4), and customer HTML CSP permits it (L4). Actual login calls signInWithPassword (core L743–780); successful enter reads profiles by authenticated user ID (L822–849); entering then refreshes additional data/starts client polling. | **Potential egress target, not evidence of a production call in this review**. Local bridge rewrite and restrictive C-01 request inspection must both be checked. Do not open raw HTML against production. |

**Critical independent difference from Stage 6:** the existing integrated **journey** is not a C-01 single-case runner. Even running lab.py with a skip filter would not prevent prepare_app from creating eight identities, modifying local roles and inserting merchant/catalog fixture data. Its integration function calls multiple scenarios, including local order creation and finance. A future explicit **test-only selector/minimal fixture** or separately approved isolated probe is mandatory; no app-product code change is suggested or authorized today.

## 3 — Current isolation risks and precise dispositions

| ID / risk | Observed proof | Severity as test-safety gate | Disposition |
|---|---|---|---|
| ISO-01: containers may reach the Internet | compose.yml has published loopback ports but no networks: internal or route/firewall policy | **P1 / hard blocker** | **BLOCKED** until whole-VM + container egress deny is proven. [Docker Compose networking](https://docs.docker.com/compose/how-tos/networking/) and [bridge NAT](https://docs.docker.com/engine/network/drivers/bridge/) explain why default bridge usually has outbound masquerading. |
| ISO-02: client may contact real API or third-party assets | Core includes the live Supabase origin; HTML CSP permits that origin and HTTPS images. gateway.py rewrites specific strings only. | **P1 / hard blocker** | **BLOCKED** until source URL/static origin scan + runtime request allowlist + OS network deny are independently evidenced. |
| ISO-03: broad fixture produces out-of-scope local effects | lab.py prepare_app seeds eight accounts, store and product; integration executes unrelated tests. | **P1 / scope blocker** | **BLOCKED**: do not invoke journey or integration for C-01. A separately authorized test-only C-01 selector/minimal fixture is needed. |
| ISO-04: hosted Actions are not air-gapped | workflow default main lookup returned 404; workflow has network downloads and broader suites, no no-egress policy | **P1 / hard blocker** | **BLOCKED**: no workflow dispatch, push trigger, copy-to-main, settings changes or rerun. |
| ISO-05: unpinned runtime binaries | PostgreSQL image uses immutable digest; GoTrue, PostgREST, Storage and Mailpit use version tags only. pip/npm versions alone do not lock OCI digest/browser binary. | **P2 / provenance blocker** | **BLOCKED**: pre-approved OCI and offline artifact digests, supply-chain manifest and signed checksum matching needed. |
| ISO-06: C-01 browser startup triggers ancillary reads/RPC | core enter fetches profile, then refresh() makes additional REST/RPC calls; some RPCs use POST even when logically read-only. | **P1 / exact scope blocker** | **BLOCKED**: whitelist reviewed calls by **function and effects**, not HTTP method alone. Stop on unapproved RPC, financial transaction or mutation. |
| ISO-07: no independently inspected runnable sealed VM | Stage 6 runner was not provisioned; this audit only inspected source; no OS interfaces/iptables/nftables/Docker network or process logs available. | **P1 / evidence blocker** | **UNTESTED**, not asserted safe or unsafe at runtime; OPS/SEC must supply independent signed attestation. |

**No production breach, live connection, live defect, or test execution was observed during Stage 7.** These are gaps in the **test safety envelope**, not proof that the application made an unauthorized live request.

## 4 — Why GitHub Actions is not the recommended first runner

- The reference workflow is available at PM source, but **not** at current default main (direct read-only GET = 404). GitHub documents that **workflow_dispatch requires the workflow file on the default branch**: [GitHub event reference](https://docs.github.com/en/actions/reference/workflows-and-actions/events-that-trigger-workflows#workflow_dispatch).
- Workflow push trigger is restricted to candidate/pilot-readiness-20261105, while the job explicitly checks out github.sha and not necessarily the audited 1cb85361 reference. It is not an exact-source C-01 declaration.
- The existing **journey** selection invokes lab.py integration, not a single valid/invalid customer-profile test. Executing it would violate the one-case scope.
- The workflow fetches source/packages/images using public network infrastructure. Neither CSP nor Playwright route nor runner ubuntu-24.04 proves an Internet-free host and containers. Pre-test network fetching is a separate activity that also requires appropriate authorization.
- **Decision:** current GHA is **NO-GO FOR C-01**. Do not move, modify, dispatch, or create workflow. An **offline, disposable non-GHA VM runner** is the least intrusive future candidate. This is a plan only, not a ready VM or authorization to create one.

## 5 — Proposed offline VM security architecture: hard fail-closed gates

The following **must be proven before execution**, not assumed:

| Gate / owner | Required control and objective evidence | Status at Stage 7 |
|---|---|---|
| **N0 — OPS/DEV provenance** | Source bundle from **exact 1cb85361 commit**, customer.html/core/vendor/assets plus lab/gateway/SQL/bootstrap/test-only runner, with complete file SHA256 and Git blob/commit, no merged branch; signed artifact manifest. Supply pre-reviewed offline images + browser binaries, Python/Node wheels/packages with immutable SHA256. PostgreSQL image already pinned by digest in Compose; resolve and lock digests for GoTrue v2.197.0, PostgREST v14.18, and browser; Storage/Mailpit not part of baseline C-01. | **PARTIAL source / execution assets BLOCKED** |
| **N1 — OPS/SEC physical/virtual network cut** | **Disposable VM with no external virtual NIC or NAT/host-only uplink**, no external default route IPv4/IPv6, no VPN, DNS forwarder, cloud metadata interface, proxy, daemon registry mirror, mount tunnel or forwarded host service. Transport source and dependencies via approved read-only/offline image before VM seal; no package/image download inside. Independent attestations of VM interface/route topology and hypervisor connectivity. | **BLOCKED** |
| **N2 — OPS/SEC host + Docker policy** | Outside-lab outbound denied by **OS network firewall** for all processes and all containers (OUTPUT/FORWARD and IPv4/IPv6), audit deny events and counters; Docker daemon cannot pull images and never attaches a second outward network. Container network dedicated to disposable VM. Optional **internal-only Compose override** evaluated **in a future authorized VM** if loopback host access remains functional; no source Compose edit during Stage 7. Docker socket is not mounted into test containers. | **BLOCKED** |
| **N3 — QA/SEC browser and API allowlist** | Isolated browser origin only 127.0.0.1:8080; bridge permitted local Auth :9999 and PostgREST :3000; services connect only to lab DB/service names. Inspect full request, XHR/fetch, WebSocket, image/font/CDN, DNS, subframes, redirects, service workers and worker subprocesses. Browser requests to anything else abort and **STOP run immediately**, with sanitized target/event evidence. Browser hooks are defense-in-depth, not boundary enforcement. | **BLOCKED** |
| **N4 — AUTH/DB data identity** | New disposable PostgreSQL + GoTrue/REST only, using newly generated **lab-only** tokens, test hostnames under synthetic.invalid, two synthetic customer accounts (A/B), their matching two profile rows with customer role. No production account/key, imported row, order, protected #1/#2/#3 or #3 settlement. No real SMTP, SMS, payment, Storage or settlement connection. | **BLOCKED** |
| **N5 — OPS/QA negative control** | With C-01 NOT yet started, independent reviewer checks no outbound NIC, default routes or DNS forwarder, verifies firewall deny through a **synthetic predeclared dummy destination** (not real production domain/IP), observes blocked event within VM, and checks authorized local HTTP/SQL paths still work. If the dummy packet can leave, **fail and do not start**. Tag preflight-only synthetic deny separately; any real unplanned non-lab attempt after opening test window triggers STOP. | **NOT EXECUTED** |
| **N6 — QA/API backend scope gate** | Monitor/deny any unexpected REST/RPC mutation and read actual network traces. Starting the customer UI can call additional read-like RPCs; only individually reviewed **non-writing** local functions may be allowed. Unknown or side-effecting RPC: STOP, no broad fixture to bypass. Confirm GoTrue/Profile row isolation and local table write boundaries. | **BLOCKED** |
| **N7 — OPS evidence + teardown** | Store only sanitized logs and summary in private QA artifact: VM/OS and image IDs; source SHA; effective deny config and counters before/during/after; DNS/flows/process tree; scope; Auth/REST role trace; table counts; results; VM and volume removal proof. Do not upload .runtime.json, JWT, passwords or raw user rows. No external network upload from sealed VM; approved offline export after it stops only. | **BLOCKED** |

**Whole-process requirement:** Internet prohibition covers **browser, Playwright test process, Python lab and local gateway, Docker daemon, GoTrue, PostgREST, PostgreSQL, any helper worker/scheduler, DNS, storage daemon if used, build/install processes and subprocesses**. Restricting only browser traffic or only 127.0.0.1 port bindings is insufficient. External response attempts are not a test signal to retry; they are **an immediate stop**, even when OS firewall blocks transmission.

**Scope/compatibility caveat:** the current gateway rewrites the fixed core origin, but client CSS/HTML may include remote references, and browser login leads to additional reads/polling/realtime attempts. A current-source **deny-by-default request inventory must pass without unintended requests**; if not, mark C-01 **BLOCKED** and request a separately authorized test-only adapter. Do not weaken network protection or use a production endpoint to make the page work.

## 6 — Smallest authorization-ready C-01 work order — future only

### C-01 boundary

Test **only** opening actual pinned customer.html, one **invalid password**, one **valid customer account** login, reading that account's profile through isolated PostgREST, and a **second synthetic customer** to prove profile row/role isolation. This is one bounded scenario with four assertions, not a rerun of C-02/C-03/C-17 and not checkout, payments, orders, profile changes, admin access, GPS, notifications or all-app navigation.

**Expected:**
- Invalid credentials for Customer A: GoTrue 400/401, no session and no access to personal profile; UI shows appropriate rejection without entering customer account.
- Valid Customer A: GoTrue returns synthetic session, application user ID matches local auth.users ID, profile read yields **exactly A** and role customer; profile UI displays the expected synthetic identity without a role mismatch.
- Customer B: own valid login and profile B; a query by A token for B profile yields no B row (empty result/denied, according to local RLS contract); untrusted user_metadata indicating admin cannot elevate server profile role.
- All traffic stays on isolated endpoints, **zero requests successfully sent outside the lab and zero unintended non-lab attempts**; no order, wallet, settlement or financial write; Auth session changes and new synthetic auth.users/profiles are **local VM writes only**.

**Source trace:** [Login input/submit in core L743–780](https://github.com/merapplications-sketch/Talabat-v3/blob/1cb85361d698d5da787d927a4c9ae7bd213c68c1/talabat-core.js#L743-L780); [profile query/role gate in L822–849](https://github.com/merapplications-sketch/Talabat-v3/blob/1cb85361d698d5da787d927a4c9ae7bd213c68c1/talabat-core.js#L822-L849); [original lab synthetic registration L99–112](https://github.com/merapplications-sketch/Talabat-v3/blob/1cb85361d698d5da787d927a4c9ae7bd213c68c1/tests/pilot/lab.py#L99-L112).

### Permitted future execution sequence (each step **requires prior explicit owner authorization**)

1. **Written task lock** — PM submits to owner the exact SHA, single C-01 boundary, no-prod/no-cloud/no-finance, disposable VM identity and operator, allowed local writes, budget zero unless separately approved. No authority from this report.
2. **Supply chain** — DEV/OPS prepare immutable offline source/assets package with verified SHA and GoTrue/PostgREST/PostgreSQL/Playwright packages/images; dedicated QA tester and security reviewer sign manifest. **No network fetching in test VM**.
3. **VM preflight** — OPS/Security instantiate an expendable no-outbound-NIC VM and sign whole-host/container egress policy, check DNS/IPv4/IPv6 routes and denied synthetic sink; **NO-GO if any control cannot be demonstrated**.
4. **Local bootstrap only** — In that approved VM, create local ephemeral PostgreSQL/GoTrue/PostgREST through vetted existing script components. The current prepare_env and prepare_db are usable concepts; **prepare_app AS-IS MUST NOT RUN IN THE NARROW C-01** because it seeds eight personas, extra privileges and store/menu data and applies unrelated candidate financial patches. A separate **authorized test-only minimal bootstrap/selector** must initialize schema, GoTrue migrations and exactly A/B accounts and profiles. Do not edit application/approved financial logic; do not change hosted database. If page cannot boot without a small synthetic read-only catalog, stop and obtain an explicit scope amendment, not automatic extra seeding.
5. **Local bridge and browser** — Run reviewed original gateway.py on VM loopback 8080 and use the browser against only /customer.html; verify rewritten HTML CSP and core SB_URL/SB_KEY point to the **new lab-only** origins, and deny everything else. Do not assume a displayed version title verifies SHA.
6. **C-01 negative then positive** — new clean browser context, enter A synthetic email with **wrong** password, confirm rejection and no profile access; separate clean context, enter correct credentials, confirm profile loaded with A ID/role; use B separate session for own profile and cross-account rejection. Observe local GoTrue/Auth/REST traces and effective DB role/RLS; record expected/actual and result per subcheck.
7. **No-side-effect oracle** — snapshots before and after login of Auth sessions/profiles (only expected local Auth writes), orders/order_items, wallet_entries, finance/settlement tables (all **unchanged**), DB origin/run identifier. Any unexpected mutation/identity/RPC/role escalations → STOP and FAIL/BLOCKED, without retry on production.
8. **Evidence and shutdown** — capture concise sanitized result manifest and egress deny logs; do not export synthetic credentials or live snapshots; stop/erase disposable processes, VM/volumes, ephemeral files and log secrets. Independent reviewer verifies VM disposal, no production write and provenance before the PM may label C-01 PASS. Even a PASS is **1/51 only**, not complete G1/QA/release acceptance.

### Case evidence record to be required

Case ID **C-01**; test SHA and complete asset/image SHA256 manifest; test VM ID (non-sensitive) + offline attestations; test source/build origin; two synthetic role IDs represented by pseudonyms only; invalid-login HTTP and UI result; valid-login outcome and profile UUID equality; B cross-profile denied/empty; effective PostgREST/RLS role; expected/actual and timestamps; HTTP/DB query summaries redacted; zero unintended DB financial/order rows; zero successful egress and zero unplanned attempted egress; firewall/DNS logs; cleanup receipt; tester and independent reviewer sign-off. Screenshots of synthetic data only.

**No current C-01 result exists**: PASS=0, executed=0, BLOCKED=1 due to runner security and test-only selector prerequisites. The prior global functional tally stays **0/51**.

## 7 — Resources, owners and explicit owner approvals

| Resource/action | Responsible person or discipline | Owner authorization required before action? | Existing / missing |
|---|---|---|---|
| Copy or checkout exact public Git source into new runner / create immutable offline artifact | DEV + OPS | **YES** | Git SHA and sources exist; executable offline bundle not evidenced |
| Build/source/OCI/browser dependency hash verification and preloading | DEV + supply-chain/SEC | **YES** | PostgreSQL digest pinned; other OCI/browser artifacts unpinned/unavailable |
| Provision sealed, disposable VM with no network NIC; install dependencies **offline** and configure firewall/logging | OPS + SECURITY | **YES** | No actual VM or sealed policy attested |
| Create/destroy local PostgreSQL, GoTrue, PostgREST and local test HTTP bridge | OPS + API/DB | **YES** | Existing scripts, no current ready runtime |
| Minimal C-01-only fixture with two fake Auth users/profiles; allowed local DB/GoTrue writes | AUTH + API/DB + DEV | **YES**, including any test-harness-only selection/adaptation | Existing prepare_app seeds extra actors and data; minimal selector missing |
| Run one C-01 browser/Auth/Profile test and collect sanitized traces | QA + SEC observer | **YES** | Browser driver examples exist, exact C-01 probe/attestation not executed |
| Transfer synthetic evidence out of sealed VM after stop; delete VM and ephemeral files | OPS + QA | **YES as part of same bounded approved work order** | Plan only |
| Modify product, actual Supabase project/Cloudflare, host keys/permissions, paid infrastructure, GHA workflow, CI dispatch, deploy/main/merge | Not part of Stage 7 | **PROHIBITED**, would require independent explicit scope and approval | No change authorized or proposed |

The owner should **not** be asked for real secrets, credentials, private financial data, project production access or manual cloud changes. Operators supply non-secret sanitized attestation and synthetic fixture artifacts.

## 8 — Emergency STOP conditions and cleanup boundary

Abort without retry, account edits, cloud side effects or workaround when **any** of the following occurs: network interface/default route to external host appears; unexpected IPv4/IPv6/DNS/HTTP/WebSocket attempt or allowed egress; source/build/image digest mismatch; production URL/key or real identity appears in the effective runtime; GoTrue/REST points outside VM; unknown RPC/permission path; customer B profile exposure; an unexpected order/payment/finance mutation (even local); unapproved SMTP/SMS/push/Storage; credentials leak to log; container connects to unauthorized Docker network or host socket; fixture scope extends beyond two customers; firewall/monitoring goes down; runtime cannot prove origin or rollback/cleanup. A negative control failing to block an explicitly dummy target stops the run **before** C-01.

STOP procedure for the **future authorized run**: isolate and terminate only disposable test processes/VM using the predeclared runbook; retain minimal redacted security incident metadata through an approved offline channel; prevent any replay; escalate to OPS/SEC and PM; leave production untouched; classify C-01 FAIL or BLOCKED with reason, do not self-repair in test.

## 9 — Decision and handoff

**Independent verdict: C-01 ENVIRONMENT READINESS = NO-GO.**

**What is proved now:** pinned source artifacts and test scripts exist; source registration uses synthetic.invalid; Compose loopback bindings and local gateway present; POST login and profile lookup call sites exist; workflow is missing from main; GHA job is broader than C-01 and depends on network downloads; no current egress proof or ready disposable runner.

**What is NOT proved:** zero actual egress from a prepared full runner, complete offline image/browser supply chain, minimal fixture selector, correctly versioned local GoTrue/PostgREST/DB, actual C-01 UI/Auth/profile trace, cross-account isolation, negative-control denies and cleanup.

**Minimum reopening condition:** a signed **N0–N7 preflight manifest** for one offline disposable VM; independently verified no-egress (including host and all containers); signed minimal C-01 fixture/test-only harness scope; explicit written approval from owner for *that exact temporary environment and local-only operations*. After that, QA may run **one** case only under separate implementation authorization; OPS/SEC then independently verifies its evidence. PM consolidates; no automatic expansion to the remaining 50 cases.

**Global state remains:** original 51 current-source functional E2E **0/51**, Admin current-source E2E **0/21**, G1-A/B/C/E/F PARTIAL and G1-D BLOCKED; **QA NO-GO / RELEASE NO-GO / PHASE2 NO-GO**. Historical accepted PRICE/RATINGS/TIP/106/107, source35 and Q09–Q17 including Q14 stay intact. No earlier acceptance was rerun or changed.

### GitHub references and delivery scope

- [Issue #33 — OPS isolation gate](https://github.com/merapplications-sketch/Talabat-v3/issues/33)
- [Issue #26 — MASTER](https://github.com/merapplications-sketch/Talabat-v3/issues/26)
- [Stage 6 pinned evidence](https://github.com/merapplications-sketch/Talabat-v3/blob/1075bcb2ffa3a8eb77c64c07b63ded404b40e3d7/docs/qa-first-20261113/STAGE6-ISOLATED-E2E-READINESS-REPORT.md)
- [Source PM continuity](https://github.com/merapplications-sketch/Talabat-v3/blob/1cb85361d698d5da787d927a4c9ae7bd213c68c1/docs/continuity/PHASE1-CURRENT.md)
- [Docker Compose default/external bridge vs internal networks](https://docs.docker.com/compose/how-tos/networking/)
- [GitHub workflow_dispatch default-branch requirement](https://docs.github.com/en/actions/reference/workflows-and-actions/events-that-trigger-workflows#workflow_dispatch)

**Git delivery:** one new Markdown report only, review/qa-stage7-ops-isolation-20261113 based on unchanged PM source 1cb85361; no executable/SQL/CI/design code modifications, no test runner created, no CI run, no merge and no deployment.
