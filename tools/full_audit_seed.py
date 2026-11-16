#!/usr/bin/env python3
"""Augment Gate1 synthetic fixture ONLY on 127.0.0.1:54321, after Gate1's original E2E PASS.
No real users or live records. This file never contains/prints bearer tokens or passwords.
"""
import os,json,pathlib,secrets,uuid,datetime,sys
from tools.gate1_local_seed import call, require_success, ORIGIN

def main():
    if os.environ.get("SUPABASE_LOCAL_URL")!=ORIGIN or any(os.environ.get(k) for k in ("SUPABASE_ACCESS_TOKEN","DATABASE_URL","SUPABASE_PROJECT_REF")):
        raise RuntimeError("HALT: non-loopback/cloud Supabase environment")
    path=pathlib.Path(os.environ["GATE1_TEST_FIXTURE_PATH"])
    data=json.loads(path.read_text("utf8"))
    if data.get("origin")!=ORIGIN or not data.get("synthetic_only"):
        raise RuntimeError("HALT: fixture not the local-only verified seed")
    anon=os.environ["SUPABASE_LOCAL_ANON_KEY"]
    service=os.environ["SUPABASE_LOCAL_SERVICE_ROLE_KEY"]
    email="audit-admin-"+secrets.token_hex(9)+"@example.invalid"
    password="Audit!"+secrets.token_urlsafe(25)
    _,user=call("POST","/auth/v1/admin/users",service,{"email":email,"password":password,"email_confirm":True})
    _,auth=call("POST","/auth/v1/token?grant_type=password",anon,{"email":email,"password":password})
    assert user.get("id") and auth.get("access_token")
    row={"id":user["id"],"name":"SYNTHETIC Директор Талабот Тестовый","role":"admin",
         "phone":"+992900000400"}
    require_success(*call("POST","/rest/v1/profiles?on_conflict=id",service,row,"resolution=merge-duplicates,return=minimal"),
                    subject="LOCAL admin profile")
    data["roles"]["admin"]={"id":user["id"],"access_token":auth["access_token"]}
    # All original Gate1 test identities/orders are preserved. Additional order rows are disposable.
    store_id=data["store_id"]; customer=data["roles"]["customer"]["id"];driver=data["roles"]["driver"]["id"]
    now=datetime.datetime.now(datetime.timezone.utc).isoformat()
    long_store="SYNTHETIC Ресторан Дарул-Хилоф Центральный филиал проспект Рудаки Душанбе"
    require_success(*call("PATCH","/rest/v1/stores?id=eq."+store_id,service,
       {"name":long_store,"address":"СИНТЕТИЧЕСКИЙ проспект Рудаки 100, Душанбе","phone":"+992900000401"},
       "return=minimal"),subject="LOCAL long-name store")
    for kind,newname in (("customer","SYNTHETIC Муҳаммад Абдураҳмонзода из Душанбе"),
                         ("merchant","SYNTHETIC Малика Раҳимова менеджер ресторана"),
                         ("driver","SYNTHETIC Баҳромҷон Имомов курьер")):
        pid=data["roles"][kind]["id"]
        require_success(*call("PATCH","/rest/v1/profiles?id=eq."+pid,service,
           {"name":newname},"return=minimal"),subject="LOCAL "+kind+" long name")
    wanted=[("pending","cash"),("preparing","cash"),("ready","cash"),("pickedup","cash"),
            ("delivered","cash"),("cancelled","cash"),("rejected","cash")]
    inserted=[]
    for i,(status,payment) in enumerate(wanted):
        order={"store_id":store_id,"customer_id":customer,"driver_id":driver,
          "status":status,"payment":payment,
          "address":"СИНТЕТИЧЕСКИЙ Душанбе, длинный адрес улица Садриддина Айни дом 102 квартира 17",
          "lat":38.56,"lng":68.78,"subtotal":50,"delivery_fee":10,"total":60}
        try:
            _,r=call("POST","/rest/v1/orders?select=id",service,order,"return=representation")
            inserted.extend([{"id":str(x["id"]),"status":status} for x in (r or []) if "id" in x])
        except Exception as e:
            # Fail closed on inability to seed a state: do not mark it as covered.
            data.setdefault("seed_limitations",[]).append({"status":status,"error":str(e)[:95]})
    data["full_audit_orders"]=inserted
    with path.open("w",encoding="utf8") as out:json.dump(data,out,separators=(",",":"))
    os.chmod(path,0o600)
    print("FULL_AUDIT_LOCAL_SEED PASS: admin session, 3 multilingual long names, store address and "+
          str(len(inserted))+" synthetic order states; limitations="+str(len(data.get("seed_limitations",[]))))
if __name__=="__main__":
    try:main()
    except Exception as exc:
        print("FULL_AUDIT_LOCAL_SEED BLOCKED: "+str(exc),file=sys.stderr);raise
