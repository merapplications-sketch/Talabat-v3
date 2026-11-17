#!/usr/bin/env python3
"""BRIEF-15: independent WebKit checks of ORIGINAL HTML/JS (not a fake DOM).
Read-only synthetic data only. Screenshot evidence is committed on isolated review branch.
No app/finance/RPC writes and no external requests. No physical iOS keyboard is claimed.
"""
import pathlib,json,os,sys,traceback,re
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
    if isinstance(r,dict): return r
    # Explicit postcondition geometry. A passing Boolean alone is NOT an
    # inspectable visual contract; no accepted case may store geometry:null.
    key=(re.search(r'F-\d\d|NOTIFY-01',name) or [None])[0]
    selectors={
      "F-01":["#app .c-current-inline","#app .d6-bento"],
      "F-02":["#app .d6-ct b","#app .d6-bt.d6tp .tt","#app input[placeholder]"],
      "F-03":["#app .p1-summary","#app .p1-contact","#app .customer-quick button"],
      "F-04":["#shn",".d6s .osh",".d6s .oshf"],
      "F-05":["#app .d67-checkout","#app .fbar","#app .d6p"],
      "F-06":[".f06-item-editor","#sn","#sp",".f06-option-name"],
      "F-07":[".f07-reject","#rjn"],
      "F-08":["#sdesc","#app .gp"],
      "F-10":["#app",".tabs button"]
    }.get(key,["#app"])
    geometry=pg.evaluate("""q => {
       const box=e=>{const r=e.getBoundingClientRect();return {
         x:Math.round(r.x*100)/100,y:Math.round(r.y*100)/100,
         w:Math.round(r.width*100)/100,h:Math.round(r.height*100)/100,
         right:Math.round(r.right*100)/100,bottom:Math.round(r.bottom*100)/100}};
       const data=q.flatMap(sel=>[...document.querySelectorAll(sel)].slice(0,8).map(e=>({
         selector:sel,text:(e.textContent||'').trim().slice(0,65),rect:box(e)})));
       return {viewport:{width:innerWidth,height:innerHeight},positions:data,
         scrollY:scrollY,verifiedCount:data.length};
    }""",selectors)
    if not geometry["positions"]:raise AssertionError(name+" no actual DOM geometry measured")
    return geometry

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
      const labelsOK=cats.every(e=>getComputedStyle(e).whiteSpace==='normal'&&
        getComputedStyle(e).webkitLineClamp==='2'&&e.scrollWidth<=e.clientWidth+2);
      const promo=document.querySelector('#app .d6-bt.d6tp .tt');
      if(!promo)return labelsOK;
      const panel=promo.closest('.d6-bt'),r=panel.getBoundingClientRect();
      const range=document.createRange();range.selectNodeContents(promo);
      const lines=[...range.getClientRects()];
      const promoOK=lines.length>=1&&lines.every(x=>x.left>=r.left+3&&x.right<=r.right-3&&x.top>=r.top-1&&x.bottom<=r.bottom+1);
      return labelsOK&&promoOK;
    }""","F-02 search/category/free-delivery banner content clipped")

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
    # A checkout screenshot is invalid unless the ORIGINAL customer has a cart.
    # The previous audit loaded Home because no cart was seeded for this case.
    pg.evaluate("""() => {
      S.sh=null;S.cart={i2:2,['i1~o11']:1};S.cartStore=STORES[0].n;
      go('cart');go('pay');
    }""")
    pg.wait_for_timeout(140)
    return assert_js(pg,"""() => {
      const checkout=document.querySelector('#app .d67-checkout'),
            raw=document.querySelector('#app')?.innerText||'',
            value=TLB.t('stepsDrag'),ru=TLB.lang()==='ru';
      return S.v==='pay'&&checkout&&checkout.getBoundingClientRect().height>90&&
        !/\bstepsDrag\b/.test(raw)&&value!=='stepsDrag'&&
        value===(ru?'Проведите вправо, чтобы заказать':'Slide to place order');
    }""","F-05 payment page with localized stepsDrag, real checkout DOM")

def F06(pg):
    pg.evaluate("() => {setTab('m');openSheet('i1')}")
    pg.locator(".f06-item-editor").wait_for(state="visible",timeout=2500)
    # Two independent views: option-name group and TOP of edit form.
    ed=pg.locator(".f06-item-editor")
    if pg.locator(".f06-option-name").count():
        # Scroll the ACTUAL .md container rather than the text input itself.
        # scrollIntoViewIfNeeded() can incorrectly count options covered by the
        # sticky Save/Delete strip as visible; force the group header above it.
        ed.evaluate("""e => {
          const g=e.querySelector('.ogc');if(!g)return;
          e.scrollTop+=g.getBoundingClientRect().top-e.getBoundingClientRect().top-18;
        }""")
        pg.wait_for_timeout(100)
        opts=pg.evaluate("""() => {
          const md=document.querySelector('.f06-item-editor'),g=md?.querySelector('.ogc'),
            foot=md?.querySelector('.f06-actions');if(!g||!foot)return null;
          const a=g.getBoundingClientRect(),f=foot.getBoundingClientRect(),b=md.getBoundingClientRect();
          return {top:a.top,clipTop:b.top,footerTop:f.top,visible:a.top>=b.top-3&&a.top<f.top-10};
        }""")
        if not opts or not opts["visible"]:raise AssertionError("F-06 option-group header not visible above Save strip: "+str(opts))
        screenshot(pg,"F-06-options","merchant",pg.evaluate("TLB.lang()"),
                   pg.evaluate("window.innerWidth"))
    ed.evaluate("e=>e.scrollTop=e.scrollHeight")
    r=assert_js(pg,"""() => {
      const ed=document.querySelector('.f06-item-editor'),name=ed?.querySelector('textarea#sn'),
        num=ed?.querySelector('#sp'),act=ed?.querySelector('.f06-actions');
      if(!name||!num||!act||act.querySelectorAll('button').length<1)return false;
      const t=name.getBoundingClientRect(),b=ed.getBoundingClientRect();
      return name.rows>=4&&name.value.length>0&&
        name.scrollHeight<=name.clientHeight+3&&
        getComputedStyle(num).appearance==='textfield'&&
        getComputedStyle(act).position==='sticky'&&t.width<=b.width;
    }""","F-06 merchant editable name, no steppers and safe actions")
    ed.evaluate("e=>e.scrollTop=0")  # final screenshot MUST show heading/name/price
    return r

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
    pg.wait_for_timeout(150)
    pg.evaluate("() => TLB.toast(TLB.t('mapFail'),true)")
    pg.wait_for_timeout(110)
    r=pg.evaluate("""() => {
      const st=document.querySelector('#a-map-state');
      const btns=[...document.querySelectorAll('#app .a-tools button,#app .a-tools a,#app .a-dock button,#app .a-collect-line')];
      const tx=TLB.t('mapFail'),rect=e=>{const r=e.getBoundingClientRect();return {
         x:r.left,y:r.top,right:r.right,bottom:r.bottom,w:r.width,h:r.height}};
      if(!st||!btns.length)return null;
      const a=rect(st),statusRects=[st,...document.querySelectorAll('.t15-flow-toast')].map(rect);
      const hits=[];
      btns.forEach(e=>{const b=rect(e);for(const q of statusRects){
        if(Math.min(q.right,b.right)-Math.max(q.x,b.x)>2&&
           Math.min(q.bottom,b.bottom)-Math.max(q.y,b.y)>2)
          hits.push(e.className||e.tagName);
      }});
      const floating=[...document.body.children].filter(e=>
         getComputedStyle(e).position==='fixed'&&e.textContent?.trim()===tx);
      const sheet=document.querySelector('#a-sheet')?.getBoundingClientRect();
      return {mapLabel:st.textContent,box:a,statusRole:st.getAttribute('role'),
         mapAboveSheet:!!sheet&&a.bottom<=sheet.top+2,
         noticeRects:statusRects,controls:btns.map(e=>({
           name:e.className||e.tagName,rect:rect(e)})),overlaps:hits,
         floatingErrors:floating.length};
    }""")
    # Map failure can be represented by the EXISTING road-unavailable status.
    # No duplicate red overlay is needed; it must not intersect tools/cash.
    if not r or not r["mapLabel"].strip() or not r["statusRole"] or not r["mapAboveSheet"] or r["overlaps"] or r["floatingErrors"]:
        raise AssertionError("F-09 core map toast still covers mission tools: "+str(r))
    return r

def NOTIFY(pg,app,w,h):
    # Core (not a fake button/DOM fixture) creates a fixed bottom:96px toast.
    # The shared policy must convert it to normal flow in ALL FOUR app shells.
    if app=="customer":
        pg.evaluate("() => {go('menu',{store:STORES[0].n});openItem('i1')}")
        pg.locator("#shn").wait_for(state="visible")
        pg.locator("#shn").focus()
    elif app=="merchant":
        pg.evaluate("() => rjOpen('ord0')")
    elif app=="driver":
        pg.evaluate("() => {const o=mine();if(o){o.status='pickedup';o.arrivedCustAt=Date.now();}render()}")
    pg.evaluate("() => TLB.toast(TLB.t('err_closed'),true)")
    pg.wait_for_timeout(105)
    r=pg.evaluate("""() => {
      const e=document.querySelector('.t15-flow-toast');
      if(!e)return null;
      const rect=x=>{const r=x.getBoundingClientRect();return {
        x:r.left,y:r.top,right:r.right,bottom:r.bottom,w:r.width,h:r.height}};
      const a=rect(e),visible=n=>{const r=n.getBoundingClientRect(),s=getComputedStyle(n);
        return s.display!=='none'&&s.visibility!=='hidden'&&r.width>0&&r.height>0;
      };
      // Strictly inspect EVERY visible button/input and nearby text in the UI.
      const activePanel=e.closest('.sheet,.ov');
      const nodes=[...document.querySelectorAll('#app button,#app a[href],#app input,#app textarea,#app h1,#app h2,#app h3,#app p,#app label,#app .d6-ch,#app .a-collect-line')].filter(n=>
        n!==e&&!n.contains(e)&&!e.contains(n)&&visible(n)&&
        (!activePanel||activePanel.contains(n)));
      // If a modal is open, geometrically coincident background controls are
      // NOT visible through its backdrop and are correctly excluded.
      const overlap=nodes.filter(n=>{const b=rect(n);return Math.min(a.right,b.right)-Math.max(a.x,b.x)>2&&
        Math.min(a.bottom,b.bottom)-Math.max(a.y,b.y)>2;});
      return {mode:getComputedStyle(e).position,box:a,
        parent:e.parentElement?.className||e.parentElement?.id||'',
        activePanel:activePanel?.className||'none',
        overlapped:overlap.map(n=>({name:n.className||n.tagName,text:n.textContent?.slice(0,35)})),
        checkedNodes:nodes.length};
    }""")
    if not r or r["mode"]!="static" or r["overlapped"] or r["checkedNodes"]<3:
        raise AssertionError("NOTIFY-01 shared core toast obscures controls or text: "+str(r))
    return r

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
 ("NOTIFY-01","customer",lambda p,w,h:NOTIFY(p,"customer",w,h)),
 ("NOTIFY-01","driver",lambda p,w,h:NOTIFY(p,"driver",w,h)),
 ("NOTIFY-01","merchant",lambda p,w,h:NOTIFY(p,"merchant",w,h)),
 ("NOTIFY-01","admin",lambda p,w,h:NOTIFY(p,"admin",w,h)),
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
                            if case=="F-03":
                                screenshot(pg,"F-03-top",app,lang,w)
                                pg.locator(".customer-quick").scroll_into_view_if_needed(timeout=2500)
                                pg.wait_for_timeout(90)
                            if case=="F-05":
                                screenshot(pg,"F-05-payment-top",app,lang,w)
                                pg.evaluate("window.scrollTo(0,document.body.scrollHeight)")
                                pg.wait_for_timeout(90)
                            rows.append({"id":case,"app":app,"lang":lang,"width":w,"status":"PASS","geometry":result if isinstance(result,dict) else None})
                        except Exception as err:
                            detail=str(err)
                            if case=="F-02" and pg:
                                detail+=" | category_metrics="+str(pg.evaluate("""() => ({
                                   cats:[...document.querySelectorAll('#app .d6-ct b')].map(e=>({
                                   txt:e.textContent,sw:e.scrollWidth,cw:e.clientWidth,
                                   fs:getComputedStyle(e).fontSize,ws:getComputedStyle(e).whiteSpace})),
                                   promo:(() => {const e=document.querySelector('#app .d6-bt.d6tp .tt');if(!e)return null;
                                     const b=e.closest('.d6-bt').getBoundingClientRect(),range=document.createRange();
                                     range.selectNodeContents(e);
                                     return {text:e.textContent,fs:getComputedStyle(e).fontSize,panelRight:b.right,
                                       textLines:[...range.getClientRects()].map(x=>({left:x.left,right:x.right}))};})()
                                })"""))
                            errors.append({"id":case,"app":app,"lang":lang,"width":w,"type":type(err).__name__,"message":detail[:1400]})
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
    refs={"NOTIFY-01":("customer","home"),"F-01":("customer","home"),"F-02":("customer","home"),"F-03":("customer","track"),"F-04":("customer","item-sheet"),
      "F-05":("customer","pay"),"F-06":("merchant","item-edit"),"F-07":("merchant","reject-sheet"),"F-08":("merchant","profile"),
      "F-09":("driver","step4"),"F-10":("admin","tab0")}
    for row in rows:
        app,sc=refs[row["id"]]
        if row["id"]=="NOTIFY-01":
            sc={"customer":"item-sheet","driver":"step4","merchant":"reject-sheet","admin":"tab0"}[app]
        before=f"../full-audit/{app}/{sc}_{row['lang']}_{row['width']}.png"
        after=pathlib.Path(row.get("image","")).name
        order.append(f"- {row['id']} {row['lang']}/{row['width']}: [{row['status']}](REPORT.json) | [BEFORE]({before}) | [AFTER]({after})")
    (OUT/"INDEX.md").write_text("\n".join(order)+"\n")
    print("BRIEF15_WEBKIT_COVERAGE",len(rows),"PASS",len(rows)-len(errors),"FAIL",len(errors))
    for err in errors[:12]:print("BRIEF15_WEBKIT_FAIL",json.dumps(err,ensure_ascii=False))
    return 1 if errors or len(rows)!=len(dims)*len(langs)*len(tests) else 0
if __name__=="__main__":sys.exit(main())
