#!/usr/bin/env python3
"""TALABOT BRIEF-19 SEC-18: real PostgreSQL auth, ACL, RLS, rollback QA.
Uses ONLY the disposable Supabase Docker DB from Gate1 at 127.0.0.1.
Never contacts a remote endpoint or commits credentials / synthetic records.
"""
import hashlib
import json
import os
from pathlib import Path
import re
import subprocess
import sys

ROOT = Path(__file__).resolve().parents[1]
PROJECT = "talabot-gate1-local"
CONTAINER = "supabase_db_" + PROJECT
MIGRATION = ROOT / "sql/proposed/brief18_delivery_instructions.sql"
ROLLBACK = ROOT / "sql/proposed/brief18_delivery_instructions_rollback.sql"
BASELINE = ROOT / "sql/baseline/schema_baseline_dzydscryrnahnneydnry_20261116.sql"
passed = []

def check(ok, why):
    if not ok:
        raise AssertionError(why)

def preflight():
    check(os.environ.get("BRIEF19_SEC18_LOCAL") == "1", "explicit BRIEF19 opt-in missing")
    check(os.environ.get("SUPABASE_LOCAL_URL") == "http://127.0.0.1:54321",
          "only the exact disposable local Supabase origin is authorized")
    for name in ("DATABASE_URL", "SUPABASE_PROJECT_REF", "SUPABASE_DB_PASSWORD", "SUPABASE_ACCESS_TOKEN"):
        check(not os.environ.get(name), "remote database credentials prohibited: " + name)
    check(os.environ.get("GATE1_SCHEMA_SHA256") == hashlib.sha256(BASELINE.read_bytes()).hexdigest(),
          "pinned schema baseline checksum mismatch")
    fixture_path = Path(os.environ.get("GATE1_TEST_FIXTURE_PATH", ""))
    check(fixture_path.is_absolute() and fixture_path.is_file()
          and str(fixture_path.parent) == os.environ.get("RUNNER_TEMP"),
          "Gate1 synthetic fixture must be inside ephemeral RUNNER_TEMP")
    data = json.loads(fixture_path.read_text("utf-8"))
    check(data.get("project_name") == PROJECT and data.get("synthetic_only") is True
          and data.get("origin") == "http://127.0.0.1:54321"
          and data.get("baseline_sha256") == os.environ["GATE1_SCHEMA_SHA256"], "foreign fixture")
    names = subprocess.run(["docker", "ps", "--format", "{{.Names}}"],
                           text=True, capture_output=True, check=True, timeout=15).stdout.splitlines()
    check(CONTAINER in names, "expected disposable LOCAL Postgres Docker container missing")
    for key in ("customer", "outsider", "driver", "other_driver"):
        uid = data["roles"][key]["id"]
        check(re.fullmatch(r"[0-9a-fA-F-]{36}", uid) is not None, "invalid local UUID")
    check(re.fullmatch(r"[0-9a-fA-F-]{36}", data["store_id"]) is not None, "invalid local store")
    return data

def psql(query, *, expect_error=None):
    cmd = ["docker", "exec", "-i", CONTAINER, "psql", "-X", "-q", "-A", "-t",
           "-v", "ON_ERROR_STOP=1", "-U", "postgres", "-d", "postgres"]
    out = subprocess.run(cmd, input=query, text=True, capture_output=True, timeout=90)
    if expect_error:
        check(out.returncode != 0 and expect_error.lower() in out.stderr.lower(),
              "EXPECTED_DENIAL " + expect_error + " rc=" + str(out.returncode)
              + " error=" + out.stderr[:500])
    else:
        check(out.returncode == 0, "PSQL_FAILED: " + out.stderr[:900])
    return [line.strip() for line in out.stdout.splitlines() if line.strip()]

def scalar(query):
    rows = psql(query)
    check(len(rows) == 1, "expected exactly one scalar, got " + str(rows))
    return rows[0]

def as_actor(uid, role, query, *, expect_error=None):
    check(role in ("authenticated", "anon"), "unexpected test DB role")
    check(re.fullmatch(r"[0-9a-fA-F-]{36}", uid) is not None or uid == "", "unsafe actor UUID")
    session = ("BEGIN;\nSET LOCAL ROLE " + role + ";\n"
               "SELECT pg_catalog.set_config('request.jwt.claim.sub','" + uid + "',true);\n"
               + query.rstrip().rstrip(";") + ";\nCOMMIT;\n")
    return psql(session, expect_error=expect_error)

def record(name, ok=True):
    check(ok, name + " failed")
    passed.append(name)
    print("PASS BRIEF19_SEC18 " + name, flush=True)

def snapshot_orders():
    return scalar("""SELECT count(*)::text || ':' ||
       md5(coalesce(string_agg(md5(to_jsonb(o)::text),'' ORDER BY o.id),''))
       FROM public.orders o;""")

