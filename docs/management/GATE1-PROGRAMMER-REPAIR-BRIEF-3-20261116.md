# TALABOT — البوابة 1 / دفعة التصحيح الموحّدة للمبرمج (2026-11-16)
**نفس مهمة البوابة 1 في #48.** المصدر: مراجعة المدقق المستقل [6902997480](https://github.com/merapplications-sketch/Talabat-v3/issues/48#issuecomment-6902997480) = **NO-GO**. المدير تحقق من SF-01/02/05/06 في المصدر @ `691d97e1`. دفعة واحدة؛ ثم إعادة مراجعة من نفس المدقق.
الفرع: `dev/gate1-f01-f04-20261116` من `691d97e1`. احتفظ بكل ما قُبل (SF-04، SF-08، search_path، FOR UPDATE، grants، Q14). لا قواعد مالية جديدة. CASH-01 وQ09–Q17 محفوظة.

## قرارات المدير (ملزمة لهذه الدفعة)
| البند | المطلوب | فحص آلي باسمه |
|---|---|---|
| **SF-01 (P1) E07** | احذف cashback كأثر مالي. الأثر المعتمد من العقود **الموجودة**: لطلب نقدي محلي: `cash_collected == total − wallet_used`، `status=delivered` مرة واحدة، `done_at` ثابت، ودلتا `cash_balances()` غير المسوّاة للسائق **مرة واحدة بالضبط** وتبقى دون تغيير بعد جلستين متزامنتين + إعادة بعد COMMIT. أبقِ فحص cashback (إن وُجد) كفحص «لا تكرار» فقط، ليس كإيصال. عقد التسوية/الإيصال خارج البوابة 1 | `E07_cash_effect_once` |
| **SF-02 (P1) F01** | `driver_ping` المقترح في `sql/proposed/gate1_*.sql` يعيد نتيجة صريحة (مثل `boolean` أو الحالة الجديدة) ويرفع خطأ عند 0 صفوف/دور خاطئ/غير معتمد. العميل يعرض Online **فقط** عند النتيجة الموجبة الصريحة؛ void/2xx وحده = فشل | `F01_explicit_ack`، `E03b_ping_denied_unapproved` |
| **SF-03 (P2)** | **افتراضي آمن:** `deliver_order` و`report_driver_cash_short` يتحققان أيضًا من `role='driver' AND driver_status='approved'` لحظة الاستدعاء. سائق أُوقف أثناء التوصيل يُرفض والإدارة تعالج يدويًا (لا مسار جديد) | `E12_revoked_driver_denied` |
| **SF-05 (P2)** | dedup في `talabat-core.js` للحمولة **المتطابقة** فقط (id+cash+note+photo)؛ حمولة مختلفة أثناء pending = رفض فوري بخطأ `busy`، لا مشاركة نجاح | `F02_conflicting_payload_rejected` |
| **SF-06 (P2)** | إعادة استخدام تذكرة مفتوحة **بـ`reason='payment'` فقط**، وإلا تذكرة جديدة. الإعادة المتطابقة بلا أي كتابة (لا `updated_at`). | `E08b_existing_unrelated_ticket`، `E08c_identical_repeat_no_write` |
| **SF-07/09 (P2)** | مصفوفة رفض محلية واحدة: customer/outsider/unassigned/revoked على `deliver_order` و`report_driver_cash_short` و`driver_ping`، وقراءة دردشة طلب غريب؛ كل رفض بلا أثر جانبي | `E13_authz_matrix` |

## القبول
`tools/check_all.sh` في CI أخضر: كل الفحوص السابقة + الجديدة أعلاه. أي فحص سابق يُكسر = مرفوض. SQL المقترح يُطبق محليًا فقط.

## التسليم — تعليق واحد في #48
FINAL_SHA، الملفات، رابط CI، جدول SF-01..SF-07 ← الفحص ← PASS. ثم يعود للمدقق نفسه لإعادة المراجعة.
