# Status and batch plan — reference for the next rounds (16 Oct 2026)

Branch `fix/uat1-v56` (not merged, not deployed). Production = main (admin unchanged since v52).
Test details: `QA-UAT1.md`. Changes: `CHANGES-v56.md`. Owner rules and history: `HANDOFF.md`.
Status words: **proven** = cause shown by code/measurement · **fixed, not verified** = needs the owner's iPhone · **open** = cause not proven.

## 1. Current stability batch (v56o)

| Item | Status | Evidence |
|---|---|---|
| Support tab moved the strip | proven, fixed (v56o); iPhone round 19:05–19:06 does not show a Support tap (no section names in that log) — not closed | the support bar (~50 px) was hidden only on Support → strip 333→283 at the page top; now the bar shows on every tab: 333→333 (`tools/tab_nav_check.py`, before 6 fails / after 0) |
| Couriers→Customers moved the strip | proven in Chromium, fixed (v56o); not closed on iPhone (§1b) | Customers is short while loading, the page could not be scrolled far enough (153→333). Now the page keeps enough height until the next section tap (no timer, no scroll lock) |
| Strip partly under the sticky support bar | fixed (v56o) | the strip comes just under the bar instead of staying covered |
| Leaving Orders moves the strip | proven (geometry), NOT fixed — needs a look decision | Orders has the indicator cards + caption (369 px) above the strip, other sections do not. When Orders is scrolled less than 369 px the other section cannot be scrolled to keep the strip: it moves up by (369 − offset): from the top of Orders 679→310, iPhone 19:06:01 at offset 329 → about 40 px (Chromium 430×815: 350→310), plus the header comes back. Same app scroll is named `tabKeep` (§1b). Options: (a) accept; (b) cards below the strip in Orders; (c) the same block above the strip in every section — (b)/(c) change the look |
| Safari jumps (rotation / background / reload) | open — see §2 | no guess fix added |

### 1b. iPhone round 16 Oct 19:05:47–19:06:50 (owner: «first time when I tapped Stores»)
The log has no build id, so it cannot prove which preview ran; taken as v56o (89b229e) per the owner. Sections are inferred from the
page length only (max offset 1292 ≈ Orders, 875 ≈ Stores, 559 ≈ Couriers, Chromium 430×815: 1305 / 858 / 550) — inference, not record.
**Diagnostic error found (proven):** the caller name skipped one frame on Safari (Safari stacks have no "Error" first line), so
«onclick» = really `tabKeep` (or `render`) called by the tap, «cuLoad<onclick» = really `render` called by `cuLoad`. Fixed in v56p.

| Time | Log | Reading (measured in Chromium unless said) | Status |
|---|---|---|---|
| 19:06:01 | app scrollTo 329→0, 6 ms after the tap redraw | Orders → Stores; strip keep step: the strip cannot stay (needs −40), page to the top, strip 350→310; then Safari bar resize 815→775 | proven cause = Orders cards (row above); acceptability = owner decision |
| 19:06:29 | 219→583 | → Orders: page scrolled by the cards' height so the strip stays | intended; visually unverified |
| 19:06:33 | 583→219 | Orders → Couriers: back by the same height, strip stays | intended; visually unverified |
| 19:06:39 | 0→219 by `render` inside `cuLoad`, page length 0 at that moment | Couriers → Customers: the loading screen is shorter than the screen, the page is clamped to 0 inside the same tap; v56o then keeps the page tall and restores 219 (Chromium: frame before 219, next frame 219, no frame at 0). On iPhone only this one call was logged, the later calm state is y219 | whether a frame at 0 was shown on Safari: not shown by the log → SECTION TAP line in v56p |
| 19:06:50 | y219→0, page 1074 unchanged, screen 815→775, no app scrollTo, no redraw | the offset fell over several frames (105, 95, 84… px) as the Safari bars came back — a gradual motion, not a one-step jump. Possible: finger fling / tap on the status bar / browser; none proven (touches were not logged) | open; v56p logs touch time with every TRACE / JUMP |

## 2. Safari — cases kept separate (owner logs, iPhone; none reproduced here)

| Case | What the log shows | Status |
|---|---|---|
| A. Rotation to landscape | 403 → 635 at the moment of resize (0 ms), no app scrollTo | open; landscape layout is shorter/longer, the browser keeps a different anchor — not proven |
| B. Back to portrait | 396 → 0 and 302 → 0 (the second with `text-size-adjust:100%` and a constant probe font → text enlargement ruled out for it); last redraw 3–4 s earlier; no app scrollTo | open; the app is not the mover by the log, the absence of app scrollTo alone does not prove the cause |
| C. 190 s in background | not reloaded, position kept | no defect seen |
| D. Reload after 16 s in background (15:13:56) | a new PAGE LOAD; the app reloads only on a tap or sign-out, neither logged | open; probably the browser discarded the page (not proven) |
| Environment | screenshots show «◀ Claude»: the preview was opened inside the Claude iOS app's browser, not Safari itself | may matter for A/B/D; a check in Safari proper would separate it |

## 3. Future batches (order to be reviewed by the owner before starting)

