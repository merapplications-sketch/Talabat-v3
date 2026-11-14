# TALABOT — سجل أدوات الاختبار: تأكيد OWASP ASVS 5.0.0 Level 2 مقابل AVA/Vitest
**Checked 2026-11-14 / Asia-Dushanbe. Documentation-only, NOT execution.**

## 1. تصحيح موثق: الاسم كان OWASP ASVS وليس AVA
**المعروف الآن بدليل من المصدر التاريخي:** المالك والمدير والمبرمج/المستشار استخدموا **OWASP ASVS 5.0.0 Level 2** كمرجع تدقيق أمني؛ وقد قرأتُ `TALABOT-Project-Handoff-2026-11-09.txt` في ChatGPT Library، وهو يسجل مصفوفة **345 متطلبًا** بنتائج تاريخية: **1 PASS, 2 FAIL, 330 UNTESTED, 12 N/A**. لا تنقل هذه النتائج إلى الحالة الحالية دون تحقق من الإصدار/البيئة. أعمال المبرمج كانت جزئيًا في فرع محلي بدون remote مثبت، ولذلك لم يظهر هذا الاسم عبر البحث في GitHub العام.
**OWASP ASVS ليس برنامج فحص آليًا**؛ هو معيار متطلبات للتحقق بالاختبارات والمراجعة والأدلة. **AVA** إطار Unit Testing منفصل غير مثبت الاستخدام، و**OWASP ZAP** أداة أخرى لم يثبت تشغيلها. لا تختلق استخدام أي منهما.
**المرجع الجديد المفصل:** [OWASP ASVS L2 historical verification](OWASP-ASVS-L2-HISTORICAL-VERIFICATION-20261114.md). [المصدر الرسمي](https://asvs.owasp.org/).
**نتيجة مهمة أخرى:** المصدر التاريخي سجل مصفوفة Functional منفصلة **57 بندًا: 10 مكتمل بالنطاق، 27 جزئي، 16 متوقف، 4 غير مختبر**، ولا تتعارض عدديًا مع مصفوفة QA الأحدث **51 E2E + 21 Admin** لأنها نطاقات وأزمنة مختلفة.

### حدود البحث عن runner فعلي
- `talabot-tailadmin-review/package.json` على `review/ux02-v01-v05-candidate-20261112`: يوجد `vite`, `eslint`, `typescript`, `next`, `vinext` وأوامر `build`, `lint`؛ **لا يوجد `ava` أو `vitest` أو `playwright` كاعتماد ظاهر في هذا manifest، ولا أمر `npm test`**. هذا لا ينفي أدوات مثبتة خارج المستودع.
- `package.json` في جذر `Talabat-v3` على مرجع الإدارة لم يُعثر عليه؛ المشروع تاريخيًا HTML/JS مباشر وSQL، مع اختبارات محلية Node/PGlite حسب تسليم Work القديم.
- بحث GitHub Code Search للفهرس الافتراضي للمستودعين عن `AVA/AVAS`/`ASVS` لم يُظهر نتائج؛ **هذا لا يشمل تاريخ Work المحلي غير المرفوع**.
- فحوص Playwright/Chromium القديمة متاحة كتقارير محدودة، لا تعني أنها شغلت ASVS أو نجحت جميع الاختبارات. لا حاجة لتثبيت Test Runner جديد حتى ننتهي من جرد القديم.

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
