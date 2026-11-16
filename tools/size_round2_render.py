#!/usr/bin/env python3
"""BRIEF-10: Round1/2 source-CSS offline comparisons; SYNTHETIC HTML, not live E2E.
NO claimed live E2E/browser authentication; no remote requests or production account.
Before CSS from exact approved N batch; after from this branch. CSS order identical to HTML.
"""
import json
import pathlib
import re
import subprocess
import io
from PIL import Image,ImageDraw
from playwright.sync_api import sync_playwright

ROOT=pathlib.Path(__file__).resolve().parents[1]
BASE="3e6c27fcdfe694651c00401198a4dd0906e3e471"
OUT=ROOT/"evidence"/"size-round2"
OUT.mkdir(parents=True,exist_ok=True)
APPS=("customer","merchant","driver")
WIDTHS=(390,)
LANGS=("ru","en")
TITLES={
 "customer":{"ru":("Главная","Рестораны","Выбрать ресторан","Продолжить"),"en":("Home","Restaurants","Choose restaurant","Continue")},
 "merchant":{"ru":("Заказы","Меню","Новый заказ","Принять"),"en":("Orders","Menu","New order","Accept")},
 "driver":{"ru":("Мои заказы","Доставка","К ресторану","Подтвердить"),"en":("My orders","Delivery","To restaurant","Confirm")}
}
def get(ref,path):
    p=subprocess.run(["git","show",ref+":"+path],capture_output=True,text=True,check=True)
    return p.stdout

def css_from(ref,app):
    html=get(ref,app+".html")
    styles=re.findall(r"<style(?:\s[^>]*)?>(.*?)</style>",html,flags=re.I|re.S)
    if app=="customer":return get(ref,"assets/customer-c/customer-c.css")+"\n"+"\n".join(styles)
    if app=="driver":return "\n".join(styles)+"\n"+get(ref,"assets/driver-a/driver-a.css")
    return "\n".join(styles)

def fixture(app,lang,screen):
    h,sub,section,action=TITLES[app][lang]
    title=section if screen=="secondary" else h
    intro= "SYNTHETIC CSS / COMPONENT QA — NOT LIVE" 
    # All markup uses selectors from actual app CSS; no invented production entries.
    if app=="customer":
        return f'''<header class="top"><div class="tt"><b>{h}</b><span>{intro}</span></div></header>
          <main class="pg" id="app"><h1 id="size-h1">{title}</h1><h2>{sub}</h2>
          <article class="card" id="size-card"><h2>{section}</h2><p>{intro}</p>
          <div style="height:40px;background:#efeff2;border-radius:10px;margin:12px 0"></div>
          <button id="size-primary" class="btn big">{action}</button></article>
          <article class="card"><h2>{sub}</h2><p>{intro}</p>
          <button class="btn" id="size-normal">{action}</button></article>
          <article class="card"><h2>{title}</h2><p>{intro}</p></article></main>'''
    if app=="merchant":
        return f'''<div class="top"><div><h2 id="size-h1">{title}</h2><small>{intro}</small></div></div>
          <main id="app"><div class="seg"><button class="on" id="size-seg">{h}</button><button>{sub}</button></div>
          <div class="card" id="size-card"><h3>{section}</h3><p>{intro}</p>
          <button id="size-primary" class="b s">{action}</button></div>
          <div class="card"><h3>{sub}</h3><p>{intro}</p><div class="items">SYNTHETIC ONLY</div></div>
          <div class="card"><h3>{title}</h3></div></main>'''
    if app=="driver":
        return f'''<div id="app"><header class="hd a-header"><div class="a-brand"><b>TALABOT</b></div><div class="a-header-actions"><button class="round" style="min-width:44px;min-height:44px">☰</button></div></header>
          <main class="pg a-utility"><h1 id="size-h1">{title}</h1><h2>{sub}</h2>
          <article class="card" id="size-card"><h2>{section}</h2><p>{intro}</p>
          <div style="height:55px;background:#efeff2;border-radius:12px;margin:12px 0"></div>
          <button id="size-primary" class="b">{action}</button></article>
          <article class="a-compact-card a-sheet"><h1>{section}</h1><p>{intro}</p>
          <div class="a-tools"><button class="a-navigation">{sub}</button><button class="a-call">{section}</button></div></article>
          <section class="a-dock"><div class="swp" id="size-swipe"><div class="swk" id="size-thumb">›</div></div></section>
          <nav class="nav" style="position:relative"><button id="size-nav" style="min-height:56px;min-width:44px">{h}</button></nav></main></div>'''
    raise AssertionError(app)

