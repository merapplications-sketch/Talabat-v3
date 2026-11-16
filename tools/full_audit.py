#!/usr/bin/env python3
"""BRIEF-14 visual audit of THE ORIGINAL four TALABOT HTML applications, not synthetic DOM.
Two clearly separate evidence modes:
  A) real HTML/JS/CSS pages with an exhaustive synthetic READ-ONLY data-adapter (offline);
  B) identical original pages authenticated against disposable LOCAL Supabase (when available).
No real/cloud endpoint is permitted. Found defects are RECORDED, never silently corrected.
"""
import os, json, re, time, sys, pathlib, threading, http.server, functools, hashlib
from playwright.sync_api import sync_playwright
from qa_all import FIX, CHECK, APPS, EMPTY

ROOT=pathlib.Path(__file__).resolve().parents[1]
OUT=ROOT/"qa-shots"/"full-audit"
OUT.mkdir(parents=True, exist_ok=True)
PORT=18765
LOCAL="http://127.0.0.1:"+str(PORT)
BACKEND="http://127.0.0.1:54321"
WIDTHS=[(375,667),(390,844),(430,932)]
LANGS=["ru","en"]
APPS4=["customer","driver","merchant","admin"]
REPORT={"source":"ORIGINAL HTML and JS/CSS from this exact Git commit; no fixture DOM", "backend_modes":
  {"rich":"real app render with existing synthetic read-only Supabase adapter (NOT server E2E)",
   "local":"original application with ephemeral locally signed Supabase user and real 127.0.0.1 database"},
 "browser":"Playwright WebKit (Linux emulated iPhone widths, NOT iOS Safari)",
 "keyboard":"visual viewport height reduction; NOT physical software keyboard",
 "no_fixes":True,"screenshots":[],"findings":[],"coverage":[],"blocked_remote_requests":[]}
LIMIT=int(os.environ.get("FULL_AUDIT_LIMIT","1000"))
MAX_ISSUES_PER_SHOT=15
SHOTS=0
def slug(s):
    return re.sub(r'[^a-zA-Z0-9_-]','-',str(s)).strip('-')[:70] or "screen"
def record(app,screen,lang,w,kind,details,severity="P2",mode="rich"):
    REPORT["findings"].append({"app":app,"screen":screen,"lang":lang,"width":w,
        "type":kind,"severity":severity,"detail":str(details)[:350],"backend_mode":mode})
def capture(pg,app,screen,lang,w,mode="rich",keyboard=False):
    global SHOTS
    if SHOTS>=LIMIT:return
    path=OUT/app/(slug(screen)+"_"+lang+"_"+str(w)+("_kbd" if keyboard else "")+("_local" if mode=="local" else "")+".png")
    path.parent.mkdir(parents=True,exist_ok=True)
    try:
        pg.screenshot(path=str(path),animations="disabled",timeout=12000)
        SHOTS+=1
        REPORT["screenshots"].append({"app":app,"screen":screen,"lang":lang,"width":w,"mode":mode,
             "keyboard_sim":keyboard,"path":str(path.relative_to(ROOT))})
    except Exception as exc:
        record(app,screen,lang,w,"SCREENSHOT_ERROR",str(exc),"P1",mode)
