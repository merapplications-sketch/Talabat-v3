#!/usr/bin/env python3
"""Compare exact live/local PostgreSQL function SQL, effective ACLs and index definitions.
NO application table-row data; fail closed on malformed catalogs."""
import json,sys,pathlib,hashlib,subprocess

ROOT=pathlib.Path(__file__).resolve().parents[1]
QUERY=ROOT/"tools"/"gate1_schema_objects.sql"

def stop(reason):
    print("GATE1_CATALOG_STOP: "+reason,file=sys.stderr)
    raise SystemExit(3)

def read_catalog(path):
    if not QUERY.is_file(): stop("catalog SQL missing")
    proc=subprocess.run(["psql","-X","-A","-t","-q","-v","ON_ERROR_STOP=1","-f",str(QUERY)],
                        capture_output=True,text=True,timeout=60)
    if proc.returncode: stop("psql catalog-only read exited "+str(proc.returncode))
    try:
        data=json.loads(proc.stdout.strip())
        assert set(data)=={"functions","indexes"}
        assert set(data["functions"])=={"driver_ping","deliver_order","report_driver_cash_short"}
        assert set(data["indexes"])=={"tickets_one_open_per_order","tickets_one_open_payment_per_order"}
    except (ValueError,TypeError,AssertionError): stop("unexpected schema-only catalog result")
    out=pathlib.Path(path)
    out.parent.mkdir(parents=True,exist_ok=True)
    out.write_text(json.dumps(data,sort_keys=True,ensure_ascii=False,indent=2)+"\n",encoding="utf-8")
    print("GATE1_CATALOG_CAPTURE_OK",out.name,hashlib.sha256(out.read_bytes()).hexdigest())

def compare(expected,actual,label):
    try:
        a=json.loads(pathlib.Path(expected).read_text(encoding="utf-8"))
        b=json.loads(pathlib.Path(actual).read_text(encoding="utf-8"))
    except Exception: stop("missing/malformed input snapshot")
    if a!=b:
        for category in ("functions","indexes"):
            for name in sorted(set(a.get(category,{}))|set(b.get(category,{}))):
                if a.get(category,{}).get(name)!=b.get(category,{}).get(name):
                    print("GATE1_SCHEMA_DIFFERENCE:",category+"/"+name,file=sys.stderr)
        stop(label+" catalog mismatch")
    print(label+"_PASS: exact function definitions, return signatures, owner, ACL and indexes match")


def compare_restricted_baseline(historical_path,restricted_path):
    """Fail closed unless ONLY the two approved anon_execute TRUE->FALSE deltas exist."""
    import copy
    try:
        historical=json.loads(pathlib.Path(historical_path).read_text(encoding="utf-8"))
        live=json.loads(pathlib.Path(restricted_path).read_text(encoding="utf-8"))
        expected=copy.deepcopy(historical)
        assert set(expected)=={"functions","indexes"} and set(live)=={"functions","indexes"}
        assert set(expected["functions"])=={"driver_ping","deliver_order","report_driver_cash_short"}
        assert set(expected["indexes"])=={"tickets_one_open_per_order","tickets_one_open_payment_per_order"}
        for name in ("driver_ping","deliver_order"):
            assert isinstance(expected["functions"][name],dict)
            assert isinstance(live["functions"][name],dict)
            assert expected["functions"][name]["anon_execute"] is True
            assert live["functions"][name]["anon_execute"] is False
            expected["functions"][name]["anon_execute"]=False
    except (KeyError,TypeError,ValueError,AssertionError):
        stop("historical/restricted catalog malformed or exact anon-only delta absent")
    if expected!=live:
        for category in ("functions","indexes"):
            for name in sorted(set(expected.get(category,{})) | set(live.get(category,{}))):
                if expected.get(category,{}).get(name)!=live.get(category,{}).get(name):
                    print("GATE1_RESTRICTED_DIFFERENCE: "+category+"/"+name,file=sys.stderr)
        stop("unexpected catalog drift beyond exactly two more restrictive anon grants")
    print("PRELIVE_ANON_RESTRICTED_ONLY_PASS: precisely two anon EXECUTE=false differences, no other drift")

def rollback_never_grants_anon(rollback_sql_path,restored_catalog_path):
    """Validate SQL contains no anonymous grant AND local executed ACL denies anon."""
    import re
    sql=pathlib.Path(rollback_sql_path).read_text(encoding="utf-8")
    sql=re.sub(r"(?m)^\s*--[^\n]*","",sql)
    grants=re.findall(r"(?ims)^\s*GRANT\s+EXECUTE\s+ON\s+FUNCTION\s+[^;]+;",sql)
    if len(grants)!=2:stop("rollback must contain exactly two explicit EXECUTE grants")
    for grant in grants:
        parts=re.split(r"(?i)\s+TO\s+",grant,maxsplit=1)
        if len(parts)!=2 or re.search(r"(?i)\b(?:anon|PUBLIC)\b",parts[1]):
            stop("rollback SQL grants anonymous or PUBLIC EXECUTE")
    try:
        catalog=json.loads(pathlib.Path(restored_catalog_path).read_text(encoding="utf-8"))
        for name in ("driver_ping","deliver_order"):
            obj=catalog["functions"][name]
            if obj["anon_execute"] is not False or obj["public_execute"] is not False:
                stop("rollback runtime would re-open anonymous function access: "+name)
            if obj["authenticated_execute"] is not True or obj["service_role_execute"] is not True:
                stop("rollback runtime missing authenticated/service role access: "+name)
        if catalog["functions"]["report_driver_cash_short"] is not None:
            stop("rollback did not remove the proposed cash-shortfall RPC")
    except (KeyError,TypeError,ValueError):
        stop("rollback catalog invalid or missing required fields")
    print("ROLLBACK_never_grants_anon PASS: SQL + executed local ACL deny anon/PUBLIC")

if __name__=="__main__":
    if len(sys.argv)==3 and sys.argv[1]=="capture":read_catalog(sys.argv[2])
    elif len(sys.argv)==5 and sys.argv[1]=="compare":compare(*sys.argv[2:])
    elif len(sys.argv)==4 and sys.argv[1]=="compare-restricted":compare_restricted_baseline(*sys.argv[2:])
    elif len(sys.argv)==4 and sys.argv[1]=="rollback-never-anon":rollback_never_grants_anon(*sys.argv[2:])
    else:stop("usage: capture OUT | compare EXPECTED ACTUAL LABEL | compare-restricted HISTORICAL RESTRICTED | rollback-never-anon SQL RESTORED")