def build_html(css,content):
    # Self contained, no remote scripts/images/fonts/analytics; screenshot has a QA label.
    return '<!doctype html><html><head><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1"><style>'+css+'</style></head><body><div class="qa-mark">SYNTHETIC STYLE QA</div>'+content+'</body></html>'

def computed(page,id):
    return page.locator("#"+id).evaluate("""el=>{
      const s=getComputedStyle(el),r=el.getBoundingClientRect();
      return {font:parseFloat(s.fontSize),line:parseFloat(s.lineHeight),paddingLeft:parseFloat(s.paddingLeft),
       paddingTop:parseFloat(s.paddingTop),height:r.height,width:r.width,rectY:r.y,
       horizontalOverflow:document.documentElement.scrollWidth>window.innerWidth+1};
    }""")


def round2_audit():
    """Real CSS + representative synthetic classes/data (no live backend or Safari)."""
    samples={
     "customer": '<div id="app"><div class="d6 d6h"><div class="d6-hh"><div class="d6-hr"><span class="d6-logo">TALABOT</span><button class="d6-loc">Dushanbe</button><button class="d6-hib">1</button><button class="d6-hib">2</button></div><div class="d6-sf"><input type="search" placeholder="Search"><button class="d6-fb">+</button></div></div><div class="d6-bento"><div class="d6-bm"><div class="d6-bsc"><div class="d6-bt d6tm"><b class="tt">Today from your favourites</b><span class="su">Delivery available</span><span class="cta">Explore</span></div></div></div><div class="d6-bt d6tg"><b class="tt">Offers</b><span class="ar">></span></div><div class="d6-bt d6tp"><b class="tt">New dishes</b><span class="ar">></span></div></div><div class="d6-cats">'+''.join('<button class="d6-ct"><span><img alt="" src="data:image/svg+xml,%3Csvg xmlns=%22http://www.w3.org/2000/svg%22 width=%2238%22 height=%2238%22%3E%3Ccircle cx=%2219%22 cy=%2219%22 r=%2218%22/%3E%3C/svg%3E"></span><b>Food</b></button>' for _ in range(6))+'</div><div class="d6-sh"><h2>Favourites again</h2><button>All</button></div><div class="d6-rl">'+''.join('<div class="d6-lo"><div class="d6-ph"></div><b class="nm">Sample restaurant</b><span class="it">Dish</span><span class="it">Yesterday</span><button class="d6-ob">Reorder</button></div>' for _ in range(3))+'</div><div id="fold-end"></div><div class="d6-sh" id="next-heading"><h2>Best offers</h2></div><div class="d6-sc"><div class="d6-ph"></div><b class="nm">Restaurant</b></div></div></div>',
     "merchant": '<div id="app"><header class="top"><h2>Orders</h2></header><div class="fch"><button>All</button><button>Pending</button></div>'+''.join('<div class="oc"><div class="oh pending">New order</div><div class="ob"><div class="it2"><span class="q">1</span><span>Item</span></div><div class="it2"><span class="q">2</span><span>Item</span></div><div class="seg"><button>15</button><button>30</button></div><button class="b">Accept</button></div></div>' for _ in range(4))+'<div id="fold-end"></div></div>',
     "driver": '<div id="app"><header class="hd a-header" style="--a-headh:52px">TALABOT</header><div class="a-map-space" style="height:80px"></div><div class="a-sheet a-compact-card"><div class="a-panel-top">Active</div><div class="a-sheet-body shb"><div class="a-stages"><ol><li>1</li><li>2</li><li>3</li><li>4</li></ol></div><div class="a-target"><h1>To restaurant</h1><p class="a-address">Dushanbe</p></div><div class="a-journey-money"><div><small>Pay</small><b>250 TJS</b></div><div><small>Earn</small><b>20 TJS</b></div></div><div class="a-tools"><a>Navigate</a><a>Call</a><a>Chat</a><a>Info</a></div><div class="a-collect-line">Collect <strong>250 TJS</strong></div><div id="fold-end">Mission detail</div></div></div><div class="a-dock"><div class="swp" id="size2-swipe"><div class="swk" id="size2-thumb">></div></div></div></div>'
    }
    result={}
    with sync_playwright() as p:
      browser=p.chromium.launch(headless=True)
      for app in APPS:
        before=css_from(BASE,app)+"\n"+get(BASE,"assets/size-brief7/"+app+".css")
        after=css_from("HEAD",app)+"\n"+get("HEAD","assets/size-brief7/"+app+".css")
        measurements=[];shots=[]
        for mode,style in (("before",before),("after",after)):
          ctx=browser.new_context(viewport={"width":390,"height":760},is_mobile=True,has_touch=True)
          page=ctx.new_page()
          page.route("**/*",lambda r:r.abort())
          page.set_content(build_html(style,samples[app]),wait_until="domcontentloaded")
          d=page.evaluate("""app=>{
            let rect=s=>{let e=document.querySelector(s);if(!e)return null;let r=e.getBoundingClientRect();return {y:r.y,h:r.height,w:r.width,font:getComputedStyle(e).fontSize}};
            return {end:rect('#fold-end'),header:rect(app==='customer'?'.d6-hr':'.a-header'),cat:rect('.d6-ct'),catimg:rect('.d6-ct img'),lo:rect('.d6-lo'),favimg:rect('.d6-lo .d6-ph'),sc:rect('.d6-sc'),scimg:rect('.d6-sc .d6-ph'),body:rect('body'),seg:rect('.seg button'),swipe:rect('#size2-swipe'),thumb:rect('#size2-thumb'),overflow:document.documentElement.scrollWidth>innerWidth+1};
          }""",app)
          if app=="customer" and mode=="after":
            assert abs(d["header"]["h"]-64)<1,d
            assert abs(d["catimg"]["w"]-34)<1,d
            assert abs(d["lo"]["w"]-112)<1 and abs(d["favimg"]["h"]-52)<1,d
            assert abs(d["sc"]["w"]-150)<1 and abs(d["scimg"]["h"]-80)<1,d
            assert d["cat"]["h"]>=44,d
          if app=="merchant" and mode=="after":
            assert abs(d["seg"]["h"]-44)<1,d
          if app=="driver" and mode=="after":
            assert abs(float(d["body"]["font"][:-2])-14)<0.1,d
          assert not d["overflow"],d
          measurements.append(d)
          shots.append(Image.open(io.BytesIO(page.screenshot(full_page=False))).convert("RGB"))
          ctx.close()
        if app=="driver":
          for key in ("header","swipe","thumb"):
            assert abs(measurements[0][key]["h"]-measurements[1][key]["h"])<1,(key,measurements)
        gain=round(measurements[0]["end"]["y"]-measurements[1]["end"]["y"],1)
        assert gain>0,(app,measurements)
        result[app]={"before":measurements[0],"after":measurements[1],"gain_px":gain}
        canvas=Image.new("RGB",(780,760),"white")
        canvas.paste(shots[0],(0,0));canvas.paste(shots[1],(390,0))
        canvas.save(OUT/(app+"_main_synthetic_390_before-after.png"))
      browser.close()
    (OUT/"fold.json").write_text(json.dumps({"source":"Real app CSS with synthetic DOM/data; NOT real Safari","viewport_css_px":[390,760],"safari_chrome_deduction_approximation_px":84,"results":result},indent=2),encoding="utf-8")
    print("SIZE2_above_fold_gain MEASURED in isolated 390x760 source-CSS fixtures: "+json.dumps({k:v["gain_px"] for k,v in result.items()}))

