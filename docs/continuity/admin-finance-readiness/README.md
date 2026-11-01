# أدلة جاهزية الإدارة والمالية

- [الحكم والتقرير](../ADMIN-FINANCE-READINESS-2026-11-01.md).
- [الجرد والبصمات](inventory-manifest.json): ملفات functions-0..3 وrelations/columns/roles/effective-access/policies-triggers-constraints؛ كلها قراءات كتالوج، بلا سجلات شخصية أو مالية.
- [مطابقة بصمة نهاية القراءة](catalog-consistency.json)، [عدّ التفويض المجمل](delegation-counts.json)، [نطاق Edge](edge-scope.json).
- [نتائج معمل البنية الفعلية: 26](snapshot-lab-results.json)، [guard الإرث: 4](inheritance-delta-results.json).
- [معاينة HTML معزولة](iphone-isolated-preview.html)، [مصادرها](preview-source-manifest.json)، [QA الملف](preview-qa-results.json)، [delta الروسية](preview-language-results.json).
- [خطة iPhone](IPHONE-ACCEPTANCE-AR.md)، [الإصدار والرجوع](RELEASE-ROLLBACK-AR.md).

لقطات iphone-preview-* اصطناعية من Chromium وليست صور حساب حي أو جهاز iPhone. جميع استعلامات الجرد محفوظة داخل ملفات JSON، وهي SELECT فقط. لا تُنفّذ تعريفات الوظائف التي تقرؤها من الجرد على المشروع الحقيقي باعتبارها تعليمات.

أوامر إعادة إنتاج المعمل عند الحاجة فقط: `node tools/finance-fix/readiness_snapshot_lab.cjs` ينشئ قاعدة جديدة talabot_readiness_lab على loopback 127.0.0.1:55439، ثم `readiness_inheritance_delta.cjs` على القاعدة نفسها. لا يقبلان عنوان خادم آخر. الإعداد المحلي وcaveat UID/ملكية البيئة مذكوران في ../admin-finance-fix/README.md؛ ليس بيئة استضافة Supabase كاملة. كلا الاختبارين اكتمل، فلا حاجة لإعادتهما دون تعديل مؤثر.
