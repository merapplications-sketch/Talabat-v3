#!/usr/bin/env python3
"""TALABOT approved SIZE-7 comparative CSS evidence: synthetic labels with REAL
source CSS, 3 apps × 3 CSS widths × RU/EN × before/after. NO auth/network.
Not screenshots of authenticated live application or physical iPhone Safari.
"""
from pathlib import Path
from html import escape
from playwright.sync_api import sync_playwright
import re,json,hashlib

ROOT=Path(__file__).resolve().parents[1]
OUTPUT=ROOT/"evidence"/"size-three-apps-20261116"
OUTPUT.mkdir(parents=True,exist_ok=True)
SOURCE_SHA="23087ed1eec83e1f4640830539ee0464e17051e1"
APPS=("customer","merchant","driver")
WIDTHS=(360,390,430)
LANGS=("ru","en")

LABELS={
 "ru":{"title":"Главная · заказы и услуги","sub":"Подтверждение заказа","detail":"Ресторан и заказ — длинное название","action":"Продолжить","second":"Заказы","third":"Меню","help":"Подтвержденные данные"},
 "en":{"title":"Home · Orders and services","sub":"Order confirmation","detail":"Restaurant and order — long sample name","action":"Continue","second":"Orders","third":"Menu","help":"Confirmed information"},
}

def base_style(app):
    s=(ROOT/(app+".html")).read_text(encoding="utf-8")
    m=re.search(r"<style>(.*?)</style>",s,re.S|re.I)
    if not m:raise AssertionError("source CSS missing: "+app)
    external=""
    if app=="customer":
        external=(ROOT/"assets/customer-c/customer-c.css").read_text(encoding="utf-8")
    elif app=="driver":
        external=(ROOT/"assets/driver-a/driver-a.css").read_text(encoding="utf-8")
    # Match ACTUAL source link order: customer external stylesheet precedes
    # its inline <style>; Driver Compact A external CSS follows its inline CSS.
    # A reversed cascade would fake the before comparison.
    if app=="driver":
        return m.group(1)+"\n"+external
    return external+"\n"+m.group(1)

def fixture(app,lang,after):
    t=LABELS[lang]
    style=base_style(app)
    if after:
        style+="\n"+(ROOT/"assets"/"size-three-apps-20261116"/(app+".css")).read_text(encoding="utf-8")
    title=escape(t["title"]);sub=escape(t["sub"]);detail=escape(t["detail"])
    action=escape(t["action"]);second=escape(t["second"]);third=escape(t["third"]);helptext=escape(t["help"])
    if app=="customer":
        body=f"""<main class="pg d6c"><div class="d6-head"><h1>{title}</h1></div>
          <h2>{sub}</h2><article class="d6-card" id="source-card">{detail}</article>
          <section class="card" id="target-card"><h2>{third}</h2><p>{helptext}</p></section>
          <button type="button" class="btn big" id="primary">{action}</button></main>"""
    elif app=="merchant":
        body=f"""<main class="w"><header class="top"><div><small>{third}</small><h2>{title}</h2></div></header>
          <div class="seg"><button type="button" id="target-seg" class="on">{second}</button><button type="button">{third}</button></div>
          <article class="card" id="target-card"><h3>{sub}</h3><p>{detail}</p>
          <button class="b s" id="primary">{action}</button></article></main>"""
    else:
        body=f"""<header class="hd a-header" id="target-header"><strong>TALABOT</strong><button class="round" id="round">⋯</button></header>
          <main class="a-utility"><h1>{title}</h1><h2>{sub}</h2><article class="card a-offer" id="target-card">
          <h2>{detail}</h2><p>{helptext}</p><button class="b" id="primary">{action}</button></article></main>
          <nav class="nav"><button type="button" id="target-nav">{second}</button><button type="button">{third}</button></nav>"""
    return (f'<!doctype html><html lang="{lang}"><head><meta charset="utf-8">'
        '<meta name="viewport" content="width=device-width,initial-scale=1">'
        f'<style>{style}</style><style>'
        'body{min-height:100vh}main{max-width:430px;margin-inline:auto}'
        'main p{margin:12px 0}.a-utility{padding-bottom:110px}'
        '</style></head><body>'+body+'</body></html>')

