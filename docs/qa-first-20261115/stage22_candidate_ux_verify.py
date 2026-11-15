"""Stage22 candidate-only synthetic UX acceptance, no production mutation.
The browser loads the public unchanged Pages site, while only demo-guard.js is
replaced IN MEMORY from the pinned programmer source commit. No deployment.
"""
import asyncio
import hashlib
import json
import os
import subprocess
import ssl
from pathlib import Path
from urllib.parse import urlsplit
from urllib.request import HTTPRedirectHandler, HTTPSHandler, Request, build_opener
from playwright.async_api import async_playwright

HOST = "talabot-safari-demo-20261115.pages.dev"
BASE = "https://" + HOST
CANDIDATE = "8e78d2df86e55326427009beea0d637414123707"
EXPECTED_GIT_BLOB = "097ec62adec0d88d2752b92cd0f4398a2a3aff8c"
ORIGINAL_HOST_ROOT_SHA256 = "2c74b7af8b8d1cdad0d3ce446ad2591703088e17948f2ba6636a83d7795466b2"
ORIGINAL_HOST_GUARD_SHA256 = "8d19a5a9d251b30202a9f6cb9d4703df67b2e862885ab5fbac4b86ec2c7892d4"
path = Path("candidate/previews/safari-zero-cost-customer/demo-guard.js")
output = Path("stage22-candidate-verification")
output.mkdir(exist_ok=True)
report = {
    "scope": "synthetic-only candidate browser overlay for EN option labels; not a published update",
    "candidate_commit": CANDIDATE,
    "runner_commit": os.getenv("GITHUB_SHA"),
    "status": "IN_PROGRESS",
    "hosted_root_sha256": None,
    "hosted_original_guard_sha256": None,
    "candidate_guard_blob": None,
    "candidate_overlay_count": 0,
    "images": [],
    "en": {},
    "ru": {},
    "en_restored": {},
    "cart": {},
    "network": {"requests": [], "responses": [], "failed": [], "external_attempts": [], "ws_attempts": [], "pageerrors": []},
    "screenshots": [],
    "har": {"state": "NOT_FINALIZED"}
}

def require(test, reason):
    if not test:
        raise RuntimeError(reason)

def on_site(url):
    q = urlsplit(url)
    return q.scheme == "https" and q.hostname == HOST and q.port in (None,443) and not q.username and not q.password

def scrub(url):
    q=urlsplit(url)
    return (q.hostname or "?") + (q.path or "/")

def git(*args):
    return subprocess.check_output(["git","-C","candidate",*args],text=True,stderr=subprocess.STDOUT).strip()

class NoRedirect(HTTPRedirectHandler):
    def redirect_request(self, req, fp, code, msg, headers, url):
        raise RuntimeError("UNEXPECTED_ORIGIN_REDIRECT")

def preflight():
    require(os.getenv("GITHUB_ACTIONS")=="true","NOT_GITHUB_QA_RUN")
    require(os.getenv("GITHUB_REPOSITORY")=="merapplications-sketch/Talabat-v3","WRONG_REPO")
    require(os.getenv("GITHUB_REF")=="refs/heads/review/stage22-one-shot-qa-20261115","WRONG_BRANCH")
    require(git("rev-parse","HEAD")==CANDIDATE,"CANDIDATE_COMMIT_NOT_PINNED")
    require(path.is_file(),"CANDIDATE_GUARD_MISSING")
    raw=path.read_bytes()
    blob=subprocess.check_output(["git","hash-object",str(path)],text=True).strip()
    report["candidate_guard_blob"]=blob
    require(blob==EXPECTED_GIT_BLOB,"CANDIDATE_GUARD_BLOB_UNEXPECTED")
    require(b"__TALABOT_SYNTHETIC" in raw and b"demoEnGroups" in raw,"SYNTHETIC_GUARD_REQUIRED")
    opener=build_opener(NoRedirect(),HTTPSHandler(context=ssl.create_default_context()))
    for endpoint,sha in [("/",ORIGINAL_HOST_ROOT_SHA256),("/demo-guard.js",ORIGINAL_HOST_GUARD_SHA256)]:
        with opener.open(Request(BASE+endpoint,headers={"User-Agent":"Stage22-readonly-compare"}),timeout=20) as r:
            require(r.status==200,"LIVE_HOST_NOT_200")
            actual=hashlib.sha256(r.read(1000000)).hexdigest()
        require(actual==sha,"PUBLISHED_SITE_CHANGED_STOP")
        if endpoint=="/":report["hosted_root_sha256"]=actual
        else: report["hosted_original_guard_sha256"]=actual
    return raw

