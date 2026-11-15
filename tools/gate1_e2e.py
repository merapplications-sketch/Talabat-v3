#!/usr/bin/env python3
"""Eleven test-only HTTP E2E gates. Exit 3/BLOCKED before network without talabot-test credentials and ephemeral seed."""
import os,json,sys,uuid,urllib.parse,urllib.request,urllib.error,concurrent.futures,pathlib,re
SCENARIOS=[
("E01","C-11/B-04","customer cash order"),
("E02","C-15/B-07","merchant accepts"),
("E03","D-02/D-07","driver Online ACK"),
("E04","D-03","driver accepts"),
("E05","D-06/B-07","ready then pickup"),
("E06","D-08/B-07","cash exact completion"),
("E07","D-10/B-07/B-10","double deliver/retry at most once"),
("E08","D-08/B-10","underpay rejected + support report"),
("E09","D-11/B-03","chat authorized/rejected"),
("E10","C-16","customer observes terminal status"),
("E11","B-03/D-01","cross-account and unassigned driver RLS")]
PROTECTED={"dzydscryrnahnneydnry","fsvrsvqfknogwmhccera","sbzcokatkhxsijsfplit"}
def blocked(reason):
 print("BLOCKED Gate1 E2E:",reason,flush=True)
 for n,source,title in SCENARIOS: print("BLOCKED",n,source,title,flush=True)
 raise SystemExit(3)
def require(ok,message):
 if not ok: raise AssertionError(message)
def preflight():
 keys=("SUPABASE_TEST_URL","SUPABASE_TEST_ANON_KEY","SUPABASE_TEST_SERVICE_ROLE_KEY","GATE1_TEST_PROJECT_REF","GATE1_TEST_FIXTURE_PATH")
 missing=[k for k in keys if not os.environ.get(k)]
 if missing: blocked("test-only environment missing: "+", ".join(missing)+"; no network attempted")
 ref=os.environ["GATE1_TEST_PROJECT_REF"]; url=os.environ["SUPABASE_TEST_URL"].rstrip("/")
 h=urllib.parse.urlparse(url)
 if ref in PROTECTED or len(ref)!=20 or not ref.isalnum() or h.scheme!="https" or h.netloc!=ref+".supabase.co" or h.path or h.query or h.fragment:
  blocked("unsafe/unknown target origin; no network attempted")
 p=pathlib.Path(os.environ["GATE1_TEST_FIXTURE_PATH"])
 if not p.is_absolute() or not p.is_file() or pathlib.Path(__file__).resolve().parents[1] in p.parents: blocked("ephemeral fixture outside repository missing")
 try: f=json.loads(p.read_text(encoding="utf-8"))
 except Exception: blocked("test fixture corrupt")
 if f.get("project_ref")!=ref or f.get("project_name")!="talabot-test" or f.get("synthetic_only") is not True:
  blocked("explicit separate talabot-test identity not verified")
 if not all(f.get("roles",{}).get(r,{}).get("access_token") for r in ("customer","merchant","driver","outsider","other_driver")):
  blocked("synthetic customer/merchant/driver/outsider sessions missing")
 if not isinstance(f.get("place_order_args"),dict) or not isinstance(f.get("cash_due"),(float,int)) or not f.get("other_driver_order"):
  blocked("real test-only seed schema/order fixture not initialized")
 receipt=f.get("finance_receipt")
 if not isinstance(receipt,dict) or not all(isinstance(receipt.get(k),str) and re.fullmatch(r"[a-z][a-z0-9_]{1,62}",receipt[k]) for k in ("table","order_key")):
  blocked("verified test-only finance receipt table/order-key mapping missing; cannot assert at-most-once financial effect")
 return url,f
class NoRedirect(urllib.request.HTTPRedirectHandler):
 def redirect_request(self,*args,**kwargs): raise RuntimeError("HTTP redirect denied")