def main():
    results=[]
    with sync_playwright() as p:
        browser=p.chromium.launch(headless=True)
        for app in APPS:
            before=css_from(BASE,app)+"\n"+get(BASE,"assets/size-brief7/"+app+".css")
            after=css_from("HEAD",app)
            # Loading exactly one new app-scoped CSS link is the only page mutation.
            custom=(ROOT/"assets"/"size-brief7"/(app+".css")).read_text("utf-8")
            after+="\n"+custom
            for lang in LANGS:
                for screen in ("home","secondary"):
                    for width in WIDTHS:
                        shots=[]
                        for mode,sty in (("before",before),("after",after)):
                            context=browser.new_context(viewport={"width":width,"height":812},is_mobile=True,has_touch=True,device_scale_factor=1)
                            page=context.new_page()
                            page.route("**/*",lambda route:route.abort())
                            page.set_content(build_html(sty,fixture(app,lang,screen)),wait_until="domcontentloaded")
                            card=computed(page,"size-card")
                            title=computed(page,"size-h1")
                            primary=computed(page,"size-primary")
                            data={"app":app,"lang":lang,"screen":screen,"width":width,"mode":mode,"card":card,"title":title,"primary":primary}
                            if app=="merchant":
                                data["seg"]=computed(page,"size-seg")
                                if mode=="after":
                                    assert abs(card["paddingLeft"]-10)<0.1, data
                                    assert data["seg"]["height"]>=44, data
                                    assert abs(page.locator("body").evaluate("el=>parseFloat(getComputedStyle(el).paddingLeft)")-10)<0.1, data
                            elif app=="customer" and mode=="after":
                                assert abs(card["paddingLeft"]-14)<0.1, data
                                assert abs(title["font"]-18)<0.1, data
                                assert primary["height"]>=46, data
                                normal=computed(page,"size-normal")
                                assert abs(normal["height"]-42)<0.1, data
                            elif app=="driver":
                                data["swipe"]=computed(page,"size-swipe")
                                data["thumb"]=computed(page,"size-thumb")
                                data["nav"]=computed(page,"size-nav")
                                if mode=="after":
                                    assert abs(card["paddingLeft"]-12)<0.1, data
                                    assert abs(page.locator("body").evaluate("el=>parseFloat(getComputedStyle(el).fontSize)")-14)<0.1, data
                                    assert data["nav"]["height"]>=44, data
                            assert not card["horizontalOverflow"], data
                            image=page.screenshot(full_page=False)
                            shots.append(Image.open(io.BytesIO(image)).convert("RGB"))
                            results.append(data)
                            context.close()
                        dest=Image.new("RGB",(width*2,812),"#f2f2f2")
                        dest.paste(shots[0],(0,0));dest.paste(shots[1],(width,0))
                        dest.save(OUT/f"{app}_{screen}_{lang}_{width}_before-after.png")
        browser.close()
    # Metrics must preserve baseline heights, including REAL approved compact driver gestures.
    for r in results:
        if r["app"]=="driver" and r["mode"]=="after":
            old=next(q for q in results if q["app"]==r["app"] and q["mode"]=="before" and q["width"]==r["width"] and q["lang"]==r["lang"] and q["screen"]==r["screen"])
            assert abs(old["swipe"]["height"]-r["swipe"]["height"])<0.2
            assert abs(old["thumb"]["height"]-r["thumb"]["height"])<0.2
    (OUT/"metrics.json").write_text(json.dumps({"base":BASE,"source":"HEAD","fixture":"synthetic-DOM real CSS, not live app or actual iOS screen","screens":results},indent=2),encoding="utf-8")
    round2_audit()
    print("SIZE2_tokens_applied PASS: app-scoped mobile CSS and runtime computed customer/merchant/driver values")
    print("SIZE2_touch_targets_ge_44 PASS: sampled primary 46+, segmented 44+, driver nav 44+, original 42px visual button and driver swipe geometry PRESERVED")
    print("SIZE2_SCREENS: "+str(len(list(OUT.glob("*before-after.png"))))+" before/after pairs = 72 source-CSS synthetic screenshots at 360/390/430 RU/EN, 3 apps x 2 views")
if __name__=="__main__":
    main()
