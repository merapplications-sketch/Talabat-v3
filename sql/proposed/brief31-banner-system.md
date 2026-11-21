# BRIEF-31 — optional banner presentation contract (proposal only)

No SQL or migration is included or executed. The unchanged core's existing banner and store update methods carry optional fields only after the client observes them in returned data. Server permissions continue to decide whether writes succeed.

## Unified banner row

Keep existing `title`, `image_url`, `link_type`, `link_value`, `sort`, `is_active`, `starts_at`, `ends_at`. Existing `presentation` JSONB, proposed by BRIEF-29, receives:

| Field | Meaning |
| --- | --- |
| `placements` | Unique selection of `home_main`, `home_side`, `dont_miss`, `home_bottom`, `orders`, `restaurants`, `checkout`, `login`. The admin label for `login` is `Вход / Login`. Empty selection shows nowhere; the editor requires at least one placement. |
| `images` | Optional `ru`, `en`, `tg` image URLs. A missing locale uses the main `image_url`. |
| `headline` | Optional RU/EN/TG text, trimmed to 80 characters. A missing or blank locale uses the existing row `title`, also limited to 80 characters. |
| `subtitle` | Optional RU/EN/TG text, trimmed to 160 characters. A missing or blank locale shows no subtitle. |
| `label` | Optional RU/EN/TG button text, maximum 40 characters. Empty or missing locale text renders no overlaid button; the whole banner stays clickable. On the login placement, an empty or missing label instead uses the localized default, `View` in EN and `Смотреть` in RU. |
| `login_access` | `public` opens the destination before sign-in; `after_auth` defers the destination until the application confirms successful sign-in. Missing or invalid values default to `after_auth`. This controls link timing, not data permissions. |
| `action` | Existing AC-03 `order`, `restaurant`, `list`, `campaign`, or `link`. Missing action retains the legacy target. |
| `item_id`, `filter`, `campaign` | Existing AC-03 destination details. |
| `url` | Absolute HTTP(S) destination for `link`; credentials and non-HTTP protocols are rejected. |

`presentation.audience` and the old orders collection selector are superseded when `placements` exists. Without it, the customer maps existing placement/audience and orders_banner_mode to equivalent views. Existing dates and sort remain authoritative. Current database placement is still only `top`/`bottom`; no unsupported placement string is submitted through core.

A row selected for `login` must use `action: "link"` and a valid absolute HTTP(S) `url` without credentials. Create and update validation both retain the draft and stop the write if this requirement is not met. Existing action behavior for other placements is unchanged. Legacy rows are not implicitly assigned to the login placement.

The optional controls remain disabled when no returned row contains `presentation`. An optional numeric settings capability `banner_presentation_ready=1` can advertise a migrated empty table. It must only be supplied by an approved backend change. Legacy main image, title, target, order and dates remain editable without presentation.

## Expiry and per-placement timing

The existing `ends_at` timestamptz is the banner's exact end date/time, entered and displayed in Asia/Dushanbe(UTC+05:00). No inferred happy-hour end is copied onto an unrelated banner. At the deadline the banner is removed.

Optional numeric settings keys `banner_rotation_<placement>_seconds` are one value per allowed placement, 1–60 seconds. `banner_rotation_login_seconds` defaults to 5 seconds; the other placements retain their 3-second default. The admin editor accepts integers only and writes only a key already returned by `TLB.settings()`, using existing `set_setting`; it never creates schema or config keys silently.

## AH-06 login provider (optional, before authentication)

The shared banner helpers expose `headline(row, language)`, `subtitle(row, language)`, and `loginAccess(row)` alongside the existing image, label, placement, eligibility and timing helpers. They do not fetch data or change authentication. The four applications can consume the same login presentation contract through the optional frontend provider:

```js
window.TALABOT_LOGIN_BANNERS.connect(async ({signal}) => ({
  version: 1,
  banners: [],
  settings: {banner_rotation_login_seconds: 5}
}));
```

The provider returns public promotional rows using the unified banner shape and only the settings needed for the login presentation. It should honor the supplied abort signal. Login display uses the explicit `login` placement and the existing active, start/end date and sort rules. The `login_access` value determines whether a valid link opens immediately or waits for the application's successful sign-in callback; it does not make authenticated records public.

With no provider connected, the login presentation uses the three approved local fallback slides: free delivery, happy hours and DineOut. A connected provider that returns an empty banner list produces a neutral presentation, without fallback promotional offers.

Customer fallback buttons wait for successful customer sign-in, then open the existing customer views. In the driver, merchant and admin login screens, those same fallback buttons explicitly say “Open customer app” and open its public entry page immediately, with localized copy explaining that offers require a customer account. This avoids asking for an operational sign-in before opening a separate customer session. It does not grant access to offers or alter role-specific authentication. Connected banners continue to honor their configured `login_access` unchanged.

This is an integration contract, not a connected pre-authentication backend. Existing authenticated `TLB.banners()` / `TLB.settings()` loads are not a public provider. No anonymous grants, endpoint, SQL migration, credentials or core authentication changes are included. Supplying real public data requires a separately approved backend integration.

## Sponsored taste dishes

Reuse the existing optional store field `home_sponsored_dishes` from W-09: ordered entries `{item_id, rank}`. The same promoted eligible dishes lead the taste section and carry the existing advertising badge. The admin editor uses existing `updateStore` only for stores whose returned record contains the field. Automatic meal filling excludes drinks, extras and sauces and keeps existing item/store availability and pricing rules.

## Backend activation, separate approval

If not present, enabling these fields needs an approved migration and the normal staff/content write and customer read policies. None is added here. A request error must retain the draft; field presence is not proof of a successful save. Synthetic fixture tests demonstrate the connected-field and missing-field contracts; they are not evidence that production schema has been activated.
