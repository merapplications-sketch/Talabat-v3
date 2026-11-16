#!/usr/bin/env python3
"""BRIEF-8 isolated 390 CSS-px synthetic Chromium proof of actual nav/cash adapters.
NEVER physical Safari or live auth; keyboard is reduced viewport, not native iOS keyboard.
All external HTTP, WS, image providers denied. Images in navigation replaced with
data URLs from the exact committed local SVGs ONLY for this disconnected fixture.
"""
import base64,json,re
from pathlib import Path
from playwright.sync_api import sync_playwright

ROOT=Path(__file__).resolve().parents[1]
OUT=ROOT/"evidence"/"driver-nav-cash-brief8"
OUT.mkdir(parents=True,exist_ok=True)
driver=(ROOT/"driver.html").read_text(encoding="utf-8")
base=re.search(r"<style>(.*?)</style>",driver,re.S).group(1)
base+="\n"+(ROOT/"assets/driver-a/driver-a.css").read_text(encoding="utf-8")
base+="\n"+(ROOT/"assets/size-brief7/driver.css").read_text(encoding="utf-8")
cash=(ROOT/"assets/driver-tech/nav-cash-brief8.js").read_text(encoding="utf-8")
route=(ROOT/"assets/driver-tech/route-layer.js").read_text(encoding="utf-8")
for name in ("google-maps","2gis","yandex-maps"):
    p=ROOT/"assets"/"driver-tech"/"map-icons"/(name+".svg")
    b64=base64.b64encode(p.read_bytes()).decode("ascii")
    route=route.replace("assets/driver-tech/map-icons/"+name+".svg","data:image/svg+xml;base64,"+b64)
STYLE="""<style>
*{box-sizing:border-box}html,body{margin:0;padding:0;min-height:100%;background:#f4f6f8;color:#17243c;font-family:Arial,sans-serif}
#app{min-height:100dvh}.ov{position:fixed;inset:0;z-index:1000;display:flex;align-items:center;justify-content:center;background:#0007}
.md{width:min(430px,100%);background:#fff;border-radius:16px;padding:16px;max-height:90dvh;overflow:auto}
.b{min-height:44px;display:flex;align-items:center;justify-content:center;gap:6px;border:0;border-radius:10px;background:#f1511b;color:#fff}
.b.s{background:#f7f7f7;color:#17243c;border:1px solid #ddd}.b.g{background:#187947;color:white}.n-body{padding:8px}
.n-heading{display:flex;align-items:center;justify-content:space-between}.n-destination{font-weight:700}
</style>"""
cash_setup=r"""
var DV={id:9122,total:278,amt:"278",cashMode:"full",note:"",cash:true,photo:false,up:false,ph:null},
    DLV={},CXL=null,online=true,chatOpen=false;
var dictionary={};
var TLB={lang:()=>window.SYN_LANG||"en",order:id=>({id:id,total:278,payment:"cash",leaveAtDoor:false}),
  addDict:(ru,en)=>Object.assign(dictionary,window.SYN_LANG==="ru"?ru:en),toast:()=>{}};
function t(k){return dictionary[k]||k}
function esc(x){return String(x).replace(/[&<>"]/g,c=>({"&":"&amp;","<":"&lt;",">":"&gt;",'"':"&quot;"}[c]))}
function ico(){return "<span></span>"}
function cashBox(){return '<div class="cashb"><b>278.00 TJS</b></div>'}
function confirmDeliver(){window.CALLS.push({amount:DV.amt,note:DV.note});return true}
function modal(){return ""}
function render(){document.getElementById("app").innerHTML=modal()}
function $(id){return document.getElementById(id)}
window.CALLS=[];
window.__deviceNotesV3={money(v){const s=String(v).trim().replace(",",".");return /^\d+(\.\d{1,2})?$/.test(s)?Number(s):null;}};
"""
nav_setup=r"""
var dictionary={};var DV=null,CXL=null,chatOpen=false,tab="o";
var DRV={id:"synthetic-driver"},GEO={lat:null,lng:null},DM=null;
var TLB={addDict:(ru,en)=>Object.assign(dictionary,window.SYN_LANG==="ru"?ru:en),
 navigation:async q=>q.op==="config"?{external:true,providers:["google","2gis","yandex"],mode:"tracking",reason:"disabled"}:
 {links:[],mode:"tracking",reason:"disabled"}};
window.TLB=TLB;
window.TALABOT_NAV_MODEL={point:p=>Array.isArray(p)&&p.length===2&&p.every(Number.isFinite),
 destination:(x,stage)=>[x.lat,x.lng],key:(x,stage,to)=>JSON.stringify([x.id,stage,to])};
function t(k){return dictionary[k]||k}
function esc(x){return String(x).replace(/[&<>"]/g,c=>({"&":"&amp;","<":"&lt;",">":"&gt;",'"':"&quot;"}[c]))}
function ico(){return "<span>×</span>"}
function aTask(){return {id:9122,lat:38.567741,lng:68.793569,address:"SYNTHETIC destination",store:"SYNTHETIC store"}}
function aTaskStage(){return 3}
function storePt(){return [38.5,68.7]}
function mapUpd(){}
function modal(){return ""}
function render(){document.getElementById("app").innerHTML=modal()}
"""
captures=[]
def blocking(route):route.abort("blockedbyclient")
def measure(page):
    return page.evaluate("""() => {
      const el=document.getElementById('b8-sheet')||document.querySelector('.n-chooser .md');
      if(!el)throw Error('modal not rendered');
      const r=el.getBoundingClientRect();
      const amount=document.querySelector('#cashAmt');
      const reason=document.querySelector('#b8-reason-slot');
      return {viewport:innerWidth,visibleHeight:innerHeight,modalTop:r.top,modalHeight:r.height,
        reasonHeight:reason?.getBoundingClientRect().height||0,
        numericMode:amount?.getAttribute('inputmode')||null,
        mapCount:document.querySelectorAll('.n-map-item').length,
        brandedIcons:[...document.querySelectorAll('.n-map-item img')].map(x=>({loaded:x.complete&&x.naturalWidth>0,w:x.naturalWidth})),
        bodyOverflow:document.body.scrollWidth>innerWidth+1};
    }""")
