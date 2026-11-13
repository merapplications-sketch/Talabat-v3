# TALABOT — STAGE 9 / OPS Controlled Offline Preparation — Actual Evidence

**Date:** 2026-11-13 — Asia/Dushanbe.  
**Mandate:** [Issue #35](https://github.com/merapplications-sketch/Talabat-v3/issues/35); [owner approval #34](https://github.com/merapplications-sketch/Talabat-v3/issues/34#issuecomment-6858292284); [MASTER #26](https://github.com/merapplications-sketch/Talabat-v3/issues/26).  
**Earlier safety review:** [Stage 7 at 33997762](https://github.com/merapplications-sketch/Talabat-v3/blob/339977623709bf0fdab12a85ffb2c404f28478a6/docs/qa-first-20261113/STAGE7-INDEPENDENT-OFFLINE-C01-ENVIRONMENT-SAFETY-REVIEW.md).  
**Immutable application source:** **1cb85361d698d5da787d927a4c9ae7bd213c68c1** (docs/phase1-operational-coordination-20261111).

## 1. Executive conclusion

**Result: PARTIAL PREPARATION — HARD STOP / ENVIRONMENT NO-GO / C-01 NOT RUN.**

Actually performed: verified management authorization and latest PM HEAD, read the relevant source file Git blobs, inventoried local host/virtualization/network capabilities, created a temporary permission-restricted preparation directory, assembled a reference/dependency manifest, executed an approved negative control **only inside a short-lived isolated user+network namespace** against synthetic documentation-only IPv4/IPv6 addresses, recorded inability to resolve a .invalid domain there, verified local loopback connectivity, and retained sanitized JSON evidence with SHA256.

**Not performed or not achieved:** NO disposable VM, NO offline source checkout/archive, NO locally materialized Docker images/browser/GoTrue/PostgREST/PostgreSQL, NO complete VM firewall, NO Docker network deny or deny counters, NO actual authenticated browser/DB/REST services, NO two-customer fixture, NO C-01, NO journey, NO GitHub Actions. A user+network namespace is **not** the authorized full VM; the observed control may NOT be promoted to full isolation acceptance.

**Hard blocking resources:** Available execution is a restricted Linux tools container, with **no Docker/Podman/QEMU/libvirt/KVM, no PostgreSQL server, no nft/iptables/ip6tables**, no host CAP_SYS_ADMIN/CAP_NET_ADMIN and no /dev/kvm. The preparation host has an IPv4 default route and proxy variable names configured, so it is **not itself a sealed offline host**. Direct unshare --net was denied EPERM; short-lived unshare --user --map-root-user --net worked, but cannot replace the approved VM or prove Docker/process-wide policies. Attempted public GitHub archive retrieval during pre-seal preparation failed because codeload.github.com could not resolve; source bytes and SHA256 were not staged. No new paid/cloud resources were created or requested.

**Safety disposition:** **N0–N7: 0/8 fully passed.** This report is an honest hard-stop handoff, not a runnable environment. **QA NO-GO / RELEASE NO-GO / PHASE2 NO-GO.** Stage 8 approval permits preparation but does not certify its completion or permit C-01 before independent security PASS.

## 2. Exact source and provenance checked

GitHub repository branch docs/phase1-operational-coordination-20261111 verified HEAD **1cb85361d698d5da787d927a4c9ae7bd213c68c1**. No later code or default main was substituted. The following Git blob SHA-1 values were directly re-checked through read-only GitHub contents for this source pin. **These identify Git source objects, not local byte copies or SHA256 checks.**

| Pinned GitHub file | Git blob SHA-1 | Actual local source copy |
|---|---|---|
| [customer.html](https://github.com/merapplications-sketch/Talabat-v3/blob/1cb85361d698d5da787d927a4c9ae7bd213c68c1/customer.html) | 9bc335f52ad58d7feab12ad8a2214bde9ab32330 | NOT MATERIALIZED |
| [talabat-core.js](https://github.com/merapplications-sketch/Talabat-v3/blob/1cb85361d698d5da787d927a4c9ae7bd213c68c1/talabat-core.js) | f639bec1d23a812866e06eb1110940c77563387c | NOT MATERIALIZED |
| [assets/vendor/supabase-2.117.2.js](https://github.com/merapplications-sketch/Talabat-v3/blob/1cb85361d698d5da787d927a4c9ae7bd213c68c1/assets/vendor/supabase-2.117.2.js) | b51e7b9e308e2162d873b84d412a9d37c398d3e0 | NOT MATERIALIZED |
| [tests/pilot/lab.py](https://github.com/merapplications-sketch/Talabat-v3/blob/1cb85361d698d5da787d927a4c9ae7bd213c68c1/tests/pilot/lab.py) | 0a4a330621a261c31c7bae243dd4303a297b0631 | NOT MATERIALIZED |
| [tests/pilot/compose.yml](https://github.com/merapplications-sketch/Talabat-v3/blob/1cb85361d698d5da787d927a4c9ae7bd213c68c1/tests/pilot/compose.yml) | db7a3053fff1418783fc2833657ab2f9bde3af6d | NOT MATERIALIZED |
| [tests/pilot/gateway.py](https://github.com/merapplications-sketch/Talabat-v3/blob/1cb85361d698d5da787d927a4c9ae7bd213c68c1/tests/pilot/gateway.py) | 199e3592c27c9280b02c3b787b4f54ced39111d6 | NOT MATERIALIZED |
| [tests/pilot/package.json](https://github.com/merapplications-sketch/Talabat-v3/blob/1cb85361d698d5da787d927a4c9ae7bd213c68c1/tests/pilot/package.json) | a476d952be4cec7972766cfd2d58b7a896d8bb70 | NOT MATERIALIZED |
| [tests/pilot/package-lock.json](https://github.com/merapplications-sketch/Talabat-v3/blob/1cb85361d698d5da787d927a4c9ae7bd213c68c1/tests/pilot/package-lock.json) | cfc0594cacc358abe74bf5726e86acbdbdcb4b27 | NOT MATERIALIZED |
| [tests/fixture.js](https://github.com/merapplications-sketch/Talabat-v3/blob/1cb85361d698d5da787d927a4c9ae7bd213c68c1/tests/fixture.js) | dce8d7b20192a652af0c85300ab2a6ffe79e51e2 | NOT MATERIALIZED |
| [tools/qa_all.py](https://github.com/merapplications-sketch/Talabat-v3/blob/1cb85361d698d5da787d927a4c9ae7bd213c68c1/tools/qa_all.py) | 19a9643f3643364b48f8fa8ccd2dd5bafd22c6c4 | NOT MATERIALIZED |
| [pilot-isolated.yml](https://github.com/merapplications-sketch/Talabat-v3/blob/1cb85361d698d5da787d927a4c9ae7bd213c68c1/.github/workflows/pilot-isolated.yml) | 6f32bb7b2ce80304d139ba75fb5c926bf73e1e36 | NOT MATERIALIZED |

Complete source-byte SHA256 and executable release digest are **BLOCKED**, not inferred from Git SHA-1, a historical site, or earlier test PASS. A full offline source-and-assets bundle still requires a legitimate approved transfer to an equipped preparation host, immutable per-file SHA256 and manifest verification before sealing the VM. The actual source staging folder contained **zero** source files after the failed archive retrieval. No product/approved-source modification occurred.

## 3. Actual resource inventory and service availability

| Component | Actual observation | Gate implication |
|---|---|---|
| Execution host | Restricted Linux x86_64 tools container; root inside container, not hypervisor operator | NOT an approved disposable VM |
| Docker/Compose, Podman, nerdctl | ABSENT | No local C-01 container stack |
| QEMU/KVM, libvirt, virsh, virt-install, /dev/kvm | ABSENT | Cannot build the specified VM |
| PostgreSQL server and psql | ABSENT | No locally provisioned DB |
| nft, iptables, ip6tables | ABSENT | Cannot attest full host/Docker firewall deny counters |
| Host CAP_SYS_ADMIN, CAP_NET_ADMIN | ABSENT | No host network/firewall policy changes authorized or possible |
| unshare user+net namespace | AVAILABLE for a short-lived process | Subsystem capability only, not VM |
| Outer IPv4 route and proxy configuration | PRESENT; values intentionally not exported | Current tools host is not proven air-gapped |
| Existing full pinned source/archive locally | ABSENT, public GitHub archive retrieval DNS failure | Offline bundle NOT BUILT |
| PostgreSQL, GoTrue, PostgREST, gateway, browser | NOT STARTED | C-01 impossible in actual present environment |
| Real cloud account/services used | NONE | No production mutations or hosted test actions |

Original Compose host publishes local 5432/9999/3000 loopback ports but does not define an internal Docker-only network that blocks egress. It also includes Storage and Mailpit not needed for C-01. Existing lab.py prepare_app seeds eight synthetic roles and store/menu fixtures; its journey/integration covers broad business/financial scenarios. **Neither Compose nor broad journey was run or edited.**

## 4. Actual synthetic negative-network preflight (LIMITED DEMONSTRATION)

A single ephemeral user+network namespace was created **only** for a security-control demonstration. No TALABOT source, API, container, browser, Auth/REST or DB process ran inside it. IPv4/IPv6 test destinations were reserved documentation networks, **not production**. The namespace process exited after the probe.

| Assertion | Direct observation | Correct interpretation |
|---|---|---|
| Parent network namespace inode | 4026531833 | Preparation host context |
| Child temporary network namespace inode | **4026532185** | Different namespace, not a VM |
| Child interfaces | only loopback; initially down | No outward virtual interface in child |
| Child default IPv4/IPv6 routes | **none** | No external route in that process namespace |
| Enable loopback + local TCP connect | **PASS** | 127.0.0.1 communication possible |
| TCP 192.0.2.123:9 (synthetic IPv4) | **DENIED / errno 101 ENETUNREACH** | This one negative case could not route out |
| TCP [2001:db8::123]:9 (synthetic IPv6) | **DENIED / errno 101 ENETUNREACH** | This one negative case could not route out |
| Synthetic DNS talabot-egress-check.invalid | EAI_AGAIN / no resolution | Not a firewall packet-counter or whole-runner DNS proof |
| Post-probe namespace listing | Only host namespace remained listed | Temporary probe finished, no retained test VM |

**CRITICAL LIMITATION:** These negative results **do not** prove host-wide or Docker egress denial for a VM that does not yet exist, and do not verify packet counters, DNS forwarder blocking, no proxy leak from all processes, or source/runtime consistency. Do not mark N1/N2/N5 PASS from them.

Evidence integrity (sanitized local preparation bundle, separately supplied to the user):
- network-namespace-control-20261113.json SHA256: **3eeb09a5243695cd54369a36629662ee55f12ca282a0453bc73a9057965b3989**
- dns-control-20261113.json SHA256: **be843f47a76b0ce0e70f2374256f955db80c0fc5946bdcc80b479cc0dd51ec88**
- STAGE9_PREPARATION_MANIFEST.json SHA256: **8f7706ee9b7f3dc567d193b51fd615c619760676302da1c6d1fc4474f99bdd3c**
- Full local evidence ZIP SHA256: **422cdc7b82accec9975d51365dec1bc6e0916d175f50b6df4438d9d36c5161b5**

Evidence directory was permission-restricted; no secrets, production URLs for live probes, raw credentials or production records were exported. The ZIP contains only manifest, metadata and negative-control results — **no executable VM, source clone or test credentials**.

## 5. Dependency/OCI inventory: declared versus actually staged

| Service | Source declaration | Actual immutable artifact status |
|---|---|---|
| PostgreSQL | postgres:17.6@sha256:00bc86618629af00d2937fdc5a5d63db3ff8450acf52f0636ec813c7f4902929 | Digest present in Compose; image bytes **NOT staged** |
| GoTrue | supabase/gotrue:v2.197.0 | Tag only; immutable digest unknown; **NOT staged** |
| PostgREST | postgrest/postgrest:v14.18 | Tag only; immutable digest unknown; **NOT staged** |
| Playwright | npm 1.56.1 | package-lock reference exists; browser binary and hash **NOT staged** |
| Supabase JS | npm 2.117.2 + vendor Git blob | Original source reference exists; offline browser bundle hash **NOT staged** |
| Python driver | psycopg[binary]==3.2.10 in old workflow | NOT installed or staged here |
| Storage/Mailpit | Version-tag declarations in original Compose | OUT OF SCOPE for C-01; not started |

No image pull, package install, new VM, GitHub Actions dispatch or cloud resource operation was undertaken. GitHub connector queries read existing code only. The original source still embeds the historical production Supabase API URL, so source/environment substitution and independent offline network denial remain mandatory before any browser use.

## 6. N0–N7 security gate matrix

| Gate | Existing evidence | Missing proof / responsible team | Status |
|---|---|---|---|
| **N0 source provenance** | Source SHA and 11 Git blob refs verified | Full source/assets copied and SHA256/OCI/browser binary digests on an approved prep host. DEV+OPS. | **PARTIAL/BLOCKED** |
| **N1 VM isolation** | Short-lived new user+net namespace no route | Real disposable VM with no public vNIC, NAT, DNS/proxy, VPN, host bypass, metadata path; hypervisor inventory/attestation. OPS+SEC. | **BLOCKED** |
| **N2 host/container denies** | Host lacks Docker and firewall tooling | OS firewall OUTPUT/FORWARD for all IPv4/IPv6/DNS, deny counters, Docker daemon and per-container network evidence. OPS+SEC. | **BLOCKED** |
| **N3 allowed processes/ports** | Original gateway and local port plan inspected at source level | Actual process tree, browser/XHR/WebSocket/worker/Docker network allowlist, listener inventory, unexpected-request stop instrumentation. QA+SEC. | **BLOCKED/UNTESTED** |
| **N4 synthetic local services** | Historical Compose and lab scripts available in GitHub | PostgreSQL, GoTrue, PostgREST, gateway in a VM; exactly two synthetic customer profiles; no actual/hosted data. DB+AUTH+OPS. | **NOT PROVISIONED** |
| **N5 dummy negative control** | IPv4/IPv6 DENIED and DNS unresolved in temporary namespace | Repeat inside **real VM including containers and subprocesses** with independent firewall/DNS deny counters before service readiness acceptance. SEC+OPS. | **PARTIAL DEMONSTRATION / NOT PASS** |
| **N6 local writes only** | Intended C-01 scope reviewed; no C-01 run | Approved minimal test-only bootstrap and RLS/role reviews, pre/post order/wallet/settlement zero-delta evidence. DEV+DB+AUTH. | **BLOCKED** |
| **N7 evidence+seal+cleanup** | Local SHA256 evidence, transient namespace ended | Stopped sealed VM ID/snapshot, custody/teardown of VM and volumes, credential/log sanitization, independent reviewer signing. OPS+SEC. | **PARTIAL/BLOCKED** |

**Fully satisfied safety gates: 0 of 8.** Readiness for independent final PASS: **NO-GO**. No one should interpret a denied dummy packet in a temporary namespace as equivalent to a certified off-network VM.

## 7. Stop conditions, owner permissions, and next exact handoff

**STOP enforced at N0/N1/N2 infrastructure gates.** VM provisioning could not proceed without tooling and a full offline source bundle, so no downstream services or functional tests were started. Do not weaken egress controls, enable public network to fetch packages inside a supposedly sealed runner, substitute active hosted Supabase or Cloudflare, dispatch broad journey or move workflow to main, create paid services, use real keys, change roles, touch protected orders #1/#2/#3 or their settlement, run hosted SQL, or run C-01.

Before any continuation under already-approved Stage 8 scope:
1. **PM/OPS** identifies an existing, permitted zero-cost capable VM/hypervisor or offline VM artifact and legitimate approved source/OCI/browser transfer path. If a **different execution medium** from the approved VM or any cost is required, seek **new explicit owner approval**; do not silently reuse this tools container/namespace.
2. **DEV/OPS** provides full exact-1cb85361 offline source and immutable dependency bytes, complete SHA256 and OCI digests. A historical CI106 or GitHub blob alone is insufficient.
3. **OPS/SEC** applies and logs real VM/host/Docker deny-all external networking including IPv4, IPv6, DNS and proxies; proves a synthetic dummy denial with independent counters and local ports allowed. No production-directed probe.
4. **DEV+AUTH+DB** prepares a dedicated separately reviewed C-01-only bootstrap with **two** synthetic customers, and local PostgreSQL/GoTrue/PostgREST/gateway. Do NOT call original eight-persona prepare_app or journey/integration.
5. **Independent technical/security reviewer** checks a **stopped/sealed VM** and N0–N7 evidence and issues a separate PASS/FAIL decision. Stage9 OPS may not self-approve C-01.
6. **Only after independent PASS and a later separate PM role dispatch** may programmer/QA execute **one C-01** invalid/valid synthetic login, A/B profile and cross-account negative read. C-01 remains **0 executed** as of this report.

Emergency triggers for any later run: unplanned external interface/default route/DNS/proxy, any production URL/key in effective runtime, attempted non-lab HTTP/DNS/TCP/WebSocket, source/digest mismatch, unexpected role or database mutation, missing deny counters, unexpected paid service or finance/order side effect → **STOP**, retain only redacted incident evidence and notify PM/SEC without any production action.

## 8. Delivery status

- **Stage9:** PARTIAL PREPARATION / BLOCKED AT INFRASTRUCTURE.
- **Actual prepared VM:** NO. **Actual prepared services:** NONE. **Offline source bundle:** NOT COMPLETE. **Sandbox demonstration:** IPv4/IPv6 dummy egress denied within a transient namespace only.
- **C-01:** NOT RUN. **Full current-source E2E:** 0/51; Admin: 0/21.
- **G1-A/B/C/E/F:** PARTIAL; **G1-D:** BLOCKED.
- **Security readiness:** NO-GO. **QA/Release/PHASE2:** NO-GO.
- **Repository write scope:** one Markdown report on a dedicated isolated documentation-only branch based on immutable PM SHA 1cb85361. No application/design/SQL/CI/Compose/main changes; no deploy, merge, cloud write or workflow execution.

The manager should receive this evidence **as a STOP and capability blocker**, not a completed setup or an independent security PASS. The previously granted owner approval has not been exceeded.
