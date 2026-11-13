# TALABOT — Programmer QA-FIRST / Stage 1 / Consolidated Handoff
**Date:** 2026-11-13 · Asia/Dushanbe
**Issue:** [#27](https://github.com/merapplications-sketch/Talabat-v3/issues/27) · **Master:** [#26](https://github.com/merapplications-sketch/Talabat-v3/issues/26)
**Decision:** **QA DISCOVERY PARTIAL — NO-GO to QA-stage closure / NO-GO to remediation**.
**Authority:** owner-authorized audit only; NO SOURCE FIXES, NO live writes, merge, SQL, role/finance changes, deployment or Phase2.

## 1. Read-only intake and immutable source provenance

- Repository: `merapplications-sketch/Talabat-v3`. PM continuity branch `docs/phase1-operational-coordination-20261111` verified HEAD `1cb85361d698d5da787d927a4c9ae7bd213c68c1` at recheck, [continuity file](https://github.com/merapplications-sketch/Talabat-v3/blob/1cb85361d698d5da787d927a4c9ae7bd213c68c1/docs/continuity/PHASE1-CURRENT.md).
- Latest inspected programmer-code branch `review/ci-native95-20261110`: `651696a3fdc51d393bcddef3effd71d6b9634845`. Compared key source file blob SHA against PM snapshot; identical: `customer.html=9bc335f52ad58d7feab12ad8a2214bde9ab32330`, `driver.html=086929844b2080d7aa2afe1c2c57267cde245d40`, `talabat-core.js=f639bec1d23a812866e06eb1110940c77563387c`, `sql/schema_patch34.sql=c969801b0d0e83d84bd704e12184dc4d1678b457`.
- Default `main` HEAD `148cfae50000e983af2221a96057c507edac6d69` is **not** the current programmer baseline. Source on divergent feature/preview branches was not silently merged or treated as deployed.
- Inspected GitHub remote branches (112 names across two pages), worktrees by GitHub commit/contents API, assignments, prior reports, workflows and CI. **Local uncommitted/unpushed work in a different developer environment is not observable**; no claim that it was inspected.
- Public documented staging URLs `/customer` and `/driver` loaded read-only on `https://talabot-isolated-safari-20261106.alwarikahtan.chatgpt.site/`; both displayed authentication UI. Returned page titles identify **`pilot-mobile-20261107.31`**, while [older published handoff](https://github.com/merapplications-sketch/Talabat-v3/blob/1cb85361d698d5da787d927a4c9ae7bd213c68c1/docs/pilot-20261105/hosted/safari-alt2/HANDOFF-AR.md) identifies `pilot-mobile-20261106.3` / source `883e3fe839be5d6872fa2b79c52b08c3de6a1609`. **Current page-title version to exact Git SHA and active backend was not proven.** No login or write occurred.
- Local runtime could not resolve `github.com` for a safe source clone; there is no owner-authorized, current-source, populated synthetic Auth/DB/API sandbox or associated synthetic credentials available in this execution. No dependencies were installed and no new CI runs were triggered.

## 2. Actual coverage — strict numerator/denominator

| Measure | Result | Counting rule |
|---|---:|---|
| Planned customer, driver, backend functional scenarios for current SHA | **51** | C01–C20 + D01–D14 + B01–B17 |
| Executed functional E2E scenarios on current pinned SHA | **0/51 (0%)** | Only actual integrated behavior counts. Static inspection, previous CI and a different deployed preview are excluded |
| Current-source static checks executed | **14/14** | 9 PASS, 5 FAIL of *source criteria*, not 9 runtime passes. S09/S13 are two checks of one in-flight-lock problem |
| Read-only remote preview landing checks | **2/2 HTTP-rendered pages** | Public customer/driver sign-in surfaces only; different release, no authentication or transactions; not part of 51 |
| Prior accepted tests | Historical | Preserved by SHA and acceptance scope; not re-executed, not current-source coverage |

**Functional status distribution (51):** PASS=0 · FAIL=0 · PARTIAL=24 · BLOCKED=21 · UNTESTED=6. `PARTIAL` means source inspected without end-to-end proof; `BLOCKED` means a specific test environment, identity, provider, or trace is missing; `UNTESTED` means not run. **No new runtime PASS or new runtime FAIL is claimed.**

All matrix rows below share immutable source commit `1cb85361d698d5da787d927a4c9ae7bd213c68c1`, read-only GitHub analysis environment; row links pin the inspected source. A row with no test execution is *not* a disguised success. Suspected priorities are triage estimates, **not** proof of exploited severity.

## 3. Customer functional scenario matrix (20)

| ID | خطوات الحالة | المتوقع | الفعلي وحد الإثبات | الحالة | أولوية محتملة | مسؤول/اعتمادية | دليل |
|---|---|---|---|---|---|---|---|
| C-01 | فتح العميل→تسجيل الدخول بهوية اصطناعية صالحة/خاطئة | نجاح الصحيح ورفض الخطأ بلا تسريب | ظهر نموذج الدخول في معاينة مختلفة المصدر فقط؛ لم تُرسل بيانات اعتماد | **BLOCKED** | P1 | DEV/AUTH | [SRC-C](https://github.com/merapplications-sketch/Talabat-v3/blob/1cb85361d698d5da787d927a4c9ae7bd213c68c1/customer.html) |
| C-02 | دخول→إعادة تحميل→خروج→حساب آخر | ثبات الجلسة وعزلها وعدم تسرب حساب | مصدر Auth مقروء ودليل جلسات سابق؛ لا حسابات اختبار مرتبطة بالإصدار الحالي | **BLOCKED** | P1 | AUTH | [SRC-CORE](https://github.com/merapplications-sketch/Talabat-v3/blob/1cb85361d698d5da787d927a4c9ae7bd213c68c1/talabat-core.js) |
| C-03 | فتح Home Dynamic Marketplace B→تمرير الأقسام | العروض والبطاقات الصحيحة واستقرار الحركة | لم تتوفر جلسة كتالوج اختبار/تشغيل إصدار مطابق | **UNTESTED** | P2 | DEV | [SRC-C](https://github.com/merapplications-sketch/Talabat-v3/blob/1cb85361d698d5da787d927a4c9ae7bd213c68c1/customer.html) |
| C-04 | فتح Restaurant Details v1.6→القائمة→المراجعات | عرض المطعم والمنتجات وتفاصيله الصحيحة | المسار موجود بالمصدر؛ لا تنفيذ بصري/وظيفي حالي | **UNTESTED** | P2 | DEV | [SRC-C](https://github.com/merapplications-sketch/Talabat-v3/blob/1cb85361d698d5da787d927a4c9ae7bd213c68c1/customer.html) |
| C-05 | بحث عربي/روسي/إنجليزي→فئات→نتائج فارغة | بحث وعرض وعودة دون تداخل أو فقد سياق | لا بيانات كتالوج اصطناعية متصلة | **UNTESTED** | P2 | DEV | [SRC-C](https://github.com/merapplications-sketch/Talabat-v3/blob/1cb85361d698d5da787d927a4c9ae7bd213c68c1/customer.html) |
| C-06 | اختيار منتج→إضافات Direction A→تعديل كمية | فرض خيارات إلزامية وسعر مطابق للخادم | دوال التخصيص مقروءة فقط؛ لا تشغيل API معزول | **UNTESTED** | P1 | DEV | [SRC-C](https://github.com/merapplications-sketch/Talabat-v3/blob/1cb85361d698d5da787d927a4c9ae7bd213c68c1/customer.html) |
| C-07 | إضافة سلة→حفظ→إغلاق/إعادة فتح | السلة والمفتاح لنفس الحساب خلال 24 ساعة | مصدر cartSave/cartLoad وCK مطابق بنيوياً؛ لم تُختبر جلسة حقيقية | **PARTIAL** | P1 | DEV | [SRC-C](https://github.com/merapplications-sketch/Talabat-v3/blob/1cb85361d698d5da787d927a4c9ae7bd213c68c1/customer.html) |
| C-08 | إدخال promo/HH/loyalty→تغير محتوى السلة | إلغاء الخصم غير الصالح وعدم تضارب السعر | راجعت calc وapplyPromo وحماية stale response؛ لم تُجرَ مطابقة DB | **PARTIAL** | P1 | FIN/DEV | [SRC-C](https://github.com/merapplications-sketch/Talabat-v3/blob/1cb85361d698d5da787d927a4c9ae7bd213c68c1/customer.html) |
| C-09 | عنوان جديد→quote→تبديل عنوان/منطقة بعيدة | الرسوم تعاد وتحظر المسافة غير المدعومة | راجعت quoteNow وensureQuote؛ لا طلب quote فعلي | **PARTIAL** | P1 | DEV | [SRC-C](https://github.com/merapplications-sketch/Talabat-v3/blob/1cb85361d698d5da787d927a4c9ae7bd213c68c1/customer.html) |
| C-10 | حفظ عنوان ناقص/إحداثية مفقودة ثم صحيح | رفض الناقص وحفظ الصحيح مع بيان الخطأ | فحص afSave في المصدر فقط؛ غابت قاعدة اختبار | **PARTIAL** | P2 | DEV | [SRC-C](https://github.com/merapplications-sketch/Talabat-v3/blob/1cb85361d698d5da787d927a4c9ae7bd213c68c1/customer.html) |
| C-11 | إرسال checkout بالنقر السريع مرتين | طلب واحد ومفتاح واحد وعدم خصم مكرر | S.busy وp_key موجودان؛ لم يُختبر التزامن على HTTP | **PARTIAL** | P1 | DEV/API | [SRC-CORE](https://github.com/merapplications-sketch/Talabat-v3/blob/1cb85361d698d5da787d927a4c9ae7bd213c68c1/talabat-core.js) |
| C-12 | إنشاء طلب→قطع الاستجابة بعد COMMIT→إعادة إرسال | رجوع لنفس الطلب بلا تكرار | اختبار تاريخي معزول في tests/pilot؛ غير منفذ على SHA الحالي | **BLOCKED** | P1 | API | [SRC-QA106](https://github.com/merapplications-sketch/Talabat-v3/blob/1cb85361d698d5da787d927a4c9ae7bd213c68c1/docs/review/continuation106/RESULTS.md) |
| C-13 | فشل checkout→إغلاق التطبيق→استعادة السلة والمفتاح | لا إعادة توليد هوية الطلب بعد فشل مجهول | استعادة S.okey من localStorage مثبتة بالمصدر؛ لم تُختبر إعادة فتح | **PARTIAL** | P1 | DEV | [SRC-C](https://github.com/merapplications-sketch/Talabat-v3/blob/1cb85361d698d5da787d927a4c9ae7bd213c68c1/customer.html) |
| C-14 | دفع نقدي/محفظة/بطاقة→تغيير وسيلة→retry | لا محاولة مالية خاطئة أو دفع غير مُكوّن | لا بوابة دفع اختبار/جلسة مالية معزولة | **BLOCKED** | P1 | FIN/API | [SRC-CONT](https://github.com/merapplications-sketch/Talabat-v3/blob/1cb85361d698d5da787d927a4c9ae7bd213c68c1/docs/continuity/PHASE1-CURRENT.md) |
| C-15 | طلب pending→cancel→تنازع قبول المطعم | لا ادعاء إلغاء ناجح عند رفض الخادم | راجعت قفل S.cxb وقراءة الحالة بعد الفشل؛ لا تنازع منفذ | **PARTIAL** | P1 | DEV/API | [SRC-C](https://github.com/merapplications-sketch/Talabat-v3/blob/1cb85361d698d5da787d927a4c9ae7bd213c68c1/customer.html) |
| C-16 | فتح tracking→إشعارات→انقطاع الشبكة | حالة نهائية صحيحة وتحديثات دون فقد | لا طلب اصطناعي جارٍ ولا قنوات Realtime مطابقة | **BLOCKED** | P1 | DEV/OPS | [SRC-CORE](https://github.com/merapplications-sketch/Talabat-v3/blob/1cb85361d698d5da787d927a4c9ae7bd213c68c1/talabat-core.js) |
| C-17 | تقييم ومفضلة وملف حساب عبر حسابين | صلاحيات وعزل وعدم تسريب التعليقات/الملف | قبول RATINGS تاريخي معزول فقط؛ لا E2E مستضاف | **BLOCKED** | P1 | AUTH/DEV | [SRC-CONT](https://github.com/merapplications-sketch/Talabat-v3/blob/1cb85361d698d5da787d927a4c9ae7bd213c68c1/docs/continuity/PHASE1-CURRENT.md) |
| C-18 | DineOut Gold/الحملات→عرض→اختيار | تدفق حسب التصميم المعتمد دون أثر مالي خاطئ | لم يُشغّل المسار ولم تتوفر fixture متصلة | **UNTESTED** | P2 | DEV | [SRC-C](https://github.com/merapplications-sketch/Talabat-v3/blob/1cb85361d698d5da787d927a4c9ae7bd213c68c1/customer.html) |
| C-19 | Group order: إنشاء/إغلاق→checkout | تجميع صحيح بلا خصومات أو تكرار غير مصرّح | راجعت grpCheckout وتجميع البنود فقط؛ لا تشغيل خادم | **PARTIAL** | P1 | DEV/API | [SRC-C](https://github.com/merapplications-sketch/Talabat-v3/blob/1cb85361d698d5da787d927a4c9ae7bd213c68c1/customer.html) |
| C-20 | التذاكر/طلب رد→خطأ→إعادة فتح | بقاء الطلب ومرجع الاستجابة والإجراء الصحيح | واجهات موجودة؛ الفحص المالي/HTTP لم يُنفذ | **BLOCKED** | P1 | DEV/FIN | [SRC-CORE](https://github.com/merapplications-sketch/Talabat-v3/blob/1cb85361d698d5da787d927a4c9ae7bd213c68c1/talabat-core.js) |

## 4. Driver functional scenario matrix (14)

| ID | خطوات الحالة | المتوقع | الفعلي وحد الإثبات | الحالة | أولوية محتملة | مسؤول/اعتمادية | دليل |
|---|---|---|---|---|---|---|---|
| D-01 | دخول سائق/حساب غير مخول→محاولة driver RPC | عزل الدور ورفض غير المخول على الخادم | نموذج دخول المعاينة متاح دون هوية اختبار؛ لا تحقق RBAC | **BLOCKED** | P1 | AUTH | [SRC-D](https://github.com/merapplications-sketch/Talabat-v3/blob/1cb85361d698d5da787d927a4c9ae7bd213c68c1/driver.html) |
| D-02 | بدء نوبة مع server ping فاشل | لا تظهر متصل حتى إقرار الخادم | startShift يضبط online=true ويتجاهل ping().ok؛ ملاحظة مصدر لا تنفيذ | **PARTIAL** | P1 | DEV | [SRC-D](https://github.com/merapplications-sketch/Talabat-v3/blob/1cb85361d698d5da787d927a4c9ae7bd213c68c1/driver.html) |
| D-03 | عرضين→قبول سريع مكرر/قبول متنازع | قبول وحيد ونتيجة taken موثقة | driverAccept RPC موجود؛ لا جلسات سائقين/طلبات اصطناعية | **PARTIAL** | P1 | DEV/API | [SRC-CORE](https://github.com/merapplications-sketch/Talabat-v3/blob/1cb85361d698d5da787d927a4c9ae7bd213c68c1/talabat-core.js) |
| D-04 | رفض عرض مراراً/بعد انتهاء المهلة | لا تكرار أو انتقال غير صحيح | decline يرسل RPC؛ لا اختبار ديناميكي | **PARTIAL** | P2 | DEV/API | [SRC-D](https://github.com/merapplications-sketch/Talabat-v3/blob/1cb85361d698d5da787d927a4c9ae7bd213c68c1/driver.html) |
| D-05 | GPS إذن/رفض/تراجع→دقة وإرسال متقطع | حالة جغرافية صريحة ولا تشويش تتبع | watchPosition وsendLocation قرئا؛ بلا جهاز/خادم تجريبي | **BLOCKED** | P2 | DEV | [SRC-D](https://github.com/merapplications-sketch/Talabat-v3/blob/1cb85361d698d5da787d927a4c9ae7bd213c68c1/driver.html) |
| D-06 | arrived store→ready→pickedup→arrived customer | منع القفز والتكرار والفشل الواضح | SWB يمنع نقر خطوة خلال الطلب؛ لا E2E متسلسل | **PARTIAL** | P1 | DEV/API | [SRC-D](https://github.com/merapplications-sketch/Talabat-v3/blob/1cb85361d698d5da787d927a4c9ae7bd213c68c1/driver.html) |
| D-07 | تشغيل النوبة→انقطاع→عودة/إغلاق | حالة الخادم والسائق متسقة بعد الاستعادة | غياب بيئة اتصالات اختبار وحالة طلب متصلة | **BLOCKED** | P1 | DEV/API | [SRC-CORE](https://github.com/merapplications-sketch/Talabat-v3/blob/1cb85361d698d5da787d927a4c9ae7bd213c68c1/talabat-core.js) |
| D-08 | تسليم كاش أقل/أكثر/مساوٍ للمستحق | تطبيق السياسة المعتمدة في UI وDB | المصدر يسمح بغير المساوي مع ملاحظة؛ تحقق السياسة والنشر مفقود | **PARTIAL** | P1 | FIN/OWNER | [SRC-SQL](https://github.com/merapplications-sketch/Talabat-v3/blob/1cb85361d698d5da787d927a4c9ae7bd213c68c1/sql/schema_patch34.sql) |
| D-09 | ترك على الباب→صورة مفقودة/فاسدة/نجاح | لا إتمام دون إثبات، وصلاحية مسار الصورة | تحقق مصدر photo_required/path؛ Storage غير متاح للاختبار | **PARTIAL** | P1 | DEV/STORAGE | [SRC-SQL](https://github.com/merapplications-sketch/Talabat-v3/blob/1cb85361d698d5da787d927a4c9ae7bd213c68c1/sql/schema_patch34.sql) |
| D-10 | نقر «تأكيد التسليم» مرتين أثناء تأخر RPC | طلب واحد أو استجابة idempotent موثقة | لا pending lock في confirmDeliver وزرها؛ لا أثر DB منفذ | **PARTIAL** | P1 | DEV/API | [SRC-D](https://github.com/merapplications-sketch/Talabat-v3/blob/1cb85361d698d5da787d927a4c9ae7bd213c68c1/driver.html) |
| D-11 | إرسال رسالة ثم قطع الشبكة/رفض insert | الرسالة لا تمحى دون تأكيد حفظ | sendChat يمسح الحقل قبل استجابة TLB.chat؛ ملاحظة مصدر مثبتة | **PARTIAL** | P2 | DEV | [SRC-D](https://github.com/merapplications-sketch/Talabat-v3/blob/1cb85361d698d5da787d927a4c9ae7bd213c68c1/driver.html) |
| D-12 | عرض المستحقات والإغلاق المالي والتسويات | تطابق دفتر المستحقات والإيصالات | غياب ربط ledger/payable الفعلي وoracle معتمد | **BLOCKED** | P1 | FIN/DB | [SRC-CONT](https://github.com/merapplications-sketch/Talabat-v3/blob/1cb85361d698d5da787d927a4c9ae7bd213c68c1/docs/continuity/PHASE1-CURRENT.md) |
| D-13 | رابط خريطة→موقع مطعم/عميل→عودة | إحداثيات صحيحة وملاحة قابلة للاستئناف | توليد الروابط مقروء؛ لا GPS/جهاز فعلي | **UNTESTED** | P2 | DEV | [SRC-D](https://github.com/merapplications-sketch/Talabat-v3/blob/1cb85361d698d5da787d927a4c9ae7bd213c68c1/driver.html) |
| D-14 | إعادة فتح السائق منتصف الطلب→تنازع تحديثين | حالة خادم واحدة ولا انتقال غير مشروع | لا حالة اصطناعية متزامنة أو جلسة معزولة | **BLOCKED** | P1 | API | [SRC-CORE](https://github.com/merapplications-sketch/Talabat-v3/blob/1cb85361d698d5da787d927a4c9ae7bd213c68c1/talabat-core.js) |

## 5. Backend/security/finance integration matrix (17)

| ID | خطوات الحالة | المتوقع | الفعلي وحد الإثبات | الحالة | أولوية محتملة | مسؤول/اعتمادية | دليل |
|---|---|---|---|---|---|---|---|
| B-01 | جرد واجهات REST/RPC ونداءات العميل/السائق | تحديد عقد كل إدخال/خروج ونقطة النسخة | استُخرجت استدعاءات place_order, driver_accept, deliver_order وغيرها؛ لا مطابقة HTTP | **PARTIAL** | P2 | API | [SRC-CORE](https://github.com/merapplications-sketch/Talabat-v3/blob/1cb85361d698d5da787d927a4c9ae7bd213c68c1/talabat-core.js) |
| B-02 | Auth/MFA/RBAC: أدوار/مفاتيح جلسة/انتحال | رفض غير المخول وعدم كشف هويات | لا trace request-scoped ولا هوية اختبار مطابقة للبيئة | **BLOCKED** | P1 | AUTH | [SRC-CONT](https://github.com/merapplications-sketch/Talabat-v3/blob/1cb85361d698d5da787d927a4c9ae7bd213c68c1/docs/continuity/PHASE1-CURRENT.md) |
| B-03 | تسريب بيانات بين حسابين/مستأجرين | عدم رؤية طلبات/محافظ/عناوين الآخرين | لم تُجرَ محاولات cross-account على DB | **BLOCKED** | P1 | AUTH/DB | [SRC-CONT](https://github.com/merapplications-sketch/Talabat-v3/blob/1cb85361d698d5da787d927a4c9ae7bd213c68c1/docs/continuity/PHASE1-CURRENT.md) |
| B-04 | إرسال طلبين متزامنين بنفس p_key | إنشاء طلب واحد وحساب واحد | العقد المصدر والمراجعة106 محفوظان؛ لا HTTP جديد على البيئة المقصودة | **PARTIAL** | P1 | API | [SRC-CI106](https://github.com/merapplications-sketch/Talabat-v3/actions/runs/42829377671) |
| B-05 | timeout/unknown بعد commit→replay بنفس المفتاح | إجابة مرجعية دون إعادة صرف/تحصيل | أدلة سابقة synthetic فقط؛ لا قناة HTTP/RPC مستضافة | **BLOCKED** | P1 | API | [SRC-QA106](https://github.com/merapplications-sketch/Talabat-v3/blob/1cb85361d698d5da787d927a4c9ae7bd213c68c1/docs/review/continuation106/RESULTS.md) |
| B-06 | SERIALIZABLE/RR/RC وإغلاق المفتاح | لا أثر بعد الإغلاق ومعاملة غير مدعومة | CI106 النجاح مثبت على SHA آخر؛ ليس اختبار SHA الحالي/المضيف | **PARTIAL** | P1 | DB | [SRC-CI106](https://github.com/merapplications-sketch/Talabat-v3/actions/runs/42829377671) |
| B-07 | تسلسل status/إعادة محاولة بعد تغيير حالة | الانتقال مرة واحدة ورفض transition خاطئ | SQL34 يتحقق من السائق وpickedup عند delivery؛ عقد النشر غير مثبت | **PARTIAL** | P1 | DB | [SRC-SQL](https://github.com/merapplications-sketch/Talabat-v3/blob/1cb85361d698d5da787d927a4c9ae7bd213c68c1/sql/schema_patch34.sql) |
| B-08 | عميل يرسل سعر/خصم/رسوم مخالفة للخادم | الخادم يحسب oracle مستقل ويمنع التلاعب | قبول PRICE تصحيحات معزولة فقط؛ لا HTTP target | **PARTIAL** | P1 | FIN/API | [SRC-CONT](https://github.com/merapplications-sketch/Talabat-v3/blob/1cb85361d698d5da787d927a4c9ae7bd213c68c1/docs/continuity/PHASE1-CURRENT.md) |
| B-09 | عمولات/بقشيش/نصيب سائق عبر تغير الإعدادات | snapshot ودقة حسابية دون أثر رجعي | TIP/PRICE أدلة محفوظة في حدودها؛ دفتر فعال غير مثبت | **PARTIAL** | P1 | FIN | [SRC-AGREED](https://github.com/merapplications-sketch/Talabat-v3/blob/1cb85361d698d5da787d927a4c9ae7bd213c68c1/docs/OWNER-AGREEMENTS-AR.md) |
| B-10 | تسوية نقد/مستحق→إعادة إرسال/تنازع | إيصال واحد ودفتر مستحق قابل للتدقيق | CC-E01/G1-C/E ما تزال ناقصة؛ ممنوع تحريك الأموال | **BLOCKED** | P1 | FIN/DB | [SRC-CONT](https://github.com/merapplications-sketch/Talabat-v3/blob/1cb85361d698d5da787d927a4c9ae7bd213c68c1/docs/continuity/PHASE1-CURRENT.md) |
| B-11 | دفع إلكتروني/استرداد→فشل طرف ثالث | عدم التكرار أو إنهاء مطالبة قبل قبض فعلي | لا sandbox gateway مُعتمد أو reconciliation خارجي | **BLOCKED** | P1 | FIN/OPS | [SRC-AGREED](https://github.com/merapplications-sketch/Talabat-v3/blob/1cb85361d698d5da787d927a4c9ae7bd213c68c1/docs/OWNER-AGREEMENTS-AR.md) |
| B-12 | Promo/loyalty/wallet: سباق واستنزاف رصيد | ذرية العملية وحدود redeemed/deductions | أدلة محلية سابقة؛ لا تحقق مباشر للنشر والـ oracle | **PARTIAL** | P1 | DB/FIN | [SRC-QA106](https://github.com/merapplications-sketch/Talabat-v3/blob/1cb85361d698d5da787d927a4c9ae7bd213c68c1/docs/review/continuation106/RESULTS.md) |
| B-13 | Storage proofs وSigned URL TTL/ACL | عدم وصول سائق لملف غيره وانتهاء الرابط | الدوال موجودة لكن bucket policy ومزود الاختبار غير مثبتين | **BLOCKED** | P1 | STORAGE/AUTH | [SRC-CORE](https://github.com/merapplications-sketch/Talabat-v3/blob/1cb85361d698d5da787d927a4c9ae7bd213c68c1/talabat-core.js) |
| B-14 | إجراء إداري غير مصرح/اختراق API خاص | رفض request وتوثيق المسار والrole والtenant | لا trace backend/request id ولا grants فعالة | **BLOCKED** | P1 | AUTH/DB | [SRC-CONT](https://github.com/merapplications-sketch/Talabat-v3/blob/1cb85361d698d5da787d927a4c9ae7bd213c68c1/docs/continuity/PHASE1-CURRENT.md) |
| B-15 | فقد اتصال/مهلة/إعادة المحاولة/تصادم متزامن | لا كسر للذرية ولا تأكيد كاذب | دليل محلي سابق فقط؛ لم تتوفر local isolated backend متصلة | **BLOCKED** | P1 | API/DB | [SRC-QA106](https://github.com/merapplications-sketch/Talabat-v3/blob/1cb85361d698d5da787d927a4c9ae7bd213c68c1/docs/review/continuation106/RESULTS.md) |
| B-16 | dispatch_tick/realtime عند غياب عميل متصل | تحريك الطلبات من خدمة مجدولة مستقلة | الجدولة في المتصفح مقروءة؛ scheduler خارجي فعّال غير مثبت | **PARTIAL** | P1 | OPS | [SRC-CORE](https://github.com/merapplications-sketch/Talabat-v3/blob/1cb85361d698d5da787d927a4c9ae7bd213c68c1/talabat-core.js) |
| B-17 | مصدر/CI/build→الإصدار النشط→الرجوع | سلسلة SHA/digest/بيئة/roll-back مثبتة | لا Actions على HEAD الحالي ولا release→deployment حديث موثق | **BLOCKED** | P1 | PUBLISHER | [SRC-CONT](https://github.com/merapplications-sketch/Talabat-v3/blob/1cb85361d698d5da787d927a4c9ae7bd213c68c1/docs/continuity/PHASE1-CURRENT.md) |

## 6. Executed deterministic *source-inspection* checks (NOT runtime behavior)

These 14 checks inspected the **actual source file contents** by path and blob SHA. They tested code-structure conditions only; the negative results are evidence of missing client/source guards, not reproduced network/production failures.

| ID | Source criterion | Static result | Source lines | Priority if runtime/policy validated |
|---|---|---|---|---|
| S01 | Checkout lock `S.busy` | **PASS** | [customer:1427](https://github.com/merapplications-sketch/Talabat-v3/blob/1cb85361d698d5da787d927a4c9ae7bd213c68c1/customer.html#L1427) | P1 |
| S02 | Restore `S.okey` per-account storage | **PASS** | [customer:1330–1346](https://github.com/merapplications-sketch/Talabat-v3/blob/1cb85361d698d5da787d927a4c9ae7bd213c68c1/customer.html#L1330-L1346) | P1 |
| S03 | `p_key` sent to `place_order` | **PASS** | [core:1247](https://github.com/merapplications-sketch/Talabat-v3/blob/1cb85361d698d5da787d927a4c9ae7bd213c68c1/talabat-core.js#L1247-L1256) | P1 |
| S04 | Delivery quote required before client checkout | **PASS** | [customer:1427–1446](https://github.com/merapplications-sketch/Talabat-v3/blob/1cb85361d698d5da787d927a4c9ae7bd213c68c1/customer.html#L1427-L1446) | P1 |
| S05 | Customer cancel in-flight guard `S.cxb` | **PASS** | [customer:1450–1461](https://github.com/merapplications-sketch/Talabat-v3/blob/1cb85361d698d5da787d927a4c9ae7bd213c68c1/customer.html#L1450-L1461) | P1 |
| S06 | Driver step `SWB` in-flight guard | **PASS** | [driver:162–173](https://github.com/merapplications-sketch/Talabat-v3/blob/1cb85361d698d5da787d927a4c9ae7bd213c68c1/driver.html#L162-L173) | P1 |
| S07 | Driver chat draft remains on insert failure | **FAIL** | [driver:146](https://github.com/merapplications-sketch/Talabat-v3/blob/1cb85361d698d5da787d927a4c9ae7bd213c68c1/driver.html#L146) | P2 |
| S08 | Driver online state requires `ping().ok` | **FAIL** | [driver:124–137](https://github.com/merapplications-sketch/Talabat-v3/blob/1cb85361d698d5da787d927a4c9ae7bd213c68c1/driver.html#L124-L137) | P1 |
| S09 | Driver delivery handler in-flight lock | **FAIL** | [driver:155–159](https://github.com/merapplications-sketch/Talabat-v3/blob/1cb85361d698d5da787d927a4c9ae7bd213c68c1/driver.html#L155-L159) | P1 |
| S10 | SQL34 owner/status guard before delivery | **PASS** | [SQL34:47–54](https://github.com/merapplications-sketch/Talabat-v3/blob/1cb85361d698d5da787d927a4c9ae7bd213c68c1/sql/schema_patch34.sql#L47-L54) | P1 |
| S11 | SQL34 rejects less-than-due even with note | **FAIL** | [SQL34:59–67](https://github.com/merapplications-sketch/Talabat-v3/blob/1cb85361d698d5da787d927a4c9ae7bd213c68c1/sql/schema_patch34.sql#L59-L67) | P1 / POLICY |
| S12 | SQL34 leave-at-door photo/path check | **PASS** | [SQL34:47–60](https://github.com/merapplications-sketch/Talabat-v3/blob/1cb85361d698d5da787d927a4c9ae7bd213c68c1/sql/schema_patch34.sql#L47-L60) | P1 |
| S13 | Confirmation button disabled during pending delivery RPC | **FAIL** | [driver:269](https://github.com/merapplications-sketch/Talabat-v3/blob/1cb85361d698d5da787d927a4c9ae7bd213c68c1/driver.html#L269) | P1 |
| S14 | Core chat insert has success/error return | **PASS** | [core:1335](https://github.com/merapplications-sketch/Talabat-v3/blob/1cb85361d698d5da787d927a4c9ae7bd213c68c1/talabat-core.js#L1335) | P2 |

**Independent static totals:** 9 PASS / 5 FAIL of 14 assertions. Do **not** interpret as 64% app correctness or a platform win rate.

## 7. New source-confirmed observations, not reproduced runtime defects

### F-01 · P1 proposed · driver presence can diverge on ping failure
- [`driver.html#L124-L137`](https://github.com/merapplications-sketch/Talabat-v3/blob/1cb85361d698d5da787d927a4c9ae7bd213c68c1/driver.html#L124-L137): `const ping=()=>TLB.ping(online)`; `startShift` sets `online=true` before `await ping()` and does not inspect `{ok:false}`. The [core ping wrapper](https://github.com/merapplications-sketch/Talabat-v3/blob/1cb85361d698d5da787d927a4c9ae7bd213c68c1/talabat-core.js#L933) explicitly maps RPC error/rejection to `{ok:false}`.
- **Reproduction for approved isolated test later:** stub `TLB.ping` to return `{ok:false}`; invoke Start Shift; compare client online display vs server state. Not executed in this audit.
- **Proposed fix, NOT applied:** acknowledge online only after successful server ping; preserve pending/offline/error state and controlled retry; test rapid toggles and reload.

### F-02 · P1 proposed · delivery confirmation may issue concurrent RPC calls
- [`driver.html#L155-L159`](https://github.com/merapplications-sketch/Talabat-v3/blob/1cb85361d698d5da787d927a4c9ae7bd213c68c1/driver.html#L155-L159) waits for `finish()` without an in-flight confirmation guard; [button#L269](https://github.com/merapplications-sketch/Talabat-v3/blob/1cb85361d698d5da787d927a4c9ae7bd213c68c1/driver.html#L269) disables only for upload/missing photo, not network pending. Repeated clicks can therefore call `TLB.deliver` while previous call is unresolved.
- [SQL34#L47-L70](https://github.com/merapplications-sketch/Talabat-v3/blob/1cb85361d698d5da787d927a4c9ae7bd213c68c1/sql/schema_patch34.sql#L47-L70) checks locked row and status, which *could* reject a second completion in that **candidate**, but active DB/source parity is not established. **No duplicate settlement or delivered order is asserted.**
- **Later isolated test:** hold first synthetic deliver RPC response, double-click; count calls, verify single DB update/financial effect and stable UI. **No fix now.** Proposed later client pending lock + server idempotent outcome contract.

### F-03 · P2 proposed · driver chat draft may be lost after send failure
- [`driver.html#L146`](https://github.com/merapplications-sketch/Talabat-v3/blob/1cb85361d698d5da787d927a4c9ae7bd213c68c1/driver.html#L146) clears `e.value` before calling `TLB.chat`, with no `await`, rejection handling or restore. [Core chat insert#L1335](https://github.com/merapplications-sketch/Talabat-v3/blob/1cb85361d698d5da787d927a4c9ae7bd213c68c1/talabat-core.js#L1335) returns a promise; error can be reported but draft is already gone.
- **Later isolated test:** force rejected synthetic insert and reload, verify draft preserved and no duplicate message. Proposed later ack-based clear and per-order draft retention. **No implementation.**

### F-04 · P1 policy/financial contract *discrepancy*, not proven live defect
- [`driver.html#L155-L159`](https://github.com/merapplications-sketch/Talabat-v3/blob/1cb85361d698d5da787d927a4c9ae7bd213c68c1/driver.html#L155-L159) permits nonmatching cash amount when a note is entered. [`sql/schema_patch34.sql#L59-L67`](https://github.com/merapplications-sketch/Talabat-v3/blob/1cb85361d698d5da787d927a4c9ae7bd213c68c1/sql/schema_patch34.sql#L59-L67) likewise allows unequal collection with nonempty note, including **less than due**.
- The owner's latest prior management summary raised rejection of under-collection, but the exact final approved CASH policy change and effective SQL writer have **not been proven** by this audit. [Approved CASH-01](https://github.com/merapplications-sketch/Talabat-v3/blob/1cb85361d698d5da787d927a4c9ae7bd213c68c1/docs/OWNER-AGREEMENTS-AR.md) governs allocation, not by itself this amount threshold.
- **Next dependency:** manager/owner confirms precise authorized short/over collection rules, finance verifies active `deliver_order` signature and writer/version, independent synthetic test examines <due, =due, >due with/without note. **Do not change cash rules before authorization.**

**P0:** no P0 demonstrated; this does **not** mean none exists. **New confirmed production incident count: zero.** Four source-level findings/candidates are recorded, not falsely elevated to exploited runtime failures.

## 8. Historical acceptances reused only in scope

- **PRICE-01** isolated corrections **ACCEPTED** under independent [`4d6007a5...`](https://github.com/merapplications-sketch/Talabat-v3/blob/4d6007a5cf370bd0d95cbe3ddd70b984191959f3/docs/review/price01-delta-independent/REPORT-AR.md), code `50b796985112002f4c47aa4dd2bd1373ffd7aeff`; no implicit target HTTP/finance approval.
- **RATINGS-INTERNAL-01** read-only isolated candidate **ACCEPTED** [`4edeb6a5...`](https://github.com/merapplications-sketch/Talabat-v3/blob/4edeb6a5fbf3e2036f77011b5a480fc92336780e/docs/review/ratings-internal01-delta-qa/REPORT-AR.md) on `f5a45b7362ea5777633d559d3e9b4ff8e37620f8`; no hosted adapter/browser/RBAC conclusion.
- **TIP** acceptance and **AUDIT107** (`60bbc90d4c8d03311464be049063d0fac3ae18f1`) preserved within the [continuity register](https://github.com/merapplications-sketch/Talabat-v3/blob/1cb85361d698d5da787d927a4c9ae7bd213c68c1/docs/continuity/PHASE1-CURRENT.md); no duplicate tests or retroactive claim.
- **CI106** [run 42829377671](https://github.com/merapplications-sketch/Talabat-v3/actions/runs/42829377671) completed `SUCCESS` on **`86eb978e1aeb2be4a9d90999dc9b5a1267cb33df`**, not current PM/programmer HEAD; the job reports `postgres` and `required106` success. [RESULTS](https://github.com/merapplications-sketch/Talabat-v3/blob/1cb85361d698d5da787d927a4c9ae7bd213c68c1/docs/review/continuation106/RESULTS.md) records 10/10 new groups and other local suites; targeted Supabase, browser, actual iPhone, storage/recovery and current production remain outside that success.
- **Source 35 / 49 files / B01 & historical recovery** accepted only as pre-existing evidence, not rehashed/rebuilt. **G1-A/B/C/E/F PARTIAL; G1-D BLOCKED; PHASE2 NO-GO** per [manager register](https://github.com/merapplications-sketch/Talabat-v3/blob/1cb85361d698d5da787d927a4c9ae7bd213c68c1/docs/continuity/PHASE1-CURRENT.md). No independent gate was silently upgraded.

## 9. CI/build/release and security gaps

- The GitHub Actions query for **`1cb85361d698d5da787d927a4c9ae7bd213c68c1`** returned **0 matching runs**; likewise 0 for programmer branch `651696a3...`. This means *no matching recorded Actions runs in these API responses*, not proof the app fails or that all other checks/deployments are absent. No CI was started or modified.
- Latest visible successful CI106 was 2026-11-10; the public preview displayed `pilot-mobile-20261107.31`, and its **active source SHA/backend/service-version mapping remains unverified**. Earlier deployed handoff is historical only.
- For **Auth/RBAC/MFA/account isolation**, request-scoped authenticated HTTP, database grants, RLS and cross-account negative tests were not executed. Do not infer safety from UI-only guards.
- For **Storage/Signed URLs** and photo paths, source checks are not an inspection of active bucket policies, object TTL or access revocation.
- For **finance/offset**, do not alter historical CASH-01, protected orders #1/#2/#3, #3 settlement, live SQL or active balances. Independent ledger reconciliation, source/version and approved oracle are missing.
- Browser: no real iPhone Safari/keyboard/device evidence in this run; Chromium/WebKit historic outputs are separate and not a physical-device acceptance.

## 10. Blockers, responsibility, and safe next action

| Dependency | Needed evidence / unblock criterion | Owner |
|---|---|---|
| A. Isolated runnable source | Exact `1cb85361d698d5da787d927a4c9ae7bd213c68c1` frontend/Backend build, source lock, no production endpoints; synthetic fixture seed and test runner already permitted | DEV / QA / OPS |
| B. Test accounts/roles | Synthetic customer/driver/merchant/admin identities, authorization matrices, **not** real credentials or profiles | AUTH |
| C. API/DB inspection | Request-scoped redacted HTTP+RLS traces, role and writer mapping, transaction/grant/catalog snapshots from isolated target | API / DB / Security |
| D. Money/Storage | Oracle for discounts/cash/commissions, settlement ledger, proof-bucket access policies; validated sandbox only | FIN / DB / STORAGE |
| E. Current release provenance | active version→build digest→source SHA for 4 clients/core plus CI gate/rollback evidence | Publisher/OPS |
| F. Device/field | Real iPhone Safari scenario and network/offline recovery, separate from emulator | QA / UX auditor |
| G. Financial rule F-04 | Clear owner decision about under/over collection; no inferred policy | Owner / PM / FIN |

## 11. Ordered remediation proposals — **not authorized and not implemented**

1. **P1 — Evidence prerequisite:** establish controlled synthetic Auth/API/DB integration and current release provenance; replay authorization, financial and duplicate-order tests before any GO judgement (DEV/API/OPS/QA).
2. **P1 — F-04 financial rule contract:** confirm exact approved cash undercollection semantics; if prohibited, separately scope front/backend changes with regression and finance review (Owner/PM/FIN).
3. **P1 — F-01 presence acknowledgement:** server-acknowledged online/offline with failure/reload and timeout tests (DEV/API).
4. **P1 — F-02 duplicate delivery calls:** client in-flight guard and server idempotency/transition evidence, with two-session synthetic contention (DEV/API/DB).
5. **P2 — F-03 chat draft retention:** preserve/send/ack failure-retry invariants in driver; compare with already safer customer send behavior (DEV).
6. **P1 — Cross-role/tenant/storage and real device:** independent RBAC, signed URL, dispatch, iPhone and rollback sign-off after isolated test environment is ready (Security/OPS/QA).

**Scope boundary:** This is the **programmer's one Stage-1 handoff**, not the manager's unified project acceptance. Admin UX evidence belongs to its independent designer/auditor assignments. This report is saved in an isolated branch only; no source files, application functions, SQL, CI, production or protected records were edited. **Await manager review/tasking; do not start fixes or Phase2.**