| Batch | Original requests (source) | Done + evidence | Remaining | Decision / access needed |
|---|---|---|---|---|
| UAT 1 (admin) + stability | owner UAT 15–16 Oct (chat; `CHANGES-v56.md`) | 10 UAT items + v56d–v56o, tests in `QA-UAT1.md` | owner iPhone check of v56o; merge | owner approval to merge `fix/uat1-v56`; production deploy |
| patch35 (search all orders) | UAT item 1 (`CHANGES-v56.md`) | `sql/schema_patch35.sql`, `sql/test_patch35.sql` 16/16 on local PostgreSQL; panel falls back to loaded 300 orders with a note | apply in Supabase | owner runs it (not applied anywhere) |
| Rating states | UAT item 9; `HANDOFF.md` line 4 | one rule «Требуют внимания» = unhandled 1–3★ (tile, filter, badge, card) | red alert ≤2★ vs attention ≤3★; separate «not reviewed» vs «needs action» states | owner decision on thresholds/states |
| Payment, collection, refund | UAT item 4; `HANDOFF.md` line 4 | admin card shows cash from courier record, online = «не проверено», refund «нет данных», wallet/points from records | real online payment status, collection reconciliation, card refunds | a payment provider/gateway + access (none exists) |
| Batch 3 — restaurant onboarding | `HANDOFF.md` (NEXT, 10 Oct); owner decisions 16 Oct 21:23 | v57 built locally on `feature/partner-onboarding-v57` (`CHANGES-v57.md`): partner.html (page, calculator, form), Edge Function partner-lead (Turnstile on the server), patch 36 (not applied), admin card, banner link; tests in CHANGES-v57 | owner review; activation list in `supabase/functions/partner-lead/README.md`; linking off until assign_owner verified | Cloudflare Turnstile keys, LEAD_HASH_KEY, function deploy, patch 36 run, read-only check of assign_owner; limits/retention approval |
| Batch 4 | `HANDOFF.md` «Owner answers 10 Oct 19:58» | out-of-stock suggestions DONE v52 | streak bonus + rating reward paid by the platform (points accounting change); receipt print 58/80 mm; combo/family banner at peaks (12:00–15:00, 18:30–21:30, admin-editable) | values of rewards; printer model/devices; «combo» mark on dishes |
| Backlog 4 | `HANDOFF.md` approved backlog | — | auto-cancel after 5 min (pg_cron), live courier GPS, offline cache + sync | pg_cron on the Supabase plan |
| Backlog 5 | same | — | push, batch delivery, heatmaps, partner requests, offers/ads | push needs PWA + VAPID + server function |
| Backlog 6 | same; `SCALING-AND-SECURITY.md` §D | — | OTP sign-up via SMS/WhatsApp | SMS provider for Tajikistan; domain |
| Backlog 7 / launch | same; `SCALING-AND-SECURITY.md` §A | — | delete test accounts, Auth rate limits, Supabase dashboard checklist, k6 load test, SRI hashes, server-side dish search | owner dashboard access |
| Small follow-ups | `QA-UAT1.md` | — | customer (10) and courier (5) handlers with unquoted ids (fine for numeric production ids); customer history 50 + «more» in admin done, other 300/200 loaded-order limits remain | none (technical) |

Pending decisions without a batch: keeping drafts after inactivity sign-out (Pending, unchanged); what wins when saving over a server edit; contracted map provider when traffic grows; owner confirmations: patch 27 applied (SC-48 showed it missing), security-check re-run after patch 28. Gift points: CANCELLED by the owner.

Designer brief document: asked 11 Oct, not delivered (`HANDOFF.md` line 5); its content is not in the project.

**Source not found in the project files:** the ordering of batches 3/4 versus backlogs 4–7 after UAT 1 is not written anywhere — to be confirmed by the owner.

## Status log — 17 Oct
- v57e (onboarding, `feature/partner-onboarding-v57` @ 5e9449c): «Local preparation complete per the recorded checks, awaiting
  review and approval of activation». Not tested on the live database. Linking OFF. Note: an annotated git tag
  `v57e-local-prep` for this was created locally but GitHub refused the push (HTTP 403); no new tag, no retry, no wider rights.
- v58 (UAT2 batch 1, `fix/uat2-v58`, base 5e9449c → depends on v57 and v56 approvals): see CHANGES-v58.md.
  | Item | Status | Evidence | Remaining |
  |---|---|---|---|
  | UAT002 cancel waits for the server | implemented | uat2_check (Chromium) | iPhone check |
  | UAT003 chat drafts per order | implemented | uat2_check | iPhone check |
  | UAT004 one delivery confirmation at a time | implemented (screen guard) | uat2_check | server idempotency not proven |
  | Hold 2 s order confirmation + 2-step keyboard path | implemented | uat2_check | iPhone / VoiceOver check |
  | UAT008/009/011/012/013/014/015 (batch 2) | moved to v59 (below) | — | — |
- Other open notes are NOT closed by this batch (Safari jumps, stability batch, onboarding activation, earlier backlog).
- v59 (UAT2 batch 2, `fix/uat3-v59`, base `fix/uat2-v58` @ 1e105c6 → depends on v58 / v57 / v56): see CHANGES-v59.md and BATCH2-PLAN.md.
  | Item | Status | Evidence | Remaining |
  |---|---|---|---|
  | UAT009 points history with the balance | implemented | uat3_check (Chromium) | iPhone check |
  | UAT008 celebration only for new earn / reward | implemented | uat3_check | iPhone check |
  | UAT012 recorded returns / collection (customer + restaurant) | implemented | uat3_check | iPhone check |
  | UAT013 rejected / cancelled as statuses only | implemented | uat3_check | responsibility data = separate item |
  | UAT014 «Чистыми к получению» + breakdown | implemented (formula unchanged) | uat3_check, merchant_stats_check | — |
  | UAT015 rate from the settings + estimate wording | implemented | uat3_check | — |
  | UAT011 expiry of returned points | NOT changed (live: new lot now + 90 days) | live read 17 Oct | owner decision |
  Logged for later batches (not in v59): UAT005 photo existence in storage; ticket_refund_room cap (refund only, executor function not read);
  driver cash settlement (concurrency, receiver / reference, partial amounts); cancellation responsibility apart from cancelled_by.
