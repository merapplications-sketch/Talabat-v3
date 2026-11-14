# TALABOT — بوابات قبول النسخة التجريبية واختبارات منع التعطل
**نسخة المالك 2026-11-14.** Matrix for owner/manager, not test results. No approved launch, no live writes, no production security/pressure testing.
**Contract:** existing 51 functional current-source E2E + 21 operational/review Admin cases and G1-A..F remain authoritative. This is an owner-facing prioritization / delta list, **not a replacement count or a new claim of 0/XX application functionality**.

## P0 — لا إطلاق مطلقًا بدون أدلة

| ID | النطاق | دليل من المصدر الحالي أو الحاجة | معيار القبول قبل أن يقول المدير GO |
|---|---|---|---|
| PILOT-01 | Source-to-host parity | default main مختلف عن PM source؛ إصدار Safari التاريخي مختلف؛ G1-A | Frontend/Driver/Merchant/Admin/backend/RPC/DB/Cloudflare & Supabase configs pinned by SHA and nonsecret version report |
| PILOT-02 | Auth/RBAC/RLS | G1-D BLOCKED | دور عميل/سائق/مطعم/إدارة لا يقرأ أو يغير بيانات غير المخوّل؛ اختبار سلبي HTTP/session/Storage مؤكد |
| PILOT-03 | checkout idempotency | C-11/12 وB-04/05 غير مثبتين على النسخة الحالية | نقرتان/timeout/إعادة تحميل/فشل بعد COMMIT ⇒ طلب واحد + مالية واحدة + استعلام بنفس المفتاح |
| PILOT-04 | dispatch/driver accept | G1-B، driver_accept وdispatch_tick في المصدر | سائقان يقبلان معًا ⇒ فائز واحد، ولا يضيع الطلب، وجدولة مستقلة مثبتة وتوجد معالجة للتراكم |
| PILOT-05 | delivery | F-02 source risk P1 | double tap/HTTP retry/concurrency ⇒ انتقال رسمي واحد + دليل تسليم واحد + أثر مالي واحد |
| PILOT-06 | CASH-01/Q09–17 | F-04 P1 مصدر مرشح؛ مالي معتمد | سند مالي مستقل يطابق سياسات المالك، دفع السائق للمطعم وحصة التوصيل فقط للمنصة، بلا قبول نقد أقل/زيادة على نحو مخالف، وتطابق سجلات المحاسبة |
| PILOT-07 | return/refund | RETURN-01 | مطالبة مفتوحة حتى قبض المال الفعلي؛ عدم تسجيل رد مالي مرتين؛ تاريخ محمي |
| PILOT-08 | releases & backups | G1-E/F PARTIAL | نسخة DB+Storage+key versions+schemas وإعادة استعادة اختبارية، فحص تعارض النسخة والتراجع ومصالحة الأرصدة |
| PILOT-09 | endpoints/attack surface | Supabase API مباشرة لا تحميه WAF Cloudflare للواجهة فقط | rate abuse/RLS/privileged RPC/token/secret/DDoS/CORS/CSP/XSS/IDOR tests في بيئة معزولة، لا مفاتيح server في العميل |
| PILOT-10 | alerting and availability | لم يثبت إنذار مستقل أو Admin health dashboard | إخطار حقيقي خارج التطبيق حتى عند تعطّل DB، سجل Incident داخل Admin، تنبيهات بمستويات وACK وتصعيد، test delivery |
| PILOT-11 | capacity | 100مطعم/10,000 صنف sample اختبار لا حد حقيقي | baseline/load/spike/soak في بيئة معزولة وحصص موثقة، p95/p99/throughput/error/limits/recovery, safe spare headroom |
| PILOT-12 | trustworthy catalog/payment | source limits واسعة وPRICE-01 | تطابق السعر والخصومات والتوافر بين المستعرض والCheckout والمطعم ولا يتم تغيير السعر بلا موافقة صحيحة |

## P1 — إكمال الرحلة والخرائط والتصميم

