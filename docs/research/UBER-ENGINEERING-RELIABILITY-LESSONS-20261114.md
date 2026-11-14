# TALABOT — دروس Uber Engineering في الذاكرة والاستيعاب والتعافي
**تاريخ البحث:** 14 نوفمبر 2026، دوشنبه | **النطاق:** بحث تقني موجه لنسخة TALABOT التجريبية. **ليس خطة لاستنساخ Uber أو أمر تنفيذ/شراء/نشر.**

## لماذا حفظنا هذا البحث؟
طلب المالك الاحتفاظ بجميع القرارات والدروس السابقة في GitHub حتى لا تضيع عند تغيير المحادثة/المبرمج، مع أولوية **إنهاء النسخة التجريبية الأولى** قبل الميزات الجديدة؛ هذه الدراسة مخصصة لـTALABOT فقط دون الرجوع إلى مستودعات أخرى.

**قانون المصدر:** الحقائق أدناه مدعومة بمدونات Uber الرسمية؛ الأرقام أمثلة من خدمات معينة وتواريخ مختلفة، **وليست سعة TALABOT أو دليل أن Uber تستخدم كل تقنية بالطريقة نفسها اليوم**. المقترحات المخصصة لـTALABOT استنتاجات هندسية تتطلب قياسًا واعتمادًا واختبارًا منفصلًا.

## 1. حقائق موثقة وما الذي نستفيده منها

