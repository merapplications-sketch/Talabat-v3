# TALABOT — Owner & Team Playbook / دليل الفريق

**Saved:** 14 نوفمبر 2026، دوشنبه  
**Branch:** `docs/owner-playbook-pilot-first-20261114` (documentation-only review branch)  
**State:** Files are saved and visible to the team in GitHub; **new team policies are REVIEW DRAFTS**, not replacements for owner-approved contracts. No merge, code modification, deployment or product redesign was performed by this playbook.

## الهدف المعتمد من المالك
**نجهّز TALABOT بميزاته الحالية للإطلاق التجريبي الآمن أولًا، ثم نرتب تطوير الميزات الجديدة على مراحل.**  
ميزة **الطلب من الخارج للمستلم المحلي** أولوية عالية لمرحلة لاحقة، لكنها ليست تفويض تنفيذ الآن.

## قبل أن تبدأ أي مهمة
1. افتح [سجل المدير #26](https://github.com/merapplications-sketch/Talabat-v3/issues/26) واقرأ آخر التعليقات والتكليف المخصص لك.
2. اقرأ [فهرس القرارات الأصلية](./SOURCE-OF-TRUTH.md) ثم [القرارات المعتمدة للمُلاك](../OWNER-AGREEMENTS-AR.md) و[آخر سجل استمرارية المرحلة الأولى](../continuity/PHASE1-CURRENT.md). عند التعارض، قرارات المالك المعتمدة هي الحاكمة.
3. ثبّت أحدث **HEAD/branch/commit** للمصدر الذي يُطلب منك فحصه. لا تستبدل `main` أو مرجع قديم بمرشح أحدث دون مقارنات موثقة.
4. اتبع **دورك فقط** وقدم دلتا أدلة واحدة. لا تفترض أن تعليق GitHub يوقظ محادثات الفريق المتوقفة.

## الملفات التي حفظناها

| الملف | الغرض | الحالة |
|---|---|---|
| [AGENTS.md](../../AGENTS.md) | نقطة دخول الفريق ومسار استعادة العمل | مسودة قابلة للمراجعة |
| [AI RULES.md](../ai/RULES.md) | حدود الصلاحية وحماية المعتمد والإنتاج | مسودة مقترحة |
| [Decision Protocol](../ai/DECISION-PROTOCOL.md) | بروتوكول القرار بناءً على الأدلة وSTOP/GO | مسودة مقترحة |
| [Pilot Readiness SKILL.md](../../.agents/skills/talabot-pilot-readiness/SKILL.md) | خطوات تدقيق الجاهزية والسلامة | مسودة مقترحة |
| [Pilot Gates](../launch/PILOT-GATES.md) | قائمة مراجعة البوابات، ليست تغييرًا لـG1 | قائمة مرجعية |
| [Pilot Risks](../launch/RISK-AND-TEST-PRIORITIES.md) | 13 مجموعة مخاطر تشغيل أولية | قائمة مراجعة |
| [Post-pilot Roadmap](../roadmap/POST-PILOT-PROPOSALS.md) | التطوير المرحلي، وخاصة الطلب الدولي للمستلم المحلي | أفكار مستقبلية غير معتمدة |
| [Global Feature + QA report](../benchmark/TALABOT-20261114-feature-risk-global.md) | مقارنة RoaQ, Talabat, Uber Eats و11 منصة، وQA-01..QA-52 | بحث ومخاطر، لا تكليف تطوير |
| [HTML comparison](../benchmark/TALABOT-20261114-feature-risk-global.html) | نسخة قابلة للعرض للجداول الطويلة | تقرير بحثي |
| [Source of Truth](./SOURCE-OF-TRUTH.md) | روابط الخطط والقرارات الأصلية المعتمدة | فهرس إحالات، لا اتفاق جديد |
| [Owner handoff](./OWNER-HANDOFF-TO-MANAGER.md) | رسالة استكمال المدير والتكليف التالي | مسودة جاهزة للمراجعة |
| [How to view/edit](./HOW-TO-EDIT.md) | خطوات عرض وتعديل الملفات عبر GitHub | إرشادات |

## حالة التشغيل عند الحفظ (14 نوفمبر 2026)
- آخر تسليم مُراجع في [Issue #39](https://github.com/merapplications-sketch/Talabat-v3/issues/39) أصلح فرض الروسية في معاينة Safari **الوهمية فقط** عند `3f74b29a`.
- 8/8 محاكاة جافاسكريبت لحفظ اللغة PASS؛ **اختبار المتصفح الحقيقي / الشبكة / iPhone Safari لم ينجز**.
- formal current-source E2E: **0/51**؛ Admin **0/21**؛ G1-A/B/C/E/F PARTIAL وG1-D BLOCKED. الإصدار والإطلاق الحقيقي **NO-GO** وفق دليل الإدارة الحالي.
- هذه أرقام **آخر مراجعة موثقة** وليست حكمًا أبديًا. كل دور يعيد فحص أحدث سجل وتحديثاته قبل استخدام هذه الأرقام.

## إدارة التغييرات
- للمالك مراجعة الملفات وإبداء تعديلات؛ استعمل [طريقة التعديل](./HOW-TO-EDIT.md) على **فرع المراجعة وحده**.
- للمبرمج/المصمم/المستشار حق إضافة الأدلة في فروعهم المصرح بها، مع ارتباطها بالـIssue. لا تفويض تلقائي لدمج هذه المسودة أو استخدامها كسياسة أعلى من الموافقات.
- عند تعارض نص هنا مع اتفاق Approved، لا تصلحه بصمت. اعرض التعارض ورابط القرار للمالك.
- ربط ملخص الفرع في #26 لا يعني قبول الخطة أو تشغيل المهام.

## مكان الخطط الأصلية
هذا الملف **يؤشر** إلى القرارات والخطط التي راجعناها، ولا يدعي استيعاب جميع نقاشات المشروع السابقة. [الخريطة الأصلية](./SOURCE-OF-TRUTH.md) هي بداية التدقيق، ويبقى سجل المدير والقرارات الموثقة حاكماً.