OPENER=urllib.request.build_opener(NoRedirect())
class API:
 def __init__(self,url,f):
  self.url=url;self.f=f;self.anon=os.environ["SUPABASE_TEST_ANON_KEY"];self.service=os.environ["SUPABASE_TEST_SERVICE_ROLE_KEY"]
 def query(self,method,path,role,body=None,service=False):
  require(not path.startswith("/") and "://" not in path and ".." not in path,"bad route")
  headers={"apikey":self.service if service else self.anon,"Authorization":"Bearer "+(self.service if service else self.f["roles"][role]["access_token"]),"Accept":"application/json"}
  raw=json.dumps(body).encode() if body is not None else None
  if raw is not None: headers["Content-Type"]="application/json"
  if method=="POST" and path=="rest/v1/order_chat": headers["Prefer"]="return=representation"
  req=urllib.request.Request(self.url+"/"+path,headers=headers,data=raw,method=method)
  try:
   with OPENER.open(req,timeout=15) as res:
    data=res.read(1024*1024);return res.status,json.loads(data) if data else None
  except urllib.error.HTTPError as exc:return exc.code,None
 def rpc(self,role,name,args): return self.query("POST","rest/v1/rpc/"+name,role,args)
 def rows(self,role,table,filters,service=False):
  route="rest/v1/"+table+"?"+urllib.parse.urlencode(filters)
  code,data=self.query("GET",route,role,service=service)
  require(code==200 and isinstance(data,list),"failed to read test table "+table)
  return data
 def cash_order(self):
  p=dict(self.f["place_order_args"]);p["p_key"]=uuid.uuid4().hex;p["p_payment"]="cash"
  c,r=self.rpc("customer","place_order",p)
  require(200<=c<300 and isinstance(r,int),"synthetic place_order not executable")
  return r
 def prep(self):
  oid=self.cash_order()
  for role,name,body in [
   ("merchant","set_order_status",{"p_id":oid,"p_to":"preparing"}),
   ("driver","driver_ping",{"p_online":True}),
   ("driver","driver_accept",{"p_id":oid}),
   ("merchant","set_order_status",{"p_id":oid,"p_to":"ready"}),
   ("driver","set_order_status",{"p_id":oid,"p_to":"pickedup"})]:
   code,_=self.rpc(role,name,body);require(200<=code<300,"prep failed: "+name)
  return oid
