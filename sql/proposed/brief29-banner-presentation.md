# BRIEF-29 banner presentation proposal

The existing banners API reads complete rows. A future schema change would add an optional JSON object named `presentation` to `banners`, subject to the existing banner management authorization. No migration accompanies this proposal.

| Key | Values |
|---|---|
| action | order, restaurant, list, campaign, or empty for the existing link |
| label | Object with optional ru and en strings, at most 40 characters each |
| item_id | Optional ID of a published dish in the linked store for order |
| filter | category, free, or disc for list |
| campaign | happy, discount, or free for campaign |
| audience | home (default) or orders |

Continue using the existing link fields for store and category targets. Validate the action target and language labels on the server when the field is enabled. Existing banner dates govern timed campaigns. The admin only sends the new key when the API exposes it on a banner row, so the existing interface remains usable during rollout.

A future server change should expose numeric app setting `orders_banner_mode` (0 shares Home, 1 uses the separate orders collection), and authorize content managers to write it through the settings RPC. Legacy installations default to 0 and do not send a write for the unexposed setting. Checkout and Home never include orders-only banners.
