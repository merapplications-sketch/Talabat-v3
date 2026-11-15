# TALABOT — البوابة 1 / دفعة الإكمال الموحّدة للمبرمج (2026-11-16)
**نفس مهمة البوابة 1 في #48، ليست مرحلة جديدة.** يلغي هذا التكليف فكرة مشروع `talabot-test` السحابي ويحل محل §2 من [التكليف الأول](GATE1-PROGRAMMER-BRIEF-20261116.md). باقي التكليف الأول ساري.
**موافقة المالك (16 نوفمبر 02:34):** قراءة المخطط فقط من قاعدة الإنتاج + Supabase محلي مؤقت داخل CI. المالك أكّد: التطبيق قيد التطوير ولم يبدأ تشغيل حقيقي.

## استلام المدير لما سبق
`8b0804bd`: 10 ملفات، main دون تغيير، F01..F04 4/4 PASS (mock)، core C-1..C-6 PASS — [CI 43761445301](https://github.com/merapplications-sketch/Talabat-v3/actions/runs/43761445301). **مقبول كمصدر مرشح.** لا تعِد هذه الفحوص إلا ضمن `check_all.sh`.

## 1) المخطط الأساسي (قراءة فقط)
- المشروع: مشروع Supabase الذي يشير إليه كود التطبيق على BASE (`talabat-core.js`). أثبت الـref في التقرير.
- **schema-only**: الجداول، الأعمدة، القيود، الفهارس، الـenum، RLS policies، الدوال والـtriggers، grants. عبر `supabase db dump --schema-only` أو استعلامات قراءة على `pg_catalog`/`information_schema` من موصل Supabase.
- **ممنوع:** أي صف بيانات، `auth.users`، Storage objects، قيم vault/secrets، أي كتابة أو migration أو تغيير إعداد على الإنتاج.
- احفظ في فرعك: `sql/baseline/schema_baseline_<ref>_20261116.sql` + سطر SHA256 وتاريخ الاستخراج في التقرير. سجّل في جدول قصير أي فرق بين المخطط وpatch17–34 (لا تصلحه).

## 2) Supabase محلي مؤقت في CI ($0)
- في workflow فرعك: `supabase/setup-cli` ثم `supabase start` (Docker على الـrunner)، ثم بالترتيب: baseline ← `sql/proposed/gate1_cash_and_idempotent_delivery.sql`. (patch17–34 فقط إن لم تكن ضمن baseline.)
- مستخدمون اصطناعيون (customer/merchant/driver/outsider/other_driver) عبر Auth المحلي فقط؛ ملف الـfixture يُكتب في `$RUNNER_TEMP`، لا في المستودع.
- عدّل `tools/gate1_e2e.py`: الأصل المسموح الوحيد `http://127.0.0.1:54321`؛ المفاتيح من `supabase status` المحلي؛ أبقِ قائمة منع refs الإنتاج/pilot. أزل الحاجة لأسرار GitHub الثلاثة.
- `finance_receipt` (E07): حدّد الجدول/العمود من baseline. إن لم يوجد أثر مالي قابل للإسناد: E07 = BLOCKED مع سطر واحد يشرح، لا تخترع جدولًا.

## 3) القبول
`tools/check_all.sh` في CI: F01..F04 PASS + core PASS + **E2E 11/11 PASS** (أو BLOCKED موثّق لـE07 فقط للسبب أعلاه). أي FAIL حقيقي في E2E يُصلح في المصدر ضمن نفس الدفعة، ويُضاف فحصه.

## 4) ممنوع
أي كتابة على الإنتاج/الـpilot، أي صف بيانات، مشروع سحابي جديد، خدمة مدفوعة، main، Cloudflare، التصميم المعتمد، CASH-01، تغيير F01..F04 إلا لإصلاح FAIL حقيقي.

## 5) التسليم — تعليق واحد في #48
BASE/FINAL SHA، الملفات، مصدر baseline (ref + SHA256)، رابط CI، جدول E01..E11، فرق baseline↔patches، المخاطر. بعده يرتب المدير المراجعة الأمنية/المالية المستقلة.
