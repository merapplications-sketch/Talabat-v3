# TALABOT — فهرس خطط المالك الموحد والمراجع الأساسية
**14 نوفمبر 2026 | حالة: OWNER REVIEW / DOCUMENTATION ONLY.**

**هذه الصفحة بوابة وصول إلى جميع الخطط التي ناقشناها**؛ لا تستبدل قرارًا معتمدًا ولا تفوّض التطوير أو نشر أي خدمة. تحفظ الخطط في فرع `docs/owner-pilot-ai-playbook-20261114` فقط، ولم تُدمج إلى `main`. **تتحقق المحادثة الجديدة أولًا من أحدث تعليقات [MASTER #26](https://github.com/merapplications-sketch/Talabat-v3/issues/26) وHEAD قبل قراءة هذه اللقطة التاريخية.**

## 1. قرار التنفيذ من المالك
- **أولًا:** إصدار تجريبي حقيقي من TALABOT: العميل والسائق والمطعم والإدارة، التصميم المعتمد، خرائط حيّة للأدوار الثلاثة، قواعد المعاملات، الأمان، مراقبة/تحذيرات، اختبارات وتجربة على أجهزة حقيقية.
- **ثانيًا:** تقليل استهلاك RAM والخادم وقاعدة البيانات بدون فقدان أي طلب أو مبلغ، مع السعة المقاسة وخطة توسع احتياطية.
- **ثالثًا:** جاهزية Google Play/App Store وفق حسابات المالك، ومستودع GitHub يتحول إلى Private بعد النسخة الأولى وبقرار منفصل يحفظ روابط النشر والصلاحيات.
- **رابعًا:** الميزات المقترحة (المتاجر الإلكترونية، عروض Push، «لا تدق الباب»، عداد الكيلومتر، الطلب من الخارج لطاجيكستان، أفكار المنافسين) **تُدرس فقط** حتى موافقة المالك بندًا بندًا.
- **خامسًا:** بعد إنهاء تطبيق Smile Up، يُقيّم فريقه تطبيق **المبادئ المناسبة** على نظامه، دون تبديل تصميمه أو صلاحياته أو كوده الآن. منصة Claude خيار استئناف محتمل فقط، **لا قرار ترحيل**.

## 2. جدول الخطط — كلها محفوظة

| المجال | الوثيقة الأساسية | الحالة وحدود التفعيل |
|---|---|---|
| **الانطلاق من أي محادثة** | [CROSS-CHAT / Work / Claude](CROSS-CHAT-CLAUDE-HANDOFF-20261114.md) | تعليمات استئناف؛ ليست تكليفًا آليًا |
| **سير عمل المالك والفريق** | [OWNER-PILOT-CONTINUITY](OWNER-PILOT-CONTINUITY-AND-RELEASE-20261114.md) | معتمد كمقترح تنظيمي؛ يحتفظ بالأدوار والتكليف الواحد |
| **القواعد المحمية** | [Original owner agreements](https://github.com/merapplications-sketch/Talabat-v3/blob/1cb85361d698d5da787d927a4c9ae7bd213c68c1/docs/OWNER-AGREEMENTS-AR.md) + [PM continuity](https://github.com/merapplications-sketch/Talabat-v3/blob/docs/phase1-operational-coordination-20261111/docs/continuity/PHASE1-CURRENT.md) | **قرارات APPROVED حاكمة**؛ لا يستبدلها أي مقترح |
| **تسلسل النسخة التجريبية** | [Pilot execution order](../launch/PILOT-EXECUTION-ORDER-20261114.md) + [Gates](../launch/PILOT-GATES.md) | خطة قبول، لا إعلان GO |
| **سيناريوهات QA الحرجة** | [Pilot must-pass tests](../qa/OWNER-PILOT-SHOWSTOPPERS-20261114.md) + [Risk/test priorities](../launch/RISK-AND-TEST-PRIORITIES.md) | اختبارات مقترحة؛ لا PASS دون أثر تشغيل |
| **اختبارات الأمان OWASP** | [ASVS v5.0.0 L2 historical](../qa/OWASP-ASVS-L2-HISTORICAL-VERIFICATION-20261114.md) + [Pilot verification gates](../qa/OWASP-PILOT-SECURITY-EXECUTION-GATES-20261114.md) | معيار أمني قديم موثق؛ مصفوفة 345 الخاصة لا تتنشر للعموم |
| **الأدوات الفعلية** | [Test technology reality](../qa/TEST-TOOLING-REALITY-20261114.md) | AVA ليس المقصود؛ OWASP ASVS هو المرجع؛ لا تثبت أدوات جديدة بلا حاجة |
| **سعة وخوادم وRAM وتنبيهات** | [Proactive capacity & resilience](../launch/PROACTIVE-CAPACITY-RESILIENCE-PLAN-20261114.md) | مراقبة إنذار مبكر وقياسات وRPO/RTO مقترحة؛ ليست مطبقة تلقائيًا |
| **Cloudflare/Supabase/حفظ المعلومات** | [Admin alerts and data safety](../launch/ADMIN-ALERTS-FREE-HOSTING-DATA-SAFETY-20261114.md) | القنوات المستقلة، quota, backup/restore مطلوبة؛ لا تغييرات موفرة |
| **الدروس من Uber** | [Uber engineering: Memory/QALM/Retry/GPS](../research/UBER-ENGINEERING-RELIABILITY-LESSONS-20261114.md) | دراسة مصدرية + تطبيقات مقترحة؛ لا نسخ بنية Uber |
| **المتاجر وتوزيع الأدوار** | [Android/iOS/Admin/Merchant/GitHub privacy](../release/PLATFORM-DISTRIBUTION-AND-REPO-PRIVACY-20261114.md) | خطة جاهزية، لا إنشاء اشتراكات أو نشر |
| **الميزات الجديدة المستقبلية** | [Owner prioritized proposals](../roadmap/OWNER-PRIORITIZED-PROPOSALS-20261114.md) + [Earlier post-pilot proposals](../roadmap/POST-PILOT-PROPOSALS.md) | **FUTURE — AWAIT OWNER FEATURE APPROVAL** |
| **المقارنة العالمية** | [Competitor features & risks](../research/TALABOT-Competitive-Features-Risks-20261114.md) + [HTML](../research/TALABOT-Competitive-Features-Risks-20261114.html) | معلومات/مقارنة، لا افتراض أن ميزة غير موجودة بدون فحص الكود |
| **Smile Up لاحقًا فقط** | [Future reliability transfer after Smile Up completion](../roadmap/SMILE-UP-FUTURE-RELIABILITY-ADOPTION-20261114.md) | مؤجل؛ **لم يُلمس مستودع Smile Up** |

## 3. آخر حالة فعلية وقت حفظ الفهرس — لا تنقلها كحالة حية لاحقًا
1. [Stage18 #44](https://github.com/merapplications-sketch/Talabat-v3/issues/44) صادَق المالك على **معاينة Safari اصطناعية مستقلة ومجانية فقط**.
2. [Stage20 #46](https://github.com/merapplications-sketch/Talabat-v3/issues/46#issuecomment-6877406578) **BLOCKED**: يوجد إسناد Pages Read/Write ومصدر GitHub الثابت، لكن Direct Upload عبر الموصل يحتاج JWT لا يمكن تمريره بالطريقة الموثقة؛ Free account eligibility لم تثبت؛ لم يتم إنشاء معاينة جديدة أو رابط.
3. **تقدّم منفصل أحدث:** استلم المدير ZIP الأصلي في **بيئة محادثته**، وأكد SHA/59 ملفًا، ثم نفّذ [Stage16B محدودة](https://github.com/merapplications-sketch/Talabat-v3/blob/6e6af296858dce4d15002bc0cd10d305ced75883/docs/qa-first-20261114/STAGE16B-OWNER-UPLOADED-ZIP-CHROMIUM-INMEMORY-QA.md): 8/8 initial viewport smoke عبر `about:blank` مع أصول أصلية ومحاكاة التخزين وحجب الشبكة، وبعض تفاعل القوائم والسلة. **ليس HTTP/CSP origin أو Safari فعليًا**؛ ملفات ZIP لم تصل تلقائيًا لبيئة الناشر.
4. QA **الإصدار التشغيلي الحقيقي** بقي مرجعًا مستقلاً: آخر [تقرير QA](https://github.com/merapplications-sketch/Talabat-v3/blob/0ab523782ee1bf6f69e2e3be7ec6e96394d9ce6a/docs/qa-first-20261113/MASTER-QA-CONSOLIDATED-20261113.md) عنده E2E 0/51، Admin 0/21، G1 0/6 fully accepted؛ هذه ليست 72 FAIL.
5. مصادر المراجعات التاريخية والأدلة المقبولة لا تُفقد أو يُعاد إجراؤها بلا فرق SHA/بيئة يقتضي ذلك؛ F-01..04 مصدرية مع حدودها.
6. **No deployment/paid service/repo privacy/production code or SQL changes from this index or its companion plans.**

## 4. ما المطلوب عند كل استئناف؟
- افتح آخر [Master Issue #26](https://github.com/merapplications-sketch/Talabat-v3/issues/26) وخذ **المهمة النشطة الحالية فقط** من أحدث تعليق، وراجع SHA/المستودع/الاختبارات المنفذة.
- راجع فقط التغييرات التي جاءت بعد آخر تقرير، ولا تحوّل موافقة على تقرير توثيقي إلى موافقة على التطبيق.
- انتقل إلى دور واحد مع مخرجات واضحة: SOURCE/ENV, PASS/FAIL/BLOCKED/UNTESTED, screenshots/logs, risk, next authorized action.
- **لا تشغّل Work أو Claude تلقائيًا** بسبب وجود CLAUDE.md أو أي Issue. إذا اضطررت لتبديل محادثة، استأنف من Cross-chat، وليس من نصوص رسائل قديمة.
- **لا تتداخل مشاريع Smile Up وTALABOT**؛ تطبيق خطة Smile Up مؤجل لتكليف مستقل بعد اكتمال تطبيقه.

**نقطة الحقيقة:** كل هذه الوثائق تعيش في GitHub وفرع توثيق منفصل، وليس في ذاكرة محادثة فقط. لا اعتماد نهائي للخطط الجديدة أو نقل لفرع الإنتاج قبل قرار المالك.