def issue_checks(pg,app,screen,lang,w,mode="rich",keyboard=False):
    try:
        # Source-backed audit from existing tools/qa_all.py (text overlap, clipping, raw tokens).
        prior=pg.evaluate(CHECK,"top")
        for msg in prior[:MAX_ISSUES_PER_SHOT]:
            sev="P1" if any(k in msg for k in ("TEXT-OVERLAP","COVERED","OUT-X","PAGE-OVERFLOW","BAD")) else "P2"
            record(app,screen,lang,w,msg.split(" ",1)[0],msg,sev,mode)
    except Exception as exc:
        record(app,screen,lang,w,"CHECK_ENGINE_ERROR",str(exc),"P1",mode)
    try:
        dom=pg.evaluate("""() => {
          const W=innerWidth,H=innerHeight, vv=window.visualViewport;
          const visible=e=>{const s=getComputedStyle(e),r=e.getBoundingClientRect();return s.display!=='none'&&s.visibility!=='hidden'&&r.width>0&&r.height>0&&r.bottom>=0&&r.top<=H};
          const rect=e=>{const r=e.getBoundingClientRect();return {x:r.left,y:r.top,right:r.right,bottom:r.bottom,width:r.width,height:r.height}};
          const out={width:W,height:H,vh:vv?vv.height:H,scrollWidth:document.documentElement.scrollWidth,
            touches:[],clipped:[],invalid:[],raw:[],mix:[],contrast:[],focus:null};
          const rgb=x=>{const m=String(x).match(/rgba?\\(([^)]+)\\)/);if(!m)return null;const v=m[1].match(/[\\d.]+/g)?.map(Number);return v&&v.length>=3?v:null};
          const luma=c=>{const v=c.slice(0,3).map(x=>x/255).map(x=>x<=.04045?x/12.92:Math.pow((x+.055)/1.055,2.4));return .2126*v[0]+.7152*v[1]+.0722*v[2]};
          const background=e=>{for(let a=e;a;a=a.parentElement){const c=rgb(getComputedStyle(a).backgroundColor);if(c&&(c.length<4||c[3]>.98))return c;}return [255,255,255]};
          for(const el of [...document.querySelectorAll('h1,h2,h3,h4,button,label,p,span,small,td,th')].filter(visible).slice(0,170)){
             const t=(el.innerText||'').trim();if(!t||t.length>90)continue;
             const color=rgb(getComputedStyle(el).color),bg=background(el);if(!color)continue;
             const a=luma(color),b=luma(bg),ratio=(Math.max(a,b)+.05)/(Math.min(a,b)+.05);
             if(ratio<4.5)out.contrast.push({text:t.slice(0,40),ratio:Math.round(ratio*100)/100});
          }
          if(out.scrollWidth>W+1)out.clipped.push({kind:'HORIZONTAL_OVERFLOW',delta:out.scrollWidth-W});
          const candidates=[...document.querySelectorAll('button,a[href],input:not([type=hidden]),select,textarea,[role=button]')].filter(visible);
          for(const e of candidates.slice(0,220)){
            const r=rect(e),s=getComputedStyle(e);
            const label=(e.getAttribute('aria-label')||e.innerText||e.id||e.tagName).trim().slice(0,70);
            if(r.right>W+1||r.x<-1)out.clipped.push({kind:'CONTROL_OUTSIDE_VIEWPORT',label,rect:r});
            if(r.width<44||r.height<44)out.touches.push({label,w:Math.round(r.width),h:Math.round(r.height)});
            let a=e.parentElement;while(a&&a!==document.body){
              const ov=getComputedStyle(a);const clip=/(auto|hidden|scroll|clip)/.test(ov.overflowY);
              if(clip){const ar=a.getBoundingClientRect(),inter=Math.min(r.bottom,ar.bottom)-Math.max(r.y,ar.top);
                if(inter>2&&inter<r.height-2){out.clipped.push({kind:'PARTIAL_CONTROL_CLIP',label,visibleH:Math.round(inter),fullH:Math.round(r.height)});break}}
              a=a.parentElement;
            }
          }
          const bad=/(?:\\bundefined\\b|\\bNaN\\b|\\bnull\\b|\\[object Object\\])/;
          for(const e of [...document.querySelectorAll('h1,h2,h3,h4,label,button,[role=tab],.card')].filter(visible).slice(0,180)){
            const txt=(e.innerText||'').trim();if(!txt||txt.length>360)continue;
            if(bad.test(txt)||txt==='—'||txt==='--')out.invalid.push(txt.slice(0,70));
            if(/\\bord\\d+\\b/i.test(txt)||/\\b[0-9a-f]{8}-[0-9a-f]{4}-[1-8][0-9a-f]{3}-[89ab][0-9a-f]{3}-[0-9a-f]{12}\\b/i.test(txt))
              out.raw.push(txt.slice(0,90));
            const lg=window.__AUDIT_LANG;
            if(lg==='ru'&&/\\b(?:Step [1-4] of 4|Cash received|Confirm amount|Take in cash|Order updated|Mark as read|Loading orders)\\b/i.test(txt))out.mix.push(txt.slice(0,90));
            if(lg==='en'&&/\\b(?:Шаг [1-4] из 4|Возьмите наличными|Подтвердить сумму|Подождите ответа)\\b/i.test(txt))out.mix.push(txt.slice(0,90));
          }
          const f=document.activeElement;
          if(f&&['INPUT','TEXTAREA','SELECT'].includes(f.tagName)){
            const r=rect(f),s=getComputedStyle(f),outline=parseFloat(s.outlineWidth)||0;
            out.focus={rect:r,outline,visible:r.y>=-1&&r.bottom<=out.vh+2};
          }
          return out;
        }""")
        for it in dom["clipped"][:7]: record(app,screen,lang,w,it["kind"],json.dumps(it,ensure_ascii=False),"P1",mode)
        for it in dom["touches"][:7]: record(app,screen,lang,w,"TAP_TARGET_LT44",json.dumps(it,ensure_ascii=False),"P2",mode)
        for it in dom["invalid"][:6]:record(app,screen,lang,w,"BAD_VALUE",it,"P1",mode)
        for it in dom["raw"][:6]:record(app,screen,lang,w,"RAW_IDENTIFIER",it,"P1",mode)
        for it in dom["mix"][:6]:record(app,screen,lang,w,"MIXED_LANGUAGE",it,"P1",mode)
        for it in dom["contrast"][:7]:record(app,screen,lang,w,"CONTRAST_LT4_5",json.dumps(it,ensure_ascii=False),"P2",mode)
        if keyboard and dom["focus"] and not dom["focus"]["visible"]:
            record(app,screen,lang,w,"KEYBOARD_FOCUS_HIDDEN",json.dumps(dom["focus"]),"P1",mode)
    except Exception as exc:
        record(app,screen,lang,w,"DOM_CHECK_ERROR",str(exc),"P1",mode)
