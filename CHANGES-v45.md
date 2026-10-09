# v45 — promo-code guessing is really rate-limited (security fix)

Owner report from security-check: "Promo code guessing is rate-limited — 13 wrong codes were not blocked".

Cause: the check counted failed attempts, but a wrong code is answered with an error, and the error rolls back the
row that records the attempt — so the counter never grew.

Fix: `sql/schema_patch28.sql` (run once in the Supabase SQL Editor; safe to run again)
- the existing `check_promo` is kept unchanged as `check_promo_base` (all its rules stay the same);
- a new `check_promo` in front of it records every check in `promo_guess` outside the part that can fail;
- blocked with `too_many` after 10 wrong codes in 10 minutes, or 60 checks of any kind in 10 minutes;
- a real code below its minimum / already used is not a wrong guess (the cart re-checks it when it changes);
- errors that are not about the code (closed, unavailable ...) are unchanged and not counted;
- customers cannot call `check_promo_base` directly, cannot read `promo_guess`; anonymous users cannot call `check_promo`.
- The apps need no change (they already show "Too many attempts. Try again in 10 minutes").

Tests: `sql/test_patch28.sql` on an empty local PostgreSQL 16 with a stand-in of the old function that has the same bug:
bug reproduced before the patch, then 15/15 after it (blocked at the 11th wrong code, other users unaffected, valid code still
recorded for place_order, minimum-order answers not counted, 60-check cap, no bypass, unblocked after 10 minutes, patch run twice).
security-check.html: new row "The promo limit cannot be bypassed".
