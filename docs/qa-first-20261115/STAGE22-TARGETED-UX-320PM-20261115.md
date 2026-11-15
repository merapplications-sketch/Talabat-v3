# TALABOT Stage22 — PM 320px Targeted UX Evidence / CONDITIONAL

**Scope:** Existing [Stage22 Issue #48](https://github.com/merapplications-sketch/Talabat-v3/issues/48) only. No new phase, no launch claim, no owner-device request.  
**Target:** Existing *synthetic-only, already published* customer demo `https://talabot-safari-demo-20261115.pages.dev/`.  
**Actual NEW executable QA SHA:** [`184c7d4f3a340642bacc7f4dcf91de3fc0dee300`](https://github.com/merapplications-sketch/Talabat-v3/commit/184c7d4f3a340642bacc7f4dcf91de3fc0dee300), on isolated `review/stage22-one-shot-qa-20261115`.  
**Real run:** [GitHub Actions `43719066978`](https://github.com/merapplications-sketch/Talabat-v3/actions/runs/43719066978), completed **SUCCESS**. *A passing test runner means the specifically requested evidence was captured; it does NOT mean all UX is accepted.*  
**Downloadable evidence:** [Actions artifact `14162949755`](https://github.com/merapplications-sketch/Talabat-v3/actions/runs/43719066978/artifacts/14162949755), `talabot-stage22-targeted-ux-synthetic-only`, 541,037 bytes (expires 2026-11-16 13:27:36 UTC). Actual ZIP SHA256: `179f88419cf53f2e50392a8cb9ee9e99de96970c7450de9cc4bbd6b73679d20e`. **ZIP CRC 7/7 PASS**. Only fictitious demo screenshots/JSON/sanitized HAR; no account credentials or real patient/customer data.

## Why the narrow run was justified

The [independent designer conditional review](https://github.com/merapplications-sketch/Talabat-v3/issues/48#issuecomment-6894916602) explicitly acknowledged no new rendered GUI inspection and classified UI labels / literal-template paths as P2 or UNTESTED. The owner-approved unified task requires finishing already-open work with the minimum isolated fix/testing, not repeating the passed security harness. This new run tested only **EN customization rendered at 320**, **Home/merchant image DOM mapping at 320**, **checkout fee and sticky CTA at 320**; it did **not** repeat the approved RU+EN 8/8 homepage smoke, no-real-order swipe, or any actual production request.

Workflow diff from previously approved PM QA checkpoint `5b14609f...` to *executed* `184c7d4f...`: **only** changed `.github/workflows/stage22-one-shot-qa-20261115.yml` and added `docs/qa-first-20261115/stage22_targeted_ux.py`; **no** app/source/static ZIP, approved design, business logic, `main`, Cloudflare/Supabase, old pilot, real transactions, deployment, secrets, or paid plan changed. Standard `ubuntu-24.04` runner, read-only GitHub checkout and exact-host browser allowlist installed **before first navigation**; 1-day synthetic-only evidence retention.

## What was *actually* verified from the new original artifacts

PM downloaded ZIP and independently checked CRC, JSON, HAR, and opened real unchanged screenshots `customization-en-320.png`, `merchant-en-320.png`, `home-en-320.png`, `checkout-en-320-fee.png`. HAR **38 entries = 38 same-origin GET / HTTP 200**, no POST, no off-origin request, no WebSocket attempt, no page errors in this **specific synthetic UI run**. HAR SHA256 `cdd140952db8e45f2c76ce1f1c31de164640ccd3dbe34b817d57fc5ec0e5631e`, cookies/auth/postData sanitized. This was **not** a standalone re-proof of deliberate off-host blocking, which was proven in accepted previous [Actions #43694105608](https://github.com/merapplications-sketch/Talabat-v3/actions/runs/43694105608).

**P2 UX22-L: CONFIRMED RENDERED EN/320.** Original 320px Playwright screenshot from real Pages origin visibly mixes English interface controls (*Required, Special requests, Add to cart*) with Russian **choice-control labels** `Размер порции (обязательно выбрать)`, `Добавки`, `Маленький`, `Средний`, `Большой`, `Сыр`, `Бекон`, `Халапеньо`, `Соус`. These are *UI control group names and option values*, not legitimate Russian merchant proper nouns. **This is now a proven P2 English demo-localization defect**, not an assumption. **No translated fake catalog, source or deployed page has been modified.** Scoped copy correction in isolated fixture/UI boundary only, preserving original RU strings, item IDs, fees/discounts and approved Direction A, is the minimal candidate to evaluate.

**P2 UX22-I: NETWORK INVALID URL PATTERN CONFIRMED, visible broken image NOT reproduced on tested screens.** HAR reveals **8 distinct** literal `/$%7B...%7D` first-party GETs returning HTML 200 (image-looking requests), e.g. `/$%7Besc(st.cover_url)%7D`; source contains JavaScript templates `<img src="${...}">`. Actual browser DOM images inspected after genuine render: Home **29/29** and merchant/menu **19/19** visible image nodes have `naturalWidth>0`. New screenshots show actual category/restaurant food art loaded. Do NOT label all image assets broken, nor silently replace approved visuals. Path/MIME anomaly is a documented P2 asset-loading hygiene risk; which parser/preloader initiates literal paths and whether other untested app screens visually break remain **UNTESTED**. No visible P1 image regression proved.

**320px checkout fees and sticky payment CTA — PASS for *tested exact scenario*.** Fake 2-unit cart rendered original **30 − 4.5 − 3 + delivery 10 = 32.5 TJS**; the screenshot at 320px shows the delivery 10 TJS row, total 32.5, and orange `Slide to place order` action anchored at bottom. Actual measured scroll reached bottom (`scrollTop=679; scrollMax=679`); delivery row center was inside viewport and **outside the sticky dock** (`centerInDock:false`). Sticky dock top=738/bottom=844, height=106, CTA center hit-test reaches the nested SVG `path` inside the actual button (not a blocked underlying page control). No document horizontal overflow (320/320). **Do not extrapolate** this one English fixture to every modal/long name or actual production Safari.

**320px customization scroll — PASS for geometry, separate from localization FAIL.** Real option scroll area client 456px/full 583px; fixed add-to-cart footer at top=772/bottom=844; area ends at 748px, avoiding footer overlap in this captured screenshot. Original screenshot confirms options/chips and fixed disabled Add-to-cart when required size unselected; no hidden action due to footer. Long sample product name wraps. **Merchant name at 320** is a 77-character fictional Russian name shown truncated on merchant header and food cards; screenshot-level P2 content discoverability requires designer judgement, not automatic style change.

**Unchanged:** historic owner-deferred demo-banner contrast ~3.54:1 below AA normal text, approved original Home B, Restaurant Legacy Premium v1.6, Customization Direction A, DineOut Gold, Admin Template B and financial rules. No production release permission or color/design change.

### Evidence file hashes (SHA256)

| Evidence | Exact hash |
|---|---|
| `customization-en-320.png` | `22c72c34a7b605c180576befda9c4ee2d9b6a0764c98edf8bfbe4de3b137a260` |
| `checkout-en-320-fee.png` | `a7bd3b84a83eea70e80edee296ee217f097b24c3152e38144ceee9c62e23851f` |
| `merchant-en-320.png` | `c28d682b52747b29f76b7c3a16cabd8a6b78af3d9cdad57047bc5c904678d3ae` |
| `home-en-320.png` | `97ad1a684b74e03ee7b34b5e4fea334fe778f378f709bece47bb6f4b9e5cab2a` |
| `targeted-ux-evidence.json` | `19f32ad4bd824c7e4da27ef28aea3c5d05034f257b6cc6b85db3da6d3a8f7575` |
| `targeted-ux-redacted.har` | `cdd140952db8e45f2c76ce1f1c31de164640ccd3dbe34b817d57fc5ec0e5631e` |

## Manager decision / next internal Stage22 action

**Status: SECURITY ACCEPTED in bounded synthetic scope; UX CONDITIONAL. NOT final Stage22 GO.** Exact new EN 320 fixture proves P2 untranslated controls; image-template network issue P2 with tested Home/menu visual breakage **NOT** reproduced; 320 checkout fee/CTA is **PASS** for tested screen. Under existing approved unified assignment, designer/programmer should address only the proven EN fixture localization issue in an isolated candidate (copy labels only, no change to original brand/financial/business/permissions or production), and explain the image-template network anomaly without replacing approved imagery. Independent UX must then confirm these bounded findings and PM must decide acceptance in existing #48. If releasing revised public demo is ever proposed, request the *separate explicit publication authorization*; current hosted preview remains unchanged. Existing Stage22 security evidence is preserved without rerun.

**Not independently proven yet:** manual RU saved-language preference after reload without query overrides; every hidden/disabled modal hitbox; all home/menu images/long names in every viewport; any real TALABOT full E2E. Formal C-01/G1/release/PHASE2 stay **NO-GO**.

**Do not send the owner routine partial statuses, open new stages/issues, or claim a GitHub comment automatically awakens paused Work chats.** This is a durable internal QA handoff for the one unified Stage22 task.