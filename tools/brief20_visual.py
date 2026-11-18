#!/usr/bin/env python3
"""BRIEF-20 offline WebKit owner baseline-vs-candidate visual acceptance.
No remote egress, live orders, SQL, deployment, synthetic offers persisted or auth credentials.
"""
import functools, http.server, io, json, pathlib, subprocess, threading, os, sys
from PIL import Image, ImageChops
from playwright.sync_api import sync_playwright
from qa_all import FIX

ROOT=pathlib.Path(__file__).resolve().parents[1]
BASE_SHA="7c7e66094c10614c01ad7359cda7bc3740e8fcfd"
OUT=ROOT/"qa-shots/unified-fix/brief20"
VARIANTS=(("ru",375,812),("en",390,844),("ru",430,932),("ru",320,700))
SCREENS=(("customer","home"),("customer","restaurant"),("driver","first"),("merchant","first"))
errors=[]; rows=[]; blocked=[]
BASE_PORT=18766; AFTER_PORT=18765

def start_server(root,port):
    class Quiet(http.server.SimpleHTTPRequestHandler):
        def log_message(self,*a): pass
    handler=functools.partial(Quiet,directory=str(root))
    srv=http.server.ThreadingHTTPServer(("127.0.0.1",port),handler)
    threading.Thread(target=srv.serve_forever,daemon=True).start()
    return srv

def ctx(browser,app,lang,w,h):
    c=browser.new_context(viewport={"width":w,"height":h},device_scale_factor=2,
                          is_mobile=True,has_touch=True,locale="ru-RU" if lang=="ru" else "en-US")
    c.add_init_script("localStorage.setItem('tlb_lang',"+json.dumps(lang)+");")
    def handle(route):
        u=route.request.url
        if ("supabase-js" in u and "cdn" in u):
            route.fulfill(status=200,content_type="application/javascript",
                          body=FIX.replace("window.__ROLE",json.dumps(app)))
        elif u.startswith("http://127.0.0.1:"+str(BASE_PORT)+"/") or u.startswith("http://127.0.0.1:"+str(AFTER_PORT)+"/"):
            route.continue_()
        else:
            blocked.append(u.split("?")[0][:140])
            route.abort("blockedbyclient")
    c.route("**/*",handle)
    return c

def prepare(page,app,screen):
    page.wait_for_function("typeof window.TLB!=='undefined' && typeof window.render==='function' && !!document.querySelector('#app')",
                           timeout=18000)
    # The same deterministic synthetic data is applied to BOTH immutable reference
    # and candidate. This demonstrates DineOut only where an eligible discount exists.
    if app=="customer":
        page.evaluate("""() => {
            const original=TLB.isOpen.bind(TLB);
            const closed=STORES.find(s=>s.c==='rest'&&s!==STORES[0]) || STORES[STORES.length-1];
            if(closed)TLB.isOpen=n=>n===closed.n?false:original(n);
            if(!STORES.some(s=>s.c==='rest'&&TLB.isOpen(s.n)&&s.disc>0)){
                const eligible=STORES.find(s=>s.c==='rest'&&TLB.isOpen(s.n));
                if(eligible) eligible.disc=20;
            }
            S.q='';S.hf=null;S.srt='';S.fo=false;
            if(!S.cart)S.cart={};
            S.v='home';render();
        }""")
        if screen=="restaurant":
            page.evaluate("() => {S.v='menu';S.store=STORES.find(s=>s.c==='rest'&&TLB.isOpen(s.n)).n;render()}")
    else:
        page.evaluate("() => {if(typeof render==='function')render()}")
    page.wait_for_timeout(400)
    page.evaluate("window.scrollTo(0,0)")
    page.wait_for_timeout(80)

