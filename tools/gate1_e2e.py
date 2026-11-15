#!/usr/bin/env python3
"""TALABOT Gate1 fail-closed E2E gate, not a simulated integration test.
Requires verified, independent new talabot-test project and real request fixtures.
"""
import os
import sys
from urllib.parse import urlparse

CASES = [
 ("G1-E01","C-11/C-14/B-04","customer cash order"),
 ("G1-E02","B-07/C-15","merchant accepts order"),
 ("G1-E03","D-02/D-07","driver server-ACK online"),
 ("G1-E04","D-03","driver accepts offer"),
 ("G1-E05","D-06","pickup"),
 ("G1-E06","D-08/D-09","exact cash delivery"),
 ("G1-E07","D-10/D-14/B-07/B-10","two sessions and post-COMMIT replay one financial/receipt effect"),
 ("G1-E08","D-08/B-07","underpaid cash blocked, support report"),
 ("G1-E09","D-11","chat insert success/failure/reload"),
 ("G1-E10","C-16","tracking status"),
 ("G1-E11","B-03/D-01","cross-account and unassigned-order RLS denial"),
]
DENIED = {"dzydscryrnahnneydnry", "fsvrsvqfknogwmhccera", "sbzcokatkhxsijsfplit"}
url = os.environ.get("SUPABASE_TEST_URL", "").strip()
host = urlparse(url).hostname or ""
ref = host.split(".")[0]
keys = all(os.environ.get(k) for k in (
    "SUPABASE_TEST_ANON_KEY", "SUPABASE_TEST_SERVICE_ROLE_KEY"))
safe_project = (os.environ.get("SUPABASE_TEST_PROJECT_NAME") == "talabot-test"
                and ref and ref not in DENIED and host == ref + ".supabase.co"
                and urlparse(url).scheme == "https")
reason = ("independent talabot-test and test-only credentials are absent"
          if not (safe_project and keys)
          else "authenticated 11-case test fixture/runner is not provisioned; do not invent E2E PASS")
for case_id, legacy, label in CASES:
    print("BLOCKED {} [{}] {}: {}".format(case_id, legacy, label, reason), flush=True)
print("GATE1_E2E: 0/11 PASS, 11 BLOCKED; no HTTP/SQL request issued",file=sys.stderr)
sys.exit(2)
