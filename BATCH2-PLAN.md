# Batch 2 (UAT008/009/011/012/013/014/015) — preparation only, NOT implemented (17 Oct)
Base for implementation: `fix/uat2-v58` (v58 under review). Mapped against the current source; live SQL not read yet
(`sql/verify_batch2_readonly.sql`, one read-only result). No polling, no points-expiry change before the live read and the owner decision. No prices, points values, funding or permissions to change.

| Item | Where in the source | Finding | Fix (display / update) | Needs live definition | Economic decision |
|---|---|---|---|---|---|
| UAT008 celebration on returned points | customer `milestone()` | fires on any balance crossing, incl. RETURNED points; ledger kinds in the repo: earn / spend / return / reward (reward = rating bonus, patch 32) | celebrate only for a NEW ledger entry of kind earn OR reward not shown before: remember the last ledger id already shown (per user); the first load only sets that mark (no celebration for old rows); return / spend never celebrate and never notify again on later loads | no | no |
| UAT009 history not updated with the balance | customer `vWallet` → `TLB.loadPoints()` once per session | the balance refreshes with order events, the history never does | reload the history on the events that create ledger rows, not on a balance change (spend + return can leave the same balance): a realtime order change of my order (placed / delivered / cancelled / rejected), my rating sent, my order placed. One load at a time (a new event while loading = one more load after it), each load numbered, an older reply is ignored. No new polling. Live check: is loyalty_ledger in the realtime publication (query section 6) | publication only | no |
| UAT011 expiry after a return | repo patch 29 `trg_orders_loyalty`: a return creates a NEW lot with `now() + expiry_days`; wallet shows `next_exp_at` of the lots | if live = repo, the changed date is the policy's effect, not a display error | display: name what the date refers to (e.g. «включая возвращённые баллы до {d}»), only after the live check | YES (live trigger function) | YES: returned points — original expiry or a new full period; points that expired while the order was open |
| UAT012 original payment vs final settlement | customer `receipt()` / `cxCard()`; restaurant `odSheet()` | a cancelled order reads like a paid one; the restaurant sees the commission as a deduction for cancelled orders | confirmed only by records: wallet «возвращено X» only with a wallet_entries return row for this order, points «возвращены N» only with a loyalty_ledger return row for this order; otherwise «возврат не подтверждён». Cash: only the recorded collection field (cash_collected); without it «нет записи о получении наличных» — never «не получены» from the status alone. Card: «данных о списании нет». Restaurant: commission «не начисляется — заказ не выполнен», no net payable | YES (return rows and cash_collected semantics) | no |
| UAT013 cancelled vs rejected | restaurant `vStats`: one bar «Отклонено» = all − delivered | statuses mixed | two counts by STATUS only (rejected / cancelled) — a status display, NOT responsibility: not used to rate, rank or penalise the restaurant. Reason only from the recorded code; old orders without a code = «причина не указана». Responsibility data is a separate item | YES (`reject_order`, `set_order_status`) | no |
| UAT014 «После комиссии» | restaurant dictionary `stNetT`, `vStats` | label only | RU «Чистыми к получению», EN «Net payable to you» + lines: выручка − комиссия − баллы − кэшбэк − доставка за ваш счёт = итог (same formula) | no | no |
| UAT015 effective points rate | customer wallet rules (`earn_per_tjs` global), menu `earnBadge` (store rate), pay summary | wallet shows only the global 10/TJS; a store may have its own (Romant 1/TJS); the order was computed right | wallet: «обычно 10 за 1 TJS, в некоторых заведениях иначе»; pay page: «начислим N баллов · ставка заведения R за 1 TJS». Settings and voucher value unchanged | YES (confirm place_order earns with the store rate) | no |

Blocking decision (economic, only one): UAT011 — expiry of returned points (original vs new period) and points that expire
while an order is open. No extension is made without it.
Order of work after approval: 009 + 008 (same data), 014, 015, 012, 013, 011 (after the decision and the live read).

## Live read (owner's result of verify_batch2_readonly, 17 Oct) — what it confirms
The live definitions used by these items match sql/ in the repository: place_order, reject_order, set_order_status, trg_loyalty,
trg_rating_reward, trg_wallet_return (patch 21), loyalty_spend / loyalty_balance / loyalty_summary / loyalty_setting. 8 settings as expected.
Realtime: orders, ratings, wallet_entries — NOT loyalty_ledger.
- 008: earn row only at delivered (trg_loyalty); reward row only on the first rating of an order (ratings insert, once per order). Plan unchanged.
- 009: no ledger realtime → refresh the history on my order status events (already subscribed), after my rating, after placing. No DB change, no polling.
- 011: confirmed policy, not a display bug: a return creates a NEW lot `now() + 90 days`; points that expired during the order come back with
  a fresh 90 days too. Behaviour unchanged until the owner decides.
- 012: the wallet return entry (= full wallet_used) and wallet_returned_at are written in the same trigger/transaction; same for the points
  return ledger row (= points_used) and points_returned_at → the order markers are the recorded proof; without a marker «возврат не подтверждён».
  cash_collected is written only by deliver_order on delivery → for a cancelled / rejected order it is always empty → «нет записи о получении
  наличных». Commission stays recorded on a cancelled order (not reset) → the restaurant sheet must not show it as due (stats already count delivered only).
  Support refunds are separate wallet entries of kind 'refund' (shown as such if present).
- 013: 'rejected' = store via reject_order (code + cancelled_by='store'), store via set_order_status from pending (no code), or admin / staff
  (no cancelled_by). 'cancelled' = customer (only while pending) or admin / staff — the store can never set it. cancelled_by is filled only by
  reject_order. Status display only, no responsibility.
- 015: points are earned at DELIVERY (not in place_order): (dishes − discounts − promo − points value) × store earn_per_tjs, or the global 10
  when the store has none; delivery and tip earn nothing. The rate is read at delivery time, so the pay page can only show an estimate
  («ориентировочно»). Information for the owner, no change.
