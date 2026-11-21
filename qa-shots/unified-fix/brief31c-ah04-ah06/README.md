# TALABOT — AH-04 / AH-05 / AH-06 delivery

Owner scope: [AH-04 / AH-05](https://github.com/merapplications-sketch/Talabat-v3/issues/48#issuecomment-7059918161) and [AH-06](https://github.com/merapplications-sketch/Talabat-v3/issues/48#issuecomment-7060033452).

**Tested code SHA:** `b026f439224018b35333fd963e72452484e74dd2`  
**Review branch:** `review/unified-fix-brief15-20261117`  
**Date:** 2026-11-21. **No deployment.**

## Separate product commits

| Item | Commit | Delivered behavior |
| --- | --- | --- |
| AH-04 | [59efe197](https://github.com/merapplications-sketch/Talabat-v3/commit/59efe1975a95b51eeabb2c78a616dddbb4dd5c0e) | Home logo is 36px high with proportional automatic width. Its own grid row accommodates the image; controls and horizontal spacing retain their existing geometry. |
| AH-05 | [4408b491](https://github.com/merapplications-sketch/Talabat-v3/commit/4408b49196f1c7f309b35e166c370194f4969457) | Localized 44px artwork inside a white pill, radius 20px, padding 12px 20px, subtle shadow. Auth/loading hosts in all four apps and dark staff navigation are covered. Loading logo itself is centered on a neutral background. |
| AH-06 | [90881df7](https://github.com/merapplications-sketch/Talabat-v3/commit/90881df7446d9aa12f78d051c99fdc515c925308) | Login stories with progress, swipe, pause/resume, five-second default and managed timing; localized imagery/copy/CTA; original auth card inside a white sheet with 28px top corners. AF-01 gains the explicit login placement and localized editor fields. |

The original `talabat-core.js`, driver operational module, and owner logo files remain byte-identical. The driver’s white operational header retains its earlier 21.8px logo geometry. Original auth input nodes, attributes, values and handlers are preserved during story/feed/language changes. Private links are released only by the existing successful application callbacks after role and driver approval gates, with current-banner and safe-URL revalidation.

## Public feed connection state

The optional public AF-01 provider is **not connected** in this delivery, as allowed by the owner’s fallback requirement. Without it, the three localized defaults use existing scooter, hamburger and DineOut artwork. A successfully connected feed with no eligible ads shows a neutral scene; it does not resurrect fallback offers. Managed ads require explicit `login` placement, a valid HTTP(S) link and an image, and honor active dates and sorting.

Administration includes `Вход / Login`, per-language imagery, headline, subtitle, button label, access timing and the login interval. The existing schema-capability and settings-key gates remain in place: unavailable backend controls remain disabled; the login interval defaults to five seconds. No anonymous grants, database migration, production request, or live setting write was added. The public provider contract is documented in [brief31-banner-system.md](../../../sql/proposed/brief31-banner-system.md).

Customer fallback buttons wait for customer sign-in, then open the existing free-delivery, Happy Hours and DineOut views. In driver, merchant and admin entry screens, fallback buttons explicitly say “Open customer app” and explain that a customer account is required. They open that public entry page immediately, retaining the separate role-specific sessions. Configured banners keep their own public/after-auth access choice.

## Verification on the same code SHA

| Gate | Result | Evidence |
| --- | --- | --- |
| Home | **success**; 776 assertions; 52 cases; 8 viewport screenshots; Home smoke and financial parity passed | [Run 44889672843](https://github.com/merapplications-sketch/Talabat-v3/actions/runs/44889672843), job 136802550411, attempt 1 |
| H-01 | **success**; real LOCAL authentication **24/24** | [Run 44889672744](https://github.com/merapplications-sketch/Talabat-v3/actions/runs/44889672744), job 136802549845, attempt 1 |

The final CI compatibility fix changes only one rendered-text assertion: it trims the surrounding whitespace that CI WebKit adds after the CTA’s SVG arrow. The checked label, original auth behavior, transport guards and product files are unchanged.

The gallery below was captured in offline WebKit 26.5 at native CSS viewport size. Its 21 recorded product hashes match the tested code SHA exactly; see [delivery-verification.json](delivery-verification.json). Full local checks are retained in [local-acceptance.json](local-acceptance.json), and the independent approved-baseline comparison is in [home-financial-parity.json](home-financial-parity.json). Local capture provenance retains its original commit and harness hashes; it is not relabeled as a CI capture. Actual CI output is attached to the Home run above. Physical-device and production tests were not performed.

Coverage includes original sign-in/sign-up and confirmation/back, short-screen submit stability, loading failure controls, locale changes without field loss, interval boundaries, swipe/multi-pointer/reduced-motion behavior, maximum-length managed copy, empty/error/expired feed handling, denied-role and failed-login deferral, logout/re-entry readiness, staff customer-entry links, and all three customer destinations. Expected image cancellations are recorded separately only after a requested exact destination has loaded; runtime, HTTP, script/style and unexpected transport failures remain fatal.

## Required screenshots

| Screen | RU / 375 × 812 | EN / 390 × 844 |
| --- | --- | --- |
| Home header | [RU Home](ru-375-home-logo.webp) | [EN Home](en-390-home-logo.webp) |
| Login, first story | [RU first](ru-375-login-story-1.webp) | [EN first](en-390-login-story-1.webp) |
| Login, second story | [RU second](ru-375-login-story-2.webp) | [EN second](en-390-login-story-2.webp) |
| Loading | [RU loading](ru-375-loading.webp) | [EN loading](en-390-loading.webp) |

H-01’s eight authenticated original-app screenshots are preserved in [../h01](../h01), including the automatic evidence commit [91474c06](https://github.com/merapplications-sketch/Talabat-v3/commit/91474c06c0ae0c733388ea0d1e9c83544c0a6645). This delivery’s evidence commit changes only files below `qa-shots/`.
