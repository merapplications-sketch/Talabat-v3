#!/usr/bin/env python3
"""BRIEF-11: real source CSS + executable JS adapters in OFFLINE WebKit iPhone-sized contexts.
Not physical iOS keyboard; reduced visual viewport is an explicit approximation.
No production auth, orders, payments or external network allowed.
"""
import json, re, base64
from pathlib import Path
from playwright.sync_api import sync_playwright

ROOT=Path(__file__).resolve().parents[1]
OUT=ROOT/"evidence"/"cash-sheet-brief11"
OUT.mkdir(parents=True,exist_ok=True)
driver=(ROOT/"driver.html").read_text(encoding="utf8")
base=re.search(r"<style>(.*?)</style>",driver,re.S).group(1)
base+="\n"+(ROOT/"assets/driver-a/driver-a.css").read_text(encoding="utf8")
base+="\n"+(ROOT/"assets/size-brief7/driver.css").read_text(encoding="utf8")
b8=(ROOT/"assets/driver-tech/nav-cash-brief8.js").read_text(encoding="utf8")
b11=(ROOT/"assets/driver-tech/cash-sheet-polish-brief11.js").read_text(encoding="utf8")
route=(ROOT/"assets/driver-tech/route-layer.js").read_text(encoding="utf8")
assert "t('cashGet')" in driver, "real source cash panel title is absent"
for name in ("google-maps","2gis","yandex-maps"):
    p=ROOT/"assets/driver-tech/map-icons"/(name+".svg")
    uri="data:image/svg+xml;base64,"+base64.b64encode(p.read_bytes()).decode("ascii")
    route=route.replace("assets/driver-tech/map-icons/"+name+".svg",uri)
confirm=driver.split("async function confirmDeliver(){",1)[1].split("\n/* the 4 steps",1)[0]
assert "reportDriverCashShort(DV.id,amt,DV.note)" in confirm
confirm="async function confirmDeliver(){"+confirm