def rights_check():
    # has_*_privilege on real LOCAL roles plus raw PUBLIC ACL. PUBLIC is not itself a SQL login role.
    sql = """SELECT (
      (SELECT relrowsecurity FROM pg_catalog.pg_class WHERE oid='public.order_delivery_instructions'::regclass)
      AND NOT has_table_privilege('anon','public.order_delivery_instructions','SELECT,INSERT,UPDATE,DELETE')
      AND NOT has_table_privilege('authenticated','public.order_delivery_instructions','SELECT,INSERT,UPDATE,DELETE')
      AND NOT has_function_privilege('anon','public.delivery_instructions_ready()','EXECUTE')
      AND NOT has_function_privilege('anon','public.set_order_delivery_instructions(bigint,text[])','EXECUTE')
      AND NOT has_function_privilege('anon','public.get_order_delivery_instructions(bigint)','EXECUTE')
      AND has_function_privilege('authenticated','public.delivery_instructions_ready()','EXECUTE')
      AND has_function_privilege('authenticated','public.set_order_delivery_instructions(bigint,text[])','EXECUTE')
      AND has_function_privilege('authenticated','public.get_order_delivery_instructions(bigint)','EXECUTE')
      AND NOT EXISTS (
        SELECT 1 FROM pg_catalog.pg_class c,
        LATERAL pg_catalog.aclexplode(coalesce(c.relacl,pg_catalog.acldefault('r',c.relowner))) a
        WHERE c.oid='public.order_delivery_instructions'::regclass AND a.grantee=0)
      AND NOT EXISTS (
        SELECT 1 FROM pg_catalog.pg_proc p,
        LATERAL pg_catalog.aclexplode(coalesce(p.proacl,pg_catalog.acldefault('f',p.proowner))) a
        WHERE p.oid IN ('public.delivery_instructions_ready()'::regprocedure,
                        'public.set_order_delivery_instructions(bigint,text[])'::regprocedure,
                        'public.get_order_delivery_instructions(bigint)'::regprocedure)
        AND a.grantee=0)
    )::text;"""
    check(scalar(sql) == "true", "real Postgres ACL/RLS checks failed")

