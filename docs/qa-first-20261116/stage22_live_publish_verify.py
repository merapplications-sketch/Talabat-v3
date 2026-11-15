"""Stage22 POST-PUBLISH read-only verification of the live synthetic demo.
No overlay, no mutation. Checks every deployed file's SHA256 against the
8e78d2df 54-file runtime list (+_headers via response headers), CSP/nosniff,
then EN/RU option labels and the fake-checkout block on the real deployment.
If the live guard is still the old one, status = NOT_DEPLOYED_YET.
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
NEW_GUARD_SHA256 = "3bc13bd4c353d439ff4702f12e50c4a76fd224d230f154bfe50eacc678be85d6"
EXPECTED = Path("docs/qa-first-20261116/stage22-expected-sha256.txt")
output = Path("stage22-candidate-verification")
output.mkdir(exist_ok=True)
report = {
    "scope": "post-publish live verification of talabot-safari-demo-20261115 (no overlay)",
    "live_files": {},
    "headers": {},
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
    opener=build_opener(NoRedirect(),HTTPSHandler(context=ssl.create_default_context()))
    exp=[l.split(None,1) for l in EXPECTED.read_text().splitlines() if l.strip()]
    require(len(exp)==54,"EXPECTED_LIST_NOT_54")
    bad=[]
    for sha,name in exp:
        url=BASE+"/" if name=="index.html" else BASE+"/"+name  # Pages 308s /index.html -> /
        with opener.open(Request(url,headers={"User-Agent":"Stage22-live-verify"}),timeout=20) as r:
            require(r.status==200,"LIVE_NOT_200:"+name)
            actual=hashlib.sha256(r.read()).hexdigest()
            if name=="index.html":
                h={k.lower():v for k,v in r.headers.items()}
                report["headers"]={k:h.get(k) for k in ("content-security-policy","x-content-type-options","content-type","referrer-policy","permissions-policy")}
        if name=="demo-guard.js":
            report["hosted_original_guard_sha256"]=actual
            if actual==ORIGINAL_HOST_GUARD_SHA256:
                raise RuntimeError("NOT_DEPLOYED_YET_OLD_GUARD_LIVE")
        if actual!=sha: bad.append(name)
    report["live_files"]={"checked":len(exp),"mismatch":bad}
    require(not bad,"LIVE_FILE_HASH_MISMATCH")
    with opener.open(Request(BASE+"/",headers={"User-Agent":"Stage22-live-verify"}),timeout=20) as r:
        h={k.lower():v for k,v in r.headers.items()}
        report["hosted_root_sha256"]=hashlib.sha256(r.read()).hexdigest()
        report["headers"]={k:h.get(k) for k in ("content-security-policy","x-content-type-options","content-type","referrer-policy","permissions-policy")}
    csp=report["headers"].get("content-security-policy") or ""
    require("connect-src 'none'" in csp and "form-action 'none'" in csp,"CSP_REGRESSION")
    require((report["headers"].get("x-content-type-options") or "").lower()=="nosniff","NOSNIFF_MISSING")
    require(report["hosted_root_sha256"]==ORIGINAL_HOST_ROOT_SHA256,"ROOT_CHANGED")

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
    preflight()
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
            # The candidate changes demo-guard.js itself. Prove the original fake checkout
            # blocking behavior still works through one legitimate full GUI pointer gesture.
            fixture=await page.evaluate("""() => {
              const st=STORES.find(x=>menuOf(x.n).some(it=>it.id==='i1'));
              if(!st)return {ok:false};
              S.sh=null;S.store=st.n;S.cartStore=st.n;
              S.cart={[lk('i1',['o10','o21'],'')]:2};
              S.pay='cash';S.useWallet=false;S.usePts=false;
              S.v='pay';S.hcf=null;render();
              const thumb=document.querySelector('#hbtn .d69-slide-thumb');
              return {ok:true,cartValid:badKeys().length===0,
                enabled:!!thumb&&!thumb.disabled,
                addressPresent:!!curAddr(),storeOpen:!closedNow(S.cartStore),
                demoFlag:window.__TALABOT_SYNTHETIC===true,
                blockedCounter:window.__demoBlockedActions,
                view:S.v,tooFar:tooFar()};
            }""")
            report["checkout_precondition"]=fixture
            require(fixture["ok"] and fixture["cartValid"] and fixture["enabled"] and
                    fixture["addressPresent"] and fixture["storeOpen"] and fixture["demoFlag"] and
                    not fixture["tooFar"] and fixture["blockedCounter"]==0,
                    "CANDIDATE_SYNTHETIC_ORDER_GUARD_PRECONDITION_FAILED")
            await page.screenshot(path=str(output/"candidate-checkout-before-320.png"),
              full_page=False,animations="disabled")
            report["screenshots"].append("candidate-checkout-before-320.png")
            thumb=await page.locator("#hbtn .d69-slide-thumb").bounding_box()
            bar=await page.locator("#hbtn").bounding_box()
            require(bool(thumb) and bool(bar),"CANDIDATE_SLIDER_NOT_VISIBLE")
            x=thumb["x"]+thumb["width"]/2
            y=thumb["y"]+thumb["height"]/2
            await page.mouse.move(x,y)
            await page.mouse.down()
            acquired=await page.evaluate("""() => ({
                active:typeof HOLD !== 'undefined' && !!HOLD,
                max:typeof HOLD!=='undefined' && HOLD?HOLD.max:0,
                disabled:document.querySelector('#hbtn .d69-slide-thumb').disabled,
                hidden:document.hidden
            })""")
            require(acquired["active"] and acquired["max"]>0 and not acquired["disabled"] and
                    not acquired["hidden"],"CANDIDATE_SLIDER_POINTER_NOT_ACQUIRED")
            await page.mouse.move(x+acquired["max"]+14,y,steps=20)
            p=await page.evaluate("typeof HOLD!=='undefined'&&HOLD?HOLD.p:0")
            require(p>=0.96,"CANDIDATE_POINTER_NOT_FULLY_COMPLETED")
            await page.mouse.up()
            await page.wait_for_timeout(600)
            outcome=await page.evaluate("""() => ({
              blocked:window.__demoBlockedActions,
              view:S.v,
              success:!!document.querySelector('[data-order-success],.order-success'),
              busy:!!S.busy
            })""")
            report["checkout"]={"state":outcome,"pointerProgress":p}
            require(outcome["blocked"]==1 and outcome["view"]=="pay" and not outcome["success"] and
                    not outcome["busy"],"CANDIDATE_MOCK_CHECKOUT_BLOCKING_REGRESSION")
            await page.screenshot(path=str(output/"candidate-checkout-after-320.png"),
              full_page=False,animations="disabled")
            report["screenshots"].append("candidate-checkout-after-320.png")

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
    report["status"]="PASS_LIVE_PUBLISHED_STAGE22"

if __name__=="__main__":
    try:
        asyncio.run(main())
    except Exception as e:
        report["status"]="NO_GO: "+str(e)[:280]
        persist()
        raise
    else:
        persist()
