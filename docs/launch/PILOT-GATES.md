# TALABOT — Pilot-First Delivery Gates

**Status:** Proposed operating plan, not release approval. Decision authority remains with owner. No unauthorized live tests, deployments, finance changes, secret access, Supabase/Cloudflare writes, new costs or product redesign.

## Key distinctions
- **A — Synthetic Safari visual preview:** read-only/fake-data consumer demo, no TALABOT/ChatGPT sign-in, separate free static HTTPS origin, no real API or payments. This is for owner visual inspection only.
- **B — Isolated functional QA:** current-source end-to-end test of all four roles with synthetic identities/orders in verified production-disconnected conditions.
- **C — Controlled real pilot:** live, limited real-world delivery with written owner approval after operational, security and finance controls pass. Passing A does **not** approve B or C.

## Sequential gate table
| Gate | Responsible role | Acceptance evidence | Current finding 14 Nov 2026 | Decision |
|---|---|---|---|---|
| G0 Source/authority baseline | Manager + code custodian | Exact branch/HEAD and owner decisions; production vs source provenance; re-use earlier accepted proof | Stage13 fake-demo SHA documented, live/source parity unresolved | OPEN |
| A1 No-login fake demo source | Programmer → independent reviewer | Approved original components preserved; no external API/order/payment; complete exact artifact with SHA | Source-only provenance; 8/8 simulated language checks; real browser not tested | PARTIAL |
| A2 Demo browser & security | Independent security+UX | Run exact artifact on safe static test host; RU/EN, 320/360/390/430; click/return/refresh/cart; screenshots, console, **actual outbound request trace**; no real checkout; physical Safari separately observed | **0** executable demo journeys/viewport runs in last formal report | BLOCKED |
| A3 Free public visual preview | Publisher only, after owner approval | Specific verified static artifact + distinct no-bindings HTTPS host + owner sign-off; no ChatGPT login, no real account, no production origin | No approved public demo URL created | NO-GO |
| B1 Functional QA | Programmer + independent QA | Current-SHA synthetic customer/driver/merchant/admin journeys; retry/race/offline/permissions/price; test execution records | 0/51 current-source integrated E2E; admin 0/21 | NO-GO |
| B2 Finance, access and release | Finance + security + OPS + manager | Q09–17/CASH-01/RETURN-01 reconciliation and isolation; active RPC/service hashes, backups/recovery, role segregation, CI, G1 gates | G1 A/B/C/E/F partial; G1-D blocked; 0/6 accepted | NO-GO |
| C1 Limited live pilot | Owner → publisher / operations | Separate scope, locality, permitted merchant/driver/customer accounts, order limits, rollback, incident contacts, stop criteria and approval | Not authorized | NO-GO |

## Exact next dispatch — one role only
**Manager should receive Stage13 #39 first**, verify the corrected exact candidate `3f74b29a...`, then assign **one independent security/browser reviewer** for **A2**. Do not repeat Stage11's already accepted source hashes. The reviewer must either produce real browser/egress/geometry evidence, or a specific `BLOCKED` diagnosis. Only after that should an independent UX/device review and publisher feasibility happen in sequence. Do not activate inactive role chats automatically. If an existing permitted test environment is unavailable, propose the least risky no-cost option for the owner's approval without silently substituting a public production host.

## Non-negotiable acceptance contract
Per case: `ID | module | exact SHA & environment | setup/synthetic fixtures | action | expected | actual | PASS/FAIL/PARTIAL/BLOCKED/UNTESTED | severity | proof URL/log/screenshot | role | next action`. For a suspected code defect, distinguish source-confirmed risk from deployed incident. Regressions must use failing-before and passing-after evidence on exactly scoped modifications after approval.

## Go/No-Go decision
Manager may request **visual demo publication** only on A1+A2 pass and an exact-host owner approval; manager may request **pilot authorization** only after B1+B2 have enough test and deployment evidence, incident/rollback plans and owner approval. Do not present either as already complete.