def run():
    f = preflight()
    roles = f["roles"]
    cust, outsider, driver, other = [roles[r]["id"] for r in ("customer","outsider","driver","other_driver")]
    # Staged sequence is baseline -> Gate1 -> BRIEF18 in an ephemeral LOCAL Supabase.
    check(scalar("SELECT (to_regclass('public.order_delivery_instructions') IS NOT NULL)::text;") == "true",
          "SEC18 migration was not staged/applied to LOCAL database")
    rights_check()
    record("S05_RLS_ACL_ANON_AUTHENTICATED_PUBLIC")

    oid_s = scalar("""INSERT INTO public.orders
         (store_id,customer_id,driver_id,status,payment,address,subtotal,delivery_fee,total)
         VALUES ('""" + f["store_id"] + """'::uuid,'""" + cust + """'::uuid,'"""
         + driver + """'::uuid,'ready','cash','SYNTHETIC SEC18 LOCAL',50,10,60)
         RETURNING id;""")
    check(oid_s.isdigit(), "failed to make an ephemeral test order")
    oid = int(oid_s)
    keyset = "ARRAY['door','call']::text[]"
    set_call = "SELECT public.set_order_delivery_instructions(" + str(oid) + "," + keyset + ")"
    read_call = "SELECT public.get_order_delivery_instructions(" + str(oid) + ")::text"

    check(as_actor(cust,"authenticated","SELECT auth.uid()::text")[-1] == cust,
          "real local auth.uid() did not resolve the customer JWT identity")
    record("S05_REAL_JWT_ROLE_CONTEXT")
    check(as_actor(cust,"authenticated",set_call)[-1] == "t", "customer did not write")
    check(as_actor(cust,"authenticated",read_call)[-1] == "{door,call}", "customer read mismatch")
    check(as_actor(driver,"authenticated",read_call)[-1] == "{door,call}", "approved assigned driver cannot read")
    record("S05_POSITIVE_CUSTOMER_WRITE_ASSIGNED_DRIVER_READ")

    stamp = scalar("SELECT updated_at::text FROM public.order_delivery_instructions WHERE order_id=" + str(oid))
    psql("SELECT pg_sleep(0.12);")
    check(as_actor(cust,"authenticated",set_call)[-1] == "t", "identical request rejected")
    check(scalar("SELECT updated_at::text FROM public.order_delivery_instructions WHERE order_id="
                 + str(oid)) == stamp, "identical payload changed updated_at")
    record("S04_IDENTICAL_NOOP_TIMESTAMP")

    as_actor(outsider,"authenticated",set_call,expect_error="forbidden")
    as_actor(outsider,"authenticated",read_call,expect_error="forbidden")
    record("S05_OTHER_CUSTOMER_DENIED")
    as_actor(other,"authenticated",read_call,expect_error="forbidden")
    record("S02_S05_OTHER_DRIVER_DENIED")
    as_actor(cust,"authenticated","SELECT public.set_order_delivery_instructions("
             + str(oid) + ",ARRAY['external']::text[])",expect_error="bad_value")
    record("S05_INVALID_KEY_DENIED")
    as_actor(cust,"authenticated","SELECT public.set_order_delivery_instructions("
             + str(oid) + ",ARRAY['door','door']::text[])",expect_error="bad_value")
    record("S05_DUPLICATE_KEYS_DENIED")
    as_actor("","anon",set_call,expect_error="permission denied")
    as_actor("","anon",read_call,expect_error="permission denied")
    as_actor("","anon","SELECT public.delivery_instructions_ready()",expect_error="permission denied")
    record("S05_ANON_ALL_RPC_DENIED")

    # A customer-profile UUID forged into orders.driver_id must never grant driver-specific reads.
    psql("UPDATE public.orders SET driver_id='" + outsider + "'::uuid WHERE id=" + str(oid))
    try:
        as_actor(outsider,"authenticated",read_call,expect_error="forbidden")
        record("S02_NON_DRIVER_ASSIGNED_DENIED")
    finally:
        psql("UPDATE public.orders SET driver_id='" + driver + "'::uuid WHERE id=" + str(oid))
    psql("UPDATE public.profiles SET driver_status='suspended' WHERE id='" + driver + "'::uuid")
    try:
        as_actor(driver,"authenticated",read_call,expect_error="forbidden")
        record("S02_SUSPENDED_DRIVER_DENIED")
    finally:
        psql("UPDATE public.profiles SET driver_status='approved' WHERE id='" + driver + "'::uuid")

    psql("UPDATE public.orders SET status='pickedup' WHERE id=" + str(oid))
    as_actor(cust,"authenticated","SELECT public.set_order_delivery_instructions("
             + str(oid) + ",ARRAY['meet']::text[])",expect_error="forbidden")
    check(scalar("SELECT instruction_keys::text FROM public.order_delivery_instructions WHERE order_id="
                 + str(oid)) == "{door,call}", "pickedup write overwrote stored instructions")
    record("S01_PICKEDUP_WRITE_DENIED_CONTENT_PRESERVED")

    # An equal existing table may be safely re-verified. Incompatible pre-existing tables fail closed.
    psql(MIGRATION.read_text("utf-8"))
    rights_check()
    record("S03_IDEMPOTENT_PREFLIGHT_MATCHING_SCHEMA")
    psql("BEGIN; ALTER TABLE public.order_delivery_instructions ADD COLUMN sec18_rogue integer;\n"
         + MIGRATION.read_text("utf-8"),expect_error="BRIEF19_PREFLIGHT_INCOMPATIBLE")
    check(scalar("""SELECT count(*)::text FROM pg_catalog.pg_attribute
          WHERE attrelid='public.order_delivery_instructions'::regclass
            AND attname='sec18_rogue' AND NOT attisdropped;""") == "0",
          "failed incompatible migration left an unexpected schema change")
    record("S03_INCOMPATIBLE_SCHEMA_FAILS_AT_PREFLIGHT")

    before = snapshot_orders()
    rows = scalar("SELECT count(*)::text FROM public.order_delivery_instructions WHERE order_id=" + str(oid))
    check(rows == "1", "instruction record absent before rollback")
    psql(ROLLBACK.read_text("utf-8"))
    check(snapshot_orders() == before, "rollback mutated orders count or row fingerprint")
    check(scalar("SELECT count(*)::text FROM public.order_delivery_instructions WHERE order_id="
                 + str(oid)) == rows, "rollback deleted instruction record")
    check(scalar("""SELECT (
      to_regprocedure('public.set_order_delivery_instructions(bigint,text[])') IS NULL
      AND to_regprocedure('public.get_order_delivery_instructions(bigint)') IS NULL
      AND to_regprocedure('public.delivery_instructions_ready()') IS NULL
      )::text;""") == "true", "rollback failed to remove SEC18 functions")
    record("S03_ROLLBACK_FUNCTIONS_ONLY_ORDERS_HASH_AND_DATA_RETAINED")
    record("S05_NONDESTRUCTIVE_LOCAL_MIGRATE_TEST_ROLLBACK")
    print("BRIEF19_SEC18_LOCAL_PASS " + str(len(passed)) + "/" + str(len(passed)), flush=True)

if __name__ == "__main__":
    try:
        run()
    except Exception as exc:
        print("BRIEF19_SEC18_LOCAL_NO_GO: " + str(exc), file=sys.stderr)
        raise SystemExit(1)
