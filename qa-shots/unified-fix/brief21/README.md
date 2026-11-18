# BRIEF-21 · customer review

[Owner 7:14 and candidate](owner-home-comparison.webp) · [Owner tracking reference and candidate](owner-tracking-comparison.webp) · [WebKit measurements](measurements.json)

## R-01 · repeat-order cards

The left, middle and right columns in each Home capture are the pinned 7c7e6609 source, the d8538a26 source and the candidate. All three run the same offline catalogue and order fixtures. The restaurant images come from the owner's approved screenshot. The broken-logo case returns HTTP 404 for the Romant logo and serves a valid cover for the same restaurant.

| Width | Valid photos | Broken logo with valid cover | Pinned width | Candidate width | Candidate photo |
|---:|---|---|---:|---:|---:|
| 375 | [Compare](home-ru-375-valid.webp) | [Compare](home-ru-375-retry.webp) | 112 | 152 | 152 × 100 |
| 390 | [Compare](home-en-390-valid.webp) | [Compare](home-en-390-retry.webp) | 112 | 152 | 152 × 100 |
| 430 | [Compare](home-en-430-valid.webp) | [Compare](home-en-430-retry.webp) | 112 | 152 | 152 × 100 |

The mobile stylesheet in both source revisions overrides the 152 × 100 inline design at viewport widths up to and including 430 px. Removing just the favourites overrides restores that inline design. **The candidate differs by 40 CSS pixels from the pinned mobile source. The requested ±2 px source-width gate is open.** The owner screenshot and the raw Git source give different mobile targets.

Both prior sources choose the logo when its URL is nonempty. On load failure the shared photo renderer removes the image without trying the cover. The candidate retrieves the stored restaurant by order store ID and retries its cover once. The happy path, 404 recovery and decoded widths are recorded in the measurements. The original device's failed image response is unavailable. Its precise cause remains unverified.

## R-02 · order tracking

Each comparison shows the original d8538a26 screen at left and the candidate at right. The cancellation fixture has a preparation event before cancellation and a late ready event after it. Rejection has no prior milestone history. The cash-shortfall fixture has an open payment support ticket while the order remains picked up.

| Order state | RU 375 | EN 390 | RU 320 | EN 320 |
|---|---|---|---|---|
| pending | [Compare](track-ru-375-pending.webp) | [Compare](track-en-390-pending.webp) | [Compare](track-ru-320-pending.webp) | [Compare](track-en-320-pending.webp) |
| preparing | [Compare](track-ru-375-preparing.webp) | [Compare](track-en-390-preparing.webp) | [Compare](track-ru-320-preparing.webp) | [Compare](track-en-320-preparing.webp) |
| ready | [Compare](track-ru-375-ready.webp) | [Compare](track-en-390-ready.webp) | [Compare](track-ru-320-ready.webp) | [Compare](track-en-320-ready.webp) |
| pickedup | [Compare](track-ru-375-pickedup.webp) | [Compare](track-en-390-pickedup.webp) | [Compare](track-ru-320-pickedup.webp) | [Compare](track-en-320-pickedup.webp) |
| delivered | [Compare](track-ru-375-delivered.webp) | [Compare](track-en-390-delivered.webp) | [Compare](track-ru-320-delivered.webp) | [Compare](track-en-320-delivered.webp) |
| cancelled | [Compare](track-ru-375-cancelled.webp) | [Compare](track-en-390-cancelled.webp) | [Compare](track-ru-320-cancelled.webp) | [Compare](track-en-320-cancelled.webp) |
| rejected | [Compare](track-ru-375-rejected.webp) | [Compare](track-en-390-rejected.webp) | [Compare](track-ru-320-rejected.webp) | [Compare](track-en-320-rejected.webp) |
| q14 | [Compare](track-ru-375-q14.webp) | [Compare](track-en-390-q14.webp) | [Compare](track-ru-320-q14.webp) | [Compare](track-en-320-q14.webp) |

## First screens

| Entry | RU 375 | EN 390 | EN 430 | RU 320 |
|---|---|---|---|---|
| customer-home | [Compare](first-customer-home-ru-375.webp) | [Compare](first-customer-home-en-390.webp) | [Compare](first-customer-home-en-430.webp) | [Compare](first-customer-home-ru-320.webp) |
| customer-restaurant | [Compare](first-customer-restaurant-ru-375.webp) | [Compare](first-customer-restaurant-en-390.webp) | [Compare](first-customer-restaurant-en-430.webp) | [Compare](first-customer-restaurant-ru-320.webp) |
| driver-first | [Compare](first-driver-first-ru-375.webp) | [Compare](first-driver-first-en-390.webp) | [Compare](first-driver-first-en-430.webp) | [Compare](first-driver-first-ru-320.webp) |
| merchant-first | [Compare](first-merchant-first-ru-375.webp) | [Compare](first-merchant-first-en-390.webp) | [Compare](first-merchant-first-en-430.webp) | [Compare](first-merchant-first-ru-320.webp) |
