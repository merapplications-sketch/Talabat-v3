#!/usr/bin/env python3
"""Eleven LOCAL Supabase-only HTTP E2E gates. Fail closed BEFORE network unless isolated Docker at 127.0.0.1:54321 plus synthetic fixture exist. NEVER production/pilot."""
import os,json,sys,uuid,urllib.parse,urllib.request,urllib.error,concurrent.futures,pathlib,re
from decimal import Decimal
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
("E11","B-03/D-01","cross-account and unassigned driver RLS"),
("E03b","SF-02","unapproved driver_ping denied"),
("E08b","SF-06","pre-existing unrelated support ticket stays separate"),
("E08c","SF-06","identical support retry causes no timestamp write"),
("E12","SF-03","revoked assigned driver cannot deliver or report"),
("E13","SF-07/09","negative authorization RPC/chat matrix")]
PROTECTED={"dzydscryrnahnneydnry","fsvrsvqfknogwmhccera","sbzcokatkhxsijsfplit"}
def blocked(reason):
 print("BLOCKED Gate1 E2E:",reason,flush=True)
 for n,source,title in SCENARIOS: print("BLOCKED",n,source,title,flush=True)
 raise SystemExit(3)
def require(ok,message):
 if not ok: raise AssertionError(message)
def preflight():
 keys=("SUPABASE_LOCAL_URL","SUPABASE_LOCAL_ANON_KEY","SUPABASE_LOCAL_SERVICE_ROLE_KEY","GATE1_TEST_FIXTURE_PATH","GATE1_SCHEMA_SHA256")
 missing=[k for k in keys if not os.environ.get(k)]
 if missing: blocked("test-only environment missing: "+", ".join(missing)+"; no network attempted")
 url=os.environ["SUPABASE_LOCAL_URL"].rstrip("/")
 h=urllib.parse.urlparse(url)
 if url!="http://127.0.0.1:54321" or h.scheme!="http" or h.netloc!="127.0.0.1:54321":
  blocked("only exact local Docker API http://127.0.0.1:54321 allowed; no network attempted")
 for key,value in os.environ.items():
  if key.startswith("SUPABASE_TEST_") and key!="SUPABASE_TEST_PROJECT_NAME" and any(p in value for p in PROTECTED):
   blocked("protected remote project detected in environment; no network attempted")
 if not re.fullmatch(r"[a-f0-9]{64}",os.environ["GATE1_SCHEMA_SHA256"]):
  blocked("missing verified baseline SHA256; no network attempted")
 p=pathlib.Path(os.environ["GATE1_TEST_FIXTURE_PATH"])
 if not p.is_absolute() or not p.is_file() or pathlib.Path(__file__).resolve().parents[1] in p.parents: blocked("ephemeral fixture outside repository missing")
 try: f=json.loads(p.read_text(encoding="utf-8"))
 except Exception: blocked("test fixture corrupt")
 if f.get("project_name")!="talabot-gate1-local" or f.get("origin")!=url or f.get("synthetic_only") is not True or f.get("baseline_sha256")!=os.environ["GATE1_SCHEMA_SHA256"]:
  blocked("fixture not bound to verified LOCAL schema and synthetic-only origin")
 if not all(f.get("roles",{}).get(r,{}).get("access_token") for r in ("customer","merchant","driver","driver_second_session","outsider","other_driver")):
  blocked("synthetic customer/merchant/driver/outsider sessions missing")
 if not isinstance(f.get("place_order_args"),dict) or not isinstance(f.get("cash_due"),(float,int)) or not f.get("other_driver_order"):
  blocked("LOCAL ephemeral seed/order fixture incomplete")
 if f["roles"]["driver"]["id"]!=f["roles"]["driver_second_session"]["id"] or f["roles"]["driver"]["access_token"]==f["roles"]["driver_second_session"]["access_token"]:
  blocked("E07 requires two independently authenticated sessions of the same LOCAL driver")
 if not isinstance(f.get("loyalty_cashback_available"),bool):
  blocked("loyalty cash-back schema metadata missing")
 return url,f