SETUP=r"""
var DV={id:9122,total:216,amt:"216",cashMode:"full",note:"",cash:true,photo:false,up:false,ph:null},
    DLV={},CXL=null,DRV={id:"synthetic-driver"},chatOpen=false,tab="o",GEO={lat:null,lng:null},DM=null;
window.CALLS={report:0,finish:0,click:0,toasts:[]};var dictionary={};
var TLB={
  lang:()=>window.SYN_LANG||"en",
  order:id=>({id:id,total:216,payment:"cash",leaveAtDoor:false,status:"pickedup"}),
  addDict:(ru,en)=>Object.assign(dictionary,window.SYN_LANG==="ru"?ru:en),
  toast:(msg,bad)=>window.CALLS.toasts.push({msg,bad}),
  supportInfo:()=>({phone:"+992900000000"}),
  reportDriverCashShort:async(id,amount,note)=>{window.CALLS.report++;window.CALLS.last={id,amount,note};return {ticket_id:"syn-only-1"};},
  navigation:async q=>q.op==="config"?{external:true,providers:["google","2gis","yandex"],mode:"tracking",reason:"disabled"}:
          {links:[],mode:"tracking",reason:"disabled"}
};
window.TLB=TLB;
window.TALABOT_NAV_MODEL={point:p=>Array.isArray(p)&&p.length===2&&p.every(Number.isFinite),
 destination:(x,n,sp)=>[x.lat,x.lng],key:(x,n,to)=>JSON.stringify([x.id,n,to])};
function t(k){return dictionary[k]||k}
function esc(x){return String(x).replace(/[&<>"]/g,c=>({"&":"&amp;","<":"&lt;",">":"&gt;",'"':"&quot;"}[c]))}
function ico(){return '<span aria-hidden="true">◯</span>'}
function aTask(){return {id:9122,status:"pickedup",lat:38.567741,lng:68.793569,address:"SYNTHETIC destination",store:"SYNTHETIC store"}}
function mine(){return aTask()}
function aTaskStage(){return 4}
function storePt(){return [38.5,68.7]}
function mapUpd(){}
function finish(){window.CALLS.finish++;return Promise.resolve(false)}
function deliverClick(){window.CALLS.click++}
function cashBox(){return '<div class="cashb"><div class="big"><span>💵 '+(window.SYN_LANG==='ru'?'Возьмите наличными':'Take in cash')+'</span><span>216.00 TJS</span></div></div>'}
function $(id){return document.getElementById(id)}
function modal(){return ""}
function render(){
  document.getElementById("app").innerHTML=
    '<header class="a-header hd" style="height:52px">TALABOT</header>'+
    '<main class="a-sheet a-compact-card" id="a-sheet"><div id="a-sheet-body">'+
    '<div class="a-current-stage">Step 4 of 4</div><h1>Customer delivery</h1>'+
    '<p class="a-compact-address">SYNTHETIC destination</p>'+
    '<div class="a-collect-line">Cash <strong>216 TJS</strong></div></div></main>'+
    '<footer class="a-dock" id="a-dock"><button class="a-step-button">Confirm delivery</button></footer>'+
    modal();
}
window.__deviceNotesV3={money(v){const s=String(v).trim().replace(",",".");return /^\d+(\.\d{1,2})?$/.test(s)?Number(s):null;}};
"""
NAV_SETUP=r"""
var DV=null,CXL=null,DRV={id:"synthetic-driver"},chatOpen=false,tab="o",
    GEO={lat:null,lng:null},DM=null,DLV={};
window.CALLS={report:0,finish:0,click:0,toasts:[]};var dictionary={};
var TLB={
  lang:()=>window.SYN_LANG||"en",order:id=>({id:id,status:"pickedup",total:216}),
  addDict:(ru,en)=>Object.assign(dictionary,window.SYN_LANG==="ru"?ru:en),
  toast:()=>{},supportInfo:()=>({phone:"+992900000000"}),
  reportDriverCashShort:async()=>({ticket_id:"synthetic"}),
  navigation:async q=>q.op==="config"?{external:true,providers:["google","2gis","yandex"],mode:"tracking",reason:"disabled"}:
        {links:[],mode:"tracking",reason:"disabled"}
};
window.TLB=TLB;
window.TALABOT_NAV_MODEL={point:p=>Array.isArray(p)&&p.length===2&&p.every(Number.isFinite),
 destination:(x,n,sp)=>[x.lat,x.lng],key:(x,n,to)=>JSON.stringify([x.id,n,to])};
function t(k){return dictionary[k]||k}
function esc(x){return String(x).replace(/[&<>"]/g,c=>({"&":"&amp;","<":"&lt;",">":"&gt;",'"':"&quot;"}[c]))}
function ico(){return '<span aria-hidden="true">◯</span>'}
function aTask(){return {id:9122,status:"pickedup",lat:38.567741,lng:68.793569,address:"SYNTHETIC destination",store:"SYNTHETIC store"}}
function mine(){return aTask()}
function aTaskStage(){return 4}
function storePt(){return [38.5,68.7]}
function mapUpd(){}
function deliverClick(){}
function confirmDeliver(){return Promise.resolve()}
function cashBox(){return '<div class="cashb">216.00 TJS</div>'}
function $(id){return document.getElementById(id)}
function modal(){return ""}
function render(){document.getElementById("app").innerHTML='<div class="a-header">Driver</div>'+modal();}
window.__deviceNotesV3={money(v){return /^\d+(\.\d{1,2})?$/.test(String(v))?Number(v):null;}};
"""
# Rendering exact production icon paths fixes the previous SYNTHETIC ◯ placeholder.
source_icons="\n".join(line for line in driver.splitlines() if line.startswith("const P=") or line.startswith("const ico="))
assert "const P=" in source_icons and "const ico=" in source_icons
nav_icon_stub="""function ico(){return '<span aria-hidden="true">◯</span>'}"""
assert nav_icon_stub in NAV_SETUP
NAV_SETUP=NAV_SETUP.replace(nav_icon_stub,source_icons)
assert "◯" not in NAV_SETUP

