# TALABOT — توزيع التطبيقات ولوحات التجار وإعداد المتاجر وحماية المستودعات
**2026-11-14 | OWNER OPERATING PLAN — REVIEW ONLY / NO STORE SUBMISSION, BILLING OR VISIBILITY CHANGE**

## 1. لا يجب أن يكون لكل دور تطبيق على المتجر

| الطرف | الشكل القياسي الأنسب للنسخة الأولى | توزيع وصلاحيات |
|---|---|---|
| **عميل TALABOT** | تطبيق Android وiOS عند الجاهزية + Web/Safari/PWA للوصول المبكر | متجر رسمي واحد لكل نظام (Google Play, Apple App Store) باسم المنتج الأصلي؛ تجربة جودة كاملة |
| **السائق** | تطبيق مخصص (أو حاوية Native مثبتة الجودة) يحتاج GPS/background notifications | Google Play Internal/Closed testing أولاً؛ iOS لاحقاً؛ يتم ربط الحساب بالسائق المعتمد ومهماته |
| **المطعم** | لوحة ويب responsive مستقلة أو داخل Merchant Portal موحد؛ إضافة للشاشة الرئيسية عند الحاجة | رابط HTTPS محمي + حساب يوافق عليه Admin + RLS لمطعم/فرع، لا ضرورة لنشر تطبيق خاص بكل مطعم |
| **التاجر الإلكتروني** | **مقترح بعد Pilot:** Portal ويب احترافي متعدد الفروع بكتالوج منتجات/SKU/options/stock/orders/returns | حساب تاجر مستقل، نفس معيار صلاحيات المطعم، لكن لا يُنسخ منطق وجبات المطعم دون تحليل؛ صلاحيات/store_id آمنة |
| **إدارة TALABOT** | TailAdmin ويب secure admin على الكمبيوتر والجوال، MFA وRBAC | عنوان خاص وحسابات Staff مخولة؛ **لا حاجة لنشر لوحة الإدارة للعامة على App Store** |
| **لوحة الشريك في المستقبل** | PWA أو تطبيق موحّد لكل التجار إذا أثبت استعمال اللوحة الحاجة | لا لكل متجر تطبيقه المستقل؛ private onboarding وQR/link/account manager |

**توزيع التاجر المقترح:** تقدم الإدارة نموذج بيانات المطعم/المتجر، تتحقق من الهوية والعنوان، تعيّن شخصًا مخوّلًا للإدارة، ترسل دعوة/رابط دخول، ثم يُقيد المستخدم برقم متجر/فروع وصلاحيات مخزون/طلب/تقارير. لا يُعرض رصيد أو طلب متجر آخر. لو احتاج الموظفون أكثر من حساب تكون Roles مُقيدة لكل فرع.

## 2. Google Play — الوضع الحالي وشرط الجاهزية
- المالك لديه حساب **Google Play Console**. **نوع الحساب وتاريخ إنشائه غير مثبتين** في الملفات الحالية؛ يُراجعان عند بدء مرحلة إصدار Stores.
- إذا كان حساب Personal قد أُنشئ بعد 13 Nov 2023، تتطلب Google عادةً **12 مختبرًا مشترِكًا 14 يومًا متصلة** في Closed Test قبل التقدم للنشر العام: https://support.google.com/googleplay/android-developer/answer/14151465
- Internal Testing متاح لاختبارات مبكرة للمستخدمين الموثوقين؛ لا يُعادل مرحلة Production أو صحة التطبيق.
- يجب إثبات Package ID النهائي، ملف **Android App Bundle (AAB)** موقعًا، versionCode، صلاحيات location/foreground service، privacy policy, Data safety, login/deletion, app quality، Crash & ANR، Google Play listing/screenshots، مفتاح التوقيع وحفظه خارج GitHub العام.
- لا يوجد في المستودع الحالي الذي فُحص إثبات بأن نسخة Android الأصلية/AAB موقعة وجاهزة؛ **NOT VERIFIED**. لا ننشئ نسخة ملفوفة سطحية من موقع ثم ندعي جاهزية المتجر.
- Background location في تطبيق السائق يتطلب مبررًا وظيفيًا حقيقيًا وافصاحًا وموافقة وفق سياسة Google؛ لا نطلبها من العميل لمجرد مشاهدة خريطة السائق: https://support.google.com/googleplay/android-developer/answer/9799150

## 3. Apple App Store — الوضع الحالي والخيار الأدنى تكلفة
- لا يوجد Apple Developer Program لدى المالك حاليًا. تبلغ العضوية **99 USD سنويًا** وفق Apple؛ لا ترقية أو اشتراك دون موافقة منفصلة: https://developer.apple.com/programs/enroll/
- عند تسجيل حساب باسم شركة تحتاج Legal Entity وD-U-N-S والأوراق اللازمة ووسائل اتصال رسمية؛ اختر الملكية الصحيحة بعد استقرار شركة TALABOT.
- Safari/PWA يمكن أن تدعم اختبارًا مبكرًا مجانيًا، ولكنها **ليست App Store** ولا تضمن جميع ميزات background GPS في iOS.
- عند الانطلاق إلى App Store: IPA/build source signed, device crash and iOS versions, privacy manifests, App Store Connect metadata, review login/demo if needed, complete application functionality. Apple تحذر من التطبيقات التي لا تزيد عن web clipping: https://developer.apple.com/app-store/review/guidelines/
- تطبيق السائق يحتاج دراسة Core Location background modes وتدرج permissions من Apple، مع اختبار قفل الشاشة/إنهاء التطبيق/توفير البطارية ونقل بيانات GPS، لا تعتمد على PWA وحدها لوعود تتبع دائم: https://developer.apple.com/documentation/corelocation/handling-location-updates-in-the-background

