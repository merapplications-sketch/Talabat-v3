# الأجهزة والمتاجر والتكلفة — 5 نوفمبر 2026

لا مشاريع Xcode أو Gradle ولا IPA/AAB/APK أو إعدادات signing/APNS/FCM في المصدر. لا Mac أو حساب نشر أو جهاز فعلي متاح لهذه الجلسة. لا تعني صفحات HTML جاهزية حزمة متجر. يمكن فصل تجربة ويب مراقبة عن مشروع المتاجر، مع بقاء حدود الخلفية.

| الجانب | المتطلبات الحالية | المتبقي |
|---|---|---|
| iOS | للرفع منذ 28 أبريل 2026: Xcode26+ وSDK iOS26+؛ هوية وحساب وشهادات وتوقيع وخصوصية وأذونات ومراجعة التطبيق | بناء الحزمة وأجهزة فعلية؛ شرط الحد الأدنى للوظائف 4.2 لا يغلق بغلاف ويب |
| Android | منذ 31 أغسطس 2026: API36 للتطبيقات الجديدة والتحديثات؛ AAB ومفتاح رفع وPlay App Signing وإفصاحات البيانات والأذونات | بناء وتوقيع وPlay Console وأجهزة فعلية |
| حساب Play شخصي جديد | للحسابات المعنية: اختبار مغلق، 12 مختبراً و14 يوماً متصلة قبل طلب الإنتاج | لا يحل المختبر الآلي محله |
| Web Push على iOS | دعم النظام وحده لا يكفي؛ Home Screen وإذن واشتراك وخادم إرسال | المصدر لا ينفذ Push؛ polling ليس إشعاراً في الخلفية |
| بريد الدخول | SMTP وروابط تأكيد واستعادة صالحة ومراقبة التسليم | autoconfirm محلي لا يثبت ذلك؛ الافتراضي في Supabase محدود برسالتين/ساعة |

المصادر الرسمية:

- https://developer.apple.com/news/upcoming-requirements/?id=04282026a
- https://developer.apple.com/app-store/review/guidelines/
- https://developer.android.com/google/play/requirements/target-sdk
- https://support.google.com/googleplay/android-developer/answer/14151465
- https://developer.apple.com/programs/enroll/
- https://support.google.com/googleplay/android-developer/answer/6112435
- https://developer.apple.com/documentation/usernotifications/sending-web-push-notifications-in-web-apps-and-browsers
- https://supabase.com/docs/guides/auth/auth-smtp
- https://supabase.com/docs/guides/platform/backups
- https://supabase.com/docs/guides/platform/billing-on-supabase

لم يُشتر اشتراك أو مورد. استخدم المعمل Actions العام وحاويات مؤقتة. لا رسوم متاجر لازمة لتجربة ويب. عند اختيار المتاجر لاحقاً: Apple نحو 99 دولاراً/سنة وGoogle Play نحو 25 دولاراً مرة واحدة وفق الرسوم الأساسية؛ قد تختلف الضرائب والعملة. ليست مشتريات مأذونة الآن.

خدمة البريد والرسائل والأجهزة والطابعة والدعم والاتصال تحتاج تقديراً بحسب المتاح فعلياً؛ لا سعر مختلق ولا شراء. لا توصية بخطة Supabase مدفوعة قبل معرفة الخطة وقياس حدودها. نسخة مشفرة خارجية قد تستفيد من الإمكانات القائمة؛ PITR والنسخ المدارة لا تفرض شراء تلقائياً ولا تثبت استعادة مجانية.
