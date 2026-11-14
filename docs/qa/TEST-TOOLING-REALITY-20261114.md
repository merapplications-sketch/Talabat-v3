# TALABOT — اختبار الأدوات المستخدمة فعليًا: AVA / AVAS / Vitest وغيرها
**Checked 2026-11-14 / Asia-Dushanbe. Documentation-only, NOT execution.**

## 1. ما الاسم الذي تذكره المالك؟
قال المالك إن هناك أداة اختبار اسمها تقريبًا `avas`. **الاسم غير مؤكّد**. يوجد إطار JS معروف اسمه **AVA** (https://github.com/avajs/ava) لتشغيل اختبارات Node.js المنعزلة والمتوازية، لكن **لم يثبت أنه مُثبّت أو مستخدم في TALABOT**. لا تعتبر مجرد التشابه في اللفظ دليلًا. قد يقصد شيئًا مختلفًا؛ ينبغي أن يحدد الفريق ما هو مستعمل من ملفات المصدر والتقارير قبل اقتراح تثبيت أي إطار.

### نتائج التحقق من مصدر المشروع
- `talabot-tailadmin-review/package.json` على `review/ux02-v01-v05-candidate-20261112`: يوجد `vite`, `eslint`, `typescript`, `next`, `vinext` وأوامر `build`, `lint`؛ **لا يوجد `ava` أو `vitest` أو `playwright` كاعتماد ظاهر في هذا manifest، ولا أمر `npm test`**. هذا ليس مسحًا لكل الشجر والأفرع ولا ينفي أداة مثبّتة خارج المستودع. [Manifest](https://github.com/merapplications-sketch/talabot-tailadmin-review/blob/review/ux02-v01-v05-candidate-20261112/package.json).
- مسار `package.json` في جذر `Talabat-v3` على مرجع الإدارة لم يُعثر عليه في هذه القراءة؛ المشروع تاريخيًا HTML/JS مباشر وملفات SQL، فلا تفترض أنه مشروع Node له نفس runner.
- بحث GitHub Code Search للأسماء `avas` / `AVA` / `Vitest` / `Playwright` في الفهرس الافتراضي للمستودعين لم يُظهر نتائج؛ **فهرس default branch ليس فحصًا كافيًا لفروع أخرى**.
- أداة `webapp-testing` الخاصة بـAnthropic كانت **اقتراحًا سابقًا** لاستخدام Playwright، وليست إثباتًا بأنها ثُبّتت أو استُخدمت في أحدث فحص.
- لا نغيّر runner أو نثبت AVA/Vitest فقط لأن الاسم يتشابه مع ما يتذكره المالك. **أولًا نحتفظ بالاختبارات الحالية ونجردها**.

## 2. الفرق بين ما شُغّل، وما استُلم كدليل تاريخي، وما لا يزال ناقصًا

| النوع | ما أثبته التقرير/المصدر | ما **لا** يثبته |
|---|---|---|
| PostgreSQL + required106 GitHub CI | CI106 SUCCESS على `86eb978e1aeb2be4a9d90999dc9b5a1267cb33df`, run `42829377671`, وفق Stage1 QA | لا يثبت تشغيل آخر Admin/Customer SHA أو Supabase المنشور |
| مصدر JavaScript / VM واختبارات قبول محلية | Stage1: 14 assertion من المصدر 9 PASS و5 FAIL (أربع مجموعات مخاطر F01–04) | لا يثبت فشلًا إنتاجيًا ولا E2E مكتمل |
| Stage13 source language regression | 8/8 محاكاة JavaScript للغة RU/EN نجحت في مصدر المعاينة الوهمية `3f74b29a...` | ليست فتح Safari أو DOM أو شبكة حقيقية |
| TailAdmin build/lint/analytics | UX checkpoint: Vite/Vinext build PASS؛ lint PASS مع 45 تحذيرًا مصنّفًا؛ 12 حسابًا Analytics و15 preservation PASS حسب صاحب الدفعة | ليست تشغيلًا عبر 21 شاشة Admin على النسخة المنشورة |
| Chromium / Playwright | رصد وجود Chromium وPlaywright عند بعض المنفذين، ومحاولات/فحوص متصفح أقدم/مصادر أخرى | **Stage16 synthetic Safari runtime 0/8**؛ لا ZIP في runner، ولا نتائج فعلية لـSafari في تلك المرحلة |
| UX source inventory | مراجعة منظومات الواجهة والقياسات الحسابية للون والنص، مع صور أقدم | لا تثبت iPhone physical Safari/خدمة حية/سعة |
| App original E2E (pinned current source) | حسب Master QA: 0/51 تكامل للعميل والسائق والـbackend، و0/21 Admin routes | **لا يعني أن التطبيق فشل 51 اختبارًا**؛ معظمها BLOCKED/UNTESTED/PARTIAL |
| Capacity / k6 / spike / soak | خطة موثقة فقط | لا يوجد اختبار قدرة مثبت لحجم المستخدمين أو الـp95/99 |
| Security pentest / auth RLS negative | مراجعات ولقطات مصدر تاريخية | G1-D بقي BLOCKED على مرجع QA؛ لا شهادة منع اختراق مطلق |

**المراجع:** [Stage1 report](https://github.com/merapplications-sketch/Talabat-v3/blob/55a3fa5113202afdc3604179fd4a4919043dd11f/docs/qa-first-20261113/PROGRAMMER-STAGE1-QA-REPORT.md) · [QA consolidated](https://github.com/merapplications-sketch/Talabat-v3/blob/0ab523782ee1bf6f69e2e3be7ec6e96394d9ce6a/docs/qa-first-20261113/MASTER-QA-CONSOLIDATED-20261113.md) · [Admin UX checkpoint](https://github.com/merapplications-sketch/talabot-tailadmin-review/blob/review/ux02-v01-v05-candidate-20261112/docs/ux02/CHECKPOINT.md) · [Stage19 publisher blocked](https://github.com/merapplications-sketch/Talabat-v3/issues/45).

## 3. إطار اختبار TALABOT المقترح دون تكرار الأدوات/إهدار الموارد

**المستوى 0: ثابت وسريع على كل Commit**
- Formatter/typecheck/lint/build مع إصدارات ثابتة؛ مراجعة secrets وdependencies، CodeQL/Dependabot حسب استحقاق/صلاحيات GitHub؛ مقارنة snapshot الكود والملفات المعتمدة.
- وحدة حساب السعر وحصة السائق/المنصة/المطعم، دون ترقية test runner قبل جرد السكربتات الموجودة.

**المستوى 1: محلي وآمن**
- محاكاة JS deterministic للـstate machine، وتعارض التزامن، وفقد ACK، ورسائل الاتصال؛ قواعد SQL/PostgreSQL داخل بيئة اختبار صناعية مع حسابات منفصلة، لا بيانات حقيقية.
- Auth/RLS/permissions: اختبارات رفض القراءة والكتابة بين عميلين ومطعمين وسائقين وإداريين، دون إفشاء data/keys.

**المستوى 2: متصفح تنفيذ فعلي**
- Playwright (أو runner المتصفح الموجود القابل للتكرار) لاختبار تسجيل الدخول الاصطناعي، البحث والسلة والطلب، السائق والمطعم والإدارة، RU/EN/TG، الهاتف والشاشة الواسعة. سجّل HAR/console/screenshots/DOM مع منع كل egress غير مصرح.
- اختبار iPhone Safari وAndroid الحقيقي مستقل؛ WebKit ≠ iPhone native Safari.

**المستوى 3: السعة والتعافي**
- k6 أو أداة معادلة **في بيئة معزولة وبحدود سرعة معتمدة**، baseline/load/spike/soak، GPS/Realtime، تصريف الطوابير، p95/p99، الاسترداد بعد عطل، no duplicate financial effects.
- Alert Admin + external independent, real receipt; DB+Storage backup & restore test; لا نتائج PASS حتى وجود receipt.

**المستوى 4: بعد إصدار التطبيق الأصلي**
- Native Crash/ANR tracking (مثلاً Crashlytics/Sentry وفق احتياج وخصوصية وتكلفة)، push token lifecycle وbackground GPS الحقيقي، مختبر Play internal/closed وApple عند وجود عضويتها.

**أدوات إضافية مقترحة فقط وليست مثبتة أو مفوضة:** AVA/Vitest (واحد منها عند حاجة اختبارات وحدة إضافية)، Playwright WebKit, k6, axe-core accessibility, Lighthouse, Sentry, OpenTelemetry, OWASP ZAP, CodeQL, Dependabot. **لا تثبت أي حزمة، ولا تبدأ scans على الإنترنت أو حمل على Production قبل تكليف صريح.**

## 4. الأصول المرجعية للحفاظ عليها
- `docs/management/CROSS-CHAT-CLAUDE-HANDOFF-20261114.md` — نقطة الدخول لجميع المحادثات.
- `docs/qa/OWNER-PILOT-SHOWSTOPPERS-20261114.md` — شروط قبول النسخة الأولى.
- `docs/launch/PROACTIVE-CAPACITY-RESILIENCE-PLAN-20261114.md` — السعة والإنذارات وحماية البيانات.
- `docs/ai/RULES.md` و`docs/ai/DECISION-PROTOCOL.md` — صلاحيات الأدوار ووقف التكرار.
- [Master Issue #26](https://github.com/merapplications-sketch/Talabat-v3/issues/26) دائمًا اقرأ آخر تعليق؛ لا تختزل حالة المشروع إلى هذا الملف التاريخي.

**قانون الإثبات:** تقرير أداة مكتوب ليس دليلًا أن الأداة اشتغلت. يلزم أمر/إصدار/وقت/بيئة/مصدر SHA/خرج فعلي/test receipts، وإلا status `NOT VERIFIED`.
