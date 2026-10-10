# v49 — points discount paid by the restaurant (owner decision); patch 27 missing in the live DB

Owner decisions (10 Oct, final): earn 10 points / 1 TJS; 1000 points = 1 TJS; minimum 1000; points expire;
cashback off until switched on in the admin; points discount AND happy hour are a marketing cost of the
restaurant; the app commission is its usual % and is NOT reduced by the points discount.

- No SQL needed for this: the commission was already calculated before the points (on subtotal − discount).
- Restaurant app: order detail shows "Customer points (paid by the restaurant) −X" and the net payout subtracts it;
  analytics "after commission" subtracts the points too; a note shows how much of the discount was the happy hour.
- Admin: order detail marks points as "paid by the restaurant"; Loyalty tab explains the rule.
- Security check result (owner, SC-48): OK 126 passed, 2 warnings — `brands` / `brand_stats` missing:
  sql/schema_patch27.sql (restaurant branches) was NOT applied in Supabase; owner asked to run it.
