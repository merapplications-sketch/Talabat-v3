# TALABOT — PHASE 1 / EXISTING EVIDENCE COLLECTION
التاريخ: 10 نوفمبر 2026 — Asia/Dushanbe.
الحكم: PARTIAL EVIDENCE COLLECTED / PENDING INDEPENDENT REVIEW.
G1-A..F غير مغلقة؛ المرحلة 2 NO-GO. لا انتقال أو ترحيل.

## ال نطاق والمراجع
بدء المرحلة 1 بتكليف المالك لجمع ال موجود فقط. قبول تصحيحات REVIEW108-C معتمد من تكليف المالك الحالي؛ لم نستنتج منه قبول المرحلة 1 أو إذن قراءة هدف.
الخطة المقبولة: [docs/review/continuation108/TARGET-ALIGNMENT-PLAN.md](https://github.com/merapplications-sketch/Talabat-v3/blob/9a5d3145ddaec9ab4d653053424ed9197d784222/docs/review/continuation108/TARGET-ALIGNMENT-PLAN.md) عند 9a5d3145ddaec9ab4d653053424ed9197d784222.
AUDIT107:60bbc90d4c8d03311464be049063d0fac3ae18f1 ؛ ال مصدر 106:86eb978e1aeb2be4a9d90999dc9b5a1267cb33df. القبول المعزول وإغلاق 107 محفوظان.
فُحص فهرس Git كاملاً (غير truncated) عند المرجع أعلاه. قُرئت 61 ملفات نصية موجودة، بينها جميع ملفات SQL الأربعين تحت sql/، والتطبيقات الأربعة والنواة المشتركة وعقود المرشح وأدلة الاستعادة. بيان SOURCES.json يربط كل ملف ب Git blob ثابت.
لم نشغّل الملفات أو SQL أو اختبارات، ولم نتصل ب Supabase أو Cloudflare. لم تُقرأ أسرار أو بيانات طلبات. الحفظ توثيق فقط.

**مستويات الإثبات:** SOURCE OBSERVED = نص قرئ بهذه الدفعة؛ INHERITED = نتيجة سابقة ب حدودها؛ UNVERIFIED = لا دليل كافٍ. وجود ملف قديم أو proposed أواختبار لا يثبت نشره. جرد ال مصدر أدناه ليس تصريحاً بحصر جميع الخدمات المنشورة. الحزم المشفرة/base64 و ZIP لم تُفك أو تُشغّل؛ ولا ندعي تدقيق كل تاريخ الفروع أو كل خدمة خارج المستودع.

## G1-A..F
| البوابة | ما ثبت من ال موجود | الناقص والإجراء المحدد | ال مسؤول عن توفيره / قبوله | الحكم |
|---|---|---|---|---|
|G1-A ال نطاق وال مصدر|مرجع الخطة وال مصدر وفهرس الملفات؛ 107 يحدد الهدف المعزول؛ بيان 49 موجود|محتوى الأدلة الخام 49 ب قناة خاصة والتحقق من بصماتها؛ ربط ال مصدر ب النشر الفعلي و نطاق العزل؛ البيان لا يعوضها|حافظ أدلة 107 و مسؤول النشر / QA مستقل|PARTIAL / BLOCKED|
|G1-B الكتّاب والآثار|أربعة عملاء ونواة مشتركة ومداخل RPC ونصوص كتّاب SQL وتريغرات تاريخية؛ الجدول أدناه|جرد نشر Workers/Jobs/service_role وتواقيع الهدف وتريغراته المتعدية؛ حدود كل معاملة وآلية أي أثر خارجي وإثبات قابلية التصريف|مشغلو الخدمات و DB / QA مالي وأمني مستقل|PARTIAL / BLOCKED|
|G1-C المال والدقة|اعتماديات وحالات round في المرشح ونصوص تاريخية؛ numeric(12,2) مذكور في 107 وملفات مقترحة|مرجع إعدادات التشغيل و التقريب والتحويل الكامل، وجدول نتائج مستقل يراجعه مختص مالي؛ لا fixture كمرجع أسعار|DB ومختص مالي؛ المالك للتعارض الموثق فقط / QA مالي مستقل|PARTIAL / BLOCKED|
|G1-D الهوية والعزل|حارس 106 وعقود ACL ؛ 107 يثبت منحاً محددة تاريخياً|دليل request-scoped من مسار موجود على الدور والعزل لكل RPC وربطه بالإعداد الفعال؛ جلسة postgres RC لا تكفي|مسؤول API/gateway وأمن / QA مستقل|PARTIAL / BLOCKED|
|G1-E المفاتيح والمصالحة|HMACv1 ومخطط key IDs و bindings والحواجز وعقود unknown واسترجاعالأصل|إتاحة قناة مفاتيح و نسخ قديمة للمخولين دون كشفها، مصدرتجهيز فعلي، مصالحة بين الأجهزة والخدمات، حصصمعتمدة بعدقياس|مسؤولمفاتيح و DB وتشغيل؛ المالك للسياسات / QA مستقل|PARTIAL / BLOCKED|
|G1-F التعافي وخطةالإثبات|اختباراستعادة 106 المحفوظ وأداةاستعادة خارجية اصطناعية مع Storage وتشفير؛ عقوداختبار لاحقة موجودة|نسخمزود فعلية و دليلإتاحة هدفاستعادة و RPO/RTO ؛ أدلة NOT VALID المصرح بها عندالحاجة؛ نطاقجلسات وأجهزة و قناة CI خاصة|مسؤولال نسخ والمنسق والمزود / QA مستقل؛ المالك لل نطاق و RPO/RTO|PARTIAL / BLOCKED|

لا يوجد GO من أي توقيع قائمة أو اكتمال هذا ال تقرير. جميع G1 تحتاج مراجعة قبول دليلها؛ الاعتماد الحاسم الناقص يمنع المرحلة التابعة. ال حالة لا تغيّر حالات البنود 24 الأصلية.

## جرد التطبيقات والمداخل — SOURCE OBSERVED
| البرنامج/المسار | المداخل المرصودة | حدود الإثبات |
|---|---|---|
|[customer.html](https://github.com/merapplications-sketch/Talabat-v3/blob/9a5d3145ddaec9ab4d653053424ed9197d784222/customer.html)|TLB.placeOrder ، confirmOrder ، setStatus ، rateOrder ، orderWallet|العميل يفوض للنواة؛ ليس إثبات صلاحية خادمية أو نشر|
|[merchant.html](https://github.com/merapplications-sketch/Talabat-v3/blob/9a5d3145ddaec9ab4d653053424ed9197d784222/merchant.html)|reviewOrder ، quoteOrderChange ، setStatus ، rejectOrder ؛ إعداداتمطعم مؤثرة|التسعير/المراجعة قد يغيران الطلب؛ يجب ربط نسخة النشر بالـ RPC|
|[driver.html](https://github.com/merapplications-sketch/Talabat-v3/blob/9a5d3145ddaec9ab4d653053424ed9197d784222/driver.html)|driverAccept ، deliver ، setStatus|الاستلام/التسليم يمران بالنواة؛ ليسإثبات دور فعلي|
|[admin.html](https://github.com/merapplications-sketch/Talabat-v3/blob/9a5d3145ddaec9ab4d653053424ed9197d784222/admin.html)|assignDriver ، ticketSetStatus ،واجهاتالمال وإعداداتالمتجر|قد تنشأ آثارعبرالتذاكر والتوزيع؛ لا تختزل فيزرإنشاء|
|[assets/admin-finance/admin-finance.js](https://github.com/merapplications-sketch/Talabat-v3/blob/9a5d3145ddaec9ab4d653053424ed9197d784222/assets/admin-finance/admin-finance.js)|settleCash ، financeReconcile ،قراءةالأحداث والإيصالات|عميلأوامر مالية؛ لايُثبت تكاملدفعخارجي|
|[assets/driver-returns/panel.js](https://github.com/merapplications-sketch/Talabat-v3/blob/9a5d3145ddaec9ab4d653053424ed9197d784222/assets/driver-returns/panel.js)|writeOrderReturn/readOrderReturn|واجهةإرجاع؛ إغلاقمحاولة الطلب مختلفعنالإرجاع المالي|
|[talabat-core.js](https://github.com/merapplications-sketch/Talabat-v3/blob/9a5d3145ddaec9ab4d653053424ed9197d784222/talabat-core.js)|place_order ؛ merchant_review_order ؛ customer_confirm_order ؛ set_order_status ؛ set_prep_time ؛ driver_accept/decline/arrived ؛ deliver_order ؛ reject_order ؛ admin_assign_driver ؛ order_return_action ؛ ticket_set_status ؛ finance_execute ؛ group_create/add/remove/set|مداخل ثابتةومغلّفات approvalWrite ؛ يجب جردتواقيعها وأثرها منالتعريفالفعلي|
|النواةالمشتركة:dispatch_tick|استدعاءدوري عندحاجةالتوزيع، سطر 516|ليس دليلاً على Job خادمي منشور؛ ال جرد يجب أن يشمل تشغيلالمتصفح|
|[tests/native105/build-client.py](https://github.com/merapplications-sketch/Talabat-v3/blob/9a5d3145ddaec9ab4d653053424ed9197d784222/tests/native105/build-client.py)|يبني overlay العميل المقبول ويستدعي build-client104 ؛ يستعيدالمفتاح ويفصلالمسودة|مولّد مرشحاختبار لاخدمة منشورة؛ لا تعتبر root core القديم دليلاً علىفقدإصلاحات 105|
|[ops/pilot-watchdog.py](https://github.com/merapplications-sketch/Talabat-v3/blob/9a5d3145ddaec9ab4d653053424ed9197d784222/ops/pilot-watchdog.py)|مراقبة HTTP ونقلتنبيهات اختياري|النص يصرح بعدمتهيئة scheduler أووجهة فعلية؛ ليسكاتبطلبات مثبتاً|
|Workers/خدماتخارجية/Jobs و service_role|غيرمحصورةمنهذهالملفات|غياب Edge Functions في 107 لايثبتغيابها؛ يلزمبياننشر من مسؤولكلخدمة|

في[talabat-core.js](https://github.com/merapplications-sketch/Talabat-v3/blob/9a5d3145ddaec9ab4d653053424ed9197d784222/talabat-core.js): أوامرالمال عند 260–261 تحفظ request وتستعلم finance_command_status عندالالتباس؛ التعليق ينص أنالغياب لايثبت rollback. عند 1272–1274 تظهر merchant_review_order/customer_confirm_order عبر approvalWrite. عند 1254 يظهر place_order القديم وتهيئة p_wallet لدىالعميل؛ هذه ليست سياسةتقريبالخادم.
تعذر إثبات الحصرالشامل؛ لا تُوصف هذه القائمة بأنها جميع الكتّاب المنشورين.

## جرد SQL ال موجود والتريغرات
تمت قراءة 40 ملف SQL كنص فقط. مسح مواضع CREATE FUNCTION و INSERT/UPDATE/DELETE يحدد **مرشحي الكتابة** وليس parser كاملاً أو إثباتاً للتنفيذ؛ قد يربط نصاً لاحقاً بالتعريف السابق، لذلك لا تعتمد نتائج المسح الخام كحصر معتمد.
- [sql/schema_patch17.sql](https://github.com/merapplications-sketch/Talabat-v3/blob/9a5d3145ddaec9ab4d653053424ed9197d784222/sql/schema_patch17.sql) إلى [sql/schema_patch34.sql](https://github.com/merapplications-sketch/Talabat-v3/blob/9a5d3145ddaec9ab4d653053424ed9197d784222/sql/schema_patch34.sql): نسخ تاريخية متعددة لـ place_order ؛ مداخل driver_accept/admin_assign_driver/set_order_status/set_prep_time/deliver_order/reject_order/driver_arrived ؛ wallet_adjust/settle_driver_cash/ticket_set_status ؛ group_*؛ trg_wallet_return/trg_loyalty/trg_rating_reward و trg_store_phone تظهر ضمن الملفات ذات الصلة. يجب تمييز كتابة مباشرة من قراءة أو trigger متعدٍ عند جرد الهدف؛ لا اختيار آخر رقم patch ك دليل نشر.
- [sql/proposed/pilot_z_cash_confirmation_20261105.sql](https://github.com/merapplications-sketch/Talabat-v3/blob/9a5d3145ddaec9ab4d653053424ed9197d784222/sql/proposed/pilot_z_cash_confirmation_20261105.sql): merchant_review_order/customer_confirm_order و place_order.
- [sql/proposed/pilot_zzzz_cash_allocation_20261106.sql](https://github.com/merapplications-sketch/Talabat-v3/blob/9a5d3145ddaec9ab4d653053424ed9197d784222/sql/proposed/pilot_zzzz_cash_allocation_20261106.sql): snapshot_cash و guard_cash_allocation و cash_allocation_guard و finance_execute ؛ أعمدة cash shares بنوع numeric(12,2).
- [sql/proposed/admin_finance_integrity_20261101.sql](https://github.com/merapplications-sketch/Talabat-v3/blob/9a5d3145ddaec9ab4d653053424ed9197d784222/sql/proposed/admin_finance_integrity_20261101.sql) و[sql/proposed/admin_finance_receipts_20261102.sql](https://github.com/merapplications-sketch/Talabat-v3/blob/9a5d3145ddaec9ab4d653053424ed9197d784222/sql/proposed/admin_finance_receipts_20261102.sql): finance_execute/finance_command_status وقيودتعديل المحفظة وتسوية؛ ملفات proposed ليستإثبات تطبيق.
- [sql/proposed/pilot_zzz_driver_returns_20261106.sql](https://github.com/merapplications-sketch/Talabat-v3/blob/9a5d3145ddaec9ab4d653053424ed9197d784222/sql/proposed/pilot_zzz_driver_returns_20261106.sql) وملفات refund_cap/driver_claim/delivery_proof/payment_guard ضمنبيان المصادر: اعتماديات حماية مسارات الإرجاع والتسليم والتأكيد.
- [tests/native106/isolation.sql](https://github.com/merapplications-sketch/Talabat-v3/blob/9a5d3145ddaec9ab4d653053424ed9197d784222/tests/native106/isolation.sql): security_private.create_order103 للمرشح؛ public.place_order/103/104 موثقةفي عقد 106. ليستدالة مطابقة تلقائياً للهدف القديم.
- [docs/review/continuation107/REPORT-AR.txt](https://github.com/merapplications-sketch/Talabat-v3/blob/9a5d3145ddaec9ab4d653053424ed9197d784222/docs/review/continuation107/REPORT-AR.txt):17 تريغراً غير داخلي و 10 سياسات على الجداول الأساسية في لقطة 107 ؛ لا نستنتج مطابقتها للقائمة التاريخية أو أن عددها حالياً ثابت. تعريفاتها الخام ليست ضمن الحزمة العامة.

## الحسابات المالية والدقة
| المسار | ما قرئ | ما لم يُثبت |
|---|---|---|
|التوصيل|المرشح 106 يستدعي delivery_calc(store,lat,lng,uid)، و 107 يصفاعتماد الهدف على الإعداداتوالمطعموسجلطلبات|قيم الإعداداتو حدودها و نتائجمعتمدةمستقلة؛ البديلالثابتليسمرجعاً|
|Happy Hour|happy_hour_pct في patch29 ؛ المرشح 106 يستعملنتيجته فيحسابخصمالأسطر|ال نسخة المنشورة و الإعداداتوالتوقيتالمعتمد؛ بديل fixture الصفريلايثبتسلوكاً|
|Promo/ولاء|[tests/native103/dependencies.sql](https://github.com/merapplications-sketch/Talabat-v3/blob/9a5d3145ddaec9ab4d653053424ed9197d784222/tests/native103/dependencies.sql) يعرّف promo_codes و loyalty_lots ؛ loyalty_setting فيهثوابتاصطناعية؛ 107 يقرمطابقةنصمساعدات محددةفقط|إعدادات الهدف وجداولهوقيوده، الانتهاءوالتداخل والتوقعات المستقلة|
|المحفظة|106: round(least(p_wallet,v_bal,v_total),2)، ثم INSERTspend ؛ patch29/31 بهما loyalty/cashback/return|تطابقكلالكتابوالتريغرات وآثار المعاملةالمستضافة|
|التقريب|106 سطر 130–131:sum(round(خصمالسطر,2))؛ 158:round للعمولة؛ 174:round لقيمةالنقاط؛ 185–187:تقريبخصم المحفظة|عقدأعمال مستقللكلخطوة/نصفكسر/فيض/NULL ؛ لا تعميمصيغةواحدة علىكلالمال|
|numeric(12,2)|107 يثبتنوع wallet_entries.amount فيالكتالوجالمحفوظ؛ ملف cash_allocation يصرحبه لحقولمحددة|خريطةكلالتحويلات الضمنية/الصريحة وقواعد التقريب المعتمدة في الهدف؛ تحتاجتعريفاتمؤكدة وليسأسهلف ixture|
|تسوية/إرجاع|finance_execute و order_return_action و ticket_set_status والتريغراتمدخلاتمتعدية|أيعلاقةبجهةخارجية، آلية dedup ومصالحة، و حدودمعاملةكلأثر|

مثال يوضح ضرورة تثبيت ال مصدر:patch29 يحسبعمولة بعد v_disc ، بينما patch31 والمرشح 106 يحتويان v_disc و v_hdisc. هذااختلافنصتاريخي وليسعيباً جديداً أوطلبتغييرمعادلة. لا يمكنإنتاج oracle ماليمن نسخةتاريخيةمختارةعشوائياً.
حدودمعاملةالمرشح مثبتةباختباراتهالسابقة ضمن fixture فقط. كلأثرهدف داخلي يحتاج T ، وكلخارجي إنوجد يحتاج X ، وكلاهما R وفقخطة 108. لا يوجدبهذهالقراءة إثباتجديدلذريةالمستضاف أووجودآليةأثرخارجي.

## الصلاحيات والعزل
- SOURCE: مخطط 103 يفعّل RLS لجدول المفاتيح ويسحبمنح client ؛ حارس 106 يقعقبل الأثر ويُرجع unresolved للـ RR/Serializable. هذهعقودمرشح، لا حالة Supabase.
- INHERITED107: authenticated يملك TRUNCATE على order_items ، anon لا؛ سياسة pilot_active_account restrictive ؛ مساعداتماليةخاصة غيرقابلةللتنفيذالمباشر من authenticated. لااختباراستغلال HTTP مثبت.
- INHERITED107: جلسةقراءة postgres كانت RC ، و pre-request محفوظ؛ كلاهما لايثبتدوروعزل API.
- ال مصدرالمشترك يحملمنطق finance_access/my_perms وقراءة finance_audit ؛ تحققالواجهة لايعوض RLS أوتفويض RPC.
- المطلوبمن مسؤول API: إعدادفعالو دليل request-scoped موجود ومصرحبه، لا توليد جلسات/دالة فحص. لا شيء من ذلك نُفذ هنا.

## المفاتيح ومنعالتكرار والمصالحة
[docs/review/continuation103/CONTRACT.md](https://github.com/merapplications-sketch/Talabat-v3/blob/9a5d3145ddaec9ab4d653053424ed9197d784222/docs/review/continuation103/CONTRACT.md) و[tests/native103/schema.sql](https://github.com/merapplications-sketch/Talabat-v3/blob/9a5d3145ddaec9ab4d653053424ed9197d784222/tests/native103/schema.sql):
HMAC-SHA256 v1 ؛ key_id ثابت، MAC32byte ،مفتاحلايقلعن 32byte ،جدول owner-only ،لا rawaddress/recipient في binding. المخططلايوفرمفتاحإنتاج؛ المفاتيحفي الاختبارات مؤقتة. لم نقرأقيممفاتيح.
التحققمنقديم binding يعتمد key_id القديم؛ فقدالمفتاحلايسمحبتبديلالبصمة أوإعادةتصنيفالجديد كتاريخي. تاريخيبلا binding يُسترجعبالقراءةمعالتفويض ولا يُختلقله binding.
[docs/review/continuation105/CONTRACT.md](https://github.com/merapplications-sketch/Talabat-v3/blob/9a5d3145ddaec9ab4d653053424ed9197d784222/docs/review/continuation105/CONTRACT.md): closures وحصةمواردبلاقيمإنتاجية،امتلاءالحصة→unresolved ،لا receipt كاذب؛لا TTL يحذفحاجزاً أوينهي unknown. IndexedDB ينظممتصفحاً/أصلاً،لاتنسيقبينالأجهزة.
SOURCE core:finance_command_status للمصالحة؛ هذاوجود عقدعميل،لاتحققمن المنشور.
الناقص: مسؤولحفظ المفاتيح و دليلالإتاحةوالتدويروال نسخالآمن، جردالمحاولاتو الكتّاب،مصالحةبينالأجهزة والخدمات،قراراتالمواردبعدالقياس. لا طلب أسرار في المحادثة.

## ال نسخ والاستعادة — الأدلة ال موجودة
| المرجع | ما يثبت | ما لا يثبت |
|---|---|---|
|[docs/review/continuation106/RESULTS.md](https://github.com/merapplications-sketch/Talabat-v3/blob/9a5d3145ddaec9ab4d653053424ed9197d784222/docs/review/continuation106/RESULTS.md)|تقريرمحفوظ يشيرلـ CI42829377671 ونجاح pg_dump/restore للطلب/المفتاح/البصمة/closure/policy|لم نعدتشغيل CI أوتفحص artifact الحالي؛ لا مزود/Storage. انتظار QA المذكورفيالوثيقة حالةتاريخية تجاوزها قبول 106 المعزول|
|[tests/native106/restore.py](https://github.com/merapplications-sketch/Talabat-v3/blob/9a5d3145ddaec9ab4d653053424ed9197d784222/tests/native106/restore.py)|شفرةتحضير restore106_source والتحققمن restore106_target ؛ السجلالمتوقع يصف separate synthetic DB|وجود script ليسنتيجةتنفيذجديدة|
|[tests/pilot/external-restore.py](https://github.com/merapplications-sketch/Talabat-v3/blob/9a5d3145ddaec9ab4d653053424ed9197d784222/tests/pilot/external-restore.py)|أداةتفصل runner مصدرعنآخر، pg_dump+Storage tar وتشفيرومقارنةصفوف/دوال/منح/سياسات/تريغرات وصلاحيات Storage|لا دليل نسخ Supabase حالياً، ولا ضمان RPO/RTO ، ولا أنها تشملمخطط 106 دونمطابقة|
|[.github/workflows/pilot-external-restore.yml](https://github.com/merapplications-sketch/Talabat-v3/blob/9a5d3145ddaec9ab4d653053424ed9197d784222/.github/workflows/pilot-external-restore.yml)|workflow موجودللتشفير والاستعادة بعد teardown ،ومفتاحالمستلم يبقىفي runner الاستعادة حسبال عقد|لا إعلاننجاح run لم يُفحص؛ لا تشغيلهنا|
|[docs/review/continuation107/EVIDENCE-MANIFEST.json](https://github.com/merapplications-sketch/Talabat-v3/blob/9a5d3145ddaec9ab4d653053424ed9197d784222/docs/review/continuation107/EVIDENCE-MANIFEST.json)|فهرس 49 معأحجاموبصمات؛النص صريحأنهليس نسخةأرشيفية|لا يُثبتوجود 49 حالياً أوإمكانيةاستعادتها؛ لاتُنشرالخام هنا|
|[docs/review/continuation101/HANDOFF.md](https://github.com/merapplications-sketch/Talabat-v3/blob/9a5d3145ddaec9ab4d653053424ed9197d784222/docs/review/continuation101/HANDOFF.md)|عقد قناةخاصةلـ build-gate/db-evidence وخطةتعافٍ مستقلة|تقريروصول 101 تاريخيوليسفحصصلاحياتحالياً|

## سجلالنواقص وال مسؤوليات
1. حافظأدلة 107: توفير 49 الأصلية للمراجع عبر قناةخاصة ومطابقةبصماتها؛ لا رفعهاالعامة. نقص مصدر لايُحلّباختراعه.
2. مسؤول النشر لكلتطبيق/Worker/Job: مصدرمنشور SHA ،توقيع RPC ،دورالخدمة،جدولالعمل،حد المعاملة،طريقةالتصريف؛ بياناتوصولسرية لا تدخل ال تقرير.
3. DB/مختصمالي: تعريفات الهدف المحفوظة و عقد التقريبو الإعدادات و oracle مستقل. للمالكفقط تعارضأعمالمحدد أو مرجعغيرمعتمد؛لا إعادةقرارقواعدمقبولة.
4. مسؤول API/أمن: دليلعزلودور request-scoped من مصدر موجود؛ يحتاجتفويضمنفصل لأيقراءةمستضافة جديدة.
5. مسؤول المفاتيح و التعافي: إثباتإتاحة المفاتيحالقديمة وال نسخ وسياسةالتدوير والاحتفاظ، هدفاستعادةمنفصل ومصالحة؛ المالك يعتمد RPO/RTO وال نطاقوالسياسات.
6. منسق QA: قناةجلساتمخولة finance/orders/outsider و بياناتاصطناعية وآليةتنظيف، دليل Storage/SU-543851 وجهاز Safari و قناة CI خاص؛ لا اختباراتضمنهذاالتكليف.
7. المراجعالمستقل: قبولأورفضكل G1 وفقال مصدر، لااعتبارال تقريرنفسهإثباتإغلاق.

## ما يحتاجقرار المالك فقط
اختيار/تفويض قناةالأدلةالخاصة وحافظها إذا لم تكنمعتمدة، نطاقأيقراءةمستضافةمستقبلية، RPO/RTO وسياسات المفاتيحوالاحتفاظ، القيمالعدديةللمواردبعدالقياس، وحسمتعارضمالي موثقإنظهر. توفيرال مصدر و جرد النشر وإعداد oracle عملال مسؤولين الفنيين،ليسسؤالاًجديداًللمالك عنكلبند. لاتوجدحاجةلموافقةتنفيذ المرحلة 2 الآن لأنها NO-GO.

## نقطةالاستئناف
مراجعةمستقلة لهذاالجمعالم حدود و SOURCES.json ؛ ثم تكليفجمعالمصادرالناقصةمنحافظها، بدءاً بالأدلة 107 الخام و جرد النشر وال عقد المالي. لا تكرارالفحوصالمقبولة ولا استعلام Supabase أو SQL أواختبارجديد ضمنهذاالحفظ. لا مرحلة 2 أوترحيل.
جميعحواجز HMAC/التاريخ/closures/unknown و rollback للاسترجاعفقط محفوظة؛لا تغيير مصدر أومنح/RLS أوحسابات/MFA أو main/نشر أوطلبات#1/#2/#3 ومستحق#3.