def block_remote(route):
    u=route.request.url
    if u.startswith("data:") or u.startswith("blob:") or u.startswith(LOCAL+"/"):
        return route.continue_()
    REPORT["blocked_remote_requests"].append(u.split("?")[0][:180])
    route.abort("blockedbyclient")
def start_server():
    class Quiet(http.server.SimpleHTTPRequestHandler):
        def log_message(self,*a):pass
    srv=http.server.ThreadingHTTPServer(("127.0.0.1",PORT),lambda *a,**kw:Quiet(*a,directory=str(ROOT),**kw))
    threading.Thread(target=srv.serve_forever,daemon=True).start()
    return srv
def make_context(browser,app,lang,w,h,empty=False):
    ctx=browser.new_context(viewport={"width":w,"height":h},device_scale_factor=2,is_mobile=True,has_touch=True,
         locale="ru-RU" if lang=="ru" else "en-US")
    ctx.add_init_script("window.__AUDIT_LANG="+json.dumps(lang)+";localStorage.setItem('tlb_lang',"+json.dumps(lang)+");"+("window.__EMPTY=true;" if empty else ""))
    # Offline adapter is only substituted for Supabase CDN; ALL actual TALABOT HTML/JS/CSS are original.
    def route(req):
        if "supabase-js" in req.request.url and "cdn" in req.request.url:
            req.fulfill(status=200,content_type="application/javascript",body=FIX.replace("window.__ROLE",json.dumps(app)))
        else:block_remote(req)
    ctx.route("**/*",route)
    return ctx
