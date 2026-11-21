# BRIEF32 · AI-01 login stories

## Delivered scope

AI-01 implements the login presentation requested in owner comments `7061725687` and `7061808632`. Product changes are confined to `assets/shared/login-banners-ah06.js` and `assets/shared/login-banners-ah06.css`.

The existing artwork now fills the upper story frame with `object-fit: cover` and a dark gradient. The foreground has a large white headline, white subtitle and compact dark CTA. Default CTA labels are `Смотреть`, `View` and `Дидан`; a connected banner's configured label still takes precedence. The upper edge has only story progress bars. Previous/next arrows, pause button and numeric story count are removed from the DOM. Transparent, labelled edge buttons and horizontal swipes navigate the stories; holding a pointer still pauses autoplay. Reduced motion disables autoplay and slide transitions.

The original white auth card now has a broad upward arc and a light upward shadow. Its existing fields, IDs, handlers and form controls remain the original core nodes. Brand artwork, pill helper and logo dimensions are unchanged. The public/deferred CTA contract, role checks, original successful app-callback readiness, keyboard layout latch and provider API are unchanged. Staff fallback subtitles still explain that offers open in the customer app and require a customer account.

No core, backend, SQL, shared banner/countdown, app HTML, image asset, build workflow or authentication implementation was edited for this item. No deployment was performed.

## Artwork provenance

The source images are existing repository artwork. Their exact bytes match base commit `99db45a7f713615468e7ce9f2cb3c5493826a4e3`; see [artwork-audit.json](artwork-audit.json) for SHA-256 and byte comparisons.

| Story | Existing source | Source size | Presentation |
|---|---|---:|---|
| Free delivery | `assets/3d/motor-scooter.webp` | 256 × 256 | Full story cover over the ink surface |
| Happy Hours | `assets/3d/hamburger.webp` | 256 × 256 | Full story cover over the ink surface |
| DineOut, RU/TG | `assets/customer-c/dineout-header-ru.webp` | 1200 × 400 | Full cover, right crop showing the food and cloche |
| DineOut, EN | `assets/customer-c/dineout-header-en.webp` | 1200 × 400 | Full cover, right crop showing the food and cloche |

The 256 px artwork is scaled to fill the frame; these are reused supplied illustrations, not new high-resolution photographs. No raster art was generated, redrawn, recolored, composited or replaced. DineOut's source text can be cropped by the portrait cover; the separate localized headline remains readable. Managed-banner maximum-copy screenshots use the existing offline QA photo fixture and are distinguished by their filenames.

## Verification

**Final focused result: 452 passing assertions, 0 failures, 14 actual viewport screenshots.** [results.json](results.json) records all checks, request/auth traces, source hashes, screenshot hashes and runtime versions. [run.log](run.log) records the case results. Playwright `1.62.0`, WebKit `26.5`.

The final run used the original four app HTML files with the existing offline SDK harness. It covered RU 375 × 812 and EN 390 × 844 for customer, driver, merchant and admin, plus the existing 560 px short-viewport signup interaction. Checks include:

- Three real default stories, full-frame image geometry, top bars only, no old arrow/pause/count controls, readable white copy and unobstructed compact CTA.
- Broad white arc verified by center/corner hit tests, overlap and upward shadow; approved logo pill and original core form node/attribute identity.
- Right/left edge taps, a real pointer swipe, pointer hold, five-second default timing, seven-second configured timing, and reduced-motion manual navigation.
- Managed maximum-length headline/subtitle/CTA values of 80/160/40 characters, horizontal overflow, CTA hit target and connected-empty neutral state. Existing line limits can visually truncate long copy while preserving the full DOM text.
- Original password visibility, retained input focus and typed values, failed sign-in error, exactly one sign-in request from Enter, reachable signup submission at short height, and original confirmation/back behavior.
- Public CTA navigation without sign-in, deferred CTA remaining at login after a failed sign-in, and release only after a real successful synthetic SDK sign-in traverses the original core/app callback.
- No unexpected external requests, runtime errors or local transport/HTTP failures in the tested flows.
- Byte preservation of all four app HTML files, `talabat-core.js`, shared brand/banner helpers and both owner logo files against the isolated base.

[red-results.json](red-results.json) preserves the pre-change smoke failure: the old presentation had three bars plus five matched visible-control/count nodes where the new contract requires three bars and zero old controls. The final evidence above was produced after the implementation and after the harness import flag was added.

This is offline WebKit evidence using a synthetic SDK; it is not a production account/database test or a physical-phone test. The results record the pre-commit base HEAD and the actual modified product/harness SHA-256 values; the source hashes, rather than that base HEAD alone, identify the tested implementation. The product source remained unchanged during the run.

### Reproduce

From the repository root, with Playwright and a runnable WebKit installed:

```sh
PYTHONDONTWRITEBYTECODE=1 \
TALABOT_WEBKIT=/path/to/webkit \
python3 tools/brief32_login_webkit.py /tmp/brief32-ai01 --case all
```

The BRIEF32 master gate can import the focused runner and supply its unified source guard:

```python
from brief32_login_webkit import run_ai01
run_ai01(run, browser, server, photos, check_source=False)
```

`check_source` defaults to `True` for this isolated item. The master must use its own scoped guard because other authorized BRIEF32 items intentionally edit shared files. AI-01 defaults do not require a restaurant record, DineOut record or admin banner.

## Screenshots

All images below are viewport captures of the original app pages. They are not mockups.

| App / case | RU 375 | EN 390 |
|---|---|---|
| Customer · free delivery | [RU](ru-375-customer-login-story-1.webp) | [EN](en-390-customer-login-story-1.webp) |
| Customer · Happy Hours | [RU](ru-375-customer-login-story-2.webp) | [EN](en-390-customer-login-story-2.webp) |
| Customer · DineOut | [RU](ru-375-customer-login-story-3.webp) | [EN](en-390-customer-login-story-3.webp) |
| Driver · free delivery | [RU](ru-375-driver-login-story-1.webp) | [EN](en-390-driver-login-story-1.webp) |
| Merchant · free delivery | [RU](ru-375-merchant-login-story-1.webp) | [EN](en-390-merchant-login-story-1.webp) |
| Admin · free delivery | [RU](ru-375-admin-login-story-1.webp) | [EN](en-390-admin-login-story-1.webp) |
| Managed maximum copy | [RU](ru-375-customer-managed-maximum-copy.webp) | [EN](en-390-customer-managed-maximum-copy.webp) |
