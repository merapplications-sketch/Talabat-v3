#!/usr/bin/env python3
"""TALABOT Gate1 B: fail-closed checks plus read-only connection health probe.
Never prints database connection details, SQL row data or credentials."""
import os,sys,json,urllib.parse,urllib.request
REF="dzydscryrnahnneydnry"
INT_HEAD="09ef07fd29fb5c5a3e323c23c7331e577567ab1e"
REPO="merapplications-sketch/Talabat-v3"

def stop(message):
    print("GATE1_B_PRECHECK_STOP: "+message,file=sys.stderr)
    raise SystemExit(3)

def run():
    if os.environ.get("GITHUB_REF")!="refs/heads/ops/gate1-apply-b-20261116":
        stop("unauthorized workflow branch")
    raw=os.environ.get("SUPABASE_PROD_DB_URL","")
    if not raw:stop("SUPABASE_PROD_DB_URL repository secret absent; no SQL executed")
    if any(ch in raw for ch in "\n\r\x00"):stop("database URI contains forbidden control characters")
    try:
        u=urllib.parse.urlsplit(raw)
        host=(u.hostname or "").lower()
        name=urllib.parse.unquote(u.username or "")
        password=u.password
        port=u.port or 5432
        query=urllib.parse.parse_qs(u.query)
    except ValueError:stop("database URI invalid")
    if u.scheme not in ("postgres","postgresql") or not password or not host or not name:
        stop("database connection URI missing required fields")
    direct=host==f"db.{REF}.supabase.co" and name=="postgres"
    pooler=host.endswith(".pooler.supabase.com") and name==f"postgres.{REF}"
    if not (direct or pooler):stop("target must be EXACT authorized Talabat database ref; pilot forbidden")
    if port not in (5432,6543) or u.path!="/postgres":
        stop("unexpected target database or port")
    if any(v not in ("require","verify-ca","verify-full") for v in query.get("sslmode",["require"])):
        stop("SSL validation must not be disabled")
    token=os.environ.get("GITHUB_TOKEN","")
    if not token:stop("GitHub read-only token unavailable")
    url=f"https://api.github.com/repos/{REPO}/git/ref/heads/tech/v82-int"
    request=urllib.request.Request(url,headers={"Authorization":"Bearer "+token,
          "Accept":"application/vnd.github+json","X-GitHub-Api-Version":"2022-11-28"})
    try:
        with urllib.request.urlopen(request,timeout=12) as response:
            status=json.load(response)
        sha=status.get("object",{}).get("sha")
    except Exception:stop("unable to independently verify integration branch; no SQL permitted")
    if sha!=INT_HEAD:stop("tech/v82-int changed since approval; no SQL permitted")
    # Read-only SELECT 1 diagnostic before any catalog query or DDL. Failure output is
    # reduced to a fixed reason code; NEVER print libpq stderr or connection URI.
    import subprocess
    env=os.environ.copy()
    env["PGDATABASE"]=raw
    env["PGSSLMODE"]="require"
    env["PGCONNECT_TIMEOUT"]="10"
    try:
        probe=subprocess.run(["psql","-X","-q","-A","-t","-w","-v","ON_ERROR_STOP=1","-c","SELECT 1"],
                             env=env,capture_output=True,text=True,timeout=18)
    except subprocess.TimeoutExpired:
        stop("PSQL_CONNECT_TIMEOUT (read-only precheck, no SQL migration executed)")
    except OSError:
        stop("PSQL_CLIENT_UNAVAILABLE (read-only precheck, no SQL migration executed)")
    if probe.returncode!=0:
        detail=probe.stderr.lower()
        if "password authentication failed" in detail or "authentication failed" in detail:
            reason="PSQL_AUTHENTICATION_REJECTED"
        elif "could not translate host name" in detail or "name or service not known" in detail or "temporary failure in name resolution" in detail:
            reason="PSQL_DNS_FAILURE"
        elif "network is unreachable" in detail or "no route to host" in detail:
            reason="PSQL_NETWORK_UNREACHABLE"
        elif "connection timed out" in detail or "timeout expired" in detail:
            reason="PSQL_CONNECTION_TIMEOUT"
        elif "connection refused" in detail:
            reason="PSQL_CONNECTION_REFUSED"
        elif "no pg_hba.conf entry" in detail or "ssl" in detail or "certificate" in detail:
            reason="PSQL_SSL_OR_ACCESS_REJECTED"
        elif "tenant or user not found" in detail or "tenant" in detail:
            reason="PSQL_POOLER_TENANT_REJECTED"
        elif "does not exist" in detail:
            reason="PSQL_DATABASE_OR_USER_NOT_FOUND"
        elif "invalid" in detail or "malformed" in detail:
            reason="PSQL_CONNECTION_STRING_INVALID"
        else:
            reason="PSQL_CONNECTION_FAILED_UNCLASSIFIED"
        stop(reason+" (read-only precheck; no migration executed; psql exit "+str(probe.returncode)+")")
    if probe.stdout.strip()!="1":
        stop("PSQL_READ_ONLY_PROBE_UNEXPECTED_RESULT (no migration executed)")
    print("GATE1_B_PSQL_READONLY_CONNECT_PASS")
    print("GATE1_B_PRECHECK_PASS: exact Talabat database, SSL, isolated ops ref, and unchanged integration head")
if __name__=="__main__":run()
