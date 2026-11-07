# UI checkpoint 2026-11-07

Order #2 / TS-000000000002 is complete, unchanged, not reopened or re-settled. #1 unchanged. No new order created.

Map defect affected shipped source: no-referrer HTML prevented required OSM Referer. Scoped fix sets Leaflet tile-image referrerPolicy:'origin' at three map call sites, preserving document no-referrer and excluding page paths/query. Same provider/cache/security. Regression failed before and passed after, JS syntax passed.

Published isolated Site v12, pilot-mobile-20261107.4, source 221ded4a23e213ba564becd78c9bb85e16ad6de2, deployment appgdep_6aeec10ceeb88191a64dd5dd43488dad succeeded. Customer location picker visibly rendered Dushanbe map; DOM confirmed tile complete,width256,referrerPolicy origin. No address saved. Physical Safari not tested; OSM service remains best effort. Internal routing unchanged.

Fresh customer password login succeeded. Earlier merchant/driver/admin/accountant UI successes preserved. No credential reset.

Proof bucket private. INSERT requires assigned authenticated driver while pickedup. SELECT permits assigned folder owner, admin/orders permission, or related customer. Finance-only permission does not grant proof access. Upload, recipient display and unauthorized byte denial remain NOT proven on deployed UI.
Chat INSERT restricted to assigned driver/customer during preparing/ready/pickedup. Orders #1 and #2 are closed. Publication includes orders,order_chat,order_offers. Customer notification panel opened, no new notifications. No new-event or audible-sound verification claimed.

Automatic review rejected a proposed separate zero-value noncash active test fixture because prior user instruction forbids alternative orders. No mutation occurred and no workaround attempted. Need explicit authorization for one separate synthetic active fixture using existing test accounts, no cash or settlement, solely for proof, chat and open-app live events. Do not reopen #2.

Automatic review also rejected copying full GitHub app files because original branch contains production connection settings. Left those files unchanged. Store isolated patch as documentation only; applied code lives in Site source above. Test database fsvrsvqfknogwmhccera only, no production change.

Routes: https://talabot-isolated-safari-20261106.alwarikahtan.chatgpt.site/customer ; /merchant ; /driver ; /admin (also accountant).
