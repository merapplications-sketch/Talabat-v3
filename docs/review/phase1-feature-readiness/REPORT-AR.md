# تجهيز الميزات الحالية — تسليم G1 موحد
2026-11-12 Asia/Dushanbe. **DOCUMENTATION DELTA / PENDING INDEPENDENT REVIEW. PHASE1 PARTIAL/BLOCKED; PHASE2 NO-GO.**
أساس هذه الحزمة رأس الإدارة ec4cbd2b89cc1b823131baa744e53e5539eb9c3e. الفرع الجديد مستقل؛ لا تعديل فرع الإدارة أو فروع التنفيذ، ولا دمج فروع متباعدة. لا تشغيل اختبارات أو طلبات تطبيق/مزود أو SQL أو ضغط أو استعادة. قراءة GitHub للوثائق المحفوظة فقط. لا إعادة جرد 61/W/T أو نقل 49 أو مراجعة المقبول.

## الأدلة المقروءة وهوية الحالة
- [السجل الحاكم وأجوبة 35/40](https://github.com/merapplications-sketch/Talabat-v3/blob/ec4cbd2b89cc1b823131baa744e53e5539eb9c3e/docs/continuity/PHASE1-CURRENT.md). الخمسة المؤجلة Q33/Q34/Q35/Q37/Q38 تبقى مؤجلة. Q35 لا يجيز إسقاط الدفع الإلكتروني من شرط الإطلاق.
- [جرد الوظائف التاريخي](https://github.com/merapplications-sketch/Talabat-v3/blob/ec4cbd2b89cc1b823131baa744e53e5539eb9c3e/docs/pilot-20261105/FEATURE-MATRIX.md)، [نطاق التجهيز الأصلي](https://github.com/merapplications-sketch/Talabat-v3/blob/ec4cbd2b89cc1b823131baa744e53e5539eb9c3e/docs/pilot-20261105/OWNER-SCOPE.md). لا تُستعمل حالات النشر أو الأسئلة القديمة فيهما بدلاً من الإجابات الحالية.
- [سجل المصدر والكتّاب](https://github.com/merapplications-sketch/Talabat-v3/blob/ec4cbd2b89cc1b823131baa744e53e5539eb9c3e/docs/review/phase1-completion/SOURCE-DEPLOYMENT-WRITERS.md)، [العقود المالية](https://github.com/merapplications-sketch/Talabat-v3/blob/ec4cbd2b89cc1b823131baa744e53e5539eb9c3e/docs/review/phase1-completion/FINANCIAL-CONTRACTS.md)، [المفاتيح والمصالحة](https://github.com/merapplications-sketch/Talabat-v3/blob/ec4cbd2b89cc1b823131baa744e53e5539eb9c3e/docs/review/phase1-completion/KEYS-RECONCILIATION-RECOVERY.md). صفوف W01..W49/T01..T37 محفوظة؛ الحزمة دلتا عليها وليست جرداً موازياً.
- [القراءات التشغيلية للمستشار](https://github.com/merapplications-sketch/Talabat-v3/blob/464638a21a32b23f19bce375e64727fad0fcc08a/docs/review/phase1-operational-reads/REPORT-AR.md): خصائص 173 دالة و 58 علاقة ضمن مرشح القراءة، لا أجسام حديثة أو عزل API. لا إعادة محاولة الاستعلام المرفوض.
- [PRICE QA](https://github.com/merapplications-sketch/Talabat-v3/blob/4d6007a5cf370bd0d95cbe3ddd70b984191959f3/docs/review/price01-delta-independent/REPORT-AR.md): مصدر 50b796985112002f4c47aa4dd2bd1373ffd7aeff ، أدلة/HEAD efc80a38bf15f8f93f0016e980d180b2f3a546be. قبول التصحيحين فقط؛ PostgreSQL17.6 اصطناعي و Node VM. رؤوس فرع التنفيذ مطابقة عند القراءة.
- [RATINGS QA](https://github.com/merapplications-sketch/Talabat-v3/blob/4edeb6a5fbf3e2036f77011b5a480fc92336780e/docs/review/ratings-internal01-delta-qa/REPORT-AR.md): المرشح/HEAD f5a45b7362ea5777633d559d3e9b4ff8e37620f8 ؛ 10 مجموعات Node مستقلة، منفصلة عن 24 للمبرمج؛ لا PostgreSQL/HTTP.
- TIP: المصدر d76269c9f3e5c02fe0be379ac8ba6356e624f9b8 ، HEAD الأدلة المتحقق 4d1c55c7e16dd9afe3380d4cc5f2482e82a4ea43 ؛ [قبول 3c13f5f](https://github.com/merapplications-sketch/Talabat-v3/blob/3c13f5ff9a36638f2e421e17389d1666bae4487b/docs/review/tip02-qa01-independent/REPORT-AR.md) وفق السجل الحاكم. NULL/TIP-G مقبولان معزولاً؛ لا إعادة اختبار.
- [PREC-03 QA](https://github.com/merapplications-sketch/Talabat-v3/blob/8c0bde7bf8165538e37757e6ff37a0da73e2ec3b/docs/review/g1c-prec03-independent/REPORT-AR.md): قبول إثبات العيب فقط، لا إصلاح.
- الإدارة التصميمية: HEAD المتحقق f28c80e78698137831d149ef4977126d16314048 في talabot-tailadmin-review/review/ux02-v01-v05-candidate-20261112. حكم REVISE السابق على b331c489 لا يُنقل تلقائياً إليه؛ لا تدقيق تصميم جديد هنا. هذه ليست الإدارة التشغيلية.

## سلسلة كل تطبيق: الموجود مقابل الحلقة المفقودة
D1 يعني publication31/published-bytes في سجل المصدر أعلاه: مصدر ea65f5289f3d19ccc5d3dbb65b59650e23e01370 ، hosting41 ، وقت 2026-11-07T20:52:03.422706Z ، byte-match العميل/core فقط.
START اسم مختصر لسجل startup: [HANDOFF](https://github.com/merapplications-sketch/Talabat-v3/blob/ec4cbd2b89cc1b823131baa744e53e5539eb9c3e/docs/pilot-20261105/hosted/startup-20261106/HANDOFF-AR.md)، source0737e54b4f2d0d71a22ea766c54ce869c206e9ce ، pilot-mobile-20261106.2 ، deployment1a602ee4-6daa-4a76-a8aa-68339321cac5. نجاح دخول أربعة أدوار تاريخياً مع بوابة طلبات موقوفة. المضيفان مستقلان؛ لا تجميعهما في سلسلة نشر واحدة.

| المكون/الملف ومراجع الجرد | المصدر والدليل القائم | الإصدار الفعّال الآن / الحلقة الناقصة | حامل الإغلاق |
|---|---|---|---|
| العميل customer.html ؛ A01/W01,W06,W08,W21–27 | D1 بايتات تاريخية؛ START دخول؛ overlays TIP/PRICE أعلاه منفصلة عن root | UNKNOWN ؛ artifact/build ووقت تفعيل وبصمات الملفات المقدمة وربط backend ، لا آخر Git | مسؤول نشر واجهة العميل؛ بطاقة B02 |
| المتجر merchant.html ؛ A02/W05,W07–09,W13,W28–32 | مرجع callsites611b0ebdaa3ed83dd34b623528ea374935a9d8e1 ؛ START دخول؛ جرد الأسعار والتوافر | UNKNOWN ؛ لا byte-match merchant مستقل في D1 ولا إثبات نشر ذاتي/تحديث القائمة المفتوحة الحالي | مسؤول نشر المتجر/النواة؛ B02/B03 |
| السائق driver.html و assets/driver-returns/panel.js ؛ A03/W10–12,W14,W16,W33 | START دخول، جرد رحلة وإرجاع، اختبارات تاريخية في FEATURE-MATRIX | UNKNOWN ؛ artifact للملفين وتوافق RPC ونشر GPS/الإشعارات إن وجدا | مسؤول السائق/النشر؛ B02/B03 |
| الإدارة التشغيلية admin.html و assets/admin-finance/admin-finance.js و assets/finance-receipt/receipt.js ؛ A04/W15,W17–20,W28–32 | START دخول، CASH-01/finance/returns في الجرد | UNKNOWN ؛ إصدار assets وصلاحيات finance/إيصال ونشر backend المقابل | مسؤول الإدارة التشغيلية/المالية؛ B02/B05/B07 |
| talabat-core.js ؛ A05 | D1 byte-match ؛ approvalWrite/finCommand/finReconcile ؛ كل RPC طلب مستقل | UNKNOWN لكل تطبيق؛ لا افتراض أن الأربعة تستخدم core واحداً فعّالاً | مسؤول build/API ؛ B02 |
| backend/Jobs ؛ A07–09 | dispatch_tick callsite وتعريف 107 ؛ ops/pilot-watchdog.py مصدر | scheduler/Worker فعّال و pause/drain UNKNOWN ؛ وجود script أو غياب pg_cron لا يحسم الخدمة الخارجية | مشغّل كل خدمة؛ B03 |
| TailAdmin/الخريطة | مرشح UX أعلاه؛ map851b5bc620aaeae8f9764693cad6dc0cd9cd8438 وفق السجل | معاينة منفصلة؛ لا backend تشغيلي مثبت ولا شمول كل الأقسام | المصمم و QA ضمن مساره؛ لا تعديل هنا |

إغلاق B02 يحتاج ربط كل صف على حدة. محفوظات النشر الحالية لا تكفي لملء active_version ؛ لم يُستدعَ Cloudflare لإعادة محاولة فشل المصادقة المسجل في الإدارة.

## متبقي الوظائف القائمة — دلتا على FEATURE-MATRIX لا إعادة جرد
كل معيار أدناه يخص نطاقه؛ نتائج مراحل 3–5 لا تُطلب قبل عقود المرحلة 1. حامل الدليل اسم وظيفة مسؤولية، لا ادعاء تعيين شخص أو امتلاكنا وصوله؛ يسجل المدير اسم حامل المورد عند تسلم البطاقة.

| الميزة | الأصل الموجود / الحالة | المتبقي المحدد وحامله | معيار الإغلاق وموضعه |
|---|---|---|---|
| الدخول وتجديد الجلسة واسترجاع الحساب | GoTrue/REST محلي، START دخول تاريخي | SMTP/reset/المضيف الفعّال وربط كل دور؛ API/النشر | B02/B05 عقد 1 ؛ رحلة حقيقية مخولة في 5 مع expiry/رفض وعدم كشف |
| انضمام السائق | apply_as_driver/pending بالجرد التاريخي؛ تعديل الرحلة مطلب مستقل | مقترح الإجراء والقرار النهائي غير مثبتين؛ مسؤول السائق/المالك | عرض الحالي والبديل دون وثائق/رسوم مخترعة ثم اعتماد منفصل؛ لا تغيير تسجيل هنا |
| الأصناف والأسعار والساعات والفروع | جرد وحراس؛ نشر المطعم المباشر المؤهل قرار ثابت | دليل save→visible للزبون الجديد والقائمة المفتوحة وعزل فرع؛ المطعم/core و QA | ربط writer في 1 ثم قياس تقارب ورفض غير المخول في 5 ؛ لا حذف approved عالمي |
| العنوان والخريطة | عزل محلي؛ map معاينة | إحداثيات الشركاء والأقسام ودقة المسار/خصوصية القراءة؛ المصمم/API | Q01–08 و Q26–28 محفوظة؛ adapter ومصدر جغرافي بعقد منفصل؛ لا Google fallback |
| السلة/PRICE/إنشاء الطلب | PRICE QA-01/02 و 106/TIP مقبولة معزولاً | Chromium/IndexedDB و Safari/HTTP للمرشح الفعلي، snapshot الهدف؛ QA/API | نقاط حفظ وسيطة، موافقة السعر المتغير، replay بلا إعادة تسعير/خصم؛ لا إعادة المقبول |
| الإكرامية/NULL | TIP02 recovery و NULL/TIP-G مقبولة | TIP-D/F جهاز/متصفح/هدف؛ QA | اختبار دليل فعلي بنفس source و origin ، فصل جهازين عن تبويبات origin ؛ لا تغيير HMAC |
| أول كاش والتحضير | confirmation/IMPLEMENTATION تاريخي | مطابقة Q36=180 ثانية في المرشح، Q37 مؤجل؛ المبرمج/QA | تتبع المهلة والموافقة دون اعتبار الصمت قبولاً؛ أي فرق تنفيذ بتكليف؛ 180 ليست مدة تحمل |
| الإسناد/قبول السائق والتسليم | سباقات محلية تاريخية | تشغيل dispatch/عامل فعلي وعقد retry/drain ، تريغرات الهدف؛ تشغيل/DB | B03 قبل انتقال؛ رحلة بأدوار منفصلة في 5 لا زر مصطنع |
| GPS/Realtime/الملاحة | إحداثيات وملكية محلية | قناة الموقع الفعّالة، رفض الإذن/قدم الموقع/الخلفية؛ السائق/الجهاز | دليل جهاز وشبكة في 5 ؛ Q28 لا مسافة مستقيمة عند فشل الطريق |
| الدفع/المحفظة/الولاء/الخصومات | FINANCIAL-CONTRACTS وقبول المعاملات المحدود | B04 ، PREC-03 ، إعدادات الحملات والممول؛ حافظ المالية/المبرمج | oracle مستقل وإعداد مؤرخ؛ إصلاح PREC مفوض منفصلاً؛ Q35 مؤجل فلا ادعاء اكتمال الدفع |
| CASH-01/التسويات والإيصالات | finance_execute/finReconcile و R1 ؛ تاريخ الإيصال والطباعة | مستلم النقد ومصالحة الإيصال وطباعة فعلية؛ المالية/QA | B07 وخطة اختبار ذري ثم جهاز؛ كشف الأرباح ليس دفعاً |
| الإلغاء/الدعم/RETURN-01 | قبول محلي لمنع التعويض المكرر/المطالبة | ممول الرد الجزئي والتسوية بعد إنفاق الرصيد؛ مالية/عقود | Q24 إلى أصل كل جزء، Q38 رجوع مؤجل؛ لا دين سلبي أو صرف حي مفترض |
| إشعارات الخلفية والمراقبة | watchdog مصدر؛ foreground تاريخي | SW/push/عامل ومستلم تنبيه فعّال غير مثبت؛ التشغيل | إثبات قناة موجودة أو مقترح وظيفة/خدمة وكلفة منفصل؛ لا اعتبار script scheduler |
| صور التسليم و Storage | StorageAPI/restore محلي تاريخي | SU-543851 ، كاميرا جهاز، تفويض بعد revoke ؛ Storage/QA | B08/B09 ثم نفس URL/token و GET/HEAD/Range في 5 ؛ purge لا إصلاح دائم |
| إدارة الوظائف 12/مصفوفة 37/FP16 | UX f28c80e ، V04 محفوظ؛ قبول اللون للمالك منفصل | V01/V03/V05 والدلتا الفنية V02 وصفوف 37 المتأثرة؛ المصمم/مدقق UX | تقرير دلتا على المرشح نفسه، Q40 معاينة لا قبول؛ لا اختراع CRUD/نشر |
| التقييمات | RATINGS قارئ معزول مقبول | adapter كامل التاريخ/لقطة مستقرة و HTTP خصوصية؛ المبرمج/API | لا آخر 300 ، لا rawratings للمتصفح، unavailable≠zero ؛ عقد Q01/Q02 منفصل عن نشر النصوص |
| التعافي/CI/موارد التشغيل | عقود وسكربتات وأدلة قديمة | B06–09 وعقد القياس أدناه؛ تشغيل/CI/QA | عقود وإتاحة 1 ؛ نتائج 3–5 لاحقاً؛ لا ادعاء سعة أو جاهزية |
| حزم iOS/Android والطباعة | FEATURE-MATRIX يميز الويب عن IPA/APK والطابعة | توقيع/حساب متجر/جهاز عند تكليفه؛ مسؤول الإصدار | لا يمنع اختبار الويب ولا يُحذف من سجل المنتج؛ لا شراء أو نشر |

CASH-CHANGE مسار مستقل: Q09–17 حسمت السياسة وتتقدم على PENDING في 00f8386 ؛ لا إعادة سؤال. Q10 يسمح برفع السقف فوق 20 ، لذلك اقتراح قصره 0..20 ليس سياسة. يبقى الحد التقني والتنبيهات وعقد التطبيق بحاجة إعداد؛ M1 مستقل عن CC-E01 ، M3 المقاصة تتوقف على مستحق غير مدفوع/مستخدم و writer تخصيص ذري. هذا لا يوقف تجهيز بقية الميزات.

## حالة البوابات والتسليم
| البوابة | الإضافة هنا | الحكم الإداري |
|---|---|---|
| G1-A | ربط 5 مكونات وملاحقها بفصل مصدر/نشر/مرشح؛ B02 بطاقة قابلة للتسليم | PARTIAL/BLOCKED ؛ الإصدار الفعّال غير مثبت |
| G1-B | ربط الفراغات بالصفوف القائمة وبطاقة caller/transaction/drain | PARTIAL/BLOCKED ؛ لا حصر خارجي مثبت |
| G1-C | Q09–25 إلى العقود، نطاق PREC و oracle/دقة | PARTIAL/BLOCKED ؛ لا إعدادات مؤرخة وعقد تقريب مكتمل |
| G1-D | حقول trace لكل مدخل ودور وقناة إنتاجه | BLOCKED ؛ لا trace request-scoped جديد |
| G1-E | بطاقة metadata مفاتيح ومصالحة بأصول وإيصالات | PARTIAL/BLOCKED ؛ لا إثبات إتاحة تشغيلية |
| G1-F | نطاق نسخ وقنوات ومعايير القياس والتوقف، الأدلة القديمة مفصولة | PARTIAL/BLOCKED ؛ العقود والإتاحة غير مكتملة |

[بطاقات B02–B09 والعقد المالي](EVIDENCE-WORK-PACKETS.md) و[عقد القياس](MEASUREMENT-CONTRACT.md) جزءان من هذا التسليم الواحد. لا أهداف رقمية جديدة معتمدة ولا تشغيل.
الخطوة التالية: استلام مخرجات البطاقات من حامليها، ثم مراجعة المستشار لهذه الدلتا فقط. G1 جميعها تحتاج قبولاً مستقلاً؛ جمع الوثائق لا يمنح GO. لا انتظار نتائج المرحلة 5 لكتابة عقد 1 ، ولا انتقال 2 بغياب اعتماد حاسم. لا إجراء محمي أو مساس بالطلبات#1/#2/#3 ومستحق#3.
