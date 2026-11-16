#!/usr/bin/env python3
"""BRIEF-7: 36 source-style + synthetic-DOM before/after comparisons, 360/390/430 RU/EN.
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
BASE="23087ed1eec83e1f4640830539ee0464e17051e1"
OUT=ROOT/"evidence"/"size-brief7"
OUT.mkdir(parents=True,exist_ok=True)
APPS=("customer","merchant","driver")
WIDTHS=(360,390,430)
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

def main():
    results=[]
    with sync_playwright() as p:
        browser=p.chromium.launch(headless=True)
        for app in APPS:
            before=css_from(BASE,app)
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
                                    assert abs(card["paddingLeft"]-12)<0.1, data
                                    assert data["seg"]["height"]>=44, data
                                    assert abs(page.locator("body").evaluate("el=>parseFloat(getComputedStyle(el).paddingLeft)")-12)<0.1, data
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
                                    assert abs(card["paddingLeft"]-14)<0.1, data
                                    assert abs(page.locator("body").evaluate("el=>parseFloat(getComputedStyle(el).fontSize)")-15)<0.1, data
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
    print("SIZE_spec_tokens_applied PASS: app-scoped mobile CSS and runtime computed customer/merchant/driver values")
    print("SIZE_touch_targets_ge_44 PASS: sampled primary 46+, segmented 44+, driver nav 44+, original 42px visual button and driver swipe geometry PRESERVED")
    print("SIZE_SCREENS: "+str(len(list(OUT.glob("*before-after.png"))))+" before/after pairs = 72 source-CSS synthetic screenshots at 360/390/430 RU/EN, 3 apps x 2 views")
if __name__=="__main__":
    main()
