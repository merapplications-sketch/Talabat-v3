#!/usr/bin/env python3
"""Gate1 test-only fixture. Creates five synthetic users and orders ONLY on local Supabase at 127.0.0.1.
No production, cloud ref, real account, external redirect, or shared credentials.
All secrets and fixture output remain in ephemeral RUNNER_TEMP, never the repository or logs.
"""
import datetime
import hashlib
import json
import os
import pathlib
import secrets
import sys
import urllib.error
import urllib.parse
import urllib.request
import uuid

ORIGIN = "http://127.0.0.1:54321"
ROLES = ("customer", "merchant", "driver", "outsider", "other_driver")
ROOT = pathlib.Path(__file__).resolve().parents[1]
BASELINE = ROOT / "sql" / "baseline" / "schema_baseline_dzydscryrnahnneydnry_20261116.sql"


def blocked(reason):
    print("BLOCKED GATE1 local-only fixture: " + reason, file=sys.stderr)
    raise SystemExit(3)


class NoRedirect(urllib.request.HTTPRedirectHandler):
    def redirect_request(self, *args, **kwargs):
        raise RuntimeError("any redirect is denied in local-only fixture")


CLIENT = urllib.request.build_opener(urllib.request.ProxyHandler({}), NoRedirect())


def call(method, route, key, data=None, prefer=None):
    if not route.startswith("/") or ".." in route or "://" in route:
        raise RuntimeError("invalid local-only URL route")
    url = ORIGIN + route
    url_parts = urllib.parse.urlsplit(url)
    if url_parts.scheme != "http" or url_parts.hostname != "127.0.0.1" or url_parts.port != 54321:
        raise RuntimeError("LOCAL ORIGIN GATE FAILED")
    headers = {"apikey": key, "Authorization": "Bearer " + key, "Accept": "application/json"}
    if data is not None:
        headers["Content-Type"] = "application/json"
    if prefer:
        headers["Prefer"] = prefer
    body = None if data is None else json.dumps(data, separators=(",", ":")).encode("utf-8")
    request = urllib.request.Request(url, headers=headers, data=body, method=method)
    try:
        with CLIENT.open(request, timeout=20) as response:
            raw = response.read(2_000_000)
            return response.status, json.loads(raw) if raw.strip() else None
    except urllib.error.HTTPError as e:
        # Only PostgREST error codes are logged, never body/credentials/identity.
        try:
            code = json.loads(e.read(1500)).get("code", "unknown")
            if not isinstance(code, str) or len(code) > 25 or not code.replace("_", "").isalnum():
                code = "unknown"
        except Exception:
            code = "unknown"
        raise RuntimeError("local API " + route.split("?")[0] + " HTTP " + str(e.code) + " code=" + code) from None


def require_success(code, value, subject):
    if not 200 <= code < 300:
        raise RuntimeError("local " + subject + " request returned HTTP " + str(code))
    return value