class NoRedirect(urllib.request.HTTPRedirectHandler):
 def redirect_request(self,*args,**kwargs): raise RuntimeError("HTTP redirect denied")
OPENER=urllib.request.build_opener(urllib.request.ProxyHandler({}),NoRedirect())
class API:
 def __init__(self,url,f):
  self.url=url;self.f=f;self.anon=os.environ["SUPABASE_LOCAL_ANON_KEY"];self.service=os.environ["SUPABASE_LOCAL_SERVICE_ROLE_KEY"]
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
 def cash_balance(self,role="driver"):
  code,rows=self.rpc(role,"cash_balances",{})
  require(200<=code<300 and isinstance(rows,list),"driver cash_balances() was not readable on LOCAL")
  own_id=self.f["roles"]["driver"]["id"]
  entries=[row for row in rows if row.get("driver_id")==own_id]
  require(len(entries)<=1,"duplicate driver cash balance row")
  return Decimal(str(entries[0]["balance"])) if entries else Decimal("0")
 def cash_order(self):
  p=dict(self.f["place_order_args"]);p["p_key"]=uuid.uuid4().hex;p["p_payment"]="cash"
  c,r=self.rpc("customer","place_order",p)
  require(200<=c<300 and isinstance(r,int),"synthetic place_order not executable")
  return r
 def refresh_driver(self):
  # LOCAL fake driver GPS/presence only; ensures the real server dispatcher sees a fresh, approved driver.
  code,_=self.rpc("driver","driver_ping",{"p_online":True})
  require(200<=code<300,"LOCAL driver ping denied")
  import datetime
  now=datetime.datetime.now(datetime.timezone.utc).isoformat()
  did=self.f["roles"]["driver"]["id"]
  code,_=self.query("PATCH","rest/v1/profiles?id=eq."+str(did),None,
                    {"last_seen":now,"loc_updated":now,"online":True,
                     "lat":38.56,"lng":68.78,"loc_acc":8},service=True)
  require(200<=code<300,"LOCAL synthetic driver presence refresh denied")
 def prep(self):
  self.refresh_driver()
  oid=self.cash_order()
  for role,name,body in [
   ("merchant","set_order_status",{"p_id":oid,"p_to":"preparing"}),
   ("driver","driver_accept",{"p_id":oid}),
   ("merchant","set_order_status",{"p_id":oid,"p_to":"ready"}),
   ("driver","set_order_status",{"p_id":oid,"p_to":"pickedup"})]:
   code,value=self.rpc(role,name,body)
   require(200<=code<300,"prep failed: "+name)
   if name=="driver_accept":require(value is True,"driver_accept returned false")
  return oid