| ID | السيناريو | دليل المصدر | المطلوب |
|---|---|---|---|
| PILOT-13 | **خريطة السائق الحية** | driver.html يحتوي Leaflet/OSM + watchPosition وsendLocation throttled (ليس native background) | خريطة حقيقية، نقطة المطعم والزبون، GPS permissions/accuracy/TTL، إغلاق/عودة/خلفية، رسائل الموقع القديم، مسار شارع لا خط وهمي، رد فشل واضح |
| PILOT-14 | **خريطة العميل أثناء الطلب** | tracker بمراحل/رسائل؛ خريطة حية لحركة السائق لم تثبت من المصدر الحالي | customer يرى موقع السائق المخوّل لطلبه بعد الإسناد فقط، وقت آخر تحديث، تحديث آمن، وصول/انقطاع، عدم كشف موقع سائق لزبون آخر |
| PILOT-15 | **خريطة الإدارة المباشرة** | Admin لديه روابط معلومات الموقع، TailAdmin الحالية UX source review only؛ لا live fleet dashboard مثبتة | مدير مخوّل يرى الطلبات النشطة والسائقين فقط حسب صلاحياته/مجاله، GPS stale, filters, urgent tickets, لا وصول لأدمن غير مأذون |
| PILOT-16 | حالة سائق Online | F-01 source P1 | لا تدّعي واجهة Online حتى ACK خادمي، وفي الفشل/reload/reconnect تبقى الحالة صحيحة |
| PILOT-17 | المحادثات واستعادة الشبكة | F-03 source P2 | مسودة السائق لا تُمحى قبل إقرار حفظ الرسالة، لا تكرار عند إعادة المحاولة، customer يفتح نفس الطلب |
| PILOT-18 | العميل | Home B / Restaurant v1.6 / Direction A / cart/notifications/group/gift | search/checkout/mandatory extras/cancel/refresh/RTL? لا تكسر original RU/EN، gift/support والأسماء الطويلة، بدون console errors |
| PILOT-19 | المطعم | Merchant menu/Stop-list/approval/prepare موجود بالمصدر | موافقة/رفض/وقت تجهيز/بدائل/إيقاف صنف/موعد مجدول؛ لا تشويش للطلب أو السعر |
| PILOT-20 | التسليم عند الباب | leaveAtDoor موجود بمصدر driver/merchant/admin؛ نص صريح «لا تدق الباب» ليس مثبتًا في جميع المسارات | لا نكرر ميزة leave-at-door؛ نتحقق من عرض تعليمات «لا تدق الباب» وإثبات الصورة والخصوصية ثم نطلب موافقة المالك على فرق UX إن لزم |
| PILOT-21 | تجربة الإدارة | TailAdmin B/4 KPI/V04 source locked | اختبارات 320/360/390/430/768/1440 RU/EN/TG light/dark، إشعارات، عودة لنفس الفلاتر، صلاحيات/مالية وempty/error/offline |
| PILOT-22 | التطبيق على هاتفين/منصتين | لا Android/iOS native release artifact مثبت في المصدر الأساسي | اختبار Android Chromium/PWA وiPhone Safari/iOS للتتبع/الإشعارات، ثم test native AAB/IPA عند توفر المصادر والموافقات |
| PILOT-23 | GPS/background | source browser geolocation؛ driver background توقف محتمل | إطفاء الشاشة/تبديل التطبيق/قيادة/انقطاع GPS/تبديل الأذونات/بطارية؛ إثبات فعلية التحديث أو قرار native driver |
| PILOT-24 | «الطلب الحقيقي من المتجر إلى المستلم» | Source four roles, no integrated E2E | عميل يطلب→مطعم يؤكد→السائق يقبل→يستلم→يوصل→المحاسبة→التقييم والدعم؛ سجل واحد قابل للمصالحة |
| PILOT-25 | تجربة عامة/جاذبية | تصاميم العميل والإدارة معتمدة لكن browser QA غير مكتمل | صور/فيديو تشغيل فعلية، مراجعة المالك من هاتف، لا dark pilot بديل عن approved UI، no old synthetic/stale catalog |

## تطبيقات المتاجر / التوزيع — اختبارات إضافية قبل نشر أي نسخة

- **Android:** نسخة AAB موثقة التوقيع والpackage ID، سياسة خصوصية وحذف حساب عند اللزوم، Data safety، permissions، startup/crash/network/mobile data، Google Play internal/closed review. إذا الحساب شخصي حديث يلزمه 12 مختبرًا مستمرًا 14 يومًا قبل طلب production access حسب Play Console.
- **iOS:** إن لم يوجد Apple Developer paid account، يمكن اختبار Safari/PWA مؤقتًا ولكن لا نشر على App Store/TestFlight المدفوع. عند الاشتراك: build signing, App Privacy, screenshots, account demo for review, no incomplete wrapper. Background GPS needs native Core Location entitlement and separate approval.
- **الخرائط:** Leaflet أداة UI فقط، وOSM tile.openstreetmap.org خدمة best-effort بلا SLA ولا تدعم تحميلًا جماعيًا/استخدامًا تجاريًا كبيرًا بغير قيود؛ خطة موفر مرخص/قابل للاستبدال مع attribution, caching policy, quota alert, no billing surprises.
- **التجربة المحدودة ليست عرضًا وهميًا:** مرحلة Stage19 fake-data Safari static لا تحسب ضمن PILOT-01..25 functional E2E.

## الاختبارات تحت الضغط والحالات النادرة

1. Ramp حتى safe headroom متفق عليه؛ إحصاء CPU/RAM/DB pool/IOPS/Realtime/429/5xx/queue age.
2. Spike/internet reconnect جماعي: jitter/backoff، منع thundering herd، حظر new work فقط وفق سياسة مستقبلية مالك.
3. Deadlock/parallel accept/finalize/checkout: اختبار صفر ازدواج أثر تجاري، لا يكفي status 200.
4. 20 دقيقة/ساعة/عدة ساعات soak فقط عند توفر بيئة اختبار معزولة مع خطة إيقاف؛ لا عدد افتراضي يدّعي نجاحًا.
5. Storage signed URL TTL/ACL وتغيير الحساب، الصور الفاسدة، الرجوع دون فقد المدخلات.
6. توقّف Supabase أو provider أو فقد اتصال الدفع: حالة معلّقة صريحة وعدم نجاح وهمي؛ recovery RTO/RPO يحددان بالموافقة.
7. التلاعب في السعر، هوية المطعم، صلاحيات السائق، عدد/سعر الإضافات، rate limit Auth وحماية الحساب.

## قائمة الإصلاحات المصدرية الحالية قبل التكليف
- F-01 / P1: driver shifts ack before online claim.
- F-02 / P1: driver delivery confirm needs client flight-lock **plus** server-side exactly-once business effect; source is not live incident proof.
- F-03 / P2: chat draft deletion before persistence ack.
- F-04 / P1: cash collection candidate mismatch with Q14; **do not replace Q14**؛ يلزم فحص active SQL writer ومقارنة oracle مالي أولاً.
- Live customer/admin tracking and native driver background location: **unverified owner-required pilot gaps**, not automatically authorized implementation. Manager scopes them as distinct tested items.
- Contract tests for Q09–17, security scopes and Timezone Asia/Dushanbe.

**Priority:** formal QA and original accepted constraints first. Developer changes only upon verified branch/dependency/test and explicit owner-governed minimal correction; QA reviewer signs off. No current FAIL/NO-GO changes until evidenced.