def main():
    if os.environ.get("SUPABASE_LOCAL_URL") != ORIGIN:
        blocked("SUPABASE_LOCAL_URL is not literal loopback")
    keys = ("SUPABASE_LOCAL_ANON_KEY", "SUPABASE_LOCAL_SERVICE_ROLE_KEY", "GATE1_TEST_FIXTURE_PATH", "GATE1_SCHEMA_SHA256", "RUNNER_TEMP")
    missing = [x for x in keys if not os.environ.get(x)]
    if missing:
        blocked("required local-only ephemeral runtime variables missing: " + ", ".join(missing))
    if any(os.environ.get(k) for k in ("SUPABASE_ACCESS_TOKEN", "SUPABASE_DB_PASSWORD", "DATABASE_URL", "SUPABASE_PROJECT_REF")):
        blocked("remote Supabase credentials detected; refusing test seed")
    ref = "dzydscryrnahnneydnry"
    schema_sha = hashlib.sha256(BASELINE.read_bytes()).hexdigest()
    if schema_sha != os.environ["GATE1_SCHEMA_SHA256"]:
        blocked("schema baseline SHA256 mismatch")
    schema = BASELINE.read_text("utf-8")
    confirmed_cashback = all(x in schema for x in (
        'CREATE TABLE IF NOT EXISTS "public"."wallet_entries"',
        'CREATE UNIQUE INDEX "wallet_one_cashback_per_order"',
        'CREATE OR REPLACE FUNCTION "public"."trg_loyalty"',
        'CREATE OR REPLACE TRIGGER "trg_orders_loyalty"'))
    fixture_path = pathlib.Path(os.environ["GATE1_TEST_FIXTURE_PATH"])
    runner = pathlib.Path(os.environ["RUNNER_TEMP"])
    if not fixture_path.is_absolute() or fixture_path.parent != runner or ROOT in fixture_path.parents:
        blocked("fixture must be located directly within ephemeral RUNNER_TEMP")
    anon = os.environ["SUPABASE_LOCAL_ANON_KEY"]
    service = os.environ["SUPABASE_LOCAL_SERVICE_ROLE_KEY"]
    prefix = "gate1-" + secrets.token_hex(8)
    profiles = {}
    for number, role in enumerate(ROLES, 1):
        email = prefix + "-" + role + "@example.invalid"
        password = "Gate1!" + secrets.token_urlsafe(24)
        _, created = call("POST", "/auth/v1/admin/users", service,
                          {"email": email, "password": password, "email_confirm": True})
        if not isinstance(created, dict) or not created.get("id"):
            blocked("LOCAL Auth did not create a test identity")
        _, logged = call("POST", "/auth/v1/token?grant_type=password", anon,
                         {"email": email, "password": password})
        if not isinstance(logged, dict) or not logged.get("access_token"):
            blocked("LOCAL Auth did not issue a test session")
        # H-01: actual LOCAL test-only login; credentials remain in mode-0600 RUNNER_TEMP, never commit.
        profiles[role] = {"id": created["id"], "access_token": logged["access_token"],
                          "audit_email": email, "audit_password": password}
        if role == "driver":
            # Two separately authenticated HTTP sessions of the SAME driver for E07.
            _, second = call("POST", "/auth/v1/token?grant_type=password", anon,
                             {"email": email, "password": password})
            if not isinstance(second, dict) or not second.get("access_token") or second["access_token"] == logged["access_token"]:
                blocked("independent LOCAL second driver session unavailable")
            profiles["driver_second_session"] = {
                "id": created["id"], "access_token": second["access_token"]
            }
    now = datetime.datetime.now(datetime.timezone.utc).isoformat()
    profile_rows = []
    for number, role in enumerate(ROLES, 1):
        kind = "customer" if role == "outsider" else "driver" if role == "other_driver" else role
        entry = {
            "id": profiles[role]["id"],
            "role": kind,
            "name": "SYNTHETIC Gate1 " + role,
            "phone": "+992" + str(900000000 + number),
        }
        if kind == "driver":
            entry.update({"driver_status": "approved",
                          "cash_limit": 100000,
                          "online": True,
                          "last_seen": now,
                          "lat": 38.56, "lng": 68.78,
                          "loc_acc": 8, "loc_updated": now,
                          "accept_blocked": False})
        profile_rows.append(entry)
    # PostgREST bulk arrays require homogeneous keys. Driver-only fields differ;
    # upsert each synthetic LOCAL identity separately (never patch real users).
    for entry in profile_rows:
        require_success(*call("POST", "/rest/v1/profiles?on_conflict=id", service, entry,
                              "resolution=merge-duplicates,return=minimal"), subject="profile")
    store_id = str(uuid.uuid4())
    item_id = str(uuid.uuid4())
    store = {"id": store_id, "owner_id": profiles["merchant"]["id"],
             "name": "SYNTHETIC Gate1 Store", "category": "rest",
             "fee_type": "fixed", "fee_base": 10, "fee_per_km": 0,
             "is_open": True, "is_active": True,
             "lat": 38.56, "lng": 68.78,
             "discount_pct": 0, "cashback_pct": 0}
    require_success(*call("POST", "/rest/v1/stores", service, store, "return=minimal"), subject="store")
    item = {"id": item_id, "store_id": store_id, "name": "SYNTHETIC Gate1 Dish",
            "price": 50, "available": True, "approved": True,
            "discount_pct": 0}
    require_success(*call("POST", "/rest/v1/menu_items", service, item, "return=minimal"), subject="item")
    # Unrelated ready order belongs to OTHER driver for the RLS negative case.
    unrelated = {"store_id": store_id, "customer_id": profiles["outsider"]["id"],
                 "driver_id": profiles["other_driver"]["id"],
                 "status": "ready", "payment": "cash", "address": "SYNTHETIC Gate1 Street",
                 "lat": 38.56, "lng": 68.78, "subtotal": 50, "delivery_fee": 10, "total": 60}
    _, other_rows = call("POST", "/rest/v1/orders?select=id", service, unrelated, "return=representation")
    if not isinstance(other_rows, list) or len(other_rows) != 1 or "id" not in other_rows[0]:
        blocked("unable to create unrelated LOCAL driver-RLS order")
    fixture = {
        "project_name": "talabot-gate1-local", "origin": ORIGIN,
        "baseline_sha256": schema_sha, "synthetic_only": True,
        "roles": profiles,
        "store_id": store_id,
        "item_id": item_id,
        "place_order_args": {
            "p_store": store_id,
            "p_items": [{"item_id": item_id, "qty": 1, "options": [], "note": ""}],
            "p_tip": 0, "p_address": "SYNTHETIC Gate1 Street",
            "p_lat": 38.56, "p_lng": 68.78,
        },
        "cash_due": 60,
        "other_driver_order": other_rows[0]["id"],
        # Loyalty entries are optional dedup evidence, NEVER a cash-accounting receipt.
        # Cashback is intentionally ZERO in this fixture to prove E07 independence.
        "loyalty_cashback_available": confirmed_cashback,
    }
    fd = os.open(fixture_path, os.O_CREAT | os.O_WRONLY | os.O_EXCL, 0o600)
    with os.fdopen(fd, "w", encoding="utf-8") as fh:
        json.dump(fixture, fh, separators=(",", ":"))
    print("PASS Gate1: five synthetic LOCAL Auth identities + independent driver session, store/menu and negative RLS order seeded.")
    print("PASS Gate1: cashback=0 test fixture; E07 cash effect is measured via cash_balances(), NOT loyalty.")
    print("PASS Gate1: ephemeral fixture saved at RUNNER_TEMP; no tokens or account identifiers logged.")


if __name__ == "__main__":
    try:
        main()
    except Exception as exc:
        print("FAIL Gate1 LOCAL synthetic seed: " + str(exc), file=sys.stderr)
        raise SystemExit(1)
