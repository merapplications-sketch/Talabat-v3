#!/usr/bin/env python3
"""BRIEF-15: independent WebKit checks of ORIGINAL HTML/JS (not a fake DOM).
Read-only synthetic data only. Screenshot evidence is committed on isolated review branch.
No app/finance/RPC writes and no external requests. No physical iOS keyboard is claimed.
"""
import pathlib,json,os,sys,traceback
from playwright.sync_api import sync_playwright
from full_audit import ROOT,LOCAL,start_server,make_context
OUT=ROOT/"qa-shots"/"unified-fix"
OUT.mkdir(parents=True,exist_ok=True)
SIZES=[(375,667),(390,844),(430,932)]
LANGS=("ru","en")
rows=[];errors=[]

def assert_js(pg,script,name):
    r=pg.evaluate(script)
    if not r: raise AssertionError(name)
    return r

def ready(pg,app,w,h,lang):
    ctx=make_context(BROWSER,app,lang,w,h)
    pg=ctx.new_page()
    pg.goto(LOCAL+"/"+app+".html",wait_until="domcontentloaded",timeout=20000)
    pg.wait_for_timeout(750)
    assert_js(pg,"() => !!window.TLB && !!document.querySelector('#app') && document.querySelector('#app').textContent.trim().length>10","actual "+app+" rendered")
    return ctx,pg

def screenshot(pg,case,app,lang,w):
    path=OUT/(case+"-"+app+"-"+lang+"-"+str(w)+"-after.png")
    pg.screenshot(path=str(path),animations="disabled",timeout=15000)
    return str(path.relative_to(ROOT))

def F01(pg):
    pg.evaluate("() => {S.v='home';render()}")
    pg.wait_for_timeout(120)
    return assert_js(pg,"""() => {
      const c=document.querySelector('#app .c-current-inline'),b=document.querySelector('#app .d6-bento');
      if(!c||!b)return false;const a=c.getBoundingClientRect(),r=b.getBoundingClientRect();
      return getComputedStyle(c).position!=='fixed'&&a.top>=r.bottom-1&&
        c.previousElementSibling===b&&a.width>240;
    }""","F-01 floating current-order card intersects Home banner")

def F02(pg):
    pg.evaluate("() => {S.v='home';render()}")
    return assert_js(pg,"""() => {
      const cats=[...document.querySelectorAll('#app .d6-ct b')],inp=document.querySelector('#app input[placeholder]');
      if(!inp||!cats.length)return false;
      const ph=inp.placeholder.toLowerCase();
      const lang=TLB.lang();
      if(lang==='ru'&&!ph.includes('поиск еды и магазинов'))return false;
      if(lang==='en'&&!ph.includes('search food and stores'))return false;
      return cats.every(e=>getComputedStyle(e).whiteSpace==='normal'&&
        getComputedStyle(e).webkitLineClamp==='2'&&e.scrollWidth<=e.clientWidth+2);
    }""","F-02 search placeholder/category labels clipped")

def F03(pg):
    pg.evaluate("() => go('track',{tid:'ord1'})")
    pg.wait_for_timeout(120)
    return assert_js(pg,"""() => {
      const contact=document.querySelector('#app .p1-contact'),sum=document.querySelector('#app .p1-summary'),
        receipt=document.querySelector('#app .p1-receipt'),buttons=[...document.querySelectorAll('#app .customer-quick button')];
      if(!contact||!sum||!receipt||buttons.length<3)return false;
      const q=e=>e.getBoundingClientRect(),x=q(contact),y=q(sum),z=q(receipt);
      if(x.top<y.bottom-1||z.bottom>x.top+1&&z.top<x.bottom-1)return false;
      for(let i=0;i<buttons.length;i++){
        const a=q(buttons[i]);
        if(a.left<x.left-1||a.right>x.right+1||a.width<80||a.height<40)return false;
        for(let j=0;j<i;j++){const b=q(buttons[j]);
           if(Math.min(a.right,b.right)-Math.max(a.left,b.left)>2&&
              Math.min(a.bottom,b.bottom)-Math.max(a.top,b.top)>2)return false;}
      }
      return getComputedStyle(contact).display==='flow-root';
    }""","F-03 tracking summary vs chat/quick controls intersect")