**القرار الاقتصادي:** نجهّز تدفق الهاتفين والتصاميم والأصول واختبارات الجهاز والتوقيع قبل دفع Apple، ونطلب عضوية المطور عندما يثبت إصدار iOS readiness وتتوفر الأوراق والميزانية.

## 4. الخرائط بثلاثة أدوار وأقل تكلفة واقعية

- المصدر الحالي: واجهة السائق Leaflet + tiles.openstreetmap.org وGPS browser؛ Customer Tracking stage موجودة؛ Admin Map Live fleet غير مثبتة على UX candidate. **شرط المالك للنسخة الأولى** أن يرى العميل والسائق والإدارة تتبعًا حيًا مقيد الصلاحية، دون تغيير مالي أو ربط سري.
- اعتمد Tracking state: current order id, server-authorized courier, last-known lat/lng+timestamp, accuracy, TTL, only active order recipient, no customer sees another courier. **حركة السائق** قد تتطلب مصدر native/background مع heartbeat.
- لا تعرض خطًا مستقيمًا على أنه طريق شوارع، ولا ETA غير مبني على مصدر حقيقي؛ طريق/ETA يتطلب provider data and test.
- **OpenStreetMap Data free ≠ tile.openstreetmap.org CDN unlimited**. سياسة OSMF تمنع bulk/prefetch ولها best-effort no SLA وتطلب attribution/caching: https://operations.osmfoundation.org/policies/tiles/
- قبل إطلاق كبير اختر provider نظام خرائط مرخّص منخفض الكلفة أو خدمة self-hosted مبررة، مع حساب معدل tile loads، route calls، limits، switchable provider وalerts؛ لا افتراض أن Public OSM tiles يكفي لأي عدد عملاء.
- لا تكتب آلاف نقاط GPS للقرص بلا قياس؛ استخدم freshness, TTL, dedup، لكن احفظ سجلات الطلب/إثبات التسليم والقيم المالية اللازمة دائمًا.

## 5. GitHub: من Public إلى Private دون كسر المنتج

**المشاهد:** merapplications-sketch/Talabat-v3 وmerapplications-sketch/talabot-tailadmin-review كلاهما public في فحص 2026-11-14. المالك قرر سابقًا تأجيل الخصوصية إلى ما بعد أول نسخة وتجربة.

**بوابة الخصوصية المقترحة بعد قبول النسخة الأولى:**
1. افحص فوريًا أن تاريخ GitHub والأفرع/Actions ولا تحتوي credentials/خصوصيات أو service_role. إذا ظهر سر مكشوف، **دوّر المفاتيح واحمِ الوصول فورًا** وفق الصلاحيات؛ لا تنتظر تحويل المستودع إلى خاص.
2. جهز فريق وأذونات أقل privilege، وتحقق أن GitHub/CI/Pages/Cloudflare integrations والربط مع الحسابات وWork لن تتوقف بعد تغيير Visibility؛ سجّل URLs والبدائل.
3. تحقق من GitHub Pages: على خطة Free قد يُلغى نشر الموقع تلقائيًا بعد تحويل repo إلى private. جمهور المعاينة العامة منفصل عن خصوصية كود المستودع، ولا نُسقط موقعًا حيًا دون بديل: https://docs.github.com/en/repositories/managing-your-repositorys-settings-and-features/managing-repository-settings/setting-repository-visibility
4. ملاحظة: forks العامة القديمة لا تصبح خاصة تلقائيًا؛ تأمين المفاتيح يجب أن يسبق تغيير visibility.
5. المالك وحده يصرّح بتغيير visibility؛ تُحفظ نتيجة التغيير/من يرى المستودع وخطة استرجاع الوصول في MASTER #26، ولا يتم التغيير الآن.

## 6. الخط الفاصل بين Marketing Push وOperating Alerts

- رسالة new restaurant/offers للعميل: feature proposal to owner, needs **opt-in, segmentation, RU/EN, frequency limits, unsubscribe, audit**؛ لا اعتماد push على فتح التطبيق فقط.
- رسالة إيقاف/سعة داخل Admin: critical **Operations**، قناة مستقلة عن نفس backend حتى عند outage، تأكيد قراءة ومسؤول on-call؛ ليست نفس Marketing engine.
- Push Web على iOS له شروط homescreen/browser platform، وNative Push يحتاج FCM/APNs permission and token lifecycle؛ اختبارات collapse/dedup/battery/device.

## 7. سياسة عدم فقدان بيانات أثناء الانتقال للمتاجر
- التخزين الرسمي في Postgres بعمليات ذرية ومفتاح idempotency؛ المزامنة المحلية لا تعطي نجاحًا قبل server ack.
- لا نقل من Supabase إلى Cloudflare D1 أو إعادة تعريف Cash/Refund أثناء تجهيز تطبيقات Stores.
- نسخة DB+Storage+schema+keys واختبار restore ومصالحة Finance قبل فتح التجربة على الجمهور.
- App Store / Play release **ليسا دليل صحة**؛ سلّم first pilot functional QA وStore submission readiness على مرحلتين منفصلتين.