def check_sequence(browser,app,lang,w,h,empty=False):
    ctx=make_context(browser,app,lang,w,h,empty)
    pg=ctx.new_page()
    errors=[]
    pg.on("pageerror",lambda e:errors.append(str(e)[:300]))
    pg.goto(LOCAL+"/"+app+".html",wait_until="domcontentloaded",timeout=22000)
    if not empty:
        capture(pg,app,"loading_or_initial",lang,w)
        issue_checks(pg,app,"loading_or_initial",lang,w)
    pg.wait_for_timeout(650)
    seq=(EMPTY.get(app,[]) if empty else APPS.get(app,[]))
    if app=="admin":
        n=pg.locator(".tabs button").count()
        seq=[("tab"+str(i),"document.querySelectorAll('.tabs button')["+str(i)+"].click()") for i in range(n)]
        if not empty:seq+= [("loyalty_editor","tab='y';HE=null;heOpen()")]
    for screen,expr in seq:
        mode=("empty_" if empty else "")+screen
        try:
            pg.evaluate("() => {"+expr+";if(typeof render==='function')render()}") 
            pg.wait_for_timeout(90)
        except Exception as e:
            record(app,mode,lang,w,"SCENARIO_UNAVAILABLE",str(e),"P2")
            continue
        pg.evaluate("() => window.scrollTo(0,0)")  # baseline screenshot always starts at top of actual app
        pg.wait_for_timeout(30)
        capture(pg,app,mode,lang,w)
        issue_checks(pg,app,mode,lang,w)
        REPORT["coverage"].append({"app":app,"screen":mode,"lang":lang,"width":w,"mode":"rich"})
        if not empty and screen in ("pay","cart","addrForm","item-sheet","ticket","profile","reject-sheet","menu","wallet"):
            target=pg.locator('input:not([type=hidden]):visible,textarea:visible').first
            if target.count():
                try:
                    target.focus(timeout=1200)
                    pg.set_viewport_size({"width":w,"height":max(300,h-280)})
                    pg.wait_for_timeout(120)
                    capture(pg,app,screen,lang,w,keyboard=True)
                    issue_checks(pg,app,screen+"_kbd",lang,w,keyboard=True)
                    pg.set_viewport_size({"width":w,"height":h})
                    target.blur(timeout=1000)
                except Exception as e:record(app,screen,lang,w,"KEYBOARD_CASE_UNAVAILABLE",str(e),"P2")
    if not empty:
        try:
            pg.evaluate("() => window.dispatchEvent(new Event('offline'))")
            pg.wait_for_timeout(170)
            capture(pg,app,"offline",lang,w)
            issue_checks(pg,app,"offline",lang,w)
            REPORT["coverage"].append({"app":app,"screen":"offline","lang":lang,"width":w,"mode":"rich"})
            pg.evaluate("() => window.dispatchEvent(new Event('online'))")
        except Exception as exc:record(app,"offline",lang,w,"OFFLINE_CASE_UNAVAILABLE",str(exc),"P2")
    if errors:record(app,"global",lang,w,"JAVASCRIPT_ERROR"," | ".join(errors[:4]),"P1")
    ctx.close()