def measure(page,app):
    return page.evaluate("""app => {
      const s=q=>document.querySelector(q);
      const val=(q,name)=>s(q)?getComputedStyle(s(q))[name]:null;
      const h=q=>s(q)?Math.round(s(q).getBoundingClientRect().height*100)/100:null;
      const result={
        bodyFont:val('body','fontSize'),bodyLine:val('body','lineHeight'),
        bodyPaddingLeft:val('body','paddingLeft'),
        h1Font:val('h1','fontSize'),h2Font:val('h2','fontSize'),
        cardPaddingLeft:val('#target-card','paddingLeft'),
        primaryHeight:h('#primary'),
        scrollWidth:document.documentElement.scrollWidth,
        viewportWidth:innerWidth
      };
      if(app==='merchant')result.segmentHeight=h('#target-seg');
      if(app==='driver'){
        result.headerHeight=h('#target-header');
        result.roundHeight=h('#round');
        result.navHeight=h('#target-nav');
      }
      return result;
    }""",app)

def assert_targets(app,v,variant):
    if variant!="after":return
    if app=="customer":
        assert v["bodyFont"]=="13px",v
        assert v["h1Font"]=="18px",v
        assert v["cardPaddingLeft"]=="14px",v
        assert v["primaryHeight"]>=46,v
    if app=="merchant":
        assert v["bodyPaddingLeft"]=="12px",v
        assert v["cardPaddingLeft"]=="12px",v
        assert v["segmentHeight"]>=44,v
        assert v["primaryHeight"]>=42,v # 42px original is owner-locked
    if app=="driver":
        assert v["bodyFont"]=="15px",v
        assert v["bodyLine"]=="21px",v
        assert v["cardPaddingLeft"]=="14px",v
        assert v["primaryHeight"]>=44 and v["roundHeight"]>=44 and v["navHeight"]>=56,v
    assert v["scrollWidth"]<=v["viewportWidth"]+2,v

records=[]
with sync_playwright() as p:
    browser=p.chromium.launch(headless=True)
    ctx=browser.new_context(is_mobile=True,has_touch=True,device_scale_factor=2)
    page=ctx.new_page()
    requests=[]
    page.route("**/*",lambda route:(requests.append(route.request.url),route.abort()))
    for app in APPS:
        for lang in LANGS:
            for width in WIDTHS:
                pair={}
                for variant in ("before","after"):
                    page.set_viewport_size({"width":width,"height":844})
                    page.set_content(fixture(app,lang,variant),wait_until="domcontentloaded")
                    value=measure(page,app)
                    assert_targets(app,value,variant)
                    filename=f"{app}_{lang}_{width}_{variant}_synthetic_css.png"
                    page.screenshot(path=str(OUTPUT/filename),full_page=False)
                    pair[variant]={"file":filename,**value}
                # Immutable touch geometry: never shrink previously compliant targets.
                if app=="driver":
                    assert pair["after"]["headerHeight"]==pair["before"]["headerHeight"],"map header offset changed"
                    for k in ("primaryHeight","roundHeight","navHeight"):
                        assert pair["after"][k]>=pair["before"][k],(k,pair)
                if app=="customer":
                    assert pair["after"]["primaryHeight"]==pair["before"]["primaryHeight"],pair
                if app=="merchant":
                    assert pair["after"]["primaryHeight"]==pair["before"]["primaryHeight"],pair
                records.append({"app":app,"lang":lang,"width":width,**pair})
    ctx.close()
    browser.close()

manifest={
 "source_candidate_parent_sha":SOURCE_SHA,
 "scope":"customer,merchant,driver ONLY; admin excluded",
 "real_source_css":True,
 "authenticated_app_screenshots":False,
 "native_iphone_safari":False,
 "synthetic_fixture":True,
 "network_attempts_blocked":len(requests),
 "keyboard_not_emulated":True,
 "viewport_css_widths":WIDTHS,
 "languages":LANGS,
 "comparisons":records
}
(OUTPUT/"EVIDENCE.json").write_text(json.dumps(manifest,ensure_ascii=False,indent=2),encoding="utf-8")
print("PASS SIZE_spec_tokens_applied: 3 apps, source-styled BEFORE/AFTER fixtures, RU/EN, 360/390/430 CSS px")
print("PASS SIZE_touch_targets_ge_44: major actionable controls protected; original 42px merchant/customer ordinary controls preserved exactly")
print("SIZE_CAPTURE: "+str(len(records))+" before/after comparisons; "+str(len(records)*2)+" PNG (SYNTHETIC CSS fixtures; NOT actual authenticated app/iPhone)")
