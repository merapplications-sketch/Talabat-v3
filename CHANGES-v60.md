# v60 (prepared, NOT applied) — delivery proof, support refunds, courier cash receipts
Branch `prep/batch3-v60` from `fix/uat3-v59` (v59b unchanged). Details, alternatives and decisions: BATCH3-PLAN.md.
- SQL patch 37 + rollback (live definitions) + tests on isolated stand-in data; races with two real sessions.
- core: errors photo_missing / order_not_finished / amount_too_high / nothing_due; refundRoom breakdown; receiveCash, cashReceipts,
  orderWallet (wallet entries of one order, existing RLS).
- customer: receipt reads the refunds of THIS order (no 60-operation limit); a failed read says «not checked».
- admin: refund maximum with its breakdown; courier card: receive any amount (form key, reference, note) + history.
- courier: photo_missing → message, photo again.
Checks (local / Chromium): test_patch37 53/53; patch37_race 12/12 (gaps shown on the live functions, closed by the patch);
patch37_ui_check 15/15; uat3_check 70/70 (UAT012 checks adapted to the per-order read); smoke; flow; courier; ui_rules; qa_all customer / admin / driver.
