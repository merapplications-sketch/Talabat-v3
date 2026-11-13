# TALABOT — Owner Safari / Zero-Cost Continuity

**Date:** 2026-11-13 Asia/Dushanbe  
**Status:** OWNER CLARIFICATION / DOCS ONLY / NO DEPLOYMENT  
**Management:** https://github.com/merapplications-sketch/Talabat-v3/issues/26  
**Stage9:** https://github.com/merapplications-sketch/Talabat-v3/issues/35  
**Owner Stage8 approval:** https://github.com/merapplications-sketch/Talabat-v3/issues/34#issuecomment-6858292284  
**Pinned formal source:** 1cb85361d698d5da787d927a4c9ae7bd213c68c1

## 1. New owner constraints — preserve and honor

- **Zero extra cost:** no paid hosting, subscriptions, rented VM, or purchases. Do not request laptop, Docker, personal hardware, production credentials, database data or technical setup from the owner. The team handles technical operations.
- **Owner test device:** iPhone Safari. **Do not give the owner a ChatGPT-login-gated preview.** A TALABOT app login is a different matter and must not be bypassed for authenticated C-01.
- Give the owner practical instructions, **one step per line**, only when an action is genuinely necessary. Do not send repeated operational questions or broad infrastructure requests.
- **Continuity is mandatory:** Every verified outcome, approved choice, SHA, screenshot (no private data), blocker and next owner must be saved in GitHub on isolated branches with a link in Issue #26. If a chat ends, new management continues from GitHub, not from guesses.
- Preserve previously accepted UI/UX, Q09–Q17 including Q14, PRICE/RATINGS/TIP/106/107/Source35. No changes to product/production/main without exact approval.

## 2. Separate two different tests

**Track A — immediate visual Safari preview:** the owner wants to open a public synthetic demo in iPhone Safari without ChatGPT sign-in, verify its appearance and give screenshot feedback. This is NOT C-01, NOT backend/RBAC security acceptance and NOT permission to enter credentials or submit orders.

An existing **historic** synthetic candidate is recorded at:
https://talabot-pilot-20261106.pages.dev/customer.html

Archived pilot metadata at https://github.com/merapplications-sketch/Talabat-v3/blob/1cb85361d698d5da787d927a4c9ae7bd213c68c1/docs/pilot-20261105/hosted/db-progress.json mentions Cloudflare Pages project talabot-pilot-20261106, historical deployment af22de56-73d1-4195-aefd-135b5e46ac7f, source 66fc8ee023ee3738f84e8be956b963b2b67bdfdc, and separate pilot database fsvrsvqfknogwmhccera. The artifact is **NOT** source-pinned to formal C-01; metadata is historical, its **current** live accessibility/backend isolation is **UNVERIFIED**. Web checks in this session could not verify availability. **Allow only first-page observation, no sign-in, no order, no personal data.** A preview at the Pages.dev domain avoids depending on the ChatGPT-site host type but is NOT guaranteed available or public until actually observed.

The historical GitHub Pages frontend at https://merapplications-sketch.github.io/Talabat-v3/customer.html refers to the primary TALABOT Supabase, according to https://github.com/merapplications-sketch/Talabat-v3/blob/1cb85361d698d5da787d927a4c9ae7bd213c68c1/docs/pilot-20261105/hosted/current-links.json . **DO NOT use that as a synthetic Auth/transaction test target.**

**Owner's first action — one step per line:**
1. Open Safari on iPhone.
2. Open https://talabot-pilot-20261106.pages.dev/customer.html .
3. Do not enter any email/password or press order/payment actions.
4. Send a screenshot of the **first page** and say whether it shows a ChatGPT gate, TALABOT page, or an error.
5. If the link fails, stop; technical team owns the next remedy and must not request purchases.

After screenshot, PM records factual result in #26; OPS/DEV verify current source mapping and no production dependency before interaction. If failed, propose a distinct **zero-cost synthetic-only public visual preview** with no production API/session and no ChatGPT login. **Do not create, publish or move a site without a separate explicit owner approval.** Keep original product styling, and label any visual-only demo as not C-01.

**Track B — real C-01 Auth+profile E2E:** only after the independently checked N0–N7 safety gate in a truly isolated disposable runner, two fake accounts and local DB. Stage9 at https://github.com/merapplications-sketch/Talabat-v3/blob/809767288c80f8c626be2f173712a20d396ba5e2/docs/qa-first-20261113/STAGE9-OPS-SEALED-ENVIRONMENT-PREPARATION-REPORT.md is **PARTIAL/BLOCKED**: no VM, Docker/QEMU/PostgreSQL or full offline source bundle. Do not run C-01, broad journey or CI. No vendor services or financial/role operations.

## 3. Handoff for any replacement manager

- MASTER Issue #26 is the durable control record; owner-approved test scope in #34; OPS Stage9 blocker in #35.
- Source 1cb85361d698d5da787d927a4c9ae7bd213c68c1 is the formal pinned C-01 baseline, not a claim about current live deployment.
- Existing preview Pages.dev source 66fc8ee... is historical and not current-source acceptance.
- Immediate next step: owner first-screen Safari screenshot **only**, without credentials; log observed access/error and link actual evidence.
- Subsequent team step: verify a genuinely safe public synthetic-only Safari visual preview, or present one isolated free publication proposal for explicit owner approval.
- C-01 remains 0/51 E2E executed; Admin 0/21; G1 incomplete; QA/RELEASE/PHASE2 NO-GO.
- Every future report/comment: exact SHA, environment, observed result (PASS/BLOCKED/UNTESTED), owner and next step. Never infer a PASS from a link or a document.
- This branch is a single documentation-only owner-continuity update. No source/CI/Cloudflare/Supabase/GitHub Pages/production modification or deployment was undertaken.
