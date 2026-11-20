# BRIEF-31 — optional banner presentation contract (proposal only)

No SQL or migration is included or executed. The unchanged core's existing banner and store update methods carry optional fields only after the client observes them in returned data. Server permissions continue to decide whether writes succeed.

## Unified banner row

Keep existing `title`, `image_url`, `link_type`, `link_value`, `sort`, `is_active`, `starts_at`, `ends_at`. Existing `presentation` JSONB, proposed by BRIEF-29, receives:

| Field | Meaning |
| --- | --- |
| `placements` | Unique selection of `home_main`, `home_side`, `dont_miss`, `home_bottom`, `orders`, `restaurants`, `checkout`. Empty selection shows nowhere; the editor requires at least one placement. |
| `images` | Optional `ru`, `en`, `tg` image URLs. A missing locale uses the main `image_url`. |
| `label` | Optional RU/EN/TG button text, maximum40 characters. Empty or missing locale text renders no overlaid button; the whole banner stays clickable. |
| `action` | Existing AC-03 `order`, `restaurant`, `list`, `campaign`, or `link`. Missing action retains the legacy target. |
| `item_id`, `filter`, `campaign` | Existing AC-03 destination details. |
| `url` | Absolute HTTP(S) destination for `link`; credentials and non-HTTP protocols are rejected. |

`presentation.audience` and the old orders collection selector are superseded when `placements` exists. Without it, the customer maps existing placement/audience and orders_banner_mode to equivalent views. Existing dates and sort remain authoritative. Current database placement is still only `top`/`bottom`; no unsupported placement string is submitted through core.

The optional controls remain disabled when no returned row contains `presentation`. An optional numeric settings capability `banner_presentation_ready=1` can advertise a migrated empty table. It must only be supplied by an approved backend change. Legacy main image, title, target, order and dates remain editable without presentation.

## Expiry and per-placement timing

The existing `ends_at` timestamptz is the banner's exact end date/time, entered and displayed in Asia/Dushanbe(UTC+05:00). No inferred happy-hour end is copied onto an unrelated banner. At the deadline the banner is removed.

Optional numeric settings keys `banner_rotation_<placement>_seconds` are one value per allowed placement,1–60seconds, default3seconds. The editor writes only a key already returned by `TLB.settings()`, using existing `set_setting`; it never creates schema or config keys silently.

## Sponsored taste dishes

Reuse the existing optional store field `home_sponsored_dishes` from W-09: ordered entries `{item_id, rank}`. The same promoted eligible dishes lead the taste section and carry the existing advertising badge. The admin editor uses existing `updateStore` only for stores whose returned record contains the field. Automatic meal filling excludes drinks, extras and sauces and keeps existing item/store availability and pricing rules.

## Backend activation, separate approval

If not present, enabling these fields needs an approved migration and the normal staff/content write and customer read policies. None is added here. A request error must retain the draft; field presence is not proof of a successful save. Synthetic fixture tests demonstrate the connected-field and missing-field contracts; they are not evidence that production schema has been activated.
