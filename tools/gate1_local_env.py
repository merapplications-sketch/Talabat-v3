#!/usr/bin/env python3
"""Parse only SUPABASE LOCAL CLI status output and export ephemeral CI-only settings. No remote account access."""
import os
import pathlib
import sys
import urllib.parse

def fail(reason):
    print("BLOCKED Gate1 LOCAL ENV: " + reason, file=sys.stderr)
    raise SystemExit(3)

if __name__ == "__main__":
    if len(sys.argv) != 2: fail("local status file path required")
    p = pathlib.Path(sys.argv[1])
    if not p.is_file(): fail("Supabase LOCAL status output missing")
    values = {}
    for line in p.read_text("utf-8").splitlines():
        k, eq, v = line.partition("=")
        if eq and k.strip() in ("API_URL", "ANON_KEY", "SERVICE_ROLE_KEY"):
            values[k.strip()] = v.strip().strip('"').strip("'")
    url = values.get("API_URL", "").rstrip("/")
    parsed = urllib.parse.urlsplit(url)
    if url != "http://127.0.0.1:54321" or parsed.hostname != "127.0.0.1" or parsed.port != 54321:
        fail("refusing non-loopback Supabase status origin")
    keys = (values.get("ANON_KEY"), values.get("SERVICE_ROLE_KEY"))
    if any(not val or len(val) < 32 or "\n" in val for val in keys):
        fail("local auth keys absent or malformed")
    envpath = os.environ.get("GITHUB_ENV")
    tmp = os.environ.get("RUNNER_TEMP")
    if not envpath or not tmp: fail("GitHub ephemeral runner paths missing")
    for secret in keys:
        print("::add-mask::" + secret)
    with open(envpath, "a", encoding="utf-8") as f:
        f.write("SUPABASE_LOCAL_URL=http://127.0.0.1:54321\n")
        f.write("SUPABASE_LOCAL_ANON_KEY=" + keys[0] + "\n")
        f.write("SUPABASE_LOCAL_SERVICE_ROLE_KEY=" + keys[1] + "\n")
        f.write("GATE1_TEST_FIXTURE_PATH=" + str(pathlib.Path(tmp) / "gate1-fixture.json") + "\n")
    print("PASS Gate1: local-only API origin and ephemeral keys exported; no cloud keys requested")
