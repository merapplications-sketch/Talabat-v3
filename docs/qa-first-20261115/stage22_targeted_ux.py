"""Read-only Stage22 targeted UX evidence. No product edits, payments, accounts, backend or production navigation.
Entire test is constrained to the already-approved static synthetic Pages origin.
"""
import asyncio
import hashlib
import json
import os
from pathlib import Path
from urllib.parse import urlsplit
from playwright.async_api import async_playwright

HOST = "talabot-safari-demo-20261115.pages.dev"
ROOT = f"https://{HOST}/?lang=en"
ART = Path("stage22-targeted-ux")
ART.mkdir(exist_ok=True)
data = {
    "scope": "Stage22 conditional UX-only, no repeated full network/8x geometry/checkout transaction suite",
    "executed_sha": os.getenv("GITHUB_SHA"),
    "status": "RUNNING",
    "requests": [],
    "responses": [],
    "outside_attempts": [],
    "websocket_attempts": [],
    "pageerrors": [],
    "screens": [],
    "home_images": [],
    "menu_images": [],
    "customization": {},
    "checkout320": {},
    "har": {"state": "NOT_FINALIZED"},
}

def check(test, reason):
    if not test:
        raise RuntimeError(reason)

def allowed(u):
    p=urlsplit(u)
    return p.scheme=="https" and p.hostname==HOST and p.port in (None,443) and not p.username and not p.password

def display(u):
    p=urlsplit(u)
    return (p.hostname or "?")+(p.path or "/")

def save():
    (ART/"targeted-ux-evidence.json").write_text(json.dumps(data,ensure_ascii=False,indent=2),encoding="utf-8")
    print("STAGE22_TARGETED_JSON_START")
    concise={k:v for k,v in data.items() if k not in ("requests","responses","home_images","menu_images")}
    concise["observed_counts"]={
       "requests":len(data["requests"]),"responses":len(data["responses"]),
       "unexpanded_requests":[x for x in data["responses"] if "$%7B" in x["path"]][:25],
       "home_images":len(data["home_images"]),"menu_images":len(data["menu_images"]),
       "visible_broken_home":[x for x in data["home_images"] if x["visible"] and x["naturalWidth"]==0][:15],
       "visible_broken_menu":[x for x in data["menu_images"] if x["visible"] and x["naturalWidth"]==0][:15]
    }
    print(json.dumps(concise,ensure_ascii=False)[:34000])
    print("STAGE22_TARGETED_JSON_END",flush=True)

def sanitize_har(src):
    if not src.exists():
        data["har"]={"state":"MISSING"}
        return
    h=json.loads(src.read_text(encoding="utf-8"))
    entries=h.get("log",{}).get("entries",[])
    for e in entries:
        for key in ("request","response"):
            v=e.get(key,{})
            v["headers"]=[h for h in v.get("headers",[]) if h.get("name","").lower() not in
               ("authorization","cookie","set-cookie","proxy-authorization")]
            for k in ("cookies","postData","queryString"):
                v.pop(k,None)
            if key=="response":
                v.get("content",{}).pop("text",None)
                v.get("content",{}).pop("encoding",None)
    dest=ART/"targeted-ux-redacted.har"
    dest.write_text(json.dumps(h,ensure_ascii=False),encoding="utf-8")
    data["har"]={"state":"FINALIZED","entries":len(entries),"sha256":hashlib.sha256(dest.read_bytes()).hexdigest()}
    src.unlink()

