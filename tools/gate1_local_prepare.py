#!/usr/bin/env python3
"""Gate1: local-only schema integrity and migration staging. No DB/network access."""
import datetime
import hashlib
import json
import os
import pathlib
import re
import shutil
import sys

ROOT = pathlib.Path(__file__).resolve().parents[1]
REF = "dzydscryrnahnneydnry"
BASE = ROOT / "sql" / "baseline" / f"schema_baseline_{REF}_20261116.sql"
MANIFEST = ROOT / "sql" / "baseline" / f"schema_baseline_{REF}_20261116.json"
PROPOSED = ROOT / "sql" / "proposed" / "gate1_cash_and_idempotent_delivery.sql"


def fail(reason):
    print("BLOCKED Gate1 LOCAL CI: " + reason + "; NO DATABASE OR NETWORK CALLED", flush=True)
    raise SystemExit(3)


def run():
    for name in ("SUPABASE_ACCESS_TOKEN", "SUPABASE_DB_PASSWORD", "SUPABASE_PROJECT_REF", "DATABASE_URL"):
        if os.environ.get(name):
            fail("remote-link credential/env " + name + " is prohibited in isolated CI")
    if not BASE.is_file() or not MANIFEST.is_file():
        fail("authentic schema-only production baseline and extraction manifest absent")
    try:
        m = json.loads(MANIFEST.read_text("utf-8"))
        sql = BASE.read_bytes()
    except Exception:
        fail("baseline/manifest unreadable")
    digest = hashlib.sha256(sql).hexdigest()
    if m.get("source_ref") != REF or m.get("schema_only") is not True or m.get("sha256") != digest:
        fail("schema origin, schema-only declaration or SHA256 integrity mismatch")
    if not isinstance(m.get("patches17_34_included"), bool):
        fail("baseline patch17-34 inclusion status not explicitly verified")
    try:
        stamp = datetime.datetime.fromisoformat(m["extracted_utc"].replace("Z", "+00:00"))
        if stamp.tzinfo is None:
            raise ValueError("missing timezone")
    except (ValueError, TypeError, KeyError):
        fail("schema extraction timestamp missing or invalid")
    src = sql.decode("utf-8")
    if len(src) < 4096 or not re.search(r"(?im)^\s*(?:CREATE TABLE|CREATE FUNCTION|CREATE OR REPLACE FUNCTION)\s+", src):
        fail("incomplete/placeholder schema; cannot construct test database")
    if re.search(r"(?im)^\s*(?:COPY\s+.*?\s+FROM\s+stdin|INSERT\s+INTO\s+auth\.users)\b", src):
        fail("baseline appears to include row data (never allowed)")
    if not PROPOSED.is_file():
        fail("pinned Gate1 proposed SQL missing")
    staging = ROOT / "supabase"
    migrations = staging / "migrations"
    migrations.mkdir(parents=True, exist_ok=True)
    config = staging / "config.toml"
    if config.exists():
        fail("unreviewed Supabase config already present; no destructive overwrite")
    config.write_text(
        'project_id = "talabot-gate1-local"\n[api]\nenabled = true\nport = 54321\n'
        '[db]\nport = 54322\nmajor_version = 17\n[studio]\nenabled = false\n',
        encoding="utf-8",
    )
    shutil.copyfile(BASE, migrations / "20261116000100_baseline.sql")
    if m["patches17_34_included"] is False:
        for n in range(17, 35):
            patch = ROOT / "sql" / ("schema_patch%d.sql" % n)
            if not patch.is_file():
                fail("missing source patch%d: no stack start" % n)
            shutil.copyfile(patch, migrations / ("%014d_patch%02d.sql" % (20261116000100 + n, n)))
    shutil.copyfile(PROPOSED, migrations / "20261116000900_gate1_proposed.sql")
    print("PASS Gate1 baseline integrity: SHA256 " + digest + "; migrations staged LOCALLY", flush=True)
    envfile = os.environ.get("GITHUB_ENV")
    if envfile:
        with open(envfile, "a", encoding="utf-8") as f:
            f.write("GATE1_SCHEMA_SHA256=" + digest + "\n")


if __name__ == "__main__":
    run()