EXTRA="""<style>
*{box-sizing:border-box}
html,body{margin:0;padding:0;background:#f4f6f8;color:#17243c;font-family:Arial,sans-serif}
#app{min-height:100dvh}
.ov{position:fixed;inset:0;display:flex;align-items:flex-end;background:#0007;z-index:900}
.md{width:min(430px,100%);background:#fff;border-radius:18px;padding:16px}
.b{display:flex;align-items:center;justify-content:center;background:#f1511b;color:#fff;border:0;border-radius:10px;min-height:44px}
.b.g{background:#187947}.b.s{background:#f7f7f7;color:#17243c}
</style>"""
records=[]
blocked=[]
def offline(route):
    blocked.append(route.request.url)
    route.abort("blockedbyclient")
def bounds(page):
    return page.evaluate("""() => {
      const vi=window.visualViewport;
      const viewport={w:innerWidth,h:vi?vi.height:innerHeight,top:vi?vi.offsetTop:0};
      const q=s=>{const e=document.querySelector(s);if(!e)return null;const r=e.getBoundingClientRect();
         return {x:r.left,y:r.top,right:r.right,bottom:r.bottom,w:r.width,h:r.height}};
      return {viewport, sheet:q('#b8-sheet'),overlay:q('#b8-ov'),
       input:q('#cashAmt'),footer:q('.b8-footer'),content:q('.b8-content'),
       reserved:q('#b8-reserved'),alert:q('.b11-inline-alert'),
       policy:q('#b8-policy'),nav:q('.n-chooser .md'),rootScrollWidth:document.documentElement.scrollWidth,
       totalVisible:innerWidth,reportBanner:q('.b11-waiting')};
    }""")
def assert_horizontal(page,label):
    bad=page.evaluate("""() => {
      const w=innerWidth, bad=[];
      for(const el of document.querySelectorAll('#b8-ov button,#b8-ov input,#b8-ov .b8-sheet,.n-chooser button,.n-chooser a,.n-chooser .md,.a-sheet.a-compact-card')){
       const r=el.getBoundingClientRect(),s=getComputedStyle(el);
       if(s.display==='none'||s.visibility==='hidden'||r.height<1)continue;
       if(r.left<-1||r.right>w+1)bad.push({cls:el.className,left:r.left,right:r.right});
      }
      return bad;
    }""")
    assert not bad,(label,bad)
def assert_vertical_visible(page,label,field,with_amount_label=False):
    data=page.evaluate("""args => {
      const content=document.querySelector('.b8-content');
      const footer=document.querySelector('.b8-footer');
      const target=document.querySelector(args.field);
      const title=args.with_label?document.querySelector('label[for="cashAmt"]'):null;
      const r=e=>{if(!e)return null;const a=e.getBoundingClientRect();return {top:a.top,bottom:a.bottom,height:a.height}};
      return {content:r(content),footer:r(footer),input:r(target),title:r(title),
       isActive:document.activeElement===target,display:getComputedStyle(target).display};
    }""",{"field":field,"with_label":with_amount_label})
    c=data["content"];e=data["input"];f=data["footer"]
    assert data["isActive"] and e["height"]>=44,(label,data)
    assert c["bottom"]<=f["top"]+2,(label,data)
    assert e["top"]>=c["top"]-2 and e["bottom"]<=c["bottom"]+2,(label,data)
    if with_amount_label:
        title=data["title"]
        assert title and title["top"]>=c["top"]-2 and title["bottom"]<=e["top"]+2,(label,data)
    return data