| مصدر Uber الأصلي وتاريخه | المبدأ الموثق | النقل المبدئي إلى TALABOT |
|---|---|---|
| [Translations at Scale — 15 أكتوبر 2026](https://www.uber.com/us/en/blog/translations-at-scale/) | تحليل memory profiles وGC في خدمات Go؛ مثال كاش ترجمة حمل ~800MB قبل الحل الهجين، ثم metadata ~40MB وعادةً ~80–120MB بعد حد 50,000 عنصر؛ hit ratio >99.9% | **لا ننقل هذا الرقم إلى TALABOT**. نقيس Heap/RSS/CPU، وحجم الكتالوج والصور والاشتراكات وتكرار إعادة التحميل قبل تعديل أي Cache |
| [QALM — 22 مارس 2018](https://www.uber.com/us/en/blog/qalm-qos-load-management-framework/) | فرز الطلبات حسب الأهمية، قياس انتظارها، عزل الموارد للعمليات الحرجة وGraceful Degradation؛ Uber قدّرت أن نسبة من الحوادث التاريخية كانت قابلة للتخفيف | أولوية checkout/driver acceptance/delivery/finance قبل الإحصاءات والعروض؛ **حظر العمل الجديد قبل ACK/الخصم فقط وفق عقد مالك معتمد**؛ لا إلغاء عمليات سابقة |
| [Database overload management — 20 أبريل 2026](https://www.uber.com/us/en/blog/from-static-rate-limiting-to-intelligent-load-management/) | في بنيتها المتعددة العملاء، ضبط ضغط القاعدة عند طبقة التخزين باستعمال التوازي والانتظار وأولوية العمليات وحدود عادلة للمستخدمين؛ فحوص memory/bytes/hot keys مهمة، وليس QPS وحده | راقب **active queries + queue delay + disk IO + response p95/p99 + per-role load**، وحدّ طلبات الداشبورد والبحث عند الحاجة فقط، مع حماية المالية |
| [Retry Storms — 17 سبتمبر 2026](https://www.uber.com/us/en/blog/protecting-against-retry-storms/) | تكرار الطلبات في سلاسل الخدمات قد يضاعف الحمل أثناء انقطاع خدمة واحدة؛ استخدمت Uber تحليل الاعتماديات لتحديد من يملك حق إعادة المحاولة | في TALABOT: retries bounded + exponential backoff/jitter + circuit breaking على الاتصالات المسموح لها، وعدم تكرار checkout/finance دون idempotency؛ قياس network reconnect storm |
| [H3 — 27 يونيو 2018](https://www.uber.com/us/en/blog/h3/) | H3 فهرس خلايا جغرافية سداسية متعدد الدرجات للتحليل/التوزيع المكاني | **لا نضيف H3 تلقائيًا**: نختبر فهارس/PostGIS أولاً في PostgreSQL، ونقارن مسافة الطريق بترتيب الخلايا بعد إثبات اختناق matching |
| [Traffic/ETA — 19 مايو 2026](https://www.uber.com/mx/en/blog/scaling-real-time-traffic/) | GPS pings للرحلات ~كل أربع ثوانٍ، Map Matching على شبكة طرق ثم توقع المرور وETA؛ لا يُثبت وحده أين تحفظ Uber كل نقطة GPS | متطلبات العميل/السائق/Admin: موقع مرخّص، freshness TTL، دقة وخصوصية، فصل خط الطريق عن الخط المستقيم، وإثبات إحداثيات السائق بالخلفية |
| [Global Rate Limiting — 12 فبراير 2026](https://www.uber.com/us/en/blog/ubers-rate-limiting-system/) | تحكم في المعدلات حسب caller/RPC لحماية الخدمة من طرف واحد يستهلك معظم الموارد | حماية API عند **المدخل الحقيقي** وRPC/Supabase، لا الاعتماد فقط على Cloudflare WAF الخاص بالواجهة |
| [Go stack allocation — 7 مايو 2026](https://www.uber.com/us/en/blog/zero-growth-stack-real-gains/) | تقنيات إدارة ذاكرة خاصة بخدمات Go | **لا تبرر الانتقال إلى Go أو Rust**؛ تتبع أسباب التضخم في JavaScript وPostgreSQL أولاً |

**مقاطع الفيديو عن Rust:** تشرح `Ownership` / `Borrowing` / `Drop` لحماية ذاكرة البرمجيات ذات المستوى المنخفض من فئات من الأخطاء. لا تقيس استهلاك TALABOT، ولا تمنع تكرار طلبين أو انهيار خدمة خارجية. **Rust خيار هندسي مؤجل** لخدمة صغيرة مقاسة إن ثبتت الحاجة، وليس عملية إعادة كتابة عامة.

## 2. ما ثبت في TALABOT من المصدر، وما لم يثبت
**مصدر تاريخي معرّف لا يُفترض أنه الإصدار المنشور:** `talabat-core.js`, `customer.html`, `driver.html`, `merchant.html`, `admin.html` من الفرع الإداري `docs/phase1-operational-coordination-20261111`, مرجع `1cb85361d698d5da787d927a4c9ae7bd213c68c1`. Admin الجديد في `merapplications-sketch/talabot-tailadmin-review` على مرشح UX-02؛ آخر HEAD يجب فحصه قبل التقييم.

- يوجد تصنيف تحديثات stat/orders/misc/offers؛ Realtime مع فحص دوري احتياطي؛ Backoff عند بعض الأخطاء وتوقف polling الدوري عندما الصفحة مخفية. **لا تقِس فعالية الإجراءات من مجرد وجود الكود**.
- تحميل الكتالوج يحتوي استعلامات بحدود مصدرية كبيرة للأصناف/الخيارات؛ يحتاج قياس `requests per active user`, `bytes/user`, حجم heap، cold/warm وذاكرة هاتف منخفض المواصفات.
- واجهة السائق تملك Leaflet/OpenStreetMap مع `watchPosition`, مسار إرسال `driver_location` عبر Supabase RPC. **لا إثبات لتتبع Native GPS عند قفل الهاتف ولا خريطة حيّة كاملة للعميل والإدارة**.
- `dispatch_tick` يُستدعى في واجهة المستخدم؛ وجود scheduler خارجي مستقل غير مثبت في تقارير G1.
- مخاطر مصدرية F-01 online قبل ACK، F-02 تداخل تأكيد التسليم، F-03 فقدان مسودة المحادثة، F-04 تعارض تحصيل محتمل مع Q14؛ ليست حوادث تشغيل مثبتة.
- [Master QA الحالي وقت البحث](https://github.com/merapplications-sketch/Talabat-v3/blob/0ab523782ee1bf6f69e2e3be7ec6e96394d9ce6a/docs/qa-first-20261113/MASTER-QA-CONSOLIDATED-20261113.md) يورد 0/51 current-source E2E و0/21 Admin runtime و0/6 G1 fully accepted؛ الفشل بعدم تشغيل الاختبار مختلف عن FAIL.
- [Stage16B الجديد — 14 نوفمبر](https://github.com/merapplications-sketch/Talabat-v3/blob/6e6af296858dce4d15002bc0cd10d305ced75883/docs/qa-first-20261114/STAGE16B-OWNER-UPLOADED-ZIP-CHROMIUM-INMEMORY-QA.md): owner ZIP مُستلم وفُحص داخل **بيئة محادثة المدير**؛ 8/8 دخـول RU/EN × أحجام شاشة في `about:blank` مع شيم اختبار ورفض الشبكة الخارجية. **ليس HTTP-origin/CSP/Safari فعليًا**، ولا يعني أن الناشر يملك الملف نفسه؛ Stage20 JWT upload ما زال BLOCKED.
- لا يوجد دليل حمل فعلي على الإنتاج أو عدد طلبات آمنة/ثانية أو حدود ذاكرة معتمدة.

## 3. خطة تحسين الذاكرة — مشتركة بين العميل والسائق والإدارة والخادم (اقتراح)

| فحص | طريقة القياس المقترحة | معيار قرار الإصلاح |
|---|---|---|
| JS Heap على هاتف العميل | Chrome Performance/Memory, Safari Web Inspector على أجهزة مأذونة، لقطة بداية/بعد 30–60 تنقل/بعد العودة وإعادة تحميل | ارتفاع مستمر غير مستقر بعد تفريغ الواجهات، أو تجمد/قتل التطبيق؛ سجل source SHA والجهاز والمتصفح |
| السائق 2–4 ساعات مع الخريطة | allocated JS heap, markers/map listeners, subscriptions, timer count, battery/network requests, tab suspension | لا تراكم دائم غير ضروري أو تكرار subscription؛ GPS freshness والتتبع مستمران وفق موافقة OS |
| الاستعلامات والصور | Data transfer bytes لكل شاشة/جلسة، `select('*')`, memory of images, image decoding/thumbnail sizing, cache hit | عرض العناصر اللازمة فقط؛ lazy/pagination/thumbnail; لا تغيير السعر/التوافر بصمت من stale cache |
| Realtime reconnect | افصل الشبكة لعدد عملاء اختبار اصطناعي ثم أعدها؛ عدد اتصالات الرسائل والـRPC خلال 1/5 دقائق | لا تصاعد غير محدود للاتصالات، لا Retry Storm، لا طلب أو إشعار مكرر |
| قاعدة البيانات | Supabase Reports: CPU/RAM/IOPS/disk/active connections، slow query plans، lock waits | تحديد الاختناق المقاس قبل pool/index/rate-limiting؛ RLS/المالية لا تضحي بها |
| Background jobs | real scheduler heartbeat, oldest queued job age, retry count, worker memory | المهمة لا تضيع أو تتكرر ماليًا؛ عدم انتظار إتمام Notifications قبل تثبيت order |
| Backup + data recovery | استعادة PostgreSQL+Storage+metadata+key version في بيئة معزولة مع Ledger reconciliation | لا نجاح مزيف، والطلبات/المستحقات مرتبطة بوثيقة إثبات؛ أهداف RPO/RTO تحتاج موافقة وقدرة مزود |

**الفرق الأساسي:** في الهاتف **Heap** يسبب بطئًا أو App termination؛ في الخادم RSS/GC/Out-of-Memory يضرب الاستيعاب؛ في قاعدة البيانات RAM/IO/connections تؤثر على المعاملات؛ **القرص/DB هو المكان الدائم للحقيقة** وليس كاش الهاتف أو Redis.

## 4. حماية الحمل مع أقل استهلاك — خطة بدون أعمال ذاتية
1. **قياس أولاً:** أصغر مورد يحد السعة (DB connections/CPU/IO, Realtime message limits, GPS update fanout, egress, images, mem), ثم baseline يعاد بنفس الحمل والبيانات.
2. **تحسين الاستعلامات:** أحجام صفحات، اختيار الحقول اللازمة، فهرسة الاستعلامات الثقيلة، تجميع عمليات تحديث الحالة بدل تحميل القوائم كلها، تخزين الأصول العامة القابلة لإعادة الإنشاء في CDN، مع إبطال Cache عند تغير السعر/الصنف.
3. **التزامن الآمن:** عمليات ذات هوية فريدة وشرط خادمي ذرّي؛ لا ACK قبل commit/التأكيد الحقيقي. لا تعتمد على زر disabled في الواجهة لضمان السلوك.
4. **إعادة المحاولة المقيّدة:** timeouts مستقلة، backoff+jitter والحد الأعلى للتكرار؛ لا retry تلقائي لعمليات المال دون مفتاح Idempotency ومصالحة.
5. **أولوية العمل:** checkout/driver_accept/deliver/finance/tenant security، يليها realtime critical، ثم notifications، ثم analytics/reports/recommendations. إذا لا طاقة، رفض **طلب جديد قبل قبوله** وفق السياسة المعتمدة، ولا خسارة طلب مثبت سابقًا.
6. **تفريغ المهام الثانوية:** Durable Outbox/Queue لا يتبنى دون حاجة؛ إدخال الأحداث التي يجب عدم فقدها في معاملة دائمة، مع مطابقة Delivery/Acknowledgment.
7. **المراقبة:** داخل Admin + تنبيه خارجي مستقل حتى لو توقف الخادم؛ نظرة p95/p99/error-rate/CPU/IO/disk/connections/Realtime، مع حد مبكر وخطة توسع متفق عليها. ChatGPT hourly ليس real-time monitoring.
8. **الأمان:** OWASP ASVS 5.0.0 L2 التاريخي، WSTG/API Top 10/MASVS، وRLS/Auth/Storage/tenant isolation، ومراقبة retry abuse وDDoS. Cloudflare front-door لا يحمي بشكل تلقائي Supabase RPC الموجه مباشرة.
9. **الاختبار المتدرّج:** unit/static/financial contracts → synthetic E2E → memory soak → baseline/ramp/spike/reconnect → backup recovery → مستقل QA → owner GO/NO-GO. جميع اختبارات الضغط داخل بيئة اصطناعية منفصلة فقط بموافقة مستقلة على المعدلات والموارد والمدة.
10. **لا مبالغة في الأدوات:** لا Rust، Kafka، Redis، Kubernetes أو H3 أو microservice جديدة لمجرد أنها مستخدمة عند Uber؛ أولوية تجربة TALABOT الأصلية.

## 5. ترتيب التنفيذ المرغوب والمراجع
**المرحلة الأولى: Pilot safety** — مصدر بيئة مطابق، الطلب/التسليم/المالية مع Idempotency، صلاحيات RLS، GPS الثلاثي، تصحيح F-01..04 عند تأكيدهما، memory profiling، Alerting وbackup restore، اختبارات E2E.

**المرحلة الثانية: Low-resource optimization** — قياس الطلبات/البايتات، تحسين query/caching/delta refresh، إعادة الاتصال وعزل العمليات الثقيلة، إثبات حدود سعة آمنة (وليس أرقام افتراضية).

**المرحلة الثالثة: Growth-only** — توزيع مكاني PostGIS/H3، Queue/Redis، تحليل/تنبؤ وصول أو backend محسن، ترقية مزود بناء على قياسات وتكلفة موافق عليها.

المراجع الملزمة:
- [Proactive Capacity & Resilience](../launch/PROACTIVE-CAPACITY-RESILIENCE-PLAN-20261114.md)
- [Admin alerts and no-data-loss](../launch/ADMIN-ALERTS-FREE-HOSTING-DATA-SAFETY-20261114.md)
- [Pilot must-pass gates](../qa/OWNER-PILOT-SHOWSTOPPERS-20261114.md)
- [OWASP security gate](../qa/OWASP-PILOT-SECURITY-EXECUTION-GATES-20261114.md)
- [Cross-chat handoff](../management/CROSS-CHAT-CLAUDE-HANDOFF-20261114.md)
- [Owner-approved original contracts](https://github.com/merapplications-sketch/Talabat-v3/blob/1cb85361d698d5da787d927a4c9ae7bd213c68c1/docs/OWNER-AGREEMENTS-AR.md)

**حالة الملف:** محفوظ للدراسة واختبارات مقترحة، **ليس تنفيذًا أو اعتمادًا**. لا تشغيل ضغط، SQL، Cloudflare، Supabase، GitHub Main، مالية، أو تعديل مشروع Smile Up دون موافقة/تكليف مستقل.
