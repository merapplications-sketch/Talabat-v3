# G1 — استكمال التسليم نفسه: الأصول وسجلات التشغيل

> **تحديث الحالة — 12 نوفمبر2026:** أصل35 مسترجع ومطابق وفق إيصال الإدارة عند7d832904؛ انتهى مانع الوصول للملفات17 في نطاق استرجاع الأصل. [دلتا الربط الحالية](SOURCE35-ALIGNMENT.md) تفصل الاعتماديات المتاحة عن الربط التشغيلي الباقي. أحكام05084193 السابقة محفوظة: G1-A/B/C/E/F PARTIAL وG1-D BLOCKED؛ مراجعة هذا الفرق فقط ما زالت مطلوبة. وصف الحجب ومحاولةGit128 أدناه تاريخيان ولا يمثلان الحالة الحالية.
2026-11-12 UTC. DOCUMENTATION DELTA — PENDING INDEPENDENT QA.
الأساس a7d011dc54a7e129f882ad263b34f21d352521f8 ؛ فرع docs/phase1-feature-readiness-20261112.
[آخر سجل إدارة مقروء](https://github.com/merapplications-sketch/Talabat-v3/blob/fb88868d798e4b08f1f1f0f91dd7be9458d1816b/docs/continuity/PHASE1-CURRENT.md) عند fb88868d798e4b08f1f1f0f91dd7be9458d1816b. لا دمج فرع الإدارة ولا تغيير تكليف أو قرار.
هذه إضافة إلى REPORT-AR و EVIDENCE-WORK-PACKETS ، لا استبدال لهما. الأدلة التاريخية نتائج منفذيها؛ القراءة الحالية ليست إعادة تنفيذها.

## 1. النتيجة الفعلية لاسترجاع أصل 35 — B02/B09
- ثبت المصدر المطلوب bb73be06f4f60d3125eccc7c6fd45fda9b72db42 ومستودع Sites الأصلي من TALABOT-MASTER-ENGINEERING-HANDOFF.txt ، إصدار 0 ، الأسطر 37–42 ؛ قرئ الأصل النصي الموجود في القناة الخاصة. لم يُنشر النص الخام أو عنوان Git الخاص.
- [إيصال الإدارة](https://github.com/merapplications-sketch/Talabat-v3/blob/fb88868d798e4b08f1f1f0f91dd7be9458d1816b/docs/continuity/evidence/20261112-ci106-build-gate/source-provenance-receipt.json) يربط hosting35 بمصدره و deployment appgdep_6aef74a0afc481918ac4eb9641b22fd5 ؛ succeeded بتاريخ 2026-11-07T18:57:55.085244+00:00. أرشيف المزود موصوف 2467840 بايت/ملفان و SHA256 92ed9c87f140ce0e485098222805183952eb6282e4959d1327588e0fa09a7546 ؛ **metadata فقط، لم تُسترجع بايتاته هنا ولا يثبت اكتمال المصدر**.
- محاولة مستقلة واحدة من جلسة المبرمج: GIT_TERMINAL_PROMPT=0 git ls-remote --symref <المستودع المحدد> HEAD. النتيجة exit128: fatal: could not read Username for 'https://git.chatgpt-team.site': terminal prompts disabled. لم تبدأ عملية clone مستمرة، ولم يُنشأ اعتماد أو تُغيّر صلاحية. ليست دليلاً على ضياع المصدر.
- get_site للمشروع المحدد أعاد أحدث نسخة محفوظة 58 دون source_repository_credential. أداة إنشاء اعتماد الكتابة ليست قناة قراءة قائمة؛ لم تستخدم. لا يطلب هذا التسليم كلمة مرور أو مادة اعتماد في المحادثة.
- [جدول البصمات 28](https://github.com/merapplications-sketch/Talabat-v3/blob/fb88868d798e4b08f1f1f0f91dd7be9458d1816b/docs/continuity/evidence/20261112-ci106-build-gate/build-gate-recovery.json) محفوظ كما استرجعته الإدارة:11 مطابقة، 7 مرشحات مختلفة، 10 أسماء غير موجودة في الشجرة المفحوصة. لم تُحسب ثانية ولم تُركب نسخة هجينة. هذه ليست جميع اعتماديات البناء.
- المطلوب من **حائز مستودع Sites الأصلي في الحساب نفسه**: إتاحة قراءة المصدر المثبت عبر قناة Git مخولة قائمة، أو تصدير أصلي/bundle لذلك Commit إلى قناة خاصة معتمدة، شاملاً manifests/assets/vendor و public/scripts/tests/worker. المدير يحدد الشخص الحائز؛ لا يوجد اسم مشغّل مثبت في المصادر. يقارن المبرمج البايتات بالجدول قبل أي ادعاء استعادة. لا حاجة لتفويض نشر أو write credential لهذا الغرض.

### الملفات 17 التي لا يثبت الجدول امتلاك أصلها المطابق
- `public/admin.html` — المرشح المقروء مختلف؛ البصمة المطلوبة في جدول الإدارة.
- `public/assets/mfa.js` — لا اسم مماثل في الشجرة المفحوصة؛ البصمة المطلوبة في جدول الإدارة.
- `public/customer.html` — المرشح المقروء مختلف؛ البصمة المطلوبة في جدول الإدارة.
- `public/driver.html` — المرشح المقروء مختلف؛ البصمة المطلوبة في جدول الإدارة.
- `public/merchant.html` — المرشح المقروء مختلف؛ البصمة المطلوبة في جدول الإدارة.
- `public/talabat-core.js` — المرشح المقروء مختلف؛ البصمة المطلوبة في جدول الإدارة.
- `scripts/csp-policy.mjs` — لا اسم مماثل في الشجرة المفحوصة؛ البصمة المطلوبة في جدول الإدارة.
- `tests/admin-idle.cjs` — لا اسم مماثل في الشجرة المفحوصة؛ البصمة المطلوبة في جدول الإدارة.
- `tests/customer-auth-scope.cjs` — لا اسم مماثل في الشجرة المفحوصة؛ البصمة المطلوبة في جدول الإدارة.
- `tests/image-limits.cjs` — لا اسم مماثل في الشجرة المفحوصة؛ البصمة المطلوبة في جدول الإدارة.
- `tests/map-policy.cjs` — لا اسم مماثل في الشجرة المفحوصة؛ البصمة المطلوبة في جدول الإدارة.
- `tests/merchant-report.cjs` — المرشح المقروء مختلف؛ البصمة المطلوبة في جدول الإدارة.
- `tests/mfa.cjs` — لا اسم مماثل في الشجرة المفحوصة؛ البصمة المطلوبة في جدول الإدارة.
- `tests/proof-access.cjs` — لا اسم مماثل في الشجرة المفحوصة؛ البصمة المطلوبة في جدول الإدارة.
- `tests/return-receipt.cjs` — المرشح المقروء مختلف؛ البصمة المطلوبة في جدول الإدارة.
- `tests/test-inline-context.py` — لا اسم مماثل في الشجرة المفحوصة؛ البصمة المطلوبة في جدول الإدارة.
- `worker/index.js` — لا اسم مماثل في الشجرة المفحوصة؛ البصمة المطلوبة في جدول الإدارة.
لا تعني هذه القائمة غياب الملفات عالمياً. dependencies غير المدرجة 28 و db-evidence-binding تحتاج مصادرها الخاصة؛ لا تعويض بأدلة الطلب 3 أو fixture.

## 2. النشر والجدولة والتوزيع والمراقبة — B02/B03/B07/B09
| الأصل المقروء | ما أضيف للحزمة | الحد المتبقي |
|---|---|---|
| إيصال Sites35/41/58 أعلاه | ربط نسخة 35 بالمصدر؛ نسخة 58 بالمصدر c6e82b51e15d2e9de80a55fb0145a63b1a48e0a5 و deployment appgdep_6af0d0ddf03081918c11b3224b95d064 الناجح بتاريخ 2026-11-08T19:43:43.149586Z | لا بايتات فعالة لكل تطبيق/core/ملحق ولا backend مطابق؛ لا دمج سجل startup بمضيف Sites |
| قراءة get_site الحالية | automations=[] في المشروع المحدد | لا جدول Sites مرتبط ظاهر؛ لا نفي cron/Worker/queue خارجي |
| ملفات .github/workflows في الأساس | قرئت 19/19 ملفاً؛ لا schedule/cron مصرح به في النصوص المقروءة؛ أسماء و blob IDs في الإيصال المرافق | هذه workflows اختبار/تحضير وليست إثبات scheduler توزيع أو مراقبة؛ لا تشغيل جديد |
| [A07/W04 في إيصال الإدارة](https://github.com/merapplications-sketch/Talabat-v3/blob/fb88868d798e4b08f1f1f0f91dd7be9458d1816b/docs/continuity/evidence/20261112-g1-runtime-linkage/writer-runtime-evidence-receipt.json) | dispatch_tick من المتصفح؛ حد 4000ms داخل الصفحة، و skip لحلقة polling عند document.hidden | ليس حداً عالمياً ولا إثبات Job خادمي أو توقف كل callbacks ؛ deployment/actor/transaction/drain غير مثبتة |
| A08 في الإيصال نفسه | ربط ops/pilot-watchdog.py واختباره بالمصدر 606da113 ؛ حفظ journal وقفل ملف وإعادة محاولة بالمعرف نفسه | قفل ملف لا يحسم تزامن عدة خوادم؛ POST ثم حفظ إيصال ليسا معاملة ذرية واحدة |
| LOCAL-EVIDENCE في alert-repair |11 حالة متانة و 4 سابقة مقبولة بحدودها، وبصمتا المصدر مثبتتان من الإدارة | لا إعادة إصلاح أو اختبار؛ real_on_call_delivery/human_acknowledgement/real_escalation=false |
| [HOST-EVIDENCE](https://github.com/merapplications-sketch/Talabat-v3/blob/a7d011dc54a7e129f882ad263b34f21d352521f8/docs/pilot-20261105/operations/alert-repair/HOST-EVIDENCE.json) | مصدر 606da113 ، Auth/REST/SMTP عبر loopback و Mailpit ؛ live=false و current_host_configuration_mirrored=false | ليست هوية طلب على Supabase أو بريد خارجي أو دور تشغيل حالي |

لا يُغيّر هذا الربط تعريف W04 أو ينشئ جرداً موازياً. جميع التطبيقات الأربعة والنواة تظل بسلسلة النشر الجزئية السابقة؛ TailAdmin معاينة منفصلة.

## 3. استكمال B02–B09: أصل موجود أو مورد محدد
أسماء المخرجات المطلوبة أدناه عقود تسليم موجودة في EVIDENCE-WORK-PACKETS ؛ ليست ملفات ادعينا استرجاعها. المسؤول الوظيفي ليس شخصاً عُيّن أو وصولاً مُنح.

| البطاقة | النتيجة الجديدة/الأصل المثبت | النقص والملف أو السجل المحدد | حامل المورد والقناة/الفعل التالي |
|---|---|---|---|
| B02 | source-provenance-receipt وربط 35/58 ؛ فشل وصول المصدر موثق | أصل 35 ؛ DEPLOYMENT-LINKS لكل customer/merchant/driver/admin/core وملحقات receipt/finance/returns مع artifact/config/backend | حائز Sites: قراءة Git/تصدير Commit أصلي خاص؛ مسؤول نشر كل واجهة: سجل artifact→deployment محفوظ. لا فحص تطبيق مستضاف هنا |
| B03 | writer-runtime-evidence-receipt و 19workflow و Sitesautomations | WRITER-BOUNDARIES لل Jobs: config scheduler/Worker ، deployment ID ، actor ، آخر run محفوظ، تعددالمثيلات، pause/drain/resume | حائز مشغل dispatch/watchdog يسلّم config وسجلتشغيل منقحين عبرقناة خاصة؛ إن لم يُعيّن مورد لا نستنتج عدم وجوده، والمدير يحددحائزه قبل طلبنفاذ |
| B04 | عقد F01..17 وأجوبة Q18..25 و QA PREC-03 كما فيالحزمةالأصلية؛ لم يرد إعداد/oracle جديد ضمن الموادالمسترجعة | FINANCE-ORACLE-PACK: إصدار تعرفة/أسعار/خيارات وحملات/مموليها و round/tie/residual ومراجع effective_at | حائز عقودالمتاجر والحملات يسلمالنسخالمؤرخة القائمة خاصة؛ QA يستخرج expected مستقلاً. السياسةمحسومةلايعادسؤالها؛ PREC مسارمنفصل ولااختبارجديد |
| B05 | HOST-EVIDENCE يثبت معملالأدوارفقط؛ R05 يبقىمرجعخصائص لا trace | REQUEST-SCOPED-TRACE لنفس RPC/هوية/isolation/version/COMMIT ؛ لا يثبتغيابه أن logging لاينتجه | حائز API/gateway يسلم trace قائماًمنقحاً عبرقناةمخوّلة؛ إن لميسجل الحقول يحددذلك ثم نطاق TRACE-CAPTURE منفصل. لااستعلامأوجلسةهنا |
| B06 | key_exported=false فيدليلالتعافيالاصطناعي؛ ليسحيازةمفتاحتشغيلي | KEY-CUSTODY-METADATA: keyID/version/domain/custodian/retained ومرجعنسخ/إتاحةالمفاتيحالقديمة | حائزالمخزنالمستخدمفعلاً يسلم metadata وإيصالإتاحةخاصاً؛ لاافتراض KMS ولامادةمفتاح ولاتدوير |
| B07 | مصدر watchdog يحفظ event_id ؛ حد POST/receipt منفصل؛ finReconcile و finance_command_status محفوظان | RECONCILIATION-PAIR للأثرالخارجي، وعقدمستقبلالتنبيه durable dedup/lookup وإيصالاستلامفعلي | حائزالقناة/المستقبليسلّم عقداًوإيصالاًقائمين؛ حائزسندالنقديسلّم مرجعاًمنقحاً غيرمحمي؛ لاحدثأوحركةجديدة؛ CC-E01 للمقاصةفقط |
| B08 | أدلة SOURCE-PASS/RESTORE-PASS أدناه: PostgreSQL و Storage بينمشغلينمستقلين | BACKUP-COVERAGE التشغيلي: backupID/PITR/WAL/retention ، Storagebytes/versions ، bindings/closures/keys ،حجمممثل ووجهةمعزولة | حائزنسخ DB و Storage وأمينالمفتاح يسلمونفهرساً/إيصالاًقائماًخاصاً؛ لاتنزيلنسخةحساسةأواستعادة. RPO/RTO قرارلاحقبمقترحمدعوم |
| B09 |CI106 محفوظفي Git بإيصالالإدارة؛ قبولالمراقبالمحليمحفوظ؛ توثيقالتعافيالمسترجع | build-gate الأصل/قناة db-evidence-binding ؛ قناة HTTP ب finance/orders/outsider ؛رد SU-543851 ؛موارد iPhone/طابعة/قناةتنبيه | حائز CI يوفرقناةأدلةخاصةمحددة ACL/retention ؛ حائزبيئة QA يوثقالموردوالنطاق؛ حائزتذكرة Storage يسلمرداًمؤرخاً؛ منسقالجهازيوفرطراز/OS/HTTPS/SHA. لااختباراتالآن |

### B08: دليل إضافي محدد لا يُختزل إلى SQLite
قرئت [INDEX](https://github.com/merapplications-sketch/Talabat-v3/blob/a7d011dc54a7e129f882ad263b34f21d352521f8/docs/pilot-20261105/operations/external-acceptance/INDEX.json) و[SOURCE-PASS](https://github.com/merapplications-sketch/Talabat-v3/blob/a7d011dc54a7e129f882ad263b34f21d352521f8/docs/pilot-20261105/operations/external-acceptance/SOURCE-PASS.json) و[RESTORE-PASS](https://github.com/merapplications-sketch/Talabat-v3/blob/a7d011dc54a7e129f882ad263b34f21d352521f8/docs/pilot-20261105/operations/external-acceptance/RESTORE-PASS.json).
المصدر 6216cb570375705a764ed488c4ffd0f0dbec5c41 ؛ [تشغيل 42111418834](https://github.com/merapplications-sketch/Talabat-v3/actions/runs/42111418834)، sourcejob127539660970 و restorejob127539660599 ، artifact13455151933. هذه روابط تاريخية؛ لم يُنزّل artifact أو يُعدالتشغيل.
- pass=true/live=false/synthetic_only=true. تفريغ PostgreSQL وملف Storage فعلي شُفّرا؛ source_job_completed_before_download=true ؛ هوية kernelboot مستقلة.
- الدليل يسجلتطابق 62 جدولاً والدوال والمنح والسياسات والتريغرات/RLS ؛ مطابقةبايتات Storage للمخول ورفضغيرالمرتبط والحزمةالتالفة.
- الفهرس يحفظ 3 محاولاتاستعادةفاشلة سابقة و 37 فرقتمثيل ACL معالتطابق الدلالي؛ لا نخفيالفشل. كود HTTP الرفضالتفصيليغيرمصدر؛ ليستمصفوفةأدواركاملة.
- key_exported=false و production_rpo_rto_accepted=false ؛ 82.45 ثانية و 44.827 ثانية مقاييسالتمرينفقط. لاجدولةنسخدائمة أوحيازةمفتاحتشغيلي أوقبول RPO/RTO.
- FINAL-READINESS/ACCESS-REQUEST و RESOURCE-AVAILABILITY مؤرخة 6 نوفمبر؛ لا تنقلقائمةمواردها كفحصحالي ولا شروطهاالتجاريةالقديمة مكانأجوبةالمالكالحالية.

## 4. القبول المحفوظ ونقطة الاستئناف
[إيصال CI106](https://github.com/merapplications-sketch/Talabat-v3/blob/fb88868d798e4b08f1f1f0f91dd7be9458d1816b/docs/continuity/evidence/20261112-ci106-build-gate/retrieval-receipt.json) وأرشيفهالمحفوظ مرجعالحفظ؛ لا إعادةاختبارأو hash. PRICE/RATINGS/TIP والمراقب و 106 لمتتغير.
ALERT-01..06 و DEV-01..06/PRINT-01..02 في [REMAINING-CHECKS](https://github.com/merapplications-sketch/Talabat-v3/blob/a7d011dc54a7e129f882ad263b34f21d352521f8/docs/pilot-20261105/operations/alert-repair/REMAINING-CHECKS.md) تبقىنطاقالقبولاللاحق؛ لاخطةموازيةأوتنفيذ. Q36=180 ثانيةلأولكاش، Q39=10 دقائقلغيابالزبون؛ ليستا SLO للتنبيه. عقد MEASUREMENT-CONTRACT محفوظ، لا ضغطأوهدفعدديجديد.

| البوابة | أثرالاستكمال | الحالة |
|---|---|---|
|G1-A|هويةنشر 35/58 أوضح؛ أصل 35 محجوبوالفعّالغيرمثبت|PARTIAL/BLOCKED|
|G1-B|حدود dispatch/watchdog وغياب schedule داخل 19workflow فقط|PARTIAL/BLOCKED|
|G1-C|لاإعداد/oracle جديد؛ القراراتوقبولالمصدرمحفوظة|PARTIAL/BLOCKED|
|G1-D|معمل Auth/REST ليس trace للطلبالفعلي|BLOCKED|
|G1-E|حدالأثرالخارجيوبيانمفتاحالتمرينأوضح؛ حيازة/مصالحةتشغيليةناقصة|PARTIAL/BLOCKED|
|G1-F|أصلالتعافيالاصطناعي و CI106 مربوطان؛ القنواتوالنسخالتشغيليةناقصة|PARTIAL/BLOCKED|

نقطةالاستئناف: المستشاريراجع هذهالدلتا مع a7d011dc فقط؛ حائزمستودع Sites يتيح أصل 35 المثبت، وحائزوالموارديسلمونالأصولالمسماةأعلاه. لا مهمةجديدة ولاتكراربحثفيالمصادرنفسهادونإتاحةجديدة. لا إعلانإغلاق G1 أو READY. PHASE1 PARTIAL/BLOCKED ؛ PHASE2 NO-GO.
هذهالدفعةتوثيقفقط: لاتعديلمصدر/اختبارات/CI ، لا SQL مستضافأونشرأودمجأوصلاحياتأومال، لاضغطأواستعادة، ولاطلبات#1/#2/#3 أومستحق#3.