with sync_playwright() as pw:
    browser=pw.chromium.launch(headless=True)
    for lang in ("ru","en"):
        ctx=browser.new_context(viewport={"width":390,"height":760},device_scale_factor=1,
            is_mobile=True,has_touch=True)
        ctx.route("**/*",blocking)
        page=ctx.new_page()
        page.set_content("<!doctype html><html><head><meta name='viewport' content='width=device-width,initial-scale=1'>"+STYLE+"<style>"+base+"</style></head><body><div id='app'></div></body></html>")
        page.evaluate("(lang)=>{window.SYN_LANG=lang}",lang)
        page.add_script_tag(content=cash_setup)
        page.add_script_tag(content=cash)
        page.evaluate("render()")
        page.screenshot(path=str(OUT/("cash_"+lang+"_full_390.png")))
        full=measure(page)
        page.locator("#b8-different").click()
        page.locator("#cashAmt").fill("200")
        page.locator('.b8-chip[data-reason="short"]').click()
        page.screenshot(path=str(OUT/("cash_"+lang+"_short_390.png")))
        short=measure(page)
        assert abs(full["modalHeight"]-short["modalHeight"])<0.25, (full,short)
        assert short["numericMode"]=="decimal"
        assert short["reasonHeight"]>=180
        page.set_viewport_size({"width":390,"height":430}) # only simulated keyboard
        page.wait_for_timeout(250)
        page.screenshot(path=str(OUT/("cash_"+lang+"_keyboard-sim_390.png")))
        keyboard=measure(page)
        assert keyboard["modalTop"]>=-1 and keyboard["modalHeight"]<=430
        captures.append({"lang":lang,"view":"cash","full":full,"short":short,"keyboard_simulated":keyboard})
        ctx.close()
        ctx=browser.new_context(viewport={"width":390,"height":760},device_scale_factor=1,
            is_mobile=True,has_touch=True)
        ctx.route("**/*",blocking)
        page=ctx.new_page()
        page.set_content("<!doctype html><html><head><meta name='viewport' content='width=device-width,initial-scale=1'>"+STYLE+"<style>"+base+"</style></head><body><div id='app'></div></body></html>")
        page.evaluate("(lang)=>{window.SYN_LANG=lang}",lang)
        page.add_script_tag(content=nav_setup)
        page.add_script_tag(content=route)
        page.evaluate("aNavigationOpen();render()")
        page.wait_for_timeout(150)
        navm=measure(page)
        assert navm["mapCount"]==3,navm
        assert all(x["loaded"] for x in navm["brandedIcons"]),navm
        page.screenshot(path=str(OUT/("navigation_"+lang+"_390.png")))
        captures.append({"lang":lang,"view":"navigation","rendered":navm})
        ctx.close()
    browser.close()
(OUT/"EVIDENCE.json").write_text(json.dumps({
 "source":"exact checked BRIEF-8 candidate",
 "browser":"isolated Chromium; NOT physical iOS Safari",
 "mode":"source CSS + executable adapter with synthetic order/data and offline brand assets",
 "keyboard":"reduced viewport simulates visible space; no native iOS keyboard",
 "live_network_requests":"blocked",
 "screenshots":len(list(OUT.glob("*.png"))),
 "captures":captures
},ensure_ascii=False,indent=2),encoding="utf-8")
print("PASS CASH_sheet_no_layout_jump: constant 390px synthetic sheet rect on difference/reason")
print("PASS CASH_numeric_keypad: actual numeric inputmode, keyboard simulated via viewport")
print("PASS NAV_three_icons_row: three branded local SVGs loaded inside 390px Chromium")
print("BRIEF8_CAPTURE: "+str(len(list(OUT.glob("*.png"))))+" synthetic screenshots RU/EN at 390px (NOT native Safari)")
