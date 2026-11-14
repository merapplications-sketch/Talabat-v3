# TALABOT — إنذار الإدارة، اختيار الاستضافة المجانية، وحماية الطلبات من الضياع
**التاريخ:** 14 نوفمبر 2026 | **الحالة:** تصميم وتحقيق مصادر / للمراجعة فقط **NOT IMPLEMENTED**. لا يغير ملف قائم معتمد ولا ينقل الإنتاج ولا يشغّل اختبارات ضغط ولا ينشئ نفقات.

## قرار المالك الذي نطبقه في التخطيط
- الإنذار يجب أن يصل **داخل لوحة الإدارة وخارج ChatGPT** أيضًا، وحتى إن تعطّل تطبيق TALABOT.
- الأولوية للإطلاق التجريبي بميزات المشروع الحالية، تقليل استهلاك قاعدة البيانات وRealtime والباندويث، وحفظ البيانات والحقوق المالية.
- نبني أمانًا متعدد الطبقات، واستجابة مؤسسية للضغط؛ لا وعد بعدم وقوع أي حادث أو اختراق.
- نحتفظ بقاعدة القبول الآمن للطلبات الجديدة **كمقترح تشغيلي خاضع لموافقة المالك على التفاصيل**؛ لا تعديل صامت لقواعد الطلبات أو المال أو الأدوار.
- هذا الملف تابع لخطة [SCALABILITY & OPERATIONAL RESILIENCE](https://github.com/merapplications-sketch/Talabat-v3/blob/1cb85361d698d5da787d927a4c9ae7bd213c68c1/docs/review/continuation108/TARGET-ALIGNMENT-PLAN.md) و[خطة الإنذار الاستباقي](PROACTIVE-CAPACITY-RESILIENCE-PLAN-20261114.md) ولا ينشئ بوابة جديدة ولا يعيد ترتيب G1. تحفظ قرارات CASH-01/RETURN-01/SCOPE-01/Q09–17 والواجهة الأصلية.

## A. فحص واقعي للمصدر — لا نخلط بين ما هو موجود وما هو مفعّل

1. مصدر `talabat-core.js` المرجعي يربط Supabase على مشروع Talabat `dzydscryrnahnneydnry`. **النسخة المنشورة الفعلية وSHA/إعداداتها لم تثبت بعد، G1-A/F**.
2. الاستعلامات الخاصة بالكتالوج تتضمن حدودًا مصدرية كبيرة (حتى 5,000 منتج و20,000 خيار في مسار القراءة). لا تعني الأعداد أنها تجلبها كاملة دائمًا. يجب قياس البايتات والاستعلامات الفعلية.
3. Realtime + الاستعلام الدوري مع Backoff موجودان؛ عدد الاتصالات وCPU وEgress/جلسة غير مثبت.
4. `driver_location` يعمل كـRPC في كود العميل؛ ليس لدينا دليل يثبت أن كل موقع يذهب إلى RAM فقط أو إلى قرص فقط.
5. `dispatch_tick` يُستدعى من التطبيق؛ العامل الخلفي المستقل والتوقيت الفعلي غير مثبتين.
6. لوحة الإدارة TailAdmin تحتوي مكونات إشعارات للأعمال؛ لم يُثبت وجود Health/Capacity/Incident Alerts مستقلة.
7. فحص Supabase المتصل قدّم حساب Free وثلاثة مشاريع مرتبطة بالاسم، حالتان ACTIVE_HEALTHY وثالثة INACTIVE في القائمة. تعارضت لاحقًا نتيجة طلب مستشاري الأداء مع القائمة برسالة سبات. **لا تستخدم هذا كإثبات صحة، ولا توقظ أي مشروع أو تستنتج التطبيق المنشور دون ربط الأدلة.**
8. تقرير QA المرجعي يذكر F-01/02/03/04 وموانع G1؛ حالات مخاطر مصدرية لا أعطال تشغيل مثبَتة. محادثات Stage17/Safari المعزولة مسار مستقل لا يشهد لسعة الإنتاج.

## B. مقارنة المصادر المجانية الرسمية (المعلومات قابلة للتغيير)

| الطبقة | Supabase Free | Cloudflare Free | نتيجة القرار |
|---|---|---|---|
| واجهات HTML/CSS/JS والصور الثابتة | Bandwidth ضمن حصة Supabase | Workers Static Assets/Pages ملفات ثابتة مجانية وغير محدودة الطلبات، ما لم تمر عبر تنفيذ Worker | **Cloudflare للواجهة** |
| APIs | واجهات PostgREST/Auth/Edge Functions مع حصص كل خدمة | Workers Free **100,000 استدعاء/يوم و10ms CPU/استدعاء** | استخدام Worker لحاجة محددة فقط |
| معاملات الطلبات/المال | PostgreSQL + transaction/RLS/RPC | D1 SQLite-type، **500MB لكل قاعدة**، 5GB إجمالي حساب؛ Free يوميًا 5M صف مقروء و100k صف مكتوب، بعد الحد تُرفض العمليات | **الاحتفاظ بقاعدة PostgreSQL الحالية**؛ لا ترحيل عشوائي إلى D1 |
| قاعدة البيانات والتخزين | 500MB حصة Database، القرص الفيزيائي Free **2GB ثابت** يصل read-only عند استخدام 95%، 1GB Storage | R2 Standard 10GB-month مع 1M Class A و10M Class B مجانًا، ولا رسوم نقل egress؛ يتطلب تمكين خدمة R2 وتوضيح شروط الفوترة | تقييم R2 للصور/الأصول **بعد** دراسة الصلاحيات ومطابقة الكائنات |
| Realtime | 200 اتصال متزامن و100 رسالة/ثانية Free + 2M رسالة شهريًا | لا بديل تلقائي لـSupabase Realtime عبر Static Assets | قياس المستهلكين واستهلاك الرسائل |
| حماية نطاق الواجهة | يوفر حماية للخدمات المدارة مع RLS/Auth مسؤولة عن التطبيق | WAF Free Managed Ruleset، DDoS، Rule واحدة Rate Limiting ضمن Free | **Cloudflare عند الحافة**، مع حماية Supabase API مباشرة |
| تعافي ونسخ | Free لا يحتوي نسخًا تلقائية؛ المشاريع الخاملة قد تتوقف خلال 7 أيام | D1 Time Travel 7 أيام على Free؛ **ليس Backup لبيانات PostgreSQL** | نسخ PostgreSQL+Storage منفصلة ومراجعة استعادة |

**المصادر الأصلية:** [Supabase pricing](https://supabase.com/pricing) · [Realtime limits](https://supabase.com/docs/guides/realtime/limits) · [Free pausing](https://supabase.com/docs/guides/platform/free-project-pausing) · [Supabase database disk](https://supabase.com/docs/guides/platform/database-size) · [Supabase backups](https://supabase.com/docs/guides/platform/backups) · [Cloudflare Workers limits](https://developers.cloudflare.com/workers/platform/limits/) · [Static assets billing](https://developers.cloudflare.com/workers/static-assets/billing-and-limitations/) · [Cloudflare D1 limits](https://developers.cloudflare.com/d1/platform/limits/) · [D1 pricing](https://developers.cloudflare.com/d1/platform/pricing/) · [R2 pricing](https://developers.cloudflare.com/r2/pricing/) · [WAF](https://developers.cloudflare.com/waf/).

**مهم:** السعة للمستخدمين لا تقاس بالـGB؛ الحد الحقيقي هو أصغر هامش بين API/Realtime/DB CPU/RAM/IOPS/disk/connections/egress/jobs، وليس عدد المستخدمين المسجلين.

## C. الإنذار المطلوب للإدارة: تصميم متعدد القنوات

```
مراقب خارجي مستقل (خارج TALABOT / Supabase)
            ↓
  خدمة جمع مؤشرات مقيّدة وصالحة للقراءة فقط
            ↓
  سياسة العتبة + الاتجاه + التكرار + التأكيد
         ↙                  ↘
تنبيه مباشر للإدارة      سجل تنبيهات ظاهر في TailAdmin
(بريد + إشعار جوال/      (فتح/قيد المعالجة/مغلق،
Telegram عند اعتماده)     مسؤول، زمن، مصدر، رابط)
```

**شرطان إلزاميان:**
- تنبيه خارج التطبيق **حتى لو انقطعت قاعدة البيانات**؛ لوحة الإدارة وحدها لا تكفي، ورمز الجرس الحالي ليس إثبات منظومة مراقبة موارد.
- عدم إرسال بيانات المستخدمين أو مفاتيح أو أسرار إلى طرف تنبيه خارجي. فقط الحالة، الخدمة، مستوى الخطورة، الزمن، المعرف التشغيلي غير السري، ورابط تقرير مخوّل.

**طبقة مجانية متاحة للاستكشاف دون تفعيل الآن:** [UptimeRobot Free](https://help.uptimerobot.com/en/articles/11604710-who-should-use-uptimerobot-s-free-plan) يدعم حتى 50 مراقبًا بفاصل 5 دقائق، تنبيهات خارجية بالبريد/تطبيق؛ يمكن تخصيصه لمراقبة HTTPS وendpoint صحة **GET لا يغيّر بيانات** إذا وُجد أو أُنشئ بتفويض. HTTP 200 للواجهة وحده لا يثبت صحة Checkout/DB. لا يصلح وحده لإنذار CPU/IO أو حماية الهجوم. قبل البدء يجب تحديد بريد إداري موثوق/قناة تنبيه، وفحص حدود الاستخدام والتحقق من استلام إشعار اختباري.

**السعة الدقيقة:** تستخدم Supabase Reports المجانية لمدة 24 ساعة لقياس RAM/CPU/IOPS/الاتصالات/القرص وAPI/Realtime. [Supabase Reports](https://supabase.com/docs/guides/observability/reports). **Metrics endpoint ليس مشمولًا على Free بحسب صفحة الأسعار**، فلا نعد باستخراج CPU الآلي الدقيقة بالدقيقة عبر Prometheus بدون تحقق من الاستحقاقات. حدود استخدام Cloudflare المباشرة تُراقب من Dashboard/Observability إذا كانت الخدمة تعمل فعليًا.

**خطوة التنفيذ المستقبلية المطلوب اعتمادها منفصلًا:** (1) read-only service map وhealth contract (2) مصدر مستقل للإشعارات + المستلمون + الأسرار من Vault (3) سجل أحداث مؤمّن في لوحة Admin (4) اختبار سقوط DB/Cloudflare الوهمي مع سجل مستلم (5) تشغيليًا تحقق من عدم الإزعاج وإعادة الإرسال والتصعيد.

## D. مؤشرات إنذار مبدئية (غير مفعلة — تحتاج معايرة وقرار)

- ضوء Early عندما يصل مقياس حقيقي إلى نحو 50% من سقفه مع نمو مستمر أو موعد متوقع للاصطدام خلال 14 يومًا.
- Watch عند 65–70% مستمر أو ارتفاع p95/حصة الأخطاء/زمن الانتظار عن Baseline.
- Critical عند 80–85% أو ظهور timeout/503/429 أو تدهور واجهة/عمليات الأموال، مع اتصال بمسؤول ثانٍ إن لم يُؤكد التنبيه.
- Alert مستقل عند فقد heartbeat أو failure من endpoint حيوي، أو خرق نزاهة (طلب/خصم/تسليم مكرر = صفر مسموح).
- عتبات زمنية مختلفة بين API, Realtime, CPU, disk/WAL, queue age, DB pool وEgress؛ **لا يوجد حد موحد اسمه 80% حمل السيرفر**.
- ChatGPT hourly automation إضافة ثانوية، **وليست إنذارًا لحظيًا أو بديلًا للمراقب المستقل**.

## E. مصفوفة المخاطر الواقعية والمتوقعة والوقاية

| رمز | الخطر/السبب المحتمل | الوقاية قبل الخسارة | اختبار قبول آمن (اصطناعي/معزول) |
|---|---|---|---|
| OPS-01 | Free plan الخمول/وقف المشروع | قرار استضافة إنتاجية مُسعّر ومراقبة مستقلة؛ رسالة توقف مقبولة | تمييز pause عن incident دون استدعاء إنتاج |
| OPS-02 | حدود API/Worker/Realtimes | مراجعة quotas وSLIs وتوقع الاستهلاك؛ demand shaping قبل الحظر | Load + Spike مع احتفاظ الطلبات الموجودة |
| OPS-03 | ارتفاع CPU/RAM/DB connections | تحليل hot queries وpool، ضبط حد التوازي، ترقيم وحجم صفحات | P95/P99/اتصالات لا تنمو بلا حدود |
| OPS-04 | امتلاء Disk/WAL وتحول القاعدة read-only | مراقبة Disk الفعلي وWAL/IO quota، إنذار قبل 95%، خطة backup/upgrade | امتلاء آمن وهمي مع عدم إقرار طلب لم يُحفظ |
| OPS-05 | Egress/Storage/Realtime Messages استنزاف | صور CDN متوافقة مع الخصوصية، حقول محددة، Delta، مراقبة الكلفة | بايتات/جلسة ورسائل/جلسة قبل/بعد |
| OPS-06 | كتالوج ضخم/بحث غير مفهرس | Paging/indices/query selection بعد قياس، تخزين عام فقط مع invalidation | 100 مطعم/10,000 صنف كنقطة قياس لا قدرة مثبتة |
| OPS-07 | Storm تحديثات Realtime + reconnect | debounce/jitter, single subscription, hidden-tab pause, backoff، عدم flood | انقطاع وعودة جماعية بلا قفزة غير محدودة |
| OPS-08 | موقع سائق يكتب كثيرًا أو قديم | TTL/decimation/accuracy وخانة latest + سجل تسليم دائم؛ بدون نقل RAM تلقائي | عمر إحداثية معقول، لا إعادة مواقع مهجورة |
| OPS-09 | dispatch_tick عدة جلسات، غياب Job مستقل | إثبات المراقب/worker، idempotent claim، queue age وحد التوازي | عامل واحد أو أكثر مع assign واحد ومسار تعافٍ |
| OPS-10 | قبول مزدوج أو مرحلتان غير قانونيتان | شرط خادمي ذرّي وقواعد State Machine، ليس تعطيل زر فقط | قبول سائقين بالتزامن؛ واحد فقط يفوز |
| OPS-11 | Checkout مكرر/Timeout بعد COMMIT | request key ثابت، قيد uniqueness ومعاملة خادمية، status lookup | طلب واحد وأثر مالي واحد بعد إعادة المحاولة |
| OPS-12 | التسليم/المستحقات تتكرر | delivery state/ledger constraint ومعاملة atomically، سجل reconciliation | 2 confirm + retry => تسليم واحد ودفتر واحد |
| OPS-13 | خصم/سعر غير مطابق أو تعديل مطعم متأخر | quote snapshot + required customer reapproval + PRICE/TIP/CASH-01 immutability | لا خصم أو تحصيل مخالف للقواعد |
| OPS-14 | عمليات جانبية تفشل بعد نجاح الطلب | durable outbox/queue عند إثبات الحاجة؛ retries bounded/idempotent؛ أولوية إشعارات ثانوية | إشعار يفشل دون فقدان الطلب أو تكرار المال |
| OPS-15 | إلغاء/إرجاع/فشل مزود دفع | Saga/reconciliation، pending حالة واضحة، لا success وهمي | فقد ACK واسترجاع مالي: نتيجة واحدة قابلة للتدقيق |
| OPS-16 | اختراق بيانات/تجاوز صلاحيات RPC | RLS ownership + SECURITY DEFINER audit + MFA staff + least privilege | عميلان/سائقان/مطعمان لا يقرؤون بيانات غيرهم |
| OPS-17 | Bot/DDoS/credential stuffing | Cloudflare WAF عندما المرور أمامه، Auth captcha/rate limits عند Supabase، تنبيهات abuse | حركة مسيئة وهمية لا تمنع العملاء الشرعيين |
| OPS-18 | كشف أسرار العميل/مفاتيح الخادم | لا service_role في المتصفح، secrets manager، دور محدود وتدوير مفاتيح | Source/CI secret scan واختبارات صلاحيات |
| OPS-19 | صور إثبات/روابط موقعة تتسرب أو تضيع | ACL/TTL/metadata checksum، backup DB + object bytes + key versions | تصادم، انتهاء URL، restore كائن + سجله |
| OPS-20 | انقطاع إنترنت/إغلاق Safari والعميل غير متأكد | status recovery by stable order key، drafts local non-authoritative | إعادة فتح بعد commit => نفس الطلب لا طلب جديد |
| OPS-21 | نسخة منشورة لا تطابق كود/RPC الحالي | immutable manifest وrelease gates، rollback متوافق مع DB | SHA بيئة الإنتاج ↔ frontend/API/SQL، stop drift |
| OPS-22 | فشل backup أو فقدان مستندات مالية | نسخ خارج بيئة التشغيل بتشفير، تحقق checksums، restore drill، snapshots قانونية | استعادة آمنة واعتماد RPO/RTO لا تخمين |
| OPS-23 | المراقبة نفسها تتعطل | independent watchdog/heartbeat + secondary channel + acknowledgement | إيقاف مراقب/DB وهمي يرسل تنبيهًا خارجيًا |
| OPS-24 | Fast fail غير مضبوط يمنع طلبًا مقبولًا | Admission قبل المصادقة المالية/commit فقط، لا قبول/خصم وهمي؛ إنقاذ accepted work | Burst يخفض noncritical ولا يضيع عمل مقبول |

**تنبيه منهجي:** الحالة الواقعية لـOPS-01..24 متفاوتة؛ هذه خريطة **مخاطر واختبارات مقترحة** لا إثبات 24 عطلًا قائمًا. F-01..F-04 في التقرير السابق هي مصدرية ضمن حدودها.

## F. كيف نخفض حمل TALABOT بدون فقدان المعلومات

**تقسيم البيانات إلى 3 طبقات:**

| الطبقة | أمثلة | قاعدة الأمان |
|---|---|---|
| دائمة/حرجة | الطلب، الحالة الرسمية، أسعار البيع المثبتة، قيود المالية، إثبات الاستلام، الموافقة، تدقيق الإدارة | **PostgreSQL transaction + durable unique keys + append-only audit/ledger**؛ لا حذف تلقائي ولا اعتماد على cache |
| قابلة لإعادة الإنشاء | أقسام Home، صور عامة، قائمة تصنيف، تقييمات مجمعة، نتائج بحث عامة | Cache/CDN/version TTL، invalidation عند تغير السعر/توفر الصنف؛ لا caching لبيانات شخصية |
| حيّة/مؤقتة | موقع السائق الأخير وحالة presence ومؤشر progress والموصلات | TTL + freshness + fallback؛ فقط ما يتطلبه قانون/عقد التدقيق يُحفظ في سجل دائم؛ لا كتابة GPS لمجرد الحركة بدون قياس |

**قاعدة التنفيذ:** لا نعلن «تم الطلب» قبل commit حقيقي، ولا «تم الدفع» قبل إقرار مزود الدفع/دفتر المالية وفق سياسة معتمدة. الطلب الذي أُرسل ولم يصل الرد يُستعلم عنه بمفتاح العملية بدل إنشاء نسخة جديدة. العملية المالية تنفذ **مرة في أثرها الفعلي** حتى لو أعيد إرسال HTTP. تؤجل فقط التحليلات وبعض الإشعارات؛ لا تؤجل حقيقة قبول الطلب/المبلغ في RAM.

**تحسينات مقترحة بعد القياس:** select fields بدل `*`، scoped pagination، Lazy loading، cache images، WebP compress بدون فقد أصل، تقليل polling، dedup subscriptions، consolidate repeat notifications، short bounded timeouts/backoff with jitter، index & query plan checks، GPS TTL، limit expensive reports/concurrent jobs. لا تغيير في البيانات الأساسية ولا حراس RLS/خصومات/توزيع السائقين دون اختبار واعتماد.

## G. نسخ وحماية المعلومات — شرط مستقل عن أداء السيرفر

1. نسخة **PostgreSQL** آمنة ومتزامنة مع إصدار schema/migrations، ونسخة **Storage objects** وmetadata وversions/keys اللازمة، في موقع منعزل عن المشروع الجاري. لا تكفي نسخة GitHub أو واجهة كاش.
2. سياسة احتفاظ موقعة: ما بيانات العميل/السائق التي يجب حفظها قانونيًا؟ وما التي تُحذف بعد TTL فقط عند اعتماد السياسة؟
3. تدقيق checksum / line counts / foreign-key integrity / order-finance reconciliation لنسخة اختبارية، واستعادة دورية على نسخة معزولة.
4. RPO (البيانات المقبول فقدها) وRTO (وقت الاستعادة) أهداف يحددها المالك بعد معرفة القدرات والتكلفة؛ لا يمكن ضمان فقدان صفر على Free بلا تصميم وقياس.
5. مفتاح التشفير والأسرار خارج GitHub، صلاحية وصول أقل ما يمكن، سجل إداري محمي ومراقبة استرداد؛ لا تجريب استعادة على الإنتاج.

## H. المسار التنفيذي الحالي بدون تعارض مع فريق Safari

1. **المدير يواصل مرحلة التكليف الجارية من آخر Issue #26 (Stage17 OPS إن بقيت هي الأحدث)**؛ لا تكليف جديد جماعي ولا إيقاف لاختبار Safari.
2. **بعدها** تكليف منفصل بالقراءة فقط لمستشار/OPS: مطابقة deployed frontend→Supabase project→backend/Cloudflare/limits ومصادر Telemetry الحالية. سلّم جدول قياس usable vs missing، وبيّن القنوات الواقعية للإشعار المجاني.
3. بناء **مواصفة** إنذار App Admin + خارج التطبيق مع أدوار ack وتاريخ وتنبيهات بريد/موبايل/Telegram حسب اعتماد المالك. لا كود أو زر أو webhook قبل إقرار قناة الاستلام وحدود البيانات والصلاحيات.
4. اعتماد Owner للجمهور المستهدف، أصحاب المناوبة/بديلهم، مؤشرات SLI/SLO والعتبات، موازنة صفر/كلفة ترقية محتملة، وعقد القبول الآمن للطلبات عند الضغط.
5. تجهيز واختبار فعلي على نسخة **معزولة اصطناعية** بعد Gate مستقل: monitoring delivery, failover, burst, backup/restore, idempotency, RLS/WAF, UI offline status. مجرد UptimeRobot 200 أو GitHub build ليس قبولًا.
6. إصدار GO/NO-GO للتجربة من المدير فقط بعد استلام أدلة متجانسة. لا تغيير في SHA أو الحسابات أو DB أو النشر أو الدفع ضمن هذا المستند.

**النتيجة النهائية المستهدفة:** تشغيل آمن بسعة مقاسة، إنذار خارجي مُجرّب، ظهور التفاصيل في لوحة الإدارة، وخطة توسع مطورة قبل التشبع، مع حفظ أي طلب/مبلغ مقبول في سجل دائم قابل للاسترجاع. أي CLAIM لحماية كاملة أو «لا ينهار أبدًا» ممنوع بلا قياس وتقييد.
