# AI-01b — exact artwork provenance

Accepted base: `7cc3136280b491cf23c4bf7e8f723d48ccfb10ce`.

## Owner instructions

- [AI-01b — reuse the existing photographic banner artwork](https://github.com/merapplications-sketch/Talabat-v3/issues/48#issuecomment-7063613993): delivery scooter, large burger and localized DineOut; CSS `cover`; AI-02 through AI-07 remain accepted.
- [AI-01 correction](https://github.com/merapplications-sketch/Talabat-v3/issues/48#issuecomment-7063632254): the white sheet has a straight top between its 32px upper corners and a light upward shadow.
- [Original localized DineOut instruction](https://github.com/merapplications-sketch/Talabat-v3/issues/48#issuecomment-7052345068): use the supplied RU/EN files; TG uses RU until a TG original is supplied.
- [BRIEF-28 visual reference instruction](https://github.com/merapplications-sketch/Talabat-v3/issues/48#issuecomment-7037912295): the reference uses the live pizza, scooter and burger artwork.

## Original files and exact copies

The two PNG originals were recovered from the user's saved generated artwork. Their recovered filenames are `Emerald scooter, free delivery.png` and `Burnt orange burger of the day.png`. Each application PNG was compared directly with its recovered source and is byte-for-byte identical. No cropping, resizing, re-encoding, recolouring or image regeneration was performed.

| Application path | Dimensions | Bytes | SHA256 |
| --- | --- | ---: | --- |
| [assets/shared/login-free-delivery-ai01b.png](../../../../assets/shared/login-free-delivery-ai01b.png) | 1514×1039 | 1,862,487 | `6a9ca929a0abec75ed9aacd7082c59cbb21d6d6a14470837ce73238b1a5dd009` |
| [assets/shared/login-burger-ai01b.png](../../../../assets/shared/login-burger-ai01b.png) | 1298×1212 | 2,184,932 | `1869136642bdbb3597682b6ee1e6f61f1096d3229918c3fcc1fb7dc5fff2a928` |
| [assets/customer-c/dineout-header-ru.webp](../../../../assets/customer-c/dineout-header-ru.webp) | 1200×400 | 127,802 | `6d17335f4cb7b5cd219a2dc7bd710c0be873108c3070b7807595028b0efc4c09` |
| [assets/customer-c/dineout-header-en.webp](../../../../assets/customer-c/dineout-header-en.webp) | 1200×400 | 121,714 | `345da3771866be9d6207b2a4fa97540aebb2d6ccf53e7d4414e8214434ec0d9a` |

The existing DineOut files remain unchanged. Both were verified byte-for-byte against the owner originals in commit `3032c7cb2bacc8cad43e0f5d098a31d20ac3d486`, under `mockups-20261120/`: [RU original](https://github.com/merapplications-sketch/Talabat-v3/blob/3032c7cb2bacc8cad43e0f5d098a31d20ac3d486/mockups-20261120/dineout-header-ru.webp) and [EN original](https://github.com/merapplications-sketch/Talabat-v3/blob/3032c7cb2bacc8cad43e0f5d098a31d20ac3d486/mockups-20261120/dineout-header-en.webp). They also match those files in owner commit `991e86727a307564e08c36be5360b89300e2bbdd`. EN selects EN artwork; RU and TG select RU artwork.

## Immutable visual reference

[BRIEF-28 RU/375 screenshot](https://github.com/merapplications-sketch/Talabat-v3/blob/bfc9acebe884d44cde303dcccbcdf847ada3b398/qa-shots/unified-fix/brief28/ru-375.webp), commit `bfc9acebe884d44cde303dcccbcdf847ada3b398`, is 40,442 bytes with SHA256 `27abdfba774ac9b34e295e8f4b3b8468a4661f75b6ec2228fb9a9f388a0fd070`.

Independent visual comparison confirmed the same emerald background, orange scooter, cream delivery box and «Доставка бесплатно»; and the same burnt-orange background, large burger, «Бургер дня» and printed «В меню →». The reference proves visual correspondence; the full original PNGs above supply the application bytes. No screenshot crop is used as an application asset.

## Display treatment and scope

The login fallback uses CSS `object-fit: cover`. Delivery and DineOut use `object-position: right center` to retain the scooter and steak/cloche focal areas; the burger uses `center`. This changes browser framing only. Portrait cover necessarily crops a wide source; the existing localized login copy remains responsible for readable interface text.

This file records artwork provenance only. Runtime acceptance and final CI results belong in the delivery acceptance report. No SQL, schema/data mutations, production writes or deployment were performed for this artwork correction.
