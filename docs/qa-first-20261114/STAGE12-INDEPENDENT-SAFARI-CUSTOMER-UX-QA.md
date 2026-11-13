# TALABOT — STAGE 12 / INDEPENDENT SAFARI CUSTOMER UX QA

**التاريخ:** 2026-11-14 (Asia/Dushanbe)  
**السلطة:** [Issue #38](https://github.com/merapplications-sketch/Talabat-v3/issues/38) · [سجل المدير #26](https://github.com/merapplications-sketch/Talabat-v3/issues/26)  
**القرار:** **GO فقط لطلب تصحيح محدود بالمعاينة الاصطناعية ثم اختبارها بأمان / NO-GO للمطابقة البصرية النهائية أو العرض العام / PHASE2 NO-GO.**  
**طريقة العمل:** فحص مستقل للمصدر والأدلة بدون إصلاح أو نشر أو دخول أو أي بيانات إنتاج.

## 1. ثبات المصدر والنسخة

| عنصر | مرجع موثق | حدود الاستدلال |
|---|---|---|
| فرع المعاينة | **review/safari-zero-cost-synthetic-demo-20261113**، HEAD **2bae45cc5a21372123228befcbe87c19d6aac974** | أُعيد فحص HEAD عند بدء المهمة وقبل حفظ التقرير ولم يتغير؛ GitHub لا يكشف تعديلات محلية غير مرفوعة. |
| أصل العميل المعتمد | **1cb85361d698d5da787d927a4c9ae7bd213c68c1** | [Git compare](https://github.com/merapplications-sketch/Talabat-v3/compare/1cb85361d698d5da787d927a4c9ae7bd213c68c1...2bae45cc5a21372123228befcbe87c19d6aac974): مرشح ahead=2 / behind=0؛ 58 ملفاً مضافاً حصراً في مجلد المعاينة، دون تعديل أو حذف في أصل المشروع. |
| تقرير المستشار Stage 11 | [المصدر](https://github.com/merapplications-sketch/Talabat-v3/blob/c90585b479f43143daa00504238a3732f962d625/docs/qa-first-20261114/STAGE11-INDEPENDENT-SAFARI-SECURITY-QA.md) | شهادة فحص ثابت للمصدر وبعض متطلبات العزل فقط؛ لا فحص شبكة أو متصفح منفذ. |
| Stage 10 | [تقرير التسليم](https://github.com/merapplications-sketch/Talabat-v3/blob/2bae45cc5a21372123228befcbe87c19d6aac974/previews/safari-zero-cost-customer/STAGE10-VALIDATION-REPORT.md) · [manifest](https://github.com/merapplications-sketch/Talabat-v3/blob/2bae45cc5a21372123228befcbe87c19d6aac974/previews/safari-zero-cost-customer/manifest.json) | الملفات 58 في Git، و50 ملفاً من الأصول CSS/JS/3D نُقلت ببصمات متطابقة وفق فحص Stage 11؛ لم نكرر فحص جميع البصمات. |
| التشغيل الفعلي | فحص وجود ملفات المعاينة مركبة محلياً | Chromium متوافر، لكن دليل 58 ملفاً الكامل بما فيه WebP غير مركب ولا يوجد مضيف آمن بمصدر SHA محدد. لم نكرر محاولات Git/DNS/download التي تعذرت في Stage11، ولم نشغل نسخة ناقصة. |

**التحقق المستقل من التصميم في المصدر:** قورنت عينات CSS/تصميم متطابقة حرفياً بين 1cb85361d698d5da787d927a4c9ae7bd213c68c1 و2bae45cc5a21372123228befcbe87c19d6aac974 في مواضع customer.html/index.html **250–380، 538–692، 818–870، 1024–1097** (413 سطراً دون فروق). فُحصت كذلك ملفات **index.html / demo-core.js / demo-fixture.js / demo-guard.js / _headers / manifest.json**. هذا يؤكد ثبات المكونات ضمن المصدر، وليس اختبار بكسلات أو متصفح. لا رابط Safari فعلي منشور لهذا المرشح؛ روابط GitHub تعرض الملفات فقط.

## 2. مطابقة عناصر العميل المعتمدة

| العنصر المحمي | الدليل بالمصدر | الحالة |
|---|---|---|
| **Home — Dynamic Marketplace B** | [index.html L538–692](https://github.com/merapplications-sketch/Talabat-v3/blob/2bae45cc5a21372123228befcbe87c19d6aac974/previews/safari-zero-cost-customer/index.html#L538-L692)، الوظائف hHead وvHome، البنتو والبحث والأقسام والشرائح | **SOURCE-CONFORMING / VISUAL UNTESTED**. |
| **Restaurant Details v1.6 Legacy Premium** | [index.html L250–380](https://github.com/merapplications-sketch/Talabat-v3/blob/2bae45cc5a21372123228befcbe87c19d6aac974/previews/safari-zero-cost-customer/index.html#L250-L380)، vMenu، مطعم تجريبي مفتوح وآخر مغلق مع أسماء طويلة | **SOURCE-CONFORMING / VISUAL UNTESTED**. |
| **Product Customization Direction A** | واجهة dish-sheet الأصلية، openItem وshPick، [fixture](https://github.com/merapplications-sketch/Talabat-v3/blob/2bae45cc5a21372123228befcbe87c19d6aac974/previews/safari-zero-cost-customer/demo-fixture.js) تتضمن g1 إلزامية وg2 اختيارية للصنف i1 | **SOURCE PRESENT / EXECUTION BLOCKED**. |
| **Cart** | vCart، cartSave وcartLoad، مفاتيح تخزين تجريبية tlb-demo-cart- وtlb-demo-pref- | **SOURCE PRESENT / EXECUTION BLOCKED**. |
| **DineOut Premium Gold** | [index.html L1582–1586](https://github.com/merapplications-sketch/Talabat-v3/blob/2bae45cc5a21372123228befcbe87c19d6aac974/previews/safari-zero-cost-customer/index.html#L1582-L1586) دالة dineH. fixture مطعم s1 مفتوح بخصم 15% | **SOURCE PRESENT / VISUAL UNTESTED**؛ لا جزم بدرجات الذهب/المحاذاة أو ظهور الصورة. |
| **Campaigns, categories, logo, fonts/colors** | HOME_CATS وheroH وbottomBn وd6Logo، أصل CSS متطابق ضمن الفحص، أصول 3D محفوظة وفق Stage11 | **SOURCE/IDENTITY PRESERVED**؛ لا إثبات صور حملات فعلية مصوّرة بالمتصفح. |

**فرق بصري مشروع خاص بالعرض:** أضيف شريط توضيح **#tlb-demo-banner** وشاشة انتظار **#tlb-startup** خارج مكونات الصفحة المعتمدة لإعلان وجود بيانات وهمية وعدم إتمام الطلبات. لا تُعامَل هذه الزيادة كإعادة تصميم لشاشات العميل. يجب فحص ألا تحجب الرأس أو نافذة المنتج عند التنفيذ. بيانات الحملات الوهمية تضع image_url فارغاً؛ مسار bottomBn يُظهر النص كبديل للصورة. هذه **حدود fixture** وليست عيوب قص مرئية مثبتة. ملاحظة ألوان صفحة تسجيل الدخول للمعاينة القديمة **DEFERRED / NOT ACCEPTED**، ولا يجوز اعتمادها لتغيير الهوية.

## 3. مصفوفة UX S10-01..S10-08

| Case | المسار ومعيار القبول | الدليل الثابت | حكم التنفيذ |
|---|---|---|---|
| **S10-01** | Home B تظهر دون تسجيل TALABOT/ChatGPT | Fake Customer session عبر demo-fixture، TLB.start('customer') في index | **SOURCE PRESENT / BROWSER BLOCKED**؛ لا Console ولا Screenshot. |
| **S10-02** | المطاعم/الأقسام/الحملات/DineOut والتمرير | vHome، vCat، vPromo، dineH، مخزون بيانات وهمية | **SOURCE PRESENT / BROWSER BLOCKED**؛ fallback نصي للبنرات دون صورة. |
| **S10-03** | فتح مطعم v1.6 ثم الرجوع | openStore وvMenu ومطاعم s1/s2 | **SOURCE PRESENT / BROWSER BLOCKED**؛ لا إثبات للتنقل. |
| **S10-04** | Direction A، اختيار إلزامي/اختياري وإضافة صحيحة | مجموعات g1/g2 موجودة في fixture، واجهة الخيارات الأصلية | **SOURCE PRESENT / BROWSER BLOCKED**؛ التحقق من الإلزامي غير منفذ. |
| **S10-05** | سلة وهمية: إضافة/زيادة/نقصان/رجوع/Refresh | cartSave/cartLoad ووظائف الكمية والتخزين المحلي التجريبي | **SOURCE PRESENT / BROWSER BLOCKED**؛ الاحتفاظ الفعلي غير مثبت. |
| **S10-06** | منع إنشاء طلب/دفع حقيقي وإبلاغ المستخدم بوضوح | [demo-guard.js](https://github.com/merapplications-sketch/Talabat-v3/blob/2bae45cc5a21372123228befcbe87c19d6aac974/previews/safari-zero-cost-customer/demo-guard.js) يعيد demo_only، Mock SDK وCSP نصّي | **SOURCE-GUARDED / BROWSER & EGRESS BLOCKED**. لا ندّعي أن كل زر disabled أو أن عدد محاولات الطلبات الخارجية صفر. |
| **S10-07** | تبديل RU↔EN وبقاء اليدوي بعد reload؛ أول زيارة بلغة المتصفح | منطق اختيار اللغة سليم في index/core لكن fixture يفرض RU | **P2 FAIL SOURCE / BROWSER BLOCKED**؛ تفصيل §4. |
| **S10-08** | 320/360/390/430 × RU/EN، scroll/overlap/long strings/hit targets/safe areas | responsive CSS ومحتوى اصطناعي طويل؛ لا قياسات | **0/8 EXECUTED — UNTESTED**. |

**العدّ الصادق:** **0/8** مسارات تنفيذية مثبتة؛ **0/8** مجموعات مقاسات×لغة؛ **0** Screenshot جديدة؛ **0** DOM/overflow measurements؛ **0** browser network/console traces؛ **0** physical Safari. مصدر مؤكد لا يعادل PASS بصرياً، وعدم إجراء الاختبار لا يعني فشلاً وظيفياً أو نجاحاً. لا يمكن إعلان clipping أو عدمه.

## 4. عيوب مثبتة من المصدر والحالات غير المحسومة

### UX12-F-01 / P2 — LANGUAGE RESET / CONFIRMED SOURCE, RUNTIME UNTESTED

**المراجع:** [index.html L8](https://github.com/merapplications-sketch/Talabat-v3/blob/2bae45cc5a21372123228befcbe87c19d6aac974/previews/safari-zero-cost-customer/index.html#L8)، [demo-fixture.js L2](https://github.com/merapplications-sketch/Talabat-v3/blob/2bae45cc5a21372123228befcbe87c19d6aac974/previews/safari-zero-cost-customer/demo-fixture.js#L2)، [demo-core.js L23 وL41](https://github.com/merapplications-sketch/Talabat-v3/blob/2bae45cc5a21372123228befcbe87c19d6aac974/previews/safari-zero-cost-customer/demo-core.js#L23-L41).

**الفعل الفعلي للمصدر:** index يقرأ tlb_demo_lang المخزّن ثم لغة المتصفح؛ demo-core يحفظ تغيير المستخدم ويستعيده. لكن fixture يكتب **localStorage.setItem('tlb_demo_lang','ru') دون شرط في كل تحميل** قبل بدء demo-core. يتوقع عند EN ثم Refresh الرجوع إلى RU. كما يفقد الزائر الجديد ذو تفضيل EN في المتصفح تفضيله الأولي. قد تظهر رسالة startup بالإنجليزية قبل فرض RU على التطبيق بسبب ترتيب السكربتات؛ هذا استنتاج مصدر لا صورة منفذة.

**التصحيح الأدنى المطلوب، غير المنفذ:** بموجب تكليف منفصل من PM للمبرمج: **حذف الكتابة غير المشروطة إلى tlb_demo_lang من previews/safari-zero-cost-customer/demo-fixture.js فقط**، مع إبقاء __ROLE و__TALABOT_SYNTHETIC والبيانات الوهمية وحواجز الاتصال. لا مساس بـ customer.html / talabat-core.js الجذر أو خط/ألوان/شعار.

**اختبارات الإغلاق بعد التصحيح:**
1. مخزن فارغ + navigator.languages = en-US ⇒ EN؛ وru-RU ⇒ RU؛ ولغة غير معتمدة ⇒ RU الافتراضي، كما تسمح السياسة الموجودة.
2. اختيار EN يظل EN بعد reload، واختيار RU يظل RU؛ تتوافق قيمة tlb_demo_lang وdocument.documentElement.lang وTLB.lang، وعناوين Home/Restaurant/Cart وشريط DEMO.
3. زيارة Home→Restaurant→Direction A→Cart→Back ثم reload لا تغيّر اللغة اليدوية أو تُسقط سلة المعاينة.
4. منع localStorage في بيئة الاختبار لا يكسر الإقلاع، بل يعود إلى سياسة تفضيل المتصفح.
5. **حالة مشروطة:** [index.html L2095](https://github.com/merapplications-sketch/Talabat-v3/blob/2bae45cc5a21372123228befcbe87c19d6aac974/previews/safari-zero-cost-customer/index.html#L2095) يعيد فرض ?lang=ru/en عند كل reload، حتى إذا اختار المستخدم لغة أخرى يدوياً. هذا **سلوك مصدر مؤكد**، لكن كونه عيباً يتوقف على سياسة أسبقية رابط الاختبار مقابل اليدوي. يجب قياس حالتي URL دون معامل ومعامل صريح، وطلب قرار PM عند التعارض؛ لا تغيير إضافي من دون إذن.

### UX12-F-02 / P2 ACCESSIBILITY CRITERION — DEMO NOTICE ONLY

[CSS في index.html L11 وL1098](https://github.com/merapplications-sketch/Talabat-v3/blob/2bae45cc5a21372123228befcbe87c19d6aac974/previews/safari-zero-cost-customer/index.html#L1098-L1099) يحدد للشريط **#tlb-demo-banner** خلفية var(--o) من :root = **#F1511B**، نصاً أبيض **#FFFFFF**، font-size **11px** وfont-weight **600**. بما أن الشريط خارج .d6، لا يرث لونها المحلي. بحساب WCAG relative luminance مستقل، L(background)=0.2466476325 ونسبة التباين **3.539552941:1**، أقل من **4.5:1** المطلوبة لنص عادي. هذا **فشل معيار حسابي من CSS**، وليس شكوى عرض Safari موثقة. يتعلق فقط بالتنبيه الاصطناعي المضاف، لا بتغيير هوية العميل أو لون المعتمد.

**قرار مطلوب من PM/المالك:** بيان أولوية وصولية هذا النص التجريبي؛ أي معالجة مرئية يجب تكليفها واعتمادها منفصلاً، دون تغيير الألوان/الخطوط المعتمدة داخل تصميم العميل. لم أغيّر شيئاً.

### UX12-O-01 / SOURCE LIMITATION, NOT RENDERING DEFECT

fixture تزوّد البنرات بقيم image_url فارغة، وbottomBn يعرض fallback نصياً. صورة حملة واقعية لن تُثبت من مجرد تطابق CSS والأصول. يُوثق أثر البيانات الوهمية في أي مقارنة بصرية لاحقة؛ لا صور تخمينية ولا تجميل مستقل.

## 5. الدليل التنفيذي المفقود وملاك إغلاق البوابات

| المانع | المالك المسؤول بعد تكليف PM | معيار الإغلاق |
|---|---|---|
| **P2 لغة** | المبرمج، فقط على فرع تصحيح معزول | أقل تغيير لملف fixture، Commit، فرق ملفات محدود، ونتائج RU/EN أول زيارة/يدوي/Refresh و?lang. |
| **عدم وجود artifact كامل للتشغيل** | صاحب الحزمة/المبرمج + PM | تسليم كامل الـ58 ملفاً وأصولها الأصلية مع SHA/manifest ثابت إلى مختبر معزول، دون استبدال أو اتصال إنتاج. |
| **0/8 geometry/UX** | المدقق المستقل بعد توفير artifact | لقطات شاشة غير معدلة + DOM getBoundingClientRect/clientWidth/scrollWidth لكل 320/360/390/430 × RU/EN، أسماء طويلة، عرض modal والتأكيد، Safe Area، أهداف لمس، رجوع وسلة. |
| **أمان الشبكة سلوكياً** | المستشار الأمني/QA مفوّض | تسجيل attempted + failed requests, WebSocket, CSP, console, redirects وأفعال الدفع/الطلب على localhost شبكة ممنوعة مع mock فقط؛ لا HTTP إنتاج. |
| **تباين شعار DEMO النصي** | PM → المالك | قرار خاص بإخطار المعاينة، لا تفويض لإعادة تلوين المنتج. |
| **iPhone Safari / مضيف static Pages** | مختبر جهاز + Publisher بعد تخويل منفصل | فحص جهاز Safari حقيقي على أصل اختبار آمن، ثم إثبات HTTP CSP وorigin منفصل وعدم وجود Auth أو Worker/Functions/production binding؛ إذن المالك للـartifact والرابط قبل أي نشر. |

**الصور/القياسات:** أصول 3D محفوظة على Git، وليست صور اختبارات Safari. لا صور جديدة أو DOM أو Console أو Network. لا يجوز تحويل تقرير Stage11 الأمني الساكن إلى شهادة أمان تشغيلية، ولا إعادة استغلال صور pilot قديمة كاختبار لهذا SHA.

## 6. تسليم الحكم إلى المدير

- **GO (للتكليف فقط):** المبرمج يمكن أن يتلقى من PM تفويضاً جديداً لتصحيح P2 في نسخة DEMO فقط، ثم توفير artifact كامل للاختبار المعزول وإعادة التدقيق المستقل. **لا يقوم المدقق بأي إصلاح.**
- **NO-GO للمطابقة البصرية النهائية:** ثبات تصميم المصدر مدعوم، لكن كل اختبارات العرض الحالية BLOCKED/UNTESTED.
- **NO-GO للنشر أو رابط Safari عام:** يحتاج نجاح اختبار الشبكة الحقيقي والطلب السلبي وRU/EN والقياسات، وقرار وصولية التنبيه، والتحقق من المضيف والـCSP، وموافقة مالك صريحة.
- **PHASE2: NO-GO.** C-01 خارج التكليف، وكذلك إعادة الاختبارات المقبولة PRICE/RATINGS/TIP/106/107. لا تعديل أصل العميل أو Admin Template B أو KPIs A أو V04، ولا Cloudflare/Supabase/SQL/CI/account/production/merge/deploy.

**تصنيف نهائي:** **PARTIAL SOURCE FIDELITY / P2 LANGUAGE CONFIRMED + P2 DEMO-ONLY NOTICE ACCESSIBILITY SOURCE FAILURE / EXECUTABLE SAFARI QA BLOCKED / GO TO NARROW DEMO FIX AND SAFE RETEST ONLY / PUBLIC RELEASE NO-GO.**

**الفرع التوثيقي:** review/qa-first-independent-safari-customer-ux-stage12-20261114 — الأصل **2bae45cc5a21372123228befcbe87c19d6aac974**، التقرير وحده مطلوب إضافته. [Issue #38](https://github.com/merapplications-sketch/Talabat-v3/issues/38) · [Issue #26](https://github.com/merapplications-sketch/Talabat-v3/issues/26).
