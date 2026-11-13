# TALABOT — RELEASE & DEPLOYMENT QA / STAGE 3

**التاريخ:** 2026-11-13، Asia/Dushanbe  
**المسؤول:** Release / Publisher (قراءة فقط)  
**التكليف:** [Issue #29](https://github.com/merapplications-sketch/Talabat-v3/issues/29) | **MASTER:** [Issue #26](https://github.com/merapplications-sketch/Talabat-v3/issues/26)  
**مدخلات التدقيق:** [Stage 1، 55a3fa5](https://github.com/merapplications-sketch/Talabat-v3/blob/55a3fa5113202afdc3604179fd4a4919043dd11f/docs/qa-first-20261113/PROGRAMMER-STAGE1-QA-REPORT.md)؛ [Stage 2، ea06d61d](https://github.com/merapplications-sketch/Talabat-v3/blob/ea06d61d349667f0a1135b63d923cc756159cc3d/docs/qa-first-20261113/INDEPENDENT-TECHNICAL-STAGE2-QA-REPORT.md).  
**الحكم:** **RELEASE READINESS NO-GO. PHASE2 NO-GO.** هذا حكم جاهزية، لا إذن نشر ولا إثبات حادثة إنتاجية.

## 1 — منهج القراءة وحدود الإثبات

- تم التحقق مباشرة بقراءات GitHub من أسماء الفروع وHEAD ومحتوى الملفات، وقائمة GitHub Actions وحالات SHA المحددة، وقوائم Releases، وأدلة النشر التاريخية. لم تُنفذ workflows أو اختبارات أو تنزيلات تشغيلية أو تحديثات خدمة.
- المصدر المرجعي الإداري: الفرع **docs/phase1-operational-coordination-20261111**، HEAD **1cb85361d698d5da787d927a4c9ae7bd213c68c1**. المصدر البرمجي الموازي **review/ci-native95-20261110**، HEAD **651696a3fdc51d393bcddef3effd71d6b9634845**؛ تقرير Stage 1 أثبت تطابق blobs الجوهرية بينهما ضمن نطاقه. فرع تقرير المبرمج 55a3fa5113202afdc3604179fd4a4919043dd11f وفرع المستشار ea06d61d349667f0a1135b63d923cc756159cc3d تقارير معزولة، وليسَا بناءين منشورين.
- المستودع الإداري المستقل **merapplications-sketch/talabot-tailadmin-review**: مرشح **review/ux02-v01-v05-candidate-20261112**، HEAD **254757fab9d5fa80bffe22fa30de5e65aac2f153**؛ default main = 1ef305c5b1332c899c5ffdeb72b56235d42d6d00. main الرئيسي = 148cfae50000e983af2221a96057c507edac6d69. **لا يُعدّ أي main أو فرع أحدث اسماً بالضرورة إصداراً نشطاً.**
- سمات المصدر المحلية غير المدفوعة/غير المحفوظة لدى الآخرين غير مرئية. بيانات الإنتاج تُثبت فقط عندما يتوافر receipt نشر حالي يربط environment → version/digest → source SHA → backend/config → CI/rollback.
- Supabase: أُجريت **قراءات metadata فقط** لقائمة المشاريع وEdge Functions والهجرات للفهرسة، دون SQL أو RLS أو تغيير. قائمة مشاريع 2026-11-13 أظهرت Talabat بحالة ACTIVE_HEALTHY؛ TALABOT isolated pilot 20261106 بحالة ACTIVE_HEALTHY؛ Talabat-tj بحالة INACTIVE. فشل استعراض migrations على المشروع الأساسي ومشروع Talabat-tj بسبب connection timeout، فلا نستنتج عدم وجودها. ظهر في isolated pilot **43 migration metadata** وآخرها 20261108150750 / qa_fixture_isolation_60؛ وجود الهجرات لا يثبت تطابق كل دالة/سياسة/Storage.
- Cloudflare: قراءة قائمة Workers/Pages المباشرة تتطلب موافقة/تسجيل دخول لم تُمنح في مسار الاتصال؛ **لم تُعَد المحاولة أو يُستخدم مسار التفاف**. لا توجد شهادة حالة Cloudflare حية. GitHub Deployments وGitHub Pages API metadata غير متاحين عبر موصل GitHub الحالي؛ جرت قراءة **الإيصالات المحفوظة بالمستودع** بدلاً من اختلاق نتائج. GitHub Releases القابلة للقراءة في المستودعين: **0**؛ لا ينفي ذلك النشر خارج GitHub Releases.
- التصنيفات: **VERIFIED HISTORICAL** = إيصال/بصمة تاريخية قابلة للتتبع؛ **DIRECT METADATA** = نتيجة قراءة حالة وصفية بتاريخ الفحص؛ **BLOCKED** = لا إثبات متاح بسبب صلاحية/غياب سلسلة بيانات؛ **UNTESTED** = لم يجرِ تحقق على بيئة تنفيذية مطابقة. لم تُرسل طلبات للموقع الحي/المعاملات ولا اختبارات مالية.

## 2 — جدول الإصدارات الفعلية ومصدر الإثبات

| الخدمة / الواجهة | البيئة المقصودة / عنوانها | آخر نشر يمكن **إثباته تاريخياً** | Artifact / Digest / تاريخ الإثبات | النسخة الفعالة اليوم والمطابقة للمصدر |
|---|---|---|---|---|
| العميل customer.html | GitHub Pages عام / https://merapplications-sketch.github.io/Talabat-v3/customer.html (واجهة قائمة تاريخياً، تصنيف Production-facing غير مؤكد اليوم) | GitHub deployment receipt **7161677425**، مصدر **ca8808dd6dee4f4815a266ae9bb9ea20a155f892**، فرع integration/customer-v80-current | SHA256: e599bf4403bd4c5e29a8b0120668e6964d97bf63c1bfe8f9bab25f0674f2d8ee؛ سجل نشر 2026-10-18T22:26:42Z؛ مطابقة HTTP تاريخية بتاريخ 2026-11-05 | **BLOCKED**؛ لا receipt راهن |
| السائق driver.html | GitHub Pages / .../driver.html | نفس receipt والمصدر ca8808dd | SHA256: 08535c9d9d20ecf1ac9a6b68a6bbeb0f649e4c84306af9a980ecc81db5d2bb0a | **BLOCKED** |
| المطعم merchant.html | GitHub Pages / .../merchant.html | نفس receipt والمصدر ca8808dd | SHA256: f33a5036b87404760a65091a9bff772fa86bee15d276ceffae1a93d8dc37637e | **BLOCKED** |
| الإدارة القديمة admin.html | GitHub Pages / .../admin.html | نفس receipt والمصدر ca8808dd | SHA256: 6b461c61bc6702979d7442fba3c6ad225525bb72cda86fb44220fd49d3895fa0 | **BLOCKED** |
| النواة talabat-core.js | GitHub Pages / .../talabat-core.js | نفس receipt والمصدر ca8808dd | SHA256: 77796be799c4677cfcc24c6e2c1104366bebae6db42dffc886f28d985cc6ae15 | **BLOCKED**؛ لا ربط API/DB حديث |
| لوحة TailAdmin الجديدة / Worker | **غير مثبت أنها إنتاج**؛ تعريف مصدر Cloudflare Worker باسم talabot-tailadmin-review | ملف cloudflare.config.ts يعرّف الاسم والـentrypoint فقط؛ **لا receipt Worker deployment فعّال** | BUILD-ONLY: نجاح vinext قديم بتاريخ 2026-11-09 على ed5e33af؛ لا Worker deployment digest | **BLOCKED** |
| معاينة إدارة اصطناعية | Preview منفصل: talabot-admin-review-gallery.alwarikahtan.chatgpt.site وtalabot-admin-takeover-review.alwarikahtan.chatgpt.site | docs/review-hosting.json يسجل Gallery **version 2 / e215037f** وInteractive **version 2 / a5beb108**؛ سجلات موقع اصطناعي، ليست نشر الإدارة الإنتاجي | version IDs محفوظة بالملف؛ لم تُقرأ حالة الاستضافة الراهنة؛ مرشح UX الحالي 254757fa مختلف | **VERIFIED HISTORICAL manifest / CURRENT UNTESTED** |
| Backend / PostgREST / RPC المالي | مشروع Supabase **Talabat**، المعرّف dzydscryrnahnneydnry (مرجع الواجهات القديمة) | **DIRECT METADATA:** المشروع ACTIVE_HEALTHY؛ وظيفتا Edge باسم route- (v2) وroute (v4)، last-update بتاريخ 2026-10-25، بحالة ACTIVE | **لا** source SHA أو digest أو ربط موثق بين Edge Functions والواجهات وRPC؛ الهجرات الحية تعذرت قراءتها (timeout) | **BLOCKED**؛ project health ليس صحة تطبيق ولا دليل writer |
| Supabase pilot معزول | **Staging/Preview مُعد سابقاً**: fsvrsvqfknogwmhccera | **DIRECT METADATA:** ACTIVE_HEALTHY، 43 migrations، آخرها 20261108150750؛ **HISTORICAL:** معاينة talabot-pilot-20261106.pages.dev / deployment af22de56... / source 66fc8ee... | لا Edge Functions في قائمة المشروع؛ لا current build/runtime parity أو Storage/auth test evidence كاملة | **PARTIAL infrastructure / E2E BLOCKED** |
| مشروع Talabat-tj الأقدم | sbzcokatkhxsijsfplit | **DIRECT METADATA:** INACTIVE، لا Edge Functions في القائمة | لا إثبات أنه endpoint أي واجهة جارية؛ migrations read timeout | **NOT VERIFIED AS ACTIVE APP TARGET** |
| Watchdog / dispatch / scheduled jobs | بيئة تشغيل مستقلة **غير مثبتة** | مصدر watchdog script، واستدعاء dispatch_tick من كود العميل، **ليسا إيصال خدمة أو Job منفصل** | لا Scheduler ID، deployment، cron receipt، heartbeat أو log يربط job بالبيئة | **BLOCKED** |

**مصادر النشر التاريخي:** [Published source receipt](https://github.com/merapplications-sketch/Talabat-v3/blob/1cb85361d698d5da787d927a4c9ae7bd213c68c1/docs/pilot-20261105/hosted/published-source.json)، [Current-links snapshot](https://github.com/merapplications-sketch/Talabat-v3/blob/1cb85361d698d5da787d927a4c9ae7bd213c68c1/docs/pilot-20261105/hosted/current-links.json)، [SHA inventory](https://github.com/merapplications-sketch/Talabat-v3/blob/1cb85361d698d5da787d927a4c9ae7bd213c68c1/docs/pilot-20261105/published-inventory.json)، [Pilot db-progress](https://github.com/merapplications-sketch/Talabat-v3/blob/1cb85361d698d5da787d927a4c9ae7bd213c68c1/docs/pilot-20261105/hosted/db-progress.json)، [Admin preview version IDs](https://github.com/merapplications-sketch/talabot-tailadmin-review/blob/254757fab9d5fa80bffe22fa30de5e65aac2f153/docs/review-hosting.json)، [Admin Worker config](https://github.com/merapplications-sketch/talabot-tailadmin-review/blob/254757fab9d5fa80bffe22fa30de5e65aac2f153/cloudflare.config.ts).

**المهم:** سجل 5 نوفمبر 2026 ليس فحصاً جديداً أجري اليوم. active deployment SHA/digest/route/created_at **غير معروفة** لكل خدمة؛ لا ننسب إليها ca8808dd بوصفه حياً اليوم، ولا ننسب PM HEAD أو TailAdmin UX إلى الإنتاج.

## 3 — SOURCE ↔ DEPLOYMENT DIFF

تمت **مقارنة Git Blob SHA مباشرة** لكل ملف تنفيذي بين **أرشيف النشر ca8808dd** و**المصدر الإداري 1cb85361**. النتيجة **5/5 مختلفة**:

| الملف | منشور تاريخي ca8808dd — Git blob | مصدر PM 1cb85361 — Git blob | الحكم |
|---|---|---|---|
| customer.html | f7d72fa1f1cb1d834d36cc8bd5c65477d620d00b | 9bc335f52ad58d7feab12ad8a2214bde9ab32330 | DIFFERENT |
| driver.html | 3ffd2ccd192aa60533723a43fe0a81c87282de59 | 086929844b2080d7aa2afe1c2c57267cde245d40 | DIFFERENT |
| merchant.html | de3d678932a6f63ddddf1b8ebee7efc5abb7542a | 5f09dd5cc3d5abc9d6b0d3afa031342b05f5212c | DIFFERENT |
| admin.html | bdcec1a020d5eb38633f519386997172ba5469e3 | 062a68cfa740f2733cad39b5c4c5b0c635f54e55 | DIFFERENT |
| talabat-core.js | 2ebfb62f3bb2c964887d6a33834399e50c91ecc0 | f639bec1d23a812866e06eb1110940c77563387c | DIFFERENT |

هذا يثبت **فرق محتوى فعلي بين المرجعين المثبتين**، ولا يثبت وحده أن النسخة الحية حالياً متأخرة أو أن فروق الكود وصلت إليها. دمج branch أو نجاح CI لا يحل غياب link deployment→artifact→source.

ملاحظة: قوائم published-inventory وcurrent-links التاريخية تسند بعضها لمراجع مرشح مختلفة وتختلف في بعض أعلام same-as-candidate؛ لذلك استُخدمت blob comparisons مباشرة بين **مرجعين مسمّيين صراحة** بدلاً من استنتاج مطابقة مرشح غير محدد.

## 4 — CI: ما نجح وما فشل وما يغطي HEAD الجاري

| النطاق | Workflow / Run / SHA | الموثق | حدود الاستدلال |
|---|---|---|---|
| Main latest visible | [CI106 #42829377671](https://github.com/merapplications-sketch/Talabat-v3/actions/runs/42829377671)، 2026-11-10T13:57Z، **86eb978e1aeb2be4a9d90999dc9b5a1267cb33df** | **SUCCESS**؛ Postgres وrequired106 ناجحان | تاريخي على review/batch106-20261110؛ workflow محصور بالفرع ومسارات tests/native106؛ **ليس** اختبار 1cb85361 أو إصدار deploy |
| Main prior success | [CI105 #42822666873](https://github.com/merapplications-sketch/Talabat-v3/actions/runs/42822666873)، **3893352541f8a2a94ed87ee11863519e69ad45fb** | **SUCCESS** postgres/client/required105 | أصل آخر؛ لا قبول إطلاق |
| Main historical failure | [CI105 #42821898901](https://github.com/merapplications-sketch/Talabat-v3/actions/runs/42821898901)، **7290f4ff5343a3607991a6b30e513e690f267833** | **FAILURE** في native105/native.py وbrowser.mjs وrequired105؛ يوجد نجاح لاحق على SHA آخر | لا نمحو الفشل أو ننسب إصلاحه آلياً لكل فروع المصدر |
| Main historical failure | [REVIEW103 #42808981791](https://github.com/merapplications-sketch/Talabat-v3/actions/runs/42808981791)، **4cb516cc8d1a2ffa2bc8274ceaef3196404fc4a1** | **FAILURE** في native-independent.py | مرجع فشل مستقل على SHA قديم؛ لم نُعد تشغيله |
| Admin original | [#42640577614](https://github.com/merapplications-sketch/talabot-tailadmin-review/actions/runs/42640577614)، **ed5e33af0f4f1d9b5d4a54c25444a2e8b5916395** | **SUCCESS**، 2026-11-09 | original-build فقط، فرع review/cloudflare-vinext |
| Admin vinext | [#42640577750](https://github.com/merapplications-sketch/talabot-tailadmin-review/actions/runs/42640577750)، نفس ed5e33af | **SUCCESS** في vinext-build | ليس CI لمرشح UX الحالي ولا إثبات Worker منشور |

**استعلام GitHub Actions المفلتر على exact head_sha أعاد 0 runs، وحالة combined statuses فارغة، للمراجع:** PM 1cb85361؛ programmer-code 651696a3؛ programmer QA 55a3fa5؛ consultant QA ea06d61d؛ Admin UX 254757fa؛ Admin main 1ef305c5. هذا وصف للـAPI المتاح، لا حكم بأن أي اختبار آخر مستحيل أو لم يوجد تاريخياً.

**فجوة coverage مؤكدة:** workflow CI106 يختبر بيئة PostgreSQL اصطناعية وnative106، وليس release snapshot مع browser/API/Storage/auth/dispatch على البيئة المستهدفة. workflows الخاصة بالـpilot مربوطة غالباً بفرع candidate/pilot-readiness-20261105؛ وفحص Safari المذكور هو macOS Safari وليس iPhone Safari. workflow لوحة الإدارة مقصور على review/cloudflare-vinext؛ أحد workflows له صلاحية contents:write ويدفع إعداد vinext إلى نفس الفرع عند نجاحه، ولذلك **لا يجوز تشغيله في نطاق تقرير القراءة فقط**.

**المطلوب لإغلاق CI:** release-artifact attestation مستقل (commit + build manifest + digest + immutable assets + backend migration version)، تشغيل CI آمن مرخّص على **source SHA المختبر بالضبط**، HTTP/API contract + role isolation + financial oracle + storage/notifications + repeat/unknown/failure E2E، وفحوص Safari فعلي. CI106/107/PRICE/RATINGS/TIP محفوظة كقبول تاريخي ضمن نطاقها فقط.

**عدّ Stage 1/2:** **0/51** سيناريو E2E تكاملي منفذ على المصدر المثبت الحالي؛ 14 static assertions = 9 PASS / 5 FAIL معيار مصدر فقط؛ ليست 51 حالة ناجحة/فاشلة. F-01/02/03/04 source findings من المستشار دون إثبات أثر إنتاجي.

## 5 — حالة الخادم والكتّاب والـJobs

| العقد | الدليل | الحالة |
|---|---|---|
| Calling path: driver → deliver_order | [talabat-core.js عند L1304](https://github.com/merapplications-sketch/Talabat-v3/blob/1cb85361d698d5da787d927a4c9ae7bd213c68c1/talabat-core.js#L1304) يرسل rpc(deliver_order)؛ [SQL candidate schema_patch34 عند L47–70](https://github.com/merapplications-sketch/Talabat-v3/blob/1cb85361d698d5da787d927a4c9ae7bd213c68c1/sql/schema_patch34.sql#L47-L70) يحوي row-lock وشرط الحالة | **SOURCE VERIFIED، ACTIVE DB VERSION BLOCKED**؛ لا ادعاء وصول هذا التعريف للإنتاج أو حماية كل مؤثر مالي |
| Actual writer / financial RPC versions | بعض أسماء/تواقيع الماضي موثقة؛ إصدار functions من Supabase Edge metadata لا يثبت إصدار SQL RPC أو trigger | **BLOCKED**؛ مطلوب من API/DB current effective definitions checksums / deployed migration and role-bound writer inventory **metadata** |
| dispatch_tick | [core عند L494–516](https://github.com/merapplications-sketch/Talabat-v3/blob/1cb85361d698d5da787d927a4c9ae7bd213c68c1/talabat-core.js#L494-L516) يستدعي sb.rpc('dispatch_tick') من client-side setInterval؛ **جميع 19 workflow ملفات** المسجلة بفرع PM بلا schedule/cron وبدون dispatch_tick | **مصدر استدعاء عميل VERIFIED؛ Scheduler مستقل فعّال BLOCKED**. عدم ظهور Cron في GitHub لا ينفي Supabase cron أو خدمة خارجية غير مفحوصة |
| Watchdog | [ops/pilot-watchdog.py](https://github.com/merapplications-sketch/Talabat-v3/blob/1cb85361d698d5da787d927a4c9ae7bd213c68c1/ops/pilot-watchdog.py) يصرح بأن module ليس لديه scheduler أو destination حقيقي مُهيأ | **SOURCE VERIFIED؛ active daemon / on-call receipt BLOCKED** |
| API ↔ frontend ↔ DB version | أرشيف صفحات GitHub القديمة يشير إلى مشروع dzydscryrnahnneydnry؛ Supabase project metadata نشط | **BLOCKED**: لا request-scoped route trace أو build-header/worker version أو current RPC-def signatures |
| Authentication/RBAC/tenant and financial settlement | [Technical Stage 2](https://github.com/merapplications-sketch/Talabat-v3/blob/ea06d61d349667f0a1135b63d923cc756159cc3d/docs/qa-first-20261113/INDEPENDENT-TECHNICAL-STAGE2-QA-REPORT.md) صنف G1-D BLOCKED؛ R05 historical grant/TRUNCATE observation لا يثبت live reachability أو exploit | **NOT TESTED on pinned live routing**؛ يحتاج request-scoped sanitized evidence ثم synthetic negative tests بتفويض مستقل |
| Storage/signed URLs/notification deliveries | قواعد وأمثلة قديمة معزولة؛ project active وEdge functions listing لا تثبت bucket ACL/expiry/revocation أو delivery receipts | **BLOCKED** |

**ملاحظة مالية محكومة:** F-04 في المرشح يسمح بتحصيل كاش أقل من due مع note، بينما **قرار المالك Q14 يمنع إتمام التسليم بتحصيل أقل**. Q09–Q17 تضبط زيادة الدفع والتغيير/القيد والسقف الافتراضي 20 TJS. هذه **مخالفة مرشح SOURCE** وفق المستشار، وليست حادثة إنتاجية مثبتة أو تفويضاً لتعديل الحسابات أو اعتماد عقد جديد. F-02 يثبت تعدد طلبات client المحتمل، **ولا يثبت مضاعفة قبض/أجر** في قاعدة البيانات الحية.

## 6 — جاهزية الرجوع والنسخ والتعافي

[خطة HOST-UPGRADE-ROLLBACK](https://github.com/merapplications-sketch/Talabat-v3/blob/1cb85361d698d5da787d927a4c9ae7bd213c68c1/release/pilot-candidate/HOST-UPGRADE-ROLLBACK.md) و[ACTIVATION-REVIEW](https://github.com/merapplications-sketch/Talabat-v3/blob/1cb85361d698d5da787d927a4c9ae7bd213c68c1/docs/pilot-20261105/ACTIVATION-REVIEW.md) موجودتان كمقترح وإجراءات حماية، وليس كدليل rollback معتمد ومختبر اليوم:

1. **Frontend rollback:** archive ca8808dd تاريخي، لكنه **غير مضمون التوافق المالي** بعد تبديل writers/finance schema. لا إعادة دوال قبض معيبة أو أرصدة قديمة. حالة **PARTIAL PLAN / BLOCKED LIVE TARGET**.
2. **DB backup/PITR:** أمثلة PostgreSQL محلية وreadback تاريخي معزول محفوظان، لكن **لا** backup ID حديث وUTC snapshot/PITR window أو schema/grants/trigger version binding مثبت بمصدر النشر المستهدف. **BLOCKED**.
3. **Storage:** metadata وحدها غير كافية؛ يلزم تأكيد bytes وobject version IDs والبصمات وACLs وربط consistency point مع قاعدة البيانات والتشفير. **BLOCKED**.
4. **Keys/custody:** المطلوب metadata أسماء الإصدارات والمسؤول/قابلية الوصول والاحتفاظ والمطابقة، بلا raw keys/tokens/passwords أو تنزيل. **BLOCKED**.
5. **Transactions since backup:** ledger/outbox/remote receipts/unknown ACK يجب صونها ومصالحتها، ولا تُستعاد أرصدة أو عقود أقدم فوق معاملات أحدث. **BLOCKED** قبل أي recovery.
6. **RPO/RTO & independent restore:** اقتراحات في خطط قديمة لا تساوي هدفاً معتمداً مقاساً. لا وجهة restore مستقلة مثبتة بسجل اختبار مرتبط بإصدار ونسخة بيانات وStorage الحالية؛ **UNTESTED**.

**Rollback-readiness: NO-GO**. لا استعادة أو تجربة رجوع أُجريت في هذا التدقيق.

## 7 — شروط إنشاء E2E اصطناعي معزول — لا تنفيذ الآن

- **T1 / Build & provenance (OPS/DEV):** commit pinned لمصادر customer/driver/merchant/admin/core، Build digests immutable، manifest DB/RPC/Worker/Job config؛ عنوان HTTPS معزول وشهادة أن طلبات الاختبار لا تصل إلى مشروع الإنتاج أو عميله أو مفاتيحه.
- **T2 / Auth & isolation (AUTH/SECURITY):** هويات اختبارية منفصلة (2 عميل، 2 سائق، 2 مطعم، أدوار الإدارة/الدعم/المالية حسب الاختبار، denied role)، جلسات/MFA اصطناعية ومصفوفة role×tenant. Credentials خارج GitHub.
- **T3 / DB/RPC/Jobs (API/DB/OPS):** PostgreSQL معزول مع نسخ تعريفات schema/RLS/grants والكتّاب المعتمدة وتكوين Storage اصطناعي؛ scheduler مستقل وهمي/مضبوط، trace request-id/effective role/writer version، snapshots قبل وبعد.
- **T4 / Finance (FIN/DB):** fixtures نسخ العقود المالية المعتمدة، oracle مستقل، قضايا كاش Q09–17 (نقص/مساواة/زيادة، cap 0/20/المعدل، due=0، كسور)، محافظ وتسوية وأخطاء دفع وهمية لا تحول أموالاً.
- **T5 / Storage/Notifications (Storage/QA):** bucket منفصل لصور وهمية، signed URL TTL/revocation/role-negative tests، إشعارات/chat/mock providers مستقلة.
- **T6 / deterministic races (QA/DEV):** double taps، فشل RPC، انقطاع قبل/بعد COMMIT، two-session contention، retries مع ACK غير محسوم، أثر DB وLedger once-only.
- **T7 / device & CI (QA/CI):** ربط كل حالة بـsource SHA والبيئة وscreenshot/log منقح؛ أحجام 320/360/390/430، RU/EN/TG وLight/Dark؛ **Safari فعلي على iPhone** في تكليف منفصل. لا خلط مع macOS Safari أو Chromium/WebKit.

**قاعدة التوقف:** أي endpoint إنتاج، هوية حقيقية، أثر مالي فعلي أو اختلاف environment manifest = STOP/ESCALATE بلا محاولة تعويض أو retry حي. **كل 51 E2E تبقى 0/51 منفذة**. لا تفويض ضمن Stage 3 لتجهيز/اختبار هذه البيئة أو حتى تشغيل workflows، وهذه قائمة متطلبات فقط.

## 8 — قرار الجاهزية وإغلاق موانع G1

| بوابة | الحكم | مانع النشر / صاحب الدليل / معيار الإغلاق |
|---|---|---|
| G1-A | **PARTIAL** | **OPS/Release + build owner:** receipt حالي لكل واجهة وAPI يثبت ID، بيئة، تاريخ، SHA، artifact digest وتطابق كل المكونات؛ القديمة 5/5 مختلفة عن source الحالي |
| G1-B | **PARTIAL** | **API/DB/Jobs:** actual deliver_order/writers versions + transaction boundaries/roles/trigger inventory وdispatch_tick scheduler مستقلة + draining |
| G1-C | **PARTIAL** | **FIN/API/DB:** approved oracle/versioned active finance contract، Q09–17 وبصمات writers؛ لا تعديل مال أو retroactive records |
| G1-D | **BLOCKED** | **AUTH/SECURITY/DB:** sanitized request-scoped identity/RLS/effective role trace ومصفوفة رفض اصطناعية، لا اختبار حسابات حية |
| G1-E | **PARTIAL** | **OPS/FIN/key custodian:** metadata keys + reconciliation receipts/settlement trace + unknown idempotent outcome |
| G1-F | **PARTIAL** | **OPS/CI/Backup/Storage:** evidence current SHA CI، release→backup/PITR+object bytes+keys manifest، independent restore target، RPO/RTO proof وphysical Safari |

**Release status: NO-GO** (0/6 بوابات G1 مقبولة). **QA closure: NO-GO** بسبب 0/51 E2E على المصدر الحالي وعدم ثبوت deployed source parity. **PHASE2: NO-GO**. لا موافقة نشر ضمن هذا التقرير؛ أي قرار مستقبلي يتطلب حزمة مبنية ومحددة المصدر وموافقة مالك صريحة منفصلة. لا يُعتبر العجز عن الوصول لبيانات Cloudflare أو timeout migrations عيب تشغيل مثبتاً.

## 9 — تسليم ومراجع قابلة للتحقق

- [Issue #29](https://github.com/merapplications-sketch/Talabat-v3/issues/29) تكليف مسؤول النشر؛ [Issue #26](https://github.com/merapplications-sketch/Talabat-v3/issues/26) سجل الإدارة.
- [Stage 1](https://github.com/merapplications-sketch/Talabat-v3/blob/55a3fa5113202afdc3604179fd4a4919043dd11f/docs/qa-first-20261113/PROGRAMMER-STAGE1-QA-REPORT.md) و[Stage 2](https://github.com/merapplications-sketch/Talabat-v3/blob/ea06d61d349667f0a1135b63d923cc756159cc3d/docs/qa-first-20261113/INDEPENDENT-TECHNICAL-STAGE2-QA-REPORT.md).
- [Continuity decision register](https://github.com/merapplications-sketch/Talabat-v3/blob/1cb85361d698d5da787d927a4c9ae7bd213c68c1/docs/continuity/PHASE1-CURRENT.md)، [Historic deployment receipt](https://github.com/merapplications-sketch/Talabat-v3/blob/1cb85361d698d5da787d927a4c9ae7bd213c68c1/docs/pilot-20261105/hosted/published-source.json)، [Checksums](https://github.com/merapplications-sketch/Talabat-v3/blob/1cb85361d698d5da787d927a4c9ae7bd213c68c1/docs/pilot-20261105/hosted/current-links.json)، [Rollback](https://github.com/merapplications-sketch/Talabat-v3/blob/1cb85361d698d5da787d927a4c9ae7bd213c68c1/release/pilot-candidate/HOST-UPGRADE-ROLLBACK.md).
- [CI106 workflow definition](https://github.com/merapplications-sketch/Talabat-v3/blob/1cb85361d698d5da787d927a4c9ae7bd213c68c1/.github/workflows/ci106.yml)، [Admin vinext workflow](https://github.com/merapplications-sketch/talabot-tailadmin-review/blob/254757fab9d5fa80bffe22fa30de5e65aac2f153/.github/workflows/verify-vinext-build.yml).
- **تسليم هذا المستند فقط** على فرع المراجعة المعزول **review/qa-first-release-stage3-20261113**، مبني على PM HEAD **1cb85361**. لا تغييرات على مصدر/CI/SQL أو Main، ولا Deploy/Merge/Workflow run/SQL/Keys/MFA/Restore. **PHASE2 NO-GO**.
