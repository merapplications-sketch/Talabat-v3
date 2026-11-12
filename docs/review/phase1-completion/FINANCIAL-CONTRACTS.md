# العقود المالية والدقة — استكمال من النصوص الموجودة

**SOURCE / HISTORICAL / INHERITED ONLY. لا اختبارات أو حسابات على بيانات حقيقية. G1-C غير مغلقة.**

المستودع merapplications-sketch/Talabat-v3. كل إحالة أدناه مثبتة عند 611b0ebdaa3ed83dd34b623528ea374935a9d8e1؛ تاريخ القرار داخل الوثيقة منفصل عن تاريخ حفظ هذا المرجع. المصطلح «معتمد» يخص قراراً صريحاً محفوظاً، ولا يثبت إعداداً منشوراً حالياً. وصف SQL ليس اعتماداً لقاعدة أعمال جديدة.

## مصادر السلطة ومصادر التعريف

| الرمز | المرجع | درجة الإثبات |
|---|---|---|
|O1|[قرارات المالك — CASH-01 / RETURN-01 / SCOPE-01، تحديث 6 نوفمبر](https://github.com/merapplications-sketch/Talabat-v3/blob/611b0ebdaa3ed83dd34b623528ea374935a9d8e1/docs/OWNER-AGREEMENTS-AR.md)|قواعد أعمال معتمدة محفوظة؛ لا استخراج قيم طلبات محمية|
|O2|[عقد المحاسب والإيصال —2 نوفمبر](https://github.com/merapplications-sketch/Talabat-v3/blob/611b0ebdaa3ed83dd34b623528ea374935a9d8e1/docs/continuity/OWNER-ACCOUNTANT-AND-RECEIPT-20261102.md)|إيصال TJS فريد مرتبط بالتسوية ومفتاح طلب وقراءة لاحقة؛ ليس إثبات تنفيذ دفع خارجي|
|O3|[v48، قرار 10 أكتوبر](https://github.com/merapplications-sketch/Talabat-v3/blob/611b0ebdaa3ed83dd34b623528ea374935a9d8e1/CHANGES-v48.md)|Happy Hour يتحمله المطعم؛ cashback يبقى متوقفاً حتى تفعيله من الإدارة؛ تاريخي|
|O4|[v51، قرارات 10 أكتوبر 18:43 و 19:21](https://github.com/merapplications-sketch/Talabat-v3/blob/611b0ebdaa3ed83dd34b623528ea374935a9d8e1/CHANGES-v51.md)|إعفاء التوصيل وولاء 10 نقاط/TJS كسباً و 1000 نقطة/TJS استخداماً؛ override المطعم للكسب وإعدادات الإدارة محفوظة؛ ليست قراءة إعدادات اليوم|
|S1|[مرشح 106 — create_order103](https://github.com/merapplications-sketch/Talabat-v3/blob/611b0ebdaa3ed83dd34b623528ea374935a9d8e1/tests/native106/isolation.sql)|النص الحسابي للمرشح المعزول؛ ليس oracle مستقل ولا تسعير الهدف|
|S2|[مساعدات promo/loyalty ملتقطة مع اعتماديات اصطناعية معلنة](https://github.com/merapplications-sketch/Talabat-v3/blob/611b0ebdaa3ed83dd34b623528ea374935a9d8e1/tests/native103/dependencies.sql)|جسم مساعدات محفوظ؛ loyalty_setting والجداول المختصرة اصطناعية|
|S3|[patch29](https://github.com/merapplications-sketch/Talabat-v3/blob/611b0ebdaa3ed83dd34b623528ea374935a9d8e1/sql/schema_patch29.sql)، [patch31](https://github.com/merapplications-sketch/Talabat-v3/blob/611b0ebdaa3ed83dd34b623528ea374935a9d8e1/sql/schema_patch31.sql)، [patch33](https://github.com/merapplications-sketch/Talabat-v3/blob/611b0ebdaa3ed83dd34b623528ea374935a9d8e1/sql/schema_patch33.sql)|تعريفات تاريخية، لا اختيار أعلى patch باعتباره المنشور|
|S4|[تخصيص الكاش و finance_execute](https://github.com/merapplications-sketch/Talabat-v3/blob/611b0ebdaa3ed83dd34b623528ea374935a9d8e1/sql/proposed/pilot_zzzz_cash_allocation_20261106.sql) و[حزمة CASH-01](https://github.com/merapplications-sketch/Talabat-v3/blob/611b0ebdaa3ed83dd34b623528ea374935a9d8e1/docs/pilot-20261105/cash/HANDOFF.md)|حزمة مرشح مرتبطة بقرار؛ وجودها لا يثبت كل كاتب فعّال|
|S5|[الإرجاع](https://github.com/merapplications-sketch/Talabat-v3/blob/611b0ebdaa3ed83dd34b623528ea374935a9d8e1/sql/proposed/pilot_zzz_driver_returns_20261106.sql) و[المحفظة/التذاكر التاريخية](https://github.com/merapplications-sketch/Talabat-v3/blob/611b0ebdaa3ed83dd34b623528ea374935a9d8e1/sql/schema_patch21.sql)|حدود معاملات ومعادلات مصدرية، لا تحويل مالي فعلي|
|S6|[تأكيد تغير الطلب](https://github.com/merapplications-sketch/Talabat-v3/blob/611b0ebdaa3ed83dd34b623528ea374935a9d8e1/sql/proposed/pilot_z_cash_confirmation_20261105.sql)|تسعير ثم موافقة وإعادة كتابة مشروطة؛ لا يفترض مساواة مسار الإنشاء بكل مسارات التعديل|

## جدول العقود

R2(x) أدناه تعني تحديداً `round(numeric_expression,2)` حيث ظهر في النص؛ لا تُستخدم تعريفاً لسياسة التقريب المعتمدة لكل التطبيق. أنواع numeric الوسيطة في الدوال المقروءة غالباً بلا precision/scale صريح. كل صف يحتاج مطابقة أعمدة الهدف و casts والتريغرات قبل اعتماده مستضافاً.

| ID / الحساب | المرجع والمدخلات والوحدات | الترتيب والتقريب والدقة المرصودة | التحويل إلى numeric(12,2) والآثار | ما يمكن اشتقاقه مستقلاً / النقص |
|---|---|---|---|---|
|F01 سعر السطر والمجموع|S1 يستدعي price_line؛ عنصر/خيارات/كمية، مبالغ TJS؛ تعريف الهدف public-price_line.sql خاص|unit يُحوّل من JSON إلى numeric؛ subtotal=sum(price×qty). قواعد اختيار الخيارات ودقتها من تعريف الهدف غير المقروء هنا|إدراج order_items ثم orders؛ أنواع كل أعمدة السعر بالهدف غير محسومة|لا أسعار تشغيل مستقلة بلا نسخة قائمة وأسعار وخيارات معتمدة. يلزم الملف الخاص والإعدادات؛ قيمة fixture ليست مرجعاً|
|F02 خصم المطعم/الصنف|S1 و O3؛ نسبة المطعم والصنف%|خصم كل سطر R2(price×qty×greatest(store_pct,item_pct)/100) ثم sum. لا تقريب سعر الوحدة بدلاً من الخصم المجمع للسطر|orders.discount؛ precision التخزين في الهدف يحتاج target-columns|يمكن حساب مثال اصطناعي من قاعدة معتمدة ومداخل معلنة لاحقاً؛ لم يُختر معدل جديد هنا. أنصاف الكسور والفيض و NULL تحتاج عقداً|
|F03 Happy Hour|O3،S3 happy_hour_pct(uuid,timestamptz default now)→int؛ schedule/day/start/end/store/active/pct|أعلى نسبة نافذة منطبقة؛ Asia/Dushanbe في التعريف؛ بداية شاملة ونهاية غير شاملة وعبور منتصف الليل يتبع اليوم السابق. S1: الفرق بين خصم أفضل نسبة شاملة HH وخصم F02 هو hh_discount؛ يحمل orders.discount مجموع الخصم|المطعم يتحمل الخصم وفق O3؛ العمولة على ما يدفعه العميل للطعام؛ لا أثر محفظة مباشر مثبت في جسم helper التاريخي|إعداد HH الفعلي وتاريخه غير متاح. تعليق قديم في S1 عن تحمل المنصة لا يغيّر قرار O3 ولا الحساب اللاحق؛ تناقض تعليق لا يعتمد كقاعدة مالية|
|F04 التوصيل وأجر السائق|S1 يستدعي delivery_calc(store,lat,lng,uid)؛ lat/lng float8؛ نتائج fee/pay رقمية|لا اشتقاق تعرفة من fixture الثابت. تفاصيل المسافات/الإعدادات/السجل في public-delivery_calc.sql الخاص مطلوبة؛ لا افتراض دقة عمليات المسافة|orders.delivery_fee/driver_payout ثم snapshot_cash؛ أنواع الهدف وال round داخل المساعد غير مثبتة هنا|BLOCKED للتعرفة ومصدرها المستقل؛ تسليم إعدادات التوصيل المؤرخة ومعادلة معتمدة من المختص|
|F05 التوصيل المجاني|O4،S1، stores.free_delivery_min بوحدة TJS؛0 في الوثيقة يعني تعطيل|بعد خصوم الطعام وقبل promo/points: إذا صافي الأطباق≥الحد وكان fee>0 يحفظ fee_waived ثم fee=0؛ المطعم يتحمل الإعفاء وفق O4|orders.fee_waived/delivery_fee وتبعات حصة السائق/المطعم؛ targetcasts غير محسومة|المقارنة والجهة المتحملة قابلتان للاشتقاق من O4؛ قيمة الحد الفعّالة ودقة الرسوم تحتاج إعداداً معتمداً|
|F06 Promo|S1+S2؛ code,base,uid,lock,gate؛ promo_codes.kind/value/min/max/time|base للأطباق غير المخفضة؛ gate لصافي الأطباق؛ percent→R2(base×value/100)، fixed→least(value,base)، ثم clamp0..base. قفل promo عند p_lock؛ استخدامات حسب orders غير المرفوضة/الملغاة|orders.promo_discount/code؛ قراءة promo_codes/orders. check_promo كاتب promo_guess مسار منفصل مقبول توثيقياً|قاعدة النص ليست بديلاً عن قرار الحملات. يلزم إصدار الكود وقيمه وأهلية التداخل؛ لا تشغيل الدالة لإنتاج oracle|
|F07 الإجمالي والعمولة والبقشيش|S1؛ sub,discount,promo,fee,tip,commission_pct؛TJS/%|قبل points: greatest(5,sub-disc-hdisc-promo+fee+tip)؛ commission=R2((sub-disc-hdisc)×pct/100)، دون طرح promo أو points؛ disc هنا v_disc قبل HH، وhdisc=v_hdisc، بينما orders.discount=disc+hdisc؛ payout=delivery_pay+tip. بعد points يعاد تطبيق حد 5 في المرشح|orders.total/commission/driver_payout؛ source numeric بلا scale للوسطاء؛ مواضع casts الهدف غير مكتملة|حد 5 هنا ثابت source **لا قرار مالي جديد**. يلزم مرجع أعمال الحد والعمولة وأنواع الأعمدة. لا اختيار قيمة عمولة أوتعميم round|
|F08 استبدال النقاط|O4؛ S1/S2؛ balance/expiry/points_per_tjs/min_redeem/voucher_points/min_order/storeoverride؛points و TJS|قفل profile؛ cap بعد خصومات/promo؛ pts=floor(min(balance,floor(max(cap,0)×rate))/step)×step؛ step≥1؛ تطابق p_points؛ value=R2(pts/rate). loyalty_spend يستنفد lots بترتيب expires_at,id FOR UPDATE ثم ledger|orders.points_used/points_value/total؛ lots/ledger integers، القيمة numeric؛ casts الهدف غير مكتملة|O4 يثبت 1000 نقطة=1TJS تاريخياً، لاالثوابت 10 في fixture. إعدادات اليوم/الحدود/الانتهاء ومصدر نتائج مستقل ناقصة|
|F09 كسب النقاط و cashback|O3/O4؛ S3 trg_loyalty؛ صافي الطعام=greatest(0,subtotal-discount-promo-points)|على الانتقال إلى delivered وبشرط loyalty_done_atNULL: points=ceil(paid×earn_rate−0.000001)::int؛ cashback=R2(paid×cashback_pct/100). expiry من loyalty_setting؛ إرجاع النقاط عند rejected/cancelled|loyalty_lots/ledger، wallet_entries.amount numeric(12,2) تاريخياًللـcashback؛ حقول done/returned على orders|قاعدة O4 واتجاه تقريب الكسب التاريخي منفصلان عن قيمة الإعداد الفعلي. لا افتراض تفعيل cashback. كل تريغرات الهدف والقيود تحتاج 107|
|F10 المحفظة والخصم|S1؛ requested/balance/total بوحدة TJS؛ wallet_balance و profilelock|R2(least(request,balance,total))؛ رفض غير الموجب/عدم مطابقة المبلغ حسب شروط المصدر؛ INSERT spend سالب ثم wallet_used وقدتتغير payment|numeric وسيط ثم wallet_entries.amount numeric(12,2)؛ NOT NULL و amount<>0 في patch21؛107 يثبت نوع amount تاريخياً، لم تُقرأ الخام هنا|لا استنتاج أن الرصيد وحده يثبتخصماًواحداً. يلزم قيد الأصل وعدد القيود و casts/overflow/NULL وعقد أنصاف الكسور|
|F11 الكاش وتخصيص التوصيل|O1/S4؛ platform_amount صريح مع policy_ref، delivery_feeTJS|platform=المبلغ المعتمد؛ driver_delivery=fee−platform؛ رفض missingpolicy أو platform>fee؛ تجميد snapshot؛ driver_payout يخفض بحصة المنصة|policy.platform_amount و orders.cash_platform_share/cash_driver_delivery_share numeric(12,2)؛ لا round صريح قبل طرح الحصص في snapshot؛ check المجموع=fee|مثالا O1 أدناه مستقلان؛ لا اعتماد المبلغ 5 كتعرفةعامّة. إعداد كل store وتاريخ policy ناقصان|
|F12 التسوية والإيصال|O1/O2/S4؛ requestUUID,operation,targetUUID,amountnumeric,note|settle_cash يجمع حصص المنصة من الصفوف التي انتقلت فع لاً إلى cash_settled_at؛ قفل request→driver→orders(id)؛ صفر المستحق لا يولد إيصالاًمزيفاً؛ wallet_adjust يستخدم round(amount,2)|commands،orders،settlement_receipts/receipt_orders؛ wallet_entries للتعديل؛ الكتابات SQL ضمن معاملة المستدعي، الاستلام النقدي خارجها|المجموع قابل للاشتقاق من حصص مثبتة دون fixture؛ لايدلإيصال DB وحده على استلام النقد. يلزم مرجع الاستلام ومصالحة الجهتين|
|F13 الإرجاع والمطالبة|O1 RETURN-01،S5 order_return_action|p_amount>0≤9999999999.99 و scale≤2؛ لا round تلقائي لقبول مدخل أكثر من منزلتين؛ remaining=paid−sum(confirmed refunds)؛ cancel يحسب delivery_due=R2(driver_payout−tip)|cases.paid/refunds.amount/delivery_due.amount numeric(12,2)؛commands/cases/refunds و orders.status؛ التريغرات المتعدية قد ترد wallet/points|لا تغلق المطالبة بمجرد استلام الوجبة أو report_refund؛ تأكيد مال فعلي هو المرجع. طريقة دفع خارجية لا يثبتها SQL|
|F14 refund عبر الدعم وإرجاع المحفظة|S5 patch21 ticket_set_status و trg_wallet_return؛ تعريف refund_cap المقترح موثق في الجرد السابق|ticketrefund التاريخي يقرب p_refund إلى 2؛ رفض/إلغاء طلب يرجع wallet_used مرةحسب marker وقيد التعارض في النص؛ التوقيع المنشور وإصدارسقف refund غيرمحسومين|support_tickets/ticket_messages/wallet_entries ثم markers؛ amountcast عند التخزين؛ لاخلطرد wallet مع cash فعلي|يلزم تحديد كاتب refund الفعلي وحدوده وتريغراته؛ لا اعتماد نسخة قديمة لتبرير تجاوز سقف حالي|
|F15 تعديل طلب بعد مراجعة مطعم|S6 merchant_review_order/quote_lines/customer_confirm_order؛ لقطة بنود وسعر ومدة/revision/request|المراجعة تحفظ quote؛ التأكيد يتحقق base_total/revision/هوية العميل؛ تبديل items ممنوعمع driver أو wallet/points مستعملة؛ commission=R2(newsubtotal×commission_pct/100) في هذا المسار المقيد|حذف/إدراج order_items ثم orders subtotal/total/commission/status؛ approvals/events/requests في نفس الدالة؛ حراس مرتبطة|لا تعميم صيغة F07 على هذا المسار دون شروط quote_lines. quote_lines يمنع تغييرات السعر مع discount/promo/fee_waived/free_delivery/HappyHour أو wallet/points أو driver؛ النسخة الفعلية وعقد نتائجها لمستقل ناقصان|
|F16 مكافأة التقييم|قبول P1-QA-01 عند 2848327f…، patch32 التاريخي|AFTER INSERT ratings→trg_rating_reward؛ lotreward ثم ledger إذاأُنشئ lot؛ لا افتراض قيمة تعليق+10|ratings/loyalty_lots/loyalty_ledger؛ ربط rate_order بالتريغر المنشور غير مثبت|لا إعادةتحقيق المسار؛ تزويد تعريف النشر والإعداد المعتمد عبر الأدلة الخاصة فقط|
|F17 تسجيل التحصيل عند التسليم|تعريف deliver_order في sql/proposed/pilot_delivery_proof_20261105.sql، p_cash numeric، p_note، p_photo|سائق الطلب وحالة pickedup؛ صورة صحيحةالمسار وموجودة في storage.objects عند تقديمها؛ cash غير سالب؛ اختلاف cash عن total−wallet_used يتطلب note؛ لا round صريح في هذا الجسم|UPDATEorders.cash_collected/cash_note/status؛ نوع cash_collected والتحويل بالهدف يحتاج target-columns؛ قفل order ثم storageobject عند وجود صورة|التسجيل إقرار داخل DB، لا يثبت المال المستلم فع لاً؛ الربط بوصل خارجي وإجراء المصالحة يحتاجان مصدرهما، دون إجراء تحصيل هنا|

## أمثلة مستقلة من قرار المالك، وليست نتائج تشغيل

المصدر O1، والأرقام أمثلة القرار نفسها، لا أسعار مختارة ولا بيانات طلبات حقيقية:

| المثال | اشتقاق مستقل | ما لا يثبته |
|---|---|---|
|طعام 25، توصيل 15، حصة السائق 10، المنصة 5|يدفع السائق 25 للمطعم؛ يستلم 40 من العميل؛ يحتفظ 35=25+10؛ يسلم 5 للمنصة؛ net السائق 10. 40=25+10+5|لا يثبت تعرفة كل المطاعم ولا عمولة المطعم ولا حدود cashback|
|طعام 25، توصيل 15 كلهللسائق، حصة المنصة 0|يستلم 40 ويحتفظ 40=تعويض 25+أجر 15؛ مستحق التوصيل للمنصة 0؛ لا إيصال تحصيل محاسب بمبلغ وهمي|لا ينشئ سياسة افتراضية 0 عند غياب القرار|
|علاقة الولاء التاريخية O4|1000 نقطة/‏1000 نقطة لكل TJS=1TJS. والكسب المذكور 10 نقاط لكل TJS يعطي 1% بالقيمة الاسمية|ليسإثباتاًلـmin_redeem أو voucherstep أو expiry أوتفعيل cashback أوالإعداد الحالي؛ لايشغل redeem فعلياً|

هذه الأمثلة لا تغلق G1-C: المختص المالي يحتاج جدولاً مستقلاً مكتمل الحالات، مداخل اصطناعية معلنة، نسخة قواعد وإعدادات معتمدة، مراجعة مستقلة لكل ناتج، ودقة محددة لكل cast. لا تُستخدم دالة المرشح أو ناتج fixture أو ثوابته oracle.

## سجل الدقة غير المحسومة

1. قاعدة الأعمال لأنصاف الكسور الموجبة والسالبة عند كل خطوة، وقواعد الفيض و NULL، غير موثقة بعقد كامل. ظهور round أونوع numeric لا يحسم اعتماد السياسة.
2. مخرجات delivery_calc/price_line والاعتماديات/أنواع الأعمدة في لقطة 107 تحتاج قراءة الخام؛ التحويل float8 للإحداثيات لايحوّل الحساب المالي إلى float افتراضياً.
3. التحويل عند INSERT إلى numeric(12,2) ليسمرادفاًلتقريب إرادي قبل تجميع السطور؛ لا يمكن تعميم هذه الفرضية على orders/items/receipts.
4. اختلاف مصدر تاريخي عن مرشح 106 لا يسمح بتغيير معادلة أواختيار إعداد؛ يُربط التعريف بالنشر ثم بالقرار المعتمد.
5. كل أثر مالي داخلي يحتاج T، والخارجي إن ثبت يحتاج X، وكلاهما R في الخطة 108. المسؤول DB+مختصمالي؛ المراجعة QA مستقل. لا تشغيل لهذه الحزم ضمن هذا التكليف.

## تحديث RECEIVED EVIDENCE ALIGNMENT — لقطة الهدف المقروءة

هذا الملحق يحدّث درجة إثبات تعريف الهدف في F01..F17 ؛ لا يغير القواعد أو الأمثلة المعتمدة أعلاه. عبارة «غير متاح/غير مثبت من الخام» في الوصف السابق تخص حالة الحزمة قبل الاستلام. الاستلام 49/49 ثابت بالإيصال؛ القراءة الحالية ليست اختباراً أو oracle مستقلاً. ترميز R/D/P/TT/COL/IX كما في سجل الكتّاب، وأسماء الملفات إحالات خاصة لا نسخ عامة.

| العقد | ما أصبح موثقاً من الأصل | الدقة والتحويل والأثر | ما بقي ناقصاً |
|---|---|---|---|
|F01|D/R(18487) price_line مع menu_items/options/groups ؛ D(18485) يضرب السعر بكمية البنود ثم يجمع|السعر والوسائط numeric ؛ COL(public.order_items.price)=numeric ؛ لا numeric(12,2) مفترض لهذا العمود؛ خيارات snap من الجسم|إصدار أسعار/خيارات معتمد ونتائج مرجعية مستقلة؛ لا استعمال ناتج الدالة نفسها oracle|
|F02|D(18485) يختار الأكبر من خصم المطعم والصنف لكل سطر|round(numeric,2) لكل سطر ثم الجمع؛ orders.discount= numeric ؛ قراءة التعريف لا تقرر سياسة كسور جديدة|قيم الأسعار والنسب والإعدادات المعتمدة ومطابقة نتائجها مستقلاً|
|F03|D(18469) يقرأ happy_hours بتوقيت Dushanbe ويعالج النافذة العابرة لمنتصف الليل؛ D(18485) يدمج الخصم ويحسب فرق HappyHour|اختيار أقصى نسبة ملائمة؛ التقريب في مسار السطر؛ لا ثبات صفر fixture ولا تبنّي قيمة fallback|الإعدادات والنوافذ المعتمدة وإصدارها؛ قبول O3 السابق محفوظ|
|F04|public-delivery_calc.sql و D(18449)، المساعد dist_km في D(18453)، stores/app_settings/orders|المسافة float8 ؛ حاصل ضرب عامل الطريق يتحول إلى numeric ثم round(...,2)؛ عدد الخطوات ceil بعد round(...,6)؛ الباقي numeric ؛ إعدادات السائق النقدية لاحقاً عبر T09|قيم الإعدادات غير ملتقطة هنا؛ لا تُعامل ثوابت COALESCE كقيم تشغيل؛ oracle مسافة مستقل وعقد القيم الحديّة ناقصان|
|F05|D(18485) يطبق threshold إعفاء رسوم المطعم؛ D(18449) يراجع تاريخ الطلبات لأول توصيل مجاني|fee_waived/delivery_fee في COL نوعهما numeric ؛ لا تحويل 12,2 عام؛ بيانات الطلبات السابقة لم تُقرأ|اعتماد الإعداد وقواعد التوقعات؛ لا أمثلة ببيانات حقيقية|
|F06|D(18441/18442/18488): promo_guess و promo_attempts ؛ price_line ثم promo_eval ؛ place_order يتطلب محاولة تحقق سابقة|الفروع والاستثناءات وأقفال العرض موثقة في W26/W38/T04 ؛ السجلات داخل caller وليست أثر خصم خارجي|لا حصر حملة فعالة أو سباق تحديثها أو نجاح rate limit من النص وحده|
|F07|D(18485) يجمع المكونات ويقرب العمولة؛ D(18835) يعيد حساب عمولة تعديل الطلب بمساره المقيد|COL orders subtotal/total/commission/driver_payout نوع numeric ؛ subtotal NOT NULL مع default0 ؛ لا يجعل default دليلاً على طلب فارغ محفوظ|عقد التقريب للحالات الحدية/NULL/الفيض ومصدر expected values المعتمد خارج fixture|
|F08|D(18474/18475/18476/18485): lots ثم قسائم صحيحة وتحويل قيمة النقاط|floor للقسائم؛ points_value round(...,2)؛ lots/ledger points integer ؛ قفل lots بترتيب expiry,id|إعدادات loyalty الفعلية و expiry والتوافق مع account/request isolation ؛ لا رصيد حي مقروء|
|F09|D(18528) + TT(18675): عند التسليم earn/ledger و cashback ؛ عند الإلغاء/الرفض return points|earn يستخدم ceil مع offset الموجود في التعريف؛ cashback round(...,2) ثم wallet_entries.amount numeric(12,2)؛ markers ضمن NEW ؛ IX على lots/wallet لا على ledger نفسه|إثبات عدم تكرار كل أثر/rollback و restore مع triggers كاملة؛ لا تغيير معادلة أو اعتماد نسبة جديدة|
|F10|D(18485/18539) و COL/IX(wallet_entries): spend مع profilelock و one_spend_per_order|round للأقل بينالمطلوب/الرصيد/الإجمالي ثم تخزين amount numeric(12,2)؛ كُتّاب refund/return/cashback/adjust متعدّون|حصر كل service/owner writer ، أثرالعزل، قبول rollback/ACK من تنفيذ مستقل لاحق|
|F11|D(18999/19000) و TT(19001): snapshot_cash والسياسة والحارس|cash_delivery_policy.platform_amount و orders.cash_platform_share/cash_driver_delivery_share نوع numeric(12,2)؛ التحويل عند التخزين؛ driver_payout numeric ؛ قفل order ثم policy SHARE|صف سياسة معتمد بإصدار ومرجعه الخارجي؛ لا استنتاج القيمة من fixture أو التعريف|
|F12|D(18697/18698/18751/18754)، TT(18752/18753): command/result/receipt وربطه بالطلبات|wallet_adjust يقرب 2 ثم amount12,2 ؛ settlement_receipts.amount و settlement_receipt_orders.amount نوع numeric ؛ جمعالحصة من orders المحددة المقفلة|دليل استلام نقد خارجي ومصالحة ACK/restore ؛ سجل receipt وحده لا يثبت النقل المادي|
|F13|D(18978/18975/18980)، TT(18981): اتفاق/عودة/مطالبة/refund/command|refund و delivery_due.amount نوع numeric(12,2)؛ body يرفض scale>2 لمبلغالطلب، ويقرب delivery_due ؛ ledger النقدي الخارجي ليسداخل SQL|مرجع الاتفاق الحقيقي وربط source_ref بالفعل الخارجي وآلية dedup/مصالحة؛ تبقى BLOCKED|
|F14|D(18522/18534) +TT(18669): ticketrefund بقفل ticket ثم order وسقف تراكمي؛ walletreturn مستقل عند cancel/reject|round(p_refund,2)؛ amount12,2 ؛ IXone_refund_per_ticket و one_return_per_order ؛ تعريف ticket الحالي لا يكتب ticket_messages|لا يثبت رداً نقدياً خارجياً؛ قبولالتزامن/التراجع الحالي يحتاج تنفيذمخوّل لاحقاً|
|F15|D(18831/18833/18835) مع TT لحراس order/items/offers|quote numeric ؛ تأكيد items مشروط ويعيد commission ؛ no wallet/points repricing فيمسار quote المقيد|مصدر نتائج مستقل لكلحالة وقبول الآثارالمتعدية؛ لا تغيرعقدالموافقة المقبول|
|F16|D(18490/18531/18530)، TT(18674/18665)، IXratings_pkey و loyalty_one_reward_per_order|rate_order→ratings→rewardlot/ledger و aggregate→stores ؛ ledger للمكافأة فقطعندإنشاء lot ؛ مقدارالمكافأة من loyalty_setting|ربطكانمحتملًاوأصبحمثبتاًبنيوياً؛ قيمةإعدادالمكافأة واعتمادها/تنفيذها لاتثبتان من الكتالوج|
|F17|D(18448) و COL(orders.cash_collected) و storage.objects dependency|cash_collected نوع numeric لا 12,2 ؛ لا round صريح في body ؛ orderlock ثم storage KEY SHARE عند photo ؛ تسجيل DB لااستلاممال|بايتات Storage والتفويض CDN/الإبطال، ومصدرإقرارالكاش الخارجي؛ جميعها غير مختبرة|

### حدود قبول الآثار المالية

الكتابات المتزامنة في W01/W05/W06/W08/W13–W18 والتريغرات المرتبطة مثبتة **بنيوياً ضمن معاملة caller** فقط. لم تُجرّب نقاط فشل أو انقطاع أو استعادة. W12 يلتقط خطأ حدث الوصول ويواصل؛ W26/W38 لديهما معالجة استثناءات محلية؛ يجب اختبار الأثر المطلوب لكل فرع لاحقاً، لا قبول عبارة ذرية عامة.

مسؤول DB يقدّم حدود المستدعي وترتيب الأقفال لجميع الكتّاب الفعلية، و QA المالي/الأمني يقبل دليل التنفيذ لاحقاً بعد التفويض. مسؤول المالية/التشغيل يقدّم سجل الاستلام/التحويل ومرجع المستلم والمصالحة؛ لا نفترض آلية idempotency خارجية. يبقى أي مسار بلا آلية إثبات BLOCKED. لم تتغير قيم أو نسب أو قواعد عمل، ولم تُعتمد سياسة تقريب أو احتفاظ أو RPO/RTO جديدة.

## تصحيح G1-C — G1C-DOC-01 / SRC-02 / PREC-03

التفصيل وإحالات المصدر ونتيجة تحليل المجال في [G1-C-FINDINGS.md](G1-C-FINDINGS.md). المرجع الأساس f9458cc6f449080ca60d95baf768850ad1f5e883؛ المراجعة المستقلة77ac8d971ff886ed2c5540b252b476cd21181d54. هذا التصحيح يعلو على الوصف السابق حيث يتعارض معه، ولا يعدل SQL أو أي قرار أعمال.

- F07: نرمز S=subtotal، D0=v_disc (خصم المطعم/الصنف قبل إضافة HH)، H=v_hdisc، D=orders.discount=D0+H، P=promo_discount، V=points_value، F=delivery_fee، T=tip، C=commission_pct. العمولة المقروءة round((S−D)×C/100,2)، وهي نفسها round((S−D0−H)×C/100,2). لا طرح P أو V من وعائها، ولا طرح H ثانية بعد D.
- الإجمالي المقروء قبل النقاط max(5,S−D−P+F+T)، وبعدها max(5,S−D−P−V+F+T). وعاء الكسب max(0,S−D−P−V)، دون F/T؛ المحفظة وسيلة دفع ولا تطرح ثانية من total أو وعاء الكسب. أجر السائق الأولي delivery_pay+T ثم تخصيص الكاش إن انطبق. تصحيح الوصف لا يحسم ممول promo أو تعرفة تشغيلية.
- G1C-SRC-02: قرار5/10/20 محفوظ؛ واجهة العميل0/5/10/20، بينما قبول SQL المقروء0/3/5/10 يحول20 إلى0. الفرق مصدري، لا نتيجة HTTP جديدة. نطاق الإصلاح والقبول مقترحان في الملحق، ولم ينفذا.
- G1C-PREC-03: أضيف تتبع السعر ومعدل الكسب والحراس والقيود، ومثال كسري مسموح بنيوياً ضمن شروطه يبين فرق epsilon. لا إثبات قبول API حالي ولا تعديل لقاعدة الكسب. numeric(12,2) للمحفظة لا يقيّد subtotal أو tip أو price تلقائياً.
- المراجع المستعادة والقرارات المتبقية مفصلة بحسب F01..F17 في الملحق؛ لا إعادة سؤال عن HH/النقاط على المطعم أو خيارات الإكرامية أو CASH-01. G1-C تبقى PARTIAL / BLOCKED، والمرحلة2 NO-GO.



## دلتا تجهيز الميزات الحالية — 2026-11-12

أجوبة Q09–25 المحسومة تتقدم على الأسئلة التاريخية؛ لا إعادة اعتماد TIP/NULL. بطاقات B04 تفصل الإعداد المؤرخ وoracle عن السياسة، وتحدد فروق F05/Q21 وF07/Q23 وPREC-03 دون تعديل معادلة. CASH مستقل، والمقاصة وحدها تعتمد CC-E01.

[التسليم الموحد](../phase1-feature-readiness/REPORT-AR.md) — [بطاقات الدليل](../phase1-feature-readiness/EVIDENCE-WORK-PACKETS.md) — [عقد القياس](../phase1-feature-readiness/MEASUREMENT-CONTRACT.md).
هذه إضافة إحالة فقط؛ النص والصفوف السابقة لم تتغير. PHASE1 PARTIAL/BLOCKED؛ PHASE2 NO-GO؛ بانتظار مراجعة مستقلة للدلتا.