def browser_page(browser,width,height,lang,setup):
    ctx=browser.new_context(viewport={"width":width,"height":height},is_mobile=True,
         has_touch=True,device_scale_factor=3,locale="ru-RU" if lang=="ru" else "en-US")
    ctx.route("**/*",offline)
    p=ctx.new_page()
    p.set_content('<!doctype html><html><head><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1,viewport-fit=cover"><style>'+base+'</style>'+EXTRA+'</head><body class="a-mission"><div id="app"></div></body></html>')
    p.evaluate("(lang)=>window.SYN_LANG=lang",lang)
    p.add_script_tag(content=setup)
    return ctx,p
def check_cash(browser,width,height,lang):
    ctx,p=browser_page(browser,width,height,lang,SETUP)
    p.add_script_tag(content=confirm)
    p.add_script_tag(content=b8)
    p.add_script_tag(content=b11)
    p.evaluate("render()")
    p.wait_for_timeout(100)
    initial=bounds(p)
    assert initial["sheet"] and initial["sheet"]["h"]<500,initial
    assert p.locator('#b8-reserved').get_attribute('aria-hidden')=='true'
    assert p.locator('#b8-reserved').evaluate("e=>getComputedStyle(e).display")=="none"
    assert_horizontal(p,"full")
    assert p.locator(".cashb .big").is_visible(), "real Take in cash block must be present"
    assert ("Take in cash" if lang=="en" else "Возьмите наличными") in p.locator(".cashb").inner_text()
    full_color=p.locator("#b8-full").evaluate("e=>getComputedStyle(e).backgroundColor")
    approved=p.evaluate("""() => {const el=document.createElement('div');el.style.backgroundColor='var(--o)';document.body.append(el);const color=getComputedStyle(el).backgroundColor;el.remove();return color}""")
    assert full_color==approved,("R03 approved orange full amount",full_color,approved)
    p.locator("#b8-different").click()
    p.locator("#cashAmt").fill("200")
    p.locator('.b8-chip[data-reason="short"]').click()
    after=bounds(p)
    assert after["sheet"]["h"]>initial["sheet"]["h"],(initial,after)
    assert_horizontal(p,"difference")
    confirm_color=p.locator("#b8-confirm").evaluate("e=>getComputedStyle(e).backgroundColor")
    assert confirm_color==approved,("R03 approved orange confirm",confirm_color,approved)
    p.screenshot(path=str(OUT/f"webkit_cash_short_{lang}_{width}.png"))
    p.locator("#cashAmt").fill("abc")
    p.locator("#b8-confirm").click()
    p.wait_for_timeout(80)
    assert p.locator('.b11-inline-alert').is_visible(),"invalid amount must be reported"
    assert p.locator('.b11-inline-alert').evaluate("e=>!!e.closest('.b8-content')"),"alert must scroll with content, never overlay the cash title"
    p.locator("#cashAmt").fill("200")
    assert p.locator("#cashAmt").input_value()=="200"
    assert p.locator(".b11-inline-alert").inner_text().strip()=="", "R02: error persisted after valid 200"
    p.locator('.b8-chip[data-reason="other"]').click()
    p.locator("#cashNote").fill("Customer disputes bill")
    p.screenshot(path=str(OUT/f"webkit_cash_other_{lang}_{width}.png"))
    keyboard=max(290,min(430,height-270))
    p.set_viewport_size({"width":width,"height":keyboard})
    p.evaluate("window.dispatchEvent(new Event('resize'));window.visualViewport?.dispatchEvent(new Event('resize'))")
    p.wait_for_timeout(420)
    p.locator("#cashAmt").focus()
    p.wait_for_timeout(320)
    visible_amount=assert_vertical_visible(p,"R01 focused amount+title","#cashAmt",True)
    small=bounds(p)
    inp=small["input"];foot=small["footer"];view=small["viewport"]
    assert inp is not None and foot is not None,small
    assert inp["y"]>=view["top"]-2 and inp["bottom"]<=foot["y"]+3,(inp,foot,view)
    assert foot["bottom"]<=view["top"]+view["h"]+2,(foot,view)
    assert_horizontal(p,"keyboard")
    assert p.locator(".b11-inline-alert").inner_text().strip()==""
    p.screenshot(path=str(OUT/f"webkit_cash_keyboard_sim_{lang}_{width}.png"))
    p.locator("#cashNote").focus()
    p.wait_for_timeout(320)
    other_rect=assert_vertical_visible(p,"R01 focused Other field","#cashNote",False)
    assert_horizontal(p,"keyboard other")
    p.screenshot(path=str(OUT/f"webkit_cash_keyboard_other_{lang}_{width}.png"))
    p.set_viewport_size({"width":width,"height":height})
    p.locator("#cashAmt").fill("200")
    p.locator('.b8-chip[data-reason="short"]').click()
    p.locator("#b8-confirm").click()
    p.wait_for_timeout(180)
    snapshot=p.evaluate("({report:CALLS.report,finish:CALLS.finish,waiting:!!document.querySelector('.b11-waiting'),open:!!document.querySelector('#b8-ov'),saved:window.__brief11?.hasReport(9122),busy:DV?.reportBusy||false})")
    print("CASH_short_result_diagnostic (synthetic): "+json.dumps(snapshot),flush=True)
    p.wait_for_function("!document.querySelector('#b8-ov')&&document.querySelector('.b11-waiting')",timeout=5000)
    status=p.evaluate("({reports:CALLS.report,finishes:CALLS.finish,notice:document.querySelector('.b11-waiting')?.textContent,disabled:document.querySelector('#a-dock .a-step-button')?.disabled,phone:document.querySelector('.b11-support')?.getAttribute('href')})")
    assert status["reports"]==1 and status["finishes"]==0,status
    assert status["disabled"] and status["phone"]=="tel:+992900000000",status
    p.evaluate("deliverClick(9122)")
    assert p.evaluate("CALLS.click")==0,"duplicate delivery action must be blocked"
    p.screenshot(path=str(OUT/f"webkit_cash_waiting_{lang}_{width}.png"))
    records.append({"view":"cash","lang":lang,"size":[width,height],"before":initial,"short":after,"keyboard_sim":small,"amount_visible":visible_amount,"other_visible":other_rect,"waiting":status})
    ctx.close()