def F04(pg,w,h):
    pg.evaluate("() => {go('menu',{store:STORES[0].n});openItem('i1')}")
    pg.locator("#shn").wait_for(state="visible",timeout=2000)
    pg.locator("#shn").focus()
    pg.set_viewport_size({"width":w,"height":max(300,h-280)})
    pg.evaluate("() => {window.dispatchEvent(new Event('resize'));window.visualViewport?.dispatchEvent(new Event('resize'))}")
    pg.wait_for_timeout(360)
    r=pg.evaluate("""() => {
      const sh=document.querySelector('.d6s'),f=document.querySelector('#shn'),
        sc=sh?.querySelector('.osh'),ft=sh?.querySelector('.oshf');
      if(!sh||!f||!sc||!ft)return null;
      const a=f.getBoundingClientRect(),c=sc.getBoundingClientRect(),b=ft.getBoundingClientRect();
      const cs=getComputedStyle(sc),before=sc.scrollTop,bound=sc.scrollHeight-sc.clientHeight;
      const post={before,scrollHeight:sc.scrollHeight,clientHeight:sc.clientHeight,scrollMax:bound,
          overflow:cs.overflowY,snap:cs.scrollSnapType,textareaOffset:f.offsetTop,visibleHeight:c.height};
      sc.scrollTop=999999;post.after=sc.scrollTop;
      const fr=f.getBoundingClientRect();post.newTop=fr.top;post.newBottom=fr.bottom;
      sc.scrollTop=before;post.restored=sc.scrollTop;
      return {kbd:sh.classList.contains('d6-keyboard'),top:a.top,bottom:a.bottom,
        scrollTop:c.top,scrollBottom:c.bottom,footerTop:b.top,active:document.activeElement===f,debug:post};
    }""")
    if not r or not r["kbd"] or not r["active"] or r["top"]<r["scrollTop"]-2 or r["bottom"]>min(r["scrollBottom"],r["footerTop"])+3:
        raise AssertionError("F-04 focused dish note hidden/partly clipped: "+str(r))
    return r

def F05(pg):
    return assert_js(pg,"""() => {
      const s=TLB.t('stepsDrag'),l=TLB.lang();
      return s&&s!=='stepsDrag'&&(l==='ru'?s==='Проведите вправо, чтобы заказать':
        s==='Slide to place order');
    }""","F-05 raw stepsDrag translation exposed")

def F06(pg):
    pg.evaluate("() => {setTab('m');openSheet('i1')}")
    pg.locator(".f06-item-editor").wait_for(state="visible",timeout=2500)
    return assert_js(pg,"""() => {
      const ed=document.querySelector('.f06-item-editor'),name=ed?.querySelector('textarea#sn'),
        num=ed?.querySelector('#sp'),act=ed?.querySelector('.f06-actions');
      if(!name||!num||!act||act.querySelectorAll('button').length<1)return false;
      ed.scrollTop=ed.scrollHeight;
      const t=name.getBoundingClientRect(),r=ed.getBoundingClientRect();
      return name.rows>=2&&name.value.length>0&&getComputedStyle(num).appearance==='textfield'
        &&getComputedStyle(act).position==='sticky'&&t.width<=r.width;
    }""","F-06 merchant item/option fields and save strip inaccessible")

def F07(pg,w,h):
    pg.evaluate("() => rjOpen('ord0')")
    pg.locator("#rjn").wait_for(state="visible",timeout=2500)
    pg.locator("#rjn").focus()
    pg.set_viewport_size({"width":w,"height":max(300,h-280)})
    pg.evaluate("() => window.visualViewport?.dispatchEvent(new Event('resize'))")
    pg.wait_for_timeout(340)
    return assert_js(pg,"""() => {
       const p=document.querySelector('.f07-reject'),a=document.querySelector('#rjn');
       if(!p||!a)return false;
       const r=a.getBoundingClientRect(),v=p.getBoundingClientRect();
       const tr=TLB.t('pickupCancel');
       return tr!=='pickupCancel'&&a===document.activeElement&&r.bottom<=v.bottom+2
         &&r.top>=v.top-2&&r.bottom<=window.innerHeight+3;
    }""","F-07 merchant rejection field not visible above keyboard or raw key present")

def F08(pg,w,h):
    pg.evaluate("() => setTab('p')")
    pg.locator("#sdesc").wait_for(state="visible",timeout=2500)
    pg.locator("#sdesc").focus()
    pg.set_viewport_size({"width":w,"height":max(300,h-280)})
    pg.evaluate("() => window.visualViewport?.dispatchEvent(new Event('resize'))")
    pg.wait_for_timeout(350)
    return assert_js(pg,"""() => {
      const e=document.querySelector('#sdesc');if(!e||document.activeElement!==e)return false;
      const r=e.getBoundingClientRect(),h=window.visualViewport?.height||innerHeight;
      return r.bottom<=h+2 && r.top>=-1 &&document.body.classList.contains('f08-profile-keyboard');
    }""","F-08 profile input obscured by keyboard")

def F09(pg):
    pg.evaluate("() => {const o=mine();if(o){o.status='pickedup';o.arrivedCustAt=Date.now();}render()}")
    pg.wait_for_timeout(220)
    return assert_js(pg,"""async () => {
      if(!document.querySelector('#app .a-tools'))return false;
      const x=document.createElement('div');
      x.textContent=TLB.t('mapFail');
      x.style.cssText='position:fixed;bottom:96px;left:25%;width:50%;z-index:9998;background:#f44;color:#fff';
      document.body.appendChild(x);
      await new Promise(res=>setTimeout(res,65));
      const tools=document.querySelector('#app .a-tools')?.getBoundingClientRect();
      if(!tools)return false;
      if(!x.isConnected)return true;
      const r=x.getBoundingClientRect();
      return !(Math.min(r.right,tools.right)>Math.max(r.left,tools.left)+1 &&
               Math.min(r.bottom,tools.bottom)>Math.max(r.top,tools.top)+1);
    }""","F-09 map failure toast obscures Call/Chat/Collect")

