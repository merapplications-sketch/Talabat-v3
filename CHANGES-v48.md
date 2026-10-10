# v48 — happy hour paid by the restaurant (patch 31) + security test uses an orderable dish

Owner decisions (10 Oct): cashback stays off until switched on in the admin; the happy-hour discount is paid by the
RESTAURANT, like its own offers; the iPhone "wider than the screen" issue is gone; patch 29 was run.

## Patch 31 (run after 30)
- `orders.discount` now holds the whole discount (restaurant / dish % or the happy hour, the best); revenue and commission
  are on what the customer pays. `orders.hh_discount` = how much of it came from the happy hour (receipts/reports).
- Points are earned on subtotal − discount − promo − points. What the customer pays is unchanged.
- Customer receipt: "Discount" = the restaurant's own part, "Happy hour −25%" its own row. Admin: "incl. happy hour".

## Security page (SC-48)
- The owner's run showed `last answer: {"ok":false,"error":"bad_options"}`: the page tested promo codes with a dish that
  has REQUIRED options and sent none, so the server stopped at "bad options" before looking at the code at all (no
  information about codes leaks there — not a hole, but the test proved nothing). The page now picks a dish without
  required options from an open restaurant.

## Tests
test_patch29 (with 30 + 31 after it) 40/40 (commission during the happy hour now 9.00 on 90 TJS), test_patch30 20/20,
test_patch28 15/15, loyalty_parity 200 carts 0 differences, qa_all 0, flow/cart/smoke 0.