def use_real_local_backend(browser,app,lang,w,h,fixture,js):
    """H-01: actual original app + ephemeral real LOCAL Supabase login via UI.
    No fabricated refresh token, no production network or printed password."""
    role=app
    entry=fixture.get("roles",{}).get(role) or {}
    if not entry.get("audit_email") or not entry.get("audit_password"):
        record(app,"local_auth",lang,w,"H01_LOCAL_CREDENTIAL_MISSING","ephemeral local test credential absent","P0","local")
        return
    ctx=browser.new_context(viewport={"width":w,"height":h},device_scale_factor=2,is_mobile=True,has_touch=True,
        locale="ru-RU" if lang=="ru" else "en-US")
    ctx.add_init_script("window.__AUDIT_LANG="+json.dumps(lang)+
        ";localStorage.setItem('tlb_lang',"+json.dumps(lang)+");")
    def handle(route):
        u=route.request.url
        if u.startswith(LOCAL+"/talabat-core.js"):
            core=(ROOT/"talabat-core.js").read_text("utf8")
            # H-01: use a strictly same-origin, loopback-only proxy to avoid iOS/WebKit
            # cross-port CORS/preflight failures. Only disposable LOCAL Supabase is reachable.
            core=core.replace("https://dzydscryrnahnneydnry.supabase.co",LOCAL+"/__audit_sb")
            core=core.replace("sb_publishable_zQKbsSffub7O-f87vsXAaQ_GHFnSOQz",
                              os.environ["SUPABASE_LOCAL_ANON_KEY"])
            route.fulfill(status=200,content_type="application/javascript",body=core)
        elif "supabase-js" in u and "cdn" in u:
            route.fulfill(status=200,content_type="application/javascript",body=js)
        elif u.startswith(LOCAL+"/__audit_sb/"):
            # Never forward browser requests to any production endpoint. Only a
            # fixed allowlist of the disposable loopback Supabase API namespaces.
            import urllib.request, urllib.error, urllib.parse
            rest=u.split(LOCAL+"/__audit_sb/",1)[1]
            api=rest.split("/",1)[0]
            if api not in ("auth","rest","storage","realtime") or ".." in rest or "://" in rest:
                route.abort("blockedbyclient")
                return
            target=BACKEND+"/"+rest
            req=route.request
            allowed=("apikey","authorization","content-type","prefer","accept","x-client-info","x-supabase-api-version")
            headers={k:v for k,v in req.headers.items() if k.lower() in allowed}
            body=req.post_data_buffer
            outbound=urllib.request.Request(target,data=body,headers=headers,method=req.method)
            opener=urllib.request.build_opener(urllib.request.ProxyHandler({}),
                type("NoRedirect",(urllib.request.HTTPRedirectHandler,),{
                    "redirect_request":lambda self,*args,**kwargs:None})())
            try:
                with opener.open(outbound,timeout=12) as reply:
                    reply_body=reply.read(2_500_000)
                    route.fulfill(status=reply.status,headers={
                      "content-type":reply.headers.get("content-type","application/json"),
                      "cache-control":"no-store"},body=reply_body)
            except urllib.error.HTTPError as err:
                route.fulfill(status=err.code,headers={"content-type":"application/json",
                    "cache-control":"no-store"},body=err.read(2_500_000))
            except Exception:
                route.abort("failed")
        elif u.startswith(LOCAL+"/") or u.startswith("data:") or u.startswith("blob:"):
            route.continue_()
        else: block_remote(route)
    ctx.route("**/*",handle)
    pg=ctx.new_page();errors=[];bad=[]
    pg.on("pageerror",lambda e:errors.append(str(e)[:180]))
    pg.on("requestfailed",lambda r:bad.append({"net":"failed",
       "route":r.url.split("?")[0].split("/")[-1][:55],
       "failure":r.failure[:70] if r.failure else "unknown"})
       if r.url.startswith(LOCAL+"/__audit_sb/") else None)
    pg.on("response",lambda r:bad.append({"status":r.status,"route":r.url.split("?")[0].split("/")[-1][:50]})
          if r.status>=400 and r.url.startswith(BACKEND+"/") else None)
    try:
        pg.goto(LOCAL+"/"+app+".html",wait_until="domcontentloaded",timeout=16000)
        pg.locator("#tlb-em").wait_for(state="visible",timeout=20000)
        capture(pg,app,"local_login",lang,w,mode="local")
        issue_checks(pg,app,"local_login",lang,w,mode="local")
        REPORT["coverage"].append({"app":app,"screen":"local_login","lang":lang,"width":w,"mode":"local"})
        pg.locator("#tlb-em").fill(entry["audit_email"])
        pg.locator("#tlb-pw").fill(entry["audit_password"])
        pg.locator("#tlb-go").click()
        pg.wait_for_function("""() => !document.getElementById('tlb-boot') &&
           !document.getElementById('tlb-ov') && !!document.getElementById('app')?.textContent.trim()
           && TLB.me()?.role===location.pathname.slice(1,-5)""",timeout=30000)
        capture(pg,app,"local_authenticated",lang,w,mode="local")
        issue_checks(pg,app,"local_authenticated",lang,w,mode="local")
        REPORT["coverage"].append({"app":app,"screen":"local_authenticated","lang":lang,"width":w,"mode":"local"})
        pg.evaluate("(l)=>TLB.setLang(l)",lang)
        pg.wait_for_timeout(180)
        capture(pg,app,"local_lang",lang,w,mode="local")
        issue_checks(pg,app,"local_lang",lang,w,mode="local")
        REPORT["coverage"].append({"app":app,"screen":"local_lang","lang":lang,"width":w,"mode":"local"})
        REPORT.setdefault("local_auth_verified",[]).append({"app":app,"width":w,"lang":lang,"ready":True})
    except Exception as e:
        state=pg.evaluate("""() => ({
          boot:!!document.getElementById('tlb-boot'),overlay:!!document.getElementById('tlb-ov'),
          login:!!document.getElementById('tlb-em'),
          err:(document.getElementById('tlb-er')?.textContent||'').slice(0,60)
        })""")
        record(app,"local_authenticated",lang,w,"H01_AUTH_NOT_READY",
               json.dumps({"state":state,"statusCodes":bad[:4],"jsErrors":errors[:2],
                           "errorType":type(e).__name__},ensure_ascii=False),"P0","local")
        pg.evaluate("""() => {document.querySelectorAll('input[type=email],input[type=password]').forEach(x=>x.value='')}""")
        capture(pg,app,"local_auth_blocked",lang,w,mode="local")
    if errors:record(app,"local_auth",lang,w,"LOCAL_JAVASCRIPT_ERROR","; ".join(errors[:2]),"P1","local")
    ctx.close()

