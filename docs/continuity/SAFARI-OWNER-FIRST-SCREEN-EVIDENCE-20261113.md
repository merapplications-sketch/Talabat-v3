# TALABOT — Safari Owner First-Screen Observation / 2026-11-13

**Type:** USER-SUPPLIED IMAGE / OBSERVATION ONLY / NO LOGIN OR E2E  
**Continuity:** [OWNER-SAFARI-ZERO-COST-HANDOFF-20261113.md](OWNER-SAFARI-ZERO-COST-HANDOFF-20261113.md)  
**MASTER:** https://github.com/merapplications-sketch/Talabat-v3/issues/26  
**Original user attachment filename:** IMG_8277.jpeg (provided in the owner conversation; not uploaded as a GitHub binary in this record).  
**Original image SHA256:** `7e50b9fc3bb8415f257ccc8c7b657050c0992fefc4c9f7c3f4d2bccddfbc7cb8`  
**Image dimensions:** 1290 × 2796 px. This hash identifies the screenshot bytes in the originating chat only; it is **not** a GitHub-hosted screenshot or provider attestation.

## Observed directly in owner's iPhone Safari screenshot

- Safari bottom address bar visibly shows the **pilot-20261106.pages.dev** host (truncated in device UI); the earlier owner-opened URL was `https://talabot-pilot-20261106.pages.dev/customer.html`.
- A TALABOT-branded orange interface visibly renders, with shopping-bag mark and Russian subtitle **Доставка еды и продуктов**.
- UI contains tabs **Войти** (Sign in) and **Регистрация** (Registration), Email/password inputs, sign-in button, **Забыли пароль?** (Forgot password).
- **No ChatGPT sign-in gate appears** in the shown first screen. The displayed form is TALABOT's own application login.
- This is a **single first-screen visual observation**, not a claim that the site is always public, that the backend is safe, or that any successful Auth/account/session exists.
- No real or synthetic credentials were supplied; no sign-in, order, SQL, payment, permission modification, or production transaction was performed by the assistant in response.
- Screenshot includes device UI; exact capture time, server version, request destinations and runtime source SHA are **UNVERIFIED**. The phone status bar reading 9:46 must not be treated as a certified timestamp.

## Updated statuses

| Check | Result | What it does NOT establish |
|---|---|---|
| Safari iPhone opens a TALABOT first screen on a Pages.dev URL | **OBSERVED — FIRST SCREEN ONLY** | No guarantee of currently deployed SHA or full application functionality |
| ChatGPT auth gate blocking this first screen | **NOT OBSERVED** | Does not prove every other route is free of such gates |
| TALABOT internal email/password form | **OBSERVED** | Does not authorize user registration or entry of any credential |
| Production independence / current network mapping | **BLOCKED** | Historic synthetic pilot metadata is not current safe-route proof |
| Formal C-01 valid/invalid Auth+profile E2E | **NOT RUN** | 0/51 functional E2E unchanged |
| Source lock for formal C-01 | `1cb85361d698d5da787d927a4c9ae7bd213c68c1` | The visible historic Pages.dev preview has an earlier distinct source manifest |
| Security N0–N7 / Stage 9 | **NO-GO** | Screenshot is not a VM/network attestation |

## Next action for project manager (team-owned, no purchase)

1. **Acknowledge** that the first screenshot confirms TALABOT app login displayed in Safari **without ChatGPT access gate**. Do not reopen that solved first-page presentation issue without new evidence.
2. **Do not ask owner for real email/password** or instruct sign-up on this preview. Its current backend isolation hasn't been established.
3. For a genuine Safari walkthrough without account credentials, assign DEV/UX **a read-only, fake-data, visual-only demo** of the approved customer screens; preserve original design and leave primary production source untouched. First inspect any existing independent mock/preview route, do not re-build unnecessarily. Public hosting must be no-cost and separately scoped/owner-approved before a new or modified deployment. It must have zero connections to production and display an explicit nonfunctional demo marker.
4. Keep **formal C-01** a separate security-gated workstream; no login automation or live database test until independent N0–N7 PASS and PM dispatch.
5. Save subsequent owner Safari screenshots, each with filename/SHA, visible condition, version/URL if verified, source ref, and next action to MASTER #26 and an isolated documentation branch. Do not claim screenshot bytes are on GitHub unless actually uploaded.

**Owner interaction now:** no additional action required until the team supplies a verified safe way to view screens without entering credentials.

**Strict boundaries:** No purchases, paid/Cloudflare/Supabase change, no new live site in this documentation update; no code/design/SQL/CI/Main merge/deployment; QA/Release/PHASE2 remain NO-GO.
