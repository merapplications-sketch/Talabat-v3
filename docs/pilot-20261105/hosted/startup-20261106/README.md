# Startup failure correction — pilot-mobile-20261106.2

Proven defect: parser-blocking external Supabase SDK preceded all startup timeouts. Holding that request left all four apps completely blank after17s. This is a reproducible code defect, not proof of the cause on the owner's iPhone.

Fix: vendor the exact pinned2.117.2 SDK with MIT license on the same origin; render an inline early startup message and15s watchdog before external scripts; bound Auth and GET fetches at15s, honoring cancellation. Financial writes are not timed out or retried by this wrapper. CSP, role storage keys, financial logic, production target and existing deployments unchanged.

Affected tests: all4 stalled core loads show localized error+reload; stalled Auth request shows Russian connection error and reenables login. No previous successful mobile/finance tests rerun.

Cloudflare: API reports successful deployment; account zones=[]; pages.dev security is not a configurable owned zone here. Python HTTP got403/code1010, while real Chromium and cloud-browser page loads succeed. No evidence ties that client-specific rejection to owner's Safari. No fingerprint bypass or protection disabled. If main HTML is unreachable, application JavaScript cannot render an error; that boundary remains distinct from startup/API failure.

Hosted release verification follows after deployment. Existing admission remains paused pending Storage/Realtime confirmation. No claim of full hosted order acceptance.
