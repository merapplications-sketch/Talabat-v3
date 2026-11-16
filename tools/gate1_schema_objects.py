#!/usr/bin/env python3
"""TALABOT Gate1: capture only approved PostgreSQL catalog object definitions; compare fail-closed.

Uses psql with inherited PGHOST/PGUSER/PGPASSWORD/PGSSLMODE, never prints credentials or table rows.
"""
import hashlib
import json
import os
import pathlib
import subprocess
import sys

ROOT = pathlib.Path(__file__).resolve().parents[1]
QUERY = ROOT / "tools" / "gate1_schema_objects.sql"

def fail(message):
    print("GATE1_SCHEMA_STOP: " + message, file=sys.stderr)
    raise SystemExit(3)

def capture(output):
    if not QUERY.is_file():
        fail("schema-only catalog query missing")
    proc = subprocess.run(
        ["psql", "-X", "-A", "-t", "-q", "-v", "ON_ERROR_STOP=1", "-f", str(QUERY)],
        capture_output=True, text=True, timeout=50,
    )
    if proc.returncode != 0:
        # Do not log psql stderr (it might contain remote host/account information).
        fail("catalog read/query failed; psql exit code " + str(proc.returncode))
    try:
        document = json.loads(proc.stdout.strip())
        assert set(document) == {"functions", "indexes"}
        assert set(document["functions"]) == {"driver_ping","deliver_order","report_driver_cash_short"}
        assert set(document["indexes"]) == {"tickets_one_open_per_order","tickets_one_open_payment_per_order"}
    except (ValueError, AssertionError, KeyError, TypeError):
        fail("schema-only JSON result malformed")
    output = pathlib.Path(output)
    output.parent.mkdir(parents=True, exist_ok=True)
    output.write_text(json.dumps(document,ensure_ascii=False,sort_keys=True,indent=2)+"\n",encoding="utf-8")
    print("GATE1_CATALOG_READ_OK: "+str(output.name)+" SHA256="+hashlib.sha256(json.dumps(document,sort_keys=True).encode()).hexdigest())

def compare(expected_path,actual_path):
    expected=json.loads(pathlib.Path(expected_path).read_text(encoding="utf-8"))
    actual=json.loads(pathlib.Path(actual_path).read_text(encoding="utf-8"))
    if expected != actual:
        for group in ("functions","indexes"):
            for name in sorted(set(expected[group])|set(actual[group])):
                if expected[group].get(name)!=actual[group].get(name):
                    print("GATE1_SCHEMA_DIFFERENCE: "+group+"/"+name, file=sys.stderr)
        fail("catalog objects do NOT match exact pinned schema; no write permitted")
    print("ROLLBACK_restores_baseline / PRE_POST_MATCH: "+str(actual_path))

if __name__ == "__main__":
    if len(sys.argv)==3 and sys.argv[1]=="capture":
        capture(sys.argv[2])
    elif len(sys.argv)==4 and sys.argv[1]=="compare":
        compare(sys.argv[2],sys.argv[3])
    else:
        fail("usage: capture PATH | compare EXPECTED ACTUAL")
