# عقد قياس التوسع والتزامن — مقترح مراجعة لا أمر تشغيل
12 نوفمبر 2026 ، دوشنبه. داخل مسار SCALABILITY & OPERATIONAL RESILIENCE في الخطة الأصلية. مرحلة 1 للعقد والإتاحة، 2 للصحة المعزولة، 3 للموارد/التعافي، 4 للانتقال، 5 للتكامل/الأجهزة، 6 للقرار. لا ضغط أو شراء أو تهيئة مورد أو استعادة الآن.

## الأصل القابل للمراجعة، لا سقف القدرة
| الأصل المحفوظ | المصدر والبيئة | القياس المسجل وحدوده |
|---|---|---|
| [staged-load.json](https://github.com/merapplications-sketch/Talabat-v3/blob/ec4cbd2b89cc1b823131baa744e53e5539eb9c3e/docs/pilot-20261105/confirmation/staged-load.json) |70bbc3397fdeb26ba9c351c260e6e9fed8f754e5 ؛ GitHub ubuntu24.04 ؛ PostgreSQL17.6/GoTrue2.197/PostgREST14.18 loopback |3 مراحل كل منها 60 ث؛ 5/10/20 رحلة متزامنة و 12/22/42 جلسة؛ 401/776/1516 طلب؛ 6.68/12.93/25.27RPS ؛ p95=43.54/19.29/39.93ms ، p99=132/40.22/56.54ms ؛ 105 تسليم و 0duplicate مسجلة. مطعم اصطناعي واحد و 10,000 **طلب تاريخي**، ليست 10,000 صنف أو 100 متجر |
| [result-load.json](https://github.com/merapplications-sketch/Talabat-v3/blob/ec4cbd2b89cc1b823131baa744e53e5539eb9c3e/docs/pilot-20261105/evidence/result-load.json) |6fe666cc84cf9eda0c8ca630bd340aab44f438e3 ؛ نفس عائلة الخدمات محلية |50 رحلة دفعة في 6.86 ث؛ 750 طلب؛ 109.38RPS ؛ p95=150.26ms/p99=228.2ms ؛ 0deadlocks مسجل. ليست ساعات تحمل أو WAN/Realtime/device |
| [SCALING-AND-SECURITY.md](https://github.com/merapplications-sketch/Talabat-v3/blob/ec4cbd2b89cc1b823131baa744e53e5539eb9c3e/SCALING-AND-SECURITY.md) |مذكرة تاريخية وليست config مزود مؤرخ |18 طلب/دقيقة مقابل 210 محاكاة؛ 50→200→1000 اقتراح قديم، 1MBStorage وتوصيات Small/Medium/PITR ليست إثبات تهيئة أو إذنشراء/تغيير MFA. لا نعتمدها حداً حالياً |
| نتائج 106 و PRICE |PostgreSQL معزول/fixtures وفق أحكامها |صحة idempotency/عزل/ACK ، لا سعة أو قبول تكامل جميع آثار الهدف |

staged-load يسجل poll_customer=25s ، poll_merchant_driver_admin=10s ، GPS=8s ، lab_p95_budget=2000ms. هذه **إعدادات تجربة تاريخية فقط**؛ لا SLO إنتاج ولا قيم العميل الفعّال. إصدارات الخدمات و digests موجودة في الملف؛ CPU/RAM/IOPS وحجم pool وحدود الاتصالات و Realtime/egress/rate/body الحالية UNKNOWN.
Q36=180 ث مهلة أعمال للموافقة؛ ليس هدف حمل. مجموع 3×60 ث تجربة تاريخية منفصلة أيضاً، لا إثبات تحمل طويل.

## سجل الموارد المطلوب قبل اختيار الأرقام
يسلم مسؤول النشر/DB ملف RESOURCE-CONFIG منقحاً: وقت/بيئة/region/serviceversion ، vCPU/RAM/disk/IOPS ، DBmaxconnections/poolmode/poolsize/waittimeout ، statement/locktimeout ، gatewayrate/body/CPUlimits ، Realtimeconnections/messages ، Storagelimits/CDN/cache ، workerqueue/concurrency/retry ، monitoring sampling ،التكلفة/السقف المعتمد. لا أسرار ولا أسماء موارد حساسة عامة.
لكل حقل: value+unit+scope+provenance أو UNKNOWN وحامل المصدر. لا نملأ UNKNOWN بمواصفات ubuntu runner أو توصية upgrade. هذه البيانات من export قائم؛ إنتاجها بقراءة مزود جديدة أو تهيئة telemetry يحتاج نطاق الوصول المنفصل.

## سيناريو البيانات ومزيج العمل
100 متجر و 10,000 صنف **نقطة التقييم المعتمدة لا سقفاً**. توزع بيانات اصطناعية بعينة متوازنة وأخرى منحازة لمتجر ساخن، فروع مستقلة، صفحات متعددة، خيارات مجانية ومدفوعة، أصناف غير متاحة، تغيّر أسعار/خصومات، تاريخ طلبات وتقييمات مستقل عن عدد الأصناف. الأحجام الأبعد يحددها قياس النمو والتكلفة؛ لا مضاعفة تلقائية.
سجل datasetID/seed/sourceSHA/schema/حجم الجداول والفهارس وتوزيع skew وإعداد الحمل قبل كل تشغيل مخول؛ يمنع استخدام بيانات محمية.

| فئة الرحلة | ما يقاس | سلامة النتائج |
|---|---|---|
| قراءة/بحث/فلترة/صفحات |first/nextpage ،حجم payload ، p95/p99 ، cold/warm ،قائمة مفتوحة أثناءحفظ |لا فقد/تكرارصفحات أو Googlefallback ؛ ربط snapshot/version ؛ زمن save→visible لكل قارئ |
| عميل checkout و PRICE |quote/confirm/create/status/replay ؛ السعر يتغير أثناء انتظارالقفل |لا إنشاء أو خصم مع سعر غيرموافق، الاسترجاعلا يعيدالتسعير، خياراتصفرية/إجماليثابت محفوظة |
| متجر/سائق/إدارة |قبول/تحضير/إسناد/قبولعرض/تسليم/إيصال |عزل المنشأة والسائق، فائزواحد، حدود المحفظة/الولاء/الكاشحسبالعقد |
| منافسة المفاتيح |نفس key ونفسحساب؛ مفاتيحمختلفةلحساب؛ حساباتمختلفة؛ تبويبات/أجهزة |طلبواحد وخصمواحد، closure لا يفتح، unknown لا يبدلمفتاحاً |
| قراءةتقييمات |تاريخأكبرمن 300 وصفحاتوذيلمتزامن |عدد/متوسط منالمصدر الداخليكله أو unavailable ؛ بياناتشخصيةمحجوبة |
| فشل/تعافٍ |timeout/failure قبلوبعد COMMIT ،إنفاق/إرجاعمتزامن، queuebacklog |كلأثرداخليذري؛ الخارجي dedup+reconcile ، لا no_effects كاذب |
| خلفيةوجهاز |poll/Realtime/GPS/background/صور/إيصال |لا تساوي VUs والمستخدمين؛ قياس بطارية/إذن/طباعة عند تكليفالجهاز |

الأوزان w_read/w_checkout/w_store/w_driver/w_finance تجمع 1 ، ويحددها سجل استخدام قائم أو ملف افتراضات معلن يقبله المراجع. لا اعتماد نسب عشوائية. تقاس كل فئة وحدها ثمالمزيج حتىلايخفي تحسنالمتوسط تدهورالكتابة. burst/retry تضخم الحمل الكلي وتُعد منفصلة.

## المقاييس وتعريفها
- latency: ساعة monotonic من إرسال الطلب حتى اكتمال جسم الرد؛ UI من فعل المستخدم حتى نتيجة مرئية مؤكدة، مساران منفصلان. تحفظ histogram/raw samples منقحة، عددالعينة وفترةالقياس؛ لا متوسط p95 بينالمراحل.
- RPS: attempted/completed/successful لكل نافذة؛ concurrency=in-flight ، sessions و VUs و orders/min مقاييسمختلفة. blocked/expected denial لا يخلطان مع 5xx/timeout ؛ timeout ضمن errorbudget.
- p95/p99 لكل route/role/مرحلة coldwarm ونوعالمعاملة، مع throughput+errors ومدةالعينة. coordinated omission يمنع عبرجدولة arrival مستقلة وإظهار missed arrivals/queuewait.
- DB:CPU/RAM/IO/WAL/poolwait/activeconnections/lockwait/deadlocks/timeouts/querycost ، rowcounts وعدد credit/debit/receipt/binding/closure قبلوبعد. queues:depth/lag/retries/drain ، cache:staleness/invalidation ، resources:saturation/egress/cost.
- سلامة ثابتة وليست SLO اختياري: صفر طلب/خصم مكرر،صفر تسرب هوية،صفر فقد closure ،صفر سعرغيرموافق،صفر أثرمالي جزئي. أي منها فشل يوقف الاختبار ويجمّد إعادة المحاولة للمصالحة.
- أهداف L95/L99/errorbudget/staleness/backlog/poolwait/CPUmargin ومدة T وحجم N و RPO/RTO **غيرمعتمدة**؛ لا نجاح أداء مع حقلإلزامي فارغ.

## خيارات حجم التكليف المستقبلي
| الخيار | النطاق المقترح وسبب الاختيار | ما لا يثبته |
|---|---|---|
|A تحديد baseline ، موصى به أولاً بعد البوابات |عينة 100/10,000 ؛ كل رحلةمنفصلة cold/warm ، تدرج arrival حتىبلوغأولحد متفق؛ يشتق نقطة الاختناق ومواردها |لا تحميلمستضافالآن، لا userscapacity أو تحملطويل |
|B مزيج واعتماد هدف |بعد A ومع resourceconfig ، اختيار peakarrival+headroom مبرر منسجل استخدام أوتوقعمالك معلن؛ mixed+burst+نافسة |لا أرقامإنتاجمننتيجةمختبر،لا سقفمن 100 متجر |
|C تحمل وفشل وتعافٍ |بعد B وتفويضحقن/restore ، T يغطي دورة token/cache/job/backup المعنية؛ مقارنة normal/degraded/recovered |لا استبدالأدلة Storage/Safari أو مستقبل الأثرالمالي |

الفريق يقدم بعد metadata جدولخيارات L95/L99/RPS/T/كلفة مع قياس baseline وسببكل قيمة، ثم يعتمدالمالك الهدف/الميزانية/النطاق. لا يطالبالمالك باختراع config أوإعادةسياسة؛ لا اختبار 180 ث بديلاًعنذلك.

## حدود التنفيذ والتوقف وإغلاق العقد
قبل التشغيلالمستقبلي: تثبيتالمرشحوالبيئةوالهوياتوالبياناتوالأهدافوالميزانيةوالمدةو SLOs ؛ isolationallowlist ،حظر orders#1/#2/#3/payable3 ؛ maxrequestbudget و kill switch ؛ حامل الاختبارومراقبماليومسؤول cleanup/m صالحة،أرشفةخاصة.
وقففوري عندوجهةخارجالنطاق،تسرب/أثرمكرر/اختلالذري،تجاوزكلفة/حملمعتمد،أوقيم telemetry الحرجةالمتفقعليها؛ لا تعديل limits أثناءالتشغيللإظهار PASS. يحتفظ evidence ،ويوقفإنتاجطلباتجديدة دون إعادة unknown ؛ لا cleanup يحذفحواجزأومفاتيح.
قبول 1: تعريفاتالقياس ومصادرالموارد وقنواتها ومسؤولياتها وعقودالتعافيوالإتاحةمقبولة؛ لا تتطلب نتائجتحميلالمراحل 3–5 مقدماً. الحالي **DRAFT/PARTIAL** لأن metadata والأهدافلم تثبت. أي instrumentation أوتعديل index/pool/cache أوشراءيحتاجتفويضاًمحدداً. لا خطةموازية أو GO2.