def persist():
    (output/"candidate-result.json").write_text(json.dumps(report,ensure_ascii=False,indent=2),encoding="utf-8")
    n=report["network"]
    print("STAGE22_CANDIDATE_BEGIN",flush=True)
    summary={k:v for k,v in report.items() if k not in ("network","images")}
    summary["network_summary"]={"requests":len(n["requests"]),"responses":len(n["responses"]),
      "failed":n["failed"][:8],"external_attempts":n["external_attempts"],"ws_attempts":n["ws_attempts"],
      "pageerrors":n["pageerrors"]}
    print(json.dumps(summary,ensure_ascii=False)[:24000],flush=True)
    print("STAGE22_CANDIDATE_END",flush=True)

def sanitized_har(p):
    if not p.is_file():
        report["har"]={"state":"MISSING"}
        return
    j=json.loads(p.read_text(encoding="utf-8"))
    entries=j.get("log",{}).get("entries",[])
    for e in entries:
        for kind in ("request","response"):
            q=e.get(kind,{})
            q["headers"]=[v for v in q.get("headers",[]) if v.get("name","").lower() not in
              ("authorization","cookie","set-cookie","proxy-authorization")]
            for f in ("cookies","postData","queryString"):q.pop(f,None)
            if kind=="response":
                q.get("content",{}).pop("text",None)
                q.get("content",{}).pop("encoding",None)
    dst=output/"candidate-redacted.har"
    dst.write_text(json.dumps(j,ensure_ascii=False),encoding="utf-8")
    report["har"]={"state":"FINALIZED","entries":len(entries),"sha256":hashlib.sha256(dst.read_bytes()).hexdigest()}
    p.unlink()
    require(len(entries)>0,"ZERO_CANDIDATE_HAR_ENTRIES")