def run():
 url,f=preflight();a=API(url,f);passed=[];state={}
 def check(n,fn):
  fn();passed.append(n);print("PASS",n,"[live isolated test HTTP only]",flush=True)
 def E01():
  state["oid"]=a.cash_order()
  row=a.rows("customer","orders",{"id":"eq."+str(state["oid"]),"select":"total,payment,status"})
  require(len(row)==1 and abs(float(row[0]["total"])-float(f["cash_due"]))<0.005,"actual server cash total differs from synthetic fixture")
  require(row[0]["payment"]=="cash" and row[0]["status"]=="pending","customer cash order invalid")
 check("E01",E01)
 def E02():require(200<=a.rpc("merchant","set_order_status",{"p_id":state["oid"],"p_to":"preparing"})[0]<300,"merchant accept")
 check("E02",E02)
 def E03():
  code,ack=a.rpc("driver","driver_ping",{"p_online":True})
  require(200<=code<300 and ack is True,"driver ping must return an explicit positive server ACK")
  rows=a.rows("driver","profiles",{"id":"eq."+str(f["roles"]["driver"]["id"]),"select":"online,last_seen"})
  require(len(rows)==1 and rows[0]["online"] is True and rows[0]["last_seen"],"server Online presence not committed")
 check("E03",E03)
 def E03b():
  uid=f["roles"]["other_driver"]["id"]
  path="rest/v1/profiles?id=eq."+uid
  try:
   require(200<=a.query("PATCH",path,None,{"driver_status":"suspended","online":False},service=True)[0]<300,"could not suspend LOCAL synthetic other driver")
   before=a.rows(None,"profiles",{"id":"eq."+uid,"select":"driver_status,online,last_seen"},service=True)
   require(len(before)==1 and before[0]["driver_status"]=="suspended","LOCAL other driver revocation absent")
   code,_=a.rpc("other_driver","driver_ping",{"p_online":True})
   require(code>=400,"revoked driver_ping returned a false positive ACK")
   require(a.rows(None,"profiles",{"id":"eq."+uid,"select":"driver_status,online,last_seen"},service=True)==before,"denied ping wrote presence state")
  finally:
   a.query("PATCH",path,None,{"driver_status":"approved","online":True},service=True)
 check("E03b_ping_denied_unapproved",E03b)
 def E04():
  code,value=a.rpc("driver","driver_accept",{"p_id":state["oid"]})
  require(200<=code<300 and value is True,"driver accept not acknowledged by server")
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
   rows=a.rows(None,"orders",{"id":"eq."+str(oid),"select":"status,done_at,total,wallet_used,cash_collected,cash_settled_at"},service=True)
   require(len(rows)==1,"LOCAL delivery order absent")
   return rows[0]
  def cashback():
   if not f["loyalty_cashback_available"]:return None
   return a.rows(None,"wallet_entries",{"order_id":"eq."+str(oid),"kind":"eq.cashback","select":"id,amount,kind"},service=True)
  before=snapshot()
  require(before["status"]=="pickedup" and before["cash_collected"] is None,"E07 must start before a cash collection")
  due=Decimal(str(before["total"]))-Decimal(str(before["wallet_used"] or 0))
  require(due>0 and due==Decimal(str(f["cash_due"])),"cash due must equal total minus wallet_used")
  opening=a.cash_balance()
  # Separate GoTrue sessions, same driver, simultaneous PostgREST HTTP RPC calls.
  with concurrent.futures.ThreadPoolExecutor(max_workers=2) as pool:
   tasks=[pool.submit(a.rpc,role,"deliver_order",body) for role in ("driver","driver_second_session")]
   codes=[task.result()[0] for task in tasks]
  require(len(codes)==2 and all(200<=c<300 for c in codes),"concurrent identical delivery did not ACK both sessions")
  first=snapshot();balance=a.cash_balance();cashback_before=cashback()
  require(first["status"]=="delivered" and first["done_at"] is not None,"cash order not delivered")
  require(first["cash_settled_at"] is None,"unapproved settlement occurred")
  require(Decimal(str(first["cash_collected"]))==due,"cash_collected != total - wallet_used")
  require(balance-opening==due,"unsettled courier cash_balance delta was not EXACTLY ONCE")
  if cashback_before is not None:require(len(cashback_before)<=1,"cashback duplicated (not a cash receipt)")
  require(200<=a.rpc("driver_second_session","deliver_order",body)[0]<300,"identical post-COMMIT retry failed")
  second=snapshot();after_balance=a.cash_balance();cashback_after=cashback()
  require(second==first and after_balance==balance,"identical replay changed delivery/cash balance/done_at")
  if cashback_before is not None:require(cashback_after==cashback_before,"identical replay changed optional loyalty entries")
  changed=dict(body,p_cash=round(f["cash_due"]+1,2))
  require(a.rpc("driver","deliver_order",changed)[0]>=400,"conflicting post-COMMIT replay accepted")
  require(snapshot()==first and a.cash_balance()==balance,"conflicting retry caused a cash side effect")
 check("E07_cash_effect_once",E07)
 def E08():
  oid=a.prep()
  state["underpaid_oid"]=oid
  # An open COURIER complaint already exists; payment report needs a separate ticket.
  record={"customer_id":f["roles"]["customer"]["id"],"order_id":oid,"reason":"courier"}
  code,_=a.query("POST","rest/v1/support_tickets",None,record,service=True)
  require(200<=code<300,"synthetic unrelated open support ticket not seeded")
  unrelated=a.rows(None,"support_tickets",{"order_id":"eq."+str(oid),"reason":"eq.courier","select":"id,reason,status,updated_at"},service=True)
  require(len(unrelated)==1 and unrelated[0]["status"]=="open","unrelated ticket invalid")
  state["unrelated_ticket"]=unrelated[0]
  paid=round(f["cash_due"]-1,2)
  require(paid>=0,"test due below one")
  args={"p_id":oid,"p_cash":paid,"p_note":"Test only"}
  state["underpaid_args"]=args
  code,ticket=a.rpc("driver","report_driver_cash_short",args)
  require(200<=code<300 and isinstance(ticket,int),"payment support-report RPC denied")
  state["underpaid_ticket"]=ticket
  def tickets():
   return a.rows(None,"support_tickets",{"order_id":"eq."+str(oid),"id":"eq."+str(ticket),"select":"id,reason,status,updated_at"},service=True)
  first=tickets()
  require(len(first)==1 and first[0]["reason"]=="payment","payment ticket absent")
  code,ticket2=a.rpc("driver","report_driver_cash_short",args)
  require(200<=code<300 and ticket2==ticket and tickets()==first,"identical support report changed ticket metadata")
  require(a.rpc("driver","deliver_order",{"p_id":oid,"p_cash":paid,"p_note":"Test only","p_photo":None})[0]>=400,"short cash accepted")
  status=a.rows("customer","orders",{"id":"eq."+str(oid),"select":"status"})
  require(len(status)==1 and status[0]["status"]=="pickedup","underpayment changed delivery state")
  messages=a.rows(None,"ticket_messages",{"ticket_id":"eq."+str(ticket),"select":"id,sender_id,body,created_at"},service=True)
  require(len(messages)==1 and messages[0]["sender_id"]==f["roles"]["driver"]["id"],"support report message lost or duplicated")
 check("E08",E08)
 def E08b():
  oid=state["underpaid_oid"]
  tickets=a.rows(None,"support_tickets",{"order_id":"eq."+str(oid),"select":"id,reason,status,updated_at"},service=True)
  require(len(tickets)==2,"unrelated and payment ticket must coexist without loosening other uniqueness")
  unrelated=[t for t in tickets if t["reason"]=="courier"]
  payment=[t for t in tickets if t["reason"]=="payment"]
  require(len(unrelated)==1 and len(payment)==1,"support report reused unrelated reason")
  require(unrelated[0]==state["unrelated_ticket"],"original unrelated ticket mutated")
  require(payment[0]["id"]==state["underpaid_ticket"],"payment ticket misattributed")
 check("E08b_existing_unrelated_ticket",E08b)
 def E08c():
  oid=state["underpaid_oid"];ticket=state["underpaid_ticket"]
  def snapshot():
   t=a.rows(None,"support_tickets",{"order_id":"eq."+str(oid),"select":"id,reason,status,updated_at"},service=True)
   m=a.rows(None,"ticket_messages",{"ticket_id":"eq."+str(ticket),"select":"id,body,sender_id,created_at"},service=True)
   o=a.rows(None,"orders",{"id":"eq."+str(oid),"select":"status,done_at,cash_collected"},service=True)
   return t,m,o
  before=snapshot()
  code,returned=a.rpc("driver","report_driver_cash_short",state["underpaid_args"])
  require(200<=code<300 and returned==ticket,"idempotent report retry failed")
  require(snapshot()==before,"identical report replay wrote updated_at/message/order state")
 check("E08c_identical_repeat_no_write",E08c)
 def E09():
  # E08 leaves a real LOCAL driver-owned pickedup order: reuse for chat; no parallel active delivery conflict.
  oid=state["underpaid_oid"];r=f["roles"]
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
 def E12():
  oid=state["underpaid_oid"];uid=f["roles"]["driver"]["id"]
  path="rest/v1/profiles?id=eq."+uid
  require(200<=a.query("PATCH",path,None,{"driver_status":"suspended","online":False},service=True)[0]<300,"LOCAL driver revocation denied")
  try:
   before=a.rows(None,"orders",{"id":"eq."+str(oid),"select":"status,done_at,cash_collected"},service=True)
   tickets=a.rows(None,"support_tickets",{"order_id":"eq."+str(oid),"select":"id,reason,status,updated_at"},service=True)
   profile=a.rows(None,"profiles",{"id":"eq."+uid,"select":"driver_status,online,last_seen"},service=True)
   require(profile[0]["driver_status"]=="suspended","driver revocation did not persist")
   delivery={"p_id":oid,"p_cash":f["cash_due"],"p_note":None,"p_photo":None}
   require(a.rpc("driver","deliver_order",delivery)[0]>=400,"suspended assigned driver delivered order")
   require(a.rpc("driver","report_driver_cash_short",state["underpaid_args"])[0]>=400,"suspended assigned driver reported shortfall")
   require(a.rpc("driver","driver_ping",{"p_online":True})[0]>=400,"suspended assigned driver ping falsely acknowledged")
   require(a.rows(None,"orders",{"id":"eq."+str(oid),"select":"status,done_at,cash_collected"},service=True)==before,"revoked denial changed order")
   require(a.rows(None,"support_tickets",{"order_id":"eq."+str(oid),"select":"id,reason,status,updated_at"},service=True)==tickets,"revoked denial wrote ticket metadata")
   require(a.rows(None,"profiles",{"id":"eq."+uid,"select":"driver_status,online,last_seen"},service=True)==profile,"revoked ping wrote profile")
  finally:
   require(200<=a.query("PATCH",path,None,{"driver_status":"approved","online":True},service=True)[0]<300,"could not restore LOCAL synthetic driver")
 check("E12_revoked_driver_denied",E12)
 def E13():
  oid=state["underpaid_oid"]
  def snapshot():
   orders=a.rows(None,"orders",{"id":"eq."+str(oid),"select":"status,done_at,cash_collected"},service=True)
   tickets=a.rows(None,"support_tickets",{"order_id":"eq."+str(oid),"select":"id,reason,status,updated_at"},service=True)
   messages=a.rows(None,"ticket_messages",{"ticket_id":"eq."+str(state["underpaid_ticket"]),"select":"id,body,sender_id,created_at"},service=True)
   return orders,tickets,messages
  before=snapshot()
  for role in ("customer","outsider","other_driver"):
   require(a.rpc(role,"deliver_order",{"p_id":oid,"p_cash":f["cash_due"],"p_note":None,"p_photo":None})[0]>=400,role+" unauthorized delivery RPC succeeded")
   require(a.rpc(role,"report_driver_cash_short",state["underpaid_args"])[0]>=400,role+" unauthorized shortfall RPC succeeded")
  for role in ("customer","outsider"):
   uid=f["roles"][role]["id"]
   pre=a.rows(None,"profiles",{"id":"eq."+uid,"select":"online,last_seen"},service=True)
   require(a.rpc(role,"driver_ping",{"p_online":True})[0]>=400,role+" unauthorized presence RPC succeeded")
   require(a.rows(None,"profiles",{"id":"eq."+uid,"select":"online,last_seen"},service=True)==pre,"denied ping mutated wrong-role profile")
  # An approved but unassigned driver may legitimately ping globally; the order
  # authorization denial is covered above. No invented per-order ping restriction.
  require(a.rows("outsider","order_chat",{"order_id":"eq."+str(oid),"select":"id"})==[],"outsider read foreign chat")
  require(a.rows("other_driver","order_chat",{"order_id":"eq."+str(oid),"select":"id"})==[],"unassigned driver read foreign chat")
  require(snapshot()==before,"unauthorized RPC attempts changed order/ticket/message")
 check("E13_authz_matrix",E13)
 require(len(passed)==len(SCENARIOS),"gate count mismatch: "+str(len(passed))+"/"+str(len(SCENARIOS)))
 print("GATE1_E2E:",len(passed),"/",len(SCENARIOS),"LOCAL HTTP PASS",flush=True)
if __name__=="__main__":
 try: run()
 except Exception as e:
  print("FAIL local-only E2E:",str(e),file=sys.stderr);raise SystemExit(1)
