# v47 — promo guessing limit, robust version (patch 30)

The owner re-ran security-check after v46: still "13 wrong codes were not blocked".

Patch 28 counted a wrong code only when the old (unknown, pre-patch-17) check answered exactly
"promo_invalid". If it answers differently (another error word, or an error raised instead of an answer),
nothing was counted. Patch 30 flips the rule: every answer that is not a success is a wrong guess, except
answers that prove the code is real (promo_min / used / limit / offer / expired) or that are not about the code
(closed, unavailable ...). Errors are always answered (never thrown), so the counted attempt is kept.
Works whether patch 28/29 were run or not; safe to run again.

Tests: sql/test_patch30.sql (empty PostgreSQL 16) against 3 possible old behaviours + "after patch 28": 20/20.
test_patch29 (with patch 30 after it) 40/40, test_patch28 15/15.

security-check.html (build SC-47): new row "Promo guard (patch 30) is installed"; the promo row now shows the
server's last answer when it fails, so the cause is visible from the phone.