async def main():
    candidate_guard=preflight()
    async with async_playwright() as pw:
        browser=await pw.chromium.launch(headless=True)
        ctx=None
        try:
            ctx=await browser.new_context(viewport={"width":320,"height":844},
              service_workers="block",accept_downloads=False,
              record_har_path=str(output/"raw.har"))
            async def route(rt):
                u=rt.request.url
                if not on_site(u):
                    report["network"]["external_attempts"].append(scrub(u))
                    await rt.abort("blockedbyclient")
                    return
                if urlsplit(u).path=="/demo-guard.js":
                    require(rt.request.method=="GET","UNEXPECTED_GUARD_WRITE")
                    report["candidate_overlay_count"]+=1
                    await rt.fulfill(status=200,body=candidate_guard,content_type="application/javascript",
                      headers={"Cache-Control":"no-store","X-Content-Type-Options":"nosniff"})
                else:
                    await rt.continue_()
            await ctx.route("**/*",route)
            require(hasattr(ctx,"route_web_socket"),"WS_GUARD_MISSING")
            async def ws(rt):
                report["network"]["ws_attempts"].append(scrub(rt.url))
                await rt.close()
            await ctx.route_web_socket("**/*",ws)
            page=await ctx.new_page()
            page.on("request",lambda r:report["network"]["requests"].append({"url":scrub(r.url),"method":r.method}))
            page.on("response",lambda r:report["network"]["responses"].append({"url":scrub(r.url),"status":r.status}))
            page.on("requestfailed",lambda r:report["network"]["failed"].append({"url":scrub(r.url),"error":str(r.failure)}))
            page.on("pageerror",lambda e:report["network"]["pageerrors"].append(str(e)[:350]))
            r=await page.goto(BASE+"/?lang=en",wait_until="load",timeout=30000)
            require(r is not None and r.status==200,"SYNTHETIC_SITE_PAGE_NOT_READY")
            await page.wait_for_timeout(300)
            require(report["candidate_overlay_count"]==1,"CANDIDATE_OVERLAY_NOT_EXECUTED_ON_REAL_SITE")

            # Exact real storefront fixture. Opening its sheet only reads synthetic data.
            opened=await page.evaluate("""() => {
              if(!(window.__TALABOT_SYNTHETIC===true && window.TLB && typeof openItem==='function')) return false;
              const st=STORES.find(x=>menuOf(x.n).some(it=>it.id==='i1'));
              if(!st) return false;
              S.store=st.n;S.v='menu';render();openItem('i1');
              return !!document.querySelector('.sheet.d6s');
            }""")
            require(opened,"PRODUCT_SHEET_NOT_RENDERED")
            en=await page.evaluate("""() => ({
              lang:TLB.lang(),
              labels:[...document.querySelectorAll('.sheet.d6s .og h3')].map(n=>n.innerText),
              choices:[...document.querySelectorAll('.sheet.d6s .d6-ch .nm')].map(n=>n.innerText),
              sourceGroups:TLB.optionsOf('i1',true).map(g=>({
                id:g.id,required:g.required,max:g.max,options:g.options.map(o=>({id:o.id,price:o.price,available:o.available}))
              })),
              optText:optTxt('i1',['o10','o21']),
              enabled:!!window.TLB.placeOrder && String(TLB.placeOrder).includes('__demoBlockedActions'),
              blockedActions:window.__demoBlockedActions,
              docOverflow:document.documentElement.scrollWidth>document.documentElement.clientWidth+1
            })""")
            report["en"]=en
            require(en["lang"]=="en","WRONG_EN_LANG")
            require(en["labels"]==["Portion size (required)","Add-ons"],"EN_GROUP_LABELS_NOT_CORRECT")
            require(en["choices"]==["Small","Medium","Large","Cheese","Bacon","Jalapeño","Sauce"],
                "EN_OPTION_CHOICES_NOT_CORRECT")
            require(en["optText"]=="Small, Bacon","EN_CART_OPTION_DISPLAY_NOT_CORRECT")
            require(en["enabled"] and en["blockedActions"]==0 and not en["docOverflow"],
                "GUARD_OR_EN_LAYOUT_REGRESSION")
            await page.screenshot(path=str(output/"candidate-en-customization-320.png"),
              full_page=False,animations="disabled")
            report["screenshots"].append("candidate-en-customization-320.png")

            # Toggle the real synthetic language setting and render again: no page reload, same IDs and prices.
            ru=await page.evaluate("""() => {
              TLB.setLang('ru');render();
              return {
                lang:TLB.lang(),
                labels:[...document.querySelectorAll('.sheet.d6s .og h3')].map(n=>n.innerText),
                choices:[...document.querySelectorAll('.sheet.d6s .d6-ch .nm')].map(n=>n.innerText),
                sourceGroups:TLB.optionsOf('i1',true).map(g=>({
                  id:g.id,required:g.required,max:g.max,options:g.options.map(o=>({id:o.id,price:o.price,available:o.available}))
                })),
                optText:optTxt('i1',['o10','o21']),
                blockedActions:window.__demoBlockedActions
              };
            }""")
            report["ru"]=ru
            require(ru["lang"]=="ru","RUSSIAN_TOGGLE_NOT_APPLIED")
            require(ru["labels"]==["Размер порции (обязательно выбрать)","Добавки"],"RU_GROUPS_CHANGED")
            require(ru["choices"]==["Маленький","Средний","Большой","Сыр","Бекон","Халапеньо","Соус"],
                "RU_OPTION_FIXTURE_CHANGED")
            require(ru["optText"]=="Маленький, Бекон","RU_CART_DISPLAY_CHANGED")
            require(ru["sourceGroups"]==en["sourceGroups"],"GROUP_ID_PRICE_OR_MAX_REGRESSION")
            require(ru["blockedActions"]==0,"UNEXPECTED_DEMO_ACTION")
            await page.screenshot(path=str(output/"candidate-ru-customization-320.png"),
                full_page=False,animations="disabled")
            report["screenshots"].append("candidate-ru-customization-320.png")

            returned=await page.evaluate("""() => {
               TLB.setLang('en');render();
               return {lang:TLB.lang(),
                 labels:[...document.querySelectorAll('.sheet.d6s .og h3')].map(n=>n.innerText),
                 optText:optTxt('i1',['o10','o21']),
                 blockedActions:window.__demoBlockedActions};
            }""")
            report["en_restored"]=returned
            require(returned["lang"]=="en" and returned["labels"]==en["labels"] and
                    returned["optText"]=="Small, Bacon" and returned["blockedActions"]==0,
                    "EN_AFTER_RU_TOGGLE_REGRESSION")
            check_unexpected=[x for x in report["network"]["requests"] if x["method"]!="GET"]
            require(not check_unexpected,"NON_GET_ATTEMPT")
            require(not report["network"]["external_attempts"] and not report["network"]["ws_attempts"],
                    "UNEXPECTED_EGRESS_ATTEMPT")
        finally:
            if ctx is not None:
                await ctx.close()
            await browser.close()
            sanitized_har(output/"raw.har")
    require(not report["network"]["pageerrors"],"JS_PAGE_ERRORS")
    report["status"]="PASS_ISOLATED_CANDIDATE_EN_RU_BROWSER_ONLY"

if __name__=="__main__":
    try:
        asyncio.run(main())
    except Exception as e:
        report["status"]="BLOCKED_CANDIDATE_NO_GO: "+str(e)[:280]
        persist()
        raise
    else:
        persist()
