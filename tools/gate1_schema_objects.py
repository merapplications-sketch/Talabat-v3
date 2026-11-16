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

if __name__=="__main__":
    if len(sys.argv)==3 and sys.argv[1]=="capture":read_catalog(sys.argv[2])
    elif len(sys.argv)==5 and sys.argv[1]=="compare":compare(*sys.argv[2:])
    else:stop("usage: capture OUT | compare EXPECTED ACTUAL LABEL")