def run():
 url,f=preflight();a=API(url,f);passed=[];state={}
 def check(n,fn):
  fn();passed.append(n);print("PASS",n,"[live isolated test HTTP only]",flush=True)
 def E01():state["oid"]=a.cash_order()
 check("E01",E01)
 def E02():require(200<=a.rpc("merchant","set_order_status",{"p_id":state["oid"],"p_to":"preparing"})[0]<300,"merchant accept")
 check("E02",E02)
 def E03():require(200<=a.rpc("driver","driver_ping",{"p_online":True})[0]<300,"driver ping ACK")
 check("E03",E03)
 def E04():require(200<=a.rpc("driver","driver_accept",{"p_id":state["oid"]})[0]<300,"driver accept")
 check("E04",E04)
 def E05():
  oid=state["oid"]
  require(200<=a.rpc("merchant","set_order_status",{"p_id":oid,"p_to":"ready"})[0]<300,"ready")
  require(200<=a.rpc("driver","set_order_status",{"p_id":oid,"p_to":"pickedup"})[0]<300,"pickup")
 check("E05",E05)
 def E06():
  oid=state["oid"];code,_=a.rpc("driver","deliver_order",{"p_id":oid,"p_cash":f["cash_due"],"p_note":None,"p_photo":None})
  require(200<=code<300,"exact cash delivery")
 check("E06",E06)
 def E07():
  oid=a.prep()
  body={"p_id":oid,"p_cash":f["cash_due"],"p_note":None,"p_photo":None}
  def snapshot():
   order=a.rows(None,"orders",{"id":"eq."+str(oid),"select":"status,done_at,cash_collected"},service=True)
   require(len(order)==1,"delivery row absent in isolated test")
   meta=f["finance_receipt"]
   receipt=a.rows(None,meta["table"],{meta["order_key"]:"eq."+str(oid),"select":"id"},service=True)
   return order[0],receipt
  with concurrent.futures.ThreadPoolExecutor(max_workers=2) as pool:
   codes=list(pool.map(lambda _:a.rpc("driver","deliver_order",body)[0],(0,1)))
  # Approved Gate1 SQL returns void/HTTP 2xx for identical retries, WITHOUT a second UPDATE.
  require(len(codes)==2 and all(200<=c<300 for c in codes),"idempotent concurrent delivery did not acknowledge both identical attempts")
  first,receipt=snapshot()
  require(first["status"]=="delivered" and first["done_at"] is not None,"server did not reach delivered exactly once")
  require(len(receipt)==1,"financial/receipt effects are not exactly one")
  require(200<=a.rpc("driver","deliver_order",body)[0]<300,"same-payload post-COMMIT replay must acknowledge without new update")
  second,receipt_after=snapshot()
  require(second==first and receipt_after==receipt,"post-commit replay mutated delivery or financial receipt")
  changed=dict(body,p_cash=round(f["cash_due"]+1,2))
  require(a.rpc("driver","deliver_order",changed)[0]>=400,"conflicting completed replay must be rejected")
 check("E07",E07)
 def E08():
  oid=a.prep()
  paid=round(f["cash_due"]-1,2)
  require(paid>=0,"test due below one")
  args={"p_id":oid,"p_cash":paid,"p_note":"Test only"}
  code,ticket=a.rpc("driver","report_driver_cash_short",args)
  require(200<=code<300 and isinstance(ticket,int),"driver support-report RPC denied")
  # Support record is independent of rejected delivery transaction (Q14).
  def tickets():
   return a.rows(None,"support_tickets",{"order_id":"eq."+str(oid),"id":"eq."+str(ticket),"select":"id,reason,status"},service=True)
  first=tickets()
  require(len(first)==1 and first[0]["reason"]=="payment","support record not persisted")
  code,ticket2=a.rpc("driver","report_driver_cash_short",args)
  require(200<=code<300 and ticket2==ticket and tickets()==first,"duplicate support ticket on retry")
  require(a.rpc("driver","deliver_order",{"p_id":oid,"p_cash":paid,"p_note":"Test only","p_photo":None})[0]>=400,"short cash was accepted")
  status=a.rows("customer","orders",{"id":"eq."+str(oid),"select":"status"})
  require(len(status)==1 and status[0]["status"]=="pickedup","underpayment changed order status")
  messages=a.rows(None,"ticket_messages",{"ticket_id":"eq."+str(ticket),"select":"id,sender_id,body"},service=True)
  require(len(messages)==1 and messages[0]["sender_id"]==f["roles"]["driver"]["id"],"support message lost or duplicated")
 check("E08",E08)
 def E09():
  oid=a.prep();r=f["roles"]
  require(200<=a.query("POST","rest/v1/order_chat","driver",{"order_id":oid,"sender_id":r["driver"]["id"],"body":"Synthetic chat"})[0]<300,"chat valid")
  require(a.query("POST","rest/v1/order_chat","outsider",{"order_id":oid,"sender_id":r["outsider"]["id"],"body":"Illegal test"})[0]>=400,"chat outsider allowed")
 check("E09",E09)
 def E10():
  q=a.rows("customer","orders",{"id":"eq."+str(state["oid"]),"select":"status"})
  require(len(q)==1 and q[0]["status"]=="delivered","tracking not delivered")
 check("E10",E10)
 def E11():
  oid=state["oid"];other=f["other_driver_order"]
  require(a.rows("outsider","orders",{"id":"eq."+str(oid),"select":"id"})==[],"outsider read leakage")
  require(a.rows("driver","orders",{"id":"eq."+str(other),"select":"id"})==[],"unassigned driver read leakage")
 check("E11",E11)
 require(len(passed)==11,"11 case count mismatch")
if __name__=="__main__":
 try: run()
 except Exception as e:
  print("FAIL E2E on isolated test project:",str(e),file=sys.stderr);raise SystemExit(1)