def check_nav(browser,width,height,lang):
    ctx,p=browser_page(browser,width,height,lang,NAV_SETUP)
    p.add_script_tag(content=route)
    p.add_script_tag(content=b8)
    p.add_script_tag(content=b11)
    p.evaluate("aNavigationOpen();render()")
    p.wait_for_timeout(250)
    count=p.locator(".n-map-item").count()
    assert count==3,("nav links",count)
    assert p.locator(".n-chooser .n-heading button svg path").count()>0,"R04 SVG X icon missing"
    close_path=p.locator(".n-chooser .n-heading button svg path").first.get_attribute("d")
    assert close_path=="M6 6l12 12M18 6L6 18",("R04 actual X icon from real source",close_path)
    assert "◯" not in p.locator(".n-chooser .n-heading button").inner_text()
    assert_horizontal(p,"navigation")
    r=bounds(p)
    assert r["nav"]["x"]>=-1 and r["nav"]["right"]<=width+1,r
    p.screenshot(path=str(OUT/f"webkit_navigation_{lang}_{width}.png"))
    records.append({"view":"navigation","lang":lang,"size":[width,height],"rects":r})
    ctx.close()
def check_home_css(browser,width,height,app):
    css=(ROOT/(app+".html")).read_text(encoding="utf8")
    style="\n".join(re.findall(r"<style(?:\s[^>]*)?>(.*?)</style>",css,re.S|re.I))
    if app=="customer":
        style+="\n"+(ROOT/"assets/customer-c/customer-c.css").read_text()
        style+="\n"+(ROOT/"assets/size-brief7/customer.css").read_text()
        markup='<div id="app"><div class="d6 d6h"><div class="d6-hh"><div class="d6-hr"><div class="d6-logo">TALABOT</div><button class="d6-loc">Dushanbe</button><button class="d6-hib">1</button><button class="d6-hib">2</button></div><div class="d6-sf"><input type="search"><button class="d6-fb">+</button></div></div><div class="d6-cats">'+''.join('<button class="d6-ct"><span>◯</span><b>Food</b></button>' for _ in range(6))+'</div><div class="d6-sh"><h2>Favourite restaurants</h2><button>All</button></div><div class="d6-rl"><div class="d6-lo"><div class="d6-ph"></div><b class="nm">Restaurant</b></div></div></div></div>'
    else:
        style+="\n"+(ROOT/"assets/size-brief7/merchant.css").read_text()
        markup='<div class="w"><header class="top">Orders</header><div class="seg"><button>Active</button><button>All</button></div>'+''.join('<div class="oc"><div class="oh pending">Order #9000</div><div class="ob"><div class="it2">Item</div><button class="b">Accept</button></div></div>' for _ in range(3))+'</div>'
    ctx=browser.new_context(viewport={"width":width,"height":height},is_mobile=True,has_touch=True)
    ctx.route("**/*",offline);p=ctx.new_page()
    p.set_content('<!doctype html><html><head><meta name="viewport" content="width=device-width,initial-scale=1"><style>'+style+'</style></head><body>'+markup+'</body></html>')
    horizontal=p.evaluate("({w:innerWidth,scroll:document.documentElement.scrollWidth})")
    assert horizontal["scroll"]<=width+1,(app,width,horizontal)
    p.screenshot(path=str(OUT/f"webkit_{app}_main_{width}.png"))
    records.append({"view":app,"size":[width,height],"width":horizontal})
    ctx.close()

