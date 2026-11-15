# TALABOT — Stage 22 / المدير: فحص مستقل لأدلة الاختبار المنشور

**الوثيقة:** تسليم داخلي لمدير المشروع، وليس إعلان إغلاق نهائي للمالك  
**تاريخ:** 2026-11-15 (Asia/Dushanbe)  
**Issue العمل الوحيد:** [#48](https://github.com/merapplications-sketch/Talabat-v3/issues/48) — **سجل الإدارة:** [#26](https://github.com/merapplications-sketch/Talabat-v3/issues/26)  
**المصدر المنشور الثابت:** https://talabot-safari-demo-20261115.pages.dev/  
**Code/QA executable commit:** [9ce0909a47248e696c2611116b0bf3c36198b319](https://github.com/merapplications-sketch/Talabat-v3/commit/9ce0909a47248e696c2611116b0bf3c36198b319)  
**Workflow run:** [43694105608](https://github.com/merapplications-sketch/Talabat-v3/actions/runs/43694105608); **Job:** 132750740903 — **CONCLUSION: success**  
**Original approved fake/static demo source:** `3f74b29a7c4bcc89cef9e25dd73f574448ab7896`, unchanged  
**Owner visual evidence previously verified:** RU iOS, EN native Safari Private; no need for repeated owner screenshots  

## 1. حدود التفويض وسلامة الملفات
- Owner approved a single complete Stage22 task with internal harness repairs on isolated QA branch, one final delivery, no owner relay, no changed approved designs, no merge, deploy, billing, Cloudflare, Supabase, real transactions or production access.
- Isolated QA branch `review/stage22-one-shot-qa-20261115`. Against OPS handoff `58a5fd3202ce765e4c8a272a3ad7027fc3b89d03`, the **executed commit** adds **two QA-only files**: `.github/workflows/stage22-one-shot-qa-20261115.yml` and `docs/qa-first-20261115/stage22_guarded_browser_test.py`. The latter is test code, not a TALABOT app patch.
- Standard `ubuntu-24.04` public-repo runner, no imported prod credentials, `permissions: contents: read`, `persist-credentials:false`, no production mutation commands. `upload-artifact@v4` stores only fictitious QA evidence with **1-day retention**; no additional paid service was enabled. Owner's approved designs and production configs unchanged.
- Independently rechecked Cloudflare Pages: existing demo `talabot-safari-demo-20261115` deployment `636ae248-c8ac-45b9-8183-5a9fa3ddb986` **success**; old `talabot-pilot-20261106` deployment `1a602ee4-6daa-4a76-a8aa-68339321cac5` **success** and separate. No new Pages deployment.

## 2. Evidence retrieved and independently inspected by PM
**Evidence download:** [Actions run artifact](https://github.com/merapplications-sketch/Talabat-v3/actions/runs/43694105608/artifacts), artifact **14153557488** `talabot-stage22-qa-synthetic-only`, **558,036 bytes** ZIP, expires `2026-11-16T08:21:48Z`. Local independently downloaded ZIP **SHA256** `7b435543647cba9cd6baa0ec0d3708a585948c14c9306d44361b6f790bc400a1`; internal ZIP test **PASS**. Five files: `case-result.json`, `checkout-before.png` (390×1482), `checkout-after.png` (390×1482), `en-home-390.png` (390×2445), `stage22-network-sanitized.har` (162,139 bytes).
- Independent HAR parser: **57 entries**; **56** same-origin `https://talabot-safari-demo-20261115.pages.dev` HTTP 200 GET responses, and **one** synthetic `.invalid` outbound request with response `-1`, blocked. Request verbs **GET-only, 0 POST**; 24 WebP, 18 HTML, 10 JavaScript, 4 CSS, one failed blocked test request. **No real external host/WS attempt was recorded** within this bounded test. Test interception was installed before navigation; the deliberately unauthorized URL `qa-stage22-denied.invalid/never-sent` was recorded with `net::ERR_BLOCKED_BY_CLIENT`.
- Sanitized HAR **SHA256:** `6e59e0802874d30d3b80893bfcc0fe4ae7017c77d1affa3c80181b34925abad2`. HAR request/response headers exclude Cookie/Authorization/Set-Cookie and bodies/text content. User uploaded real credentials: none.
- PM opened **both real unedited screenshots** `checkout-before.png` and `checkout-after.png`: same mock payment screen, fake address, cash-to-courier, non-production footer and order summary; after UI swipe the **red toast** `DEMO: No real orders or payments` visibly appears and **no order success screen** appears. Hero/home screenshot original logo/offer bento/categories plus initial scrolling; no visual proof of broad breakage.
- `case-result.json` proves pointerdown acquired `HOLD` and enabled thumb; pointer progress **1.00 ≥ 0.96**; pointerup executed; `__demoBlockedActions` increment **+1**; `S.v='pay'`; `busy=false`; `success_visible=false`. **This closes previous first-run P1 harness coverage defect** (the original zero-counter test was invalid because it lacked pointer/precondition logging). Demo fake checkout guard **PASS for this synthetic scope only**, not real production order processing.
- PM checked live HTTP site receipts: `/`, `/demo-guard.js`, `/demo-fixture.js`, `/assets/3d/hamburger.webp` all HTTP 200 correct MIME; root, guard, fixture **SHA256 matched original static-only package**. Site CSP: `connect-src 'none'; form-action 'none'`; `nosniff` present.

## 3. Reconciled case matrix (do not repeat accepted work)
| Requirement | Executed evidence and exact scope | Result |
|---|---|---|
| Internet-reachable real Pages browser with network guard | GitHub Actions #43694105608: same browser live navigation and before-navigation exact-host HTTP/WS interception | **PASS** |
| Record successful / blocked / failed requests | **57-entry sanitized actual HAR** (56 same-origin GET 200 + 1 denied fake outside-host GET); separate JSON and job logs | **PASS scoped** |
| Synthetic dummy Slide-to-place-order blocks all mutation | Real rendered UI drag, HOLD progress=1, guard counter +1, red `DEMO: No real orders or payments` toast, no success; all requests GET | **PASS scoped** |
| RU+EN at widths 320/360/390/430 | **Previously completed** real hosted Actions #43684336979: **8/8 document lang/banner/global horizontal-overflow PASS**; PM did not re-run full matrix. New run #43694105608 covers 390px EN as corroboration | **PASS for documented geometry only** |
| Locale after reload | Earlier EN explicit-query reload + current EN explicit-query reload PASS; RU query URL previously PASS, **RU manual-toggle/storage reload across profiles NOT PROVEN** | **PARTIAL** |
| Delivery pricing clarity | Current English synthetic checkout screenshot order summary shows subtotal 30, discount −4.5, happy hour −3, delivery 10, total **32.5 TJS**, **math reconciles**. Separate earlier owner screenshot: mock item 27 + synthetic delivery quote 12 = 39, also reconciled | **PASS summary visibly clear in tested checkout; detailed base/extra split remains P2 unverified** |
| Fixed footer / payment action visibility | 390px screenshot shows active payment option, sticky slider, and order summary accessible in full-page capture; **no 320px checkout scroll-hitbox execution evidence** | **PARTIAL** |
| Paths and images | 8 category WebPs/restaurant visuals previously rendered, 390px screenshot still renders; HAR **8 unique literal template-like first-party URL requests** (e.g. `/$%7Besc(st.cover_url)%7D`) return 200 HTML fallback. Checkout live DOM `broken_image_paths:[]`; no global image failure | **P2 investigate on relevant UI; NOT a proven broken app layout** |
| English customization group labels | Earlier source/fixture uses `Размер порции`/`Добавки` under English despite translated UI. New run did not open product sheet in English | **P2 source-level concern; independent designer verification pending** |
| Demo banner WCAG contrast | Historical white on orange ~3.54:1 < AA 4.5:1, **owner-deferred** | **Deferred; DO NOT restyle without explicit owner permission** |
| Actual production customer app / official integrated E2E | Separate program; no deployment or real backend here | **NO-GO unchanged** |

## 4. Manager's assessment and narrow next internal work

**Manager verification**: technical Stage22 critical problem (safe mock order / egress trace) is **RESOLVED within exact synthetic live-demo path**. This is NOT equivalent to independent security + designer signoff on every UI flow; full Stage22 final acceptance therefore remains **PENDING** rather than falsely closed. In this conversation tools allow PM/GitHub + test runners but cannot wake separate ChatGPT Work role chats merely by posting a comment.

**One internal completion handoff in the SAME Issue #48 (not new Stage or Issue):** 
- **Independent security auditor:** read actual `case-result.json`, sanitized 57-entry HAR, 3 screenshots, original approved immutable source, latest Actions SHA and script. Verify no secret/prod destinations, no false checkout success, no replay or unsafe gesture, and whether any unverified escape route merits a test. Mark independently `ACCEPT / REJECT / NEEDS EVIDENCE` with exact pointer and bounded risk.
- **Independent designer/UX auditor:** compare 390px English Home & checkout and accepted owner RU/EN iPhone Safari views to approved Home B, Restaurant v1.6, Customization A, DineOut Gold; verify real visual overlap/truncation and English group-label source findings. Distinguish P2 fixture content from translated UI; leave owner-deferred colours unchanged. No redesign or code changes.
- **PM:** after both role reviews, reconcile PASS/FAIL, fix any **proven and in-scope** problems on isolated branch with minimal patch+real tests, then produce ONE final GO/NO-GO delivery. No other issue, stage, merge or deploy.

**DIL boundary:** workflow, test harness, and evidence are owned by the QA review branch. The already published preview and full TALABOT production app must remain untouched. The temporary GitHub artifact **expires after one day**; hashes, job log, and this durable written record remain. If raw screenshots/HAR are required long-term after expiration, arrange existing allowed storage without new charges and without publicly disclosing real data. No user interaction required.