def audit(page,app,screen,lang,w):
    result=page.evaluate("""() => {
        const W=innerWidth, e=document.documentElement;
        const hdr=document.querySelector('#app .d6h .d6-hr')||document.querySelector('#app header')||document.querySelector('#app .hd');
        const h=hdr?.getBoundingClientRect(),cats=[...document.querySelectorAll('#app .d6-ct img')];
        return {
          width:W,scrollWidth:e.scrollWidth,
          viewport:document.querySelector('meta[name="viewport"]')?.content||'',
          header:h&&{left:h.left,right:h.right,top:h.top,bottom:h.bottom,width:h.width,height:h.height},
          dineout:!!document.querySelector('#app .d6-dn'),categories:cats.map(x=>x.getAttribute('src')),
          bento:!!document.querySelector('#app .d6-bento'),
          categoryTexts:[...document.querySelectorAll('#app .d6-ct b')].map(x=>x.textContent.trim()),
          closedCount:document.querySelectorAll('#app .closed').length,
          htmlRendered:(document.querySelector('#app')?.innerText||'').trim().length
        };
    }""")
    if result["htmlRendered"]<90:raise AssertionError("Original app did not render usable "+app+" "+screen)
    if app=="customer" and screen=="home":
        if result["scrollWidth"]!=w:errors.append(f"H20_HORZ_OVERFLOW {lang}/{w}: "+repr(result))
        if not result["dineout"]:errors.append(f"H20_DINEOUT_MISSING {lang}/{w}")
        if not result["bento"] or len(result["categories"])<5:errors.append(f"H20_ICON_BENTO_MISSING {lang}/{w}")
        h=result["header"]
        if not h or h["left"]<-1 or h["right"]>w+1 or h["top"]<-1:
            errors.append(f"H20_HEADER_CLIPPED {lang}/{w}: "+repr(h))
    return result

def pixel_delta(before,after):
    # A 2px high bottom footer on only one side must NOT become fictitious 100% diff.
    # Record full heights as objective evidence; compare aligned common top area.
    geometry=None
    if before.size!=after.size:
        geometry=dict(before=before.size,after=after.size,
                      width_diff=after.width-before.width,
                      height_diff=after.height-before.height)
        w=min(before.width,after.width);h=min(before.height,after.height)
        before=before.crop((0,0,w,h));after=after.crop((0,0,w,h))
    diff=ImageChops.difference(before.convert("RGB"),after.convert("RGB")).convert("L")
    hist=diff.histogram()
    changed=sum(hist[16:])
    return round(100*changed/(before.width*before.height),3),geometry

def masking(page):
    page.evaluate("""() => {
        document.querySelectorAll('#app .closed,#app .g12-closed-badge').forEach(x=>{x.style.visibility='hidden'});
    }""")

def financial(page):
    if not page.evaluate("typeof calc === 'function'"):return None
    return page.evaluate("""() => {
      S.cart={i1:1};S.cartStore=STORES[0].n;S.tip=10;S.useWallet=false;S.usePts=false;
      const v=calc();return ['sub','d','h','p','pv','fee','total','due','w'].map(k=>Number(v[k]||0)).concat([Number(S.tip)]);
    }""")