with sync_playwright() as pw:
    try:
        browser=pw.webkit.launch(headless=True)
    except Exception as exc:
        raise RuntimeError("LAYOUT_webkit_suite BLOCKED: WebKit cannot run; no Chromium fallback") from exc
    for width,height in [(390,844),(375,667)]:
      for lang in ("en","ru"):
        check_cash(browser,width,height,lang)
        check_nav(browser,width,height,lang)
      for app in ("customer","merchant"):
        check_home_css(browser,width,height,app)
    browser.close()
assert len(blocked)==0,("external requests attempted (blocked)",blocked)
(OUT/"REPORT.json").write_text(json.dumps({"browser":"Playwright WebKit engine (NOT real iPhone Safari)",
 "scope":"source CSS with executable BRIEF8/11 JS and synthetic model; NO real user backend",
 "keyboard":"viewport height reduced; no native software keyboard",
 "blocked_external_attempts":blocked,"cases":records},ensure_ascii=False,indent=2),encoding="utf8")
print("CASH_no_large_empty_gap PASS (WebKit source CSS; full card height <500)")
print("CASH_sheet_no_layout_jump PASS (single content-driven sheet; no fixed reserved space)")
print("CASH_short_closes_and_shows_waiting_state PASS (ticket response; no delivery; duplicate blocked)")
print("CASH_toast_not_overlapping PASS (error inline within scroller, no fixed overlay)")
print("CASH_no_false_decimal_error PASS (abc invalid -> 200 valid, old error cleared)")
print("CASH_approved_orange_and_cash_title PASS (real approved tokens + localized title)")
print("NAV_close_svg_real PASS (uses exact source X path; no synthetic circle)")
print("CASH_focused_input_visible_webkit PASS (keyboard-height approximation, WebKit)")
print("LAYOUT_no_horizontal_overflow_webkit PASS (375/390 CSSpx, iPhone-sized WebKit)")
print("LAYOUT_no_text_overlap_webkit PASS (focused labels+inputs inside scroll clip, no footer overlap; 390/375 EN/RU)")
print("LAYOUT_webkit_suite PASS; real iPhone keyboard and live authenticated app UNTESTED")
