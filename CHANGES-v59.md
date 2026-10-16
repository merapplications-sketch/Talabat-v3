# v59 — UAT2 batch 2 (UAT008 / 009 / 012 / 013 / 014 / 015), local, not published
Branch `fix/uat3-v59` from `fix/uat2-v58`. Files: customer.html, merchant.html, talabat-core.js (one function). No SQL, no settings,
no prices / points / cashback / commission / permission rules changed. Live definitions used as reference: owner's read of 17 Oct.

- UAT009 (customer): the points history reloads on the events that create ledger rows — my order placed or changing status
  (existing realtime on orders), my rating saved, a points balance different from the one seen at the last read. No timer.
  One load at a time; any events during a load → exactly one more load after it; a failed / never-answered load frees the loader (15 s).
  Core `loadPoints`: each call numbered, a reply older than the newest call is ignored (returns null = not applied).
- UAT008 (customer): the voucher celebration needs NEW 'earn' or 'reward' ledger rows (id above the last id seen, per user on this
  device) that make the balance cross a voucher step. First read only sets the marks; 'return' / 'spend' never celebrate; reopening
  or reloading never repeats it. If the balance arrives before its history, the history is read first.
- UAT012 (customer receipt of a cancelled / rejected order, block «Итог по заказу»): wallet return shown only with
  wallet_returned_at, points return only with points_returned_at (both written by the return triggers with the return entry), amounts
  = what was really used; otherwise «возврат … не подтверждён»; nothing shown for a part not used. Cash: only cash_collected,
  otherwise «Наличные X TJS: получение не записано». Card: «данных о списании нет». Support refunds (wallet 'refund' entries of the
  order) are their own line. The rejected-order card no longer says «already returned». Total label «Сумма заказа».
  Restaurant order sheet of a cancelled / rejected order: commission «не начисляется — заказ не выполнен», no deductions, no net.
- UAT013 (restaurant): «Отклонено» and «Отменено» counted and labelled separately by status, with the note that these are statuses,
  not a rating of the restaurant; history pills use neutral «Отклонено» / «Отменено» (the shared label «Отклонён рестораном» names an
  executor the status alone does not prove). Reason = the recorded code only, else «причина не указана» (free text never used as the reason).
- UAT014 (restaurant): «После комиссии» → «Чистыми к получению» / «Net payable to you», with the breakdown revenue − commission −
  customer points − cashback − delivery paid by you = net. Same formula (merchant_stats_check unchanged).
- UAT015 (customer): wallet «Обычно {n} баллов за 1 TJS — в некоторых заведениях своя ставка» ({n} from the setting); pay page and
  store page show points / cashback as «≈» with «Ориентировочно: начисляются при доставке по ставке заведения на тот момент».
- UAT011: not changed (returned points get a new lot now + 90 days, live). Owner decision pending.

Checks (Chromium): tools/uat3_check.py 52/52; merchant_stats_check 0 fails; qa_all customer + merchant; smoke (core changed) 0 errors;
flow_check 0 fails; ui_rules 0 fails.