def run():
    if any(os.environ.get(k) for k in ("SUPABASE_ACCESS_TOKEN","DATABASE_URL","SUPABASE_DB_PASSWORD","SUPABASE_PROJECT_REF")):
        raise RuntimeError("FORBIDDEN_REMOTE_CREDENTIAL_IN_VISUAL_TEST")
    base=ROOT/".brief20-owner-reference"
    if base.exists():raise RuntimeError("Unexpected existing baseline worktree")
    subprocess.run(["git","worktree","add","--detach",str(base),BASE_SHA],cwd=ROOT,check=True,capture_output=True,text=True)
    for p in (ROOT,base):
        if not (p/"customer.html").is_file():raise RuntimeError("Missing exact source in worktree")
    v0=(base/"customer.html").read_text("utf-8").split('<meta name="viewport"',1)[1].split(">",1)[0]
    v1=(ROOT/"customer.html").read_text("utf-8").split('<meta name="viewport"',1)[1].split(">",1)[0]
    if v0!=v1:raise AssertionError("Changed baseline meta viewport")
    servers=[start_server(base,BASE_PORT),start_server(ROOT,AFTER_PORT)]
    try:
      with sync_playwright() as pw:
        b=pw.webkit.launch(headless=True)
        for app,screen in SCREENS:
          for lang,w,h in VARIANTS:
            data={}
            photos={}
            mask_images={}
            money={}
            for stage,port in (("before",BASE_PORT),("after",AFTER_PORT)):
                c=ctx(b,app,lang,w,h);page=c.new_page();page_errors=[]
                page.on("pageerror",lambda err:page_errors.append(str(err)[:170]))
                page.goto("http://127.0.0.1:"+str(port)+"/"+app+".html",wait_until="domcontentloaded",timeout=24000)
                prepare(page,app,screen)
                data[stage]=audit(page,app,screen,lang,w)
                out=OUT/stage;out.mkdir(parents=True,exist_ok=True)
                dest=out/f"{app}-{screen}-{lang}-{w}.png"
                page.screenshot(path=str(dest),full_page=(screen=="home"),animations="disabled",timeout=20000)
                photos[stage]=Image.open(dest).convert("RGB")
                if app=="customer" and screen=="home":
                    masking(page)
                    raw=page.screenshot(full_page=True,animations="disabled",timeout=20000)
                    mask_images[stage]=Image.open(io.BytesIO(raw)).convert("RGB")
                    money[stage]=financial(page)
                if page_errors:errors.append(f"JS_ERROR {app}/{screen}/{lang}/{w} {page_errors[:2]}")
                c.close()
            before,after=photos["before"],photos["after"]
            side=Image.new("RGB",(before.width+after.width,max(before.height,after.height)),"white")
            side.paste(before,(0,0));side.paste(after,(before.width,0))
            (OUT/"compare").mkdir(parents=True,exist_ok=True)
            filename=f"{app}-{screen}-{lang}-{w}-side-by-side.png"
            side.save(OUT/"compare"/filename,optimize=True)
            diff,why=pixel_delta(mask_images["before"],mask_images["after"]) if mask_images else pixel_delta(before,after)
            row={"app":app,"screen":screen,"lang":lang,"width":w,"baseline":data["before"],
                 "after":data["after"],"pixels_changed_pct":diff,"size_note":why,
                 "side_by_side":"compare/"+filename}
            if app=="customer" and screen=="home":
                if data["before"]["categories"]!=data["after"]["categories"]:
                    errors.append(f"H20_CATEGORY_ICON_MISMATCH {lang}/{w}")
                if data["before"]["categoryTexts"]!=data["after"]["categoryTexts"]:
                    errors.append(f"H20_CATEGORY_LABEL_MISMATCH {lang}/{w}")
                if money.get("before")!=money.get("after"):
                    errors.append(f"H20_FINANCIAL_PARITY_FAIL {lang}/{w}")
                row["financial_parity"]=money.get("before")==money.get("after")
                # Record percent; do not conceal differences from approved closed-card or imagery changes.
                if diff>1.5 or (why and abs(why['height_diff'])>50):
                    errors.append(f"H20_HOME_PIXEL_MISMATCH {lang}/{w} diff={diff}% size={why}")
            rows.append(row)
            print("BRIEF20_VISUAL "+app+" "+screen+" "+lang+"/"+str(w)+" diff="+str(diff)+
                  "% width="+str(data["after"]["scrollWidth"])+"/"+str(w)+
                  " DineOut="+str(data["after"]["dineout"]),flush=True)
        b.close()
    finally:
        for s in servers:s.shutdown()
        subprocess.run(["git","worktree","remove","--force",str(base)],cwd=ROOT,capture_output=True)
    report={"source":{"before":BASE_SHA,"after":subprocess.run(["git","rev-parse","HEAD"],cwd=ROOT,capture_output=True,text=True).stdout.strip()},
            "mode":"isolated LOCAL read-only WebKit synthetic fixture, not physical iPhone",
            "screenshots":len(rows)*3,"cases":len(rows),"errors":errors,
            "blocked_external_urls":sorted(set(blocked))[:20],"rows":rows}
    OUT.mkdir(parents=True,exist_ok=True)
    (OUT/"REPORT.json").write_text(json.dumps(report,ensure_ascii=False,indent=2),encoding="utf-8")
    index=["# TALABOT BRIEF-20 — side-by-side, owner Home-B SHA "+BASE_SHA,"",
           "All screenshots are ORIGINAL HTML rendered under deterministic OFFLINE synthetic data.",
           "Left: approved baseline · Right: proposed isolated candidate · no production or orders.","",
           "## Pinned side-by-side comparisons",""]
    for r in rows:
        index.append(f"- [{r['app']} {r['screen']} {r['lang']} {r['width']} — changed {r['pixels_changed_pct']}%]({r['side_by_side']})")
    index+=["","## Observed failures","","\n".join("- "+e for e in errors) if errors else "None."]
    (OUT/"INDEX.md").write_text("\n".join(index)+"\n",encoding="utf-8")
    print("BRIEF20_VISUAL_TOTAL "+str(len(rows))+" cases; failures "+str(len(errors)),flush=True)
    if errors:raise AssertionError("BRIEF20_VISUAL_NO_GO: "+"; ".join(errors[:8]))
    print("BRIEF20_VISUAL_PASS 16/16; Home B pixel diff <=1.5%; finance unchanged",flush=True)

if __name__=="__main__":
    try:run()
    except Exception as exc:
        print("BRIEF20_VISUAL_FAILURE "+str(exc),file=sys.stderr,flush=True)
        sys.exit(1)