async def main():
    check(os.getenv("GITHUB_ACTIONS")=="true" and
          os.getenv("GITHUB_REPOSITORY")=="merapplications-sketch/Talabat-v3" and
          os.getenv("GITHUB_REF")=="refs/heads/review/stage22-one-shot-qa-20261115",
          "UNAUTHORIZED_GITHUB_RUNNER_CONTEXT")
    async with async_playwright() as pw:
        browser=await pw.chromium.launch(headless=True)
        ctx=None
        try:
            ctx=await browser.new_context(viewport={"width":320,"height":844},service_workers="block",
                 accept_downloads=False,record_har_path=str(ART/"raw.har"))
            async def route(req):
                if allowed(req.request.url):
                    await req.continue_()
                else:
                    data["outside_attempts"].append(display(req.request.url))
                    await req.abort("blockedbyclient")
            await ctx.route("**/*",route)
            check(hasattr(ctx,"route_web_socket"),"NO_WS_GUARD")
            async def ws(route):
                data["websocket_attempts"].append(display(route.url))
                await route.close()
            await ctx.route_web_socket("**/*",ws)
            page=await ctx.new_page()
            page.on("request",lambda r:data["requests"].append(display(r.url)))
            page.on("response",lambda r:data["responses"].append({"path":display(r.url),"status":r.status,
                                                   "type":r.headers.get("content-type","")}))
            page.on("pageerror",lambda e:data["pageerrors"].append(str(e)[:250]))
            r=await page.goto(ROOT,wait_until="load",timeout=25000)
            check(r is not None and r.status==200,"APPROVED_STATIC_SITE_INACCESSIBLE")
            check(await page.evaluate("""() => document.documentElement.lang==='en' &&
                    Boolean(window.TLB&&typeof S!=='undefined'&&typeof render==='function'&&
                    typeof ME!=='undefined'&&ME.phone&&window.__demoBlockedActions===0)"""),"SYNTHETIC_ONLY_RUNTIME_NOT_READY")

            # Existing approved English home, but new 320px DOM image mapping is narrowly scoped to the P2 image URL finding.
            data["home_images"]=await page.evaluate("""() => [...document.images].map(i=>({
               src:i.currentSrc || i.getAttribute('src') || '',
               naturalWidth:i.naturalWidth, naturalHeight:i.naturalHeight,
               visible:!!(i.getBoundingClientRect().width&&i.getBoundingClientRect().height),
               display:getComputedStyle(i).display,
               className:typeof i.className==='string'?i.className:''
            }))""")
            await page.screenshot(path=str(ART/"home-en-320.png"),full_page=False,animations="disabled")
            data["screens"].append("home-en-320.png")
            # Use only existing synthetic code to open a real already-existing merchant screen, no network writes.
            got=await page.evaluate("""() => {
              const st=STORES.find(x=>menuOf(x.n).some(it=>it.id==='i1'));
              if(!st)return {ok:false};
              S.store=st.n;S.v='menu';S.sh=null;render();
              return {ok:true,store:st.n,view:S.v,title:document.querySelector('.d6m h1')?.innerText||''};
            }""")
            check(got.get("ok") and got.get("view")=="menu","DEMO_MERCHANT_MENU_NOT_FOUND")
            await page.wait_for_timeout(220)
            data["menu_images"]=await page.evaluate("""() => [...document.images].map(i=>({
                src:i.currentSrc || i.getAttribute('src') || '',
                naturalWidth:i.naturalWidth, naturalHeight:i.naturalHeight,
                visible:!!(i.getBoundingClientRect().width&&i.getBoundingClientRect().height),
                className:typeof i.className==='string'?i.className:''
            }))""")
            data["long_merchant"]=await page.evaluate("""() => {
                const x=document.querySelector('.d6m h1');
                if(!x)return null;
                const r=x.getBoundingClientRect();
                return {text:x.innerText,length:x.innerText.length,clientWidth:x.clientWidth,
                     scrollWidth:x.scrollWidth,rectWidth:r.width,cssOverflow:getComputedStyle(x).overflow,
                     visible:r.width>0&&r.height>0};
            }""")
            await page.screenshot(path=str(ART/"merchant-en-320.png"),full_page=False,animations="disabled")
            data["screens"].append("merchant-en-320.png")

            selected=await page.evaluate("""() => {
                openItem('i1');
                return {sheet:!!document.querySelector('.sheet.d6s'),
                       pageLang:document.documentElement.lang,
                       titles:[...document.querySelectorAll('.sheet.d6s .og h3')].map(x=>x.innerText),
                       choices:[...document.querySelectorAll('.sheet.d6s .d6-ch .nm')].map(x=>x.innerText),
                       screen:S.v,dialogLabel:document.querySelector('#shT')?.innerText||''};
            }""")
            check(selected.get("sheet"),"EN_CUSTOMIZATION_SHEET_NOT_RENDERED")
            data["customization"]=selected
            await page.screenshot(path=str(ART/"customization-en-320.png"),full_page=False,animations="disabled")
            data["screens"].append("customization-en-320.png")
            data["customization"]["option_scroll"]=await page.evaluate("""() => {
                const s=document.querySelector('.sheet.d6s .osh'),f=document.querySelector('.sheet.d6s .oshf');
                const sr=s?.getBoundingClientRect(),fr=f?.getBoundingClientRect();
                return {scroll_client:s?.clientHeight||0,scroll_full:s?.scrollHeight||0,
                    sheet_height:document.querySelector('.sheet.d6s')?.getBoundingClientRect().height,
                    fixed_footer_rect:fr?{top:fr.top,bottom:fr.bottom,height:fr.height}:null,
                    options_rect:sr?{top:sr.top,bottom:sr.bottom,height:sr.height}:null,
                    document_scroll_width:document.documentElement.scrollWidth,
                    viewport:document.documentElement.clientWidth};
            }""")

            # Existing fake fixture, no payment gesture or network POST. Compare real checkout on 320px against accepted 390px.
            checkout=await page.evaluate("""() => {
                const st=STORES.find(x=>menuOf(x.n).some(it=>it.id==='i1'));
                S.sh=null;S.store=st.n;S.cartStore=st.n;
                const required=TLB.optionsOf('i1').filter(g=>g.required).map(g=>g.options[0].id);
                S.cart={[lk('i1',required,'')]:2};
                S.pay='cash';S.useWallet=false;S.usePts=false;S.v='pay';S.hcf=null;render();
                const thumb=document.querySelector('#hbtn .d69-slide-thumb');
                return {view:S.v,cart_valid:badKeys().length===0,thumb_present:!!thumb,
                  thumb_enabled:!!thumb&&!thumb.disabled,
                  fake_address_present:!!curAddr(),demo_guard_present:window.__demoBlockedActions===0,
                  amount:calc().total};
            }""")
            check(checkout.get("cart_valid") and checkout.get("thumb_present") and checkout.get("fake_address_present"),
                  "INVALID_SYNTHETIC_320_CHECKOUT")
            data["checkout320"]=checkout
            await page.screenshot(path=str(ART/"checkout-en-320-initial.png"),full_page=False,animations="disabled")
            data["screens"].append("checkout-en-320-initial.png")

            # Scroll the fee row into the visible center and measure hit testing against the fixed payment dock.
            fee=page.locator(".d67-checkout .row").filter(has_text="Delivery")
            data["checkout320"]["fee_rows"]=await fee.count()
            if await fee.count():
                target=fee.last
                await target.scroll_into_view_if_needed(timeout=5000)
                await page.wait_for_timeout(140)
            data["checkout320"]["metrics"]=await page.evaluate("""() => {
                const first=[...document.querySelectorAll('.d67-checkout .row')]
                    .find(x=>/Delivery/i.test(x.innerText));
                const dock=document.querySelector('.d68-pay-dock');
                const thumb=document.querySelector('#hbtn .d69-slide-thumb');
                const f=first?.getBoundingClientRect(),d=dock?.getBoundingClientRect(),
                      a=thumb?.getBoundingClientRect();
                const hit=(r)=>{if(!r)return null;let x=r.left+r.width/2,y=r.top+r.height/2;
                  return {inViewport:y>=0&&y<=innerHeight&&x>=0&&x<=innerWidth,
                    hitTag:document.elementFromPoint(x,y)?.tagName||'',
                    centerInDock:!!d&&x>=d.left&&x<=d.right&&y>=d.top&&y<=d.bottom}};
                return {viewportWidth:innerWidth,documentScrollWidth:document.documentElement.scrollWidth,
                   checkoutText:document.querySelector('.d67-checkout')?.innerText.slice(-850)||'',
                   feeText:first?.innerText||'',feeHit:hit(f),sliderHit:hit(a),
                   dock:d?{top:d.top,bottom:d.bottom,height:d.height}:null,
                   scrollTop:document.scrollingElement.scrollTop,
                   scrollMax:document.scrollingElement.scrollHeight-innerHeight};
            }""")
            await page.screenshot(path=str(ART/"checkout-en-320-fee.png"),full_page=False,animations="disabled")
            data["screens"].append("checkout-en-320-fee.png")
            check(not data["websocket_attempts"] and not data["outside_attempts"] and
                  await page.evaluate("window.__demoBlockedActions===0"),
                  "UNEXPECTED_EXTERNAL_ATTEMPT_OR_FAKE_ORDER")
            data["status"]="TARGETED_UX_EVIDENCE_CAPTURED_CONDITIONAL"
        finally:
            if ctx is not None:
                await ctx.close()
            await browser.close()
            sanitize_har(ART/"raw.har")
    check(not data["pageerrors"],"BROWSER_PAGE_ERROR")
    check(data["har"].get("entries",0)>0,"EMPTY_REAL_HAR")

if __name__=="__main__":
    try:
        asyncio.run(main())
    except Exception as e:
        data["status"]="FAIL_CLOSED: "+str(e)[:300]
        save()
        raise
    else:
        save()
