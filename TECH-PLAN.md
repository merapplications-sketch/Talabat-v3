# TECH-PLAN — technical batches after customer v80 (reference; read this instead of re-opening the whole project)
Base: `tech/v81` = published state (`integration/customer-v80-current` ca8808d) + v81 fix. Scope: logic, data, permissions,
order cycle, accounts, tests. NOT design / visual application (ChatGPT team; hand-offs = files + changes only).
Test words: **mock** = Chromium + in-memory Supabase (tools/*) · **live** = the published app + the real database.

## 1. Published now (verified from the repo, not live)
| File | Version | Notes |
|---|---|---|
| customer.html | v80 (ChatGPT team) | built on the v61 customer logic; calls 3 core functions that the published core lacks (pointsSnapshot, pointsAbandon, orderWallet) → those 2 features hide quietly |
| admin / merchant / driver / talabat-core.js | v55 (main 148cfae) | v56–v59 approved in UAT but never published |
| DB | patches up to 34 assumed applied; 27 doubtful (SC-48); 35–38 not applied | to confirm with `sql/verify_catalog_readonly.sql` (patch section) |

## 2. Past batches
| Batch | Goal | Status |
|---|---|---|
| v30–v55 | core apps, RBAC (26), branches (27), loyalty (29–33), courier batch 2 (34), Home | published (main) |
| v56 (UAT1 admin + stability) | admin search (patch 35 optional), filters, timeline names, settlement, invoice, chat, banner label, rating counters, forms kept on refresh, ids as JSON, history paging, OSM origin | local `fix/uat1-v56`, mock-tested, not published |
| v57 (onboarding) | partner page, Edge Function + Turnstile, patch 36, admin lead card | local, needs patch 36 + keys + function deploy — waits |
| v58 (UAT2-1) | cancel waits for server, chat drafts per order, one delivery confirmation at a time, order confirmation control | customer part in v80; driver / core parts not published |
| v59 (UAT2-2) | points history + snapshot, recorded returns / collection, rejected vs cancelled, net payable, rate wording | customer part in v80; merchant / core parts not published |
| v60 / v61 (finance, patch 37/38) | proof, refunds, courier / store accounting | FROZEN (economic decisions 1–8 in STATUS-PLAN) |
| v62–v63b (design) | customer design | superseded by v80 (ChatGPT team) |
| v81 (tech) | admin add-store fix; catalog + admin sign-in mock checks; read-only DB query | branch `tech/v81`, mock only |
| v81b (tech) | T2 done (mock); plan file; read-only query + patch markers; cart / flow checks follow the approved v80 controls | branch `tech/v81`, mock only |

## 3. Batches to do (order; done-criteria; what it waits for)
| # | Batch | Content (sources) | Done when | Waits for |
|---|---|---|---|---|
| T1 | Live DB read | `sql/verify_catalog_readonly.sql`: catalog defaults, RLS, bucket `media`, storage policies, triggers, owner/perm functions, accounts by role, patch markers 26–38, wallet / loyalty columns | result table received and mapped here | owner runs it once (no access from this workspace) |
| T2 ✔ mock | Core functions v80 already calls | port `pointsSnapshot`, `pointsAbandon` (v59) and `orderWallet` (read-only, from v60, existing table `wallet_entries`) into the published core; no SQL, no UI change | catalog / flow / qa_all mock clean; uat3 customer parts pass; live: columns confirmed by T1 | can start now (live confirmation after T1) |
| T3 | v56 admin — functional items only | 10 UAT1 items + forms kept on refresh (v56d–f), ids as JSON (v56h, v56m), customer history paging (v56g), merchant analytics from recorded values (v56l–m), OSM origin; search uses patch 35 when present, else loaded orders (existing fallback) | admin_uat / form_keep / merchant_ids / merchant_stats / qa_all mock clean; hand-off list of touched admin / merchant lines | can start now; visual parts (v56i–j staff look, v56n–o strip) go to the UI team as a hand-off, not ported by us |
| T4 | v58 driver / core | one delivery confirmation at a time (UAT004 screen guard), chat drafts per order (core), cancel waits for the server (core) | courier / uat2 mock clean | can start now; driver visual design waits for the designer — only logic lines touched |
| T5 | v59 merchant / core | UAT012 recorded returns in the restaurant order sheet, UAT013 rejected vs cancelled labels, UAT014 net payable + breakdown (formula unchanged) | uat3 (merchant parts), merchant_stats mock clean | can start now; label/text changes listed for the UI team |
| T6 | Live functional pass | sign-in (admin, staff, restaurant, courier, customer), save store / dish / sizes / extras / photos / banners, customer sees them, one test order through the 4 apps, assignment, cancel / reject | each step done on the published app with the test accounts, results logged | owner opens Chrome with the Claude extension (or does the steps himself) |
| T7 | Merge / publish T2–T5 | PR to main with the list of files and checks | owner approval | owner |
| T8 | Onboarding (v57) | patch 36, partner-lead function, Turnstile, lead card ON | activation list in ACTIVATION-v57.md | keys + patch 36 approval |
| T9 | Finance (v60 / v61) | patch 37 / 38 | — | FROZEN: decisions 1–8 |
| T10 | Later (approved backlog, no new requirements) | rating thresholds (decision), payment provider (none), batch 4 (streak / rating reward, receipt print, combo banner), backlog 4–7 (auto-cancel pg_cron, courier GPS, offline, push, OTP), launch checklist (test accounts, Auth rate limits, k6, SRI), small follow-ups (unquoted ids, loaded-order limits), UAT011 / UAT005 / ticket_refund_room / cash settlement concurrency | per item | decisions / providers / plan features |

Rules: one batch per branch from the previous one; customer.html (v80) is not edited — logic needs there go to the UI team as
a hand-off; every SQL is read-only unless the owner approves a named patch; mock results never reported as live.