def F10(pg):
    # Synthetic ids are not production id bugs: they come only from QA fixtures.
    return assert_js(pg,"""() => TLB.orders().some(o=>String(o.id)==='ord0')""","F-10 synthetic QA fixture not as expected")

TESTS=[
 ("F-01","customer",lambda p,w,h:F01(p)),
 ("F-02","customer",lambda p,w,h:F02(p)),
 ("F-03","customer",lambda p,w,h:F03(p)),
 ("F-04","customer",lambda p,w,h:F04(p,w,h)),
 ("F-05","customer",lambda p,w,h:F05(p)),
 ("F-06","merchant",lambda p,w,h:F06(p)),
 ("F-07","merchant",lambda p,w,h:F07(p,w,h)),
 ("F-08","merchant",lambda p,w,h:F08(p,w,h)),
 ("F-09","driver",lambda p,w,h:F09(p)),
 ("F-10","admin",lambda p,w,h:F10(p)),
]
def main():
    global BROWSER
    server=start_server()
    try:
        with sync_playwright() as pw:
            BROWSER=pw.webkit.launch(headless=True)
            dims=[x for x in SIZES if not os.environ.get("BRIEF15_WIDTHS") or x[0] in [int(v) for v in os.environ["BRIEF15_WIDTHS"].split(",")]]
            langs=[x for x in LANGS if not os.environ.get("BRIEF15_LANGS") or x in os.environ["BRIEF15_LANGS"].split(",")]
            tests=[x for x in TESTS if not os.environ.get("BRIEF15_CASES") or x[0] in os.environ["BRIEF15_CASES"].split(",")]
            for w,h in dims:
                for lang in langs:
                    for case,app,fn in tests:
                        ctx=pg=None
                        try:
                            ctx,pg=ready(None,app,w,h,lang)
                            result=fn(pg,w,h)
                            rows.append({"id":case,"app":app,"lang":lang,"width":w,"status":"PASS","geometry":result if isinstance(result,dict) else None})
                        except Exception as err:
                            errors.append({"id":case,"app":app,"lang":lang,"width":w,"type":type(err).__name__,"message":str(err)[:240]})
                            rows.append({"id":case,"app":app,"lang":lang,"width":w,"status":"FAIL"})
                        finally:
                            if pg:
                                try:rows[-1]["image"]=screenshot(pg,case,app,lang,w)
                                except Exception as err:errors.append({"id":case,"app":app,"lang":lang,"width":w,"type":"SCREENSHOT_FAILURE","message":str(err)[:130]})
                            if ctx:ctx.close()
            BROWSER.close()
    finally:server.shutdown()
    (OUT/"REPORT.json").write_text(json.dumps({"browser":"WebKit Linux, original app DOM, read-only synthetic data","keyboard":"height simulation","cases":rows,"errors":errors},ensure_ascii=False,indent=2))
    order=["# BRIEF-15 Original App WebKit — BEFORE / AFTER","",
      "These are original source-backed pages with read-only synthetic fixture. Not production auth or physical iPhone.",
      "Each BEFORE reference is pinned to unchanged BRIEF-14 original screenshots in this same isolated branch.",""]
    refs={"F-01":("customer","home"),"F-02":("customer","home"),"F-03":("customer","track"),"F-04":("customer","item-sheet"),
      "F-05":("customer","pay"),"F-06":("merchant","item-edit"),"F-07":("merchant","reject-sheet"),"F-08":("merchant","profile"),
      "F-09":("driver","step4"),"F-10":("admin","tab0")}
    for row in rows:
        app,sc=refs[row["id"]]
        before=f"../full-audit/{app}/{sc}_{row['lang']}_{row['width']}.png"
        after=pathlib.Path(row.get("image","")).name
        order.append(f"- {row['id']} {row['lang']}/{row['width']}: [{row['status']}](REPORT.json) | [BEFORE]({before}) | [AFTER]({after})")
    (OUT/"INDEX.md").write_text("\n".join(order)+"\n")
    print("BRIEF15_WEBKIT_COVERAGE",len(rows),"PASS",len(rows)-len(errors),"FAIL",len(errors))
    for err in errors[:12]:print("BRIEF15_WEBKIT_FAIL",json.dumps(err,ensure_ascii=False))
    return 1 if errors or len(rows)!=len(dims)*len(langs)*len(tests) else 0
if __name__=="__main__":sys.exit(main())
