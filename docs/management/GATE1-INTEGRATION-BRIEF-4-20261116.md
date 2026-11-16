# TALABOT — البوابة 1 / التكامل: تكليف المبرمج (2026-11-16)
**موافقة المالك (10:43):** دمج المرشح في `tech/v82-int` (ليس main) + تطبيق SQL البوابة 1 على مشروع Talabat `dzydscryrnahnneydnry` + ملف تراجع. المالك أكّد أن التطبيق قيد التطوير بلا تشغيل حقيقي.
**المنفّذ الوحيد: المبرمج.** تقرير واحد في #48.

## المصدر
- المرشح المقبول: `dev/gate1-f01-f04-20261116` @ `1c1ce8d0` (مراجعة مستقلة GO [6908370549](https://github.com/merapplications-sketch/Talabat-v3/issues/48#issuecomment-6908370549)).
- `tech/v82-int` @ `09ef07fd` = سلف مباشر (ahead 12، behind 0) ← **fast-forward فقط**. إن تغيّر `tech/v82-int` قبل الدمج: STOP ومانع.

## 1) ملف التراجع (قبل أي تطبيق)
`sql/rollback/gate1_rollback_20261116.sql`: يعيد بالضبط تعريفات baseline (`4de26eb4…`) لـ`driver_ping` (void)، `deliver_order`، فهرس التذكرة المفتوحة الأصلي، ويحذف `report_driver_cash_short` والفهارس الجديدة. يُختبر محليًا في CI: baseline ← gate1 ← rollback ← يطابق baseline للكائنات المعنية (`ROLLBACK_restores_baseline`).

## 2) تطبيق SQL على المشروع (workflow واحد)
- workflow على فرع `ops/gate1-apply-20261116`، يُشغَّل بتعديل ملف trigger فقط، سر `SUPABASE_PROD_DB_URL`، مقيّد بـref `dzydscryrnahnneydnry` (STOP لأي مشروع آخر، خصوصًا pilot).
- قبل التطبيق: حفظ `pg_get_functiondef`/`pg_indexes` الحالية للكائنات المعنية كـartifact، والتأكد أنها تطابق baseline؛ إن اختلفت: STOP.
- التطبيق: `psql -v ON_ERROR_STOP=1 --single-transaction -f sql/proposed/gate1_cash_and_idempotent_delivery.sql` ثم `NOTIFY pgrst, 'reload schema'`.
- بعد التطبيق (قراءة فقط): توقيعات الدوال، `driver_ping` يعيد boolean، grants (لا anon/PUBLIC)، الفهرسان الجديدان. لا كتابة بيانات، لا اختبار بطلب حقيقي.
- إن لم يوجد السر: مانع واحد في #48 (المالك يعيده كما في المرة السابقة).

## 3) الدمج
بعد نجاح §2 فقط: `git push origin 1c1ce8d0:tech/v82-int` (fast-forward). لا main، لا force.

## 4) اختبار الجهاز (تجهيز فقط)
حدد في التقرير كيف تُخدَم واجهات `tech/v82-int` للسائق/الزبون على الموبايل الآن (الرابط). إن احتاج نشر معاينة جديدة: لا تنشر؛ اكتب الملفات/الأمر المطلوب والمدير ينشر. ثم خطوات قصيرة للمالك: سائق Online/Offline، تسليم نقدي مطابق، نقد ناقص يُرفض.

## ممنوع
main، pilot `talabot-pilot-20261106` (Cloudflare وSupabase)، كتابة بيانات، تغيير التصميم/CASH-01/Q09–Q17، تعديل الكود المقبول (أي تغيير = مراجعة جديدة).

## التسليم — تعليق واحد في #48
SHA الدمج، رابط CI للتراجع، رابط run التطبيق + فحوص ما بعده، مسار ملف التراجع، طريقة خدمة الواجهات للجهاز، المخاطر.