def f10_classify_source_ids():
    """F-10: `ord0` is synthetic QA fixture ONLY; real order IDs are PostgreSQL bigint.
    No admin display/URL rewrite of server-generated IDs is permitted based on fake data."""
    import re
    admin=(ROOT/"admin.html").read_text("utf8")
    schema=(ROOT/"sql/baseline/schema_baseline_dzydscryrnahnneydnry_20261116.sql").read_text("utf8")
    assert not re.search(r"\\bord[0-9]+\\b",admin), "F-10 raw synthetic order ID hardcoded in production admin"
    assert re.search(r'CREATE TABLE IF NOT EXISTS "public"\\."orders"\\s*\\(\\s*"id" bigint NOT NULL',schema)
    assert "id:'ord'+i" in (ROOT/"tools/qa_all.py").read_text("utf8")
    REPORT.setdefault("triage",{})["F-10"]={
      "classification":"synthetic-fixture noise",
      "evidence":"qa_all.py creates ord0..ord6, baseline production orders.id is bigint, admin.html has no hardcoded ord0",
      "production_change":"none"}
    print("F10_REAL_ORDER_IDS_NOT_FIXTURE PASS: bigint SQL; ord* only synthetic",flush=True)

def main():
    if os.environ.get("SUPABASE_LOCAL_URL")!=BACKEND:
        raise SystemExit("STOP: FULL AUDIT requires disposable Supabase on loopback, not cloud.")
    if os.environ.get("SUPABASE_PROJECT_REF") or os.environ.get("DATABASE_URL") or os.environ.get("SUPABASE_ACCESS_TOKEN"):
        raise SystemExit("STOP: foreign/remote credential detected.")
    print("FULL_AUDIT real original HTML WebKit; synthetic read-only + disposable LOCAL backend; never remote")
    f10_classify_source_ids()
    server=start_server()
    try:
        with sync_playwright() as pw:
            browser=pw.webkit.launch(headless=True)
            # Comprehensive USER INTERFACE state explorer using ORIGINAL app pages and full synthetic dataset.
            if os.environ.get("FULL_AUDIT_MODE","full")!="auth_only":
                for w,h in WIDTHS:
                    for lang in LANGS:
                        for app in APPS4:
                            check_sequence(browser,app,lang,w,h,empty=False)
                        # Deliberately keep empty-state coverage explicit; do not manufacture success.
                            if app in ("customer","driver","merchant","admin"):
                                check_sequence(browser,app,lang,w,h,empty=True)
            fixture_path=os.environ.get("GATE1_TEST_FIXTURE_PATH")
            npm=os.environ.get("FULL_AUDIT_SUPABASE_UMD")
            if not fixture_path or not pathlib.Path(fixture_path).is_file():
                record("all","local","all",0,"LOCAL_FIXTURE_MISSING","No ephemeral local identities","P1","local")
            elif not npm or not pathlib.Path(npm).is_file():
                record("all","local","all",0,"LOCAL_SUPABASE_JS_MISSING","UMD unavailable","P1","local")
            else:
                fixture=json.loads(pathlib.Path(fixture_path).read_text("utf8"))
                assert fixture.get("synthetic_only") and fixture.get("origin")==BACKEND
                js=pathlib.Path(npm).read_text("utf8")
                for w,h in WIDTHS:
                    for lang in LANGS:
                        for app in APPS4:
                            try:use_real_local_backend(browser,app,lang,w,h,fixture,js)
                            except Exception as e:record(app,"local_auth",lang,w,"LOCAL_BACKEND_RUNTIME_ERROR",str(e),"P1","local")
            browser.close()
    finally:
        server.shutdown()
    # Only screenshots with locally constructed synthetic data may be committed.
    verified=len(REPORT.get("local_auth_verified",[]))
    if verified!=24:
        record("all","H-01","all",0,"H01_AUTH_COVERAGE_BLOCKED",
               "Expected 24 original-app real LOCAL authenticated views, got "+str(verified),"P0","local")
    print("H01_LOCAL_AUTHENTICATED "+str(verified)+"/24",flush=True)
    REPORT["counts"]={"screenshots":SHOTS,"cases":len(REPORT["coverage"]),
      "findings":len(REPORT["findings"]),"by_type":{},"by_app":{}}
    for row in REPORT["findings"]:
        kind=row["type"];app=row["app"]
        REPORT["counts"]["by_type"][kind]=REPORT["counts"]["by_type"].get(kind,0)+1
        REPORT["counts"]["by_app"][app]=REPORT["counts"]["by_app"].get(app,0)+1
    REPORT["blocked_remote_requests"]=sorted(set(REPORT["blocked_remote_requests"]))[:70]
    (OUT/"FINDINGS.json").write_text(json.dumps(REPORT,ensure_ascii=False,indent=2),encoding="utf8")
    idx=["# TALABOT BRIEF-14 — FULL APPLICATION AUDIT","",
         "Real original HTML/JS/CSS pages; evidence distinguishes read-only synthetic-data adapter vs disposable LOCAL Supabase-authenticated pages.",
         "WebKit on Linux at 375/390/430 RU/EN, reduced viewport simulates keyboard — NOT physical iPhone.",
         "Evidence only. No production, no application fixes. **No finding is automatically approved or closed.**","",
         "## Totals","",
         f"- Screenshots: {SHOTS}",f"- Cases: {len(REPORT['coverage'])}",f"- Findings: {len(REPORT['findings'])}",
         f"- Apps: {', '.join(APPS4)}", "", "## Findings by type",""]
    for k,v in sorted(REPORT["counts"]["by_type"].items(),key=lambda x:-x[1]):idx.append(f"- {k}: {v}")
    idx+=["","## Screenshot index",""]
    for row in REPORT["screenshots"]:
        rel=row["path"].split("qa-shots/full-audit/",1)[1]
        idx.append(f"- [{row['app']} · {row['screen']} · {row['lang']} · {row['width']} · {row['mode']}]({rel})")
    (OUT/"INDEX.md").write_text("\n".join(idx)+"\n",encoding="utf8")
    print("FULL_APP_AUDIT screenshots="+str(SHOTS)+" cases="+str(len(REPORT["coverage"]))+" findings="+str(len(REPORT["findings"])),flush=True)
    print("FULL_APP_AUDIT_BY_TYPE "+json.dumps(REPORT["counts"]["by_type"],ensure_ascii=False),flush=True)
    # Audit should return nonzero if P1/P2 findings: CI remains NO-GO, yet evidence is still committed.
    return 2 if REPORT["findings"] else 0
if __name__=="__main__":
    sys.exit(main())
